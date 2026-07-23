"""
BOLT  — Database Module — FIXED FOR RAILWAY PERSISTENCE
 Users, Tokens, Rewards, Activity
 Admins Management
 Tutorial Videos
 Bans
"""
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from crypto_utils import encrypt_token, decrypt_token, token_fingerprint

# FIX: Support Railway Volume /data and local fallback
def _get_db_path():
    # Priority: ENV -> /data volume (Railway) -> local
    env_path = os.environ.get("DB_PATH")
    if env_path:
        return env_path
    # Railway volume mount is /data
    if os.path.isdir("/data"):
        # Ensure /data exists writable
        try:
            test = "/data/.write_test"
            with open(test, "w") as f: f.write("ok")
            os.remove(test)
            return "/data/bolt.db"
        except:
            pass
    return "bolt.db"

DB_FILE = _get_db_path()
_lock = threading.Lock()


def _conn() -> sqlite3.Connection:
    dirn = os.path.dirname(DB_FILE)
    if dirn and not os.path.exists(dirn):
        os.makedirs(dirn, exist_ok=True)
    c = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA synchronous=NORMAL")
    return c


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Init ─────────────────────────────────────────────────────────────────────

def init_db():
    with _lock:
        c = _conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id          INTEGER PRIMARY KEY,
            username         TEXT DEFAULT '',
            first_name       TEXT DEFAULT '',
            lang             TEXT DEFAULT '',
            onboarded        INTEGER DEFAULT 0,
            encrypted_token  TEXT DEFAULT NULL,
            token_fingerprint TEXT DEFAULT NULL,
            token_set_at     TEXT DEFAULT NULL,
            joined_at        TEXT NOT NULL,
            last_active      TEXT NOT NULL,
            total_ops        INTEGER DEFAULT 0,
            today_ops        INTEGER DEFAULT 0,
            today_ops_date   TEXT DEFAULT '',
            referral_code    TEXT DEFAULT '',
            referred_by      INTEGER DEFAULT NULL
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

        CREATE TABLE IF NOT EXISTS admins (
            user_id       INTEGER PRIMARY KEY,
            added_by      INTEGER NOT NULL,
            added_at      TEXT NOT NULL,
            permissions   TEXT DEFAULT 'full'
        );

        CREATE TABLE IF NOT EXISTS tutorial_videos (
            platform      TEXT PRIMARY KEY,
            video_url     TEXT NOT NULL,
            updated_by    INTEGER NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key           TEXT PRIMARY KEY,
            value         TEXT NOT NULL,
            updated_by    INTEGER NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bans (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            banned_by     INTEGER NOT NULL,
            reason        TEXT NOT NULL,
            duration_hours REAL DEFAULT NULL,
            banned_at     TEXT NOT NULL,
            expires_at    TEXT DEFAULT NULL,
            is_active     INTEGER DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_bans_user ON bans(user_id, is_active);

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
        """)
        c.commit()

        existing = c.execute("SELECT COUNT(*) FROM tutorial_videos").fetchone()[0]
        if existing == 0:
            now = _now()
            c.execute("INSERT INTO tutorial_videos (platform, video_url, updated_by, updated_at) VALUES (?, ?, ?, ?)",
                      ("android", "https://example.com/android-tutorial.mp4", 0, now))
            c.execute("INSERT INTO tutorial_videos (platform, video_url, updated_by, updated_at) VALUES (?, ?, ?, ?)",
                      ("ios", "https://example.com/ios-tutorial.mp4", 0, now))

        c.commit()
        c.close()
        print(f"✅ DB initialized at {DB_FILE}")


# ─── User Management ──────────────────────────────────────────────────────────

def ensure_user(user_id: int, username: str = "", first_name: str = "") -> dict:
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
    return u["lang"] if u and u["lang"] else "ar"


def set_onboarded(user_id: int, value: int = 1):
    with _lock:
        c = _conn()
        c.execute("UPDATE users SET onboarded=? WHERE user_id=?", (value, user_id))
        c.commit()
        c.close()


# ─── Token Management ────────────────────────────────────────────────────────

def set_token(user_id: int, token: str):
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
    with _lock:
        c = _conn()
        row = c.execute("SELECT encrypted_token FROM users WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    if not row or not row["encrypted_token"]:
        return None
    try:
        return decrypt_token(row["encrypted_token"])
    except Exception as e:
        print(f"Decrypt failed for {user_id}: {e} - ENCRYPTION_KEY changed?")
        return None


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


# ─── Admin Management ────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    owner = int(os.environ.get("OWNER_ID", "0"))
    if user_id == owner:
        return True
    with _lock:
        c = _conn()
        row = c.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    return row is not None


def add_admin(user_id: int, added_by: int, permissions: str = "full") -> bool:
    if is_admin(user_id):
        return False
    with _lock:
        c = _conn()
        c.execute("INSERT INTO admins (user_id, added_by, added_at, permissions) VALUES (?,?,?,?)",
                  (user_id, added_by, _now(), permissions))
        c.commit()
        c.close()
    return True


def remove_admin(user_id: int) -> bool:
    owner = int(os.environ.get("OWNER_ID", "0"))
    if user_id == owner:
        return False
    with _lock:
        c = _conn()
        c.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        c.commit()
        c.close()
    return True


def get_admins() -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("SELECT * FROM admins ORDER BY added_at DESC").fetchall()
        c.close()
    return [dict(r) for r in rows]


# ─── Tutorial Videos ─────────────────────────────────────────────────────────

def get_tutorial_video(platform: str) -> str | None:
    with _lock:
        c = _conn()
        row = c.execute("SELECT video_url FROM tutorial_videos WHERE platform=?", (platform,)).fetchone()
        c.close()
    return row["video_url"] if row else None


def update_tutorial_video(platform: str, video_url: str, updated_by: int):
    with _lock:
        c = _conn()
        c.execute("""
            INSERT OR REPLACE INTO tutorial_videos (platform, video_url, updated_by, updated_at)
            VALUES (?,?,?,?)
        """, (platform, video_url, updated_by, _now()))
        c.commit()
        c.close()


# ─── Settings ────────────────────────────────────────────────────────────────

def get_setting(key: str) -> str | None:
    with _lock:
        c = _conn()
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        c.close()
    return row["value"] if row else None


def set_setting(key: str, value: str, updated_by: int):
    with _lock:
        c = _conn()
        c.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_by, updated_at)
            VALUES (?,?,?,?)
        """, (key, value, updated_by, _now()))
        c.commit()
        c.close()


# ─── Ban System ─────────────────────────────────────────────────────────────

def ban_user(user_id: int, banned_by: int, reason: str, duration_hours: float = None) -> bool:
    if is_admin(user_id):
        return False
    with _lock:
        c = _conn()
        c.execute("UPDATE bans SET is_active=0 WHERE user_id=? AND is_active=1", (user_id,))

        expires_at = None
        if duration_hours:
            expires_at = (datetime.now(timezone.utc) + timedelta(hours=duration_hours)).isoformat()

        c.execute("""
            INSERT INTO bans (user_id, banned_by, reason, duration_hours, banned_at, expires_at, is_active)
            VALUES (?,?,?,?,?,?,1)
        """, (user_id, banned_by, reason, duration_hours, _now(), expires_at))
        c.commit()
        c.close()
    return True


def unban_user(user_id: int) -> bool:
    with _lock:
        c = _conn()
        c.execute("UPDATE bans SET is_active=0 WHERE user_id=? AND is_active=1", (user_id,))
        c.commit()
        c.close()
    return True


def is_banned(user_id: int) -> tuple[bool, str]:
    with _lock:
        c = _conn()
        row = c.execute("""
            SELECT reason, expires_at, duration_hours FROM bans
            WHERE user_id=? AND is_active=1
            ORDER BY id DESC LIMIT 1
        """, (user_id,)).fetchone()
        c.close()

    if not row:
        return False, ""

    reason = row["reason"]
    expires_at = row["expires_at"]

    if expires_at:
        if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
            unban_user(user_id)
            return False, ""

    return True, reason


def get_bans(limit: int = 50) -> list[dict]:
    with _lock:
        c = _conn()
        rows = c.execute("""
            SELECT b.*, u.username, u.first_name
            FROM bans b LEFT JOIN users u ON b.user_id = u.user_id
            WHERE b.is_active=1
            ORDER BY b.id DESC LIMIT ?
        """, (limit,)).fetchall()
        c.close()
    return [dict(r) for r in rows]


# ─── Daily Operations ────────────────────────────────────────────────────────

DAILY_OP_LIMIT = 15

def check_daily_ops(user_id: int) -> tuple[bool, int, int]:
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


def peek_daily_ops(user_id: int) -> tuple[int, int]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _lock:
        c = _conn()
        row = c.execute("SELECT today_ops, today_ops_date FROM users WHERE user_id=?", (user_id,)).fetchone()
        c.close()
    if not row or row["today_ops_date"] != today:
        return DAILY_OP_LIMIT, DAILY_OP_LIMIT
    ops = row["today_ops"]
    return max(0, DAILY_OP_LIMIT - ops), DAILY_OP_LIMIT


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
    return dict(row) if row else {"user_id": user_id, "points": 0, "level": 1, "streak": 0, "last_daily": "", "total_earned": 0}


def add_points(user_id: int, points: int, action: str = "", detail: str = ""):
    with _lock:
        c = _conn()
        c.execute("UPDATE rewards SET points=points+?, total_earned=total_earned+? WHERE user_id=?",
                  (points, points, user_id))
        c.commit()
        c.close()


def claim_daily(user_id: int) -> tuple[bool, int]:
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

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        streak = (row["streak"] + 1) if row["last_daily"] == yesterday else 1
        points = min(5 + streak, 15)

        c.execute("UPDATE rewards SET last_daily=?, streak=?, points=points+?, total_earned=total_earned+? WHERE user_id=?",
                  (today, streak, points, points, user_id))
        c.commit()
        c.close()
    return True, points


# ─── Support Tickets ────────────────────────────────────────────────────────

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


# ─── Stats ────────────────────────────────────────────────────────────────────

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
    with _lock:
        c = _conn()
        data = {
            "users": [dict(r) for r in c.execute("SELECT * FROM users").fetchall()],
            "admins": [dict(r) for r in c.execute("SELECT * FROM admins").fetchall()],
            "rewards": [dict(r) for r in c.execute("SELECT * FROM rewards").fetchall()],
            "tickets": [dict(r) for r in c.execute("SELECT * FROM support_tickets").fetchall()],
            "bans": [dict(r) for r in c.execute("SELECT * FROM bans WHERE is_active=1").fetchall()],
            "exported_at": _now(),
            "db_path": DB_FILE,
        }
        c.close()
    return data
