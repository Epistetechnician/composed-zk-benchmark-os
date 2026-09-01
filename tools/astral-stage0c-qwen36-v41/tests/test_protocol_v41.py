"""Hermetic protocol tests for V41.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOCOL = load_module("astral_stage0c_qwen36_protocol_v41", "protocol_v41.py")


class ProtocolV41Tests(unittest.TestCase):
    def test_state_slice_and_feature_geometry_are_fixed(self) -> None:
        self.assertEqual(PROTOCOL.PROTOCOL_ID, PROTOCOL.STATE_SLICE)
        self.assertEqual(PROTOCOL.BLOCK_COUNT * PROTOCOL.BLOCK_WIDTH, PROTOCOL.EXPECTED_HIDDEN_WIDTH)
        self.assertEqual(PROTOCOL.FEATURE_WIDTH, 516)
        self.assertEqual(PROTOCOL.feature_map_digest(), PROTOCOL.feature_map_digest())

    def test_signs_are_deterministic_and_cover_each_block(self) -> None:
        signs = [PROTOCOL.block_sign(3, index) for index in range(PROTOCOL.BLOCK_WIDTH)]
        self.assertEqual(signs, [PROTOCOL.block_sign(3, index) for index in range(PROTOCOL.BLOCK_WIDTH)])
        self.assertIn(1, signs)
        self.assertIn(-1, signs)

    def test_external_path_guard_rejects_repository(self) -> None:
        with self.assertRaises(PROTOCOL.ProtocolError):
            PROTOCOL.assert_external(HERE.parents[1], HERE.parents[1])

    def test_freshness_inventory_digest_is_canonical(self) -> None:
        inventory = list(PROTOCOL.FRESHNESS_EXCLUSION_INVENTORY)
        self.assertEqual(PROTOCOL.freshness_exclusion_digest(inventory), PROTOCOL.freshness_exclusion_digest(list(reversed(inventory))))

    def test_selection_is_fresh_and_balanced(self) -> None:
        ids = [item["gutenberg_id"] for item in PROTOCOL.SELECTION]
        self.assertEqual(len(ids), PROTOCOL.TOTAL_DOCUMENTS)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(ids).isdisjoint(PROTOCOL.KNOWN_RESERVED_GUTENBERG_IDS))
        self.assertEqual(
            {split: sum(item["split"] == split for item in PROTOCOL.SELECTION) for split in PROTOCOL.SPLITS},
            {split: PROTOCOL.DOCUMENTS_PER_SPLIT for split in PROTOCOL.SPLITS},
        )


if __name__ == "__main__":
    unittest.main()
