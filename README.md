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

## 1. Backend & Worker Setup (Python)

The backend and worker use `uv` for dependency management. A `Makefile` is provided for convenience.

1.  **Initialize the Environment**:
    ```bash
    make setup
    make dev-install
    ```
    This command sets up the virtual environment (`.venv`) and installs all dependencies.

2.  **Run Tests** (Optional but recommended):
    ```bash
    make test
    ```

3.  **Run the Worker** (for processing corrections):
    ```bash
    make run-worker
    ```

4.  **Run the Backend Service**:
    ```bash
    make run-backend
    ```

---

## 2. Database Setup (Supabase)

You can run the full database stack locally using the Supabase CLI.

1.  **Start Supabase**:
    ```bash
    supabase start
    ```
    This will spin up local instances of Postgres, Auth, Storage, Edge Functions, and the Studio UI.

2.  **Get Credentials**:
    After starting, you will see output containing your `API URL` and `anon key`. You will need these for the frontend configuration.

    To view them again later:
    ```bash
    supabase status
    ```

---

## 3. Frontend Setup (React)

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**:
    ```bash
    npm install
    ```

3.  **Environment Configuration**:
    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    
    Edit `.env` and configure your Supabase variables (obtained from `supabase status`):
    ```env
    VITE_SUPABASE_URL=http://127.0.0.1:54321
    VITE_SUPABASE_ANON_KEY=your-local-anon-key
    ```

4.  **Run Development Server**:
    ```bash
    npm run dev
    ```
    The application will be available at `http://localhost:5173`.

---

## Development Workflow

### Running the Full Stack Locally

1.  **Supabase**: Ensure Supabase is running (`supabase start`).
2.  **Worker**: Open a terminal and run `make run-worker`.
3.  **Frontend**: Open a second terminal, go to `frontend/`, and run `npm run dev`.

### Code Quality

*   **Frontend**: Run `npm run lint` or `npm run type-check` (if configured) to verify code quality. `npm run build` will compile the project.
*   **Backend**: Use `make quality` to run formatting (black/isort), linting (flake8), type checking (mypy), and tests.

## Features

*   **Exam Builder**: Create multi-variant exams with automated DOCX generation.
*   **Automated Correction**: Upload scans of answer sheets for automated grading.
*   **Dashboard**: Track corrections and manage exams.
