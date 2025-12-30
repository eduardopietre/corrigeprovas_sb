from pathlib import Path

import cv2
import numpy as np


def point_distance(p1, p2):
    """
    Calculates the Euclidean distance between two points.

    Args:
        p1 (tuple or list): First point (x1, y1).
        p2 (tuple or list): Second point (x2, y2).

    Returns:
        float: The Euclidean distance between p1 and p2.
    """
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def calculate_center_xy(points: np.ndarray | list) -> np.ndarray:
    """
    Calculates the center point of a set of points.

    Args:
        points (np.ndarray or list): Array or list of points with shape (N, 2), where N is the number of points.

    Returns:
        np.ndarray: The center point as an array [x, y].
    """
    return np.mean(points, axis=0)


def contour_center(contour) -> (int, int):
    """
    Calculates the center (centroid) of a contour using image moments.

    Args:
        contour (np.ndarray): Contour points as an array of shape (N, 1, 2).

    Returns:
        tuple[int, int]: The centroid coordinates (cx, cy).
    """
    m = cv2.moments(contour)
    if m["m00"] != 0:
        cx = int(m["m10"] / m["m00"])
        cy = int(m["m01"] / m["m00"])
    else:
        cx, cy = 0, 0
    return cx, cy


def convert_to_relative(triangle: np.ndarray) -> (np.ndarray, np.ndarray):
    """
    Converts a triangle from absolute coordinates to relative coordinates based on its center point.

    Parameters:
        triangle (np.ndarray): A 2D array representing the triangle with shape (3, 2).

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the relative triangle and the center point.
    """
    center = calculate_center_xy(triangle)
    relative_triangle = triangle - center
    return relative_triangle, center


def convert_to_absolute(relative_triangle: np.ndarray, center: np.ndarray) -> np.ndarray:
    """
    Converts a triangle from relative coordinates back to absolute coordinates using its center point.

    Parameters:
        relative_triangle (np.ndarray): A 2D array representing the triangle with shape (3, 2) in relative coordinates.
        center (np.ndarray): A 1D array representing the center point of the triangle.

    Returns:
        np.ndarray: The triangle in absolute coordinates.
    """
    absolute_triangle = relative_triangle + center
    return absolute_triangle


def reorder_warped_triangle(tri_orig: np.ndarray, tri_warped: np.ndarray) -> np.ndarray:
    """
    Reorders the points of a warped triangle to match the order of the original triangle.

    Parameters:
        tri_orig (np.ndarray): A 2D array representing the original triangle with shape (3, 2).
        tri_warped (np.ndarray): A 2D array representing the warped triangle with shape (3, 2).

    Returns:
        np.ndarray: The reordered warped triangle in absolute coordinates.
    """
    # Convert both triangles to relative coordinates
    tri_orig_rel, center_orig = convert_to_relative(tri_orig)
    tri_warped_rel, center_warped = convert_to_relative(tri_warped)

    # Find the best matching order for points in tri_warped_rel
    reordered_indices = []
    remaining_indices = list(range(3))

    for point in tri_orig_rel:
        distances = [np.linalg.norm(point - tri_warped_rel[i]) for i in remaining_indices]
        best_match_idx = remaining_indices[np.argmin(distances)]
        reordered_indices.append(best_match_idx)
        remaining_indices.remove(best_match_idx)

    # Reorder the warped triangle points
    reordered_warped_rel = tri_warped_rel[reordered_indices]

    # Convert back to absolute coordinates
    reordered_warped_abs = convert_to_absolute(reordered_warped_rel, center_warped)
    return reordered_warped_abs


def rect_to_xywh(rect: np.ndarray | list) -> list:
    """
    Converts a rectangle from [x0, y0, x1, y1] format to [x, y, w, h] format.

    Parameters:
        rect (numpy.ndarray or list): Rectangle in [x0, y0, x1, y1] format.

    Returns:
        numpy.ndarray: Rectangle in [x, y, w, h] format, where:
                       - (x, y) is the top-left corner.
                       - w is the width.
                       - h is the height.
    """
    if isinstance(rect, np.ndarray):
        rect = rect.flatten()
    if len(rect) != 4:
        raise ValueError("Input rectangle must have 4 values: [x0, y0, x1, y1].")

    x0, y0, x1, y1 = rect
    w = x1 - x0
    h = y1 - y0

    if w < 0 or h < 0:
        raise ValueError("Invalid rectangle dimensions: width and height must be non-negative.")

    return [x0, y0, w, h]


