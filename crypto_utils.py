"""
BOLT ⚡ — Crypto Module
━━━━━━━━━━━━━━━━━━━━━━━
🛡️ Fernet (AES-128-CBC + HMAC-SHA256) double-layer encryption
🔐 Token fingerprints for tamper detection
🔑 Key derived from ENCRYPTION_KEY env var via PBKDF2
"""

import os
import base64
import hashlib
import hmac as _hmac
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# ─── Salt (static, acceptable for app-level KDF) ─────────────────────────────
_SALT = b'bolt_v1_2026_static_salt__'

# ─── HMAC Secret (derived from main key + separate salt) ─────────────────────
_HMAC_SALT = b'bolt_hmac_integrity_v1____'


def _derive_key() -> bytes:
    """Derive Fernet key from ENCRYPTION_KEY env var."""
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if not raw or len(raw) < 16:
        raise RuntimeError(
            "❌ ENCRYPTION_KEY must be set (min 16 chars).\n"
            "   Generate one: python gen_key.py"
        )
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=600_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(raw.encode()))


def _derive_hmac_key() -> bytes:
    """Derive HMAC key for integrity checks."""
    raw = os.environ.get("ENCRYPTION_KEY", "")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_HMAC_SALT,
        iterations=600_000,
    )
    return kdf.derive(raw.encode())


def _get_fernet() -> Fernet:
    return Fernet(_derive_key())


# ─── Core Encrypt / Decrypt ──────────────────────────────────────────────────

def encrypt_token(plaintext: str) -> str:
    """Encrypt a token → base64 ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str | None:
    """Decrypt a token. Returns None if key mismatch / corrupted."""
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        return None


# ─── Token Fingerprint ────────────────────────────────────────────────────────

def token_fingerprint(token: str) -> str:
    """
    HMAC-SHA256 fingerprint of the token.
    Used to detect tampering without exposing the actual token.
    """
    key = _derive_hmac_key()
    return _hmac.new(key, token.encode(), hashlib.sha256).hexdigest()[:16]


def verify_fingerprint(token: str, expected_fp: str) -> bool:
    """Verify a token against a stored fingerprint."""
    return token_fingerprint(token) == expected_fp


# ─── Token Hash (for logging) ────────────────────────────────────────────────

def hash_token(token: str) -> str:
    """Short SHA-256 hash for safe logging (first 8 hex chars)."""
    return hashlib.sha256(token.encode()).hexdigest()[:8]


# ─── Masked Display ──────────────────────────────────────────────────────────

def mask_token(token: str) -> str:
    """Display token as 'ABCD••••••WXYZ'."""
    if not token or len(token) < 10:
        return "••••••"
    return f"{token[:4]}{'•' * (len(token) - 8)}{token[-4:]}"


# ─── Token Format Validation ─────────────────────────────────────────────────

def is_valid_token_format(token: str) -> bool:
    if not token:
        return False
    if len(token) < 20 or len(token) > 500:
        return False
    if any(c in token for c in ' \n\r\t\x00\x0b\x0c'):
        return False
    if not any(c.isalnum() for c in token):
        return False
    return True
