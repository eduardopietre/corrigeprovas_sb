# Makefile para projeto CorrigeProvas com UV

.PHONY: help setup install install-dev clean test lint format type-check run-worker run-backend

# Variáveis
PYTHON_VERSION := 3.10
VENV_PATH := .venv

help: ## Mostrar esta ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Configurar ambiente UV completo
	@echo "🚀 Configurando ambiente UV..."
	@./setup_uv.sh

install: ## Instalar dependências principais
	@echo "📦 Instalando dependências principais..."
	uv pip install -e .

install-dev: ## Instalar dependências de desenvolvimento
	@echo "📦 Instalando dependências de desenvolvimento..."
	uv pip install -e ".[dev]"

clean: ## Limpar ambiente virtual e cache
	@echo "🧹 Limpando ambiente..."
	rm -rf $(VENV_PATH)
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete

test: ## Executar testes
	@echo "🧪 Executando testes..."
	uv run pytest

test-cov: ## Executar testes com cobertura
	@echo "🧪 Executando testes com cobertura..."
	uv run pytest --cov=corrector_backend_v2 --cov=worker --cov-report=html --cov-report=term

lint: ## Executar linting (flake8)
	@echo "🔍 Executando linting..."
	uv run flake8 corrector_backend_v2 worker

format: ## Formatar código (black + isort)
	@echo "✨ Formatando código..."
	uv run black corrector_backend_v2 worker
	uv run isort corrector_backend_v2 worker

type-check: ## Verificar tipos (mypy)
	@echo "🔍 Verificando tipos..."
	uv run mypy corrector_backend_v2 worker

check-all: lint type-check test ## Executar todas as verificações

run-worker: ## Executar worker
	@echo "🏃 Executando worker..."
	uv run corrigeprovas-worker

run-backend: ## Executar backend
	@echo "🏃 Executando backend..."
	uv run python -m corrector_backend_v2.core

# Comandos de desenvolvimento
dev-install: clean setup install-dev ## Configuração completa para desenvolvimento

# Comandos UV diretos
uv-add: ## Adicionar nova dependência (uso: make uv-add PACKAGE=nome-do-pacote)
	uv add $(PACKAGE)

uv-remove: ## Remover dependência (uso: make uv-remove PACKAGE=nome-do-pacote)
	uv remove $(PACKAGE)

uv-sync: ## Sincronizar dependências
	uv pip sync

uv-lock: ## Gerar arquivo de lock
	uv pip freeze > requirements-lock.txt

# Comandos de qualidade
quality: format lint type-check test ## Executar pipeline completo de qualidade