import tempfile
import unittest
from pathlib import Path

from src import netctl


class DummyWriter:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class NetCtlTests(unittest.TestCase):
    def setUp(self):
        self._original_file = netctl.DATA_FILE
        self._temp_dir = tempfile.TemporaryDirectory()
        netctl.DATA_FILE = Path(self._temp_dir.name) / "netctl.json"
        netctl._sessions.clear()
        netctl._actions.clear()
        netctl._settings = {
            "throttle_kbps": 0,
            "block_hosts": [],
            "result_guard": False,
        }

    def tearDown(self):
        netctl.DATA_FILE = self._original_file
        netctl._sessions.clear()
        netctl._actions.clear()
        self._temp_dir.cleanup()

    def test_defaults_are_safe(self):
        settings = netctl.load_settings()
        self.assertEqual(settings["throttle_kbps"], 0)
        self.assertEqual(settings["block_hosts"], [])
        self.assertFalse(settings["result_guard"])

    def test_save_normalizes_and_round_trips(self):
        saved = netctl.save_settings(
            {
                "throttle_kbps": "64",
                "block_hosts": ["Konami.net", ".konami.com", "", "konami.net"],
                "result_guard": True,
            }
        )
        self.assertEqual(saved["throttle_kbps"], 64)
        self.assertEqual(saved["block_hosts"], ["konami.net", "konami.com"])
        self.assertTrue(saved["result_guard"])
        self.assertEqual(netctl.load_settings()["throttle_kbps"], 64)

    def test_save_rejects_negative_and_oversize_throttle(self):
        saved = netctl.save_settings({"throttle_kbps": -5})
        self.assertEqual(saved["throttle_kbps"], 0)
        saved = netctl.save_settings({"throttle_kbps": 999_999_999})
        self.assertEqual(saved["throttle_kbps"], 200_000)

    def test_blocklist_suffix_matching(self):
        netctl.save_settings({"block_hosts": ["konami.net"]})
        self.assertTrue(netctl.should_block("pes22-game.cs.konami.net"))
        self.assertTrue(netctl.should_block("konami.net"))
        self.assertTrue(netctl.should_block("konami.net:443"))
        self.assertFalse(netctl.should_block("konami.net.evil.org"))
        self.assertFalse(netctl.should_block("notkonami.net"))
        self.assertFalse(netctl.should_block(""))

    def test_register_kill_and_abort(self):
        writer = DummyWriter()
        sid = netctl.register_session(writer, None, "pes22-game.cs.konami.net", 443)
        self.assertFalse(netctl.should_abort(sid))
        self.assertEqual(len(netctl.active_sessions()), 1)

        killed = netctl.kill_all("test")
        self.assertEqual(killed, 1)
        self.assertTrue(netctl.should_abort(sid))
        netctl.unregister_session(sid)
        self.assertEqual(len(netctl.active_sessions()), 0)
        # بدون loop لا نستدعي close — العلم يكفي لإنهاء حلقة النقل
        self.assertFalse(writer.closed)

    def test_kill_with_loop_closes_writer(self):
        import threading

        def fake_schedule(callback):
            callback()

        class FakeLoop:
            def call_soon_threadsafe(self, callback):
                fake_schedule(callback)

        writer = DummyWriter()
        sid = netctl.register_session(writer, FakeLoop(), "host", 443)
        netctl.kill_all("test")
        self.assertTrue(writer.closed)
        netctl.unregister_session(sid)

    def test_actions_are_bounded_and_newest_first(self):
        for number in range(25):
            netctl.record_action(f"action-{number}")
        actions = netctl.get_actions()
        self.assertEqual(len(actions), 10)
        self.assertEqual(actions[0]["msg"], "action-24")


if __name__ == "__main__":
    unittest.main()
