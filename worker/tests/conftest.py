"""
Configuração de fixtures para testes do Worker.
"""

import os

import pytest
from hypothesis import settings

# Configuração global do Hypothesis para testes de propriedade
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=50)
settings.load_profile("dev")


def pytest_configure(config):
    """Configura marcadores personalizados."""
    config.addinivalue_line(
        "markers", "slow: marca testes que demoram para executar"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração que precisam de Supabase local"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica itens de teste baseado em marcadores."""
    # Adiciona marcador 'integration' para testes que usam Supabase
    for item in items:
        if "integration" in item.nodeid or "supabase" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def supabase_config():
    """Configuração do Supabase local para testes."""
    return {
        "url": "http://127.0.0.1:54321",
        "service_role_key": os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        )
    }


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
