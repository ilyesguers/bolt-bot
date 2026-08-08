"""أدوات التحكم الشبكي — تعمل عبر البروكسي فقط (لا IPA، لا مود مينو).

التحكمات الممكنة عبر بروكسي نفق شفاف هي **شبكية بحتة**:

- قطع الاتصالات النشطة (kill) — يغلق أنفاق TCP مع خادم اللعبة فوراً.
- تحديد سرعة المرور (throttle) — حد أقصى KB/s لكل اتصال.
- حجب نطاقات (blocklist) — يرفض الاتصال بنطاقات محددة (مثلاً القياسات/الإعلانات).
- إسقاط مزامنة ما بعد المباراة (result_guard) — تقديري: يُسقط اتصالات
  خادم AI التي تظهر بعد "نهاية المباراة" لمنع رفع النتيجة.

**لا يمكن للبروكسي تغيير ذكاء AI أو النتيجة داخل اللعبة**: المباريات
الآفلانية تُحسب على الجهاز (لا تمر بالشبكة)، والأونلاين مشفّر TLS 1.3
ومتحقق منه Server-Side. كل إجراء هنا يوصف بوضوح في اللوحة.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import deque
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import DATA_DIR, is_efootball_host
from .ai_analyzer import AI_HOSTS, is_ai_file

DATA_FILE = Path(
    os.environ.get("NETCTL_FILE", str(Path(DATA_DIR) / "netctl.json"))
)

_lock = threading.RLock()
_action_lock = threading.Lock()
_actions: deque[dict[str, Any]] = deque(maxlen=20)
# لمنع تكرار نفس الإجراء/الإشعار مع كل إعادة محاولة من اللعبة
_recent_actions: dict[str, float] = {}
DEFAULT_DEDUP_SEC = 30.0

# ساعة قابلة للاستبدال في الاختبارات
_now = time.time

# نسخة حية سريعة القراءة — تُحدَّث من الملف عند التحميل/الحفظ
_settings: dict[str, Any] = {
    "throttle_kbps": 0,
    "block_hosts": [],
    "result_guard": False,
    "result_guard_scope": "offline",   # "offline" (موصى به) أو "all"
    "block_matchmaking": False,
    "auto_finish_sec": 0,              # 0 = مؤقّت المباراة متوقف
    "jitter_ms": 0,                    # 0 = بدون تأخير عشوائي
    "finish_cooldown_sec": 120,
}

# كلمات دالة على نطاقات المطابقة/البحث عن الخصم (تخمين — ليست بروتوكولاً موثقاً)
MATCHMAKING_KEYWORDS = ("match", "lobby", "queue", "search", "battle", "room", "mm")

# حجب مؤقت (منع إعادة الاتصال بعد إنهاء المباراة) — host -> حتى (timestamp)
_temp_blocks: dict[str, float] = {}

_sessions: dict[int, dict[str, Any]] = {}
_next_id = 0


# ---------------------------------------------------------------------------
# الإعدادات
# ---------------------------------------------------------------------------

def _normalize(bundle: Mapping[str, Any] | None) -> dict[str, Any]:
    bundle = bundle or {}
    throttle = bundle.get("throttle_kbps", 0)
    try:
        throttle = max(0, min(200_000, int(throttle)))
    except (TypeError, ValueError):
        throttle = 0

    cooldown = bundle.get("finish_cooldown_sec", 120)
    try:
        cooldown = max(0, min(3600, int(cooldown)))
    except (TypeError, ValueError):
        cooldown = 120

    auto_finish = bundle.get("auto_finish_sec", 0)
    try:
        auto_finish = max(0, min(3600, int(auto_finish)))
    except (TypeError, ValueError):
        auto_finish = 0

    jitter = bundle.get("jitter_ms", 0)
    try:
        jitter = max(0, min(2000, int(jitter)))
    except (TypeError, ValueError):
        jitter = 0

    scope = bundle.get("result_guard_scope", "offline")
    if scope not in ("offline", "all"):
        scope = "offline"

    block_hosts = bundle.get("block_hosts", [])
    if not isinstance(block_hosts, list):
        block_hosts = []
    cleaned = []
    for item in block_hosts:
        text = str(item).strip().lower().lstrip(".")
        # حماية الذات: لا يمكن إضافة دومين اللوحة/الاستضافة لقائمة الحظر
        if text and text not in cleaned and not is_protected_host(text):
            cleaned.append(text)

    return {
        "throttle_kbps": throttle,
        "block_hosts": cleaned[:50],
        "result_guard": bundle.get("result_guard") is True,
        "result_guard_scope": scope,
        "block_matchmaking": bundle.get("block_matchmaking") is True,
        "auto_finish_sec": auto_finish,
        "jitter_ms": jitter,
        "finish_cooldown_sec": cooldown,
        "updated_at": bundle.get("updated_at"),
    }


def load_settings() -> dict[str, Any]:
    """اقرأ الإعدادات من الملف وحدّث النسخة الحية."""
    global _settings
    with _lock:
        bundle: dict[str, Any] = {}
        try:
            if DATA_FILE.exists():
                value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    bundle = value
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        _settings = _normalize(bundle)
        return dict(_settings)


def save_settings(values: Mapping[str, Any]) -> dict[str, Any]:
    """حفظ الإعدادات (تطبيع + ذرّي) وتسجيل الإجراء."""
    global _settings
    with _lock:
        current = _normalize(values)
        current["updated_at"] = time.time()
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = DATA_FILE.with_name(f".{DATA_FILE.name}.{uuid.uuid4().hex}.tmp")
        try:
            temp_file.write_text(
                json.dumps(current, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temp_file, DATA_FILE)
        finally:
            try:
                temp_file.unlink(missing_ok=True)
            except OSError:
                pass
        _settings = dict(current)
        record_action(
            "⚙️ تغيير إعدادات الشبكة",
            f"تحديد سرعة: {current['throttle_kbps']}KB/s • حجب: {len(current['block_hosts'])} نطاق • "
            f"منع رفع النتيجة: {'نشط' if current['result_guard'] else 'متوقف'} • "
            f"مانع المطابقة: {'نشط' if current['block_matchmaking'] else 'متوقف'} • "
            f"مؤقّت المباراة: {current['auto_finish_sec']}ث • "
            f"Jitter: {current['jitter_ms']}ms",
        )
        return dict(current)


def get_setting(key: str) -> Any:
    with _lock:
        return _settings.get(key)


def throttle_kbps() -> int:
    with _lock:
        return int(_settings.get("throttle_kbps", 0))


def _clean_host(host: str) -> str:
    value = (host or "").strip().lower().rstrip(".")
    if ":" in value:
        value = value.rsplit(":", 1)[0]
    return value


# ---------------------------------------------------------------------------
# حماية الذات: لا يُحجب أبداً دومين اللوحة نفسه ولا منصة الاستضافة
# ---------------------------------------------------------------------------

# لواحق منصات الاستضافة المدعومة — أي مضيف ينتهي بها يعتبر "ذاتنا"
PROTECTED_SUFFIXES = ("railway.app", "railway.internal", "railway.com", "localhost")


def _env_protected_hosts() -> set[str]:
    """مضيفات محمية إضافية من البيئة: PROTECTED_HOSTS + دومين النشر."""
    hosts: set[str] = set()
    for chunk in os.environ.get("PROTECTED_HOSTS", "").split(","):
        value = _clean_host(chunk)
        if value:
            hosts.add(value)
    for key in ("RAILWAY_PUBLIC_DOMAIN", "DASHBOARD_HOST"):
        value = _clean_host(os.environ.get(key, ""))
        if value:
            hosts.add(value)
    return hosts


def is_protected_host(host: str) -> bool:
    """True للمضيفات التي يمنع حجبها دائماً (دومين اللوحة/الاستضافة/localhost)."""
    value = _clean_host(host)
    if not value:
        return False
    if value in ("127.0.0.1", "::1"):
        return True
    if any(value == suffix or value.endswith("." + suffix) for suffix in PROTECTED_SUFFIXES):
        return True
    return any(value == p or value.endswith("." + p) for p in _env_protected_hosts())


def is_game_host(host: str) -> bool:
    """True فقط لنطاقات اللعبة (KONAMI/eFootball + خادم AI) غير المحمية.

    يستخدمه "إنهاء المباراة" ليحجب اللعبة وحدها دون يوتيوب/انستغرام/آبل
    ودون دومين اللوحة نفسه.
    """
    value = _clean_host(host)
    if not value or is_protected_host(value):
        return False
    return is_efootball_host(value) or is_ai_file(value)


def is_matchmaking_host(host: str) -> bool:
    """تخمين: هل النطاق يخص المطابقة/البحث عن الخصم؟

    يستخدم كلمات دالة شائعة (match/lobby/queue/search/...) داخل أسماء
    المضيفات. يُستثنى خادم بيانات AI حتى لا يقطع المزامنة الآفلانية.
    هذه قاعدة تخمينية — ليست قائمة نطاقات KONAMI موثقة.
    """
    value = _clean_host(host)
    if not value or is_ai_file(value):
        return False
    hostname = value.rsplit(".", 1)[0] if "." in value else value
    return any(keyword in hostname for keyword in MATCHMAKING_KEYWORDS)


def block_reason(host: str) -> str | None:
    """سبب منع الاتصال إن وُجد: كولداون الإنهاء / قائمة الحظر / مانع المطابقة.

    المضيفات المحمية (دومين اللوحة/منصة الاستضافة) لا تُحجب أبداً.
    """
    if not host:
        return None
    value = _clean_host(host)
    if is_protected_host(value):
        return None
    now = _now()
    with _lock:
        until = _temp_blocks.get(value)
        if until is not None:
            if until > now:
                return "cooldown_finish"
            _temp_blocks.pop(value, None)
        rules = _settings.get("block_hosts", [])
        matchmaking = _settings.get("block_matchmaking", False)
    if any(value == rule or value.endswith("." + rule) for rule in rules):
        return "blocklist"
    if matchmaking and is_matchmaking_host(value):
        return "matchmaking"
    return None


def should_block(host: str) -> bool:
    return block_reason(host) is not None


def jitter_ms() -> int:
    with _lock:
        return int(_settings.get("jitter_ms", 0))


def auto_finish_sec() -> int:
    with _lock:
        return int(_settings.get("auto_finish_sec", 0))


def auto_finish_due(session_start: float | None, now: float | None = None) -> bool:
    """هل انقضت مدة مؤقّت المباراة؟ (0 = المؤقّت متوقف)."""
    limit = auto_finish_sec()
    if limit <= 0 or not session_start:
        return False
    return (_now() if now is None else now) - session_start >= limit


def result_guard_applies(host: str, phase: str, mode: str) -> bool:
    """هل يسقط منع رفع النتيجة هذا الاتصال؟

    - يجب أن يكون منع رفع النتيجة مفعّلاً + الطور ``full_time`` + مضيف AI.
    - ``result_guard_scope``: ``offline`` (موصى به) = فقط عندما تكون
      الجلسة مصنّفة ``offline_ai``؛ ``all`` = أي جلسة.
    """
    if not _settings.get("result_guard"):
        return False
    if phase != "full_time" or not is_ai_file(host):
        return False
    scope = _settings.get("result_guard_scope", "offline")
    if scope == "offline":
        return mode == "offline_ai"
    return True


def temp_blocks() -> list[dict[str, Any]]:
    """قائمة الحجب المؤقت مع الوقت المتبقي (للعرض في اللوحة)."""
    now = _now()
    with _lock:
        expired = [h for h, until in _temp_blocks.items() if until <= now]
        for host in expired:
            _temp_blocks.pop(host, None)
        return [
            {"host": host, "until": until, "remaining": round(until - now, 1)}
            for host, until in sorted(_temp_blocks.items(), key=lambda item: item[1])
        ]


def finish_match(cooldown_sec: int | None = None) -> dict[str, Any]:
    """⚡ إنهاء المباراة الآن: قطع اتصالات اللعبة فقط + منع عودتها مؤقتاً.

    - يغلق فوراً أنفاق اللعبة فقط (نطاقات KONAMI/eFootball وخادم AI).
    - يضيف حجباً مؤقتاً (كولداون) لنطاقات اللعبة فقط، حتى لا تعود وتكمل
      المباراة/المزامنة. بقية الترافيك (يوتيوب/انستغرام/آبل...) والمضيفات
      المحمية (دومين اللوحة ومنصة الاستضافة) لا تُمس أبداً.
    - يعيد ملخص: عدد المقصوص + المضيفات المحجوبة + مدة الكولداون.

    هذه "إنهاء" شبكي: في الأونلاين تنتهي المباراة بالقطع (تُحسب حسب سياسة
    اللعبة)، وفي الآفلان تمنع المزامنة (اللعبة محلية) — لا تغيّر النتيجة.
    """
    with _lock:
        default = int(_settings.get("finish_cooldown_sec", 120))
    cooldown = int(cooldown_sec) if cooldown_sec is not None else default
    cooldown = max(0, min(3600, cooldown))

    now = _now()
    hosts: set[str] = set()
    with _lock:
        session_hosts = [
            _clean_host(session.get("host", "")) for session in _sessions.values()
        ]
    for host in list(AI_HOSTS) + session_hosts:
        if is_game_host(host):
            hosts.add(host)

    killed = kill_game_sessions("⚡ إنهاء المباراة — قطع اتصالات اللعبة فقط")

    until = now + cooldown
    with _lock:
        for host in hosts:
            if host:
                _temp_blocks[host] = until
        expired = [h for h, u in _temp_blocks.items() if u <= now]
        for host in expired:
            _temp_blocks.pop(host, None)

    blocked = sorted(host for host in hosts if host)
    record_action(
        "⚡ إنهاء المباراة",
        f"قُطعت {killed} اتصالات • حُجب العودة لـ {len(blocked)} مضيف لمدة {cooldown} ثانية"
        + (f" ({', '.join(blocked[:4])}{'…' if len(blocked) > 4 else ''})" if blocked else ""),
    )
    return {
        "killed": killed,
        "blocked_hosts": blocked,
        "until": until,
        "cooldown_sec": cooldown,
    }


# ---------------------------------------------------------------------------
# جلسات نشطة + قطع
# ---------------------------------------------------------------------------

def register_session(writer, loop, host: str, port: int) -> int:
    global _next_id
    with _lock:
        _next_id += 1
        session_id = _next_id
        _sessions[session_id] = {
            "id": session_id,
            "host": host,
            "port": port,
            "start": time.time(),
            "abort": False,
            "writer": writer,
            "loop": loop,
        }
        return session_id


def unregister_session(session_id: int) -> None:
    with _lock:
        _sessions.pop(session_id, None)


def should_abort(session_id: int) -> bool:
    with _lock:
        session = _sessions.get(session_id)
        return bool(session and session["abort"])


def active_sessions() -> list[dict[str, Any]]:
    with _lock:
        now = time.time()
        return [
            {
                "id": session["id"],
                "host": session["host"],
                "port": session["port"],
                "age_sec": round(now - session["start"], 1),
            }
            for session in _sessions.values()
        ]


def _kill_sessions(reason: str, host_filter=None) -> int:
    """قطع الأنفاق النشطة فوراً (إغلاق الـ writers من خيط الويب).

    ``host_filter`` اختياري: دالة تستقبل المضيف النظيف وتعيد True للجلسات
    المراد قطعها — بدونه تُقطع كل الجلسات.
    """
    with _lock:
        targets = [
            session
            for session in _sessions.values()
            if host_filter is None or host_filter(_clean_host(session.get("host", "")))
        ]
        for session in targets:
            session["abort"] = True
            writer = session.get("writer")
            loop = session.get("loop")
            if writer is not None and loop is not None:
                try:
                    loop.call_soon_threadsafe(writer.close)
                except Exception:
                    pass
        count = len(targets)
    if count:
        record_action("🔌 قطع الاتصال", f"أُغلق {count} اتصال نشط — {reason}")
    return count


def kill_all(reason: str = "طلب يدوي من اللوحة") -> int:
    """قطع كل الأنفاق النشطة فوراً."""
    return _kill_sessions(reason)


def kill_game_sessions(reason: str = "إنهاء المباراة") -> int:
    """قطع اتصالات اللعبة فقط (نطاقات KONAMI/AI) دون بقية الترافيك."""
    return _kill_sessions(reason, is_game_host)


# ---------------------------------------------------------------------------
# سجل الإجراءات
# ---------------------------------------------------------------------------

def record_action(msg: str, detail: str = "", dedup_sec: float = 0.0) -> dict[str, Any] | None:
    """سجّل إجراءً؛ مع ``dedup_sec`` يُهمل نفس الإجراء (نفس النص والتفاصيل)
    خلال النافذة — لمنع إغراق السجل بإعادات المحاولة المتطابقة."""
    now = time.time()
    key = f"{msg}|{detail}"
    with _action_lock:
        if dedup_sec > 0:
            last = _recent_actions.get(key)
            if last is not None and now - last < dedup_sec:
                return None
            _recent_actions[key] = now
            if len(_recent_actions) > 200:
                cutoff = now - dedup_sec
                for stale in [k for k, v in _recent_actions.items() if v < cutoff]:
                    _recent_actions.pop(stale, None)
        item: dict[str, Any] = {
            "id": uuid.uuid4().hex[:8],
            "timestamp": now,
            "time": time.strftime("%H:%M:%S", time.localtime(now)),
            "msg": str(msg),
            "detail": str(detail),
        }
        _actions.append(item)
    return item


def get_actions() -> list[dict[str, Any]]:
    with _action_lock:
        return list(_actions)[-10:][::-1]
