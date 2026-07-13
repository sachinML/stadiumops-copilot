import unittest
from pathlib import Path

from copilot.data import load_kb


class TestRag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index, cls.chunks = load_kb(Path(__file__).parent.parent / "data")

    def test_search_returns_relevant_chunks(self):
        results = self.index.search("step-free elevator accessibility", k=3)
        self.assertTrue(results)
        top_chunk = results[0][0]
        self.assertIn("accessibility", top_chunk.doc_id.lower() + " " + top_chunk.title.lower() + " " + top_chunk.text.lower())


if __name__ == "__main__":
    unittest.main()

