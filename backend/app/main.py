"""
FastAPI Application Entry Point.
Initializes middleware, routers, rate limiting, and health check routes.
"""
from app.api.v1 import (
    admin,
    advisor,
    alerts,
    auth,
    budgets,
    demo,
    ingestion,
    privacy,
    transactions,
)
from app.core.config import settings
from app.core.database import Base, engine
from app.core.middleware import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    limiter,
)
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

# Create DB tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI Budget & Spending Assistant REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiter attachment
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda req, exc: Response("Rate limit exceeded.", status_code=429))

# Middleware setup
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registrations
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(privacy.router, prefix=settings.API_V1_STR)
app.include_router(ingestion.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(budgets.router, prefix=settings.API_V1_STR)
app.include_router(advisor.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Monitoring"])
def health_check():
    """Liveness probe returning system operational status."""
    return {"status": "healthy", "project": settings.PROJECT_NAME}


@app.get("/ready", tags=["Monitoring"])
def readiness_check():
    """Readiness probe checking database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(Base.metadata.tables['users'].select().limit(1))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}
