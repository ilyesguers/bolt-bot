"""تقدير أطوار المباراة من شكل الترافيق — Match Phase Estimator (v5.2).

اتصال ``CONNECT`` نفق TLS معتم، لذلك لا نرى قرارات اللعبة ولا نتائجها.
هذا الموديول يبني "صورة تقديرية" لسير المباراة من إشارات كمية فقط:
عدد اتصالات خادم AI، أحجام الدفعات، الفجوات الزمنية بينها.

كل نتيجة هنا تحمل وصف "تقدير" — ليست قراءة بروتوكول KONAMI موثقة.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

# أطوار المباراة المفترضة
PHASE_IDLE = "idle"
PHASE_KICKOFF = "kickoff"
PHASE_FIRST_HALF = "first_half"
PHASE_HALFTIME = "halftime"
PHASE_SECOND_HALF = "second_half"
PHASE_FULL_TIME = "full_time"

PHASES = [
    PHASE_IDLE,
    PHASE_KICKOFF,
    PHASE_FIRST_HALF,
    PHASE_HALFTIME,
    PHASE_SECOND_HALF,
    PHASE_FULL_TIME,
]

PHASE_LABELS: dict[str, str] = {
    PHASE_IDLE: "لا مباراة بعد",
    PHASE_KICKOFF: "بداية المباراة (تقدير)",
    PHASE_FIRST_HALF: "الشوط الأول (تقدير)",
    PHASE_HALFTIME: "الاستراحة (تقدير)",
    PHASE_SECOND_HALF: "الشوط الثاني (تقدير)",
    PHASE_FULL_TIME: "انتهت المباراة (تقدير)",
}

# معاملات التقدير (ثوانٍ/بايت) — قابلة للتعديل
NEW_SESSION_GAP = 90.0     # فجوة بين اتصالات AI ≥ 90 ثانية = مباراة جديدة
GAP_HALFTIME = 45.0        # فجوة ≥ 45 ثانية داخل شوط = استراحة
LONG_MATCH_SECONDS = 420.0 # مباراة تتجاوز 7 دقائق = قاربت على النهاية
FIRST_HALF_BURST = 5000    # دفعة بيانات مباراة ≥ 5KB = بدء الشوط الأول
END_BURST = 8000           # دفعة كبيرة ≥ 8KB في الشوط الثاني = إشارة نهاية


class MatchTracker:
    """تتبع تقديري لأطوار المباراة عبر اتصالات خادم AI."""

    def __init__(self, now=None) -> None:
        self._lock = threading.Lock()
        self._now = now or time.time
        self.phase = PHASE_IDLE
        self.phase_since: float | None = None
        self.session_start: float | None = None
        self.connections = 0
        self.server_bytes = 0
        self.client_bytes = 0
        self.last_activity: float | None = None
        self.timeline: deque[dict[str, Any]] = deque(maxlen=20)
        self._active = 0
        self._last_conn_server = 0
        self._last_conn_client = 0

    # -- helpers ---------------------------------------------------------
    def _add_event(self, phase: str) -> dict[str, Any]:
        event = {
            "phase": phase,
            "label": PHASE_LABELS[phase],
            "timestamp": self._now(),
            "connections": self.connections,
        }
        self.timeline.append(event)
        return event

    # -- lifecycle hooks -------------------------------------------------
    def connection_start(self, host: str) -> list[dict[str, Any]]:
        """يُستدعى عند فتح اتصال CONNECT لخادم AI. يعيد أحداث طور جديدة."""
        now = self._now()
        events: list[dict[str, Any]] = []
        with self._lock:
            gap = (now - self.last_activity) if self.last_activity is not None else None
            fresh_session = self._active == 0 and (
                self.last_activity is None or gap >= NEW_SESSION_GAP
            )
            if fresh_session:
                # مباراة/جلسة جديدة
                self.phase = PHASE_KICKOFF
                self.phase_since = now
                self.session_start = now
                self.connections = 0
                self.server_bytes = 0
                self.client_bytes = 0
                self._last_conn_server = 0
                self._last_conn_client = 0
                events.append(self._add_event(PHASE_KICKOFF))
            elif self.phase == PHASE_HALFTIME:
                # انتهت الاستراحة وعاد اللعب
                self.phase = PHASE_SECOND_HALF
                self.phase_since = now
                events.append(self._add_event(PHASE_SECOND_HALF))
            elif (
                self._active == 0
                and gap is not None
                and gap >= GAP_HALFTIME
                and self.phase in (PHASE_KICKOFF, PHASE_FIRST_HALF)
            ):
                # فجوة صمت ≥ 45 ثانية أثناء الشوط الأول = استراحة (تقدير)،
                # والاتصال الحالي يمثل العودة للعب = الشوط الثاني.
                self.phase = PHASE_HALFTIME
                self.phase_since = now
                events.append(self._add_event(PHASE_HALFTIME))
                self.phase = PHASE_SECOND_HALF
                self.phase_since = now
                events.append(self._add_event(PHASE_SECOND_HALF))

            self._active += 1
            self.connections += 1
            self.last_activity = now
            self._last_conn_server = 0
            self._last_conn_client = 0
        return events

    def chunk(self, direction: str, size: int) -> list[dict[str, Any]]:
        """يُستدعى لكل دفعة أثناء النقل. يعيد أحداث طور جديدة."""
        now = self._now()
        events: list[dict[str, Any]] = []
        with self._lock:
            if self.phase in (PHASE_IDLE, PHASE_FULL_TIME):
                return events
            if direction == "client_to_server":
                self.client_bytes += size
                self._last_conn_client += size
            else:
                self.server_bytes += size
                self._last_conn_server += size
            self.last_activity = now

            if self.phase == PHASE_KICKOFF and self.server_bytes >= FIRST_HALF_BURST:
                self.phase = PHASE_FIRST_HALF
                self.phase_since = now
                events.append(self._add_event(PHASE_FIRST_HALF))
        return events

    def connection_end(self, host: str) -> list[dict[str, Any]]:
        """يُستدعى عند إغلاق الاتصال. يعيد أحداث طور جديدة."""
        now = self._now()
        events: list[dict[str, Any]] = []
        with self._lock:
            self._active = max(0, self._active - 1)
            gap = (now - self.last_activity) if self.last_activity is not None else 0.0
            self.last_activity = now

            if self._active != 0:
                return events

            session_age = (
                (now - self.session_start) if self.session_start is not None else 0.0
            )

            if self.phase in (PHASE_KICKOFF, PHASE_FIRST_HALF):
                if gap >= GAP_HALFTIME:
                    self.phase = PHASE_HALFTIME
                    self.phase_since = now
                    events.append(self._add_event(PHASE_HALFTIME))
            elif self.phase == PHASE_SECOND_HALF:
                if (
                    session_age >= LONG_MATCH_SECONDS
                    or self._last_conn_server >= END_BURST
                ):
                    self.phase = PHASE_FULL_TIME
                    self.phase_since = now
                    events.append(self._add_event(PHASE_FULL_TIME))
        return events

    # -- read ------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "phase": self.phase,
                "phase_label": PHASE_LABELS.get(self.phase, self.phase),
                "phase_since": self.phase_since,
                "phase_seconds": (
                    round(self._now() - self.phase_since, 1)
                    if self.phase_since is not None
                    else 0
                ),
                "session_start": self.session_start,
                "session_seconds": (
                    round(self._now() - self.session_start, 1)
                    if self.session_start is not None
                    else 0
                ),
                "connections": self.connections,
                "server_bytes": self.server_bytes,
                "client_bytes": self.client_bytes,
                "active_connections": self._active,
                "last_activity": self.last_activity,
                "timeline": list(self.timeline)[-8:][::-1],
                "heuristic": True,
                "note": (
                    "تقدير مبني على حجم الترافيك والفجوات الزمنية فقط — "
                    "ليست قراءة لبروتوكول KONAMI."
                ),
            }


tracker = MatchTracker()


def timing_active(timing: str, phase: str) -> bool:
    """هل نافذة التفعيل الزمنية للميزة مفتوحة في الطور الحالي؟

    ``any``: نشط منذ بداية المباراة وحتى النهاية (ليس idle).
    ``early``: نشط في البداية والشوط الأول فقط.
    ``late``: نشط من الشوط الثاني فصاعداً (متأخر — كما طُلب).
    """
    if phase == PHASE_IDLE:
        return False
    if timing == "any":
        return True
    if timing == "early":
        return phase in (PHASE_KICKOFF, PHASE_FIRST_HALF)
    if timing == "late":
        return phase in (PHASE_SECOND_HALF, PHASE_FULL_TIME)
    return False
