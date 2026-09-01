"""Hermetic feature-map tests for V41.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


import protocol_v41 as PROTOCOL
FEATURES = load_module("astral_stage0c_qwen36_features_v41", "features_v41.py")


class FeaturesV41Tests(unittest.TestCase):
    def test_block_projection_is_fixed_and_non_overlapping(self) -> None:
        vector = np.arange(PROTOCOL.EXPECTED_HIDDEN_WIDTH, dtype=np.float32)
        first = FEATURES.block_projection(vector)
        second = FEATURES.block_projection(vector)
        self.assertEqual(first.shape, (PROTOCOL.BLOCK_COUNT,))
        np.testing.assert_array_equal(first, second)
        self.assertTrue(np.isfinite(first).all())

    def test_pair_and_clean_features_are_fixed_width(self) -> None:
        ordinary = np.arange(PROTOCOL.EXPECTED_HIDDEN_WIDTH, dtype=np.float32)
        counterfactual = ordinary[::-1].copy()
        pair = FEATURES.pair_features(ordinary, counterfactual)
        clean = FEATURES.clean_activation_features(ordinary, counterfactual)
        self.assertEqual(pair.shape, (PROTOCOL.FEATURE_WIDTH,))
        self.assertEqual(clean.shape, (PROTOCOL.FEATURE_WIDTH,))
        self.assertTrue(np.isfinite(pair).all())
        self.assertFalse(np.array_equal(pair, clean))

    def test_invalid_activation_shape_fails_closed(self) -> None:
        with self.assertRaises(PROTOCOL.ProtocolError):
            FEATURES.block_projection(np.zeros(64, dtype=np.float32))

    def test_text_feature_width_is_capacity_matched(self) -> None:
        vector = FEATURES.text_features("ordinary passage", "counterfactual passage")
        self.assertEqual(vector.shape, (PROTOCOL.FEATURE_WIDTH,))
        self.assertTrue(np.isfinite(vector).all())


if __name__ == "__main__":
    unittest.main()
