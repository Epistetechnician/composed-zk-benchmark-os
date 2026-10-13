"""Hermetic contract checks for private-decision-model-fhe-inference-v1."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

import decision_model
import run_v1
import server_worker


class SyntheticScorerContractTests(unittest.TestCase):
    def test_fit_recovers_fixed_synthetic_scorer(self) -> None:
        weights, bias = decision_model.fit_synthetic_scorer()
        np.testing.assert_array_equal(weights, [2, -3, 1, 4, -2, 3])
        self.assertEqual(bias, 5)

    def test_calibration_and_evaluation_are_shape_fixed_and_disjoint(self) -> None:
        calibration = decision_model.synthetic_calibration_requests()
        evaluation = decision_model.synthetic_evaluation_requests()

        self.assertEqual(calibration.shape, (12, 4, 6))
        self.assertEqual(evaluation.shape, (8, 4, 6))
        self.assertTrue(np.all(calibration >= -8))
        self.assertTrue(np.all(calibration <= 8))
        self.assertTrue(np.all(evaluation >= -8))
        self.assertTrue(np.all(evaluation <= 8))
        self.assertFalse(np.array_equal(calibration[:8], evaluation))

    def test_fixture_digest_is_deterministic(self) -> None:
        self.assertEqual(
            decision_model.synthetic_fixture_sha256(),
            decision_model.synthetic_fixture_sha256(),
        )

    def test_request_validation_rejects_bad_shape_type_and_range(self) -> None:
        valid = decision_model.synthetic_evaluation_requests()
        bad_shape = np.zeros((8, 4, 5), dtype=np.int64)
        bad_type = np.zeros((8, 4, 6), dtype=np.float64)
        bad_range = np.full((8, 4, 6), 9, dtype=np.int64)
        for candidate in (bad_shape, bad_type, bad_range):
            with self.subTest(candidate=candidate.shape, dtype=candidate.dtype):
                with self.assertRaises(ValueError):
                    decision_model.validate_request_batch(candidate)
        with self.assertRaises(ValueError):
            decision_model.validate_request_batch(valid, expected_count=7)

    def test_bounded_randomized_scorer_inputs_match_independent_integer_formula(self) -> None:
        generator = np.random.default_rng(20260931)
        requests = generator.integers(-8, 9, size=(256, 4, 6), dtype=np.int64)
        decision_model.validate_request_batch(requests, expected_count=256)
        weights, bias = decision_model.fit_synthetic_scorer()

        for request in requests:
            actual = decision_model.option_scores(request)
            expected = np.asarray(
                [
                    sum(
                        int(value) * int(weight)
                        for value, weight in zip(row, weights, strict=True)
                    )
                    + bias
                    for row in request
                ],
                dtype=np.int64,
            )
            np.testing.assert_array_equal(actual, expected)

    def test_server_request_schema_rejects_cleartext_or_secret_key_fields(self) -> None:
        malicious = {
            "evaluation_keys": "not-a-key",
            "encrypted_arguments": ["not-a-ciphertext"],
            "clear_features": "sentinel",
            "client_secret_key": "sentinel",
        }
        with self.assertRaisesRegex(ValueError, "only evaluation keys and encrypted arguments"):
            server_worker._validate_evaluation_request(malicious)

    def test_server_process_does_not_inherit_unapproved_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "AWS_SECRET_ACCESS_KEY": "synthetic-sentinel",
                "OPENAI_API_KEY": "synthetic-sentinel",
                "TMPDIR": "/tmp",
            },
            clear=True,
        ):
            worker_environment = run_v1._worker_environment()
        self.assertEqual(worker_environment, {"TMPDIR": "/tmp"})


if __name__ == "__main__":
    unittest.main()
