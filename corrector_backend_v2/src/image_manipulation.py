import cv2
import numpy as np

from .constants import MEDIAN_BLUR, BGR_BLACK, BGR_WHITE
from .json_handler import KEY_Y0, KEY_X1, KEY_Y1, KEY_X0, KEY_CHECKBOXES, KEY_CONTENT


def resize_to_vertical_fit(img: np.ndarray, screen_height: int) -> np.ndarray:
    """
    Resize an image to fit verticaly within a given screen height.

    Parameters:
        img (numpy.ndarray): The input image.
        screen_height (int): The height of the screen.

    Returns:
        numpy.ndarray: The resized image.
    """
    target_height = round(screen_height * 0.9)
    width, height = img.shape[1], img.shape[0]
    aspect = target_height / height
    target_width = round(width * aspect)
    return cv2.resize(img, (target_width, target_height))


def resize_to_horizontal_fit(img: np.ndarray, screen_width: int) -> np.ndarray:
    """
    Resize an image to fit horizontally within a given screen width.

    Parameters:
        img (np.ndarray): The input image.
        screen_width (int): The width of the screen.

    Returns:
        numpy.ndarray: The resized image.
    """
    target_width = round(screen_width * 0.9)
    width, height = img.shape[1], img.shape[0]
    aspect = target_width / width
    target_height = round(height * aspect)
    return cv2.resize(img, (target_width, target_height))


def resize_to_fit(img: np.ndarray, screen_width: int = 1200, screen_height: int = 1000) -> np.ndarray:
    """
    Resize an image to fit within a given screen's width and height,
    maintaining the aspect ratio. Resizes horizontally or vertically as needed.

    Parameters:
        img (np.ndarray): The input image.
        screen_width (int): The width of the screen.
        screen_height (int): The height of the screen.

    Returns:
        np.ndarray: The resized image.
    """
    width, height = img.shape[1], img.shape[0]

    # Check if resizing is necessary
    if width > screen_width * 0.9:
        img = resize_to_horizontal_fit(img, screen_width)

    # After horizontal resizing, check vertical dimension
    if img.shape[0] > screen_height * 0.9:
        img = resize_to_vertical_fit(img, screen_height)

    return img


def remove_shadow(img: np.ndarray) -> np.ndarray:
    """
    Removes shadow from an image using dilation, blurring, and normalization.

    Args:
        img (np.ndarray): Input image from which shadows will be removed.

    Returns:
        np.ndarray: Image with reduced shadows.
    """
    def dilate_blur_norm(img_: np.ndarray) -> np.ndarray:
        """
        Applies dilation, median blurring, and normalization to enhance the image.

        Args:
            img_ (np.ndarray): Single channel image to process.

        Returns:
            np.ndarray: Processed image with reduced shadow effects.
        """
        img_dilated = cv2.dilate(img_, np.ones((7, 7), np.uint8))
        img_blured = cv2.medianBlur(img_dilated, MEDIAN_BLUR)
        img_diff = 255 - cv2.absdiff(img_, img_blured)
        img_norm = cv2.normalize(img_diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        return img_norm

    channels = cv2.split(img)
    return cv2.merge([dilate_blur_norm(ch) for ch in channels])


def offset_image(img: np.ndarray, off_x: int, off_y: int) -> np.ndarray:
    """
    Shifts an image by a specified offset, filling empty areas with black.

    Args:
        img (np.ndarray): Input image to shift.
        off_x (int): Horizontal offset. Positive values shift right, negative values shift left.
        off_y (int): Vertical offset. Positive values shift down, negative values shift up.

    Returns:
        np.ndarray: Shifted image with empty areas filled with black.
    """
    img = np.roll(img, off_y, axis=0)
    img = np.roll(img, off_x, axis=1)

    if off_y > 0:
        img[:off_y, :] = 0
    elif off_y < 0:
        img[off_y:, :] = 0

    if off_x > 0:
        img[:, :off_x] = 0
    elif off_x < 0:
        img[:, off_x:] = 0

    return img


def in_place_draw_checkboxes(cell: dict, img_res: np.ndarray, is_selected_mask: np.ndarray[bool], color: (int, int, int), radius: int = 9):
    """
    Processes checkboxes within a cell, drawing shapes on the image to represent
    their selection state and bounding boxes.

    Args:
        cell (dict): A dictionary containing checkbox data. Must include a key specified by `KEY_CHECKBOXES`.
        img_res (numpy.ndarray): The image on which to draw.
        is_selected_mask (list of bool): A list where each boolean indicates if the corresponding checkbox is selected.
        color (tuple): The RGB color for the final rectangle and center circle.
        radius (tuple): The BGR color representing black.

    Returns:
        None: Modifies the input `img_res` in-place to draw shapes on it.
    """
    # Sort checkboxes by the content key
    checkboxes = sorted(cell[KEY_CHECKBOXES], key=lambda e: e[KEY_CONTENT])

    for checkbox_index, checkbox in enumerate(checkboxes):
        x0, y0, x1, y1 = checkbox[KEY_X0], checkbox[KEY_Y0], checkbox[KEY_X1], checkbox[KEY_Y1]

        # Draw selection marker if the checkbox is selected
        if is_selected_mask[checkbox_index]:
            center = ((x0 + x1) // 2, (y0 + y1) // 2)
            cv2.circle(img_res, center, radius, BGR_BLACK, 8)
            cv2.circle(img_res, center, radius, BGR_WHITE, 6)
            cv2.circle(img_res, center, radius, color, 4)

        # Draw bounding boxes
        cv2.rectangle(img_res, (x0, y0), (x1, y1), BGR_BLACK, 10)
        cv2.rectangle(img_res, (x0, y0), (x1, y1), BGR_WHITE, 8)
        cv2.rectangle(img_res, (x0, y0), (x1, y1), color, 6)
