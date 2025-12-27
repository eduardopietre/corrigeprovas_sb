from dataclasses import dataclass
from enum import Enum

import numpy as np

from .encoding import image_to_base64
from .errors import WrongNumberDetectedInImageException, UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException
from .correction_utils import letters_from_indexes


@dataclass
class CircleInfo:
    x: int
    y: int
    radius: int
    marked: bool
    square_xy0: (int, int)
    square_xy1: (int, int)


class NQuestions(Enum):
    Q10 = 10
    Q20 = 20
    Q50 = 50
    Q100 = 100


class NAlternatives(Enum):
    A4 = 4
    A5 = 5


@dataclass
class CorrectorModelsInfo:
    n_questions: NQuestions
    n_alternatives: NAlternatives
    name: str

    def blank_template_path(self):
        return f"../generated/{self.n_questions}_{self.n_alternatives}_template.png"


class CorrectorModels(Enum):
    Q10_A4 = CorrectorModelsInfo(NQuestions.Q10, NAlternatives.A4, "Modelo 10 Questões 4 Alternativas")
    Q20_A4 = CorrectorModelsInfo(NQuestions.Q20, NAlternatives.A4, "Modelo 20 Questões 4 Alternativas")
    Q50_A4 = CorrectorModelsInfo(NQuestions.Q50, NAlternatives.A4, "Modelo 50 Questões 4 Alternativas")
    Q100_A4 = CorrectorModelsInfo(NQuestions.Q100, NAlternatives.A4, "Modelo 100 Questões 4 Alternativas")

    Q10_A5 = CorrectorModelsInfo(NQuestions.Q10, NAlternatives.A5, "Modelo 10 Questões 5 Alternativas")
    Q20_A5 = CorrectorModelsInfo(NQuestions.Q20, NAlternatives.A5, "Modelo 20 Questões 5 Alternativas")
    Q50_A5 = CorrectorModelsInfo(NQuestions.Q50, NAlternatives.A5, "Modelo 50 Questões 5 Alternativas")
    Q100_A5 = CorrectorModelsInfo(NQuestions.Q100, NAlternatives.A5, "Modelo 100 Questões 5 Alternativas")

    @staticmethod
    def __map_to_str():
        return {e: e.name for e in CorrectorModels}

    @staticmethod
    def valid_strs() -> [str]:
        return CorrectorModels.__map_to_str().values()

    @classmethod
    def from_str(cls, s):
        lookup = {v: k for k, v in CorrectorModels.__map_to_str().items()}
        assert s in lookup
        return cls(lookup[s])


@dataclass
class ExtractedData:
    correct_count: int
    selected_indexes: [int]
    img_result: np.array


@dataclass
class ExtractedDataOrError:
    """
    Represents either extracted data or an error encountered during data extraction.
    """
    img: np.array
    data: ExtractedData | None
    error: WrongNumberDetectedInImageException | UnableToFindFourAlignTrianglesException | FoundAlignTrianglesAreNotFilledException | None

    @property
    def is_error(self) -> bool:
        """
        Checks if an error occurred during data extraction.

        Returns:
            bool: True if there is an error, False otherwise.
        """
        return self.error is not None

    @property
    def is_ok(self) -> bool:
        """
        Inverse of is_error.

        Returns:
            bool: True if there was no error, False otherwise.
        """
        return not self.is_error


    @property
    def answers(self) -> str | None:
        """
        Retrieves the answers as a string if no error occurred.

        Returns:
            str | None: The answers string or None if an error occurred.
        """
        if self.is_error:
            return None
        return letters_from_indexes(self.data.selected_indexes)

    def as_json_dict(self) -> dict[str, str]:
        """
        Converts the extracted data or error information into a JSON-serializable dictionary.

        Returns:
            dict[str, str]: A dictionary containing either the extracted data or error information.
        """
        if self.is_error:
            return {
                "identifier": "",
                "correct_count": "",
                "answers": "",
                "img": image_to_base64(self.img),
                "after": "",
                "error": str(self.error),
            }
        else:
            return {
                "identifier": "",  # data.identifier,
                "correct_count": self.data.correct_count,
                "answers": self.answers,
                "img": image_to_base64(self.img),
                "after": image_to_base64(self.data.img_result),
                "error": "",
            }
