# CorrigeProvas Worker

Worker Python para processamento assíncrono de correções de provas de múltipla escolha.

## Arquitetura

O worker consome mensagens da fila `corrections` (pgmq) no Supabase e processa imagens de folhas de resposta usando OpenCV.

```
Queue (pgmq) → Worker → Storage (results)
                 ↓
              Postgres (correction_items)
```

## Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instalar dependências
pip install -e ".[dev]"
```

## Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
QUEUE_NAME=corrections
VISIBILITY_TIMEOUT=300
POLL_INTERVAL=5
MAX_RETRIES=3
```

## Execução

```bash
# Executar worker
corrigeprovas-worker

# Ou diretamente
python -m worker.main
```

## Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=worker --cov-report=html

# Apenas testes de propriedade
pytest -k "property"
```

## Estrutura

```
worker/
├── worker/
│   ├── __init__.py
│   ├── config.py          # Configuração
│   ├── models.py          # Modelos de dados
│   ├── queue_consumer.py  # Consumidor da fila
│   ├── image_processor.py # Pipeline OpenCV
│   ├── xlsx_generator.py  # Gerador de relatórios
│   ├── supabase_client.py # Cliente Supabase
│   └── main.py            # Entry point
├── tests/
│   ├── conftest.py
│   ├── test_image_processor.py
│   ├── test_xlsx_generator.py
│   └── test_answer_comparison.py
├── pyproject.toml
└── README.md
```
