"""
Privacy & DPDP Act 2023 Compliance Endpoints: Data Export, Account Deletion, Consent Management.
"""
from typing import Any, Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.db_models import User, UserConsent, Transaction, UserBudget, AnomalyAlert, WeeklySummary, AuditLog
from app.schemas.api_schemas import ConsentResponse, UpdateConsentRequest
from app.repositories.user_scoped_repo import UserScopedRepository
from app.core.encryption import decrypt_field
from app.api.deps import get_current_user

router = APIRouter(prefix="/privacy", tags=["Privacy & Consent"])


@router.get("/consent", response_model=ConsentResponse)
def get_consent_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch active user consent preferences."""
    consent = db.query(UserConsent).filter(UserConsent.user_id == current_user.id).first()
    if not consent:
        return ConsentResponse(
            transaction_storage_consent=True,
            llm_processing_consent=True,
            consent_given_at=current_user.created_at,
            consent_withdrawn_at=None
        )
    return ConsentResponse(
        transaction_storage_consent=consent.transaction_storage_consent,
        llm_processing_consent=consent.llm_processing_consent,
        consent_given_at=consent.consent_given_at,
        consent_withdrawn_at=consent.consent_withdrawn_at
    )


@router.post("/consent", response_model=ConsentResponse)
def update_consent(
    req: UpdateConsentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update or withdraw granular consent preferences."""
    consent = db.query(UserConsent).filter(UserConsent.user_id == current_user.id).first()
    if not consent:
        consent = UserConsent(user_id=current_user.id)
        db.add(consent)

    consent.transaction_storage_consent = req.transaction_storage_consent
    consent.llm_processing_consent = req.llm_processing_consent

    if not req.transaction_storage_consent or not req.llm_processing_consent:
        consent.consent_withdrawn_at = datetime.now(timezone.utc)
    else:
        consent.consent_withdrawn_at = None

    db.add(AuditLog(user_id=current_user.id, action="update_consent", resource="user_consents"))
    db.commit()
    db.refresh(consent)

    return ConsentResponse(
        transaction_storage_consent=consent.transaction_storage_consent,
        llm_processing_consent=consent.llm_processing_consent,
        consent_given_at=consent.consent_given_at,
        consent_withdrawn_at=consent.consent_withdrawn_at
    )


@router.get("/export")
def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    DPDP Act Right to Data Portability: Export complete user records as structured JSON.
    Decrypts sensitive fields at rest for the rightful account owner.
    """
    txns = db.query(Transaction).filter(Transaction.user_id == current_user.id).all()
    budgets = db.query(UserBudget).filter(UserBudget.user_id == current_user.id).all()
    alerts = db.query(AnomalyAlert).filter(AnomalyAlert.user_id == current_user.id).all()
    summaries = db.query(WeeklySummary).filter(WeeklySummary.user_id == current_user.id).all()

    export_payload = {
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "monthly_income": float(current_user.monthly_income) if current_user.monthly_income else None,
            "savings_goal": float(current_user.savings_goal) if current_user.savings_goal else None,
            "created_at": current_user.created_at.isoformat()
        },
        "transactions": [
            {
                "id": t.id,
                "date": t.transaction_date.isoformat(),
                "description": decrypt_field(t.encrypted_description),
                "merchant": t.normalized_merchant,
                "amount": float(t.amount),
                "type": t.transaction_type,
                "category": t.category
            } for t in txns
        ],
        "budgets": [
            {
                "category": b.category,
                "weekly_target_amount": float(b.weekly_target_amount)
            } for b in budgets
        ],
        "anomaly_alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type,
                "reason": a.plain_language_reason,
                "feedback": a.user_feedback
            } for a in alerts
        ],
        "weekly_summaries": [
            {
                "id": s.id,
                "week_start": s.week_start_date.isoformat(),
                "week_end": s.week_end_date.isoformat(),
                "total_spend": float(s.total_spend),
                "explanation": s.llm_explanation
            } for s in summaries
        ]
    }

    db.add(AuditLog(user_id=current_user.id, action="export_data", resource="users"))
    db.commit()

    return export_payload


@router.get("/activity-history")
def get_activity_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch user audit log history (logins, uploads, updates)."""
    logs = db.query(AuditLog).filter(AuditLog.user_id == current_user.id).order_by(AuditLog.timestamp.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource": l.resource,
            "timestamp": l.timestamp.isoformat()
        } for l in logs
    ]


@router.delete("/account", status_code=status.HTTP_200_OK)
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    DPDP Act Right to Erasure / Right to be Forgotten:
    Permanently deletes user account and hard-purges all associated financial records.
    """
    user_id = current_user.id

    # Purge scoped data across all tables
    for model in [Transaction, UserBudget, AnomalyAlert, WeeklySummary, UserConsent, AuditLog]:
        UserScopedRepository(model, db, user_id).delete_all_user_data()

    # Delete User entity
    db.delete(current_user)
    db.commit()

    return {
        "message": "Account and all associated personal data permanently erased.",
        "note": "Backups auto-expire according to our standard 30-day retention policy."
    }
