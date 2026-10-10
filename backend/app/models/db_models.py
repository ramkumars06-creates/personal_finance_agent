"""
SQLAlchemy ORM Data Models representing domain entities.
Enforces foreign key relationships and schema definitions.
"""
import uuid
from datetime import UTC, datetime

from app.core.database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # "user" | "admin"
    is_verified = Column(Boolean, nullable=False, default=False)
    age_confirmed = Column(Boolean, nullable=False, default=False)
    currency_symbol = Column(String(10), nullable=False, default="Rs.")
    monthly_income = Column(Numeric(12, 2), nullable=True)
    savings_goal = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    consents = relationship("UserConsent", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    category_rules = relationship("CategoryRule", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("UserBudget", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("AnomalyAlert", back_populates="user", cascade="all, delete-orphan")
    weekly_summaries = relationship("WeeklySummary", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class UserConsent(Base):
    __tablename__ = "user_consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_storage_consent = Column(Boolean, nullable=False, default=True)
    llm_processing_consent = Column(Boolean, nullable=False, default=True)
    consent_given_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    consent_withdrawn_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="consents")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_name = Column(String(100), nullable=False)
    masked_account_number = Column(String(20), nullable=False)
    account_type = Column(String(50), nullable=False, default="checking")  # checking, credit_card, savings

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True)
    transaction_date = Column(Date, nullable=False, index=True)
    encrypted_description = Column(Text, nullable=False)
    normalized_merchant = Column(String(255), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(String(20), nullable=False, default="debit")  # debit, credit, refund
    category = Column(String(50), nullable=False, default="other", index=True)
    category_confidence = Column(Numeric(3, 2), nullable=False, default=1.0)
    categorization_method = Column(String(20), nullable=False, default="rule")  # rule, llm, user
    dedup_hash = Column(String(64), nullable=False, index=True)
    is_uncertain = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    alerts = relationship("AnomalyAlert", back_populates="transaction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_dedup", "user_id", "dedup_hash", unique=True),
        Index("idx_user_date", "user_id", "transaction_date"),
    )


class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_pattern = Column(String(255), nullable=False)
    target_category = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="category_rules")

    __table_args__ = (
        Index("idx_user_merchant_pattern", "user_id", "merchant_pattern", unique=True),
    )


class UserBudget(Base):
    __tablename__ = "user_budgets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    weekly_target_amount = Column(Numeric(12, 2), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="budgets")

    __table_args__ = (
        Index("idx_user_category_budget", "user_id", "category", unique=True),
    )


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # baseline_deviation, unseen_merchant, frequency_spike
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high
    plain_language_reason = Column(Text, nullable=False)
    signals_fired = Column(JSON, nullable=False)
    user_feedback = Column(String(20), nullable=False, default="pending")  # pending, expected, suspicious
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="alerts")
    transaction = relationship("Transaction", back_populates="alerts")


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date = Column(Date, nullable=False)
    week_end_date = Column(Date, nullable=False)
    total_spend = Column(Numeric(12, 2), nullable=False)
    category_breakdown = Column(JSON, nullable=False)
    recommendations = Column(JSON, nullable=False)
    llm_explanation = Column(Text, nullable=False)
    is_accepted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="weekly_summaries")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="audit_logs")
