import tempfile
import unittest
from pathlib import Path

from src import modmenu


class ModMenuStoreTests(unittest.TestCase):
    def setUp(self):
        self._original_file = modmenu.DATA_FILE
        self._temp_dir = tempfile.TemporaryDirectory()
        modmenu.DATA_FILE = Path(self._temp_dir.name) / "modmenu.json"

    def tearDown(self):
        modmenu.DATA_FILE = self._original_file
        self._temp_dir.cleanup()

    def test_defaults_include_every_known_feature(self):
        cfg = modmenu.load_config()
        self.assertEqual(set(cfg["features"]), set(modmenu.FEATURES))
        self.assertFalse(any(cfg["features"].values()))
        self.assertEqual(cfg["protocol"], modmenu.PROTOCOL_VERSION)

    def test_save_round_trips_and_normalizes(self):
        saved = modmenu.save_config(
            {"instant_finish": True, "auto_win": 1, "unknown": True}
        )
        self.assertTrue(saved["features"]["instant_finish"])
        self.assertFalse(saved["features"]["auto_win"])
        self.assertNotIn("unknown", saved["features"])
        self.assertEqual(modmenu.get_enabled(), ["instant_finish"])

    def test_config_payload_is_light_for_the_modified_app(self):
        modmenu.save_config({"stamina_client": True})
        payload = modmenu.config_payload()
        self.assertEqual(payload["protocol"], modmenu.PROTOCOL_VERSION)
        self.assertTrue(payload["features"]["stamina_client"])
        self.assertNotIn("defs", payload)  # لا تعريفات للوحة في صيغة الجهاز
        self.assertIn("updated_at", payload)

    def test_malformed_file_falls_back_to_defaults(self):
        modmenu.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        modmenu.DATA_FILE.write_text("not json", encoding="utf-8")
        cfg = modmenu.load_config()
        self.assertFalse(any(cfg["features"].values()))


if __name__ == "__main__":
    unittest.main()
