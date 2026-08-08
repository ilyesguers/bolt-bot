"""Persistent feature preferences, bounded live notifications, and per-feature status (v5.2).

الميزات نوعان:

- ``patch`` — تعديلات بايتات تجريبية لبيانات مفكوكة/Offline فقط؛ لا تُطبَّق على
  نفق TLS أبداً (تعديل ciphertext يكسر تحقق AEAD ويقطع اللعبة).
- ``detect`` — ميزات رصد تعمل على الميتاداتا نفسها (أحجام، توقيت، أطوار مباراة
  تقديرية) وبالتالي تعمل فعلاً داخل CONNECT دون لمس البايتات.
- ``ui`` — عرض فقط (لا يوجد تعديل).
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

from .ai_analyzer import is_ai_file
from .config import DATA_DIR
from .match_tracker import PHASE_LABELS, tracker

# ---------------------------------------------------------------------------
# التعريفات
# ---------------------------------------------------------------------------

TARGETS: dict[str, str] = {
    "me": "عليك",
    "opponent": "على الخصم",
    "both": "كلاهما",
}

TIMINGS: dict[str, str] = {
    "any": "فوراً/دائماً",
    "early": "بدري (البداية والشوط الأول)",
    "late": "متأخر (الشوط الثاني والنهاية)",
}

KIND_PATCH = "patch"
KIND_DETECT = "detect"
KIND_UI = "ui"

FEATURES: dict[str, dict[str, str]] = {
    # --- ميزات التعديل التجريبية (لا تُطبَّق على TLS) -------------------
    "slow_ai": {
        "name": "إبطاء AI 50%",
        "desc": "AI يتحرك ببطء",
        "icon": "🐢",
        "risk": "منخفض",
        "kind": KIND_PATCH,
        "target": "me",
        "timing": "late",
        "verdict": "تعديل بايتات تجريبي — لا يُطبَّق على نفق TLS المشفر.",
    },
    "show_ai": {
        "name": "إظهار قرار AI",
        "desc": "سهم أين سيمرر",
        "icon": "👁️",
        "risk": "منخفض",
        "kind": KIND_UI,
        "target": "both",
        "timing": "any",
        "verdict": "واجهة عرض فقط — لا يوجد تعديل على الشبكة.",
    },
    "no_press": {
        "name": "AI لا يضغط",
        "desc": "يبقى بعيد 5م",
        "icon": "🚫",
        "risk": "منخفض",
        "kind": KIND_PATCH,
        "target": "opponent",
        "timing": "late",
        "verdict": "تعديل بايتات تجريبي — لا يُطبَّق على نفق TLS المشفر.",
    },
    "stamina": {
        "name": "ستامينا لا تنقص",
        "desc": "فريقك لا يتعب",
        "icon": "⚡",
        "risk": "متوسط",
        "kind": KIND_PATCH,
        "target": "me",
        "timing": "any",
        "verdict": "تعديل بايتات تجريبي — لا يُطبَّق على نفق TLS المشفر.",
    },
    "ai_miss": {
        "name": "تسديد AI يخطئ",
        "desc": "تسديداته خارج",
        "icon": "🎯",
        "risk": "متوسط",
        "kind": KIND_PATCH,
        "target": "opponent",
        "timing": "late",
        "verdict": "تعديل بايتات تجريبي — لا يُطبَّق على نفق TLS المشفر.",
    },
    # --- ميزات الرصد الحقيقية (تعمل على الميتاداتا داخل CONNECT) --------
    "kickoff_alert": {
        "name": "تنبيه بداية المباراة",
        "desc": "يُشعرك فور رصد إشارة البداية",
        "icon": "⚽",
        "risk": "لا شيء",
        "kind": KIND_DETECT,
        "target": "both",
        "timing": "early",
        "verdict": "رصد تقديري من حجم الترافيك — يعمل داخل CONNECT.",
    },
    "match_end_alert": {
        "name": "تنبيه نهاية المباراة",
        "desc": "يُشعرك فور رصد إشارة النهاية",
        "icon": "🏁",
        "risk": "لا شيء",
        "kind": KIND_DETECT,
        "target": "both",
        "timing": "late",
        "verdict": "رصد تقديري من حجم الترافيك — يعمل داخل CONNECT.",
    },
    "live_match": {
        "name": "متابعة المباراة الحية",
        "desc": "أطوار: بداية/استراحة/نهاية + إحصائيات",
        "icon": "📡",
        "risk": "لا شيء",
        "kind": KIND_DETECT,
        "target": "both",
        "timing": "any",
        "verdict": "متتبع أطوار تقديري — يعمل داخل CONNECT.",
    },
    "server_ping": {
        "name": "قياس بينغ الخادم",
        "desc": "زمن استجابة خادم AI لكل اتصال",
        "icon": "📶",
        "risk": "لا شيء",
        "kind": KIND_DETECT,
        "target": "both",
        "timing": "any",
        "verdict": "قياس مدة الاتصال وحجمه — يعمل داخل CONNECT.",
    },
}

# ---------------------------------------------------------------------------
# التخزين
# ---------------------------------------------------------------------------

DATA_FILE = Path(
    os.environ.get("FEATURES_FILE", str(Path(DATA_DIR) / "features.json"))
)

_file_lock = threading.RLock()
_notification_lock = threading.Lock()
notifications: deque[dict[str, Any]] = deque(maxlen=20)

# نافذة منع تكرار نفس الإشعار (اللعبة تعيد المحاولة كل ~ثانية أثناء الحجب)
NOTIFY_DEDUP_SEC = float(os.environ.get("NOTIFY_DEDUP_SEC", "30"))
_recent_notifications: dict[str, float] = {}

# آخر تحليل اتصال AI (لحساب حالة الميزات في اللوحة)
_last_analysis_lock = threading.Lock()
_last_analysis: dict[str, Any] | None = None


def _defaults() -> dict[str, bool]:
    return {key: False for key in FEATURES}


def _default_targets() -> dict[str, str]:
    return {key: meta.get("target", "both") for key, meta in FEATURES.items()}


def _default_timings() -> dict[str, str]:
    return {key: meta.get("timing", "any") for key, meta in FEATURES.items()}


def _normalize(values: Mapping[str, object] | None) -> dict[str, bool]:
    normalized = _defaults()
    if not values:
        return normalized
    for key in FEATURES:
        # Deliberately accept JSON booleans only, not truthy strings/numbers.
        normalized[key] = values.get(key) is True
    return normalized


def _normalize_targets(values: Mapping[str, object] | None) -> dict[str, str]:
    normalized = _default_targets()
    if not values:
        return normalized
    for key in FEATURES:
        value = values.get(key)
        if value in TARGETS:
            normalized[key] = str(value)
    return normalized


def _normalize_timings(values: Mapping[str, object] | None) -> dict[str, str]:
    normalized = _default_timings()
    if not values:
        return normalized
    for key in FEATURES:
        value = values.get(key)
        if value in TIMINGS:
            normalized[key] = str(value)
    return normalized


def _read_bundle() -> dict[str, Any]:
    """اقرأ الملف الكامل؛ يرجع بنية نظيفة دائماً."""
    bundle: dict[str, Any] = {}
    try:
        if DATA_FILE.exists():
            value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                bundle = value
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    # توافق مع الصيغة القديمة: {"slow_ai": true, ...}
    if "features" not in bundle:
        features_raw = {k: v for k, v in bundle.items() if k in FEATURES}
        targets_raw = bundle.get("targets")
        timings_raw = bundle.get("timings")
    else:
        features_raw = bundle.get("features", {})
        targets_raw = bundle.get("targets")
        timings_raw = bundle.get("timings")

    return {
        "features": _normalize(features_raw),
        "targets": _normalize_targets(targets_raw),
        "timings": _normalize_timings(timings_raw),
        "saved_at": bundle.get("saved_at"),
    }


def load_features() -> dict[str, bool]:
    """Load preferences, filling missing keys and ignoring malformed data."""
    with _file_lock:
        return _read_bundle()["features"]


def load_prefs() -> dict[str, Any]:
    """التحميل الكامل: الحالة + الهدف + التوقيت لكل ميزة."""
    with _file_lock:
        return _read_bundle()


def save_prefs(
    features: Mapping[str, object] | None = None,
    targets: Mapping[str, object] | None = None,
    timings: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """حفظ الحزمة كاملة (state + targets + timings) بشكل ذرّي."""
    with _file_lock:
        current = _read_bundle()
        current["features"] = _normalize(features) if features is not None else current["features"]
        if targets is not None:
            current["targets"] = _normalize_targets(targets)
        if timings is not None:
            current["timings"] = _normalize_timings(timings)
        current["saved_at"] = time.time()

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
        return current


def save_features(enabled: Mapping[str, object]) -> dict[str, bool]:
    """Back-compat: حفظ الحالة فقط، مع الإبقاء على targets/timings الحالية."""
    saved = save_prefs(features=enabled)
    return saved["features"]


def get_enabled() -> list[str]:
    return [key for key, value in load_features().items() if value]


def is_ai_host(host: str) -> bool:
    return is_ai_file(host)

# ---------------------------------------------------------------------------
# حالة الميزات لكل اتصال AI
# ---------------------------------------------------------------------------

STATUS_DISABLED = "disabled"
STATUS_ACTIVE = "active"            # ميزة رصد: نافذة التفعيل مفتوحة
STATUS_WAIT_TIMING = "wait_timing"  # ميزة رصد/تعديل: خارج نافذة التوقيت
STATUS_APPLIED = "applied"          # تعديل طُبّق (Offline/مفكوك فقط)
STATUS_BLOCKED_TLS = "blocked_tls"  # TLS مشفر — لا يمكن تعديله
STATUS_BLOCKED_OPPONENT = "blocked_opponent"  # الخصم خارج نطاق جهازك
STATUS_UI_ONLY = "ui_only"          # عرض فقط

STATUS_LABELS: dict[str, str] = {
    STATUS_DISABLED: "معطّلة",
    STATUS_ACTIVE: "نشطة (رصد يعمل)",
    STATUS_WAIT_TIMING: "مؤجلة — بانتظار توقيت التفعيل",
    STATUS_APPLIED: "طُبّقت",
    STATUS_BLOCKED_TLS: "محجوبة — TLS مشفر",
    STATUS_BLOCKED_OPPONENT: "محجوبة — الخصم خارج جهازك",
    STATUS_UI_ONLY: "واجهة فقط",
}


def feature_status(
    key: str,
    *,
    analysis: Mapping[str, Any] | None,
    phase: str,
    enabled: bool,
    target: str,
    timing: str,
) -> dict[str, Any]:
    """احسب حالة ميزة واحدة في سياق اتصال/طور محدد."""
    meta = FEATURES.get(key, {})
    base = {
        "key": key,
        "name": meta.get("name", key),
        "icon": meta.get("icon", "⚙️"),
        "kind": meta.get("kind", KIND_UI),
        "enabled": enabled,
        "target": target,
        "target_label": TARGETS.get(target, target),
        "timing": timing,
        "timing_label": TIMINGS.get(timing, timing),
    }
    if not enabled:
        return {**base, "status": STATUS_DISABLED, "reason": "متوقفة — فعّلها من اللوحة."}

    encrypted = bool(analysis.get("encrypted_transport", True)) if analysis else True
    phase_label = PHASE_LABELS.get(phase, phase)

    if meta.get("kind") == KIND_DETECT:
        if _timing_ok(timing, phase):
            return {
                **base,
                "status": STATUS_ACTIVE,
                "reason": f"رصد يعمل الآن — الطور الحالي: {phase_label}.",
            }
        return {
            **base,
            "status": STATUS_WAIT_TIMING,
            "reason": f"التوقيت '{TIMINGS.get(timing, timing)}' — الطور الحالي: {phase_label}.",
        }

    if meta.get("kind") == KIND_UI:
        return {
            **base,
            "status": STATUS_UI_ONLY,
            "reason": "واجهة عرض فقط — لا تعديل على الشبكة.",
        }

    # kind == patch
    if encrypted:
        return {
            **base,
            "status": STATUS_BLOCKED_TLS,
            "reason": (
                "الاتصال TLS 1.3 مشفر؛ تعديل أي بايت في ciphertext يفشل تحقق AEAD "
                "ويقطع اللعبة فوراً. الميزة محفوظة للتطبيق على عينات Offline/مفكوكة فقط."
            ),
        }
    if target == "opponent":
        return {
            **base,
            "status": STATUS_BLOCKED_OPPONENT,
            "reason": (
                "اتصال الخصم يمر عبر جهازه هو، لا عبر بروكسيك. لا يمكن تعديل أي "
                "شيء على جهاز الخصم من هنا — السيرفر هو المرجع النهائي."
            ),
        }
    if not _timing_ok(timing, phase):
        return {
            **base,
            "status": STATUS_WAIT_TIMING,
            "reason": f"التوقيت '{TIMINGS.get(timing, timing)}' — الطور الحالي: {phase_label}.",
        }
    return {
        **base,
        "status": STATUS_APPLIED,
        "reason": "طُبّقت على عينة مفكوكة/Offline (offset تجريبي غير موثق).",
    }


def _timing_ok(timing: str, phase: str) -> bool:
    from .match_tracker import timing_active

    return timing_active(timing, phase)


def feature_statuses(
    analysis: Mapping[str, Any] | None,
    phase: str,
) -> list[dict[str, Any]]:
    """حالة كل الميزات حسب آخر اتصال والطور الحالي."""
    prefs = load_prefs()
    enabled = prefs["features"]
    targets = prefs["targets"]
    timings = prefs["timings"]
    return [
        feature_status(
            key,
            analysis=analysis,
            phase=phase,
            enabled=enabled.get(key, False),
            target=targets.get(key, "both"),
            timing=timings.get(key, "any"),
        )
        for key in FEATURES
    ]


def set_last_analysis(analysis: dict[str, Any] | None) -> None:
    global _last_analysis
    with _last_analysis_lock:
        _last_analysis = analysis


def get_last_analysis() -> dict[str, Any] | None:
    with _last_analysis_lock:
        return _last_analysis


# ---------------------------------------------------------------------------
# الإشعارات
# ---------------------------------------------------------------------------

def add_notification(msg: str, level: str = "info", **details: Any) -> dict[str, Any] | None:
    """أضف إشعاراً للوحة؛ نفس النص خلال ``NOTIFY_DEDUP_SEC`` يُهمل حتى لا
    تتكرر الإشعارات مع كل إعادة محاولة من اللعبة (كل ~ثانية)."""
    now = time.time()
    key = str(msg)
    with _notification_lock:
        last = _recent_notifications.get(key)
        if last is not None and now - last < NOTIFY_DEDUP_SEC:
            return None
        _recent_notifications[key] = now
        if len(_recent_notifications) > 200:
            cutoff = now - NOTIFY_DEDUP_SEC
            for stale in [k for k, v in _recent_notifications.items() if v < cutoff]:
                _recent_notifications.pop(stale, None)
        item: dict[str, Any] = {
            "id": uuid.uuid4().hex[:8],
            "timestamp": now,
            "time": time.strftime("%H:%M:%S", time.localtime(now)),
            "level": level,
            "msg": key,
        }
        if details:
            item["details"] = details
        notifications.append(item)
    return item


def get_notifications() -> list[dict[str, Any]]:
    with _notification_lock:
        return list(notifications)[-10:][::-1]
