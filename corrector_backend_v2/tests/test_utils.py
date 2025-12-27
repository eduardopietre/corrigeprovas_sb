import unittest

import cv2
import numpy as np

from ..src.utils import point_distance, calculate_center_xy, standardize_triangle_vertices, order_triangles, \
    calculate_square_means, find_strongest_white_line_in_image, find_strongest_white_lines, bounding_rectangle, \
    enclosing_rectangle, reorder_warped_triangle


class TestGeometryFunctions(unittest.TestCase):
    def test_point_distance(self):
        self.assertAlmostEqual(point_distance((0, 0), (3, 4)), 5.0)
        self.assertAlmostEqual(point_distance((1, 1), (4, 5)), 5.0)
        self.assertAlmostEqual(point_distance((4, 5), (1, 1)), 5.0)
        self.assertAlmostEqual(point_distance((0, 0), (0, 0)), 0.0)

    def test_calculate_center_xy(self):
        points = np.array([[0, 0], [2, 2], [4, 4]])
        expected = np.array([2, 2])
        result = calculate_center_xy(points)
        np.testing.assert_array_almost_equal(expected, result)

        points = np.array([[1, 1], [3, 3]])
        expected = np.array([2, 2])
        result = calculate_center_xy(points)
        np.testing.assert_array_almost_equal(expected, result)

    def test_standardize_triangle_vertices(self):
        triangle = np.array([[1, 3], [4, 1], [0, 0]])
        expected = np.array([[0, 0], [1, 3], [4, 1]])
        result = standardize_triangle_vertices(triangle)
        np.testing.assert_array_almost_equal(result, expected)

        triangle = np.array([[2, 2], [0, 0], [1, 3]])
        expected = np.array([[0, 0], [1, 3], [2, 2]])
        result = standardize_triangle_vertices(triangle)
        np.testing.assert_array_almost_equal(result, expected)

    def test_order_triangles(self):
        triangles = [
            np.array([[8, 0], [9, 1], [10, 2]]),  # Superior direito
            np.array([[8, 6], [9, 7], [10, 8]]),  # Inferior direito
            np.array([[0, 6], [2, 7], [1, 8]]),   # Inferior esquerdo
            np.array([[0, 0], [1, 1], [2, 2]]),   # Superior esquerdo
        ]
        image_shape = (10, 10)
        expected = [
            np.array([[0, 6], [2, 7], [1, 8]]),
            np.array([[0, 0], [1, 1], [2, 2]]),
            np.array([[8, 0], [9, 1], [10, 2]]),
            np.array([[8, 6], [9, 7], [10, 8]])
        ]
        result = order_triangles(triangles, image_shape=image_shape)
        for exp, res in zip(expected, result):
            np.testing.assert_array_almost_equal(exp, res)

        with self.assertRaises(ValueError):
            order_triangles(triangles, image_shape=None, img_center=None)


class TestCalculateSquareMeans(unittest.TestCase):
    def test_single_square(self):
        matrix = np.array([
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 16]
        ])
        regions = np.array([[1, 0, 2, 1]])
        expected = [4.5]
        result = calculate_square_means(matrix, regions)
        np.testing.assert_array_almost_equal(expected, result)

    def test_multiple_squares(self):
        matrix = np.array([
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 16]
        ])
        regions = np.array([
            [0, 0, 1, 1],
            [2, 2, 3, 3]
        ])
        expected = [3.5, 13.5]
        result = calculate_square_means(matrix, regions)
        np.testing.assert_array_almost_equal(expected, result)

    def test_large_matrix(self):
        matrix = np.random.randint(0, 100, size=(10, 10))
        regions = np.array([
            [2, 0, 4, 2],
            [5, 3, 7, 5]
        ])
        result = calculate_square_means(matrix, regions)
        for r in result:
            self.assertIsInstance(r, float)  # Garantir que o resultado são floats

    def test_empty_region(self):
        matrix = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        regions = np.array([[0, 0, 0, 0]])  # Um único ponto na matriz
        expected = [1.0]
        result = calculate_square_means(matrix, regions)
        self.assertEqual(result, expected)


