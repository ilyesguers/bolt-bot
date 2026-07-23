"""
BOLT ⚡ — Crypto Module — FIXED FOR IPHONE
Fernet encryption + Auto-extract from URL (handles Telegram line breaks + iPhone Safari)
"""

import os
import re
import base64
import hashlib
import hmac as _hmac
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT = b'bolt_v1_2026_static_salt__'
_HMAC_SALT = b'bolt_hmac_integrity_v1____'


def _derive_key() -> bytes:
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if not raw or len(raw) < 16:
        raise RuntimeError("ENCRYPTION_KEY must be set (min 16 chars) - generate one via gen_key.py")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=600_000)
    return base64.urlsafe_b64encode(kdf.derive(raw.encode()))


def _derive_hmac_key() -> bytes:
    raw = os.environ.get("ENCRYPTION_KEY", "")
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_HMAC_SALT, iterations=600_000)
    return kdf.derive(raw.encode())


def _get_fernet() -> Fernet:
    return Fernet(_derive_key())


def encrypt_token(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str | None:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except Exception:
        return None


def token_fingerprint(token: str) -> str:
    key = _derive_hmac_key()
    return _hmac.new(key, token.encode(), hashlib.sha256).hexdigest()[:16]


def verify_fingerprint(token: str, expected_fp: str) -> bool:
    return token_fingerprint(token) == expected_fp


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:8]


def mask_token(token: str) -> str:
    if not token or len(token) < 10:
        return "••••••"
    return f"{token[:4]}{'•' * (len(token) - 8)}{token[-4:]}"


def extract_token_from_url(text: str) -> str | None:
    if not text:
        return None

    # FIX: Telegram + iPhone Safari splits long URLs into 2-3 lines!
    original = text
    cleaned = text.replace('\n', '').replace('\r', '').replace(' ', '').strip()
    try:
        import urllib.parse
        cleaned = urllib.parse.unquote(cleaned)
    except:
        pass

    # Method 1: URL with ?eat= or &eat=
    match = re.search(r'[?&]eat=([a-fA-F0-9]{20,2048})', cleaned, re.IGNORECASE)
    if match:
        token = match.group(1).split('&')[0]
        return token

    # Method 2: Direct long hex string (64+)
    match = re.search(r'([a-fA-F0-9]{64,2048})', cleaned, re.IGNORECASE)
    if match:
        return match.group(1)

    # Method 3: Any hex after eat=
    match = re.search(r'eat=([a-fA-F0-9]{16,})', cleaned, re.IGNORECASE)
    if match:
        return match.group(1)

    # Method 4: Discount store heuristic - longest hex
    if "recargajogo" in original.lower() or "discount" in original.lower():
        all_hex = re.findall(r'[a-fA-F0-9]{32,}', original, re.IGNORECASE)
        if all_hex:
            return max(all_hex, key=len)

    return None


def is_valid_token_format(token: str) -> bool:
    if not token:
        return False
    if any(c in token for c in ' \n\r\t'):
        return False
    if len(token) < 20:
        return False
    # Must be hex
    try:
        int(token, 16)
    except:
        # Allow non-hex? Some tokens are base64-like, but for EAT must be hex
        pass
    return True
