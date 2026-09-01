"""Hermetic feature and aggregate tests for V40.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.
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


RUNNER = load_module("astral_stage0c_qwen36_run_preassessment_v40", "run_preassessment_v40.py")
ASSESSMENT = load_module("astral_stage0c_qwen36_run_assessment_v40", "run_assessment_v40.py")
VALIDATOR = load_module("astral_stage0c_qwen36_validate_assessment_v40", "validate_assessment_v40.py")


class FeaturesV40Tests(unittest.TestCase):
    def test_pair_and_clean_features_are_fixed_width_and_deterministic(self) -> None:
        ordinary = np.arange(2048, dtype=np.float32)
        counterfactual = ordinary[::-1].copy()
        first = RUNNER._pair_activation_features(ordinary, counterfactual)
        second = RUNNER._pair_activation_features(ordinary, counterfactual)
        clean = RUNNER._clean_activation_features(ordinary, counterfactual)
        self.assertEqual(first.shape, (RUNNER.protocol.FEATURE_WIDTH,))
        self.assertEqual(clean.shape, (RUNNER.protocol.FEATURE_WIDTH,))
        np.testing.assert_array_equal(first, second)
        self.assertTrue(np.isfinite(first).all())

    def test_norm_matching_preserves_receiver_norm(self) -> None:
        source = np.array([3.0, 4.0], dtype=np.float32)
        receiver = np.array([6.0, 8.0], dtype=np.float32)
        matched = RUNNER._norm_match(source, receiver)
        self.assertAlmostEqual(float(np.linalg.norm(matched)), 10.0, places=5)

    def test_cluster_bootstrap_is_deterministic_and_aggregate_only(self) -> None:
        rows = [
            {
                "gutenberg_id": index,
                "count": 8,
                "pair_squared_error_sum": float(index + 1),
                "constant_squared_error_sum": float(index + 2),
            }
            for index in range(6)
        ]
        first = ASSESSMENT._cluster_bootstrap(rows)
        second = ASSESSMENT._cluster_bootstrap(rows)
        self.assertEqual(first, second)
        self.assertEqual(first["document_clusters"], 6)
        self.assertNotIn("predictions", first)

    def test_invalid_bundle_returns_structured_error(self) -> None:
        missing = HERE / "missing-assessment-bundle"
        result = VALIDATOR.validate(missing, missing, missing, missing, missing, missing, missing, HERE)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "AssessmentInvalid")
        self.assertEqual(result["claim_ceiling"], VALIDATOR.assessment.ASSESSMENT_CLAIM_CEILING)
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
