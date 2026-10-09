# Personal Finance Agent: Agentic AI Budget & Spending Assistant

> **Observe ➔ Understand ➔ Detect ➔ Recommend ➔ Improve**
>
> A privacy-first, multi-user web application designed for financial awareness in India (INR, Rs.). Built with **FastAPI**, **LangGraph**, **SQLAlchemy 2.0**, **PostgreSQL / SQLite**, and **Streamlit**.

---

## 1. Product & Architecture Overview

The **Personal Finance Agent** enables members of the public to sign up, upload their bank statements (CSV/Excel), and receive automated categorization, explainable anomaly detection, budget tracking, and proactive weekly recommendations.

> [!IMPORTANT]
> **Financial Awareness Disclaimer:** This tool supports financial awareness and planning; it is **NOT** a financial adviser, investment counselor, or tax planner. No recommendation is ever executed automatically; the user must explicitly review and accept suggestions.

### Multi-Agent LangGraph Pipeline
1. **Ingestion Agent**: Normalizes statement rows, validates format/row limits, handles nulls safely, and computes SHA-256 deduplication hashes.
2. **Category Agent**: Hybrid classification using per-user category rules -> global keyword mapping -> LLM Gateway fallback.
3. **Anomaly Agent**: Statistical Z-Score / IQR baseline comparison flagging explainable spending anomalies with user feedback adjustments.
4. **Budget Agent**: Tracks weekly targets vs actual spend per category and flags overspending in INR (Rs.).
5. **Weekly Advisor Agent**: Computes actionable savings recommendations in Python, rephrased by LLM into clear plain-language advice with strict guardrails.

---

## 2. Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic
- **Database**: PostgreSQL (Row-Level Security) / SQLite
- **Agent Orchestration**: LangGraph StateGraph
- **Data Processing**: Pandas
- **LLM Gateway**: Gemini API (`google-generativeai`) with full rule-based offline fallback
- **Frontend**: Streamlit multi-page UI (communicates ONLY via REST API)
- **Auth**: Argon2id password hashing, short-lived JWT access tokens, httpOnly refresh cookies, DPDP age gate (18+)
- **Security**: AES-256 field encryption at rest, rate limiting (slowapi), prompt-injection sanitization, CSV formula injection defense
- **Infra & Testing**: Docker, docker-compose, Nginx, pytest, ruff, mypy, bandit, pip-audit

---

## 3. Quick Start & Installation

### Option A: Local Development Setup

1. **Navigate to Project Directory**:
   ```bash
   cd personal_finance_agent
   ```

2. **Set up Virtual Environment & Install Dependencies**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r backend/requirements.txt
   pip install -r frontend/requirements.txt
   ```

3. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   ```

4. **Seed Sample Data & Run Evaluation**:
   ```bash
   # Generate synthetic 12-week sample transactions
   python data/generate_sample_data.py

   # Run empirical system evaluation benchmark
   PYTHONPATH=backend python evaluation/evaluate.py
   ```

5. **Start FastAPI Backend (Port 8000)**:
   ```bash
   uvicorn app.main:app --reload --port 8000 --app-dir backend
   ```

6. **Start Streamlit Frontend (Port 8501)**:
   ```bash
   streamlit run frontend/app.py
   ```
   Open `http://localhost:8501` in your browser to access the application!

---

### Option B: Docker Compose Setup

```bash
docker-compose up --build -d
```
- **Streamlit Frontend**: `http://localhost:8501`
- **FastAPI Documentation**: `http://localhost:8000/docs`
- **Nginx Gateway**: `http://localhost`

---

## 4. Running Verification & Security Tests

```bash
# Unit & Integration Tests with Coverage
PYTHONPATH=backend pytest backend/app/tests/ -v --cov=backend/app --cov-report=term-missing

# IDOR Security Scoping Test
PYTHONPATH=backend pytest backend/app/tests/test_idor.py -v

# Prompt Injection Defense Test
PYTHONPATH=backend pytest backend/app/tests/test_prompt_injection.py -v

# Security Static Analysis
bandit -r backend/app/
pip-audit
```

---

## 5. Operations & Runbook

### Health Checks
- `GET /health` - Liveness probe.
- `GET /ready` - Database readiness probe.

### Backup & Retention Policy Note
- Raw user transactions can be set to auto-expire after N months according to DPDP retention configuration.
- Daily database backups are recommended for production PostgreSQL instances.

---

## 6. Regulatory Note & Future Work

### RBI Account Aggregator (AA) Framework Integration
Real bank statement integration in India requires onboarding with an RBI-licensed Account Aggregator (AA) provider (e.g., Anumati, OneMoney, Finvu) following FIP/FIU regulatory specifications and consent management architecture.

### Limitations & Future Roadmap
1. **Account Aggregator Adapter**: Replace manual CSV upload with live AA SDK adapter.
2. **Personalized Dynamic Thresholds**: Expand anomaly baselines using machine learning time-series models (Prophet / Holt-Winters).
3. **Multilingual NLU Insights**: Extend LLM prompts to support Hindi, Kannada, Tamil, Telugu, and Marathi advice phrasing.
4. **Goal-Aware Optimization**: Add linear programming goal solvers for long-term debt and savings target acceleration.
