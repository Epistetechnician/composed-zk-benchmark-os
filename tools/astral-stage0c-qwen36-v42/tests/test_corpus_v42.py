"""Hermetic V42 Gutenberg-custody tests.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import acquire_gutenberg_corpus_v42 as acquire
import protocol_v42 as protocol


class CorpusV42Tests(unittest.TestCase):
    def test_canonical_text_requires_both_project_gutenberg_boundaries(self) -> None:
        payload = b"header\n*** START OF TEST\nbody\n*** END OF TEST\n"
        self.assertEqual(acquire._canonical_text(payload), payload)
        with self.assertRaises(protocol.ProtocolError):
            acquire._canonical_text(b"*** START OF TEST\nbody\n")

    def test_metadata_rejects_non_english_or_collected_titles(self) -> None:
        self.assertIn("complete works", protocol.FORBIDDEN_TITLE_MARKERS)
        self.assertIn("volume ", protocol.FORBIDDEN_TITLE_MARKERS)
        self.assertEqual(protocol.freshness_exclusion_digest([3, 2, 3]), protocol.freshness_exclusion_digest([2, 3]))


if __name__ == "__main__":
    unittest.main()
