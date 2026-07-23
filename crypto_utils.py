"""
BOLT FINAL - Crypto + Extraction that handles iPhone Telegram line breaks
"""
import os, re, base64, hashlib, hmac as _hmac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from urllib.parse import urlparse, parse_qs, unquote

_SALT = b'bolt_v1_2026_static_salt__'
_HMAC_SALT = b'bolt_hmac_integrity_v1____'

def _derive_key() -> bytes:
    raw = os.environ.get("ENCRYPTION_KEY", "")
    if not raw or len(raw) < 16:
        raise RuntimeError("ENCRYPTION_KEY must be set (min 16 chars)")
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
    # Remove Telegram line breaks for iPhone
    cleaned = text.replace('\n','').replace('\r','').replace(' ','').strip()
    # Try parse_qs first - more robust
    try:
        # Need to ensure URL has ?
        if '?' in cleaned:
            parsed = urlparse(cleaned)
            qs = parse_qs(parsed.query)
            if 'eat' in qs and qs['eat']:
                token = qs['eat'][0]
                # Token may still have & attached if malformed, clean
                token = token.split('&')[0]
                return token
    except:
        pass
    try:
        cleaned2 = unquote(cleaned)
    except:
        cleaned2 = cleaned
    m = re.search(r'[?&]eat=([a-fA-F0-9]{20,2048})', cleaned2, re.IGNORECASE)
    if m:
        return m.group(1).split('&')[0]
    m = re.search(r'([a-fA-F0-9]{64,2048})', cleaned2, re.IGNORECASE)
    if m:
        return m.group(1)
    return None

def extract_full_data(text: str):
    """Returns dict with token, account_id, nickname, region - handles Telegram breaks"""
    result = {"token": None, "account_id": None, "nickname": None, "region": None, "lang": None}
    if not text:
        return result
    # Step 1: Remove line breaks but keep structure for urlparse
    cleaned = text.replace('\n','').replace('\r','').strip()
    try:
        parsed = urlparse(cleaned)
        qs = parse_qs(parsed.query)
        # parse_qs returns list
        if 'eat' in qs:
            result['token'] = qs['eat'][0].split('&')[0]
        if 'account_id' in qs:
            result['account_id'] = qs['account_id'][0]
        if 'nickname' in qs:
            # parse_qs already decodes
            result['nickname'] = qs['nickname'][0]
        if 'region' in qs:
            result['region'] = qs['region'][0]
        if 'lang' in qs:
            result['lang'] = qs['lang'][0]
        # If token not found via parse_qs, try regex fallback
        if not result['token']:
            result['token'] = extract_token_from_url(cleaned)
        return result
    except Exception as e:
        # Fallback regex
        result['token'] = extract_token_from_url(text)
        # Try account_id regex
        m = re.search(r'account_id=([0-9]+)', cleaned)
        if m:
            result['account_id'] = m.group(1)
        m = re.search(r'nickname=([^&]+)', cleaned)
        if m:
            try:
                result['nickname'] = unquote(m.group(1))
            except:
                result['nickname'] = m.group(1)
        return result

def is_valid_token_format(token: str) -> bool:
    if not token:
        return False
    if any(c in token for c in ' \n\r\t'):
        return False
    if len(token) < 20:
        return False
    return True
