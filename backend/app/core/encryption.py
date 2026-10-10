"""
Field-level encryption and masking utilities for sensitive PII and financial fields at rest.
"""
import base64
import hashlib

from app.core.config import settings
from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """Generate or retrieve a deterministic valid 32-byte base64 key for Fernet."""
    raw_key = settings.ENCRYPTION_KEY.encode('utf-8')
    # Use SHA-256 to ensure exact 32 bytes valid for Fernet
    key_bytes = hashlib.sha256(raw_key).digest()
    base64_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(base64_key)


def encrypt_field(plaintext: str) -> str:
    """Encrypt a plaintext string to an encrypted ciphertext string."""
    if not plaintext:
        return ""
    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_field(ciphertext: str) -> str:
    """Decrypt an encrypted ciphertext string back to original plaintext."""
    if not ciphertext:
        return ""
    try:
    fernet = _get_fernet()
    decrypted_bytes = fernet.decrypt(ciphertext.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')
except (ValueError, TypeError):
    # Fallback if text is unencrypted (legacy or test data)
    return ciphertext


def mask_account_number(account_num: str) -> str:
    """Mask sensitive account number, showing only last 4 digits."""
    if not account_num or len(account_num) <= 4:
        return "XXXX"
    return f"XXXX-XXXX-{account_num[-4:]}"


def sanitize_for_formula_injection(text: str) -> str:
    """
    Guard against CSV/formula injection when exporting data.
    Prefix cells starting with =, +, -, @, or tab/carriage return with a single quote.
    """
    if not text:
        return ""
    text_str = str(text).strip()
    if text_str.startswith(('=', '+', '-', '@', '\t', '\r')):
        return f"'{text_str}"
    return text_str
