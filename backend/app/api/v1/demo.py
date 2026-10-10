"""
Demo Mode API: Instant demo user creation and sample data seeding.
"""
import uuid
from datetime import date, timedelta

from app.core.database import get_db
from app.core.encryption import encrypt_field
from app.core.security import create_access_token, hash_password
from app.models.db_models import (
    AnomalyAlert,
    Transaction,
    User,
    UserBudget,
    UserConsent,
    WeeklySummary,
)
from app.schemas.api_schemas import TokenResponse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


@router.post("/seed", response_model=TokenResponse)
def seed_demo_user(db: Session = Depends(get_db)):
    """
    Seed a zero-signup demo account populated with presentation week sample transactions:
    - Rs. 450 food delivery (Swiggy)
    - Rs. 1,200 shopping (Amazon)
    - Rs. 80 metro (Namma Metro)
    - Rs. 5,000 unexpected merchant charge (Unknown Tech Corp)
    - Rs. 2,000 utilities (BESCOM Electricity)
    """
    demo_email = f"demo_{uuid.uuid4().hex[:8]}@example.com"
    demo_user = User(
        email=demo_email,
        password_hash=hash_password("DemoUser123!"),
        role="user",
        is_verified=True,
        age_confirmed=True,
        currency_symbol="Rs.",
        monthly_income=50000.0,
        savings_goal=10000.0
    )
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)

    db.add(UserConsent(user_id=demo_user.id, transaction_storage_consent=True, llm_processing_consent=True))

    # Default weekly target budgets
    targets = [
        ("food", 2000.0),
        ("groceries", 2500.0),
        ("transport", 1000.0),
        ("bills", 2500.0),
        ("shopping", 1500.0),
        ("entertainment", 1000.0),
        ("health", 1000.0),
        ("other", 1000.0)
    ]
    for cat, tgt in targets:
        db.add(UserBudget(user_id=demo_user.id, category=cat, weekly_target_amount=tgt))

    today = date.today()

    # Presentation Week Transactions
    sample_txns = [
        (today - timedelta(days=6), "SWIGGY*ORDER 8843", "Swiggy", 450.0, "food", "rule", 0.95),
        (today - timedelta(days=5), "AMZN Mktp IN", "Amazon India", 1200.0, "shopping", "rule", 0.90),
        (today - timedelta(days=4), "NAMMA METRO BMRCL", "Namma Metro", 80.0, "transport", "rule", 0.98),
        (today - timedelta(days=3), "UNKNOWN TECH CORP CHARGE", "Unknown Tech Corp", 5000.0, "other", "llm", 0.50),
        (today - timedelta(days=2), "BESCOM ELECTRICITY BILL", "BESCOM", 2000.0, "bills", "rule", 0.95),
        (today - timedelta(days=1), "ZEPTO QUICK GROCERY", "Zepto", 650.0, "groceries", "rule", 0.92)
    ]

    inserted_txns = []
    for t_date, desc, merch, amt, cat, method, conf in sample_txns:
        dedup_hash = uuid.uuid4().hex
        txn = Transaction(
            user_id=demo_user.id,
            transaction_date=t_date,
            encrypted_description=encrypt_field(desc),
            normalized_merchant=merch,
            amount=amt,
            transaction_type="debit",
            category=cat,
            category_confidence=conf,
            categorization_method=method,
            dedup_hash=dedup_hash,
            is_uncertain=False
        )
        db.add(txn)
        inserted_txns.append(txn)

    db.commit()

    # Seed Anomaly Alert for unexpected Rs. 5,000 charge
    unexpected_txn = next(t for t in inserted_txns if t.amount == 5000.0)
    db.add(AnomalyAlert(
        user_id=demo_user.id,
        transaction_id=unexpected_txn.id,
        alert_type="unseen_merchant_high_value",
        severity="high",
        plain_language_reason="First time transaction detected with merchant 'Unknown Tech Corp' for high value of Rs. 5,000.00.",
        signals_fired=["unseen_merchant", "high_single_transaction_value"],
        user_feedback="pending"
    ))

    # Seed Weekly Summary
    db.add(WeeklySummary(
        user_id=demo_user.id,
        week_start_date=today - timedelta(days=7),
        week_end_date=today,
        total_spend=9380.0,
        category_breakdown={
            "food": 450.0, "shopping": 1200.0, "transport": 80.0,
            "other": 5000.0, "bills": 2000.0, "groceries": 650.0
        },
        recommendations=[
            {
                "category": "Other",
                "rs_change": -3500.0,
                "reason": "An unexpected charge of Rs. 5,000 was flagged in the 'Other' category.",
                "savings_effect": "Investigating or disputing suspicious charges protects your primary budget."
            },
            {
                "category": "Shopping",
                "rs_change": -300.0,
                "reason": "Shopping spend reached Rs. 1,200 out of your Rs. 1,500 weekly target.",
                "savings_effect": "Trimming non-essential shopping keeps you well under target limit."
            }
        ],
        llm_explanation=(
            "In this sample week, your total expenditure was Rs. 9,380.00. "
            "Your largest single charge was Rs. 5,000.00 to Unknown Tech Corp, which our AI flagged as an anomaly alert for your review. "
            "Excluding that unexpected item, your spending across Food, Transport, and Utilities remained well within healthy limits.\n\n"
            "Disclaimer: This tool supports financial awareness and planning; it is not a replacement for a financial adviser."
        ),
        is_accepted=False
    ))

    db.commit()

    access_token = create_access_token({"sub": demo_user.id, "email": demo_user.email, "role": demo_user.role})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=demo_user.id,
        email=demo_user.email,
        role=demo_user.role
    )