def standardize_triangle_vertices(triangle: np.ndarray) -> np.ndarray:
    """
    Standardizes the order of the vertices of a triangle.

    Args:
        triangle (np.ndarray): Triangle represented as a numpy array of shape (3, 2).

    Returns:
        np.ndarray: Triangle with vertices ordered as [p0, p1, p2].
    """
    distances = np.linalg.norm(triangle, axis=1)
    p0_index = np.argmin(distances)
    p0 = triangle[p0_index]
    remaining_points = np.delete(triangle, p0_index, axis=0)

    angles = np.arctan2(remaining_points[:, 1] - p0[1], remaining_points[:, 0] - p0[0])
    sorted_indices = np.argsort(angles)[::-1]
    p1, p2 = remaining_points[sorted_indices]

    return np.array([p0, p1, p2])


def order_triangles(triangles: [np.ndarray], image_shape: [int] = None, img_center=None) -> np.ndarray:
    """
    Orders triangles based on their position relative to the center of the image.

    Args:
        triangles (list[np.ndarray]): List of standardized triangles.
        image_shape (tuple, optional): Shape of the original image as (height, width).
        img_center (tuple, optional): Center of the image as (x, y).

    Returns:
        np.ndarray: Ordered list of triangles.
    """
    if img_center is None:
        if image_shape is None:
            raise ValueError("For order_triangles, image_shape or img_center must not be None.")
        img_center = np.array([image_shape[1] / 2, image_shape[0] / 2])

    def triangle_position_score(triangle: np.ndarray) -> int:
        p0 = triangle[0]
        if p0[0] <= img_center[0] and p0[1] > img_center[1]:
            return 0
        elif p0[0] <= img_center[0] and p0[1] <= img_center[1]:
            return 1
        elif p0[0] > img_center[0] and p0[1] <= img_center[1]:
            return 2
        else:
            return 3

    triangles.sort(key=triangle_position_score)
    return np.array(triangles)


def calculate_square_means(mat: np.ndarray, regions: np.ndarray | list[list], decimals: int = 1) -> np.ndarray:
    """
    Calculates the mean values in square regions defined by coordinates.

    Args:
        mat (np.ndarray): 2D array containing input values.
        regions (np.ndarray or list[list]): List of regions defined as [x0, y0, x1, y1].
        decimals (int, optional): Number of decimal places to round the result. Defaults to 1.

    Returns:
        np.ndarray: Array of mean values for each region.
    """
    means = [
        mat[y0:y1 + 1, x0:x1 + 1].mean()
        for (x0, y0, x1, y1) in regions
    ]

    return np.around(np.array(means), decimals)


def find_corners_of_polydp2(contour):
    """
    Finds the four corners of a rectangle given a contour.

    Parameters:
        contour (numpy.ndarray): Input contour (shape: [n_points, 1, 2]).

    Returns:
        list of tuple: List of four corners as (x, y) coordinates.
    """
    # Extrai todos os pontos do contorno
    points = contour.reshape(-1, 2)  # Shape agora será (n_points, 2)

    # Encontra os extremos (mínimos e máximos de x e y)
    x_min = np.min(points[:, 0])
    x_max = np.max(points[:, 0])
    y_min = np.min(points[:, 1])
    y_max = np.max(points[:, 1])

    # Define os vértices do retângulo
    corners = [
        (x_min, y_min),  # Top-left
        (x_min, y_max),  # Bottom-left
        (x_max, y_min),  # Top-right
        (x_max, y_max),  # Bottom-right
    ]

    return corners


