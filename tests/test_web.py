import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src import features
from src.web import app


class FeatureAPITests(unittest.TestCase):
    def setUp(self):
        self._original_file = features.DATA_FILE
        self._temp_dir = tempfile.TemporaryDirectory()
        features.DATA_FILE = Path(self._temp_dir.name) / "features.json"
        features.notifications.clear()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        features.DATA_FILE = self._original_file
        features.notifications.clear()
        self._temp_dir.cleanup()

    def test_get_and_post_features(self):
        initial = self.client.get("/api/features")
        self.assertEqual(initial.status_code, 200)
        self.assertEqual(len(initial.json()["features"]), 5)
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
        self.assertEqual(response.text.count('class="ai-checkbox"'), 5)


if __name__ == "__main__":
    unittest.main()
