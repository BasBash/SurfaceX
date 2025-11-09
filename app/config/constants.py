# constants.py

from typing import Final
import numpy as np

APP_TITLE_NAME = "SurfaceX - 3D Scanner by MITEC"

# 1) Câmera
DEFAULT_CAMERA_INDEX: Final[int] = 0
READ_INTERVAL_SEC: Final[float]  = 0.01    # ritmo de leitura da câmera (~100 Hz loop, ~10–20 FPS efetivo)
CAMERA_WIDTH : Final[int] = 1280
CAMERA_HEIGHT: Final[int] =  720
CAMERA_VIEWPORT_WIDTH:  Final[int] = int(CAMERA_WIDTH  * 0.9)
CAMERA_VIEWPORT_HEIGHT: Final[int] = int(CAMERA_HEIGHT * 0.9)
FRAME_RESOLUTION: Final[tuple[int, int]] = (CAMERA_WIDTH, CAMERA_HEIGHT)
BLACK_FRAME = np.zeros((CAMERA_VIEWPORT_HEIGHT, CAMERA_VIEWPORT_WIDTH, 3), dtype=np.uint8)
BLUE_FRAME  = np.full((CAMERA_VIEWPORT_HEIGHT, CAMERA_VIEWPORT_WIDTH, 3), (255, 0, 0), dtype=np.uint8)


# --------------------------------------------- #
# ----------- DEFINIÇÕES: FIRMATA ------------- #
# --------------------------------------------- #
LSR_PIN_STR: Final[str] = "d:3:o"
DIR_PIN_STR: Final[str] = "d:2:o"
STP_PIN_STR: Final[str] = "d:4:o"

# --------------------------------------------- #
# ----------------- DELAYS -------------------- #
# --------------------------------------------- #
LASER_TOGGLE_DELAY: Final[float] = 0.225


# --------------------------------------------- #
# --------------- ARUCO/CHARUCO --------------- #
# --------------------------------------------- #
ARUCO_DICT_NAME: Final[str]         = "DICT_4X4_50"
ARUCO_REFMK_LENGTH_MM: Final[float] = 200.0
TARGET_MARKER_ID_42: Final[int]     = 42
TARGET_MARKER_ID_43: Final[int]     = 43
ROI_EXTEND_MM: Final[float]         = 60.0

DEFAULT_CAMERA_FPS = 30
VOXEL_SIZE = 0.0001
SQUARE_SIZE = 0.058  # 58mm
MARKER_SIZE = 0.043  # 43mm
BAUD_RATE = 9600
BOARD_COLS = 7
BOARD_ROWS = 7
IMG_RES = (1280, 720)
