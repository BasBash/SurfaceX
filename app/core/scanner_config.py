import numpy as np
import cv2
from numpy import ndarray
from pyfirmata2 import Arduino, util
import logging
from app.config.exceptions import CameraReadError
from app.core.proc import precompute, rectify

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Scanner:
    def __init__(self):
        self.camera_index:        int | None = None
        self.camera_name:         str | None = None
        self.firmata_port:        str | None = None
        self.calibration_file:    str | None = None
        self.camera_matrix:   ndarray | None = None
        self.dist_coeffs:     ndarray | None = None
        self.plane_constants: ndarray | None = None
        self.map_one:         ndarray | None = None
        self.map_two:         ndarray | None = None

        self.firmata_connected = False
        self.firmata_instance  = None

        self.camera_connected  = False
        self.camera_instance   = None
        self.lock = False

    def set_calibration(self, file_path):
        self.calibration_file = file_path
        try:
            data = np.load(file_path, allow_pickle=True)
            calib_data = data.item() if hasattr(data, "item") else dict(data)
            cm = calib_data.get("camera_matrix")
            dc = calib_data.get("dist_coeffs")
            if cm is None or dc is None:
                raise ValueError("Arquivo de calibração não contém camera_matrix ou dist_coeffs")
            self.camera_matrix = np.asarray(cm, dtype=np.float64)
            self.dist_coeffs = np.asarray(dc).ravel().astype(np.float64)
            self.camera_matrix, self.dist_coeffs, self.map_one, self.map_two = precompute(
                self.camera_matrix, self.dist_coeffs, (1280, 720)
            )
        except Exception as e:
            raise RuntimeError(f"Falha ao carregar arquivo de calibração: {e}")

    def load_firmata(self):
        self.lock = True
        # noinspection PyBroadException
        try:
            self.firmata_instance = Arduino(self.firmata_port)
            it = util.Iterator(self.firmata_instance)
            it.start()
        except Exception:
            pass
        self.lock = False


    def load_camera(self, feedback_cb) -> None:
        self.lock = True
        if self.camera_index is None:
            feedback_cb(text="Conecte uma câmera ao computador!")
            return

        feedback_cb(text=f"Inicializando camera {self.camera_index}.")
        self.camera_instance, cap = None, None

        cam_index = getattr(self, "camera_index", 0)
        cap = cv2.VideoCapture(cam_index)
        feedback_cb(text="Câmera conectada! Verificando...")
        if not cap.isOpened():
            raise CameraReadError("Erro ao inicializar camera")
        feedback_cb(text="Definindo resolução HD.")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        feedback_cb(text="Conexão estabelecida com sucesso!")
        self.camera_instance = cap
        self.lock = False


    def get_frame(self, flip=False) -> None | ndarray:
        if self.camera_instance is None:
            logger.debug("Nenhuma instância de VideoCapture fornecida.")
            return None

        ret, frame = self.camera_instance.read()
        if not ret:
            return None
        if flip:
            frame = cv2.flip(frame, 1)
        undistorted_frame = rectify(self.map_one, self.map_two, frame)
        return undistorted_frame


    def release_camera(self) -> None:
        if self.camera_instance is None:
            logger.debug("Nenhuma instância de VideoCapture fornecida.")
        else:
            try:
                if hasattr(self.camera_instance, "release") and callable(getattr(self.camera_instance, "release")):
                    try:
                        self.camera_instance.release()
                        logger.debug("Câmera liberada com sucesso.")
                    except Exception as e:
                        logger.exception("Falha ao liberar VideoCapture: %s", e)
                else:
                    logger.debug("Objeto cap não possui método release().")
            finally:
                pass
