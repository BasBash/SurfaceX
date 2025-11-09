import cv2
import serial
import serial.tools.list_ports
import time
from cv2_enumerate_cameras import enumerate_cameras
from app.config.logger import logger

def get_camera_list():
    cameras_available = []
    logger.info('Running camera discovery')
    fetched_cameras = enumerate_cameras(cv2.CAP_DSHOW)
    if len(fetched_cameras) == 0:
        logger.warning('No cameras found')
        return []

    for camera_info in fetched_cameras:
        cameras_available.append((camera_info.index, camera_info.name))
        logger.info(f"Camera {camera_info}")
    return cameras_available

def firmata_handshake(port):
    try:
        ser = serial.Serial(port, baudrate=57600, timeout=2)
        time.sleep(2)  # Aguarda inicialização do Arduino

        # Envia comando SYSEX vazio (Start + End)
        ser.write(bytes([0xF0, 0xF7]))
        time.sleep(0.5)

        response = ser.read(64)
        ser.close()

        # Verifica se resposta contém SYSEX válido
        return b'\xF0' in response and b'\xF7' in response
    except Exception as e:
        print(f"Erro em {port}: {e}")
        return False

def get_device_list():
    firmata_ports = []
    all_ports = serial.tools.list_ports.comports()

    for port in all_ports:
        logger.info(f"Testando: {port.device} - {port.description}")
        if firmata_handshake(port.device):
            logger.info(f"Firmata detectado via handshake em {port.device}")
            firmata_ports.append(port.device)
        else:
            logger.info(f"Sem resposta válida de Firmata em {port.device}")

    return firmata_ports
