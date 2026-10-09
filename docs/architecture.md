# System Architecture Documentation

## Overview
The **Personal Finance Agent** is built around a decoupled multi-tier architecture:
1. **Frontend**: Streamlit multi-page UI communicating exclusively via REST API.
2. **Backend**: FastAPI 0.110+, SQLAlchemy 2.0, Pydantic v2.
3. **Agent Orchestrator**: LangGraph StateGraph engine coordinating 5 specialized agents.
4. **Database**: PostgreSQL (with Row-Level Security) or SQLite.

```mermaid
graph TD
    Client[Streamlit UI] -->|REST API| API[FastAPI Gateway]
    API -->|Auth & Scoping| Repo[User-Scoped Repository]
    API -->|Orchestrate| Graph[LangGraph Pipeline]
    Graph --> Agent1[Ingestion Agent]
    Graph --> Agent2[Category Agent]
    Graph --> Agent3[Anomaly Agent]
    Graph --> Agent4[Budget Agent]
    Graph --> Agent5[Weekly Advisor]
    Agent2 --> LLM[Gemini Gateway / Rule Fallback]
    Agent5 --> LLM
    Repo --> DB[(PostgreSQL / SQLite)]
```
