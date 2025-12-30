import cv2
import numpy as np

from .constants import TemplateName, BGR_PINK
from .correction_utils import mask_should_be_annulled, mask_is_selection_correct, get_color_for_question_result, \
    mask_true_index
from .errors import WrongNumberDetectedInImageException
from .image_manipulation import in_place_draw_checkboxes
from .json_handler import GridJSONHandler, KEY_TRIANGLES, KEY_CONTENT, KEY_CHECKBOXES, KEY_CELLS, KEY_X0, KEY_X1, \
    KEY_Y0, KEY_Y1, KEY_REFERENCE_LINES, KEY_TOP, KEY_BOTTOM, KEY_LEFT, KEY_RIGHT, KEY_SHAPE
from .normalizer import load_image
from .structures import ExtractedData
from .utils import order_triangles, calculate_square_means, relative_path


class TemplateMatcher:

    def __init__(self, template_data: 'TemplateData', template: TemplateName):
        """
        Initializes the TemplateMatcher with template data and a specific template.

        Args:
            template_data (TemplateData): Template data containing image and metadata.
            template (TemplateName): Specific template to use.
        """
        self.data = template_data
        self.template = template

    def get_triangles(self) -> np.ndarray:
        """
        Retrieves and orders the triangles from the template.

        Returns:
            np.ndarray: Ordered array of triangles.
        """
        name = self.template.value
        img_center = self.data.json_handler.image_center(name)
        triangles = self.data.json_handler[name][KEY_TRIANGLES]
        triangles = [np.array(v).reshape(3, 2) for v in triangles.values()]
        triangles = order_triangles(triangles, img_center=img_center)
        return np.array(triangles)

    def get_reference_lines(self) -> np.ndarray:
        """
        Retrieves reference lines from the template.

        Returns:
            np.ndarray: Array of reference lines.
        """
        name = self.template.value
        reference_lines = self.data.json_handler[name][KEY_REFERENCE_LINES]
        reference_lines = [
            reference_lines[KEY_TOP],
            reference_lines[KEY_BOTTOM],
            reference_lines[KEY_LEFT],
            reference_lines[KEY_RIGHT]
        ]
        return np.array(reference_lines)

    def get_image_shape(self) -> list:
        """
        Retrieves the shape of the template image.

        Returns:
            list: Shape of the image [width, height].
        """
        return self.data.json_handler[self.template.value][KEY_SHAPE]

    def get_template_image(self) -> np.ndarray:
        """
        Retrieves the template image.

        Returns:
            np.ndarray: Template image.
        """
        return self.data.images[self.template.value]

    def calculate_checkboxes_averages(self, img: np.ndarray) -> np.ndarray:
        """
        Calculates the average pixel values for checkboxes in the template.

        Args:
            img (np.ndarray): Input image.

        Returns:
            np.ndarray: Array of average pixel values for each checkbox.

        Raises:
            WrongNumberDetectedInImageException: If the number of detected averages does not match the expected number.
        """
        averages_dict = {}
        data = self.data.json_handler[self.template.value]
        for key, cell in data[KEY_CELLS].items():
            checkboxes = sorted(cell[KEY_CHECKBOXES], key=lambda e: e[KEY_CONTENT])
            # Here we need to invert Y1 and Y0, because Y0 is greater than Y1.
            areas_of_interest = [[e[KEY_X0], e[KEY_Y1], e[KEY_X1], e[KEY_Y0]] for e in checkboxes]
            means = calculate_square_means(img, areas_of_interest)

            number = int(key)
            averages_dict[number] = means

        sorted_keys = sorted(averages_dict.keys())
        averages = [averages_dict[k] for k in sorted_keys]

        if len(averages) != sorted_keys[-1]:
            raise WrongNumberDetectedInImageException(f"Expected {sorted_keys[-1]}, found {len(averages)}.")

        return np.array(averages)

    def _find_selected_mask(self, img: np.ndarray) -> np.ndarray[bool]:
        """
        Determines the selected mask for the checkboxes in the image.

        Args:
            img (np.ndarray): Input image.

        Returns:
            np.ndarray[bool]: Boolean mask indicating selected checkboxes.
        """
        averages = self.calculate_checkboxes_averages(img)  # ndarray (20, 4 or 5)

        mean = np.mean(averages, axis=1)  # ndarray (20,)
        std = np.std(averages)  # float
        threshold = mean + std  # ndarray (20,)

        mask = averages > threshold[:, np.newaxis]  # ndarray (20, 4 or 5)
        return mask

    def _result_image(self, img: np.ndarray, selected_mask: np.ndarray[bool], correct_indexes: [int]) -> (
    int, [int], np.ndarray):
        """
        Generates the result image and evaluates correctness.

        Args:
            img (np.ndarray): Input image.
            selected_mask (np.ndarray[bool]): Mask of selected checkboxes.
            correct_indexes (list[int]): List of correct indexes for each question.

        Returns:
            tuple[int, list[int], np.ndarray]: Number of correct answers, selected indexes, and result image.
        """
        correct_count = 0
        selected_indexes = []

        img_res = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for key, cell in self.data.order_iterate_over_cells(self.template):
            number = key - 1  # Keys starts at 1, so subtract 1

            if len(selected_mask) <= number:
                continue

            is_selected_mask = selected_mask[number]
            is_anullable = mask_should_be_annulled(is_selected_mask)

            # Number may be > than the corret_indexes
            # If that is the case, continue drawing but not marking as correct.
            # And only append to selected_indexes if is less than correct_indexes.
            if len(correct_indexes) > number:
                index = -1 if is_anullable else mask_true_index(is_selected_mask)
                selected_indexes.append(index)

                is_correct = False if is_anullable else mask_is_selection_correct(is_selected_mask,
                                                                                  correct_indexes[number])
                color = get_color_for_question_result(is_anullable, is_correct)

                if is_correct:
                    correct_count += 1
            else:
                color = BGR_PINK

            in_place_draw_checkboxes(cell, img_res, is_selected_mask, color)

        return correct_count, selected_indexes, img_res

    def correct(self, img: np.ndarray, correct_indexes: [int]) -> ExtractedData:
        """
        Corrects the responses in the image based on the correct indexes.

        Args:
            img (np.ndarray): Input image to correct.
            correct_indexes (list[int]): List of correct indexes.

        Returns:
            ExtractedData: Data containing the number of correct answers, selected indexes, and images.
        """
        selected_mask = self._find_selected_mask(img)
        correct_count, selected_indexes, img_res = self._result_image(img, selected_mask, correct_indexes)
        return ExtractedData(correct_count, selected_indexes, img_res)


