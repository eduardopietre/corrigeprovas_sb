import cv2
import numpy as np

from .errors import UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException


class AlignVerifier:

    @staticmethod
    def verify_triangles_contour_found(img: np.ndarray, triangles_contour: np.ndarray, min_threshold: int = 200):
        """
        Verifies the validity of detected contours representing aligned triangles in an image.

        This function checks if exactly 4 triangles were found in the image and whether each triangle is filled
        (with average pixel values above a specified threshold). If conditions are not met, custom exceptions are raised.

        Parameters:
        ----------
        img : np.ndarray
            The input image where contours were detected. Must be a 2D array representing a grayscale image.

        triangles_contour : np.ndarray
            A list or array containing the detected triangle contours. Each contour should be represented as an OpenCV coordinate array.

        min_threshold : int, optional
            The minimum average pixel value expected to consider triangles as "filled".
            Default is 200, indicating that the triangle area should be close to white.

        Raises:
        ------
        UnableToFindFourAlignTrianglesException
            If the number of provided contours is not exactly 4.

        FoundAlignTrianglesAreNotFilledException
            If the average pixel values for any contour are below the threshold defined by `min_threshold`.

        Notes:
        ------
        - The function assumes the provided contours are related to triangles and the image is grayscale.
        - The average pixel value is calculated for each contour using a binary mask filled with the contour.
        """
        if len(triangles_contour) != 4:
            raise UnableToFindFourAlignTrianglesException(img, len(triangles_contour))

        for contour in triangles_contour:
            mask = np.zeros_like(img)
            cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
            mean_val = cv2.mean(img, mask=mask)[0]

            # mean_val is expected to be close to 255.
            if mean_val < min_threshold:
                raise FoundAlignTrianglesAreNotFilledException(img, mean_val, min_threshold)

    @staticmethod
    def verify_triangles_from_coordinates(img: np.ndarray, triangles: [np.ndarray], min_threshold: int = 200):
        """
        Verifies the validity of triangles represented by coordinates in an image.

        Parameters:
        ----------
        img : np.ndarray
            The input image where triangles were defined. Must be a 2D array representing a grayscale image.

        triangles : list of np.ndarray
            A list containing the triangles. Each triangle is represented by an array of 3 coordinate pairs (X, Y).

        min_threshold : int, optional
            The minimum average pixel value expected to consider triangles as "filled".
            Default is 200, indicating that the triangle area should be close to white.

        Raises:
        ------
        UnableToFindFourAlignTrianglesException
            If the number of provided triangles is not exactly 4.

        FoundAlignTrianglesAreNotFilledException
            If the average pixel values for any triangle are below the threshold defined by `min_threshold`.

        Notes:
        ------
        - The function assumes the triangles are related to regions in the image and the image is grayscale.
        - The average pixel value is calculated for each triangle using a binary mask filled with the triangle.
        """
        if len(triangles) != 4:
            raise UnableToFindFourAlignTrianglesException(img, len(triangles))

        for triangle in triangles:
            mask = np.zeros_like(img, dtype=np.uint8)
            points = np.array(triangle, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
            mean_val = cv2.mean(img, mask=mask)[0]

            if mean_val < min_threshold:
                raise FoundAlignTrianglesAreNotFilledException(img, mean_val, min_threshold)
