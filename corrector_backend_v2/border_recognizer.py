import cv2
import numpy as np

from .utils import order_triangles, standardize_triangle_vertices, calculate_center_xy, point_distance


def find_white_triangles(binary_image, min_area) -> (np.ndarray, np.ndarray):
    """
    Identifica triângulos brancos grandes em uma imagem binária.

    :param binary_image: Imagem binária invertida (triângulos brancos em fundo preto).
    :param min_area: Área mínima para considerar um triângulo.
    :return: Cordenada dos triangulos encontrados e contorno desses triângulos.
    """
    # Encontrar contornos na imagem binária
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filtrar contornos para encontrar triângulos grandes
    triangles_contour = []
    triangles_cords = []
    for cnt in contours:
        # Aproximar o contorno para verificar se é um triângulo
        epsilon = 0.04 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # Verificar se o contorno tem 3 vértices e área suficiente
        if len(approx) == 3 and cv2.contourArea(cnt) > min_area:
            triangles_cords.append(approx.reshape((3, 2)))
            triangles_contour.append(cnt)

    return triangles_cords, triangles_contour


def filter_triangles(triangles, image_shape):
    """
    Filtra e padroniza os triângulos:
    1. Remove duplicados com base na proximidade.
    2. Garante no máximo 4 triângulos.
    3. Padroniza a ordem dos pontos de cada triângulo.
    4. Ordena os triângulos conforme a posição na imagem.

    :param triangles: Lista de contornos de triângulos.
    :param image_shape: Tupla (altura, largura) da imagem original.
    :return: Lista de até 4 triângulos filtrados e ordenados.
    """

    # Remover triângulos duplicados
    filtered = []
    for tri in triangles:
        tri_center = calculate_center_xy(tri)
        tri_size = np.sqrt(cv2.contourArea(tri))
        is_duplicate = any(
            point_distance(tri_center, calculate_center_xy(t)) < 2 * tri_size
            for t in filtered
        )
        if not is_duplicate:
            filtered.append(tri)

    # Garantir no máximo 4 triângulos
    if len(filtered) > 4:
        img_center = np.array([image_shape[1] / 2, image_shape[0] / 2])
        filtered.sort(key=lambda tri: point_distance(calculate_center_xy(tri), img_center))
        filtered = filtered[:4]

    # Padronizar a ordem dos pontos em cada triângulo
    standardized_triangles = [standardize_triangle_vertices(tri) for tri in filtered]
    ordered_triangles = order_triangles(standardized_triangles, image_shape)
    return np.array(ordered_triangles)
