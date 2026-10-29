import pathlib
import unittest

import classify

DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs"


class T(unittest.TestCase):
    def test_every_stop_doc_is_classified(self):
        res = classify.collect(DOCS)
        self.assertGreaterEqual(len(res), 40)
        self.assertNotIn("unclassified", res.values())

    def test_known_examples(self):
        self.assertEqual(classify.classify("669-phase-aeneas-driver-link-failure.md"), "toolchain")
        self.assertEqual(classify.classify("717-acquisition-provenance-stop.md"), "provenance")
        self.assertEqual(classify.classify("721-primary-worktree-stop.md"), "ordering")

    def test_retry_result_documented(self):
        doc = (DOCS / "aeneas-one-shot-extraction-attempt-and-stop-classification.md").read_text()
        self.assertIn("## Retry result (extraction succeeded)", doc)
        self.assertIn("Level1LocalReplayOrLower", doc)


if __name__ == "__main__":
    unittest.main()
