# CorrigeProvas - Configuração UV

Este projeto usa [UV](https://docs.astral.sh/uv/) como gerenciador de pacotes e ambiente virtual Python.

## 🚀 Configuração Inicial

### Instalação Automática
```bash
# Executar script de configuração (recomendado)
./setup_uv.sh
```

### Instalação Manual

1. **Instalar UV** (se não estiver instalado):
   ```bash
   # macOS (Homebrew)
   brew install uv
   
   # macOS/Linux (curl)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Criar ambiente virtual**:
   ```bash
   uv venv
   ```

3. **Ativar ambiente virtual**:
   ```bash
   # macOS/Linux
   source .venv/bin/activate
   
   # Windows
   .venv\Scripts\activate
   ```

4. **Instalar dependências**:
   ```bash
   # Dependências principais
   uv pip install -e .
   
   # Dependências de desenvolvimento
   uv pip install -e ".[dev]"
   ```

## 📦 Gerenciamento de Dependências

### Adicionar Dependências
```bash
# Adicionar dependência principal
uv add numpy

# Adicionar dependência de desenvolvimento
uv add --dev pytest

# Adicionar dependência com versão específica
uv add "opencv-python>=4.10.0"
```

### Remover Dependências
```bash
uv remove numpy
```

### Atualizar Dependências
```bash
# Atualizar todas as dependências
uv pip install --upgrade -e .

# Atualizar dependência específica
uv pip install --upgrade numpy
```

## 🛠️ Comandos de Desenvolvimento

### Usando Makefile (Recomendado)
```bash
# Ver todos os comandos disponíveis
make help

# Configuração completa para desenvolvimento
make dev-install

# Executar testes
make test

# Executar testes com cobertura
make test-cov

# Formatar código
make format

# Verificar linting
make lint

# Verificar tipos
make type-check

# Pipeline completo de qualidade
make quality
```

### Comandos UV Diretos
```bash
# Executar comandos no ambiente virtual
uv run pytest
uv run black .
uv run mypy corrector_backend_v2 worker

# Executar aplicações
uv run corrigeprovas-worker
uv run python -m corrector_backend_v2.core
```

## 🧪 Testes

```bash
# Executar todos os testes
uv run pytest

# Executar testes com cobertura
uv run pytest --cov=corrector_backend_v2 --cov=worker --cov-report=html

# Executar testes específicos
uv run pytest corrector_backend_v2/tests/
uv run pytest worker/tests/
```

## 🔍 Qualidade de Código

### Formatação
```bash
# Formatar código com Black
uv run black corrector_backend_v2 worker

# Organizar imports com isort
uv run isort corrector_backend_v2 worker
```

### Linting
```bash
# Verificar código com flake8
uv run flake8 corrector_backend_v2 worker
```

### Verificação de Tipos
```bash
# Verificar tipos com mypy
uv run mypy corrector_backend_v2 worker
```

## 📁 Estrutura do Projeto

```
corrigeprovas/
├── corrector_backend_v2/     # Backend de correção
├── worker/                   # Worker de processamento
├── supabase/                # Configurações Supabase
├── pyproject.toml           # Configuração principal do projeto
├── uv.toml                  # Configuração UV
├── .python-version          # Versão Python
├── Makefile                 # Comandos de desenvolvimento
├── setup_uv.sh             # Script de configuração
└── README_UV.md            # Este arquivo
```

## 🔧 Configuração do Editor

### VS Code
Instale as extensões recomendadas:
- Python
- Black Formatter
- isort
- Mypy Type Checker

### PyCharm
Configure o interpretador Python para usar `.venv/bin/python`.

## 🚨 Solução de Problemas

### Ambiente Virtual não Ativado
```bash
# Verificar se está no ambiente virtual
which python
# Deve mostrar: /path/to/project/.venv/bin/python

# Se não estiver, ativar:
source .venv/bin/activate
```

### Dependências Desatualizadas
```bash
# Limpar e reinstalar
make clean
make setup
```

### Problemas com OpenCV
```bash
# No macOS, pode ser necessário instalar dependências do sistema
brew install opencv

# No Ubuntu/Debian
sudo apt-get install python3-opencv
```

## 📚 Recursos Úteis

- [Documentação UV](https://docs.astral.sh/uv/)
- [Guia de Migração para UV](https://docs.astral.sh/uv/guides/integration/)
- [Comparação UV vs pip/conda](https://docs.astral.sh/uv/pip/compatibility/)

## 🤝 Contribuindo

1. Configure o ambiente de desenvolvimento:
   ```bash
   make dev-install
   ```

2. Execute os testes antes de fazer commit:
   ```bash
   make quality
   ```

3. Siga as convenções de código configuradas (Black, isort, flake8, mypy).