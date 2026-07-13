import unittest
from pathlib import Path

from copilot.routing import load_stadium_map, shortest_path


class TestRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.smap = load_stadium_map(Path(__file__).parent.parent / "data")

    def test_accessible_route_avoids_stairs(self):
        # East concourse to Section 120 has both stairs and step-free options.
        path_accessible, minutes_accessible = shortest_path(
            self.smap, start="CONCOURSE_E", goal="SECTION_120", require_accessible=True
        )
        path_non_acc, minutes_non_acc = shortest_path(
            self.smap, start="CONCOURSE_E", goal="SECTION_120", require_accessible=False
        )

        self.assertTrue(path_accessible)
        self.assertTrue(path_non_acc)
        self.assertNotIn("STAIRS_CORE", path_accessible)
        self.assertIn("ELEVATOR_CORE", path_accessible)
        self.assertLessEqual(minutes_accessible, minutes_non_acc + 10)  # shouldn't be wildly worse

    def test_unknown_nodes_returns_inf(self):
        path, minutes = shortest_path(self.smap, start="NOPE", goal="SECTION_120", require_accessible=True)
        self.assertEqual(path, [])
        self.assertEqual(minutes, float("inf"))


if __name__ == "__main__":
    unittest.main()

