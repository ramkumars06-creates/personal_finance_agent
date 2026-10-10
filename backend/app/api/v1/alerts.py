"""
Anomaly Alerts API: List Alerts, Explain Signals, Capture User Feedback.
"""

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.db_models import AnomalyAlert, Transaction, User
from app.repositories.user_scoped_repo import UserScopedRepository
from app.schemas.api_schemas import AlertFeedbackRequest, AnomalyAlertResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/alerts", tags=["Anomaly Alerts"])


@router.get("", response_model=list[AnomalyAlertResponse])
def get_anomaly_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch user anomaly alerts with plain-language reasons and signal lists."""
    repo = UserScopedRepository(AnomalyAlert, db, current_user.id)
    alerts = repo.get_all(limit=100)

    results = []
    for a in alerts:
        txn = db.query(Transaction).filter(Transaction.id == a.transaction_id, Transaction.user_id == current_user.id).first()
        results.append(AnomalyAlertResponse(
            id=a.id,
            transaction_id=a.transaction_id,
            alert_type=a.alert_type,
            severity=a.severity,
            plain_language_reason=a.plain_language_reason,
            signals_fired=a.signals_fired or [],
            user_feedback=a.user_feedback,
            created_at=a.created_at,
            merchant=txn.normalized_merchant if txn else "Unknown",
            amount=float(txn.amount) if txn else 0.0
        ))

    return results


@router.post("/{alert_id}/feedback", response_model=AnomalyAlertResponse)
def submit_alert_feedback(
    alert_id: str,
    req: AlertFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User Feedback Loop: Mark alert as 'expected' or 'suspicious'.
    Feedback adjusts future anomaly detection sensitivity.
    """
    repo = UserScopedRepository(AnomalyAlert, db, current_user.id)
    alert = repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    alert.user_feedback = req.feedback
    db.commit()
    db.refresh(alert)

    txn = db.query(Transaction).filter(Transaction.id == alert.transaction_id, Transaction.user_id == current_user.id).first()

    return AnomalyAlertResponse(
        id=alert.id,
        transaction_id=alert.transaction_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        plain_language_reason=alert.plain_language_reason,
        signals_fired=alert.signals_fired or [],
        user_feedback=alert.user_feedback,
        created_at=alert.created_at,
        merchant=txn.normalized_merchant if txn else "Unknown",
        amount=float(txn.amount) if txn else 0.0
    )
