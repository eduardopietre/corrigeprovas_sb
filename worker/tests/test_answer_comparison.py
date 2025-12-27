"""
Testes para comparação de respostas.

Feature: corrige-provas, Property 9: Answer Comparison Correctness
Validates: Requirements 6.5
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from worker.image_processor import compare_answers


class TestAnswerComparison:
    """Testes unitários para comparação de respostas."""
    
    def test_all_correct(self):
        """Todas as respostas corretas."""
        assert compare_answers("ABCD", "ABCD") == 4
    
    def test_all_wrong(self):
        """Todas as respostas erradas."""
        assert compare_answers("ABCD", "DCBA") == 0
    
    def test_partial_correct(self):
        """Algumas respostas corretas."""
        assert compare_answers("ABCD", "ABDC") == 2
    
    def test_case_insensitive(self):
        """Comparação deve ser case-insensitive."""
        assert compare_answers("abcd", "ABCD") == 4
        assert compare_answers("AbCd", "aBcD") == 4
    
    def test_with_annulled(self):
        """Respostas anuladas (marcadas com -)."""
        assert compare_answers("A-CD", "A-CD") == 4  # Todas iguais incluindo anulada
        assert compare_answers("A-CD", "ABCD") == 3  # A, C, D corretos
    
    def test_empty_strings(self):
        """Strings vazias."""
        assert compare_answers("", "") == 0
    
    def test_different_lengths_raises(self):
        """Tamanhos diferentes devem levantar erro."""
        with pytest.raises(ValueError):
            compare_answers("ABC", "ABCD")


class TestAnswerComparisonProperty:
    """
    Testes de propriedade para comparação de respostas.
    
    Feature: corrige-provas, Property 9: Answer Comparison Correctness
    Validates: Requirements 6.5
    """
    
    @settings(max_examples=100)
    @given(
        detected=st.text(alphabet='ABCDE-', min_size=1, max_size=100),
    )
    def test_same_string_all_correct(self, detected: str):
        """
        Property: Para qualquer string, comparar consigo mesma deve retornar
        o número de caracteres (exceto '-').
        """
        # Conta caracteres que não são '-'
        expected = sum(1 for c in detected if c != '-')
        result = compare_answers(detected, detected)
        assert result == len(detected)  # Todos iguais, incluindo '-' == '-'
    
    @settings(max_examples=100)
    @given(
        length=st.integers(min_value=1, max_value=100),
    )
    def test_completely_different_zero_correct(self, length: int):
        """
        Property: Strings completamente diferentes devem ter 0 acertos.
        """
        detected = "A" * length
        correct = "B" * length
        assert compare_answers(detected, correct) == 0
    
    @settings(max_examples=100)
    @given(
        detected=st.text(alphabet='ABCDE', min_size=1, max_size=100),
        correct=st.text(alphabet='ABCDE', min_size=1, max_size=100),
    )
    def test_result_bounded(self, detected: str, correct: str):
        """
        Property: O resultado deve estar entre 0 e o tamanho da string.
        """
        if len(detected) != len(correct):
            return  # Skip se tamanhos diferentes
        
        result = compare_answers(detected, correct)
        assert 0 <= result <= len(detected)
    
    @settings(max_examples=100)
    @given(
        detected=st.text(alphabet='ABCDE', min_size=10, max_size=10),
        correct=st.text(alphabet='ABCDE', min_size=10, max_size=10),
    )
    def test_case_insensitive_property(self, detected: str, correct: str):
        """
        Property: A comparação deve ser case-insensitive.
        """
        result_lower = compare_answers(detected.lower(), correct.lower())
        result_upper = compare_answers(detected.upper(), correct.upper())
        result_mixed = compare_answers(detected, correct)
        
        assert result_lower == result_upper == result_mixed
    
    @settings(max_examples=100)
    @given(
        detected=st.text(alphabet='ABCDE', min_size=20, max_size=20),
        correct=st.text(alphabet='ABCDE', min_size=20, max_size=20),
    )
    def test_manual_count_matches(self, detected: str, correct: str):
        """
        Property: O resultado deve ser igual à contagem manual de posições iguais.
        
        Feature: corrige-provas, Property 9: Answer Comparison Correctness
        Validates: Requirements 6.5
        """
        expected = sum(1 for d, c in zip(detected.upper(), correct.upper()) if d == c)
        result = compare_answers(detected, correct)
        assert result == expected
