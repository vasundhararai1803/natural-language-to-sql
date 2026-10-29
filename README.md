# QueryLens AI

An AI-powered analytics assistant that translates plain-English business questions into validated SQL, executes them safely, and explains the trends behind business metrics without writing code.

---

## 🎯 Why This Project Was Built (Intent)

Non-technical teams (product managers, operations, business analysts) often need immediate answers from corporate databases, but they don't know SQL. At the same time, giving raw LLMs direct database access is dangerous—they can hallucinate queries, mutate data with `DROP` or `DELETE`, and misinterpret correlation as causation.

**QueryLens AI was built to solve this safely:**
- Allow non-technical users to ask questions like *"Why did transactions drop last week?"* or *"What were our top-performing products?"*.
- Translate intent into read-only SQL validated through AST parsers before touching the database.
- Go beyond basic charts: perform multi-dimensional root-cause analysis (segment contributions and anomalies).
- Ground every executive summary strictly in real retrieved data with zero fabricated numbers.

---

## ⚡ What It Does

1. **Natural Language to SQL**: Converts questions into single, read-only SQLite `SELECT` queries.
2. **Root-Cause Diagnostics ("Why Did This Change?")**: Analyzes period-over-period variance, isolates which region or product caused a volume drop, and quantifies each segment's exact percentage contribution.
3. **AST SQL Safety Guard**: Uses `sqlglot` to enforce a strict table whitelist, prevent query chaining (`;`), and block all data-modifying commands (`DROP`, `DELETE`, `INSERT`, `UPDATE`).
4. **Interactive Visualizations**: Dynamically renders Line, Bar, Grouped Bar, and Pie charts using Recharts.
5. **Grounded Executive Insights**: Summarizes findings in plain business English while explicitly distinguishing correlation from causation.
6. **Data Inspection & Export**: Allows inspecting generated SQL, viewing the raw data table, and exporting results to CSV.

---

## 🔄 How It Operates

```
User Question
    │
    ▼
1. Interpret Intent ────► Disambiguate vague questions or reject unsupported metrics
    │
    ▼
2. Formulate SQL   ────► Via Groq / OpenAI LLM (or built-in offline fallback engine)
    │
    ▼
3. Validate SQL    ────► AST safety parser (only read-only SELECT; blocks injections & DDL)
    │
    ▼
4. Execute Query   ────► Safe read-only execution with row limits (SQLite)
    │
    ▼
5. Analyze & Chart ────► Compute segment deltas, generate Recharts spec & plain-English summary
```

---

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, sqlglot, Pytest
- **Database**: SQLite (12,965 seeded realistic transaction records)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons
- **AI Integration**: Groq (Llama 3.3) / OpenAI-compatible API + Deterministic offline fallback engine

---

## 🚀 Quickstart (Running Locally)

### 1. Backend
```bash
# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed the database
PYTHONPATH=. python backend/scripts/seed_db.py

# Start the API server (http://127.0.0.1:8000)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## ⚙️ Configuration (Optional Free AI Key)

QueryLens AI works **100% offline out-of-the-box** using its built-in rule engine. 

To enable live LLM generation with **Groq (Free)**, create a `.env` file:
```env
OPENAI_API_KEY=gsk_your_free_groq_key_here
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile
DATABASE_URL=sqlite:///data/querylens.db
```

---

## 🧪 Testing & Evaluation

- **Unit & Integration Tests**:
  ```bash
  source venv/bin/activate
  PYTHONPATH=. pytest backend/tests/test_backend.py
  ```
- **32-Case Accuracy & Safety Benchmark**:
  ```bash
  source venv/bin/activate
  PYTHONPATH=. python -m backend.evaluation.benchmark_runner
  ```
  *(100% overall accuracy, 100% unsafe SQL rejection rate, ~3.5ms average latency)*

---

## 📄 License
MIT License. Created by [Vasundhara Rai](https://github.com/vasundhararai1803).
