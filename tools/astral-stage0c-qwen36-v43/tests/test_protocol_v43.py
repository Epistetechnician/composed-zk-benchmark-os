"""Hermetic V43 protocol tests.

State slice: astral-stage0c-qwen36-causal-target-localization-v43.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import protocol_v43 as protocol


class ProtocolV43Tests(unittest.TestCase):
    def test_selection_is_fresh_and_split_complete(self) -> None:
        selected = {int(item["gutenberg_id"]) for item in protocol.SELECTION}
        self.assertEqual(len(selected), protocol.TOTAL_DOCUMENTS)
        self.assertTrue(selected.isdisjoint(protocol.KNOWN_RESERVED_GUTENBERG_IDS))
        for split in protocol.SPLITS:
            self.assertEqual(sum(item["split"] == split for item in protocol.SELECTION), protocol.DOCUMENTS_PER_SPLIT)

    def test_target_localization_contract_is_fixed(self) -> None:
        self.assertEqual(protocol.CANDIDATE_LAYERS, (12, 19, 26))
        self.assertEqual(protocol.FIXED_POSITION, "last_input_position_before_response")
        self.assertEqual(protocol.FIXED_TOKEN_LENGTH, 320)
        self.assertEqual(protocol.WRAPPER_NAMES, ("wrapper_alpha", "wrapper_beta"))
        self.assertEqual(protocol.CONTROL_NAMES, ("activation_only", "text_only", "exact_copy", "shuffled", "constant", "matched"))

    def test_digests_are_stable_and_model_shape_is_sealed(self) -> None:
        self.assertEqual(protocol.selection_digest(), protocol.selection_digest())
        self.assertEqual(len(protocol.selection_digest()), 64)
        manifest = protocol.protocol_manifest()
        self.assertEqual(manifest["state_slice"], protocol.STATE_SLICE)
        self.assertEqual(manifest["model"]["layer_count"], 40)
        self.assertEqual(manifest["model"]["hidden_width"], 2048)
        self.assertEqual(manifest["model"]["candidate_layers"], [12, 19, 26])


if __name__ == "__main__":
    unittest.main()
