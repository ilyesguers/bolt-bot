import unittest

from src.match_tracker import (
    MatchTracker,
    MODE_OFFLINE,
    MODE_ONLINE,
    MODE_UNKNOWN,
    PHASE_FIRST_HALF,
    PHASE_FULL_TIME,
    PHASE_HALFTIME,
    PHASE_IDLE,
    PHASE_KICKOFF,
    PHASE_SECOND_HALF,
    timing_active,
)


class FakeClock:
    """ساعة قابلة للدفع يدوياً لاختبار التقديرات الزمنية."""

    def __init__(self):
        self.t = 1000.0

    def advance(self, seconds):
        self.t += seconds

    def __call__(self):
        return self.t


class MatchTrackerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.tracker = MatchTracker(now=self.clock)

    def test_connection_opens_a_kickoff_phase(self):
        events = self.tracker.connection_start("pes22-game.cs.konami.net")
        self.assertEqual([e["phase"] for e in events], [PHASE_KICKOFF])
        self.assertEqual(self.tracker.snapshot()["phase"], PHASE_KICKOFF)

    def test_burst_promotes_to_first_half(self):
        self.tracker.connection_start("host")
        self.tracker.connection_end("host")
        events = self.tracker.chunk("server_to_client", 6000)
        self.assertEqual([e["phase"] for e in events], [PHASE_FIRST_HALF])
        snap = self.tracker.snapshot()
        self.assertEqual(snap["phase"], PHASE_FIRST_HALF)
        self.assertEqual(snap["server_bytes"], 6000)

    def test_gap_during_first_half_is_halftime(self):
        self.tracker.connection_start("host")
        self.tracker.chunk("server_to_client", 6000)
        self.clock.advance(20)
        self.tracker.connection_end("host")

        # فجوة صمت أثناء الاتصال الثاني = استراحة عند إنهائه
        self.tracker.connection_start("host")
        self.clock.advance(60)
        events = self.tracker.connection_end("host")
        phases = [e["phase"] for e in events if e["kind"] == "phase"]
        self.assertEqual(phases, [PHASE_HALFTIME])

    def test_gap_after_first_half_moves_to_second_half_on_resume(self):
        self.tracker.connection_start("host")
        self.tracker.chunk("server_to_client", 6000)
        self.clock.advance(30)
        self.tracker.connection_end("host")

        # فجوة صمت ≥ 45 ثانية = استراحة، والاتصال العائد = الشوط الثاني
        self.clock.advance(50)
        events = self.tracker.connection_start("host")
        self.assertEqual([e["phase"] for e in events], [PHASE_HALFTIME, PHASE_SECOND_HALF])
        self.assertEqual(self.tracker.snapshot()["phase"], PHASE_SECOND_HALF)

    def test_resume_after_halftime_starts_second_half(self):
        self.tracker.connection_start("host")
        self.tracker.chunk("server_to_client", 6000)
        self.clock.advance(20)
        self.tracker.connection_end("host")

        # فجوة أثناء الشوط الأول = استراحة (تُكتشف عند إنهاء اتصال بعد صمت)
        self.tracker.connection_start("host")
        self.clock.advance(60)
        self.tracker.connection_end("host")
        self.assertEqual(self.tracker.snapshot()["phase"], PHASE_HALFTIME)

        # عودة اللعب بعد الاستراحة = الشوط الثاني
        self.clock.advance(10)
        events = self.tracker.connection_start("host")
        self.assertEqual([e["phase"] for e in events], [PHASE_SECOND_HALF])

    def test_long_session_in_second_half_reaches_full_time(self):
        self.tracker.connection_start("host")
        self.tracker.chunk("server_to_client", 6000)
        self.clock.advance(30)
        self.tracker.connection_end("host")

        # فجوة → استراحة + شوط ثاني
        self.clock.advance(50)
        self.tracker.connection_start("host")
        self.clock.advance(5)
        self.tracker.connection_end("host")
        self.assertEqual(self.tracker.snapshot()["phase"], PHASE_SECOND_HALF)

        # نُبقي المباراة نشطة بفجوات قصيرة حتى يتجاوز عمرها 7 دقائق → النهاية
        reached_full_time = False
        for _ in range(16):
            self.tracker.connection_start("host")
            self.clock.advance(15)
            self.tracker.chunk("server_to_client", 200)
            self.clock.advance(10)
            self.tracker.connection_end("host")
            if self.tracker.snapshot()["phase"] == PHASE_FULL_TIME:
                reached_full_time = True
                break
        self.assertTrue(reached_full_time)
        self.assertEqual(self.tracker.snapshot()["phase"], PHASE_FULL_TIME)

    def test_idle_gap_opens_a_new_session(self):
        self.tracker.connection_start("host")
        self.clock.advance(30)
        self.tracker.connection_end("host")
        self.clock.advance(120)  # فجوة طويلة = مباراة جديدة
        events = self.tracker.connection_start("host")
        self.assertEqual([e["phase"] for e in events], [PHASE_KICKOFF])
        self.assertEqual(self.tracker.snapshot()["connections"], 1)

    def test_snapshot_is_heuristic_and_labeled(self):
        snap = self.tracker.snapshot()
        self.assertTrue(snap["heuristic"])
        self.assertIn("تقدير", snap["note"])
        self.assertEqual(snap["phase"], PHASE_IDLE)

    def test_sparse_session_is_classified_offline_ai(self):
        # جلسة طويلة بحركة قليلة (مزامنة فقط) = مباراة آفلان ضد AI
        self.tracker.connection_start("host")
        self.clock.advance(30)
        self.tracker.chunk("server_to_client", 3000)
        self.clock.advance(30)
        self.tracker.chunk("client_to_server", 800)
        self.clock.advance(30)
        events = self.tracker.connection_end("host")
        self.assertEqual(self.tracker.snapshot()["mode"], MODE_OFFLINE)
        self.assertIn("آفلان", self.tracker.snapshot()["mode_label"])
        self.assertTrue(any(e.get("kind") == "mode" for e in events))

    def test_heavy_session_is_classified_online(self):
        self.tracker.connection_start("host")
        for _ in range(10):
            self.tracker.chunk("server_to_client", 40_000)
            self.clock.advance(2)
        events = self.tracker.connection_end("host")
        self.assertEqual(self.tracker.snapshot()["mode"], MODE_ONLINE)
        self.assertTrue(any(e.get("kind") == "mode" for e in events))

    def test_empty_short_session_is_unknown(self):
        self.tracker.connection_start("host")
        self.clock.advance(10)
        events = self.tracker.connection_end("host")
        self.assertEqual(self.tracker.snapshot()["mode"], MODE_UNKNOWN)
        self.assertEqual(events, [])  # لا أحداث نمط لجلسة بلا بيانات


class TimingGateTests(unittest.TestCase):
    def test_any_is_active_outside_idle(self):
        self.assertFalse(timing_active("any", PHASE_IDLE))
        self.assertTrue(timing_active("any", PHASE_KICKOFF))
        self.assertTrue(timing_active("any", PHASE_FULL_TIME))

    def test_early_only_until_first_half(self):
        self.assertTrue(timing_active("early", PHASE_KICKOFF))
        self.assertTrue(timing_active("early", PHASE_FIRST_HALF))
        self.assertFalse(timing_active("early", PHASE_SECOND_HALF))
        self.assertFalse(timing_active("early", PHASE_FULL_TIME))

    def test_late_from_second_half(self):
        self.assertFalse(timing_active("late", PHASE_KICKOFF))
        self.assertFalse(timing_active("late", PHASE_FIRST_HALF))
        self.assertTrue(timing_active("late", PHASE_SECOND_HALF))
        self.assertTrue(timing_active("late", PHASE_FULL_TIME))


if __name__ == "__main__":
    unittest.main()
