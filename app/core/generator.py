import threading
import time
import cv2
import numpy as np
from app.core.proc import precompute, rectify
from app.core.stream import Stream
from app.config.exceptions import CameraReadError
from app.core.scanner_config import Scanner


def frame_generator(scanner: Scanner, stop_event: threading.Event):

    if scanner.camera_instance is None or not scanner.camera_instance.isOpened():
        raise CameraReadError("Camera is not opened")
    if scanner.camera_matrix is None or scanner.dist_coeffs is None:
        pass
    if scanner.firmata_instance is None:
        pass

    scanner.plane_constants = None

    k_opt, _, map1, map2 = precompute(scanner.camera_matrix, scanner.dist_coeffs, (1280, 720))
    if k_opt is None or map1 is None or map2 is None:
        raise IOError("Could not open camera calibration file")

    start = time.time()
    while not stop_event.is_set():
        ret, frame = scanner.camera_instance.read()
        if not ret:
            stop_event.set()
            raise CameraReadError("Error reading frame")

        frame = rectify(map1, map2, frame)
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if time.time() - start > 10.0:
            scanner.plane_constants = np.array([1.,1.,2.1,-1.0])

        yield Stream(gray, 1, 0.0, 0.0, 0.0, np.zeros((1, 5)))
        time.sleep(0.01)  # ~20 FPS de leitura, mas atualiza 10 FPS


def find_refs(frame, camera_matrix, dist_coeffs):
    pass

def scan(scanner: Scanner, stop_event=None):
    if scanner.camera_instance is None or not scanner.camera_instance.isOpened():
        raise CameraReadError("Camera is not opened")

    start = time.time()
    while not stop_event.is_set():
        ret, frame = scanner.camera_instance.read()
        if not ret:
            stop_event.set()
            raise CameraReadError("Error reading frame")

        frame = cv2.flip(frame, 1)
        yield Stream(frame, 1, time.time() - start, 0.0, 0.0, np.zeros((1, 5)))
        time.sleep(0.01)  # ~20 FPS de leitura, mas atualiza 10 FPS
