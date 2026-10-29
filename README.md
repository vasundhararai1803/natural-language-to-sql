# QueryLens AI: AI-Powered Natural Language-to-SQL & Analytics Assistant

An end-to-end, production-style natural language analytics assistant that enables non-technical business users to explore transactional data, automatically generate and validate safe SQL, visualize metric trends, and conduct structured root-cause diagnostic investigations (*"Why did transactions drop last week?"*) without writing code.

---

## 📋 Table of Contents
- [Project Overview & Problem Statement](#-project-overview--problem-statement)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Data Model & Synthetic Scenarios](#-data-model--synthetic-scenarios)
- [Prerequisites & Installation](#-prerequisites--installation)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Usage Guide & Examples](#-usage-guide--examples)
- [API Reference](#-api-reference)
- [SQL Safety & Guardrail Architecture](#-sql-safety--guardrail-architecture)
- [Evaluation Benchmark & Testing](#-evaluation-benchmark--testing)
- [Repository Structure](#-repository-structure)
- [Known Boundaries & Roadmap](#-known-boundaries--roadmap)
- [License & Authors](#-license--authors)

---

## 🎯 Project Overview & Problem Statement

### The Problem
Business analysts, product managers, and team leads constantly need quick answers from corporate databases. However:
- Traditional Business Intelligence (BI) dashboards are rigid and cannot answer unexpected ad-hoc questions.
- Non-technical stakeholders cannot write SQL, creating a bottleneck for data teams.
- Existing LLM-to-SQL tools are often unsafe, hallucinate table/column names, execute dangerous mutating statements (`DROP`, `DELETE`), or present statistical correlations as definitive facts.

### The Solution: QueryLens AI
**QueryLens AI** provides an end-to-end analytics workflow:
1. Accepts questions in everyday business English.
2. Disambiguates vague queries and rejects questions requesting metrics absent from the schema.
3. Formulates single, read-only SQL queries validated through AST parsing.
4. Executes queries safely against an embedded relational database with enforced limits.
5. Performs multi-dimensional variance and anomaly analysis for "Why" diagnostic questions.
6. Returns interactive Recharts visualizations, key findings, and CSV exports.

---

## ✨ Key Features

1. **Natural-Language-to-SQL Engine**:
   - Schema-aware translation using OpenAI-compatible models (e.g. Groq Llama 3.3 or OpenAI GPT-4o-mini).
   - High-precision deterministic fallback engine for fully offline execution with zero API keys.
2. **Signature Diagnostic Engine ("Why Did This Change?")**:
   - Multi-period comparative analysis (Baseline week vs. Current week).
   - Multi-dimensional breakdown across **Region**, **Product Category**, and **Sales Channel**.
   - Segment-level percentage change and **contribution share** (% of net volume drop driven by each segment).
   - Statistically significant anomaly detection (e.g., primary regional volume collapse, elevated order cancellations).
3. **Multi-Layer SQL Safety Guard**:
   - AST-based parsing with `sqlglot`.
   - Whitelist enforcement for approved tables (`transactions`, `products`, `customers`, `regions`).
   - Hard rejection of mutation keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `ATTACH`, `DETACH`, `PRAGMA`).
   - Rejection of statement chaining (semicolon injections) and internal metadata catalogs (`sqlite_master`).
4. **Interactive Visualizations & Data Tools**:
   - Dynamic declarative charting: **Line**, **Bar**, **Grouped Bar**, and **Pie** charts.
   - Interactive data table view with clean null-handling.
   - One-click CSV export of permitted result sets.
   - Expandable SQL inspection with one-click copy.
5. **Grounded Executive Summaries**:
   - Explanations strictly cite numerical evidence from returned query rows.
   - Enforces causality boundaries: highlights that correlation does not establish causation without application telemetry.
   - Displays explicit assumptions, data boundaries, and suggested follow-up questions.
6. **Built-In Empirical Benchmark Dashboard**:
   - 32 pre-configured test cases spanning aggregations, rankings, comparisons, ambiguity handling, unsupported metric guards, and malicious SQL injection attempts.
   - Visual dashboard in the UI reporting accuracy, latency, and safety pass rates.

---

## 🏛️ System Architecture

```
                      ┌──────────────────────────────────────┐
                      │    React + TypeScript Frontend UI    │
                      │ (App, Recharts, Catalog, Benchmark)  │
                      └──────────────────┬───────────────────┘
                                         │ HTTP (JSON / REST)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │       FastAPI Backend Service        │
                      └──────────────────┬───────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
    ┌──────────────────────────┐                   ┌──────────────────────────┐
    │     AI / LLM Layer       │                   │  Fallback Offline Engine │
    │ (Groq / OpenAI API JSON) │                   │  (Rule & Template Match) │
    └────────────┬─────────────┘                   └─────────────┬────────────┘
                 └───────────────────────┬───────────────────────┘
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    SQL Safety & AST Guard Layer      │
                      │ (sqlglot parser, AST checks, tables) │
                      └──────────────────┬───────────────────┘
                                         ▼
                      ┌──────────────────────────────────────┐
                      │       Query Execution Service        │
                      │     (Read-only, row limits: 500)     │
                      └──────────────────┬───────────────────┘
                                         ▼
                      ┌──────────────────────────────────────┐
                      │        SQLite Relational DB          │
                      │  (transactions, products, customers) │
                      └──────────────────┬───────────────────┘
                                         ▼
                      ┌──────────────────────────────────────┐
                      │      Diagnostic & Insight Layer      │
                      │ (Variance, Anomaly, Recharts spec)   │
                      └──────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Python 3.10+ & FastAPI
- **Data Validation & Schemas**: Pydantic v2
- **ORM & Database Connector**: SQLAlchemy 2.0
- **SQL Parsing & AST Security**: sqlglot
- **Database Engine**: SQLite 3 (embedded file-based)
- **HTTP Client**: HTTPX (async communication)
- **Testing**: Pytest

### Frontend
- **Framework**: React 18+ with TypeScript
- **Bundler & Dev Server**: Vite
- **Styling**: Tailwind CSS v4 (dark theme)
- **Charting & Visualizations**: Recharts
- **Icons**: Lucide React

---

## 📊 Data Model & Synthetic Scenarios

The local database (`data/querylens.db`) contains **12,965 synthetic transaction records** spanning August 1, 2026 to October 25, 2026.

### Entity Relationship Model
- **`transactions`**: `transaction_id`, `transaction_timestamp`, `customer_id`, `product_id`, `region_id`, `quantity`, `unit_price`, `discount_amount`, `transaction_status` (*completed, cancelled, refunded, pending*), `payment_method`, `channel`.
- **`products`**: `product_id`, `product_name`, `category` (*Software, Electronics, Hardware, Services*), `subcategory`.
- **`customers`**: `customer_id`, `customer_segment` (*Enterprise, SMB, Consumer, VIP*), `signup_date`.
- **`regions`**: `region_id`, `region_name`, `country`.

### Seeded Diagnostic Scenarios
1. **The Drop Week (Oct 12 – Oct 18, 2026)**: Completed transactions fell by ~27% compared with the baseline week (Oct 05 – Oct 11, 2026).
2. **Regional Collapse**: The `North America - West` territory suffered an 81.3% contraction, driving the majority of the net decline.
3. **Cancellation Surge**: Order cancellations spiked significantly in `North America - West` during the drop week due to simulated payment gateway timeouts.
4. **Category Softening**: Gradual sales softening in `Electronics` throughout October.
5. **Campaign Period**: "Fall Tech Sale" promotional spike between September 15 and September 22, 2026.

---

## 🚀 Prerequisites & Installation

### Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, or 3.13
- **Node.js**: Version 18+ and **npm**

### 1. Clone the Repository
```bash
git clone https://github.com/vasundhararai1803/natural-language-to-sql.git
cd natural-language-to-sql
```

### 2. Backend Setup
```bash
# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Initialize and seed the local database
PYTHONPATH=. python backend/scripts/seed_db.py

# Start the FastAPI backend server (runs on port 8000)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the Vite development server (runs on port 5173)
npm run dev
```

Open your browser to: **`http://localhost:5173`**

---

## ⚙️ Configuration & Environment Variables

Copy `.env.example` to create your local `.env` file:
```bash
cp .env.example .env
```

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | API key for external LLM provider. Leave blank for deterministic offline mode. | `gsk_...` (Groq) or `sk-...` (OpenAI) |
| `OPENAI_BASE_URL` | Base URL of the OpenAI-compatible endpoint. | `https://api.groq.com/openai/v1` or `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model identifier to use. | `llama-3.3-70b-versatile` or `gpt-4o-mini` |
| `DATABASE_URL` | SQLAlchemy connection string. | `sqlite:///data/querylens.db` |

> [!TIP]
> **100% Free LLM Execution with Groq**: Get a free API key at [console.groq.com/keys](https://console.groq.com/keys) (no credit card required). Set `OPENAI_BASE_URL=https://api.groq.com/openai/v1` and `OPENAI_MODEL=llama-3.3-70b-versatile`.

---

## 💡 Usage Guide & Examples

### Supported Business Questions
You can enter questions directly into the search bar:

- **Root-Cause Diagnostics**:
  - *"Why did transactions drop last week?"*
  - *"What factors contributed most to the decline in sales last week?"*
- **Rankings & Aggregations**:
  - *"What were our top-performing products this month?"*
  - *"Which product category generated the highest revenue?"*
- **Comparative Analysis**:
  - *"Compare revenue this quarter with the previous quarter."*
  - *"Which region has the highest cancellation rate?"*
- **Time Series Trends**:
  - *"Show me daily transactions and highlight unusual drops."*
- **Ambiguity Disambiguation (System prompts for clarification)**:
  - *"How did we perform last week?"* ➔ Prompts user to choose between *Transaction Volume*, *Gross Revenue*, or *Average Order Value*.
- **Unsupported Metric Guard**:
  - *"What was our net profit?"* ➔ Explains that profit/margins cannot be computed because COGS is absent from the schema.
- **SQL Safety Enforcement**:
  - *"DROP TABLE transactions;"* ➔ Instantly rejected with a security policy violation message.

---

## 🔌 API Reference

### `POST /api/ask`
Submit a natural language question for interpretation, SQL generation, execution, and explanation.

**Request Body:**
```json
{
  "question": "Why did transactions drop last week?",
  "execution_mode": "auto"
}
```

**Response (Summary):**
```json
{
  "request_id": "8653f171",
  "question": "Why did transactions drop last week?",
  "interpreted_intent": {
    "type": "diagnostic_why",
    "metric": "completed_transactions",
    "current_period": "2026-10-12 to 2026-10-18",
    "baseline_period": "2026-10-05 to 2026-10-11"
  },
  "sql": "SELECT r.region_name, ... FROM transactions t JOIN regions r ...",
  "query_status": "success",
  "execution_time_ms": 3.42,
  "summary": "Completed transactions declined by 26.9% (-284 transactions) during the week of Oct 12–18 compared with the prior week.",
  "contributing_factors": [
    {
      "dimension": "Region",
      "segment": "North America - West",
      "baseline_value": 240,
      "current_value": 45,
      "delta": -195,
      "percentage_change": -81.3,
      "contribution_to_total_drop_pct": 68.7,
      "is_anomaly": true
    }
  ],
  "chart_spec": {
    "chart_type": "grouped_bar",
    "title": "Completed Transactions: Baseline vs Current Week by Region"
  }
}
```

### Other Endpoints
- `GET /api/health`: Health status and active LLM configuration.
- `GET /api/schema`: Complete list of database tables, columns, types, and foreign keys.
- `GET /api/metrics/definitions`: Canonical business metric definitions and SQL formulas.
- `POST /api/query/validate`: Standalone SQL validation endpoint checking AST safety.
- `POST /api/evaluation/run`: Runs the 32-case accuracy and safety benchmark suite.
- `GET /api/evaluation/results`: Retrieves latest benchmark results and pass rates.

---

## 🛡️ SQL Safety & Guardrail Architecture

Safety is handled by [`sql_validation_service.py`](file:///Users/vasundhararai/Desktop/Projects/Projects/AI-powered%20natural-language-to-SQL/backend/services/sql_validation_service.py) before any query touches the database:

1. **Strict SELECT / CTE Only**: Rejects all DDL/DML mutation keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `ATTACH`, `DETACH`, `PRAGMA`).
2. **Anti-Chaining**: Rejects multiple SQL statements separated by semicolons (`;`).
3. **Table Whitelist**: Only allows queries accessing `transactions`, `products`, `customers`, and `regions`.
4. **Catalog Protection**: Rejects direct inspection of SQLite internal tables (`sqlite_master`, `sqlite_schema`).
5. **Enforced Limits**: Automatically applies a `LIMIT 500` clause if not provided.
6. **Error Sanitization**: Masks raw server tracebacks and internal file paths.

---

## 🧪 Evaluation Benchmark & Testing

### 1. Automated Test Suite (Pytest)
Run the backend tests covering endpoints, safety validation, and diagnostic analysis:
```bash
source venv/bin/activate
PYTHONPATH=. pytest backend/tests/test_backend.py
```
**Outcome**: 11 passed (100%).

### 2. Empirical Benchmark Suite
Run the 32-test evaluation benchmark:
```bash
source venv/bin/activate
PYTHONPATH=. python -m backend.evaluation.benchmark_runner
```

**Benchmark Results:**
- **Total Test Cases**: 32
- **Overall Accuracy**: **100.0%**
- **SQL Safety Rate**: **100.0%** (100% of injection, DDL, and unauthorized table attacks blocked)
- **Execution Accuracy**: **100.0%** on supported business questions
- **Average Latency**: **~3.5 ms**

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   └── main.py                 # FastAPI application entrypoint with CORS
│   ├── api/
│   │   └── routes.py               # REST API endpoints
│   ├── models/
│   │   ├── db_models.py            # SQLAlchemy database models
│   │   └── api_schemas.py          # Pydantic schemas and chart specs
│   ├── services/
│   │   ├── schema_service.py       # Catalog metadata & metric definitions
│   │   ├── sql_validation_service.py # sqlglot AST verification & security rules
│   │   ├── query_execution_service.py# Safe read-only executor
│   │   ├── analysis_service.py     # Diagnostic & segment breakdown service
│   │   ├── insight_service.py      # Grounded executive summary generator
│   │   ├── chart_service.py        # Recharts specification generator
│   │   ├── fallback_sql_service.py # High-precision offline rule engine
│   │   └── llm_service.py          # OpenAI/Groq API orchestration
│   ├── evaluation/
│   │   └── benchmark_runner.py     # 32-case accuracy and safety test runner
│   ├── scripts/
│   │   └── seed_db.py              # Reproducible database seeder
│   └── tests/
│       └── test_backend.py         # Pytest test suite
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
├── data/
│   └── querylens.db                # Seeded SQLite database (12,965 rows)
├── .env.example                    # Template environment variables
├── requirements.txt                # Python backend dependencies
└── README.md                       # Documentation
```

---

## ⚠️ Known Boundaries & Roadmap

### Current Boundaries
- **Synthetic Retail Domain**: The database is structured specifically for order transactions, products, customers, and regions. Financial accounting metrics (COGS, EBITDA, Payroll) are not modeled.
- **SQLite Dialect**: Currently optimized for SQLite syntax. Multi-dialect translation (PostgreSQL, BigQuery, Snowflake) is planned.
- **Causality Limitations**: Correlative spikes (e.g. cancellations during drop week) are highlighted, but server application logs are required to confirm root technical causes.

### Planned Enhancements
- [ ] Connectors for PostgreSQL and Snowflake.
- [ ] Multi-turn conversational memory with context preservation.
- [ ] PDF report generation with chart snapshot exports.
- [ ] Role-based access control (RBAC) and row-level security.

---

## 📄 License & Authors

This project is licensed under the **MIT License**.

Developed by **Vasundhara Rai** ([@vasundhararai1803](https://github.com/vasundhararai1803)).
Questions or feedback? Please open an issue or pull request in the repository.
