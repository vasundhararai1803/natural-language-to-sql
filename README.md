# QueryLens AI

An analytics assistant that translates plain-English business questions into validated SQL, executes queries safely against a relational database, and explains the factors behind metric changes without requiring users to write code.

---

## Why This Project Was Built

Non-technical teams such as product managers, operations teams, and business analysts frequently need answers from company data, but writing SQL creates a bottleneck. At the same time, giving raw language models unconstrained access to databases introduces serious risks: models can hallucinate table structures, generate destructive queries (like `DROP` or `DELETE`), or present simple correlations as proven facts.

QueryLens AI was designed to solve this with a guarded, reliable workflow:
- Enable stakeholders to ask everyday questions such as "Why did transactions drop last week?" or "What were our top-performing products?".
- Validate generated SQL through an Abstract Syntax Tree (AST) safety layer before anything touches the database.
- Perform structured root-cause diagnostic analysis by calculating period-over-period segment contributions and anomaly flags.
- Ground all generated insights strictly in returned rows, without inventing numbers or claiming unproven causality.

---

## What It Does

- **Natural Language to SQL**: Converts business questions into single, read-only SQLite `SELECT` statements.
- **Root-Cause Diagnostics**: Compares time periods (such as last week vs. the previous week), identifies which region or category caused a change, and calculates each segment's exact share of the decline.
- **SQL Safety Enforcement**: Uses `sqlglot` to verify that queries only read from permitted tables, block semicolon-chained injection attempts, and reject mutating statements.
- **Dynamic Visualizations**: Automatically selects and renders the appropriate chart type (Line, Bar, Grouped Bar, or Pie) using Recharts.
- **Evidence-Grounded Explanations**: Produces clear business summaries backed by query figures, highlighting assumptions, data limits, and follow-up suggestions.
- **Data Inspection and CSV Export**: Allows users to inspect the underlying SQL, review tabular data, and export results.

---

## How It Operates

```
User Question
    |
    v
1. Interpret Intent  ---> Disambiguates vague queries or flags unsupported metrics
    |
    v
2. Formulate SQL    ---> Generated via Groq/OpenAI or the deterministic offline fallback engine
    |
    v
3. Validate SQL     ---> Parsed through AST rules (allows only read-only SELECT; blocks mutations)
    |
    v
4. Execute Query    ---> Runs against SQLite with enforced row limits
    |
    v
5. Analyze & Chart  ---> Calculates segment variances, generates chart spec, and writes plain-English insights
```

---

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, sqlglot, Pytest
- **Database**: SQLite (12,965 seeded transaction records)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons
- **AI Integration**: Groq (Llama 3.3) / OpenAI-compatible endpoint, plus a deterministic offline fallback engine

---

## Quickstart (Running Locally)

### 1. Backend
```bash
# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed the local SQLite database
PYTHONPATH=. python backend/scripts/seed_db.py

# Start the backend server (http://127.0.0.1:8000)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend
In a separate terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Configuration (Optional Free AI Key)

The system works completely offline out-of-the-box using its deterministic template engine.

To use live LLM inference with Groq's free tier, create a `.env` file in the project root:
```env
OPENAI_API_KEY=gsk_your_free_groq_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///data/querylens.db
```

---

## Testing & Evaluation

- **Unit and Integration Tests**:
  ```bash
  source venv/bin/activate
  PYTHONPATH=. pytest backend/tests/test_backend.py
  ```
- **32-Case Accuracy and Safety Benchmark**:
  ```bash
  source venv/bin/activate
  PYTHONPATH=. python -m backend.evaluation.benchmark_runner
  ```
  *(Measures execution accuracy, safety rejection of dangerous queries, and latency)*

---

## License
MIT License. Created by [Vasundhara Rai](https://github.com/vasundhararai1803).
