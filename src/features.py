"""Persistent feature preferences and bounded live notifications."""
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

from .ai_analyzer import is_ai_file
from .config import DATA_DIR

FEATURES: dict[str, dict[str, str]] = {
    "slow_ai": {
        "name": "إبطاء AI 50%",
        "desc": "AI يتحرك ببطء",
        "icon": "🐢",
        "risk": "منخفض",
    },
    "show_ai": {
        "name": "إظهار قرار AI",
        "desc": "سهم أين سيمرر",
        "icon": "👁️",
        "risk": "منخفض",
    },
    "no_press": {
        "name": "AI لا يضغط",
        "desc": "يبقى بعيد 5م",
        "icon": "🚫",
        "risk": "منخفض",
    },
    "stamina": {
        "name": "ستامينا لا تنقص",
        "desc": "فريقك لا يتعب",
        "icon": "⚡",
        "risk": "متوسط",
    },
    "ai_miss": {
        "name": "تسديد AI يخطئ",
        "desc": "تسديداته خارج",
        "icon": "🎯",
        "risk": "متوسط",
    },
}

DATA_FILE = Path(
    os.environ.get("FEATURES_FILE", str(Path(DATA_DIR) / "features.json"))
)

_file_lock = threading.RLock()
_notification_lock = threading.Lock()
notifications: deque[dict[str, Any]] = deque(maxlen=20)


def _defaults() -> dict[str, bool]:
    return {key: False for key in FEATURES}


def _normalize(values: Mapping[str, object] | None) -> dict[str, bool]:
    normalized = _defaults()
    if not values:
        return normalized
    for key in FEATURES:
        # Deliberately accept JSON booleans only, not truthy strings/numbers.
        normalized[key] = values.get(key) is True
    return normalized


def load_features() -> dict[str, bool]:
    """Load preferences, filling missing keys and ignoring malformed data."""
    with _file_lock:
        try:
            if DATA_FILE.exists():
                value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    return _normalize(value)
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    return _defaults()


def save_features(enabled: Mapping[str, object]) -> dict[str, bool]:
    """Atomically persist the complete normalized feature map."""
    normalized = _normalize(enabled)
    with _file_lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = DATA_FILE.with_name(f".{DATA_FILE.name}.{uuid.uuid4().hex}.tmp")
        try:
            temp_file.write_text(
                json.dumps(normalized, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temp_file, DATA_FILE)
        finally:
            try:
                temp_file.unlink(missing_ok=True)
            except OSError:
                pass
    return normalized


def get_enabled() -> list[str]:
    return [key for key, value in load_features().items() if value]


def is_ai_host(host: str) -> bool:
    return is_ai_file(host)


def add_notification(msg: str, level: str = "info", **details: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": time.time(),
        "time": time.strftime("%H:%M:%S"),
        "level": level,
        "msg": str(msg),
    }
    if details:
        item["details"] = details
    with _notification_lock:
        notifications.append(item)
    return item


def get_notifications() -> list[dict[str, Any]]:
    with _notification_lock:
        return list(notifications)[-10:][::-1]
