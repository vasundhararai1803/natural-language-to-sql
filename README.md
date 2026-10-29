# QueryLens AI: Production-Style Natural Language-to-SQL & Analytics Assistant

An end-to-end, production-style natural language analytics assistant that enables non-technical business users to explore transactional data, automatically generate and validate safe SQL, visualize metric trends, and conduct structured root-cause diagnostic investigations ("*Why did transactions drop last week?*") without writing code.

---

## 🌟 Key Capabilities

1. **Natural-Language-to-SQL Engine**: Translates questions into validated, read-only SQLite SELECT queries with schema introspection.
2. **Signature Diagnostic ("Why Did This Change?")**:
   - Compares current vs baseline equivalent periods (calendar weeks, months, or rolling).
   - Computes segment-level deltas across **Region**, **Product Category**, and **Sales Channel**.
   - Calculates mathematical share of drop contributed by each segment.
   - Detects statistically significant anomalies (e.g., regional drops, cancellation surges).
3. **Multi-Layer SQL Safety Layer**:
   - Parses AST via `sqlglot`.
   - Strictly permits only single read-only `SELECT` statements and CTEs.
   - Enforces a table whitelist (`transactions`, `products`, `customers`, `regions`).
   - Blocks multiple statement chaining (`;`), DDL/DML mutation keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `ATTACH`), and direct `sqlite_master` catalog snooping.
4. **Interactive Visualizations & Data Export**:
   - Declarative Recharts specifications dynamically rendered as Line, Bar, Grouped Bar, and Pie charts.
   - Data table view with null-handling and one-click CSV export.
   - Expandable SQL inspection with query copy capabilities.
5. **Grounded Executive Insights**:
   - Explicitly cites evidence from retrieved query rows.
   - Distinguishes observed facts from hypotheses; never claims causation from correlation alone.
   - Highlights assumptions, boundary caveats, and data quality warnings.
6. **Empirical Evaluation Benchmark**:
   - Built-in 32 test cases spanning aggregations, rankings, comparisons, ambiguity disambiguation, unsupported metric guards, and malicious SQL injection attempts.
   - 100% SQL Safety Rate and 100% Execution Accuracy on supported questions.

---

## 🏛️ Architecture Overview

```
├── backend/
│   ├── app/
│   │   └── main.py                 # FastAPI application entrypoint with CORS
│   ├── api/
│   │   └── routes.py               # REST API endpoints (/ask, /schema, /metrics, /evaluation)
│   ├── models/
│   │   ├── db_models.py            # SQLAlchemy models (transactions, products, customers, regions)
│   │   └── api_schemas.py          # Pydantic validation schemas & chart specs
│   ├── services/
│   │   ├── schema_service.py       # Catalog metadata & metric definitions
│   │   ├── sql_validation_service.py # sqlglot AST verification & security enforcement
│   │   ├── query_execution_service.py# Safe read-only executor with limits and timing
│   │   ├── analysis_service.py     # Diagnostic & segment breakdown service
│   │   ├── insight_service.py      # Grounded executive summary & limitation generator
│   │   ├── chart_service.py        # Declarative Recharts spec generator
│   │   ├── fallback_sql_service.py # Deterministic offline SQL engine
│   │   └── llm_service.py          # LLM adapter with OpenAI-compatible fallback
│   ├── evaluation/
│   │   └── benchmark_runner.py     # 32-case empirical benchmark runner
│   ├── scripts/
│   │   └── seed_db.py              # Reproducible synthetic seeder with drop scenarios
│   └── tests/
│       └── test_backend.py         # Pytest automated test suite
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AnalysisResult.tsx  # Executive findings, charts, SQL, table & CSV export
│   │   │   ├── ContributingFactors.tsx # Root-cause segment anomaly driver UI
│   │   │   ├── DynamicChart.tsx    # Recharts wrapper for Line, Bar, Grouped Bar, Pie
│   │   │   ├── EvaluationDashboard.tsx # Accuracy benchmark cards and test case list
│   │   │   └── SchemaExplorer.tsx  # Table & metric definitions catalog
│   │   ├── types.ts                # TypeScript interfaces
│   │   ├── App.tsx                 # Main layout & natural language interface
│   │   └── index.css               # Tailwind v4 dark theme styling
│   ├── package.json
│   └── vite.config.ts              # Vite configuration with proxy
└── data/
    └── querylens.db                # SQLite database with 12,965 seeded records
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup

```bash
# In the project root:
python3 -m venv venv
source venv/bin/activate

# Install dependencies:
pip install fastapi uvicorn pydantic sqlalchemy pandas sqlglot pytest httpx python-dotenv

# Initialize and seed the SQLite database:
PYTHONPATH=. python backend/scripts/seed_db.py

# Start the FastAPI backend server (port 8000):
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup

```bash
# In a new terminal window:
cd frontend

# Install frontend dependencies:
npm install

# Start Vite development server (port 5173):
npm run dev
```

Open your browser to: **`http://localhost:5173`**

---

## 🔑 LLM Configuration (Optional)

QueryLens AI includes a **high-accuracy deterministic engine** that runs completely offline with zero API keys required.

To connect to an external OpenAI-compatible model, create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

When no API key is provided, QueryLens AI automatically operates in labeled **Deterministic Fallback Engine** mode.

---

## 🧪 Running Automated Tests

Run the complete backend pytest suite:

```bash
source venv/bin/activate
PYTHONPATH=. pytest backend/tests/test_backend.py
```

### Running the Evaluation Benchmark

Run the 32-case accuracy and safety benchmark directly:

```bash
source venv/bin/activate
PYTHONPATH=. python -m backend.evaluation.benchmark_runner
```

**Measured Benchmark Outcomes:**
- **Overall Accuracy**: 100.0% (32 / 32 test cases passed)
- **SQL Safety Rate**: 100.0% (all malicious DDL/DML, prompt injections, and catalog snoopers blocked)
- **Execution Accuracy**: 100.0% on valid business queries
- **Average Latency**: ~3.5 ms
