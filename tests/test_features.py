import json
import tempfile
import unittest
from pathlib import Path

from src import features


class FeatureStoreTests(unittest.TestCase):
    def setUp(self):
        self._original_file = features.DATA_FILE
        self._temp_dir = tempfile.TemporaryDirectory()
        features.DATA_FILE = Path(self._temp_dir.name) / "features.json"
        features.notifications.clear()
        features._recent_notifications.clear()

    def tearDown(self):
        features.DATA_FILE = self._original_file
        features.notifications.clear()
        features._recent_notifications.clear()
        self._temp_dir.cleanup()

    def test_defaults_include_every_known_feature(self):
        state = features.load_features()
        self.assertEqual(set(state), set(features.FEATURES))
        self.assertFalse(any(state.values()))

    def test_save_is_normalized_and_round_trips(self):
        saved = features.save_features({"slow_ai": True, "stamina": 1})
        self.assertTrue(saved["slow_ai"])
        self.assertFalse(saved["stamina"])
        self.assertEqual(features.load_features(), saved)
        self.assertEqual(features.get_enabled(), ["slow_ai"])

    def test_malformed_file_falls_back_to_defaults(self):
        features.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        features.DATA_FILE.write_text("not json", encoding="utf-8")
        self.assertFalse(any(features.load_features().values()))

    def test_unknown_saved_keys_are_ignored(self):
        features.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        features.DATA_FILE.write_text(
            json.dumps({"slow_ai": True, "unknown": True}),
            encoding="utf-8",
        )
        state = features.load_features()
        self.assertNotIn("unknown", state)
        self.assertTrue(state["slow_ai"])

    def test_duplicate_notification_is_suppressed_within_window(self):
        # نفس الإشعار كل ثانية (إعادات محاولة اللعبة) → يظهر مرة واحدة فقط
        for _ in range(5):
            features.add_notification("🛡️ حُجب الاتصال بـ pes22-game.cs.konami.net (منع العودة بعد الإنهاء)")
        self.assertEqual(len(features.get_notifications()), 1)
        # إشعار مختلف يمرّ
        features.add_notification("⚽ تقدير المباراة: بداية")
        self.assertEqual(len(features.get_notifications()), 2)

    def test_notifications_are_bounded_and_newest_first(self):
        for number in range(25):
            features.add_notification(f"message-{number}")
        items = features.get_notifications()
        self.assertEqual(len(items), 10)
        self.assertEqual(items[0]["msg"], "message-24")
        self.assertEqual(items[-1]["msg"], "message-15")

    def test_prefs_save_and_round_trip_targets_and_timings(self):
        saved = features.save_prefs(
            features={"slow_ai": True},
            targets={"slow_ai": "opponent"},
            timings={"slow_ai": "late"},
        )
        self.assertTrue(saved["features"]["slow_ai"])
        self.assertEqual(saved["targets"]["slow_ai"], "opponent")
        self.assertEqual(saved["timings"]["slow_ai"], "late")
        prefs = features.load_prefs()
        self.assertEqual(prefs["targets"]["slow_ai"], "opponent")
        self.assertEqual(prefs["timings"]["slow_ai"], "late")

    def test_prefs_ignore_unknown_targets_and_timings(self):
        saved = features.save_prefs(
            features={"no_press": True},
            targets={"no_press": "bogus", "unknown": "me"},
            timings={"no_press": "midnight", "unknown": "late"},
        )
        self.assertEqual(saved["targets"]["no_press"], "opponent")  # القيمة الافتراضية للميزة
        self.assertEqual(saved["timings"]["no_press"], "late")
        self.assertNotIn("unknown", saved["targets"])

    def test_feature_status_blocked_on_encrypted_tunnel(self):
        status = features.feature_status(
            "slow_ai",
            analysis={"encrypted_transport": True},
            phase="first_half",
            enabled=True,
            target="me",
            timing="late",
        )
        self.assertEqual(status["status"], features.STATUS_BLOCKED_TLS)
        self.assertIn("TLS", status["reason"])

    def test_feature_status_opponent_is_unreachable_even_decoded(self):
        status = features.feature_status(
            "ai_miss",
            analysis={"encrypted_transport": False},
            phase="second_half",
            enabled=True,
            target="opponent",
            timing="late",
        )
        self.assertEqual(status["status"], features.STATUS_BLOCKED_OPPONENT)

    def test_detect_feature_active_by_timing_window(self):
        # متأخر: غير مفعل في الشوط الأول
        status = features.feature_status(
            "match_end_alert",
            analysis={"encrypted_transport": True},
            phase="first_half",
            enabled=True,
            target="both",
            timing="late",
        )
        self.assertEqual(status["status"], features.STATUS_WAIT_TIMING)
        # مفعل في الشوط الثاني
        status = features.feature_status(
            "match_end_alert",
            analysis={"encrypted_transport": True},
            phase="second_half",
            enabled=True,
            target="both",
            timing="late",
        )
        self.assertEqual(status["status"], features.STATUS_ACTIVE)

    def test_disabled_feature_reports_disabled(self):
        status = features.feature_status(
            "server_ping",
            analysis=None,
            phase="second_half",
            enabled=False,
            target="both",
            timing="any",
        )
        self.assertEqual(status["status"], features.STATUS_DISABLED)


if __name__ == "__main__":
    unittest.main()
