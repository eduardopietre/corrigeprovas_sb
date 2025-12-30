import numpy as np

from .constants import TemplateName
from .recognizer import Recognizer
from .structures import ExtractedDataOrError
from .template_matcher import TemplateData
from .errors import WrongNumberDetectedInImageException, UnableToFindFourAlignTrianglesException, \
    FoundAlignTrianglesAreNotFilledException
from .correction_utils import indexes_of_letters


class Corrector:

    def __init__(self, template_data: TemplateData):
        """
        Initializes the Corrector class with the provided template data.

        Args:
            template_data (TemplateData): An instance containing template information and matching utilities.
        """
        self.data = template_data

    def correct_test_image(self, template: TemplateName, img: np.ndarray, correct_indexes: [int], do_identifier: bool) -> ExtractedDataOrError:
        """
        Processes a test image, aligns it with the specified template, and evaluates answers against correct indexes.

        Args:
            template (TemplateName): The template to match the image with.
            img (np.ndarray): The test image to correct.
            correct_indexes (list[int]): The list of correct indexes for answers.
            do_identifier (bool): If True, processes identifier-specific corrections. Currently not implemented.

        Returns:
            ExtractedDataOrError: The result of the correction process, including scores and marked images, or an error.

        Raises:
            NotImplementedError: If `do_identifier` is True, as identifier processing is not yet implemented.
        """
        if do_identifier:
            raise NotImplementedError()

        matcher = self.data.new_template_matcher(template)

        recognizer = Recognizer(matcher)
        try:
            correction_result = recognizer.correct(img, correct_indexes)
            return ExtractedDataOrError(img, correction_result, None)
        except (WrongNumberDetectedInImageException, UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException) as e:
            return ExtractedDataOrError(img, None, e)

    def multiple_correct_test_image(self, template: TemplateName, images: [np.ndarray], answers: str, do_identifier: bool) -> [ExtractedDataOrError]:
        """
        Processes multiple test images, aligns them with the specified template, and evaluates their answers against the provided correct answers.

        Args:
            template (TemplateName): The template to match the images with.
            images (list[np.ndarray]): A list of test images to correct.
            answers (str): The string of correct answers, where each character corresponds to a correct answer choice.
            do_identifier (bool): If True, processes identifier-specific corrections. Currently not implemented.

        Returns:
            list[ExtractedDataOrError]: A list of results or errors for each image, containing correction details.

        Raises:
            NotImplementedError: If `do_identifier` is True, as identifier processing is not yet implemented.
        """
        if do_identifier:
            raise NotImplementedError()

        correct_indexes = indexes_of_letters(answers)
        results = [self.correct_test_image(template, img, correct_indexes, do_identifier) for img in images]
        return results


def main():
    """Função principal para executar o backend de correção."""
    import sys
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Backend CorrigeProvas iniciado")
    logger.info("Para usar a API, importe as classes do módulo corrector_backend_v2")

    # Exemplo de uso
    try:
        from .template_matcher import TemplateData
        from .constants import TemplateName

        # Carregar dados do template (exemplo)
        template_data = TemplateData()
        corrector = Corrector(template_data)

        logger.info(f"Backend inicializado com sucesso. Classes disponíveis: {dir()}")

    except Exception as e:
        logger.error(f"Erro ao inicializar backend: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
