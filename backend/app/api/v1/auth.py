"""
Auth Endpoints: Signup, Login, Token Refresh, Logout, Password Reset.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings
from app.models.db_models import User, UserConsent, AuditLog
from app.schemas.api_schemas import SignupRequest, LoginRequest, TokenResponse, UserProfileResponse, UpdateProfileRequest
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """User Registration with Age Confirmation & DPDP Consent Capture."""
    if not req.age_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age confirmation (18+) is required to create an account."
        )

    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account with this email already exists."
        )

    user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        role="user",
        is_verified=True,  # Auto-verified for demo convenience
        age_confirmed=req.age_confirmed,
        currency_symbol="Rs."
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Store DPDP Granular Consent
    consent = UserConsent(
        user_id=user.id,
        transaction_storage_consent=req.transaction_storage_consent,
        llm_processing_consent=req.llm_processing_consent
    )
    db.add(consent)

    # Audit Log Entry
    audit = AuditLog(user_id=user.id, action="signup", resource="users")
    db.add(audit)
    db.commit()

    access_token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.id})

    # Set httpOnly refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=7 * 24 * 3600
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """User Login returning short-lived JWT and setting httpOnly refresh cookie."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.id})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=7 * 24 * 3600
    )

    audit = AuditLog(user_id=user.id, action="login", resource="users")
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    """Refresh access token using httpOnly refresh cookie."""
    cookie_refresh = request.cookies.get("refresh_token")
    if not cookie_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh cookie missing.")

    payload = decode_token(cookie_refresh, expected_type="refresh")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    new_access = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=new_access,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        role=user.role
    )


@router.post("/logout")
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Clear refresh token cookie."""
    response.delete_cookie("refresh_token")
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current user profile details."""
    return current_user


@router.put("/me", response_model=UserProfileResponse)
def update_me(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile savings goal, income, and currency symbol."""
    if req.monthly_income is not None:
        current_user.monthly_income = req.monthly_income
    if req.savings_goal is not None:
        current_user.savings_goal = req.savings_goal
    if req.currency_symbol:
        current_user.currency_symbol = req.currency_symbol

    db.commit()
    db.refresh(current_user)
    return current_user