def find_strongest_white_line_in_image(image):
    """
    Finds the main white rectangle closest to the center of the image.

    Parameters:
        image (numpy.ndarray): Input image in grayscale.

    Returns:
        tuple or None: Coordinates of the rectangle's bounding box (x, y, w, h) or None if no rectangle is found.
    """
    # Find contours of the white regions
    contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        image_center = (image.shape[1] // 2, image.shape[0] // 2)  # (cx, cy)
        main_rectangle = None
        min_distance_to_center = float('inf')

        for contour in contours:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 2:
                # Calculate the center of the contour
                # Calculate the Euclidean distance to the image center
                # Update the main rectangle if it's closer to the center
                center = contour_center(contour)
                distance_to_center = point_distance(center, image_center)
                if distance_to_center < min_distance_to_center:
                    min_distance_to_center = distance_to_center
                    main_rectangle = contour

        points = find_corners_of_polydp2(main_rectangle)
        result_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        for p in points:
            cv2.circle(result_image, p, 3, (0, 0, 255), -1)
        # # If a rectangle was found, highlight its corners
        # if main_rectangle is not None:
        #     result_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        #     for point in main_rectangle:
        #         x, y = point[0]
        #         cv2.circle(result_image, (x, y), 10, (0, 255, 0), -1)  # Draw a filled circle at each corner
        #     debug_show_image(result_image)
        #     return [tuple(pt[0]) for pt in main_rectangle]  # Return the corner points

    return None


def find_strongest_white_lines(image, rectangles_xywh):
    """
    Finds the strongest white line in each of the specified rectangles in the image.

    Parameters:
        image (numpy.ndarray): Input image in grayscale.
        rectangles_xywh (list of tuples): List of rectangles, each defined as (x, y, width, height).

    Returns:
        list of tuples: List of line coordinates [(x1, y1, x2, y2), ...] for the strongest white line in each rectangle, or None if no line is found.
    """
    strongest_lines = []
    for rect in rectangles_xywh:
        x, y, w, h = rect
        # Extract the region of interest (ROI)
        roi = image[y:y+h, x:x+w]
        # Find the strongest white line in the ROI
        line = find_strongest_white_line_in_image(roi)
        if line:
            # Adjust coordinates relative to the full image
            x1, y1, x2, y2 = line
            strongest_lines.append((x1 + x, y1 + y, x2 + x, y2 + y))
        else:
            strongest_lines.append(None)

    return strongest_lines


def bounding_rectangle(triangle_coords: np.ndarray) -> np.ndarray:
    """
    Calculates the smallest rectangle that contains a triangle.

    Parameters:
        triangle_coords (numpy.ndarray): Array of shape (3, 2) containing the triangle's vertex coordinates (X, Y).

    Returns:
        numpy.ndarray: Array of shape (2, 2) containing the rectangle's coordinates: [[x_min, y_min], [x_max, y_max]].
    """
    if triangle_coords.shape != (3, 2):
        raise ValueError("Input array must have shape (3, 2).")

    # Find the bounds
    min_coords = np.min(triangle_coords, axis=0)  # Minimum x and y
    max_coords = np.max(triangle_coords, axis=0)  # Maximum x and y

    # Return bottom-left and top-right corners as a numpy array
    return np.array([min_coords, max_coords])


def enclosing_rectangle(rect1: np.ndarray, rect2: np.ndarray) -> np.ndarray:
    """
    Calculates the smallest rectangle that contains two given rectangles.

    Args:
        rect1 (np.ndarray): Array of shape (2, 2) containing the first rectangle's coordinates: [[x1_min, y1_min], [x1_max, y1_max]].
        rect2 (np.ndarray): Array of shape (2, 2) containing the second rectangle's coordinates: [[x2_min, y2_min], [x2_max, y2_max]].

    Returns:
        np.ndarray: Array of shape (2, 2) containing the enclosing rectangle's coordinates: [[x_min, y_min], [x_max, y_max]].

    Raises:
        ValueError: If the input rectangles do not have the correct shape (2, 2).
    """
    if rect1.shape != (2, 2) or rect2.shape != (2, 2):
        raise ValueError("Both input rectangles must have shape (2, 2).")

    combined = np.vstack((rect1, rect2))
    min_coords = np.min(combined, axis=0)
    max_coords = np.max(combined, axis=0)

    return np.array([min_coords, max_coords])


def relative_path(file_name, current):
    """
    Generates the absolute path to a file, relative to the directory where this script is located.

    Args:
        file_name (str): Name or relative path of the target file.
        current (str): Current script's __file__ path.

    Returns:
        pathlib.Path: Absolute path to the target file.
    """
    script_dir = Path(current).parent
    path = script_dir / file_name
    return path
