"""
Admin API: Anonymized, Aggregated Platform Metrics.
Strictly prevents viewing individual user transactions or PII.
"""
from datetime import UTC, datetime, timedelta

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models.db_models import AnomalyAlert, AuditLog, Transaction, User
from app.schemas.api_schemas import AdminMetricsResponse
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/admin", tags=["Admin Metrics"])


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_admin_system_metrics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Fetch platform aggregate metrics.
    Admin sees only system counts & anonymized totals, NEVER individual user transactions or PII.
    """
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_txns = db.query(func.count(Transaction.id)).scalar() or 0
    total_anomalies = db.query(func.count(AnomalyAlert.id)).scalar() or 0

    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    active_users = db.query(func.count(func.distinct(AuditLog.user_id))).filter(AuditLog.timestamp >= seven_days_ago).scalar() or 0

    return AdminMetricsResponse(
        total_users_count=total_users,
        total_transactions_processed=total_txns,
        total_anomalies_flagged=total_anomalies,
        active_users_last_7_days=active_users
    )
