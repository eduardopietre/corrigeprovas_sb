"""
Processador de imagens para correção de provas.

Encapsula o pipeline OpenCV para normalização, alinhamento,
detecção de marcações e geração de imagens marcadas.
"""

import io
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

# Adiciona o path do corrector_backend_v2 ao sys.path
BACKEND_PATH = Path(__file__).parent.parent.parent / "corrector_backend_v2"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from src.core import Corrector
from src.template_matcher import TemplateData
from src.constants import TemplateName
from src.structures import ExtractedDataOrError
from src.correction_utils import indexes_of_letters, letters_from_indexes
from src.errors import (
    WrongNumberDetectedInImageException,
    UnableToFindFourAlignTrianglesException,
    FoundAlignTrianglesAreNotFilledException
)

from .models import Template, ErrorCode, ProcessedItem

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Pipeline de processamento de imagem para correção de provas."""
    
    def __init__(self, template: Template):
        """
        Inicializa o processador com um template específico.
        
        Args:
            template: Template de folha de resposta a ser usado.
        """
        self.template = template
        self._template_data: Optional[TemplateData] = None
        self._corrector: Optional[Corrector] = None
        self._template_name: Optional[TemplateName] = None
    
    @property
    def template_data(self) -> TemplateData:
        """Carrega os dados do template de forma lazy."""
        if self._template_data is None:
            self._template_data = TemplateData()
        return self._template_data
    
    @property
    def corrector(self) -> Corrector:
        """Cria o corretor de forma lazy."""
        if self._corrector is None:
            self._corrector = Corrector(self.template_data)
        return self._corrector
    
    @property
    def template_name(self) -> TemplateName:
        """Mapeia o template do banco para o TemplateName do backend."""
        if self._template_name is None:
            self._template_name = self._map_template_name()
        return self._template_name
    
    def _map_template_name(self) -> TemplateName:
        """
        Mapeia question_count e alternatives_count para TemplateName.
        
        Returns:
            TemplateName correspondente ao template.
            
        Raises:
            ValueError: Se a combinação não for suportada.
        """
        q = self.template.question_count
        a = self.template.alternatives_count
        
        mapping = {
            (10, 4): TemplateName.T_10_4,
            (20, 4): TemplateName.T_20_4,
            (100, 4): TemplateName.T_100_4,
            (10, 5): TemplateName.T_10_5,
            (20, 5): TemplateName.T_20_5,
            (100, 5): TemplateName.T_100_5,
        }
        
        key = (q, a)
        if key not in mapping:
            raise ValueError(f"Template não suportado: {q} questões, {a} alternativas")
        
        return mapping[key]
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Normaliza a imagem ajustando brilho e contraste.
        
        Remove sombras e converte para formato binário otimizado
        para detecção de marcações.
        
        Args:
            image: Imagem BGR de entrada.
            
        Returns:
            Imagem normalizada em escala de cinza/binária.
        """
        from src.normalizer import ImageNormalizer
        return ImageNormalizer.normalize_image(image, shadow=True)
    
    def align(self, image: np.ndarray) -> np.ndarray:
        """
        Alinha a imagem usando os marcadores de referência (triângulos).
        
        Detecta os 4 triângulos de alinhamento e aplica transformação
        de perspectiva para corrigir distorções.
        
        Args:
            image: Imagem normalizada.
            
        Returns:
            Imagem alinhada com o template.
            
        Raises:
            UnableToFindFourAlignTrianglesException: Se não encontrar os triângulos.
            FoundAlignTrianglesAreNotFilledException: Se os triângulos não estiverem preenchidos.
        """
        from src.recognizer import Recognizer
        
        matcher = self.template_data.new_template_matcher(self.template_name)
        recognizer = Recognizer(matcher)
        
        # O método _normalize_and_align_by_triangles faz normalização + alinhamento
        # Aqui assumimos que a imagem já está normalizada
        return recognizer._normalize_and_align_by_triangles(image)
    
    def detect_marks(self, image: np.ndarray) -> list[str]:
        """
        Detecta as marcações na imagem e retorna as respostas.
        
        Analisa cada célula de resposta e determina qual alternativa
        foi marcada com base na intensidade dos pixels.
        
        Args:
            image: Imagem alinhada.
            
        Returns:
            Lista de respostas detectadas (ex: ['A', 'B', 'C', '-', 'D']).
            '-' indica questão anulada ou sem marcação válida.
        """
        matcher = self.template_data.new_template_matcher(self.template_name)
        
        # Usa o método interno para detectar a máscara de seleção
        selected_mask = matcher._find_selected_mask(image)
        
        # Converte a máscara para índices e depois para letras
        selected_indexes = []
        for mask in selected_mask:
            n_trues = np.sum(mask)
            if n_trues != 1:
                selected_indexes.append(-1)  # Anulada
            else:
                index = int(np.where(mask)[0][0])
                selected_indexes.append(index)
        
        return letters_from_indexes(selected_indexes)
    
    def read_qr(self, image: np.ndarray) -> Optional[str]:
        """
        Lê o QR code da imagem se presente.
        
        Args:
            image: Imagem original (BGR).
            
        Returns:
            Conteúdo do QR code ou None se não encontrado.
        """
        try:
            from pyzbar.pyzbar import decode
            
            # Tenta decodificar QR codes na imagem
            decoded_objects = decode(image)
            
            for obj in decoded_objects:
                if obj.type == 'QRCODE':
                    return obj.data.decode('utf-8')
            
            return None
        except Exception as e:
            logger.warning(f"Erro ao ler QR code: {e}")
            return None
    
    def generate_marked_image(
        self,
        image: np.ndarray,
        detected: list[str],
        correct: list[str]
    ) -> np.ndarray:
        """
        Gera imagem com marcações de certo/errado.
        
        Desenha indicadores visuais mostrando quais respostas
        estão corretas (verde), erradas (vermelho) ou anuladas (amarelo).
        
        Args:
            image: Imagem alinhada em escala de cinza.
            detected: Lista de respostas detectadas.
            correct: Lista de respostas corretas (gabarito).
            
        Returns:
            Imagem BGR com marcações coloridas.
        """
        correct_indexes = indexes_of_letters("".join(correct))
        detected_indexes = indexes_of_letters("".join(detected))
        
        matcher = self.template_data.new_template_matcher(self.template_name)
        selected_mask = matcher._find_selected_mask(image)
        
        _, _, img_result = matcher._result_image(image, selected_mask, correct_indexes)
        
        return img_result
    
    def process(
        self,
        image_bytes: bytes,
        answers_string: str
    ) -> Tuple[ProcessedItem, Optional[bytes]]:
        """
        Processa uma imagem completa e retorna os resultados.
        
        Executa o pipeline completo: normalização, alinhamento,
        detecção de marcações, comparação com gabarito e geração
        de imagem marcada.
        
        Args:
            image_bytes: Bytes da imagem original.
            answers_string: String do gabarito (ex: "ABCDAABCDA").
            
        Returns:
            Tupla com (ProcessedItem, bytes da imagem marcada ou None se erro).
        """
        # Decodifica a imagem
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return ProcessedItem(
                item_id="",
                identifier=None,
                detected_answers="",
                correct_count=0,
                total_questions=len(answers_string),
                marked_image_path="",
                success=False,
                error_code=ErrorCode.STORAGE_DOWNLOAD_FAILED.value,
                error_message="Não foi possível decodificar a imagem"
            ), None
        
        # Tenta ler QR code da imagem original
        identifier = self.read_qr(image)
        
        # Converte gabarito para índices
        correct_indexes = indexes_of_letters(answers_string)
        
        try:
            # Usa o corretor existente para processar
            result = self.corrector.correct_test_image(
                self.template_name,
                image,
                correct_indexes,
                do_identifier=False
            )
            
            if result.is_error:
                error_code, error_message = self._map_error(result.error)
                return ProcessedItem(
                    item_id="",
                    identifier=identifier,
                    detected_answers="",
                    correct_count=0,
                    total_questions=len(answers_string),
                    marked_image_path="",
                    success=False,
                    error_code=error_code,
                    error_message=error_message
                ), None
            
            # Extrai resultados
            detected_answers = result.answers or ""
            correct_count = result.data.correct_count
            
            # Codifica imagem marcada como JPEG
            marked_image_bytes = self._encode_image(result.data.img_result)
            
            return ProcessedItem(
                item_id="",
                identifier=identifier,
                detected_answers=detected_answers,
                correct_count=correct_count,
                total_questions=len(answers_string),
                marked_image_path="",
                success=True
            ), marked_image_bytes
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            return ProcessedItem(
                item_id="",
                identifier=identifier,
                detected_answers="",
                correct_count=0,
                total_questions=len(answers_string),
                marked_image_path="",
                success=False,
                error_code=ErrorCode.UNKNOWN_ERROR.value,
                error_message=str(e)
            ), None
    
    def _map_error(self, error: Exception) -> Tuple[str, str]:
        """
        Mapeia exceções do backend para códigos de erro.
        
        Args:
            error: Exceção capturada.
            
        Returns:
            Tupla (código de erro, mensagem).
        """
        if isinstance(error, UnableToFindFourAlignTrianglesException):
            return ErrorCode.ALIGN_TRIANGLES_NOT_FOUND.value, str(error)
        elif isinstance(error, FoundAlignTrianglesAreNotFilledException):
            return ErrorCode.ALIGN_TRIANGLES_NOT_FOUND.value, str(error)
        elif isinstance(error, WrongNumberDetectedInImageException):
            return ErrorCode.MARK_DETECTION_FAILED.value, str(error)
        else:
            return ErrorCode.UNKNOWN_ERROR.value, str(error)
    
    def _encode_image(self, image: np.ndarray, quality: int = 85) -> bytes:
        """
        Codifica uma imagem como JPEG.
        
        Args:
            image: Imagem numpy array.
            quality: Qualidade JPEG (0-100).
            
        Returns:
            Bytes da imagem codificada.
        """
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        _, buffer = cv2.imencode('.jpg', image, encode_params)
        return buffer.tobytes()


def compare_answers(detected: str, correct: str) -> int:
    """
    Compara respostas detectadas com o gabarito.
    
    Função utilitária para comparação case-insensitive.
    
    Args:
        detected: String de respostas detectadas.
        correct: String do gabarito.
        
    Returns:
        Número de acertos.
    """
    if len(detected) != len(correct):
        raise ValueError(f"Tamanhos diferentes: detected={len(detected)}, correct={len(correct)}")
    
    return sum(1 for d, c in zip(detected.upper(), correct.upper()) if d == c)