class TemplateData:

    def __init__(self, handler: GridJSONHandler = None, normalize_images=True):
        """
        Initializes the TemplateData class with handler and template images.

        Args:
            handler (GridJSONHandler): Template grid data object.
            normalize_images (bool, optional): Whether to normalize images. Defaults to True.
        """
        self.json_handler = handler if handler is not None else load_template_data()
        self._images = None
        self.normalize_images = normalize_images

    @property
    def images(self) -> dict:
        """
        Lazily loads and caches images associated with the templates.

        Returns:
            dict: A dictionary where keys are template names and values are the loaded images.
        """
        if self._images is None:
            self._images = {
                k: load_image(k, normalize=self.normalize_images)
                for k in self.json_handler.image_names()
            }
        return self._images

    def new_template_matcher(self, template: TemplateName) -> TemplateMatcher:
        """
        Creates a new TemplateMatcher for the specified template.

        Args:
            template (TemplateName): Template to match.

        Returns:
            TemplateMatcher: Initialized TemplateMatcher.
        """
        return TemplateMatcher(self, template)

    def order_iterate_over_cells(self, template: TemplateName) -> (int, dict):
        """
        Iterates over the cells in the specified template in an ordered manner.

        Args:
            template (TemplateName): The template object containing the name and data structure for processing.

        Yields:
            tuple: A tuple containing the key and the corresponding cell.
        """
        data = self.json_handler[template.value]
        keys = sorted([int(i) for i in data[KEY_CELLS].keys()])
        for key in keys:
            cell = data[KEY_CELLS][str(key)]
            yield key, cell


def load_template_data(json_path="generated/templates_grid_data.json") -> GridJSONHandler:
    """
    Args:
        json_path (str, optional): Path to the JSON file containing template data. Defaults to "generated/templates_grid_data.json".
    """
    return GridJSONHandler.load_from_json(relative_path(json_path, __file__))
