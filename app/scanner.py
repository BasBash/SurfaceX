import threading
import cv2
from PIL import ImageTk, Image
import time
from app.config import logger
from app.config.constants import CAMERA_VIEWPORT_WIDTH, CAMERA_VIEWPORT_HEIGHT, BLACK_FRAME
from app.config.exceptions import CameraReadError
from app.core.generator import frame_generator
from app.view.scan_view import ScanGUI
import tkinter as tk
from app.config.logger import logger


class Scanner(ScanGUI):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)

        self.stop_event            = threading.Event()
        self.running               = False
        self.frame_gen             = None
        self.thread                = None

        self.button_connect.config(command=self.connect_devices)
        self.button_reference.config(command=self.set_references)


    def connect_devices(self):
        if self.hardware.lock:
            return

        self.set_status("Conectando à câmera...")
        self.reset_progress()
        self.button_connect.config(text="Conectando...")
        self.button_connect.config(state=tk.DISABLED)

        self.datadisplay.btn_open_file.config(state=tk.DISABLED)
        self.button_firmata_refresh.config(state=tk.DISABLED)
        self.c_selector.disable_elements()
        self.combo_box.config(state=tk.DISABLED)

        def target():
            try:
                # Etapa 1: Check all conditions before connecting
                self.set_status("Iniciando conexão...")
                self.set_progress(0)

                # Etapa 2: Carregar câmera
                self.set_status("Conectando à câmera...")
                if self.hardware.camera_index is None:
                    self.set_status("Selecione uma câmera válida!")
                    raise CameraReadError("Índice da câmera não definido")
                self.hardware.camera_instance = cv2.VideoCapture(self.hardware.camera_index)
                self.set_progress(20)

                if not self.hardware.camera_instance.isOpened():
                    raise CameraReadError("Erro ao inicializar câmera")
                self.set_progress(40)

                # Etapa 3: Verificar câmera
                self.set_status("Câmera conectada. Configurando a resolução...")
                self.hardware.camera_instance.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.hardware.camera_instance.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.set_progress(50)

                # Etapa 4: Carregar Firmata
                self.set_status("Conectando ao Arduino...")
                self.hardware.load_firmata()
                self.set_progress(90)

                # Etapa 5: Verificar Firmata
                if self.hardware.firmata_instance is None:
                    raise Exception("Firmata não foi inicializada")
                self.set_status("Firmata conectada.")
                self.set_progress(100)
                self.reset_progress()


                self.start_stream()

            except Exception as e:
                logger.info(f"Erro inesperado: {e}")
                self.set_status("Erro inesperado.")
                self.set_progress(0)
            else:
                self.set_status("Conexão concluída.")

            # Atualiza botão após tentativa
            self.button_connect.config(state=tk.NORMAL)

            if self.hardware.camera_instance.isOpened() and self.hardware.firmata_instance is not None:
                self.button_connect.config(text="Desconectar")
                self.button_connect.config(command=self.disconnect_all)
            else:
                self.button_connect.config(text="Conectar")
                self.button_connect.config(command=self.connect_devices)

        threading.Thread(target=target, daemon=True).start()

    def disconnect_all(self):
        self.hardware.lock = True
        self._show_frame(BLACK_FRAME)

        self.datadisplay.btn_open_file.config(state=tk.NORMAL)
        self.button_firmata_refresh.config(state=tk.NORMAL)
        self.c_selector.enable_elements()
        self.combo_box.config(state=tk.NORMAL)

        try:
            cap = getattr(self.hardware, "camera_instance", None)
            if cap is not None:
                try:
                    if hasattr(self.hardware, "camera_running"):
                        self.hardware.camera_running = False
                    cap.release()
                except Exception as e:
                    logger.error("Erro ao liberar camera: %s", e)
        except Exception:
            logger.error("Falha ao desconectar camera")

        try:
            board = getattr(self.hardware, "firmata_instance", None)
            if board is not None:
                iterator = getattr(self.hardware, "iterator", None)
                if iterator is not None:
                    try:
                        stop = getattr(iterator, "stop", None)
                        if callable(stop):
                            stop()
                    except Exception:
                        logger.exception("Erro ao parar iterator do firmata")

                try:
                    exit_fn = getattr(board, "exit", None)
                    if callable(exit_fn):
                        exit_fn()
                except Exception:
                    logger.exception("board.exit() falhou")

                for attr in ("sp", "ser", "serial", "s"):
                    serial_obj = getattr(board, attr, None)
                    if serial_obj is not None:
                        close_fn = getattr(serial_obj, "close", None)
                        if callable(close_fn):
                            try:
                                close_fn()
                            except Exception:
                                logger.exception("Erro ao fechar serial via %s.close()", attr)
                try:
                    self.hardware.firmata_instance = None
                except Exception:
                    pass
        except Exception:
            logger.exception("Falha ao desconectar firmata")

        try:
            self.set_status("Desconectado")
            self.reset_progress()
            self.button_connect.config(text="Conectar", command=self.connect_devices, bg=None, state=tk.NORMAL)
        except Exception:
            pass

        self.hardware.plane_constants = None

        try:
            self.hardware.lock = False
        except Exception:
            pass

    def stop_if_running(self):
        if self.running:
            self.stop_stream()

    def start_stream(self):
        self.stop_event.clear()
        self.running = True

        self.frame_gen = frame_generator(self.hardware, stop_event=self.stop_event)
        self.thread    = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop_stream(self):
        self.stop_event.set()
        self.running = False

    def _capture_loop(self):
        try:
            for stream in self.frame_gen:
                if self.stop_event.is_set():
                    break
                self.label_view.after(0, self._show_frame, stream.frame)
                if (stream.progress_proc >= 1.0 and
                        stream.progress_capt >= 1.0 and
                        self.laser_plane_constants is None):
                    self.laser_plane_constants = stream.resource
                time.sleep(0.1)
        except Exception as err:
            logger.error(f"Capture error: {err}")
            # self.after(0, lambda: messagebox.showerror("Erro de Captura", str(err))) # type: ignore
        finally:
            self.after(10, self.stop_stream) # type: ignore

    def _show_frame(self, frame):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb).resize((CAMERA_VIEWPORT_WIDTH, CAMERA_VIEWPORT_HEIGHT))
        photo   = ImageTk.PhotoImage(img_pil)
        self.label_view.config(image=photo) # type: ignore
        self.label_view.image = photo

    def set_references(self):
        pass

    def start_scanning(self):
        pass