# QueryLens AI

An enterprise analytics assistant that translates natural language business questions into AST-validated, secure SQLite queries, executes them in read-only mode, and generates evidence-grounded root-cause diagnostic insights and dynamic visualizations.

---

## Key Highlights & Architecture

- **Natural Language to SQL:** Translates plain-English business inquiries into single, read-only SQLite `SELECT` or CTE queries using either Groq/OpenAI LLMs or a deterministic offline fallback engine.
- **SQL Security & AST Validation:** Every query is parsed into an Abstract Syntax Tree (AST) using `sqlglot`. It rejects destructive statements (`DROP`, `INSERT`, `UPDATE`, `ALTER`), blocks semicolon chaining, verifies table and column identifiers against the schema catalog, enforces row limits via AST rewriting, and preserves legitimate SQL functions like `REPLACE()` and `CHAR()`.
- **Read-Only Database Enforcement:** Opens SQLite connections with URI `mode=ro` and enforces `PRAGMA query_only = ON` alongside query timeout limits.
- **Evidence-Grounded Diagnostics:** Explains period-over-period metric fluctuations with mathematical segment contribution shares, cancellation rates, and anomaly detection without hallucinating causality.
- **32-Case Automated Benchmark:** Comprehensive empirical test suite measuring execution accuracy, SQL safety rate, disambiguation, and latency.
- **Modern Full-Stack Architecture:** FastAPI backend with lifespan management, structured JSON logging, rate limiting, and persistent storage paired with a React 19 + TypeScript + Vite + Recharts frontend.

---

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic, sqlglot, Uvicorn, Pytest
- **Database:** SQLite (12,965 seeded retail transactions)
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, Recharts, Lucide Icons
- **AI Providers:** Groq (Llama 3.3 70B) / OpenAI-compatible endpoint, with deterministic offline fallback

---

## Quickstart

### 1. Prerequisites
- Python 3.11+
- Node.js 20+ and npm

### 2. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Seed the local database and run schema migrations
PYTHONPATH=. python backend/scripts/seed_db.py
PYTHONPATH=. python backend/scripts/migrate_db.py

# Start the FastAPI server (runs on http://127.0.0.1:8000)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend
npm ci
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Configuration (`.env`)

QueryLens AI works completely offline out-of-the-box using its deterministic rule engine.

To enable live LLM inference with Groq or OpenAI, copy `.env.example` to `.env`:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///data/querylens.db
QUERY_TIMEOUT_SECONDS=5.0
DEFAULT_ROW_LIMIT=500
API_RATE_LIMIT_PER_MINUTE=60
```

---

## Testing & Benchmarks

Run backend automated tests:
```bash
source venv/bin/activate
PYTHONPATH=. pytest backend/tests/test_backend.py -v
```

Run the 32-case accuracy and safety benchmark suite:
```bash
PYTHONPATH=. python -m backend.evaluation.benchmark_runner
```

Run frontend production build verification:
```bash
cd frontend
npm run build
```

---

## Docker & Container Deployment

Build and start both backend and frontend via Docker Compose:
```bash
docker compose up --build
```
- Frontend will be accessible at: `http://localhost:3000`
- Backend API will be accessible at: `http://localhost:8000`
- API Health Endpoint: `http://localhost:8000/api/health`

---

## CI / CD Pipeline

Automated GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:
- Seeds the database and runs database migrations
- Runs the Pytest test suite
- Runs the 32-case benchmark runner
- Installs frontend packages via `npm ci` and verifies production builds

---

## License
MIT License. Created by [Vasundhara Rai](https://github.com/vasundhararai1803).
