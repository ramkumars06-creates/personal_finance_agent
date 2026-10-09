"""
4. Budget Agent: Manages weekly targets, actual spend accumulation, variance computation, and overspend detection.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal


class BudgetAgent:
    """Agent that computes budget-vs-actual metrics and flags overspending."""

    DEFAULT_WEEKLY_WEIGHTS = {
        "food": 0.20,
        "groceries": 0.25,
        "transport": 0.15,
        "bills": 0.15,
        "shopping": 0.10,
        "entertainment": 0.05,
        "health": 0.05,
        "education": 0.05,
        "other": 0.05
    }

    def compute_budget_vs_actual(
        self,
        weekly_transactions: List[Dict[str, Any]],
        user_budgets: List[Dict[str, Any]],
        monthly_income: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Compute target vs actual spend per category for the week.
        """
        # Build user target map
        target_map = {b["category"]: float(b["weekly_target_amount"]) for b in user_budgets}

        # If no custom budgets set, generate suggested defaults based on monthly income
        if not target_map:
            weekly_income = (monthly_income or 40000.0) / 4.0
            for cat, weight in self.DEFAULT_WEEKLY_WEIGHTS.items():
                target_map[cat] = round(weekly_income * weight, 2)

        # Accumulate actual weekly spend per category
        actual_map: Dict[str, float] = {cat: 0.0 for cat in self.DEFAULT_WEEKLY_WEIGHTS.keys()}
        total_weekly_spend = 0.0

        for txn in weekly_transactions:
            if txn.get("transaction_type", "debit") == "debit":
                cat = txn.get("category", "other")
                amt = float(txn.get("amount", 0.0))
                actual_map[cat] = actual_map.get(cat, 0.0) + amt
                total_weekly_spend += amt

        category_analysis = {}
        overspend_categories = []

        for cat, target in target_map.items():
            actual = actual_map.get(cat, 0.0)
            variance_rs = actual - target
            variance_pct = ((actual - target) / target * 100.0) if target > 0 else 0.0
            is_overbudget = actual > target

            category_analysis[cat] = {
                "category": cat,
                "weekly_target_amount": round(target, 2),
                "actual_amount": round(actual, 2),
                "variance_rs": round(variance_rs, 2),
                "variance_pct": round(variance_pct, 1),
                "is_overbudget": is_overbudget
            }

            if is_overbudget:
                overspend_categories.append(cat)

        return {
            "total_weekly_spend": round(total_weekly_spend, 2),
            "category_analysis": category_analysis,
            "overspend_categories": overspend_categories,
            "targets_used": target_map
        }
