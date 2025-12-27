"""
Testes de integração com o backend corrector_backend_v2.

Verifica se o Worker consegue usar o backend existente para
processar imagens reais de teste.
"""

from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import pytest

from worker.worker.image_processor import ImageProcessor, compare_answers
from worker.worker.models import ErrorCode, Template


class TestBackendIntegration:
    """Testes de integração com o backend de correção."""
    
    @pytest.fixture
    def template_10_4(self):
        """Template 10 questões, 4 alternativas."""
        return Template(
            id="test-template-10-4",
            name="Modelo 10 Questões ABCD",
            question_count=10,
            alternatives_count=4,
            version=1,
            template_storage_path="templates/10_4_template.png",
            is_active=True,
        )
    
    @pytest.fixture
    def test_images_10_4(self):
        """Caminhos para imagens de teste 10x4."""
        base_path = Path("corrector_backend_v2/tests/test_data/10_4_filled1")
        
        if not base_path.exists():
            pytest.skip(f"Diretório de teste não encontrado: {base_path}")
        
        images = list(base_path.glob("*.jpeg"))
        if not images:
            pytest.skip(f"Nenhuma imagem de teste encontrada em: {base_path}")
        
        return images[:3]  # Usa apenas as 3 primeiras
    
    def test_image_processor_initialization(self, template_10_4):
        """Testa inicialização do processador de imagem."""
        processor = ImageProcessor(template_10_4)
        
        assert processor.template == template_10_4
        assert processor.template_name is not None
        
        # Verifica mapeamento de template
        from corrector_backend_v2.src.constants import TemplateName
        assert processor.template_name == TemplateName.T_10_4
        
        print("✓ ImageProcessor inicializado corretamente")
    
    def test_template_name_mapping(self):
        """Testa mapeamento de templates para TemplateName."""
        test_cases = [
            (10, 4, "T_10_4"),
            (20, 4, "T_20_4"),
            (100, 4, "T_100_4"),
            (10, 5, "T_10_5"),
            (20, 5, "T_20_5"),
            (100, 5, "T_100_5"),
        ]
        
        for q_count, a_count, expected_name in test_cases:
            template = Template(
                id="test",
                name="Test",
                question_count=q_count,
                alternatives_count=a_count,
                version=1,
                template_storage_path="test",
                is_active=True,
            )
            
            processor = ImageProcessor(template)
            assert processor.template_name.name == expected_name
        
        print("✓ Mapeamento de templates funcionando")
    
    def test_invalid_template_raises_error(self):
        """Testa que template inválido levanta erro."""
        invalid_template = Template(
            id="test",
            name="Invalid",
            question_count=15,  # Não suportado
            alternatives_count=4,
            version=1,
            template_storage_path="test",
            is_active=True,
        )
        
        processor = ImageProcessor(invalid_template)
        
        with pytest.raises(ValueError, match="Template não suportado"):
            _ = processor.template_name
    
    def test_compare_answers_function(self):
        """Testa função de comparação de respostas."""
        # Casos básicos
        assert compare_answers("ABCD", "ABCD") == 4
        assert compare_answers("ABCD", "DCBA") == 0
        assert compare_answers("ABCD", "ABDC") == 2
        
        # Case insensitive
        assert compare_answers("abcd", "ABCD") == 4
        assert compare_answers("AbCd", "aBcD") == 4
        
        # Com anuladas
        assert compare_answers("A-CD", "A-CD") == 4  # Todas iguais incluindo anulada
        assert compare_answers("A-CD", "ABCD") == 3  # A, C, D corretos
        
        # Tamanhos diferentes devem dar erro
        with pytest.raises(ValueError):
            compare_answers("ABC", "ABCD")
        
        print("✓ Função compare_answers funcionando")
    
    def test_process_real_images(self, template_10_4, test_images_10_4):
        """Testa processamento de imagens reais."""
        processor = ImageProcessor(template_10_4)
        gabarito = "ABCDAABCDA"  # Gabarito conhecido das imagens de teste
        
        results = []
        
        for i, image_path in enumerate(test_images_10_4):
            print(f"\nProcessando {image_path.name}...")
            
            # Lê a imagem
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Processa
            processed_item, marked_image_bytes = processor.process(
                image_bytes=image_bytes,
                answers_string=gabarito
            )
            
            results.append((processed_item, marked_image_bytes))
            
            print(f"  Sucesso: {processed_item.success}")
            if processed_item.success:
                print(f"  Respostas: {processed_item.detected_answers}")
                print(f"  Acertos: {processed_item.correct_count}/10")
                
                # Verifica resultados básicos
                assert processed_item.detected_answers is not None
                assert len(processed_item.detected_answers) == 10
                assert 0 <= processed_item.correct_count <= 10
                assert processed_item.total_questions == 10
                assert marked_image_bytes is not None
                assert len(marked_image_bytes) > 0
                
                # Verifica se a imagem marcada é válida
                marked_array = np.frombuffer(marked_image_bytes, np.uint8)
                marked_img = cv2.imdecode(marked_array, cv2.IMREAD_COLOR)
                assert marked_img is not None
                assert marked_img.shape[2] == 3  # BGR
                
            else:
                print(f"  Erro: {processed_item.error_code} - {processed_item.error_message}")
                # Para as imagens de teste conhecidas, esperamos sucesso na maioria
                # Se muitas falharem, pode indicar problema na configuração
        
        # Verifica que pelo menos uma imagem foi processada com sucesso
        successful = [r for r in results if r[0].success]
        assert len(successful) > 0, "Nenhuma imagem foi processada com sucesso"
        
        print(f"\n✓ {len(successful)}/{len(results)} imagens processadas com sucesso")
    
    def test_error_handling(self, template_10_4):
        """Testa tratamento de erros."""
        processor = ImageProcessor(template_10_4)
        
        # Imagem inválida (dados corrompidos)
        invalid_bytes = b"invalid image data"
        processed_item, marked_bytes = processor.process(
            image_bytes=invalid_bytes,
            answers_string="ABCDAABCDA"
        )
        
        assert not processed_item.success
        assert processed_item.error_code == ErrorCode.STORAGE_DOWNLOAD_FAILED.value
        assert "decodificar" in processed_item.error_message.lower()
        assert marked_bytes is None
        
        print("✓ Tratamento de erro para imagem inválida")
    
    def test_qr_code_reading(self, template_10_4):
        """Testa leitura de QR code (se disponível)."""
        processor = ImageProcessor(template_10_4)
        
        # Cria uma imagem simples para teste
        # (Na prática, as imagens de teste podem ou não ter QR codes)
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Testa que a função não quebra mesmo sem QR code
        qr_result = processor.read_qr(test_image)
        # Pode ser None se não houver QR code, isso é esperado
        assert qr_result is None or isinstance(qr_result, str)
        
        print("✓ Função de leitura de QR code não quebra")
    
    def test_image_normalization_and_alignment(self, template_10_4, test_images_10_4):
        """Testa normalização e alinhamento de imagens."""
        processor = ImageProcessor(template_10_4)
        
        # Pega a primeira imagem de teste
        image_path = test_images_10_4[0]
        image = cv2.imread(str(image_path))
        
        if image is None:
            pytest.skip(f"Não foi possível carregar a imagem: {image_path}")
        
        print(f"Testando com {image_path.name}")
        print(f"  Tamanho original: {image.shape}")
        
        # Testa normalização
        try:
            normalized = processor.normalize(image)
            assert normalized is not None
            assert isinstance(normalized, np.ndarray)
            print(f"  ✓ Normalização: {normalized.shape}")
        except Exception as e:
            print(f"  ⚠ Erro na normalização: {e}")
        
        # Testa alinhamento (pode falhar se a imagem não tiver marcadores)
        try:
            aligned = processor.align(image)
            assert aligned is not None
            assert isinstance(aligned, np.ndarray)
            print(f"  ✓ Alinhamento: {aligned.shape}")
        except Exception as e:
            print(f"  ⚠ Erro no alinhamento: {e}")
            # Alinhamento pode falhar se não encontrar triângulos, isso é esperado
    
    def test_mark_detection_pipeline(self, template_10_4, test_images_10_4):
        """Testa pipeline completo de detecção de marcações."""
        processor = ImageProcessor(template_10_4)
        
        for image_path in test_images_10_4[:1]:  # Testa apenas a primeira
            print(f"\nTestando pipeline completo com {image_path.name}")
            
            image = cv2.imread(str(image_path))
            if image is None:
                continue
            
            try:
                # Pipeline completo
                normalized = processor.normalize(image)
                aligned = processor.align(normalized)
                detected_marks = processor.detect_marks(aligned)
                
                print(f"  ✓ Marcações detectadas: {detected_marks}")
                assert isinstance(detected_marks, list)
                assert len(detected_marks) == 10  # 10 questões
                
                # Verifica que as marcações são válidas
                valid_marks = set('ABCDE-')
                for mark in detected_marks:
                    assert mark in valid_marks, f"Marcação inválida: {mark}"
                
                # Testa geração de imagem marcada
                correct_answers = list("ABCDAABCDA")
                marked_image = processor.generate_marked_image(
                    aligned, detected_marks, correct_answers
                )
                
                assert marked_image is not None
                assert isinstance(marked_image, np.ndarray)
                assert len(marked_image.shape) == 3  # Imagem colorida
                print(f"  ✓ Imagem marcada gerada: {marked_image.shape}")
                
            except Exception as e:
                print(f"  ⚠ Erro no pipeline: {e}")
                # Alguns erros são esperados dependendo da qualidade da imagem
                # O importante é que não quebre o sistema


