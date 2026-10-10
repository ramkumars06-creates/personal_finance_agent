"""
Agent Unit Tests: Ingestion, Categorization, Anomaly Detection, Budgeting, and Advisor.
"""
from app.agents.advisor_agent import AdvisorAgent
from app.agents.anomaly_agent import AnomalyAgent
from app.agents.budget_agent import BudgetAgent
from app.agents.category_agent import CategoryAgent
from app.agents.ingestion_agent import IngestionAgent


def test_ingestion_csv_parsing():
    agent = IngestionAgent()
    csv_bytes = b"Date,Description,Amount,Type\n2026-03-01,Swiggy Order,450.0,debit\n2026-03-02,Amazon,1200.0,debit\n"
    records, stats = agent.parse_csv_file(csv_bytes, "statement.csv", "user_1")
    
    assert len(records) == 2
    assert records[0]["normalized_merchant"] == "SWIGGY ORDER"
    assert records[0]["amount"] == 450.0
    assert stats["valid_records"] == 2


def test_category_agent_rule_fallback():
    agent = CategoryAgent()
    txns = [{"normalized_merchant": "SWIGGY ORDER"}, {"normalized_merchant": "UBER RIDE"}]
    categorized, stats = agent.categorize_transactions(txns)
    
    assert len(categorized) == 2
    assert categorized[0]["category"] == "food"
    assert categorized[1]["category"] == "transport"


def test_anomaly_agent_signals():
    agent = AnomalyAgent()
    history = [
        {"category": "food", "amount": 200.0, "normalized_merchant": "swiggy", "transaction_type": "debit"},
        {"category": "food", "amount": 250.0, "normalized_merchant": "swiggy", "transaction_type": "debit"}
    ]
    new_txns = [
        {"id": "t1", "category": "food", "amount": 6000.0, "normalized_merchant": "unknown_luxe", "transaction_type": "debit"}
    ]
    anomalies = agent.detect_anomalies(new_txns, history)
    
    assert len(anomalies) == 1
    assert anomalies[0]["severity"] in ["medium", "high"]
    assert "category_baseline_deviation" in anomalies[0]["signals_fired"]


def test_budget_agent_computation():
    agent = BudgetAgent()
    txns = [
        {"category": "food", "amount": 3000.0, "transaction_type": "debit"},
        {"category": "transport", "amount": 500.0, "transaction_type": "debit"}
    ]
    budgets = [{"category": "food", "weekly_target_amount": 2000.0}]
    
    res = agent.compute_budget_vs_actual(txns, budgets)
    assert res["total_weekly_spend"] == 3500.0
    assert "food" in res["overspend_categories"]


def test_advisor_agent():
    agent = AdvisorAgent()
    budget_analysis = {
        "total_weekly_spend": 3500.0,
        "category_analysis": {
            "food": {"category": "food", "actual_amount": 3000.0, "weekly_target_amount": 2000.0, "variance_rs": 1000.0, "variance_pct": 50.0, "is_overbudget": True}
        },
        "overspend_categories": ["food"]
    }
    advice = agent.generate_weekly_advice(budget_analysis)
    
    assert len(advice["recommendations"]) > 0
    assert "food" in advice["recommendations"][0]["category"].lower()
    assert advice["disclaimer"] is not None
