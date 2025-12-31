# CorrigeProvas (Smart Bank)

CorrigeProvas is a modern web application for automated exam correction and management. This project consists of a React frontend, a Python-based backend/worker for processing corrections, and Supabase for database and authentication.

## Project Structure

*   `frontend/`: React application (Vite + TypeScript + TailwindCSS).
*   `corrector_backend_v2/`: Python backend logic for exam correction.
*   `worker/`: Python worker for processing asynchronous correction jobs.
*   `supabase/`: Supabase configuration and migrations.

## Prerequisites

Before setting up the project, ensure you have the following installed:

*   **Node.js** (v18 or higher) & **npm**
*   **Python** (v3.10 or higher)
*   **uv** (Python package manager) - [Installation Guide](https://github.com/astral-sh/uv)
    *   MacOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
*   **Supabase CLI** - [Installation Guide](https://supabase.com/docs/guides/cli)
    *   MacOS: `brew install supabase/tap/supabase`

---

## 1. Database Setup (Supabase)

**IMPORTANTE**: Configure o Supabase primeiro, pois o frontend e backend dependem dele.

1.  **Inicializar projeto Supabase local**:
    ```bash
    # Se ainda não foi inicializado
    supabase init

    # Se já existe, apenas verificar
    supabase status
    ```

2.  **Iniciar serviços Supabase locais**:
    ```bash
    supabase start
    ```
    Este comando inicia instâncias locais do Postgres, Auth, Storage, Edge Functions e Studio UI.

3.  **Aplicar migrations e configurações**:
    ```bash
    # Aplicar migrations do banco
    supabase db reset
    ```

4.  **Obter credenciais locais**:
    Após iniciar, você verá as credenciais no output. Para visualizá-las novamente:
    ```bash
    supabase status
    ```
    Anote a `API URL` e `anon key` para configurar o frontend.

---

## 2. Backend & Worker Setup (Python)

O backend e worker usam `uv` para gerenciamento de dependências. Um `Makefile` é fornecido para conveniência.

1.  **Configurar ambiente**:
    ```bash
    make setup
    make dev-install
    ```
    Este comando configura o ambiente virtual (`.venv`) e instala todas as dependências.

2.  **Executar testes** (Opcional mas recomendado):
    ```bash
    make test
    ```

3.  **Executar testes de qualidade** (Opcional mas recomendado):
    ```bash
    make quality
    ```

---

## 3. Frontend Setup (React)

1.  **Navegar para o diretório do frontend**:
    ```bash
    cd frontend
    ```

2.  **Instalar dependências**:
    ```bash
    npm install
    ```

3.  **Configuração das variáveis de ambiente**:
    Crie um arquivo `.env` na pasta `frontend` com as credenciais obtidas do `supabase status`:
    ```env
    VITE_SUPABASE_URL=http://127.0.0.1:54321
    VITE_SUPABASE_ANON_KEY=your-local-anon-key-here
    ```
    **Nota**: Substitua `your-local-anon-key-here` pela chave real mostrada no output do `supabase status`.

    Ou copie o conteúdo acima para um novo arquivo `.env` na pasta `frontend/`.

4.  **Executar servidor de desenvolvimento**:
    ```bash
    npm run dev
    ```
    A aplicação estará disponível em `http://localhost:5173`.

---

## 4. Executar a Aplicação Completa

### Workflow de Desenvolvimento Local

1.  **Terminal 1 - Supabase** (manter rodando):
    ```bash
    supabase start
    ```

2.  **Terminal 2 - Worker** (processamento assíncrono):
    ```bash
    make run-worker
    ```

3.  **Terminal 3 - Backend** (serviços):
    ```bash
    make run-backend
    ```

4.  **Terminal 4 - Frontend** (interface):
    ```bash
    cd frontend
    npm run dev
    ```

### Verificação de Funcionamento

Após iniciar todos os serviços:

- **Supabase Studio**: `http://localhost:54323`
- **Frontend**: `http://localhost:5173`
- **Backend**: Verificar se está respondendo nas portas configuradas
- **Worker**: Verificar logs para confirmar que está processando jobs

### Solução de Problemas Comuns

#### Erro: "failed to load .env"
- Certifique-se de que não há arquivo `.env` corrompido na raiz do projeto
- Execute `supabase stop` e `supabase start` novamente

#### Erro de conexão com banco
- Verifique se o Supabase está rodando: `supabase status`
- Confirme as credenciais no arquivo `.env` do frontend
- Certifique-se de que as migrations foram aplicadas: `supabase db reset`

#### Frontend não carrega
- Verifique se as variáveis `VITE_SUPABASE_URL` e `VITE_SUPABASE_ANON_KEY` estão corretas
- Execute `npm install` novamente na pasta frontend
- Limpe cache do navegador

#### Worker não processa
- Verifique se o backend está rodando
- Confirme conexão com Supabase no worker
- Verifique logs do worker para erros específicos

#### Erro: "violates check constraint check_template_storage_path_valid"
Este erro ocorre quando a função de validação de storage path está rejeitando caminhos válidos. Para corrigir:

1. **Verifique se há uma migration de correção**:
   ```bash
   # A migration 20251231000032_fix_storage_path_validation.sql deve existir
   ls supabase/migrations/20251231000032_fix_storage_path_validation.sql
   ```

2. **Execute reset do banco**:
   ```bash
   supabase db reset
   ```

3. **Se o erro persistir**, verifique se a função foi atualizada:
   ```sql
   -- Conecte no banco e execute:
   SELECT validate_storage_path('templates/modelo-10-abcd/v1/template.png');
   -- Deve retornar TRUE
   ```

### Parar Serviços Locais

Quando terminar de desenvolver, pare os serviços para liberar recursos:

```bash
# Parar Supabase
supabase stop

# Ou parar tudo de uma vez (se múltiplos projetos)
supabase stop --all
```

### Limpeza Completa (se necessário)

Se encontrar problemas persistentes:

```bash
# Limpar ambiente Python
make clean

# Resetar Supabase completamente
supabase stop
supabase start  # Isso recria todos os containers
```

---

## Development Workflow

### Running the Full Stack Locally

1.  **Supabase**: Ensure Supabase is running (`supabase start`).
2.  **Worker**: Open a terminal and run `make run-worker`.
3.  **Frontend**: Open a second terminal, go to `frontend/`, and run `npm run dev`.

### Code Quality

*   **Frontend**: Run `npm run lint` or `npm run type-check` (if configured) to verify code quality. `npm run build` will compile the project.
*   **Backend**: Use `make quality` to run formatting (black/isort), linting (flake8), type checking (mypy), and tests.

---

## Deploy em Produção

Esta seção detalha os passos necessários para fazer o deploy da aplicação CorrigeProvas em produção.

### Pré-requisitos para Deploy

1. **Conta no Supabase** (produção)
2. **Plataforma para Frontend** (Vercel, Netlify, ou similar)
3. **Plataforma para Backend/Worker** (Railway, Render, Fly.io, ou VPS)
4. **Variáveis de ambiente configuradas**

### 1. Preparação do Supabase (Produção)

#### 1.1 Criar projeto no Supabase

```bash
# Login no Supabase CLI
supabase login

# Criar novo projeto
supabase projects create corrigeprovas-prod
```

#### 1.2 Configurar banco de dados

```bash
# Linkar projeto local ao projeto remoto
supabase link --project-ref YOUR_PROJECT_REF

# Aplicar migrations
supabase db push

# Aplicar políticas RLS e configurações
supabase db reset
```

#### 1.3 Configurar Edge Functions (se necessário)

```bash
# Deploy das Edge Functions
supabase functions deploy
```

#### 1.4 Obter credenciais de produção

Após configurar o projeto no Supabase, obtenha:
- **Supabase URL**
- **Supabase Anon Key**
- **Service Role Key** (para backend/worker)

### 2. Deploy do Frontend

#### 2.1 Build do Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Criar build de produção
npm run build
```

#### 2.2 Configuração das variáveis de ambiente

Crie um arquivo `.env.production` ou configure no painel da plataforma de deploy:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-production-anon-key
```

#### 2.3 Deploy em plataformas específicas

##### Vercel (Recomendado)
```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

##### Netlify
```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Build e deploy
npm run build
netlify deploy --prod --dir=dist
```

##### Outras plataformas
Para outras plataformas de hosting estático, faça upload do conteúdo da pasta `dist` gerada pelo `npm run build`.

### 3. Deploy do Backend e Worker

#### 3.1 Preparação do código

```bash
# Instalar dependências de produção
make install

# Executar testes
make test

# Build/check qualidade
make quality
```

#### 3.2 Configuração das variáveis de ambiente

Configure as seguintes variáveis no seu serviço de backend/worker:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Configurações adicionais
WORKER_CONCURRENCY=4
MAX_FILE_SIZE=50MB
REDIS_URL=redis://your-redis-url  # se usar Redis para filas
```

#### 3.3 Deploy em plataformas específicas

##### Railway
```bash
# Usar Railway CLI ou conectar via GitHub
railway login
railway init
railway up
```

##### Render
- Conecte o repositório GitHub
- Configure como serviço web
- Defina o comando de start: `uv run python -m corrector_backend_v2.core`
- Configure variáveis de ambiente

##### Fly.io
```bash
# Instalar Fly CLI
curl -L https://fly.io/install.sh | sh

# Inicializar app
fly launch

# Configurar secrets
fly secrets set SUPABASE_URL=...
fly secrets set SUPABASE_SERVICE_ROLE_KEY=...

# Deploy
fly deploy
```

##### VPS/Docker
```dockerfile
# Dockerfile exemplo
FROM python:3.11-slim

WORKDIR /app

# Instalar UV
RUN pip install uv

# Copiar arquivos
COPY pyproject.toml uv.lock ./
COPY corrector_backend_v2/ ./corrector_backend_v2/
COPY worker/ ./worker/

# Instalar dependências
RUN uv pip install --system -e .

# Comando para executar
CMD ["uv", "run", "python", "-m", "corrector_backend_v2.core"]
```

### 4. Configurações Pós-Deploy

#### 4.1 Verificar conectividade

```bash
# Testar conexão com Supabase
curl https://your-project.supabase.co/rest/v1/

# Verificar se o frontend está carregando
curl https://your-frontend-url.com
```

#### 4.2 Configurar domínio (opcional)

- Configure domínio customizado no Supabase Auth
- Atualize URLs no frontend e backend
- Configure CORS no Supabase se necessário

#### 4.3 Configurar monitoramento

```bash
# Configurar logs no Railway/Render/Fly.io
# Configurar alertas de erro
# Configurar métricas de performance
```

#### 4.4 Backup e segurança

- Configure backups automáticos do banco Supabase
- Revise políticas RLS
- Configure rate limiting
- Monitore uso de recursos

### 5. Checklist de Deploy

- [ ] Supabase projeto criado e configurado
- [ ] Migrations aplicadas
- [ ] Edge Functions deployadas (se aplicável)
- [ ] Frontend buildado e deployado
- [ ] Backend/Worker deployado
- [ ] Variáveis de ambiente configuradas
- [ ] Testes de conectividade realizados
- [ ] Domínio configurado (se necessário)
- [ ] Monitoramento configurado
- [ ] Backups configurados

### 6. Troubleshooting Comum

#### Erro de CORS
- Verifique configurações de domínio no Supabase Auth
- Atualize `site_url` no config.toml

#### Erro de autenticação
- Verifique chaves do Supabase
- Confirme se as chaves são de produção

#### Worker não processa jobs
- Verifique conexão com banco
- Confirme variáveis de ambiente
- Verifique logs do worker

#### Frontend não carrega
- Verifique build do frontend
- Confirme variáveis VITE_ estão corretas
- Verifique CORS

---

## Features

*   **Exam Builder**: Create multi-variant exams with automated DOCX generation.
*   **Automated Correction**: Upload scans of answer sheets for automated grading.
*   **Dashboard**: Track corrections and manage exams.
