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

    def test_diagnostic_overrides_filename(self):
        # filename says "ordering"/"sandbox" but the stated diagnostic is a provenance gap
        txt = "# x\n\nDiagnostic: `MissingCommandCheckpoint`.\n"
        self.assertEqual(classify.classify_doc("721-sandbox-order-stop.md", txt)[0], "provenance")

    def test_unmapped_diagnostic_not_silently_filed(self):
        txt = "Diagnostic: `SomeNewUnknownThing`.\n"
        cat, ev = classify.classify_doc("669-phase-aeneas-driver-link-failure.md", txt)
        self.assertEqual(cat, "unclassified")
        self.assertIn("diagnostic-unmapped", ev)

    def test_every_doc_has_evidence_not_just_filename(self):
        det = classify.collect_detailed(DOCS)
        filename_only = [k for k, (_, ev) in det.items() if ev == "filename"]
        self.assertLessEqual(len(filename_only), 5, filename_only)

    def test_retry_result_documented(self):
        doc = (DOCS / "aeneas-one-shot-extraction-attempt-and-stop-classification.md").read_text()
        self.assertIn("## Retry result (extraction succeeded)", doc)
        self.assertIn("Level1LocalReplayOrLower", doc)


if __name__ == "__main__":
    unittest.main()
