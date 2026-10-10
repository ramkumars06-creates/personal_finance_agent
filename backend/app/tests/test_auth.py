"""
Auth Unit & Integration Tests: Signup, Login, Password Hashing, JWT Tokens.
"""
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hashing():
    """Verify Argon2id password hashing and verification."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_lifecycle():
    """Verify JWT access token creation and decoding."""
    data = {"sub": "user_123", "role": "user"}
    token = create_access_token(data)
    
    decoded = decode_token(token, expected_type="access")
    assert decoded is not None
    assert decoded["sub"] == "user_123"
    assert decoded["role"] == "user"


def test_invalid_token_decoding():
    """Verify invalid token handling."""
    invalid_token = "invalid.token.str"
    assert decode_token(invalid_token) is None
