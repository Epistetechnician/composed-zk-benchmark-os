"""Hermetic V42 protocol tests.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import protocol_v42 as protocol


class ProtocolV42Tests(unittest.TestCase):
    def test_selection_is_fresh_and_split_complete(self) -> None:
        selected = {int(item["gutenberg_id"]) for item in protocol.SELECTION}
        self.assertEqual(len(selected), protocol.TOTAL_DOCUMENTS)
        self.assertTrue(selected.isdisjoint(protocol.KNOWN_RESERVED_GUTENBERG_IDS))
        for split in protocol.SPLITS:
            self.assertEqual(sum(item["split"] == split for item in protocol.SELECTION), protocol.DOCUMENTS_PER_SPLIT)

    def test_protocol_digest_is_stable(self) -> None:
        self.assertEqual(protocol.selection_digest(), protocol.selection_digest())
        self.assertEqual(len(protocol.selection_digest()), 64)
        self.assertEqual(protocol.TARGET_LAYER, 19)
        self.assertEqual(protocol.EXPECTED_LAYER_COUNT, 40)
        self.assertEqual(protocol.EXPECTED_HIDDEN_WIDTH, 2048)

    def test_wrappers_and_controls_are_fixed(self) -> None:
        self.assertEqual(protocol.WRAPPER_NAMES, ("wrapper_alpha", "wrapper_beta"))
        self.assertEqual(
            protocol.CONTROL_NAMES,
            ("exact_copy", "shuffled", "constant", "matched"),
        )
        self.assertEqual(protocol.FIXED_TOKEN_LENGTH, 320)
        self.assertEqual(protocol.REPEATS, 2)


if __name__ == "__main__":
    unittest.main()
