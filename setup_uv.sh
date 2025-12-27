#!/bin/bash

# Script para configurar o ambiente UV para o projeto CorrigeProvas

set -e

echo "🚀 Configurando ambiente UV para CorrigeProvas..."

# Criar ambiente virtual
echo "🔧 Criando ambiente virtual..."
uv venv

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source .venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências do projeto..."
uv pip install -e .

# Instalar dependências de desenvolvimento
echo "📦 Instalando dependências de desenvolvimento..."
uv pip install -e ".[dev]"

echo ""
echo "🎉 Configuração concluída!"
echo ""
echo "Para ativar o ambiente virtual no futuro, execute:"
echo "  source .venv/bin/activate"
echo ""
echo "Para instalar novas dependências, use:"
echo "  uv add <package-name>"
echo ""
echo "Para executar comandos no ambiente virtual:"
echo "  uv run <command>"
echo ""
echo "Comandos úteis:"
echo "  uv run pytest                    # Executar testes"
echo "  uv run black .                   # Formatar código"
echo "  uv run isort .                   # Organizar imports"
echo "  uv run mypy corrector_backend_v2 worker  # Verificar tipos"