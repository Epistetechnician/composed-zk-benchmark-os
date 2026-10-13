"""Hermetic tests for the V4 packet-bound FHE execution receipt.

State slices: private-decision-model-fhe-local-ipc-receipt-v4 and
global-experiment-assurance-lifecycle-v1.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
V3_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v3"
sys.path.insert(0, str(V3_DIR))

import run_v3  # noqa: E402
import run_v4  # noqa: E402


class CanonicalSourceDigestTests(unittest.TestCase):
    def test_dotdot_and_absolute_spellings_have_same_repository_path(self) -> None:
        canonical = ROOT / "tools" / "private_decision_model_fhe_inference_v4" / "run_v4.py"
        alias = ROOT / "tools" / "private_decision_model_fhe_inference_v1" / ".." / "private_decision_model_fhe_inference_v4" / "run_v4.py"
        self.assertEqual(run_v4.canonical_repo_path(alias), run_v4.canonical_repo_path(canonical))

    def test_frozen_packet_sources_and_composites_match(self) -> None:
        packet, _ = run_v4.validate_frozen_packet()
        self.assertEqual(
            run_v4.v4_source_digest(),
            packet["source_identity"]["v4_source_composite_sha256"],
        )
        self.assertEqual(
            run_v4.v3_source_digest(),
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
            result = run_v4.execute()

        self.assertIs(run_v3._source_digest, original_supplier)
        self.assertEqual(result["schema"], "private-decision-model-fhe-local-ipc-receipt-v4-result")
        self.assertEqual(result["state_slice"], "private-decision-model-fhe-local-ipc-receipt-v4")
        self.assertEqual(result["claim_ceiling"], "LocalDevelopmentSyntheticFHEIPCReceiptQualificationV4")
        self.assertEqual(result["v4_source_sha256"], run_v4.v4_source_digest())
        self.assertTrue(result["execution"]["source_digest_matches_packet"])


if __name__ == "__main__":
    unittest.main()
