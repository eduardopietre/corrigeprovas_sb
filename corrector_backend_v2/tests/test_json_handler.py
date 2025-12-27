import unittest

from ..src.json_handler import *


class TestDPIToPixelPointCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = DPIToPixelPointCalculator(
            width_px=800, height_px=600,
            x0=0, x1=100, y0=0, y1=100
        )

    def test_recalculate_x(self):
        self.assertEqual(400, self.calculator.recalculate_x(50))

    def test_recalculate_y(self):
        self.assertEqual(300, self.calculator.recalculate_y(50))

    def test_recalculate_point(self):
        self.assertEqual((400, 300), self.calculator.recalculate_point(50, 50))

    def test_recalculate_number(self):
        value = {KEY_X: 50, KEY_Y: 50}
        expected = {KEY_X: 400, KEY_Y: 300}
        self.assertEqual(expected, self.calculator._recalculate_number(value))


class TestDPIToPixelPointCalculatorNegativeX0(unittest.TestCase):

    def setUp(self):
        self.calculator = DPIToPixelPointCalculator(
            width_px=800, height_px=600,
            x0=-50, x1=50, y0=0, y1=100
        )

    def test_recalculate_x_negative_x0(self):
        self.assertEqual(400, self.calculator.recalculate_x(0))

    def test_recalculate_y(self):
        self.assertEqual(300, self.calculator.recalculate_y(50))

    def test_recalculate_point(self):
        self.assertEqual((400, 300), self.calculator.recalculate_point(0, 50))

    def test_recalculate_number(self):
        value = {KEY_X: 0, KEY_Y: 50}
        expected = {KEY_X: 400, KEY_Y: 300}
        self.assertEqual(expected, self.calculator._recalculate_number(value))


class TestDPIToPixelPointCalculatorNegativeY0(unittest.TestCase):

    def setUp(self):
        self.calculator = DPIToPixelPointCalculator(
            width_px=800, height_px=600,
            x0=0, x1=100, y0=-50, y1=50
        )

    def test_recalculate_x(self):
        self.assertEqual(400, self.calculator.recalculate_x(50))

    def test_recalculate_y_negative_y0(self):
        self.assertEqual(300, self.calculator.recalculate_y(0))

    def test_recalculate_point(self):
        self.assertEqual((400, 300), self.calculator.recalculate_point(50, 0))

    def test_recalculate_number(self):
        value = {KEY_X: 50, KEY_Y: 0}
        expected = {KEY_X: 400, KEY_Y: 300}
        self.assertEqual(expected, self.calculator._recalculate_number(value))


class TestDPIToPixelPointCalculatorNegativeX0Y0(unittest.TestCase):

    def setUp(self):
        self.calculator = DPIToPixelPointCalculator(
            width_px=800, height_px=600,
            x0=-50, x1=50, y0=-50, y1=50
        )

    def test_recalculate_x_negative_x0(self):
        self.assertEqual(400, self.calculator.recalculate_x(0))

    def test_recalculate_y_negative_y0(self):
        self.assertEqual(300, self.calculator.recalculate_y(0))

    def test_recalculate_point_negative_x0_y0(self):
        self.assertEqual((400, 300), self.calculator.recalculate_point(0, 0))

    def test_recalculate_number_negative_x0_y0(self):
        value = {KEY_X: 0, KEY_Y: 0}
        expected = {KEY_X: 400, KEY_Y: 300}
        self.assertEqual(expected, self.calculator._recalculate_number(value))


class TestGridJSONHandler(unittest.TestCase):

    def setUp(self):
        self.handler = GridJSONHandler()

    def test_set_and_get_data(self):
        self.handler.set("image1", KEY_CELLS, {"cell1": {KEY_X: 50, KEY_Y: 50}})
        self.assertIn("image1", self.handler.data)
        self.assertEqual({"cell1": {KEY_X: 50, KEY_Y: 50}}, self.handler.data["image1"][KEY_CELLS])

    def test_add_cells(self):
        self.handler.add_cells("image1", {"cell1": {KEY_X: 50, KEY_Y: 50}})
        self.assertEqual({"cell1": {KEY_X: 50, KEY_Y: 50}}, self.handler.data["image1"][KEY_CELLS])

    def test_add_triangles(self):
        self.handler.add_triangles("image1", {"tri1": [(0, 0), (1, 1)]})
        self.assertEqual({"tri1": [(0, 0), (1, 1)]}, self.handler.data["image1"][KEY_TRIANGLES])

    def test_add_image_info(self):
        self.handler.add_image_info("image1", (800, 600))
        self.assertEqual((800, 600), self.handler.data["image1"][KEY_SHAPE])

    def test_number_and_checkboxes(self):
        result = GridJSONHandler.number_and_checkboxes({"num": 1}, [{"cb": 1}])
        self.assertEqual({KEY_NUMBER: {"num": 1}, KEY_CHECKBOXES: [{"cb": 1}]}, result)

    def test_number(self):
        result = GridJSONHandler.number(50, 50, "content")
        self.assertEqual({KEY_CONTENT: "content", KEY_X: 50, KEY_Y: 50}, result)

    def test_checkbox(self):
        result = GridJSONHandler.checkbox(50, 50, 100, 100, "content")
        self.assertEqual({KEY_CONTENT: 'content', KEY_X0: 50, KEY_X1: 100, KEY_Y0: 50, KEY_Y1: 100}, result)


if __name__ == "__main__":
    unittest.main()
