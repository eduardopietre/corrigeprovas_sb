from enum import Enum

MEDIAN_BLUR = 141  # Must be Odd, having a lower value resulted in black circles being ignored.

BGR_BLUE = (255, 0, 0)
BGR_GREEN = (0, 255, 0)
BGR_RED = (0, 0, 255)
BGR_YELLOW = (0, 255, 255)
BGR_WHITE = (255, 255, 255)
BGR_BLACK = (0, 0, 0)
BGR_PINK = (147, 20, 255)


class TemplateName(Enum):
    T_10_4 = "10_4_template"
    T_20_4 = "20_4_template"
    T_100_4 = "100_4_template"

    T_10_5 = "10_5_template"
    T_20_5 = "20_5_template"
    T_100_5 = "100_5_template"

    def number_of_questions(self) -> int:
        """
        Returns the number of questions associated with the template.

        Returns:
            int: Number of questions.
        """
        if self in {TemplateName.T_10_4, TemplateName.T_10_5}:
            return 10
        elif self in {TemplateName.T_20_4, TemplateName.T_20_5}:
            return 20
        elif self in {TemplateName.T_100_4, TemplateName.T_100_5}:
            return 100

    def number_of_alternatives(self) -> int:
        """
        Returns the number of answer alternatives associated with the template.

        Returns:
            int: Number of alternatives.
        """
        if self in {TemplateName.T_10_4, TemplateName.T_20_4, TemplateName.T_100_4}:
            return 4
        elif self in {TemplateName.T_10_5, TemplateName.T_20_5, TemplateName.T_100_5}:
            return 5

    @staticmethod
    def __map_to_str() -> dict['TemplateName': str]:
        """
        Maps templates to their string descriptions.

        Returns:
            dict: A dictionary mapping TemplateName to its description.
        """
        return {
            TemplateName.T_10_4: "Modelo 10 Questões ABCD",
            TemplateName.T_20_4: "Modelo 20 Questões ABCD",
            TemplateName.T_100_4: "Modelo 100 Questões ABCD",

            TemplateName.T_10_5: "Modelo 10 Questões ABCDE",
            TemplateName.T_20_5: "Modelo 20 Questões ABCDE",
            TemplateName.T_100_5: "Modelo 100 Questões ABCDE",
        }

    @staticmethod
    def valid_strs() -> [str]:
        """
        Retrieves all valid string representations of templates.

        Returns:
            list[str]: A sorted list of valid template descriptions.
        """
        pairs = list(TemplateName.__map_to_str().items())
        pairs.sort(key=lambda x: x[0].value)
        return [p[1] for p in pairs]

    @classmethod
    def from_str(cls, s: str) -> 'TemplateName':
        """
        Retrieves a TemplateName enum based on its string description.

        Args:
            s (str): The string description of a template.

        Returns:
            TemplateName: The corresponding TemplateName enum.

        Raises:
            AssertionError: If the string does not match any template.
        """
        lookup = {v: k for k, v in TemplateName.__map_to_str().items()}
        assert s in lookup, f"Invalid template string: {s}"
        return cls(lookup[s])
