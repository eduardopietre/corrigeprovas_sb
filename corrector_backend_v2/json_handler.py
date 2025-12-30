import json

import numpy as np

from .utils import standardize_triangle_vertices, calculate_center_xy

# Definição de constantes de chaves
KEY_CELLS = "cells"
KEY_TRIANGLES = "triangles"
KEY_REFERENCE_LINES = "reference_lines"
KEY_NUMBER = "number"
KEY_CHECKBOXES = "checkboxes"
KEY_CONTENT = "content"
KEY_X = "x"
KEY_Y = "y"
KEY_X0 = "x0"
KEY_Y0 = "y0"
KEY_X1 = "x1"
KEY_Y1 = "y1"
KEY_SHAPE = "shape"
KEY_DPI = "dpi"
KEY_TYPE = "type"
KEY_WIDTH = "width"
KEY_HEIGHT = "height"
KEY_TOP = "top"
KEY_BOTTOM = "bottom"
KEY_LEFT = "left"
KEY_RIGHT = "right"
KEY_BOTTOM_RIGHT = "bottom_right"
KEY_BOTTOM_LEFT = "bottom_left"
KEY_TOP_RIGHT = "top_right"
KEY_TOP_LEFT = "top_left"


class DPIToPixelPointCalculator:

    def __init__(self, width_px: int, height_px: int, x0: float, x1: float, y0: float, y1: float):
        """
        Initializes the DPIToPixelPointCalculator class.

        Args:
            width_px (int): Width of the image in pixels.
            height_px (int): Height of the image in pixels.
            x0 (float): Minimum x-coordinate in the original reference system.
            x1 (float): Maximum x-coordinate in the original reference system.
            y0 (float): Minimum y-coordinate in the original reference system.
            y1 (float): Maximum y-coordinate in the original reference system.
        """
        self.width = width_px
        self.height = height_px
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.dx = x1 - x0
        self.dy = y1 - y0

        self.match = {
            KEY_CELLS: self._recalculate_cells,
            KEY_TRIANGLES: self._recalculate_triangles,
            KEY_NUMBER: self._recalculate_number,
            KEY_CHECKBOXES: self._recalculate_checkboxes,
            KEY_REFERENCE_LINES: self._recalculate_reference_lines,
        }

    def recalculate_x(self, x: float) -> int:
        """
        Recalculates an x-coordinate from the original reference system to pixel values.

        Args:
            x (float): The x-coordinate in the original reference system.

        Returns:
            int: The recalculated x-coordinate in pixel values.
        """
        delta_x = x - self.x0
        normalized_x = delta_x / self.dx  # Normalize by dx
        scaled_x = normalized_x * self.width  # Scale to pixel width
        pixel_x = round(scaled_x)
        return pixel_x

    def recalculate_y(self, y: float) -> int:
        """
        Recalculates a y-coordinate from the original reference system to pixel values.

        Args:
            y (float): The y-coordinate in the original reference system.

        Returns:
            int: The recalculated y-coordinate in pixel values.
        """
        delta_y = y - self.y1
        normalized_y = delta_y / -self.dy  # Normalize by dy (negated)
        scaled_y = normalized_y * self.height  # Scale to pixel height
        pixel_y = round(scaled_y)
        return pixel_y

    def recalculate_point(self, x, y) -> (int, int):
        """
        Recalculates a point's coordinates from the original reference system to pixel values.

        Args:
            x (float): The x-coordinate in the original reference system.
            y (float): The y-coordinate in the original reference system.

        Returns:
            tuple[int, int]: The recalculated point's coordinates in pixel values.
        """
        return self.recalculate_x(x), self.recalculate_y(y)

    def _recalculate_number(self, value: dict) -> dict:
        """
        Recalculates the coordinates for a single numbered item.

        Args:
            value (dict): A dictionary containing x and y coordinates.

        Returns:
            dict: The dictionary with recalculated coordinates.
        """
        value[KEY_X] = self.recalculate_x(value[KEY_X])
        value[KEY_Y] = self.recalculate_y(value[KEY_Y])
        return value

    def _recalculate_checkboxes(self, value: list[dict]) -> list[dict]:
        """
        Recalculates the bounding box coordinates for checkboxes.

        Args:
            value (list[dict]): A list of dictionaries containing bounding box coordinates.

        Returns:
            list[dict]: The list with recalculated bounding box coordinates.
        """
        for i in range(len(value)):
            value[i][KEY_X0] = self.recalculate_x(value[i][KEY_X0])
            value[i][KEY_Y0] = self.recalculate_y(value[i][KEY_Y0])
            value[i][KEY_X1] = self.recalculate_x(value[i][KEY_X1])
            value[i][KEY_Y1] = self.recalculate_y(value[i][KEY_Y1])

        return value

    def _recalculate_reference_lines(self, value: dict) -> dict:
        """
        Recalculates the coordinates for reference lines.

        Args:
            value (dict): A dictionary containing lists of points for reference lines.

        Returns:
            dict: The dictionary with recalculated reference line coordinates.
        """
        data = {
            k: [self.recalculate_point(*xy) for xy in v]
            for k, v in value.items()
        }
        return data

    def _recalculate_cells(self, value: dict) -> dict:
        """
        Recalculates the coordinates for cells.

        Args:
            value (dict): A dictionary containing data about cells.

        Returns:
            dict: The dictionary with recalculated cell data.
        """
        data = {
            k: self._delegate_recalculate_dict(v)
            for k, v in value.items()
        }
        return data

    def _recalculate_triangles(self, value: dict) -> dict:
        """
        Recalculates the coordinates for triangles.

        Args:
            value (dict): A dictionary containing triangle data.

        Returns:
            dict: The dictionary with recalculated triangle data.
        """
        data = {}
        for k, v in value.items():
            triangle = [self.recalculate_point(*e) for e in v]
            data[k] = standardize_triangle_vertices(np.array(triangle)).tolist()
        return data

    def _delegate_recalculate(self, key, value):
        """
        Delegates recalculation based on the key provided.

        Args:
            key (str): The key indicating the type of data to recalculate.
            value: The data to be recalculated.

        Returns:
            The recalculated data.
        """
        if key in self.match:
            return self.match[key](value)
        return value

    def _delegate_recalculate_dict(self, value: dict) -> dict:
        """
        Delegates recalculation for all items in a dictionary.

        Args:
            value (dict): The dictionary containing data to be recalculated.

        Returns:
            dict: The dictionary with recalculated data.
        """
        return {k: self._delegate_recalculate(k, v) for k, v in value.items()}

    def recalculate_img_dict(self, img_dict: dict) -> dict:
        """
        Recalculates all coordinates in an image dictionary.

        Args:
            img_dict (dict): A dictionary containing image data to recalculate.

        Returns:
            dict: The dictionary with recalculated image data.
        """
        return self._delegate_recalculate_dict(img_dict)


