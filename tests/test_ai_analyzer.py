import unittest

from src.ai_analyzer import (
    AIConnectionAnalyzer,
    analyze_ai_payload,
    calculate_entropy,
    is_ai_file,
    looks_like_tls_record,
    modify_ai_payload,
)


class AIAnalyzerTests(unittest.TestCase):
    def test_host_matching_is_normalized_and_not_substring_based(self):
        self.assertTrue(is_ai_file("pes22-game.cs.konami.net:443"))
        self.assertTrue(is_ai_file("edge.pes22-game.cs.konami.net"))
        self.assertFalse(is_ai_file("pes22-game.cs.konami.net.example.org"))
        self.assertFalse(is_ai_file("not-konami.net"))

    def test_entropy_is_bounded_and_handles_empty_payload(self):
        self.assertEqual(calculate_entropy(b""), 0.0)
        self.assertEqual(calculate_entropy(b"a" * 2048), 0.0)
        self.assertEqual(calculate_entropy(bytes(range(256)) * 4), 8.0)

    def test_tls_record_detection(self):
        self.assertTrue(looks_like_tls_record(b"\x17\x03\x03\x00\x10" + b"x" * 16))
        self.assertFalse(looks_like_tls_record(b"plain text"))

    def test_analyze_marks_connect_transport_as_not_modifiable(self):
        result = analyze_ai_payload(
            bytes(range(256)) * 8,
            "pes22-game.cs.konami.net",
            encrypted_transport=True,
        )
        self.assertTrue(result["is_ai"])
        self.assertTrue(result["encrypted_transport"])
        self.assertFalse(result["can_modify"])
        self.assertFalse(result["needs_modify"])
        self.assertTrue(result["heuristic"])

    def test_experimental_offsets_apply_only_when_requested_and_in_range(self):
        original = bytes(100)
        modified, applied = modify_ai_payload(
            original,
            ["slow_ai", "show_ai", "no_press", "ai_miss", "stamina"],
        )
        self.assertEqual(modified[42], 0x32)
        self.assertEqual(modified[55], 0x0A)
        self.assertEqual(modified[68], 0xFF)
        self.assertEqual(modified[75], 0x00)
        self.assertEqual(applied, ["slow_ai", "no_press", "ai_miss", "stamina"])

    def test_connect_analyzer_is_byte_for_byte_passthrough(self):
        tracker = AIConnectionAnalyzer(
            "pes22-game.cs.konami.net",
            ["slow_ai", "stamina"],
            encrypted_tunnel=True,
        )
        client = b"client" * 20
        server = bytes(range(100))
        self.assertEqual(tracker.process(client, "client_to_server"), client)
        self.assertEqual(tracker.process(server, "server_to_client"), server)
        result = tracker.result()
        self.assertEqual(result["client_bytes"], len(client))
        self.assertEqual(result["server_bytes"], len(server))
        self.assertEqual(result["applied_features"], [])
        self.assertEqual(result["mode"], "metadata_only")


if __name__ == "__main__":
    unittest.main()
