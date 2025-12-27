import cv2
import numpy as np


class MultiPointWarp:
    def __init__(self, img_orig: np.ndarray, orig_points: np.ndarray, template_points: np.ndarray):
        """
        Initializes the MultiPointWarp class.

        Args:
            img_orig (np.ndarray): Original distorted image.
            orig_points (np.ndarray): Points in the original image.
            template_points (np.ndarray): Points in the reference image.
        """
        self.img_orig = img_orig
        self.orig_points = orig_points
        self.template_points = template_points

    def compute_homography(self) -> np.ndarray:
        """
        Calculates the homography matrix between the points in the original image and the template.

        Returns:
            np.ndarray: Homography matrix.
        """
        h, _ = cv2.findHomography(self.orig_points, self.template_points, method=cv2.RANSAC)
        return h

    def align_and_crop(self, output_size: tuple) -> np.ndarray:
        """
        Complete process of realignment and cropping of the original image.

        Args:
            output_size (tuple): Size of the output transformed image (width, height).

        Returns:
            np.ndarray: Aligned and cropped portion of the original image.
        """
        h = self.compute_homography()
        warped_img = cv2.warpPerspective(self.img_orig, h, output_size)
        return warped_img
