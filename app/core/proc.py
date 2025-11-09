import cv2
from typing import Tuple
import numpy as np
from app.config.constants import FRAME_RESOLUTION


def precompute(
        camera_matrix:  np.ndarray | None,
        dist_coeffs:    np.ndarray | None,
        orig_size: Tuple[int, int] | None
        ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula previamente os mapas de retificação para imagens capturadas pela câmera e
    as matrizes de calibração e distorção otimizadas.

    Args:
        camera_matrix (np.ndarray): Matriz intrínseca da câmera.
        dist_coeffs (np.ndarray): Coeficientes de distorção da câmera.
        orig_size (Tuple[int, int]): Resolução original da imagem (largura, altura).

    Returns:
        matrix_opt (np.ndarray): Matriz de câmera otimizada.
        dist_opt (np.ndarray): Coeficientes de distorção otimizados.
        map_one (np.ndarray): Mapa de retificação 1.
        map_two (np.ndarray): Mapa de retificação 2.
    """

    if camera_matrix is None or dist_coeffs is None or orig_size is None:
        raise ValueError("Matriz da câmera, resolução ou coeficientes de distorção não fornecidos.")

    k0 = camera_matrix.astype(np.float64)
    d0 = dist_coeffs.ravel()

    sx, sy = FRAME_RESOLUTION[0] / orig_size[0], FRAME_RESOLUTION[1] / orig_size[1]
    k = k0.copy()
    k[0, :] *= sx
    k[1, :] *= sy

    k_opt, _ = cv2.getOptimalNewCameraMatrix(k, d0, FRAME_RESOLUTION, alpha=0)
    d_opt = np.zeros_like(d0)
    mp1, mp2 = cv2.initUndistortRectifyMap(
        k, d0, np.array([]), k_opt, FRAME_RESOLUTION, cv2.CV_16SC2
    )
    return k_opt, d_opt, mp1, mp2

def rectify(
        map_one, map_two,
        img: np.ndarray
) -> np.ndarray:
    """
    Retifica a imagem usando os mapas de retificação fornecidos.
    
    Args:
        map_one (np.ndarray): Mapa de retificação 1.
        map_two (np.ndarray): Mapa de retificação 2.
        img (np.ndarray): Imagem a ser retificada.

    Returns:
        np.ndarray: Imagem retificada.
    """
    if img is None or img.size == 0:
        raise ValueError("Imagem inválida ou vazia para retificação.")
    tmp = cv2.resize(img, FRAME_RESOLUTION)
    return cv2.remap(tmp, map_one, map_two, interpolation=cv2.INTER_LINEAR)

'''
def detect_aruco_pose(
        img: np.ndarray,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
        aruco_id: int
) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = aruco.detectMarkers(gray, ARUCO_DICT_4X4, parameters=PARAMS)
    if ids is None or len(ids) == 0:
        logger.warning("Nenhum marcador ArUco detectado.")
        return False, None, None

    if aruco_id not in ids:
        logger.warning(f"Marcador ArUco ID {aruco_id} não detectado.")
        return False, None, None

    idx = np.where(ids == aruco_id)[0][0]
    rvec, tvec, _ = aruco.estimatePoseSingleMarkers(corners[idx], MARKER_SIZE, camera_matrix, dist_coeffs)
    if rvec is None or tvec is None:
        logger.warning("Falha ao estimar a pose do marcador ArUco.")
        return False, None, None

    return True, rvec.flatten(), tvec.flatten()

def detect_charuco_pose(
        img: np.ndarray,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray
) -> Tuple[bool, Optional[np.ndarray], Optional[np.ndarray]]:
    corners, ids, _ = aruco.detectMarkers(img, ARUCO_DICT, parameters=PARAMS)
    if ids is None or len(ids) == 0:
        return False, None, None

    ok, char_corners, char_ids = aruco.interpolateCornersCharuco(
        corners, ids, img, CHARUCO
    )
    if not ok or char_corners is None or char_ids is None:
        return False, None, None

    retval, rvec, tvec = aruco.estimatePoseCharucoBoard(
        char_corners,
        char_ids,
        CHARUCO,
        camera_matrix,
        dist_coeffs,
        np.array([]),
        np.array([])
    )

    return bool(retval), rvec.flatten(), tvec.flatten()
'''
def laser_skeleton(bg: np.ndarray, fg: np.ndarray) -> np.ndarray:
    diff = cv2.absdiff(bg, fg)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
    ker = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mor = cv2.morphologyEx(th, cv2.MORPH_CLOSE, ker)
    mop = cv2.morphologyEx(mor, cv2.MORPH_OPEN, ker)
    return cv2.ximgproc.thinning(mop)

def laser_skeleton_roi(bg: np.ndarray, fg: np.ndarray, roi_mask) -> np.ndarray:
    diff = cv2.absdiff(bg, fg)
    diff_roi = cv2.bitwise_and(diff, diff, mask=roi_mask)
    _, th = cv2.threshold(diff_roi, 20, 255, cv2.THRESH_BINARY)
    return th

def fit_laser_line(skel: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    pts = cv2.findNonZero(skel)
    if pts is None or len(pts) < 3:
        raise RuntimeError("Poucos pixels de laser para ajuste de linha")
    arr = pts.reshape(-1, 2).astype(np.float32)
    mu = arr.mean(axis=0)
    cov = np.cov((arr - mu).T)
    vals, vecs = np.linalg.eigh(cov)
    direction = vecs[:, np.argmax(vals)]
    return direction / np.linalg.norm(direction), mu

def plane_from_np(n: np.ndarray, p: np.ndarray) -> np.ndarray:
    if n.shape != (3,):
        raise ValueError("Normal deve ser um vetor 3D")
    if p.shape != (3,):
        raise ValueError("Ponto deve ser um vetor 3D")
    nn = n.astype(np.float64)
    nn /= np.linalg.norm(nn)
    d_ = -nn.dot(p)
    return np.hstack((nn, d_))

def backproject(pts2d: np.ndarray, plane: np.ndarray, k_opt: np.ndarray) -> np.ndarray:
    a, b, c, d = plane
    fx, fy = k_opt[0, 0], k_opt[1, 1]
    cx, cy = k_opt[0, 2], k_opt[1, 2]

    x = pts2d[:, 0] - cx
    y = pts2d[:, 1] - cy
    denom = a * fy * x + b * fx * y + c * fx * fy
    z_r3 = -d * fx * fy / denom
    x_r3 = x * z_r3 / fx
    y_r3 = y * z_r3 / fy
    return np.vstack((x_r3, y_r3, z_r3)).T

def camera_to_board(
        pts_cam: np.ndarray, rvec: np.ndarray, tvec: np.ndarray
) -> np.ndarray:
    r, _ = cv2.Rodrigues(rvec)
    shifted = pts_cam - tvec.reshape(1, 3)
    return (r.T @ shifted.T).T

def fit_line_from_points(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ajusta uma reta 3D via PCA. Retorna direção normalizada + ponto médio.
    """
    centroid = points.mean(axis=0)
    cov      = np.cov((points - centroid).T)
    vals, vecs = np.linalg.eigh(cov)
    direction = vecs[:, np.argmax(vals)]
    direction /= np.linalg.norm(direction)
    return direction, centroid
