"""
Pydantic v2 validation and serialization schemas for REST API endpoints.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Auth & User Schemas
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    age_confirmed: bool = Field(..., description="Must confirm age is 18+")
    transaction_storage_consent: bool = Field(True, description="Consent to store transactions")
    llm_processing_consent: bool = Field(True, description="Consent for AI categorization and analysis")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    role: str
    is_verified: bool
    age_confirmed: bool
    currency_symbol: str
    monthly_income: Optional[float]
    savings_goal: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateProfileRequest(BaseModel):
    monthly_income: Optional[float] = None
    savings_goal: Optional[float] = None
    currency_symbol: Optional[str] = "Rs."


class ConsentResponse(BaseModel):
    transaction_storage_consent: bool
    llm_processing_consent: bool
    consent_given_at: Optional[datetime]
    consent_withdrawn_at: Optional[datetime]


class UpdateConsentRequest(BaseModel):
    transaction_storage_consent: bool
    llm_processing_consent: bool


# Transaction Schemas
class TransactionResponse(BaseModel):
    id: str
    transaction_date: date
    description: str
    normalized_merchant: str
    amount: float
    transaction_type: str
    category: str
    category_confidence: float
    categorization_method: str
    is_uncertain: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryCorrectionRequest(BaseModel):
    new_category: str
    apply_to_future: bool = True


# Anomaly Alert Schemas
class AnomalyAlertResponse(BaseModel):
    id: str
    transaction_id: str
    alert_type: str
    severity: str
    plain_language_reason: str
    signals_fired: List[str]
    user_feedback: str
    created_at: datetime
    merchant: Optional[str] = None
    amount: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class AlertFeedbackRequest(BaseModel):
    feedback: str = Field(..., pattern="^(expected|suspicious)$")


# Budget Schemas
class BudgetTargetItem(BaseModel):
    category: str
    weekly_target_amount: float


class BudgetVsActualResponse(BaseModel):
    category: str
    weekly_target_amount: float
    actual_amount: float
    variance_rs: float
    variance_pct: float
    is_overbudget: bool


# Advisor & Summary Schemas
class RecommendationItem(BaseModel):
    category: str
    rs_change: float
    reason: str
    savings_effect: str


class WeeklySummaryResponse(BaseModel):
    id: str
    week_start_date: date
    week_end_date: date
    total_spend: float
    category_breakdown: Dict[str, float]
    recommendations: List[RecommendationItem]
    llm_explanation: str
    is_accepted: bool
    disclaimer: str = "This tool supports financial awareness and planning; it is not a replacement for a financial adviser."

    model_config = ConfigDict(from_attributes=True)


# Ingestion & Trace Schemas
class UploadSummaryResponse(BaseModel):
    execution_id: str
    total_rows_parsed: int
    deduplicated_count: int
    uncertain_count: int
    categories_assigned: Dict[str, int]
    anomalies_flagged: int


class AgentTraceStep(BaseModel):
    step: int
    agent_name: str
    status: str
    duration_ms: float
    summary: str


class AgentTraceResponse(BaseModel):
    execution_id: str
    run_type: str
    steps: List[AgentTraceStep]
    total_duration_ms: float
    fallback_mode_used: bool


# Admin Metrics Schema
class AdminMetricsResponse(BaseModel):
    total_users_count: int
    total_transactions_processed: int
    total_anomalies_flagged: int
    active_users_last_7_days: int
