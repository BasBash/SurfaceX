import cv2
import cv2.aruco as aruco
import numpy as np


def write_text_to_frame(frame, texto):
    altura, largura = frame.shape[:2]
    altura_faixa = 50

    y_inicio = altura - altura_faixa
    y_fim = altura

    cv2.rectangle(frame, (0, y_inicio), (largura, y_fim), (0, 0, 0), -1)

    fonte = cv2.FONT_HERSHEY_SIMPLEX
    escala_fonte = 1
    espessura = 2
    cor_texto = (255, 255, 255)
    tamanho_texto, _ = cv2.getTextSize(texto, fonte, escala_fonte, espessura)
    largura_texto = tamanho_texto[0]
    altura_texto = tamanho_texto[1]

    x_texto = (largura - largura_texto) // 2
    y_texto = y_inicio + (altura_faixa + altura_texto) // 2
    cv2.putText(frame, texto, (x_texto, y_texto), fonte, escala_fonte, cor_texto, espessura, cv2.LINE_AA)

def get_roi(frame, camera_matrix, dist_coeffs, length_exp=50, target_id=43):

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector   = cv2.aruco.ArucoDetector(
        aruco_dict,
        cv2.aruco.DetectorParameters()
    )

    aruco_lenght = 144
    obj_corners = np.array([
        [-aruco_lenght/2,  aruco_lenght/2,              0.0],
        [-aruco_lenght/2, -aruco_lenght/2,              0.0],
        [ aruco_lenght/2 + length_exp, -aruco_lenght/2, 0.0],
        [ aruco_lenght/2 + length_exp,  aruco_lenght/2, 0.0]
    ], dtype=np.float32)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is None:
        return None

    ids = ids.flatten()
    matches = np.where(ids == target_id)[0]
    if matches.size == 0:
        return None

    rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(
        corners, aruco_lenght, camera_matrix, dist_coeffs
    )

    idx = matches[0]
    rvec, tvec = rvecs[idx][0], tvecs[idx][0]

    img_pts, _ = cv2.projectPoints(
        obj_corners, rvec, tvec,
        camera_matrix, dist_coeffs
    )
    flat = img_pts.reshape(-1, 2).astype(int)
    return flat
