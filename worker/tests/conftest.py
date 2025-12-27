"""
Configuração de fixtures para testes do Worker.
"""

import pytest
from hypothesis import settings

# Configuração global do Hypothesis para testes de propriedade
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)
settings.load_profile("dev")


@pytest.fixture
def sample_answers_string_10():
    """Gabarito de exemplo com 10 questões."""
    return "ABCDAABCDA"


@pytest.fixture
def sample_answers_string_20():
    """Gabarito de exemplo com 20 questões."""
    return "ABCDAABCDAABCDAABCDA"


@pytest.fixture
def sample_template_10_4():
    """Template de exemplo: 10 questões, 4 alternativas."""
    from worker.models import Template
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
def sample_template_20_5():
    """Template de exemplo: 20 questões, 5 alternativas."""
    from worker.models import Template
    return Template(
        id="test-template-20-5",
        name="Modelo 20 Questões ABCDE",
        question_count=20,
        alternatives_count=5,
        version=1,
        template_storage_path="templates/20_5_template.png",
        is_active=True,
    )
