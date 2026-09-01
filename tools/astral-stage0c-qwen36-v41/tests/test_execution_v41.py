"""Hermetic estimator and control tests for V41.

State slice: astral-stage0c-qwen36-directional-block-target-v41.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import protocol_v41 as protocol
import run_assessment_v41 as assessment
import run_preassessment_v41 as preassessment
import validate_assessment_v41 as assessment_validator


class ExecutionV41Tests(unittest.TestCase):
    def test_ridge_selection_is_deterministic_and_fixed_width(self) -> None:
        rng = np.random.default_rng(4101)
        fit_features = rng.normal(size=(protocol.FAMILIES_PER_SPLIT, protocol.FEATURE_WIDTH))
        tune_features = rng.normal(size=(protocol.FAMILIES_PER_SPLIT, protocol.FEATURE_WIDTH))
        fit_targets = rng.normal(size=protocol.FAMILIES_PER_SPLIT)
        tune_targets = rng.normal(size=protocol.FAMILIES_PER_SPLIT)
        first_state, first_summary = preassessment._select(
            protocol.PRIMARY_CONTROL,
            fit_features,
            fit_targets,
            tune_features,
            tune_targets,
        )
        second_state, second_summary = preassessment._select(
            protocol.PRIMARY_CONTROL,
            fit_features,
            fit_targets,
            tune_features,
            tune_targets,
        )
        self.assertEqual(first_summary, second_summary)
        np.testing.assert_array_equal(first_state["coefficients"], second_state["coefficients"])
        self.assertEqual(len(first_state["coefficients"]), protocol.FEATURE_WIDTH)

    def test_shuffle_is_a_permutation_bound_to_protocol(self) -> None:
        family_ids = [f"family-{index:02d}" for index in range(protocol.FAMILIES_PER_SPLIT)]
        first = preassessment._row_permutation(family_ids, "fit", "panel-digest")
        second = preassessment._row_permutation(family_ids, "fit", "panel-digest")
        np.testing.assert_array_equal(first, second)
        self.assertEqual(sorted(first.tolist()), list(range(protocol.FAMILIES_PER_SPLIT)))

    def test_norm_match_preserves_receiver_norm_within_tolerance(self) -> None:
        source = np.arange(protocol.EXPECTED_HIDDEN_WIDTH, dtype=np.float32) + 1.0
        receiver = source[::-1].copy() * np.float32(3.0)
        replacement, relative_error = preassessment._norm_match(source, receiver)
        self.assertLessEqual(relative_error, protocol.MATCH_NORM_RELATIVE_TOLERANCE)
        self.assertAlmostEqual(
            float(np.linalg.norm(replacement.astype(np.float64))),
            float(np.linalg.norm(receiver.astype(np.float64))),
            places=5,
        )

    def test_assessment_metric_is_aggregate_only(self) -> None:
        metric = assessment._metric(np.asarray([1.0, 3.0]), np.asarray([0.0, 2.0]))
        self.assertEqual(metric["count"], 2)
        self.assertNotIn("predictions", metric)
        self.assertNotIn("effects", metric)

    def test_invalid_bundle_returns_structured_error(self) -> None:
        missing = HERE / "missing-assessment-bundle"
        result = assessment_validator.validate(missing, missing, missing, missing, missing, missing, missing, HERE)
        self.assertFalse(result["valid"])
        self.assertEqual(result["classification"], "AssessmentInvalid")
        self.assertEqual(result["claim_ceiling"], assessment.ASSESSMENT_CLAIM_CEILING)
        self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
