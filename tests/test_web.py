import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src import features, modmenu, netctl
from src.web import app


class FeatureAPITests(unittest.TestCase):
    def setUp(self):
        self._original_file = features.DATA_FILE
        self._original_modmenu = modmenu.DATA_FILE
        self._original_netctl = netctl.DATA_FILE
        self._temp_dir = tempfile.TemporaryDirectory()
        features.DATA_FILE = Path(self._temp_dir.name) / "features.json"
        modmenu.DATA_FILE = Path(self._temp_dir.name) / "modmenu.json"
        netctl.DATA_FILE = Path(self._temp_dir.name) / "netctl.json"
        netctl._settings = {"throttle_kbps": 0, "block_hosts": [], "result_guard": False}
        netctl._sessions.clear()
        netctl._actions.clear()
        netctl._recent_actions.clear()
        netctl._temp_blocks.clear()
        features.notifications.clear()
        features._recent_notifications.clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        features.DATA_FILE = self._original_file
        modmenu.DATA_FILE = self._original_modmenu
        netctl.DATA_FILE = self._original_netctl
        netctl._sessions.clear()
        netctl._actions.clear()
        netctl._recent_actions.clear()
        netctl._temp_blocks.clear()
        features.notifications.clear()
        features._recent_notifications.clear()
        self._temp_dir.cleanup()

    def test_get_and_post_features(self):
        initial = self.client.get("/api/features")
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(len(initial.json()["features"]), 9)
        self.assertFalse(initial.json()["can_modify_tls"])

        updated = self.client.post(
            "/api/features",
            json={"features": {"slow_ai": True, "show_ai": True}},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["enabled"], ["slow_ai", "show_ai"])

        persisted = self.client.get("/api/features").json()["state"]
        self.assertTrue(persisted["slow_ai"])
        self.assertTrue(persisted["show_ai"])
        self.assertFalse(persisted["stamina"])

    def test_feature_api_rejects_unknown_and_non_boolean_values(self):
        unknown = self.client.post("/api/features", json={"unknown": True})
        self.assertEqual(unknown.status_code, 422)

        invalid = self.client.post("/api/features", json={"slow_ai": 1})
        self.assertEqual(invalid.status_code, 422)

    def test_save_adds_notification(self):
        self.client.post("/api/features", json={"slow_ai": True})
        response = self.client.get("/api/notifications")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["count"], 1)
        self.assertIn("تم حفظ", response.json()["notifications"][0]["msg"])

    def test_dashboard_contains_ai_controls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("🎮 ميزات الرصد", response.text)
        self.assertEqual(response.text.count('class="ai-checkbox"'), 9)

    def test_post_accepts_targets_and_timings(self):
        updated = self.client.post(
            "/api/features",
            json={
                "features": {"slow_ai": True},
                "targets": {"slow_ai": "opponent"},
                "timings": {"slow_ai": "late"},
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["targets"]["slow_ai"], "opponent")
        self.assertEqual(updated.json()["timings"]["slow_ai"], "late")

        rejected = self.client.post(
            "/api/features",
            json={"features": {"slow_ai": True}, "targets": {"slow_ai": "bogus"}},
        )
        self.assertEqual(rejected.status_code, 422)

    def test_match_endpoint_reports_phase_and_statuses(self):
        response = self.client.get("/api/match")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["match"]["phase"], "idle")
        self.assertTrue(body["match"]["heuristic"])
        self.assertEqual(len(body["statuses"]), 9)

    def test_modmenu_get_post_and_light_config(self):
        initial = self.client.get("/api/modmenu")
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(len(initial.json()["features"]), 6)
        self.assertFalse(any(initial.json()["state"].values()))

        updated = self.client.post(
            "/api/modmenu",
            json={"features": {"instant_finish": True, "slow_ai_client": True}},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(
            updated.json()["enabled"], ["instant_finish", "slow_ai_client"]
        )

        light = self.client.get("/api/modmenu/config").json()
        self.assertEqual(light["protocol"], 1)
        self.assertTrue(light["features"]["instant_finish"])

        rejected = self.client.post("/api/modmenu", json={"bogus": True})
        self.assertEqual(rejected.status_code, 422)

    def test_netctl_get_post_and_kill(self):
        initial = self.client.get("/api/netctl")
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(initial.json()["settings"]["throttle_kbps"], 0)
        self.assertEqual(initial.json()["mode"], "proxy_only")

        updated = self.client.post(
            "/api/netctl",
            json={"settings": {"throttle_kbps": 32, "block_hosts": ["konami.net"], "result_guard": True}},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["settings"]["throttle_kbps"], 32)
        self.assertTrue(updated.json()["settings"]["result_guard"])

        rejected = self.client.post(
            "/api/netctl", json={"settings": {"throttle_kbps": -1}}
        )
        self.assertEqual(rejected.status_code, 422)

        rejected = self.client.post(
            "/api/netctl", json={"settings": {"block_hosts": "not-a-list"}}
        )
        self.assertEqual(rejected.status_code, 422)

        kill = self.client.post("/api/netctl/kill")
        self.assertEqual(kill.status_code, 200)
        self.assertIn("killed", kill.json())

    def test_menu_endpoint_lists_features_and_settings(self):
        response = self.client.get("/menu")
        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertIn("eFootball Proxy Menu", text)
        self.assertIn("مانع المطابقة", text)
        self.assertIn("مؤقّت المباراة", text)
        self.assertIn("إنهاء المباراة", text)
        self.assertIn("/api/netctl", text)

    def test_netctl_new_settings_validation(self):
        ok = self.client.post(
            "/api/netctl",
            json={"settings": {"block_matchmaking": True, "auto_finish_sec": 90, "jitter_ms": 300, "result_guard_scope": "all"}},
        )
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["settings"]["block_matchmaking"])
        self.assertEqual(ok.json()["settings"]["auto_finish_sec"], 90)

        bad = self.client.post("/api/netctl", json={"settings": {"auto_finish_sec": -1}})
        self.assertEqual(bad.status_code, 422)
        bad = self.client.post("/api/netctl", json={"settings": {"jitter_ms": 5000}})
        self.assertEqual(bad.status_code, 422)
        bad = self.client.post("/api/netctl", json={"settings": {"result_guard_scope": "bogus"}})
        self.assertEqual(bad.status_code, 422)

    def test_finish_match_endpoint(self):
        result = self.client.post(
            "/api/netctl/finish", json={"cooldown_sec": 60}
        )
        self.assertEqual(result.status_code, 200)
        body = result.json()
        self.assertIn("killed", body)
        self.assertEqual(body["cooldown_sec"], 60)
        self.assertIn("pes22-game.cs.konami.net", body["blocked_hosts"])
        self.assertEqual(len(body["temp_blocks"]), 1)
        # الآن الاتصال بخادم AI ممنوع (403) أثناء الكولداون
        blocked = self.client.post(
            "/api/netctl/finish", json={"cooldown_sec": 99999}
        )
        self.assertEqual(blocked.status_code, 422)
        invalid = self.client.post("/api/netctl/finish", json={"cooldown_sec": "x"})
        self.assertEqual(invalid.status_code, 422)

        # تنظيف الكولداون حتى لا يؤثر على بقية الاختبارات
        from src import netctl
        netctl._temp_blocks.clear()

    def test_dashboard_contains_network_controls(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("🎛️ تحكم الشبكة", response.text)
        self.assertIn('id="throttleInput"', response.text)
        self.assertIn('id="blockHostsInput"', response.text)
        self.assertIn('id="resultGuardInput"', response.text)


if __name__ == "__main__":
    unittest.main()