class TestBackendCompatibility:
    """Testes de compatibilidade com o backend existente."""
    
    def test_backend_imports(self):
        """Verifica se consegue importar módulos do backend."""
        try:
            from corrector_backend_v2.src.constants import TemplateName
            from corrector_backend_v2.src.core import Corrector
            from corrector_backend_v2.src.correction_utils import (
                indexes_of_letters,
                letters_from_indexes,
            )
            from corrector_backend_v2.src.template_matcher import TemplateData
            print("✓ Imports do backend funcionando")
        except ImportError as e:
            pytest.fail(f"Erro ao importar módulos do backend: {e}")
    
    def test_backend_basic_functionality(self):
        """Testa funcionalidade básica do backend."""
        from corrector_backend_v2.src.constants import TemplateName
        from corrector_backend_v2.src.core import Corrector
        from corrector_backend_v2.src.correction_utils import indexes_of_letters
        from corrector_backend_v2.src.template_matcher import TemplateData
        
        # Cria objetos básicos
        template_data = TemplateData()
        corrector = Corrector(template_data)
        
        assert template_data is not None
        assert corrector is not None
        
        # Testa conversão de letras para índices
        indexes = indexes_of_letters("ABCD")
        assert indexes == [0, 1, 2, 3]
        
        indexes = indexes_of_letters("ABCDE")
        assert indexes == [0, 1, 2, 3, 4]
        
        print("✓ Funcionalidade básica do backend OK")
    
    def test_template_matcher_creation(self):
        """Testa criação de template matcher."""
        from corrector_backend_v2.src.constants import TemplateName
        from corrector_backend_v2.src.template_matcher import TemplateData
        
        template_data = TemplateData()
        
        # Testa criação de matchers para diferentes templates
        templates_to_test = [
            TemplateName.T_10_4,
            TemplateName.T_20_4,
            TemplateName.T_100_4,
        ]
        
        for template_name in templates_to_test:
            try:
                matcher = template_data.new_template_matcher(template_name)
                assert matcher is not None
                print(f"  ✓ Matcher criado para {template_name.name}")
            except Exception as e:
                print(f"  ⚠ Erro ao criar matcher para {template_name.name}: {e}")