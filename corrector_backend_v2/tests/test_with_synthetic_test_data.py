import unittest

import numpy as np

from ..src.errors import UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException
from ..src.recognizer import Recognizer
from ..src.template_matcher import TemplateData
from ..src.constants import TemplateName
from ..src.utils import relative_path
from ..storage import lazy_iterate_dataset

ZERO_TOLERANCE = False


def delegate_test(template: TemplateName, append: str, recognizer: Recognizer) -> (float, float):
    total_amount = 0
    align_error = 0
    errors = []

    path = relative_path(f"../generated/synthetic_test_data/{template.value}_{append}.zarr", __file__)

    for images, labels in lazy_iterate_dataset(path, 50):
        total_amount += len(images)
        for i in range(len(images)):
            img = images[i]
            label = labels[i]

            try:
                correction_result = recognizer.correct(img, label)
            except (UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException) as e:
                # from backend.corrector_backend_v2.src.debug import debug_show_image
                # debug_show_image(e.image)
                align_error += 1
                continue
            except Exception as e:
                print(e)
                # debug_show_image(img)
                continue

            if correction_result:
                selected_indexes = correction_result.selected_indexes
                divergents = np.sum(label != np.array(selected_indexes))
                errors.append(divergents)

                if divergents > 0:
                    from backend.corrector_backend_v2.src.debug import debug_show_image
                    debug_show_image(correction_result.img_result)
                    debug_show_image(img)
                    # correction_result = recognizer.correct(img, label)

    return float(np.mean(errors)) * 100, (align_error / total_amount)


class BaseTestSynthetic(unittest.TestCase):
    T = None

    def setUp(self):
        self.data = TemplateData()
        self.matcher = self.data.new_template_matcher(self.T)
        self.recognizer = Recognizer(self.matcher, shadow=False)

    def _delegate(self, append: str) -> float:
        if self.T is None:
            raise Exception("BaseTestSynthetic must not be called with T = None.")
        return delegate_test(self.T, append, self.recognizer)

    def delegate_test(self, append: str, error_threshold: float, allign_error_error_threshold: int = 0):
        if ZERO_TOLERANCE:
            error_threshold = 0
        assert append in ["Simple", "Anullable", "Mistake", "Distort", "Complex"]
        error, allign_error = self._delegate(append)
        self.assertGreaterEqual(
            allign_error_error_threshold, allign_error,
            msg=f"Failed at '{append}', allign_error_error_threshold is '{allign_error_error_threshold}', but allign_error is '{allign_error}'.")
        self.assertGreaterEqual(error_threshold, error,
                                msg=f"Failed at '{append}', error_threshold is '{error_threshold}', but error is '{error}'.")


class TestSynthetic_10_4(BaseTestSynthetic):
    T = TemplateName.T_10_4

    def test_simple(self):
        self.delegate_test("Simple", 0.0)

    def test_anullable(self):
        self.delegate_test("Anullable", 0.0)

    def test_mistake(self):
        self.delegate_test("Mistake", 0.0)

    def test_distort(self):
        self.delegate_test("Distort", 0.0, 0.02625)


class TestSynthetic_20_4(BaseTestSynthetic):
    T = TemplateName.T_20_4

    def test_simple(self):
        self.delegate_test("Simple", 0.01)

    def test_anullable(self):
        self.delegate_test("Anullable", 0.01)

    def test_mistake(self):
        self.delegate_test("Mistake", 0.01)

    def test_distort(self):
        self.delegate_test("Distort", 0.01, 0.015)


class TestSynthetic_100_4(BaseTestSynthetic):
    T = TemplateName.T_100_4

    def test_simple(self):
        self.delegate_test("Simple", 0.01)

    def test_anullable(self):
        self.delegate_test("Anullable", 0.01)

    def test_mistake(self):
        self.delegate_test("Mistake", 0.01)

    def test_distort(self):
        self.delegate_test("Distort", 0.01, 0.0325)


class TestSynthetic_10_5(BaseTestSynthetic):
    T = TemplateName.T_10_5

    def test_simple(self):
        self.delegate_test("Simple", 0.01)

    def test_anullable(self):
        self.delegate_test("Anullable", 0.01)

    def test_mistake(self):
        self.delegate_test("Mistake", 0.01)

    def test_distort(self):
        self.delegate_test("Distort", 0.01, 0.00625)


class TestSynthetic_20_5(BaseTestSynthetic):
    T = TemplateName.T_20_5

    def test_simple(self):
        self.delegate_test("Simple", 0.01)

    def test_anullable(self):
        self.delegate_test("Anullable", 0.01)

    def test_mistake(self):
        self.delegate_test("Mistake", 0.01)

    def test_distort(self):
        self.delegate_test("Distort", 0.01, 0.015)


class TestSynthetic_100_5(BaseTestSynthetic):
    T = TemplateName.T_100_5

    def test_simple(self):
        self.delegate_test("Simple", 0.01)

    def test_anullable(self):
        self.delegate_test("Anullable", 0.01)

    def test_mistake(self):
        self.delegate_test("Mistake", 0.01)

    def test_distort(self):
        self.delegate_test("Distort", 0.01, 0.0225)


if __name__ == "__main__":
    unittest.main()
