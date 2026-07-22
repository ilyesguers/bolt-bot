"""
BOLT ⚡ — Database Module
━━━━━━━━━━━━━━━━━━━━━━━━━
🆓 Free mode — no subscription codes needed
🔐 All tokens encrypted at rest (AES-256 via Fernet)
📊 User stats, rewards, activity tracking
🗄️ SQLite with WAL mode
"""

import os
import sqlite3
import threading
from datetime import datetime, timezone
from crypto_utils import encrypt_token, decrypt_token, token_fingerprint, mask_token

DB_FILE = os.environ.get("DB_PATH", "bolt.db")
_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_FILE)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Init ─────────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables."""
    with _lock:
        c = _conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id          INTEGER PRIMARY KEY,
            username         TEXT DEFAULT '',
            first_name       TEXT DEFAULT '',
            lang             TEXT DEFAULT 'ar',
            encrypted_token  TEXT DEFAULT NULL,
            token_fingerprint TEXT DEFAULT NULL,
            token_set_at     TEXT DEFAULT NULL,
            joined_at        TEXT NOT NULL,
            last_active      TEXT NOT NULL,
            total_ops        INTEGER DEFAULT 0,
            today_ops        INTEGER DEFAULT 0,
            today_ops_date   TEXT DEFAULT '',
            is_admin         INTEGER DEFAULT 0,
            referral_code    TEXT DEFAULT '',
            referred_by      INTEGER DEFAULT NULL,
            referral_count   INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS rewards (
            user_id       INTEGER NOT NULL,
            points        INTEGER DEFAULT 0,
            level         INTEGER DEFAULT 1,
            last_daily    TEXT DEFAULT '',
            streak        INTEGER DEFAULT 0,
            total_earned  INTEGER DEFAULT 0,
            PRIMARY KEY (user_id)
        );

        CREATE TABLE IF NOT EXISTS reward_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            action      TEXT NOT NULL,
            points      INTEGER NOT NULL,
            detail      TEXT DEFAULT '',
            timestamp   TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_rh_user ON reward_history(user_id, timestamp DESC);

        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            action      TEXT NOT NULL,
            detail      TEXT DEFAULT '',
            success     INTEGER DEFAULT 1,
            timestamp   TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_al_user ON activity_log(user_id, timestamp DESC);

        CREATE TABLE IF NOT EXISTS support_tickets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            subject     TEXT NOT NULL,
            message     TEXT NOT NULL,
            status      TEXT DEFAULT 'open',
            reply       TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL,
            resolved_at TEXT DEFAULT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_st_status ON support_tickets(status);
        """)
        c.commit()
        c.close()


# ─── User CRUD ────────────────────────────────────────────────────────────────

def ensure_user(user_id: int, username: str = "", first_name: str = "") -> dict:
    """Create user if new, update last_active."""
    now = _now()
    with _lock:
        c = _conn()
        existing = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if existing:
            c.execute("UPDATE users SET last_active=?, username=?, first_name=? WHERE user_id=?",
                      (now, username, first_name, user_id))
            c.commit()
            c.close()
            return dict(existing)

        # Generate referral code
        import random, string
        ref = "BLT" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        c.execute("""
            INSERT INTO users (user_id, username, first_name, joined_at, last_active, referral_code)
            VALUES (?,?,?,?,?,?)
        """, (user_id, username, first_name, now, now, ref))
        c.execute("INSERT INTO rewards (user_id, points) VALUES (?,0)", (user_id,))
        c.commit()
        row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        c.close()
        return dict(row)


def get_user(user_id: int) -> dict | None:
    with _lock:
        c = _conn()
        row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    return dict(row) if row else None


def set_lang(user_id: int, lang: str):
    with _lock:
        c = _conn()
        c.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
        c.commit()
        c.close()


def get_lang(user_id: int) -> str:
    u = get_user(user_id)
    return u["lang"] if u else "ar"


# ─── Token Management ────────────────────────────────────────────────────────

def set_token(user_id: int, token: str):
    """Encrypt and store the access token with fingerprint."""
    enc = encrypt_token(token)
    fp = token_fingerprint(token)
    now = _now()
    with _lock:
        c = _conn()
        c.execute("""
            UPDATE users SET encrypted_token=?, token_fingerprint=?, token_set_at=?
            WHERE user_id=?
        """, (enc, fp, now, user_id))
        c.commit()
        c.close()


