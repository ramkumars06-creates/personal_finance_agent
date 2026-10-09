"""
Database connection, session management, and SQLAlchemy base configuration.
"""
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Engine setup
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def enable_postgres_rls(session: Session, user_id: str) -> None:
    """
    Set PostgreSQL session variable for Row-Level Security (RLS).
    If using SQLite, this is a no-op.
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        session.execute(
            text("SET LOCAL app.current_user_id = :user_id"),
            {"user_id": str(user_id)}
        )
