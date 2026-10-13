"""Hermetic tests for the V5 packet-bound FHE execution receipt.

State slices: private-decision-model-fhe-local-ipc-receipt-v5 and
global-experiment-assurance-lifecycle-v1.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
V5_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v5"
V3_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v3"
sys.path.insert(0, str(V5_DIR))
sys.path.insert(0, str(V3_DIR))

import run_v3  # noqa: E402
import run_v5  # noqa: E402


class CanonicalSourceDigestTests(unittest.TestCase):
    def test_dotdot_and_absolute_spellings_have_same_repository_path(self) -> None:
        canonical = V5_DIR / "run_v5.py"
        alias = ROOT / "tools" / "private_decision_model_fhe_inference_v1" / ".." / "private_decision_model_fhe_inference_v5" / "run_v5.py"
        self.assertEqual(run_v5.canonical_repo_path(alias), run_v5.canonical_repo_path(canonical))

    def test_frozen_packet_sources_and_composites_match(self) -> None:
        packet, _ = run_v5.validate_frozen_packet()
        self.assertEqual(
            run_v5.v5_source_digest(),
            packet["source_identity"]["v5_source_composite_sha256"],
        )
        self.assertEqual(
            run_v5.v3_source_digest(),
            packet["predecessor"]["v3_source_composite_sha256"],
        )


class FrozenRunnerAdapterTests(unittest.TestCase):
    def test_adapter_relabels_result_and_restores_digest_supplier(self) -> None:
        original_supplier = run_v3._source_digest
        mocked_result = {
            "schema": "prior-result",
            "state_slice": "prior-slice",
            "v3_source_sha256": "placeholder",
            "execution": {"temporary_fhe_files_removed": True},
        }
        with patch.object(run_v3, "execute", return_value=mocked_result):
            result = run_v5.execute()

        self.assertIs(run_v3._source_digest, original_supplier)
        self.assertEqual(result["schema"], "private-decision-model-fhe-local-ipc-receipt-v5-result")
        self.assertEqual(result["state_slice"], "private-decision-model-fhe-local-ipc-receipt-v5")
        self.assertEqual(result["claim_ceiling"], "LocalDevelopmentSyntheticFHEIPCReceiptQualificationV5")
        self.assertEqual(result["v5_source_sha256"], run_v5.v5_source_digest())
        self.assertTrue(result["execution"]["source_digest_matches_packet"])


if __name__ == "__main__":
    unittest.main()
