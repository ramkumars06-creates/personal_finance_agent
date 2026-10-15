"""
Configuration management using Pydantic Settings v2.
"""
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Finance Agent"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./personal_finance.db"
    
    # Security & Tokens
    SECRET_KEY: str = "insecure_default_secret_key_change_in_production_32bytes_min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption key for sensitive fields at rest (AES-256 Fernet base64 key)
    # Must be 32 url-safe base64-encoded bytes
    ENCRYPTION_KEY: str = "u6N_4kL-p1B9y8W2z3X4v5G6h7J8k9L0m1N2o3P4q5R="
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    NO_LLM_FALLBACK: bool = False
    DAILY_LLM_QUOTA_PER_USER: int = 50
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Rate Limiting & File Upload Limits
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_SIZE_MB: int = 5
    MAX_UPLOAD_ROWS: int = 10000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
    ]
    
    # Cookie security
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
