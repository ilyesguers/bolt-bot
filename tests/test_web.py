import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src import features, modmenu
from src.web import app


class FeatureAPITests(unittest.TestCase):
    def setUp(self):
        self._original_file = features.DATA_FILE
        self._original_modmenu = modmenu.DATA_FILE
        self._temp_dir = tempfile.TemporaryDirectory()
        features.DATA_FILE = Path(self._temp_dir.name) / "features.json"
        modmenu.DATA_FILE = Path(self._temp_dir.name) / "modmenu.json"
        features.notifications.clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        features.DATA_FILE = self._original_file
        modmenu.DATA_FILE = self._original_modmenu
        features.notifications.clear()
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
        self.assertIn("🎮 ميزات AI", response.text)
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

    def test_dashboard_contains_modmenu_panel(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("🛠️ مود مينو", response.text)
        self.assertEqual(response.text.count('class="modmenu-checkbox"'), 6)


if __name__ == "__main__":
    unittest.main()
