"""Hermetic V39 preassessment feature and lock tests.

State slice: astral-stage0c-qwen36-layer-effect-v39.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "astral_stage0c_qwen36_run_preassessment_v39",
    HERE / "run_preassessment_v39.py",
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class PreassessmentV39Tests(unittest.TestCase):
    def test_activation_projection_is_fixed_and_bounded(self) -> None:
        ordinary = np.arange(2048, dtype=np.float32)
        counterfactual = ordinary[::-1].copy()
        first = RUNNER._activation_features(ordinary, counterfactual)
        second = RUNNER._activation_features(ordinary, counterfactual)
        self.assertEqual(first.shape, (64,))
        np.testing.assert_array_equal(first, second)
        self.assertAlmostEqual(float(np.linalg.norm(first)), 1.0, places=6)

    def test_text_panel_uses_prompt_difference_only(self) -> None:
        ordinary = "Read the passage. Passage: silver meadow. Answer:"
        counterfactual = "Read the passage. Passage: amber meadow. Answer:"
        first = RUNNER._text_pair_features(ordinary, counterfactual)
        second = RUNNER._text_pair_features(ordinary, counterfactual)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first.shape, (64,))
        self.assertGreater(float(np.linalg.norm(first)), 0.0)

    def test_row_shuffle_is_deterministic_and_preserves_capacity(self) -> None:
        features = np.arange(4 * 64, dtype=np.float64).reshape(4, 64)
        ids = ["a", "b", "c", "d"]
        first = RUNNER._shuffled_features(features, ids, "fit", "a" * 64)
        second = RUNNER._shuffled_features(features, ids, "fit", "a" * 64)
        np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(np.sort(first[:, 0]), np.sort(features[:, 0]))

    def test_ridge_selection_tie_breaks_to_smallest_alpha(self) -> None:
        features = np.zeros((4, 64), dtype=np.float64)
        targets = np.zeros(4, dtype=np.float64)
        state, summary = RUNNER._select_model(
            "activation_only",
            features,
            targets,
            features,
            targets,
        )
        self.assertEqual(summary["selected_alpha"], min(RUNNER.RIDGE_ALPHAS))
        np.testing.assert_array_equal(RUNNER._predict(state, features), targets)

    def test_norm_matching_preserves_receiver_norm(self) -> None:
        source = np.array([3.0, 4.0], dtype=np.float32)
        receiver = np.array([6.0, 8.0], dtype=np.float32)
        matched = RUNNER._norm_match(source, receiver)
        self.assertAlmostEqual(float(np.linalg.norm(matched)), 10.0, places=5)

    def test_assessment_effect_measurement_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            RUNNER._measure_split(
                None,
                [],
                [{"split": "assessment"}],
                [],
                {},
                {},
                None,
            )


if __name__ == "__main__":
    unittest.main()
