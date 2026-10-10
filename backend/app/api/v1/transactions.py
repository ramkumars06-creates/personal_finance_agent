"""
Transactions API: List, Search, Filter, and User Category Correction.
"""

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.encryption import decrypt_field
from app.models.db_models import CategoryRule, User
from app.repositories.user_scoped_repo import (
    CategoryRuleRepository,
    TransactionRepository,
)
from app.schemas.api_schemas import CategoryCorrectionRequest, TransactionResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=list[TransactionResponse])
def get_transactions(
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch user transactions with search and category filtering.
    Decrypts sensitive descriptions for display.
    """
    repo = TransactionRepository(db, current_user.id)
    txns = repo.get_all(limit=limit, offset=offset)

    results = []
    search_lower = search.lower() if search else None

    for t in txns:
        dec_desc = decrypt_field(t.encrypted_description)
        
        if category and t.category.lower() != category.lower():
            continue

        if search_lower and (search_lower not in dec_desc.lower() and search_lower not in t.normalized_merchant.lower()):
            continue

        results.append(TransactionResponse(
            id=t.id,
            transaction_date=t.transaction_date,
            description=dec_desc,
            normalized_merchant=t.normalized_merchant,
            amount=float(t.amount),
            transaction_type=t.transaction_type,
            category=t.category,
            category_confidence=float(t.category_confidence),
            categorization_method=t.categorization_method,
            is_uncertain=t.is_uncertain
        ))

    return results


@router.put("/{transaction_id}/category", response_model=TransactionResponse)
def update_transaction_category(
    transaction_id: str,
    req: CategoryCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User Category Correction: Updates category, sets method='user', and creates a per-user CategoryRule.
    """
    repo = TransactionRepository(db, current_user.id)
    txn = repo.get_by_id(transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    txn.category = req.new_category.lower()
    txn.categorization_method = "user"
    txn.category_confidence = 1.0
    db.commit()
    db.refresh(txn)

    # Save per-user category rule if requested
    if req.apply_to_future:
        rule_repo = CategoryRuleRepository(db, current_user.id)
        existing_rule = rule_repo.find_matching_rule(txn.normalized_merchant)
        if not existing_rule:
            new_rule = CategoryRule(
                user_id=current_user.id,
                merchant_pattern=txn.normalized_merchant.lower(),
                target_category=req.new_category.lower()
            )
            db.add(new_rule)
            db.commit()

    return TransactionResponse(
        id=txn.id,
        transaction_date=txn.transaction_date,
        description=decrypt_field(txn.encrypted_description),
        normalized_merchant=txn.normalized_merchant,
        amount=float(txn.amount),
        transaction_type=txn.transaction_type,
        category=txn.category,
        category_confidence=float(txn.category_confidence),
        categorization_method=txn.categorization_method,
        is_uncertain=txn.is_uncertain
    )
