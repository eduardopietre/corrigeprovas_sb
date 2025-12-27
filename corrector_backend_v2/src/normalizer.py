import cv2
import numpy as np

from .structures import CorrectorModels
from .image_manipulation import remove_shadow, offset_image
from .utils import relative_path


class ImageNormalizer:
    @staticmethod
    def __find_vertexes(contour):
        """
        Finds the vertexes of a contour using the Douglas-Peucker algorithm.

        Args:
            contour (np.ndarray): Contour points.

        Returns:
            np.ndarray: Approximated vertexes of the contour.
        """
        length = cv2.arcLength(contour, True)
        vertexes = cv2.approxPolyDP(contour, 0.02 * length, True)
        return vertexes

    @staticmethod
    def __find_rectangles(contours: [np.ndarray], min_area: int = 20000) -> [np.ndarray]:
        """
        Finds rectangles among a list of contours.

        Args:
            contours (list[np.ndarray]): List of contours.
            min_area (int, optional): Minimum area to consider a rectangle. Defaults to 20000.

        Returns:
            list[np.ndarray]: Sorted list of rectangle contours by area in descending order.
        """
        rectangles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                vertices = ImageNormalizer.__find_vertexes(contour)
                if len(vertices) == 4:  # 4 = rectangle
                    rectangles.append(contour)
        return sorted(rectangles, key=cv2.contourArea, reverse=True)

    @staticmethod
    def __sort_points(points: np.ndarray) -> np.ndarray:
        """
        Sorts the four points of a rectangle into a consistent order: top-left, top-right, bottom-right, bottom-left.

        Args:
            points (np.ndarray): Four points to be sorted.

        Returns:
            np.ndarray: Sorted points.
        """
        points = points.reshape((4, 2))
        sorted_points = np.zeros((4, 1, 2), np.int32)
        total = points.sum(axis=1)
        sorted_points[0] = points[np.argmin(total)]  # Top-left
        sorted_points[3] = points[np.argmax(total)]  # Bottom-right
        diff = np.diff(points, axis=1)
        sorted_points[1] = points[np.argmin(diff)]  # Top-right
        sorted_points[2] = points[np.argmax(diff)]  # Bottom-left
        return sorted_points

    @staticmethod
    def __cut_border(img: np.ndarray, factor: float) -> np.ndarray:
        """
        Crops the image by a given factor around its center.

        Args:
            img (np.ndarray): Input image.
            factor (float): Factor to crop (0.0 to 1.0).

        Returns:
            np.ndarray: Cropped image.
        """
        width, height = img.shape[1], img.shape[0]
        width_crop = width * factor if width * factor < img.shape[1] else img.shape[1]
        height_crop = height * factor if height * factor < img.shape[0] else img.shape[0]
        mid_x, mid_y = int(width / 2), int(height / 2)
        cw2, ch2 = int(width_crop / 2), int(height_crop / 2)
        img_cropped = img[mid_y - ch2:mid_y + ch2, mid_x - cw2:mid_x + cw2]
        return img_cropped

    @staticmethod
    def __find_greater_rectangle_and_vertexes(img_binary: np.ndarray) -> [np.ndarray, np.ndarray]:
        """
        Finds the largest rectangle and its vertexes in a binary image.

        Args:
            img_binary (np.ndarray): Binary image.

        Returns:
            tuple[np.ndarray, np.ndarray]: Largest rectangle contour and its sorted vertexes.
        """
        contours, _ = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        greater_rectangle = ImageNormalizer.__find_rectangles(contours)[0]

        vertexes = ImageNormalizer.__find_vertexes(greater_rectangle)
        vertexes = ImageNormalizer.__sort_points(vertexes)

        vertexes_f32 = np.float32(vertexes)
        return greater_rectangle, vertexes_f32

    @staticmethod
    def __warp_greater_rectangle(img_binary: np.ndarray, vertexes_f32: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Warps the largest rectangle in the binary image to a specified size.

        Args:
            img_binary (np.ndarray): Binary input image.
            vertexes_f32 (np.ndarray): Vertex points of the rectangle.
            width (int): Target width.
            height (int): Target height.

        Returns:
            np.ndarray: Warped image without borders.
        """
        templated_rectangle = np.float32([
            [0, 0],
            [width, 0],
            [0, height],
            [width, height]
        ])
        perspective_transform = cv2.getPerspectiveTransform(vertexes_f32, templated_rectangle)

        img_warped = cv2.warpPerspective(img_binary, perspective_transform, (width, height))
        img_without_border = ImageNormalizer.__cut_border(img_warped, 0.99)

        return img_without_border

    @staticmethod
    def __find_and_warp_routine(img_binary: np.ndarray, thickness: int, width: int, height: int) -> (np.ndarray, np.ndarray):
        """
        Finds the largest rectangle in the binary image, removes it, and warps it to the specified size.

        Args:
            img_binary (np.ndarray): Binary input image.
            thickness (int): Thickness of the contour removal.
            width (int): Target width for warping.
            height (int): Target height for warping.

        Returns:
            tuple[np.ndarray, np.ndarray]: The largest rectangle contour and the warped image.
        """
        greater_rectangle, vertexes_f32 = ImageNormalizer.__find_greater_rectangle_and_vertexes(img_binary)
        cv2.drawContours(img_binary, [greater_rectangle], -1, (0, 0, 0), thickness)

        warped_greatest = ImageNormalizer.__warp_greater_rectangle(img_binary, vertexes_f32, width, height)
        return greater_rectangle, warped_greatest

    @staticmethod
    def __improve_thin_digits(warped_second: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Enhances thin digits by combining adaptive thresholding and offsetting.

        Args:
            warped_second (np.ndarray): Warped input image.
            width (int): Target width for resizing.
            height (int): Target height for resizing.

        Returns:
            np.ndarray: Enhanced image.
        """
        binary_image = cv2.adaptiveThreshold(
            warped_second, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 3, 2
        )

        fused = np.maximum(warped_second, binary_image)
        fused = cv2.resize(fused, (width, height))

        with_offset = offset_image(fused, 1, -1)
        result = np.maximum(fused, with_offset)
        return result

    @staticmethod
    def normalize_image(img: np.ndarray, shadow=True) -> np.ndarray:
        """
        Normalizes an image by removing shadows and converting it to a binary format.

        Args:
            img (np.ndarray): Input image.
            shadow (bool, optional): Whether to remove shadows. Defaults to True.

        Returns:
            np.ndarray: Binary normalized image.
        """
        img_no_shadow = remove_shadow(img) if shadow else img
        img_grayscale = cv2.cvtColor(img_no_shadow, cv2.COLOR_BGR2GRAY)
        img_binary = cv2.threshold(img_grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        return img_binary

    @staticmethod
    def normalize_responses_and_identifier_numbers(img: np.ndarray, model: CorrectorModels) -> (np.ndarray, np.ndarray):
        """
        Normalizes responses and identifier numbers from an image using a specified model.

        Args:
            img (np.ndarray): Input image.
            model (CorrectorModels): Model specifying dimensions and processing details.

        Returns:
            tuple[np.ndarray, np.ndarray]: Warped greatest rectangle and processed second rectangle.
        """
        img = cv2.resize(img, (1500, 2000))

        img_no_shadow = remove_shadow(img)
        img_grayscale = cv2.cvtColor(img_no_shadow, cv2.COLOR_BGR2GRAY)
        img_blured = cv2.GaussianBlur(img_grayscale, (3, 3), 5)
        img_binary = cv2.threshold(img_blured, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Warp greater rectangle
        greater_rectangle, warped_greatest = ImageNormalizer.__find_and_warp_routine(img_binary, 16,
                                                                                     *model.model_size())

        # Remove the greater rectangle
        cv2.drawContours(img_binary, [greater_rectangle], -1, (0, 0, 0), 32)

        warped_second = np.zeros((3, 3, 3))
        # TODO: Implement second rectangle.
        # # Warp the second rectangle
        # # Upper scale it by 3 so adaptiveThreshold in __improve_thin_digits works best, it will be resized back.
        # width, height = model.secondary_rectangle_size()
        # _, warped_second = ImageNormalizer.__find_and_warp_routine(img_binary, 20, width * 3, height * 3)
        # warped_second = ImageNormalizer.__improve_thin_digits(warped_second, width, height)

        return warped_greatest, warped_second

    @staticmethod
    def create_border(image: np.ndarray, pad=20, color=0) -> np.ndarray:
        """
        Adds a border of specified padding and color around the image.

        Args:
            image (np.ndarray): Grayscale input image.
            pad (int, optional): Padding size. Defaults to 20.
            color (int, optional): Border color. Defaults to 0 (black).

        Returns:
            np.ndarray: Image with added border.
        """
        if len(image.shape) > 2:
            raise ValueError("The image must be in grayscale (black and white).")

        bordered_image = cv2.copyMakeBorder(
            image,
            top=pad, bottom=pad, left=pad, right=pad,
            borderType=cv2.BORDER_CONSTANT,
            value=color
        )
        return bordered_image


def load_image(image: str, normalize=True) -> np.ndarray:
    """
    Loads an image from the specified path and optionally normalizes it.

    Args:
        image (str): Name of the image to load.
        normalize (bool, optional): Whether to normalize the image. Defaults to True.

    Returns:
        np.ndarray: Loaded image.
    """
    path = relative_path(f"../generated/{image}.png", __file__)
    img = cv2.imread(path)
    if normalize:
        img = ImageNormalizer.normalize_image(img, shadow=False)
    return img