class TestFindStrongestWhiteLine(unittest.TestCase):

    def setUp(self):
        """
        Prepare test images and data for the test cases.
        """
        # Create a blank black image
        self.blank_image = np.zeros((200, 200), dtype=np.uint8)

        # Add a horizontal white line
        self.image_with_line = self.blank_image.copy()
        cv2.line(self.image_with_line, (50, 100), (150, 100), (255, 255, 255), 2)

        # Add multiple lines
        self.image_with_multiple_lines = self.blank_image.copy()
        cv2.line(self.image_with_multiple_lines, (10, 50), (190, 50), (255, 255, 255), 2)  # Strong white line
        cv2.line(self.image_with_multiple_lines, (50, 150), (150, 150), (200, 200, 200), 2)  # Weak white line

        # Divide into regions (ROIs)
        self.rectangles = [
            (0, 0, 100, 100),
            (100, 100, 100, 100),
            (0, 100, 100, 100),
            (100, 0, 100, 100)
        ]

    def test_find_strongest_white_line_in_image_single_line(self):
        """
        Test that the function detects the strongest white line in an image with a single white line.
        """
        line = find_strongest_white_line_in_image(self.image_with_line)
        self.assertIsNotNone(line, "Should detect a white line.")
        self.assertEqual((49, 101, 151, 101), line, "Detected line should match the expected coordinates.")

    def test_find_strongest_white_line_in_image_no_line(self):
        """
        Test that the function returns None when no white lines are present in the image.
        """
        line = find_strongest_white_line_in_image(self.blank_image)
        self.assertIsNone(line, "Should return None when no white lines are present.")

    def test_find_strongest_white_line_in_image_multiple_lines(self):
        """
        Test that the function detects the strongest white line in an image with multiple white lines.
        """
        line = find_strongest_white_line_in_image(self.image_with_multiple_lines)
        self.assertIsNotNone(line, "Should detect a white line.")
        self.assertEqual((9, 51, 191, 51), line, "Should detect the strongest white line.")

    def test_find_strongest_white_lines(self):
        """
        Test that the function detects the strongest white line in each rectangle of an image.
        """
        # Add different lines in regions
        test_image = self.blank_image.copy()
        cv2.line(test_image, (20, 20), (80, 80), (255, 255, 255), 2)  # Line in first rectangle
        cv2.line(test_image, (120, 120), (180, 180), (255, 255, 255), 2)  # Line in second rectangle
        cv2.line(test_image, (20, 120), (80, 180), (255, 255, 255), 2)  # Line in third rectangle

        # Convert to grayscale
        strongest_lines = find_strongest_white_lines(test_image, self.rectangles)

        # Verify detected lines
        expected_lines = [
            (22, 19, 81, 80),  # First rectangle
            (122, 119, 181, 180),  # Second rectangle
            (22, 119, 81, 180),  # Third rectangle
            None  # Fourth rectangle is empty
        ]

        self.assertEqual(expected_lines, strongest_lines, "Detected lines should match expected lines.")

    def test_find_strongest_white_lines_no_lines(self):
        """
        Test that the function returns None for all rectangles if no white lines are present.
        """
        strongest_lines = find_strongest_white_lines(self.blank_image, self.rectangles)
        self.assertTrue(all(line is None for line in strongest_lines), "All rectangles should return None when no white lines are present.")


