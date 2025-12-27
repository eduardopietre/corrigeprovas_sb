import random
import concurrent.futures

import cv2
import numpy as np

from tqdm import tqdm
from functools import partial

from src.constants import TemplateName, BGR_BLACK, BGR_WHITE
from src.json_handler import KEY_X0, KEY_X1, KEY_Y0, KEY_Y1, KEY_CHECKBOXES
from src.template_matcher import TemplateData

from storage import StorageMapper


def probability(p):
    if p <= 0:
        return False
    return random.random() < p


def random_indexes_for(template: TemplateName, amount, anullable) -> np.ndarray[int]:
    questions = template.number_of_questions()
    alternatives = template.number_of_alternatives()
    return np.random.randint(-1 if anullable else 0, alternatives, (amount, questions)).astype(np.int8)


def fill_checkbox(image, cords):
    x0, x1, y0, y1 = cords[KEY_X0], cords[KEY_X1], cords[KEY_Y0], cords[KEY_Y1]
    cv2.rectangle(image, (x0, y0), (x1, y1), BGR_BLACK, thickness=-1)


def distort_image(image: np.ndarray, intensity: float) -> np.ndarray:
    """
    Applies a pseudo-random perspective transformation to an image.

    Parameters:
        image (np.ndarray): Input RGB image.
        intensity (float): Intensity of the distortion (0.01-1.0).

    Returns:
        np.ndarray: Distorted image.
    """

    h, w, _ = image.shape
    src_points = np.float32([
        [0, 0],
        [w - 1, 0],
        [0, h - 1],
        [w - 1, h - 1]
    ])

    max_distortion_x = int(w * intensity)
    max_distortion_y = int(h * intensity)

    def random_point_within_bounds(x, y):
        return [
            max(0, min(w - 1, x + np.random.randint(-max_distortion_x, max_distortion_x + 1))),
            max(0, min(h - 1, y + np.random.randint(-max_distortion_y, max_distortion_y + 1)))
        ]

    dst_points = np.float32([
        random_point_within_bounds(0, 0),
        random_point_within_bounds(w - 1, 0),
        random_point_within_bounds(0, h - 1),
        random_point_within_bounds(w - 1, h - 1)
    ])

    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    distorted_image = cv2.warpPerspective(image, matrix, (w, h), borderValue=BGR_WHITE)
    return distorted_image


def generate_many(seed: int, data: TemplateData, template: TemplateName, amount: int, mistake_prob=0.0, anullable=False, distort=0.0, pad=20) -> (np.ndarray, [int]):
    random.seed(seed)
    np.random.seed(seed)

    indexes = random_indexes_for(template, amount, anullable)
    images = []

    for i in range(amount):
        raw_image = data.images[template.value].copy()
        for key, cell in data.order_iterate_over_cells(template):
            index = indexes[i, :][key - 1]
            checkboxes = cell[KEY_CHECKBOXES]

            if 0 <= index < len(checkboxes):
                fill_checkbox(raw_image, checkboxes[index])

                # This block must be inside the 'if 0 <= index < len(checkboxes):'
                # Otherwise a bug where a mistake can happen when no alternative must be selected can arise.
                if probability(mistake_prob):
                    rand_index = index
                    while rand_index == index:
                        rand_index = random.randint(0, len(checkboxes) - 1)
                    fill_checkbox(raw_image, checkboxes[rand_index])
                    indexes[i, key - 1] = -1  # sinaliza erro

        if distort > 0:
            raw_image = distort_image(raw_image, distort)

        with_border = cv2.copyMakeBorder(raw_image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=BGR_WHITE)
        images.append(with_border)

    return np.array(images), indexes


def generate_many_partial_for(append_mode: str):
    """
    Return a partial version of generate_many with certain keyword arguments
    filled in, based on the specified 'append_mode'.
    If the mode is not recognized, raises an assertError.
    """
    if append_mode == "Simple":
        return partial(generate_many, anullable=False, mistake_prob=0.0, distort=0.0)
    elif append_mode == "Anullable":
        return partial(generate_many, anullable=True, mistake_prob=0.0, distort=0.0)
    elif append_mode == "Mistake":
        return partial(generate_many, anullable=False, mistake_prob=0.25, distort=0.0)
    elif append_mode == "Distort":
        return partial(generate_many, anullable=False, mistake_prob=0.0, distort=0.22)
    elif append_mode == "Complex":
        return partial(generate_many, anullable=True, mistake_prob=0.25, distort=0.22)
    else:
        assert False, f"ERROR: append_mode '{append_mode}' is not valid."


def generate_batch(data: TemplateData, name: TemplateName, loops: int, batch_size: int, append: str, huge: bool):
    if huge:
        path = f'generated/synthetic_test_data_huge/{name.value}_{append}.zarr'
    else:
        path = f'generated/synthetic_test_data/{name.value}_{append}.zarr'

    generate_partial = generate_many_partial_for(append)

    sample_imgs, sample_labels = generate_partial(0, data, name, 1)

    image_shape = sample_imgs.shape[1:]
    label_size = sample_labels.shape[1]
    storage = StorageMapper(path, image_shape, label_size, chunk_size=batch_size)

    for i in range(loops):
        seed = i * batch_size
        images, labels = generate_partial(seed, data, name, batch_size)
        # print("At generate_batch: ", path, i, images.shape, labels.shape)
        storage.append_data(images, labels)


def generate_synthetic_data(huge: bool):
    data = TemplateData(normalize_images=False)

    batch_size = 50
    names = [TemplateName.T_10_4, TemplateName.T_20_4, TemplateName.T_100_4, TemplateName.T_10_5, TemplateName.T_20_5, TemplateName.T_100_5]
    appends = ["Simple", "Anullable", "Mistake", "Distort", "Complex"]

    if huge:
        loops = [40, 40, 20, 40, 40, 20]
    else:
        loops = [16, 16, 8, 16, 16, 8]

    with concurrent.futures.ProcessPoolExecutor(max_workers=12) as executor:
        futures = [
            executor.submit(generate_batch, data, name, amount, batch_size, append, huge)
            for append in appends
            for (name, amount) in zip(names, loops)
        ]

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="Generating..."
        ):
            _ = future.result()


# # Debug code use to test and trigger debug points.
# import unittest
# from src.debug import debug_show_image
#
#
# class TestComplexGenerator(unittest.TestCase):
#
#     def test_complex(self):
#         data = TemplateData(normalize_images=False)
#         batch_size = 10
#         name = TemplateName.T_10_4
#         append = "Complex"
#         generate_partial = generate_many_partial_for(append)
#         sample_imgs, sample_labels = generate_partial(0, data, name, batch_size)
#         for image, label in zip(sample_imgs, sample_labels):
#             print(label)
#             debug_show_image(image)


if __name__ == '__main__':
    generate_synthetic_data(huge=False)
    print("Success!")
