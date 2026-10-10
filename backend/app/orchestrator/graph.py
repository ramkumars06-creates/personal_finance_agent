"""
LangGraph Orchestrator: Multi-agent graph flow managing shared state, execution timing, and pipeline tracing.
"""
import time
from typing import Any, TypedDict

from app.agents.advisor_agent import AdvisorAgent
from app.agents.anomaly_agent import AnomalyAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.category_agent import CategoryAgent
from app.agents.ingestion_agent import IngestionAgent
from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    """Typed shared state passed across graph nodes."""
    user_id: str
    execution_id: str
    run_type: str  # "upload" | "weekly"
    raw_file_bytes: bytes | None
    filename: str | None
    input_transactions: list[dict[str, Any]] | None
    historical_transactions: list[dict[str, Any]] | None
    user_budgets: list[dict[str, Any]] | None
    monthly_income: float | None
    savings_goal: float | None
    
    # Node Outputs
    parsed_transactions: list[dict[str, Any]]
    ingestion_stats: dict[str, Any]
    categorized_transactions: list[dict[str, Any]]
    categorization_stats: dict[str, int]
    anomalies_detected: list[dict[str, Any]]
    budget_analysis: dict[str, Any]
    weekly_advice: dict[str, Any]
    
    # Trace & Metadata
    agent_trace: list[dict[str, Any]]
    fallback_mode_used: bool


# Node Implementations
def ingestion_node(state: AgentState) -> dict[str, Any]:
    start_time = time.time()
    trace = list(state.get("agent_trace", []))
    
    file_bytes = state.get("raw_file_bytes")
    filename = state.get("filename", "upload.csv")
    user_id = state.get("user_id", "")
    
    if file_bytes:
        agent = IngestionAgent()
        records, stats = agent.parse_csv_file(file_bytes, filename, user_id)
    else:
        records = state.get("input_transactions", [])
        stats = {"valid_records": len(records), "deduplicated_count": 0, "uncertain_count": 0}

    duration_ms = (time.time() - start_time) * 1000.0
    trace.append({
        "step": 1,
        "agent_name": "IngestionAgent",
        "status": "success",
        "duration_ms": round(duration_ms, 2),
        "summary": f"Parsed {len(records)} valid records ({stats.get('uncertain_count', 0)} uncertain)."
    })

    return {
        "parsed_transactions": records,
        "ingestion_stats": stats,
        "agent_trace": trace
    }


def category_node(state: AgentState) -> dict[str, Any]:
    start_time = time.time()
    trace = list(state.get("agent_trace", []))
    parsed = state.get("parsed_transactions", [])

    agent = CategoryAgent()
    categorized, stats = agent.categorize_transactions(parsed)

    duration_ms = (time.time() - start_time) * 1000.0
    trace.append({
        "step": 2,
        "agent_name": "CategoryAgent",
        "status": "success",
        "duration_ms": round(duration_ms, 2),
        "summary": f"Assigned categories. Rule matches: {stats.get('rule', 0)}, LLM: {stats.get('llm', 0)}, User Rules: {stats.get('user_rule', 0)}."
    })

    return {
        "categorized_transactions": categorized,
        "categorization_stats": stats,
        "agent_trace": trace
    }


def anomaly_node(state: AgentState) -> dict[str, Any]:
    start_time = time.time()
    trace = list(state.get("agent_trace", []))
    categorized = state.get("categorized_transactions", [])
    history = state.get("historical_transactions", [])

    agent = AnomalyAgent()
    anomalies = agent.detect_anomalies(categorized, history)

    duration_ms = (time.time() - start_time) * 1000.0
    trace.append({
        "step": 3,
        "agent_name": "AnomalyAgent",
        "status": "success",
        "duration_ms": round(duration_ms, 2),
        "summary": f"Identified {len(anomalies)} explainable anomaly alerts."
    })

    return {
        "anomalies_detected": anomalies,
        "agent_trace": trace
    }


def budget_node(state: AgentState) -> dict[str, Any]:
    start_time = time.time()
    trace = list(state.get("agent_trace", []))
    categorized = state.get("categorized_transactions", [])
    user_budgets = state.get("user_budgets", [])
    income = state.get("monthly_income")

    agent = BudgetAgent()
    analysis = agent.compute_budget_vs_actual(categorized, user_budgets, income)

    duration_ms = (time.time() - start_time) * 1000.0
    trace.append({
        "step": 4,
        "agent_name": "BudgetAgent",
        "status": "success",
        "duration_ms": round(duration_ms, 2),
        "summary": f"Calculated weekly spend (Rs. {analysis['total_weekly_spend']:,.2f}). Overbudget categories: {len(analysis['overspend_categories'])}."
    })

    return {
        "budget_analysis": analysis,
        "agent_trace": trace
    }


def advisor_node(state: AgentState) -> dict[str, Any]:
    start_time = time.time()
    trace = list(state.get("agent_trace", []))
    analysis = state.get("budget_analysis", {})
    savings_goal = state.get("savings_goal")

    agent = AdvisorAgent()
    advice = agent.generate_weekly_advice(analysis, savings_goal)

    duration_ms = (time.time() - start_time) * 1000.0
    trace.append({
        "step": 5,
        "agent_name": "WeeklyAdvisorAgent",
        "status": "success",
        "duration_ms": round(duration_ms, 2),
        "summary": f"Generated {len(advice['recommendations'])} python recommendations. Method: {advice['generation_method']}."
    })

    fallback_used = advice.get("generation_method") == "template_fallback"

    return {
        "weekly_advice": advice,
        "agent_trace": trace,
        "fallback_mode_used": fallback_used
    }


def build_finance_agent_graph():
    """Build and compile the LangGraph StateGraph pipeline."""
    workflow = StateGraph(AgentState)

    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("category", category_node)
    workflow.add_node("anomaly", anomaly_node)
    workflow.add_node("budget", budget_node)
    workflow.add_node("advisor", advisor_node)

    workflow.set_entry_point("ingestion")
    workflow.add_edge("ingestion", "category")
    workflow.add_edge("category", "anomaly")
    workflow.add_edge("anomaly", "budget")
    workflow.add_edge("budget", "advisor")
    workflow.add_edge("advisor", END)

    return workflow.compile()


# Singleton compiled graph instance
finance_pipeline = build_finance_agent_graph()
