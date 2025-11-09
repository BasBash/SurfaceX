import logging

APP_LOG_NAME = "SurfaceX"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)

logger = logging.getLogger(APP_LOG_NAME)
logger.propagate = False

handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s", "%H:%M:%S"
)
handler.setFormatter(formatter)
logger.addHandler(handler)