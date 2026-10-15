"""
Budgets API: Category Target Definition and Budget-vs-Actual Tracking.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import User, UserBudget, Transaction
from app.schemas.api_schemas import BudgetVsActualResponse, BudgetTargetItem
from app.repositories.user_scoped_repo import BudgetRepository, TransactionRepository
from app.agents.budget_agent import BudgetAgent
from app.api.deps import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("", response_model=List[BudgetVsActualResponse])
def get_budget_vs_actual(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch weekly target budgets vs actual spending breakdown."""
    budget_repo = BudgetRepository(db, current_user.id)
    user_budgets = [{"category": b.category, "weekly_target_amount": float(b.weekly_target_amount)} for b in budget_repo.get_all()]

    txn_repo = TransactionRepository(db, current_user.id)
    txns = [{"category": t.category, "amount": float(t.amount), "transaction_type": t.transaction_type} for t in txn_repo.get_all(limit=500)]

    agent = BudgetAgent()
    income = float(current_user.monthly_income) if current_user.monthly_income else None
    analysis = agent.compute_budget_vs_actual(txns, user_budgets, income)

    results = []
    for cat, data in analysis["category_analysis"].items():
        results.append(BudgetVsActualResponse(
            category=cat,
            weekly_target_amount=data["weekly_target_amount"],
            actual_amount=data["actual_amount"],
            variance_rs=data["variance_rs"],
            variance_pct=data["variance_pct"],
            is_overbudget=data["is_overbudget"]
        ))

    return results


@router.put("", response_model=List[BudgetTargetItem])
def update_budgets(
    targets: List[BudgetTargetItem],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Batch edit category weekly targets."""
    budget_repo = BudgetRepository(db, current_user.id)

    updated_items = []
    for item in targets:
        cat_lower = item.category.lower()
        b = budget_repo.get_by_category(cat_lower)
        if not b:
            b = UserBudget(
                user_id=current_user.id,
                category=cat_lower,
                weekly_target_amount=item.weekly_target_amount
            )
            db.add(b)
        else:
            b.weekly_target_amount = item.weekly_target_amount
        
        updated_items.append(BudgetTargetItem(category=cat_lower, weekly_target_amount=float(item.weekly_target_amount)))

    db.commit()
    return updated_items
