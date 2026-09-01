"""Hermetic pure-data tests for the V40 protocol.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.
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


PROTOCOL = load_module("astral_stage0c_qwen36_protocol_v40", "protocol_v40.py")


class ProtocolV40Tests(unittest.TestCase):
    def test_state_slice_and_selection_are_fresh(self) -> None:
        self.assertEqual(PROTOCOL.PROTOCOL_ID, PROTOCOL.STATE_SLICE)
        selected = {item["gutenberg_id"] for item in PROTOCOL.SELECTION}
        self.assertEqual(len(selected), 18)
        self.assertTrue(selected.isdisjoint(PROTOCOL.V39_GUTENBERG_IDS))
        self.assertEqual(
            {split: sum(item["split"] == split for item in PROTOCOL.SELECTION) for split in PROTOCOL.SPLITS},
            {split: PROTOCOL.DOCUMENTS_PER_SPLIT for split in PROTOCOL.SPLITS},
        )

    def test_external_path_guard_rejects_repository(self) -> None:
        with self.assertRaises(PROTOCOL.ProtocolError):
            PROTOCOL.assert_external(HERE.parents[1], HERE.parents[1])

    def test_canonical_digest_is_stable(self) -> None:
        self.assertEqual(PROTOCOL.selection_digest(), PROTOCOL.selection_digest())
        self.assertEqual(len(PROTOCOL.selection_digest()), 64)


if __name__ == "__main__":
    unittest.main()