def get_token(user_id: int) -> str | None:
    """Decrypt and return the stored token."""
    with _lock:
        c = _conn()
        row = c.execute("SELECT encrypted_token FROM users WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    if not row or not row["encrypted_token"]:
        return None
    return decrypt_token(row["encrypted_token"])


def get_token_info(user_id: int) -> dict:
    """Get token metadata (no actual token)."""
    with _lock:
        c = _conn()
        row = c.execute("""
            SELECT encrypted_token, token_fingerprint, token_set_at
            FROM users WHERE user_id=?
        """, (user_id,)).fetchone()
        c.close()
    if not row or not row["encrypted_token"]:
        return {"has_token": False}
    return {
        "has_token": True,
        "fingerprint": row["token_fingerprint"],
        "set_at": row["token_set_at"],
        "masked": "***",  # we don't expose even masked token
    }


def clear_token(user_id: int):
    with _lock:
        c = _conn()
        c.execute("""
            UPDATE users SET encrypted_token=NULL, token_fingerprint=NULL, token_set_at=NULL
            WHERE user_id=?
        """, (user_id,))
        c.commit()
        c.close()


def has_token(user_id: int) -> bool:
    with _lock:
        c = _conn()
        row = c.execute("SELECT encrypted_token FROM users WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    return bool(row and row["encrypted_token"])


# ─── Daily Operations Counter ────────────────────────────────────────────────

DAILY_OP_LIMIT = 15  # generous free limit

def check_daily_ops(user_id: int) -> tuple[bool, int, int]:
    """Returns (allowed, remaining, limit)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        c = _conn()
        row = c.execute("SELECT today_ops, today_ops_date FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row or row["today_ops_date"] != today:
            c.execute("UPDATE users SET today_ops=1, today_ops_date=? WHERE user_id=?", (today, user_id))
            c.commit()
            c.close()
            return True, DAILY_OP_LIMIT - 1, DAILY_OP_LIMIT
        ops = row["today_ops"]
        if ops >= DAILY_OP_LIMIT:
            c.close()
            return False, 0, DAILY_OP_LIMIT
        c.execute("UPDATE users SET today_ops=today_ops+1 WHERE user_id=?", (user_id,))
        c.commit()
        c.close()
        return True, DAILY_OP_LIMIT - ops - 1, DAILY_OP_LIMIT


def increment_ops(user_id: int):
    with _lock:
        c = _conn()
        c.execute("UPDATE users SET total_ops=total_ops+1 WHERE user_id=?", (user_id,))
        c.commit()
        c.close()


# ─── Activity Log ─────────────────────────────────────────────────────────────

def log_activity(user_id: int, action: str, detail: str = "", success: bool = True):
    with _lock:
        c = _conn()
        c.execute("""
            INSERT INTO activity_log (user_id, action, detail, success, timestamp)
            VALUES (?,?,?,?,?)
        """, (user_id, action, detail[:300], 1 if success else 0, _now()))
        c.commit()
        c.close()


def get_activity(user_id: int, limit: int = 20) -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("""
            SELECT * FROM activity_log WHERE user_id=? ORDER BY id DESC LIMIT ?
        """, (user_id, limit)).fetchall()
        c.close()
    return [dict(r) for r in rows]


# ─── Rewards ─────────────────────────────────────────────────────────────────

def get_rewards(user_id: int) -> dict:
    with _lock:
        c = _conn()
        row = c.execute("SELECT * FROM rewards WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    return dict(row) if row else {"user_id": user_id, "points": 0, "level": 1, "streak": 0, "last_daily": ""}


def add_points(user_id: int, points: int, action: str, detail: str = ""):
    """Add reward points and log history."""
    with _lock:
        c = _conn()
        c.execute("UPDATE rewards SET points=points+?, total_earned=total_earned+? WHERE user_id=?",
                  (points, points, user_id))
        # Level up check
        row = c.execute("SELECT points FROM rewards WHERE user_id=?", (user_id,)).fetchone()
        if row:
            level = _calc_level(row["points"])
            c.execute("UPDATE rewards SET level=? WHERE user_id=?", (level, user_id))
        c.execute("""
            INSERT INTO reward_history (user_id, action, points, detail, timestamp)
            VALUES (?,?,?,?,?)
        """, (user_id, action, points, detail[:200], _now()))
        c.commit()
        c.close()


def claim_daily(user_id: int) -> tuple[bool, int]:
    """Claim daily reward. Returns (success, points_earned)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        c = _conn()
        row = c.execute("SELECT last_daily, streak FROM rewards WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            c.close()
            return False, 0
        if row["last_daily"] == today:
            c.close()
            return False, 0

        # Calculate streak
        from datetime import timedelta
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        streak = (row["streak"] + 1) if row["last_daily"] == yesterday else 1
        # Points scale with streak (5 base + 1 per streak day, max 15)
        points = min(5 + streak, 15)

        c.execute("UPDATE rewards SET last_daily=?, streak=?, points=points+?, total_earned=total_earned+? WHERE user_id=?",
                  (today, streak, points, points, user_id))
        c.execute("""
            INSERT INTO reward_history (user_id, action, points, detail, timestamp)
            VALUES (?,?,?,?,?)
        """, (user_id, "daily", points, f"streak={streak}", _now()))
        c.commit()
        c.close()
    return True, points


def _calc_level(points: int) -> int:
    """Calculate level from total points earned."""
    if points < 50: return 1
    if points < 150: return 2
    if points < 350: return 3
    if points < 700: return 4
    if points < 1200: return 5
    if points < 2000: return 6
    if points < 3500: return 7
    return 8  # MAX level


# ─── Support Tickets ─────────────────────────────────────────────────────────

def create_ticket(user_id: int, subject: str, message: str) -> int:
    with _lock:
        c = _conn()
        c.execute("""
            INSERT INTO support_tickets (user_id, subject, message, created_at)
            VALUES (?,?,?,?)
        """, (user_id, subject[:100], message[:1000], _now()))
        tid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.commit()
        c.close()
    return tid


def get_user_tickets(user_id: int) -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("""
            SELECT * FROM support_tickets WHERE user_id=? ORDER BY id DESC LIMIT 10
        """, (user_id,)).fetchall()
        c.close()
    return [dict(r) for r in rows]


def get_open_tickets() -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("""
            SELECT t.*, u.username, u.first_name FROM support_tickets t
            LEFT JOIN users u ON t.user_id = u.user_id
            WHERE t.status='open' ORDER BY t.created_at DESC LIMIT 30
        """).fetchall()
        c.close()
    return [dict(r) for r in rows]


def resolve_ticket(ticket_id: int, reply: str):
    with _lock:
        c = _conn()
        c.execute("""
            UPDATE support_tickets SET status='resolved', reply=?, resolved_at=?
            WHERE id=?
        """, (reply[:1000], _now(), ticket_id))
        c.commit()
        c.close()


# ─── Admin / Stats ────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    owner = int(os.environ.get("OWNER_ID", "0"))
    if user_id == owner:
        return True
    u = get_user(user_id)
    return u is not None and u["is_admin"] == 1


def user_count() -> int:
    with _lock:
        c = _conn()
        n = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        c.close()
    return n


def get_all_user_ids() -> list[int]:
    with _lock:
        c = _conn()
        rows = c.execute("SELECT user_id FROM users").fetchall()
        c.close()
    return [r["user_id"] for r in rows]


def leaderboard(limit: int = 10) -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("""
            SELECT u.user_id, u.username, u.first_name, u.total_ops,
                   r.points, r.level
            FROM users u
            LEFT JOIN rewards r ON u.user_id = r.user_id
            ORDER BY r.points DESC
            LIMIT ?
        """, (limit,)).fetchall()
        c.close()
    return [dict(r) for r in rows]


def export_data() -> dict:
    """Full data export (tokens stay encrypted)."""
    with _lock:
        c = _conn()
        data = {
            "users": [dict(r) for r in c.execute("SELECT * FROM users").fetchall()],
            "rewards": [dict(r) for r in c.execute("SELECT * FROM rewards").fetchall()],
            "tickets": [dict(r) for r in c.execute("SELECT * FROM support_tickets").fetchall()],
            "exported_at": _now(),
        }
        c.close()
    return data
