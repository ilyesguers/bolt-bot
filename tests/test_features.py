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

    def tearDown(self):
        features.DATA_FILE = self._original_file
        features.notifications.clear()
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

    def test_notifications_are_bounded_and_newest_first(self):
        for number in range(25):
            features.add_notification(f"message-{number}")
        items = features.get_notifications()
        self.assertEqual(len(items), 10)
        self.assertEqual(items[0]["msg"], "message-24")
        self.assertEqual(items[-1]["msg"], "message-15")


if __name__ == "__main__":
    unittest.main()