class GridJSONHandler:
    """
    Handles JSON operations for grid elements.
    """

    def __init__(self):
        self.data = {}
        self.recalculated = False

    def set(self, image_name: str, key: str, value):
        """
        Sets a value for a given key in the specified image's data.

        Args:
            image_name (str): Name of the image.
            key (str): Key to set the value for.
            value: Value to be set.
        """
        if image_name not in self.data:
            self.data[image_name] = {}
        self.data[image_name][key] = value

    def __getitem__(self, item: str):
        """
        Gets the data for the specified image.

        Args:
            item (str): Name of the image.

        Returns:
            dict: Data for the specified image.
        """
        return self.data[item]

    def image_center(self, image_name: str) -> np.ndarray:
        """
        Calculates the center of the image based on its triangles.

        Args:
            image_name (str): Name of the image.

        Returns:
            np.ndarray: Coordinates of the image center.
        """
        triangles = self[image_name][KEY_TRIANGLES]
        bottom_left = triangles[KEY_BOTTOM_LEFT]
        top_right = triangles[KEY_TOP_RIGHT]
        img_center = calculate_center_xy([
            calculate_center_xy(bottom_left),
            calculate_center_xy(top_right)
        ])
        return img_center

    def add_cells(self, image_name: str, cells_json: dict):
        """
        Adds cells data to the specified image.

        Args:
            image_name (str): Name of the image.
            cells_json (dict): Cells data to be added.
        """
        self.set(image_name, KEY_CELLS, cells_json)

    def add_triangles(self, image_name: str, points: dict):
        """
        Adds triangle data to the specified image.

        Args:
            image_name (str): Name of the image.
            points (dict): Triangle points to be added.
        """
        self.set(image_name, KEY_TRIANGLES, points)

    def add_reference_lines(self, image_name: str, reference_lines: dict):
        """
        Adds reference lines to the specified image.

        Args:
            image_name (str): Name of the image.
            reference_lines (dict): Reference lines to be added.
        """
        self.set(image_name, KEY_REFERENCE_LINES, reference_lines)

    def add_image_info(self, image_name: str, shape: tuple[int, int]):
        """
        Adds shape information to the specified image.

        Args:
            image_name (str): Name of the image.
            shape (tuple[int, int]): Shape information (width, height).
        """
        self.set(image_name, KEY_SHAPE, shape)

    def save_to_json(self, filename: str):
        """
        Saves all image data to a single JSON file.

        Args:
            filename (str): Path to the JSON file to save data.
        """
        self._recalculate_all_points()
        with open(filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def image_names(self) -> [str]:
        """
        Gets a sorted list of image names.

        Returns:
            list[str]: Sorted list of image names.
        """
        return sorted(self.data.keys())

    def _recalculate_all_points(self):
        """
        Recalculates all points for all images in the data.
        """
        if self.recalculated:
            return

        def find_values(points, func):
            value_x = func(p[0] for p in points)
            value_y = func(p[1] for p in points)
            return value_x, value_y

        new_data = {}
        for img_name, img_dict in self.data.items():
            width_px, height_px = img_dict[KEY_SHAPE]
            triangles = img_dict[KEY_TRIANGLES]
            bottom_left_triangle = triangles[KEY_BOTTOM_LEFT]
            top_right_triangle = triangles[KEY_TOP_RIGHT]

            x0, y0 = find_values(bottom_left_triangle, min)
            x1, y1 = find_values(top_right_triangle, max)

            calculator = DPIToPixelPointCalculator(width_px, height_px, x0, x1, y0, y1)
            new_data[img_name] = calculator.recalculate_img_dict(img_dict)

        self.data = new_data
        self.recalculated = True

    @staticmethod
    def number_and_checkboxes(number_dict: dict, checkbox_list: [dict]) -> dict:
        """
        Combines number and checkbox data into a single dictionary.

        Args:
            number_dict (dict): Data for the number element.
            checkbox_list (list[dict]): List of checkbox data.

        Returns:
            dict: Combined data for number and checkboxes.
        """
        return {
            KEY_NUMBER: number_dict,
            KEY_CHECKBOXES: checkbox_list,
        }

    @staticmethod
    def number(x: float, y: float, content: str) -> dict:
        """
        Creates a dictionary for a number element.

        Args:
            x (float): X-coordinate.
            y (float): Y-coordinate.
            content (str): Content of the number element.

        Returns:
            dict: Dictionary containing number data.
        """
        return {
            KEY_CONTENT: content,
            KEY_X: x,
            KEY_Y: y,
        }

    @staticmethod
    def checkbox(x0: float, y0: float, x1: float, y1: float, content: str) -> dict:
        """
        Creates a dictionary for a checkbox element.

        Args:
            x0 (float): X0-coordinate.
            y0 (float): Y0-coordinate.
            x1 (float): X1-coordinate.
            y1 (float): Y1-coordinate.
            content (str): Content of the checkbox element.

        Returns:
            dict: Dictionary containing checkbox data.
        """
        return {
            KEY_CONTENT: content,
            KEY_X0: x0,
            KEY_Y0: y0,
            KEY_X1: x1,
            KEY_Y1: y1,
        }

    @classmethod
    def load_from_json(cls, filename: str):
        """
        Loads all image data from a JSON file.

        Args:
            filename (str): Path to the JSON file to load data from.

        Returns:
            GridJSONHandler: An instance of GridJSONHandler with loaded data.
        """
        handler = GridJSONHandler()
        with open(filename, 'r') as f:
            handler.data = json.load(f)
        return handler