class TestRectangleFunctions(unittest.TestCase):

    def test_bounding_rectangle_valid_triangle(self):
        """
        Test bounding_rectangle with a valid triangle.
        """
        triangle = np.array([[2, 3], [5, 7], [4, 1]])
        expected = np.array([[2, 1], [5, 7]])
        result = bounding_rectangle(triangle)
        np.testing.assert_array_equal(result, expected, "Bounding rectangle does not match the expected result.")

    def test_bounding_rectangle_aligned_triangle(self):
        """
        Test bounding_rectangle with an aligned triangle (on axes).
        """
        triangle = np.array([[0, 0], [0, 5], [5, 0]])
        expected = np.array([[0, 0], [5, 5]])
        result = bounding_rectangle(triangle)
        np.testing.assert_array_equal(result, expected, "Bounding rectangle does not match the expected result for aligned triangle.")

    def test_bounding_rectangle_single_point_triangle(self):
        """
        Test bounding_rectangle where all three points of the triangle are the same.
        """
        triangle = np.array([[3, 3], [3, 3], [3, 3]])
        expected = np.array([[3, 3], [3, 3]])
        result = bounding_rectangle(triangle)
        np.testing.assert_array_equal(result, expected, "Bounding rectangle does not match the expected result for single-point triangle.")

    def test_bounding_rectangle_invalid_input_shape(self):
        """
        Test bounding_rectangle with invalid input shapes.
        """
        with self.assertRaises(ValueError):
            bounding_rectangle(np.array([[1, 2], [3, 4]]))  # Only two points
        with self.assertRaises(ValueError):
            bounding_rectangle(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))  # Incorrect dimensions

    def test_enclosing_rectangle_valid_rectangles(self):
        """
        Test enclosing_rectangle with two valid rectangles.
        """
        rect1 = np.array([[2, 3], [5, 7]])
        rect2 = np.array([[4, 1], [8, 6]])
        expected = np.array([[2, 1], [8, 7]])
        result = enclosing_rectangle(rect1, rect2)
        np.testing.assert_array_equal(result, expected, "Enclosing rectangle does not match the expected result.")

    def test_enclosing_rectangle_identical_rectangles(self):
        """
        Test enclosing_rectangle with two identical rectangles.
        """
        rect1 = np.array([[1, 1], [4, 4]])
        rect2 = np.array([[1, 1], [4, 4]])
        expected = np.array([[1, 1], [4, 4]])
        result = enclosing_rectangle(rect1, rect2)
        np.testing.assert_array_equal(result, expected, "Enclosing rectangle does not match the expected result for identical rectangles.")

    def test_enclosing_rectangle_contained_rectangles(self):
        """
        Test enclosing_rectangle where one rectangle is fully contained within the other.
        """
        rect1 = np.array([[2, 2], [6, 6]])
        rect2 = np.array([[3, 3], [5, 5]])
        expected = np.array([[2, 2], [6, 6]])
        result = enclosing_rectangle(rect1, rect2)
        np.testing.assert_array_equal(result, expected, "Enclosing rectangle does not match the expected result for contained rectangles.")

    def test_enclosing_rectangle_invalid_input_shape(self):
        """
        Test enclosing_rectangle with invalid input shapes.
        """
        with self.assertRaises(ValueError):
            enclosing_rectangle(np.array([[1, 2], [3, 4]]), np.array([[5, 6]]))  # Second rectangle invalid
        with self.assertRaises(ValueError):
            enclosing_rectangle(np.array([[1, 2], [3, 4]]), np.array([[5, 6, 7], [8, 9, 10]]))  # Incorrect dimensions


class TestReorderWarpedTriangle(unittest.TestCase):

    def test_reorder_basic_case(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[1, 1], [5, 1], [3, 4]])
        expected = tri_warped
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_reverse_order(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[3, 4], [5, 1], [1, 1]])
        expected = np.array([[1, 1], [5, 1], [3, 4]])
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_rotated_triangle(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[5, 1], [3, 4], [1, 1]])
        expected = np.array([[1, 1], [5, 1], [3, 4]])
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_with_noise(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[1.1, 1.2], [5.0, 1.0], [3.0, 4.1]])
        expected = np.array([[1.1, 1.2], [5.0, 1.0], [3.0, 4.1]])
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_large_coordinates(self):
        tri_orig = np.array([[1000, 1000], [4000, 1000], [2500, 3000]])
        tri_warped = np.array([[1100, 1100], [5000, 1000], [3000, 4000]])
        expected = tri_warped
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_negative_coordinates(self):
        tri_orig = np.array([[-2, -2], [2, -2], [0, 3]])
        tri_warped = np.array([[-1, -1], [3, -1], [1, 4]])
        expected = tri_warped
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_flipped_triangle(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[5, 1], [1, 1], [3, 4]])
        expected = np.array([[1, 1], [5, 1], [3, 4]])
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_single_point_shift(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[2, 1], [5, 1], [3, 4]])
        expected = np.array([[2, 1], [5, 1], [3, 4]])
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)

    def test_reorder_already_ordered(self):
        tri_orig = np.array([[0, 0], [4, 0], [2, 3]])
        tri_warped = np.array([[1, 1], [5, 1], [3, 4]])
        expected = tri_warped
        result = reorder_warped_triangle(tri_orig, tri_warped)
        np.testing.assert_almost_equal(result, expected)


if __name__ == "__main__":
    unittest.main()
