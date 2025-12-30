import cv2
import numpy as np

from .align_verifier import AlignVerifier
from .border_recognizer import find_white_triangles, filter_triangles
from .debug import debug_show_image
from .errors import FoundAlignTrianglesAreNotFilledException
from .image_grid_warp import MultiPointWarp
from .normalizer import ImageNormalizer
from .structures import ExtractedData
from .template_matcher import TemplateMatcher
from .utils import reorder_warped_triangle


class Recognizer:

    def __init__(self, matcher: TemplateMatcher, shadow=True):
        """
        Initializes the Recognizer class with a template matcher and shadow removal option.

        Args:
            matcher (TemplateMatcher): Template matcher to use for triangle and shape alignment.
            shadow (bool, optional): Whether to remove shadows during normalization. Defaults to True.
        """
        self.matcher = matcher
        self.target_triangles = matcher.get_triangles()
        self.template_shape = matcher.get_image_shape()
        self.shadow = shadow

    def _warp_image_by_points(self, img: np.ndarray, triangles_cords: np.ndarray, target_triangles: np.ndarray) -> np.ndarray:
        """
        Warps the input image to align its triangles with the target triangles.

        Args:
            img (np.ndarray): Input image to warp.
            triangles_cords (np.ndarray): Coordinates of the detected triangles.
            target_triangles (np.ndarray): Target triangle coordinates for alignment.

        Returns:
            np.ndarray: Warped image.
        """
        src_points = triangles_cords.reshape(-1, 2)
        dst_points = target_triangles.reshape(-1, 2)
        warper = MultiPointWarp(img, src_points, dst_points)
        warped_img = warper.align_and_crop(self.template_shape)
        return warped_img

    def _warp_image_by_points_and_verify(self, img: np.ndarray, triangles_contour: [np.ndarray], triangles_cords: np.ndarray, first_pass=True) -> np.ndarray:
        """
        Warps an image by aligning its triangles to target triangles and verifies the process.

        Args:
            img (np.ndarray): Input image.
            triangles_contour (list[np.ndarray]): Contours of the detected triangles.
            triangles_cords (np.ndarray): Coordinates of the detected triangles.

        Returns:
            np.ndarray: Warped and verified image.

        Raises:
            FoundAlignTrianglesAreNotFilledException: If the warped image does not satisfy alignment checks.
        """
        try:
            AlignVerifier.verify_triangles_contour_found(img, triangles_contour)
            warped_img = self._warp_image_by_points(img, triangles_cords, self.target_triangles)
            AlignVerifier.verify_triangles_from_coordinates(warped_img, self.target_triangles)
        except FoundAlignTrianglesAreNotFilledException:
            triangles_cords = np.array([
                reorder_warped_triangle(orig, tri) for (orig, tri) in zip(self.target_triangles, triangles_cords)
            ])
            warped_img = self._warp_image_by_points(img, triangles_cords, self.target_triangles)

            try:
                AlignVerifier.verify_triangles_from_coordinates(warped_img, self.target_triangles)
            except FoundAlignTrianglesAreNotFilledException as e:
                if not first_pass:
                    raise e

                # Attempt one last trick
                warped_img = cv2.copyMakeBorder(warped_img, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=(0, 0, 0))
                warped_img = self._warp_image_by_points_and_verify(warped_img, triangles_contour, triangles_cords, first_pass=False)

        return warped_img

    def _normalize_and_align_by_triangles(self, img: np.ndarray) -> np.ndarray:
        """
        Normalizes and aligns an image based on detected triangles.

        Args:
            img (np.ndarray): Input image to normalize and align.

        Returns:
            np.ndarray: Warped and normalized image.
        """
        # Normalize the image and find triangles
        img = ImageNormalizer.normalize_image(img, shadow=self.shadow)
        triangles_cords, triangles_contour = find_white_triangles(img, min_area=200)
        triangles_cords = filter_triangles(triangles_cords, img.shape)

        warped_img = self._warp_image_by_points_and_verify(img, triangles_contour, triangles_cords)

        return warped_img

    # def _align_by_reference_lines(self, img) -> np.ndarray:
    #     """
    #     Aligns the image by reference lines.
    #
    #     Parameters:
    #         img (numpy.ndarray): Input image in grayscale.
    #
    #     Returns:
    #         numpy.ndarray: The aligned image.
    #     """
    #     # Convert image to BGR to allow colored drawings
    #     img_color = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    #
    #     # Canto inferior esquerdo, superior esquerdo, superior direito, inferior direito.
    #     boundings = [bounding_rectangle(t) for t in self.target_triangles]
    #
    #     # Calculate enclosing rectangles
    #     top_rect = enclosing_rectangle(boundings[1], boundings[2])
    #     bottom_rect = enclosing_rectangle(boundings[0], boundings[3])
    #     left_rect = enclosing_rectangle(boundings[0], boundings[1])
    #     right_rect = enclosing_rectangle(boundings[2], boundings[3])
    #
    #     # Order here is important
    #     rectangles_xywh = [rect_to_xywh(r) for r in [top_rect, bottom_rect, left_rect, right_rect]]
    #
    #     found_lines = find_strongest_white_lines(img, rectangles_xywh)
    #     print(found_lines)
    #
    #     # Draw enclosing rectangles in a different shade of blue
    #     for rect in found_lines:
    #         if rect:
    #             x0, y0, x1, y1 = np.array(rect).astype(int)
    #             cv2.rectangle(img_color,
    #                           (x0, y0),
    #                           (x1, y1),
    #                           color=(0, 0, 255),  # Purple-ish blue in BGR
    #                           thickness=6)
    #
    #     debug_show_image(img_color)
    #
    #     return img_color

    def correct(self, img: np.ndarray, correct_indexes: [int]) -> ExtractedData:
        """
        Corrects the input image based on the provided indexes using the matcher.

        Args:
            img (np.ndarray): Input image to correct.
            correct_indexes (list[int]): List of indexes for correction.

        Returns:
            ExtractedData: The corrected data extracted from the image.
        """
        img = self._normalize_and_align_by_triangles(img)
        # img = self._align_by_reference_lines(img)
        return self.matcher.correct(img, correct_indexes)
