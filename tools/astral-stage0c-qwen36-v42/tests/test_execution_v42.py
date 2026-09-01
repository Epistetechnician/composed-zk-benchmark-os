"""Hermetic V42 reliability and retention tests.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import protocol_v42 as protocol
import run_target_reliability_v42 as runner
import validate_target_reliability_v42 as validator


class ExecutionV42Tests(unittest.TestCase):
    def test_reliability_is_deterministic_for_fixed_vectors(self) -> None:
        left = np.asarray([0.1, -0.4, 0.3, 0.8, -0.2, 0.5], dtype=np.float64)
        right = np.asarray([0.2, -0.5, 0.4, 0.7, -0.1, 0.6], dtype=np.float64)
        first = runner._reliability(left, right)
        second = runner._reliability(left, right)
        self.assertEqual(first, second)
        self.assertEqual(first["gates"]["target_effect_non_degenerate"], True)

    def test_configuration_lock_digest_excludes_its_self_digest(self) -> None:
        lock = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE, "x": 1}
        unsigned_digest = runner._configuration_lock_digest(lock)
        lock["configuration_lock_sha256"] = unsigned_digest
        self.assertEqual(runner._configuration_lock_digest(lock), unsigned_digest)

    def test_forbidden_output_keys_are_rejected(self) -> None:
        errors = validator._scan_forbidden({"aggregate": {"predictions": [1], "mean": 0.0}})
        self.assertEqual(errors, ["forbidden_key:$.aggregate.predictions"])

    def test_bootstrap_is_seed_bound(self) -> None:
        left = np.asarray([0.1, -0.4, 0.3, 0.8, -0.2, 0.5], dtype=np.float64)
        right = np.asarray([0.2, -0.5, 0.4, 0.7, -0.1, 0.6], dtype=np.float64)
        self.assertEqual(runner._bootstrap_lower(left, right), runner._bootstrap_lower(left, right))


if __name__ == "__main__":
    unittest.main()
