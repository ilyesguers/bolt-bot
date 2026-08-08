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

from .config import DATA_DIR

DATA_FILE = Path(
    os.environ.get("NETCTL_FILE", str(Path(DATA_DIR) / "netctl.json"))
)

_lock = threading.RLock()
_action_lock = threading.Lock()
_actions: deque[dict[str, Any]] = deque(maxlen=20)

# نسخة حية سريعة القراءة — تُحدَّث من الملف عند التحميل/الحفظ
_settings: dict[str, Any] = {
    "throttle_kbps": 0,
    "block_hosts": [],
    "result_guard": False,
}

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

    block_hosts = bundle.get("block_hosts", [])
    if not isinstance(block_hosts, list):
        block_hosts = []
    cleaned = []
    for item in block_hosts:
        text = str(item).strip().lower().lstrip(".")
        if text and text not in cleaned:
            cleaned.append(text)

    return {
        "throttle_kbps": throttle,
        "block_hosts": cleaned[:50],
        "result_guard": bundle.get("result_guard") is True,
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
            f"منع رفع النتيجة: {'نشط' if current['result_guard'] else 'متوقف'}",
        )
        return dict(current)


def get_setting(key: str) -> Any:
    with _lock:
        return _settings.get(key)


def throttle_kbps() -> int:
    with _lock:
        return int(_settings.get("throttle_kbps", 0))


def should_block(host: str) -> bool:
    """هل النطاق في قائمة الحظر؟ (مطابقة لاحقة بعد تنظيف المنفذ)."""
    if not host:
        return False
    value = (host or "").strip().lower().rstrip(".")
    if ":" in value:
        value = value.rsplit(":", 1)[0]
    with _lock:
        rules = _settings.get("block_hosts", [])
    return any(value == rule or value.endswith("." + rule) for rule in rules)


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


def kill_all(reason: str = "طلب يدوي من اللوحة") -> int:
    """قطع كل الأنفاق النشطة فوراً (إغلاق الـ writers من خيط الويب)."""
    with _lock:
        targets = list(_sessions.values())
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


# ---------------------------------------------------------------------------
# سجل الإجراءات
# ---------------------------------------------------------------------------

def record_action(msg: str, detail: str = "") -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": time.time(),
        "time": time.strftime("%H:%M:%S"),
        "msg": str(msg),
        "detail": str(detail),
    }
    with _action_lock:
        _actions.append(item)
    return item


def get_actions() -> list[dict[str, Any]]:
    with _action_lock:
        return list(_actions)[-10:][::-1]
