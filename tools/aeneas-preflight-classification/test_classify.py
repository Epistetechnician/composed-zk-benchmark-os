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


if __name__ == "__main__":
    unittest.main()
