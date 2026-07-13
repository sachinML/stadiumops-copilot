import unittest
from datetime import datetime, timezone

from copilot.telemetry import snapshot


class TestTelemetry(unittest.TestCase):
    def test_snapshot_shape_and_ranges(self):
        s = snapshot(datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc))
        self.assertIn("ts", s)
        self.assertIn("gates", s)
        self.assertIsInstance(s["gates"], list)
        self.assertGreaterEqual(len(s["gates"]), 4)

        for g in s["gates"]:
            self.assertGreaterEqual(g["density"], 0.0)
            self.assertLessEqual(g["density"], 1.0)
            self.assertGreaterEqual(g["risk"], 0.0)
            self.assertLessEqual(g["risk"], 1.0)
            self.assertGreaterEqual(g["queue_min"], 0)
            self.assertGreaterEqual(g["accessible_queue_min"], 0)


if __name__ == "__main__":
    unittest.main()

