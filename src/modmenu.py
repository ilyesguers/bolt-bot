"""لوحة تحكم المود مينو — للمباريات الآفلانية ضد AI (Client-Side).

الفرق الجوهري: المباراة ضد الكمبيوتر تُلعب **على الجهاز** بالكامل (القرارات
والنتيجة محلية)، والسيرفر لا يتحقق من كل لحظة. لذلك التعديلات "الأسطورية"
(إنهاء فوراً، فوز تلقائي، إبطاء AI...) ممكنة فيها، لكن **تطبيقها يتم داخل
اللعبة المعدّلة نفسها** (IPA معدل + حقنة dylib تقرأ هذا الإعداد)، وليس عبر
البروكسي — البروكسي لا يرى المباراة لأنها ليست على الشبكة.

هذا الموديول هو الطرف الخادم: يحفظ المفاتيح ويقدمها بصيغة JSON خفيفة
``GET /api/modmenu/config`` يقرأها التطبيق المعدل بانتظام.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .config import DATA_DIR

FEATURES: dict[str, dict[str, str]] = {
    "instant_finish": {
        "name": "إنهاء المباراة فوراً",
        "desc": "ينهي المباراة ويسجّل النتيجة لصالحك",
        "icon": "🏁",
        "risk": "متوسط",
        "note": "Client-Side — داخل التطبيق المعدل",
    },
    "auto_win": {
        "name": "فوز تلقائي",
        "desc": "يثبّت النتيجة محلياً (مثل 3-0)",
        "icon": "🏆",
        "risk": "متوسط",
        "note": "Client-Side — داخل التطبيق المعدل",
    },
    "slow_ai_client": {
        "name": "إبطاء AI (محلي)",
        "desc": "حركة الخصم الكمبيوتر أبطأ على جهازك",
        "icon": "🐢",
        "risk": "منخفض",
        "note": "Client-Side — داخل التطبيق المعدل",
    },
    "ai_miss_client": {
        "name": "AI يخطئ بالتسديد (محلي)",
        "desc": "تسديدات الخصم خارج المرمى",
        "icon": "🎯",
        "risk": "منخفض",
        "note": "Client-Side — داخل التطبيق المعدل",
    },
    "stamina_client": {
        "name": "ستامينا لا تنقص (محلي)",
        "desc": "فريقك لا يتعب أثناء المباراة",
        "icon": "⚡",
        "risk": "منخفض",
        "note": "Client-Side — داخل التطبيق المعدل",
    },
    "stats_max_client": {
        "name": "قيم اللاعبين 99 (محلي)",
        "desc": "يرفع تقييمات فريقك داخل المباراة",
        "icon": "💎",
        "risk": "متوسط",
        "note": "Client-Side — داخل التطبيق المعدل",
    },
}

DATA_FILE = Path(
    os.environ.get("MODMENU_FILE", str(Path(DATA_DIR) / "modmenu.json"))
)

_file_lock = threading.RLock()

PROTOCOL_VERSION = 1


def _defaults() -> dict[str, bool]:
    return {key: False for key in FEATURES}


def _normalize(values: Mapping[str, object] | None) -> dict[str, bool]:
    normalized = _defaults()
    if not values:
        return normalized
    for key in FEATURES:
        normalized[key] = values.get(key) is True
    return normalized


def load_config() -> dict[str, Any]:
    """الحالة المحفوظة + وقت التحديث."""
    with _file_lock:
        bundle: dict[str, Any] = {}
        try:
            if DATA_FILE.exists():
                value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    bundle = value
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        features_raw = bundle.get("features", bundle)
        return {
            "features": _normalize(features_raw),
            "updated_at": bundle.get("updated_at"),
            "protocol": PROTOCOL_VERSION,
        }


def save_config(values: Mapping[str, object]) -> dict[str, Any]:
    """حفظ الحالة كاملة (صيغة JSON خفيفة للتطبيق المعدل)."""
    normalized = _normalize(values)
    with _file_lock:
        bundle = {
            "features": normalized,
            "updated_at": time.time(),
            "protocol": PROTOCOL_VERSION,
        }
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = DATA_FILE.with_name(f".{DATA_FILE.name}.{uuid.uuid4().hex}.tmp")
        try:
            temp_file.write_text(
                json.dumps(bundle, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temp_file, DATA_FILE)
        finally:
            try:
                temp_file.unlink(missing_ok=True)
            except OSError:
                pass
        return bundle


def get_enabled() -> list[str]:
    return [key for key, value in load_config()["features"].items() if value]


def config_payload() -> dict[str, Any]:
    """صيغة يقرأها التطبيق المعدل بسهولة (بدون تعريفات اللوحة)."""
    cfg = load_config()
    return {
        "protocol": PROTOCOL_VERSION,
        "features": cfg["features"],
        "updated_at": cfg["updated_at"],
        "note": "يقرأها التطبيق المعدل؛ التعديل Client-Side على جهازك فقط.",
    }
