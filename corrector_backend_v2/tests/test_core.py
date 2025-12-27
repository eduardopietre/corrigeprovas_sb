import os
import unittest

import cv2

from backend.corrector_backend_v2.src.core import Corrector
from ..src.debug import debug_show_image
from ..src.correction_utils import indexes_of_letters
from ..src.constants import TemplateName
from ..src.template_matcher import TemplateData


class TestCoreCorrector(unittest.TestCase):

    def setUp(self):
        self.data = TemplateData()
        self.corrector = Corrector(self.data)

    def _delegate_test(self, template: TemplateName, file: str, alternatives: str, correct_count: int, selected_indexes: [int], show=False):
        test_image = os.path.join("corrector_backend_v2", "tests", "test_data", file)
        img = cv2.imread(test_image)
        correct_indexes = indexes_of_letters(alternatives)

        correction_result = self.corrector.correct_test_image(template, img, correct_indexes, False).data
        if show:
            debug_show_image(correction_result.img_result)

        self.assertEqual(correct_count, correction_result.correct_count)
        self.assertEqual(selected_indexes, correction_result.selected_indexes)
        return correction_result.img_result

    def test_corrector_10_04_img_01_to_05_correct(self):
        for i in range(1, 5 + 1):
            self._delegate_test(
                TemplateName.T_10_4,
                f"10_4_filled1/10_04_img_0{i}.jpeg",
                "abcdaabcda",
                10,
                [0, 1, 2, 3, 0, 0, 1, 2, 3, 0],
                show=False,
            )

    def test_corrector_10_04_img_01_to_05_error1(self):
        for i in range(1, 5 + 1):
            self._delegate_test(
                TemplateName.T_10_4,
                f"10_4_filled1/10_04_img_0{i}.jpeg",
                "abcdaababb",
                7,
                [0, 1, 2, 3, 0, 0, 1, 2, 3, 0],
                show=False,
            )

    def test_corrector_10_04_img_01_to_05_error2(self):
        for i in range(1, 5 + 1):
            self._delegate_test(
                TemplateName.T_10_4,
                f"10_4_filled1/10_04_img_0{i}.jpeg",
                "dabaccdaac",
                0,
                [0, 1, 2, 3, 0, 0, 1, 2, 3, 0],
                show=False,
            )


if __name__ == '__main__':
    unittest.main()
