"""
BOLT ⚡ — Security Module
━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ Rate limiting (sliding window)
🚫 Ban system with expiry
📋 Audit trail (SQLite-backed)
🧼 Input sanitization & email validation
🔍 Token abuse detection
"""

import time
import re
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from html import escape as _escape

logger = logging.getLogger("bolt.security")

# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding-window rate limiter backed by SQLite.
    Separate buckets per (user, action) pair.
    """

    LIMITS = {
        # action: (max_requests, window_seconds)
        "general":      (30, 60),
        "token_ops":    (5,  120),    # token add / change
        "garena_api":   (6,  120),    # external API calls
        "nickname":     (3,  300),    # name changes
        "bind_change":  (2,  300),
        "broadcast":    (1,  600),
        "code_gen":     (15, 60),
        "reward_claim": (1,  86400),  # once per 24h
    }

    def __init__(self, db_path: str = "bolt_security.db"):
        self._db = db_path
        self._lock = threading.Lock()
        self._mem: dict[str, list[float]] = {}
        self._init_db()

    # ── DB Init ────────────────────────────────────────────────────────

    def _init_db(self):
        conn = sqlite3.connect(self._db)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                username  TEXT DEFAULT '',
                action    TEXT    NOT NULL,
                detail    TEXT    DEFAULT '',
                timestamp TEXT    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_audit_user_ts
                ON audit_log(user_id, timestamp DESC);

            CREATE TABLE IF NOT EXISTS banned (
                user_id    INTEGER PRIMARY KEY,
                reason     TEXT DEFAULT '',
                banned_at  TEXT NOT NULL,
                expires_at TEXT
            );

            CREATE TABLE IF NOT EXISTS abuse_flags (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                flag_type TEXT NOT NULL,
                detail    TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_abuse_user
                ON abuse_flags(user_id);
        """)
        conn.commit()
        conn.close()

    # ── Rate Checking ──────────────────────────────────────────────────

    def check(self, user_id: int, action: str = "general") -> tuple[bool, int]:
        """Returns (allowed, retry_seconds)."""
        now = time.time()
        key = f"{user_id}:{action}"
        max_req, window = self.LIMITS.get(action, (10, 60))

        with self._lock:
            entries = self._mem.get(key, [])
            # Prune old
            entries = [t for t in entries if now - t < window]

            if len(entries) >= max_req:
                oldest = entries[0]
                retry = int(window - (now - oldest)) + 1
                self._mem[key] = entries
                self._flag_abuse(user_id, "rate_limit", f"{action} blocked")
                return False, max(retry, 1)

            entries.append(now)
            self._mem[key] = entries
            return True, 0

    def remaining(self, user_id: int, action: str = "general") -> int:
        now = time.time()
        key = f"{user_id}:{action}"
        _, window = self.LIMITS.get(action, (10, 60))
        max_req, _ = self.LIMITS.get(action, (10, 60))
        active = [t for t in self._mem.get(key, []) if now - t < window]
        return max(0, max_req - len(active))

    # ── Audit Logging ──────────────────────────────────────────────────

    def audit(self, user_id: int, action: str, detail: str = "", username: str = ""):
        now = datetime.now(timezone.utc).isoformat()
        detail = detail[:500]
        conn = sqlite3.connect(self._db)
        conn.execute(
            "INSERT INTO audit_log (user_id, username, action, detail, timestamp) "
            "VALUES (?,?,?,?,?)",
            (user_id, username, action, detail, now)
        )
        conn.commit()
        conn.close()
        logger.info("AUDIT [%s] %s: %s", user_id, action, detail[:80])

    def get_audit(self, user_id: int = None, limit: int = 50) -> list[dict]:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def cleanup_audit(self, days: int = 30):
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        conn = sqlite3.connect(self._db)
        conn.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()

    # ── Ban System ─────────────────────────────────────────────────────

    def ban(self, user_id: int, reason: str, hours: float = None):
        now = datetime.now(timezone.utc)
        expires = (now + timedelta(hours=hours)).isoformat() if hours else None
        conn = sqlite3.connect(self._db)
        conn.execute(
            "INSERT OR REPLACE INTO banned (user_id, reason, banned_at, expires_at) "
            "VALUES (?,?,?,?)",
            (user_id, reason, now.isoformat(), expires)
        )
        conn.commit()
        conn.close()
        self.audit(user_id, "BANNED", reason)

    def unban(self, user_id: int):
        conn = sqlite3.connect(self._db)
        conn.execute("DELETE FROM banned WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        self.audit(user_id, "UNBANNED", "Removed")

    def is_banned(self, user_id: int) -> tuple[bool, str]:
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._db)
        row = conn.execute(
            "SELECT reason, expires_at FROM banned WHERE user_id=?", (user_id,)
        ).fetchone()
        conn.close()
        if not row:
            return False, ""
        reason, exp = row
        if exp and exp < now:
            self.unban(user_id)
            return False, ""
        return True, reason

    def get_banned(self) -> list[dict]:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM banned ORDER BY banned_at DESC").fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── Abuse Detection ────────────────────────────────────────────────

    def _flag_abuse(self, user_id: int, flag_type: str, detail: str):
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self._db)
        conn.execute(
            "INSERT INTO abuse_flags (user_id, flag_type, detail, timestamp) "
            "VALUES (?,?,?,?)",
            (user_id, flag_type, detail[:200], now)
        )
        conn.commit()
        conn.close()

    def get_abuse_count(self, user_id: int, hours: int = 24) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        conn = sqlite3.connect(self._db)
        n = conn.execute(
            "SELECT COUNT(*) FROM abuse_flags WHERE user_id=? AND timestamp > ?",
            (user_id, cutoff)
        ).fetchone()[0]
        conn.close()
        return n

    # ── Stats ──────────────────────────────────────────────────────────

    def stats(self) -> dict:
        conn = sqlite3.connect(self._db)
        s = {
            "total_logs": conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0],
            "banned": conn.execute("SELECT COUNT(*) FROM banned").fetchone()[0],
            "unique_users": conn.execute("SELECT COUNT(DISTINCT user_id) FROM audit_log").fetchone()[0],
            "last_24h": conn.execute(
                "SELECT COUNT(*) FROM audit_log WHERE timestamp >= datetime('now','-1 day')"
            ).fetchone()[0],
            "abuse_flags": conn.execute(
                "SELECT COUNT(*) FROM abuse_flags WHERE timestamp >= datetime('now','-1 day')"
            ).fetchone()[0],
        }
        conn.close()
        return s


# ─── Input Sanitization ───────────────────────────────────────────────────────

def sanitize_html(text: str) -> str:
    return _escape(text, quote=True)

def sanitize_text(text: str, max_len: int = 200) -> str:
    cleaned = ''.join(c for c in text if c.isprintable() or c in '\n')
    return cleaned[:max_len].strip()

def validate_email(email: str) -> bool:
    if not email or len(email) > 254:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email.strip()))

def validate_nickname(name: str) -> tuple[bool, str]:
    """Validate Free Fire nickname."""
    name = name.strip()
    if len(name) < 2:
        return False, "الاسم قصير جداً (2+ أحرف)"
    if len(name) > 18:
        return False, "الاسم طويل جداً (18 حرف كحد أقصى)"
    # Check for invalid characters
    if any(c in name for c in '\n\r\t'):
        return False, "أحرف غير مسموحة في الاسم"
    return True, name
