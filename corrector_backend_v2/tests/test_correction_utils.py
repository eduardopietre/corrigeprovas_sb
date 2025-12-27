import unittest

from ..src.correction_utils import index_of_letter, letter_from_index, indexes_of_letters, letters_from_indexes


class TestAlternativesFunctions(unittest.TestCase):

    def test_index_of_letter(self):
        self.assertEqual(0, index_of_letter("A"))
        self.assertEqual(1, index_of_letter("B"))
        self.assertEqual(2, index_of_letter("C"))
        self.assertEqual(3, index_of_letter("D"))
        self.assertEqual(4, index_of_letter("E"))
        self.assertEqual(0, index_of_letter("a"))  # Case insensitivity

        with self.assertRaises(ValueError):
            index_of_letter("Z")  # Invalid letter

    def test_letter_from_index(self):
        self.assertEqual("A", letter_from_index(0))
        self.assertEqual("B", letter_from_index(1))
        self.assertEqual("C", letter_from_index(2))
        self.assertEqual("D", letter_from_index(3))
        self.assertEqual("E", letter_from_index(4))
        self.assertEqual("-", letter_from_index(-1))  # Negative index
        with self.assertRaises(IndexError):
            letter_from_index(5)  # Out of bounds

    def test_indexes_of_letters(self):
        self.assertEqual([0, 1, 2, 3, 4], indexes_of_letters("ABCDE"))
        self.assertEqual([0, 1, 2, 3, 4], indexes_of_letters("abcde"))  # Case insensitivity
        with self.assertRaises(ValueError):
            indexes_of_letters("ABCFZ")  # Invalid letter in string

    def test_letters_from_indexes(self):
        self.assertEqual(["A", "B", "C", "D", "E"], letters_from_indexes([0, 1, 2, 3, 4]))
        self.assertEqual(["-", "A", "B"], letters_from_indexes([-1, 0, 1]))  # Handling negative index
        with self.assertRaises(IndexError):
            letters_from_indexes([5])  # Out of bounds index


if __name__ == "__main__":
    unittest.main()
