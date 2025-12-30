# Define a list of possible alternatives (multiple-choice answers).
import numpy as np

from .constants import BGR_YELLOW, BGR_RED, BGR_GREEN

_ALTERNATIVES = ["A", "B", "C", "D", "E"]


def index_of_letter(s: str) -> int:
    """
    Returns the index of a given letter from the alternatives list.

    Args:
        s (str): A single letter (case-insensitive) to find in _ALTERNATIVES.

    Returns:
        int: The index of the letter in _ALTERNATIVES.

    Raises:
        ValueError: If the letter is not found in _ALTERNATIVES.
    """
    return _ALTERNATIVES.index(s.upper())


def letter_from_index(i: int) -> str:
    """
    Returns the letter corresponding to a given index in the alternatives list.

    Args:
        i (int): The index to convert into a letter.

    Returns:
        str: The letter at the specified index in _ALTERNATIVES.
              If the index is negative, returns "-".

    Raises:
        IndexError: If the index is out of bounds for _ALTERNATIVES.
    """
    if i < 0:
        return "-"
    return _ALTERNATIVES[i]


def indexes_of_letters(letters: str) -> [int]:
    """
    Converts a string of letters into a list of their corresponding indexes.

    Args:
        letters (str): A string of letters (case-insensitive) to convert.

    Returns:
        list[int]: A list of indexes corresponding to the letters in _ALTERNATIVES.

    Raises:
        ValueError: If any letter in the input is not found in _ALTERNATIVES.
    """
    return [index_of_letter(s) for s in letters]


def letters_from_indexes(values: [int]) -> [str]:
    """
    Converts a list of indexes into their corresponding letters.

    Args:
        values (list[int]): A list of indexes to convert into letters.

    Returns:
        list[str]: A list of letters corresponding to the indexes in _ALTERNATIVES.
                   Negative indexes are converted to "-".

    Raises:
        IndexError: If any index is out of bounds for _ALTERNATIVES.
    """
    return [letter_from_index(v) for v in values]


def mask_should_be_annulled(mask: np.ndarray[bool]) -> bool:
    """
    Determines if a boolean mask should be annulled.

    A mask is considered invalid (annulled) if it contains any number of `True`
    values other than exactly one.

    Args:
        mask (np.ndarray[bool]): A NumPy array of boolean values representing the mask.

    Returns:
        bool: `True` if the mask should be annulled (not exactly one `True` value), `False` otherwise.
    """
    n_trues = np.sum(mask)  # Count the number of `True` values
    return n_trues != 1


def mask_true_index(mask: np.ndarray[bool]) -> int:
    """
    Returns the index of selection indicated by a boolean mask.

    Assumes that the mask contains exactly one `True` value.
    The function identifies the index of the `True`.

    Args:
        mask (np.ndarray[bool]): A NumPy array of boolean values representing the mask.

    Returns:
        int: the index of the `True` value in the mask.

    Raises:
        IndexError: If the mask does not contain exactly one `True` value.
    """
    index = np.where(mask)[0][0]
    return int(index)


def mask_is_selection_correct(mask: np.ndarray[bool], correct: int) -> bool:
    """
    Checks if the selection indicated by a boolean mask matches the correct index.

    Assumes that the mask contains exactly one `True` value.
    The function identifies the index of the `True` value and compares it to the
    expected correct index.

    Args:
        mask (np.ndarray[bool]): A NumPy array of boolean values representing the mask.
        correct (int): The expected correct index.

    Returns:
        bool: `True` if the index of the `True` value in the mask matches `correct`, `False` otherwise.

    Raises:
        IndexError: If the mask does not contain exactly one `True` value.
    """
    # Find the index of the single `True` value
    return mask_true_index(mask) == correct


def get_color_for_question_result(is_anullable: bool, is_correct: bool) -> (int, int, int):
    """
    Determines the color for a question result based on its properties.

    Args:
        is_anullable (bool): Indicates if the question is nullable.
        is_correct (bool): Indicates if the question is correct.

    Returns:
        tuple[int, int, int]: A tuple representing the BGR color code.
            - Yellow if the question is nullable.
            - Green if the question is correct.
            - Red otherwise.
    """
    if is_anullable:
        return BGR_YELLOW
    if is_correct:
        return BGR_GREEN
    return BGR_RED
