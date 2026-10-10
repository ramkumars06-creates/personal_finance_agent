"""
Weekly Advisor API: Weekly Summaries, Recommendations, and Acceptance Actions.
"""
from datetime import date

from app.agents.advisor_agent import AdvisorAgent
from app.agents.budget_agent import BudgetAgent
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.db_models import User, WeeklySummary
from app.repositories.user_scoped_repo import (
    BudgetRepository,
    TransactionRepository,
    UserScopedRepository,
)
from app.schemas.api_schemas import RecommendationItem, WeeklySummaryResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/advisor", tags=["Weekly Advisor"])


@router.get("/weekly", response_model=WeeklySummaryResponse)
def get_weekly_advice(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch latest weekly summary and actionable recommendations."""
    repo = UserScopedRepository(WeeklySummary, db, current_user.id)
    summaries = repo.get_all(limit=1)

    if summaries:
        s = summaries[0]
        recs = [
            RecommendationItem(
                category=r.get("category", "General"),
                rs_change=float(r.get("rs_change", 0.0)),
                reason=r.get("reason", ""),
                savings_effect=r.get("savings_effect", "")
            ) for r in (s.recommendations or [])
        ]
        return WeeklySummaryResponse(
            id=s.id,
            week_start_date=s.week_start_date,
            week_end_date=s.week_end_date,
            total_spend=float(s.total_spend),
            category_breakdown=s.category_breakdown or {},
            recommendations=recs,
            llm_explanation=s.llm_explanation,
            is_accepted=s.is_accepted
        )

    # If no summary generated yet, run on-demand calculation
    txn_repo = TransactionRepository(db, current_user.id)
    txns = [{"category": t.category, "amount": float(t.amount), "transaction_type": t.transaction_type} for t in txn_repo.get_all(limit=500)]

    budget_repo = BudgetRepository(db, current_user.id)
    user_budgets = [{"category": b.category, "weekly_target_amount": float(b.weekly_target_amount)} for b in budget_repo.get_all()]

    b_agent = BudgetAgent()
    income = float(current_user.monthly_income) if current_user.monthly_income else None
    budget_analysis = b_agent.compute_budget_vs_actual(txns, user_budgets, income)

    adv_agent = AdvisorAgent()
    savings_goal = float(current_user.savings_goal) if current_user.savings_goal else None
    advice = adv_agent.generate_weekly_advice(budget_analysis, savings_goal)

    recs = [
        RecommendationItem(
            category=r.get("category", "General"),
            rs_change=float(r.get("rs_change", 0.0)),
            reason=r.get("reason", ""),
            savings_effect=r.get("savings_effect", "")
        ) for r in advice.get("recommendations", [])
    ]

    return WeeklySummaryResponse(
        id="generated_summary",
        week_start_date=date.today(),
        week_end_date=date.today(),
        total_spend=advice.get("total_weekly_spend", 0.0),
        category_breakdown=advice.get("category_breakdown", {}),
        recommendations=recs,
        llm_explanation=advice.get("llm_explanation", ""),
        is_accepted=False
    )


@router.post("/weekly/{summary_id}/accept", response_model=WeeklySummaryResponse)
def accept_weekly_recommendations(
    summary_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark weekly recommendations as accepted by user."""
    repo = UserScopedRepository(WeeklySummary, db, current_user.id)
    s = repo.get_by_id(summary_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Weekly summary not found.")

    s.is_accepted = True
    db.commit()
    db.refresh(s)

    recs = [
        RecommendationItem(
            category=r.get("category", "General"),
            rs_change=float(r.get("rs_change", 0.0)),
            reason=r.get("reason", ""),
            savings_effect=r.get("savings_effect", "")
        ) for r in (s.recommendations or [])
    ]

    return WeeklySummaryResponse(
        id=s.id,
        week_start_date=s.week_start_date,
        week_end_date=s.week_end_date,
        total_spend=float(s.total_spend),
        category_breakdown=s.category_breakdown or {},
        recommendations=recs,
        llm_explanation=s.llm_explanation,
        is_accepted=s.is_accepted
    )
