"""Hermetic verification suite for Layer 4 PQAI Multi-Assumption Cryptanalysis Frontier."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from frontier import (  # noqa: E402
    build_pqai_frontier_report,
    run_hash_algebraic_vs_conservative_probes,
    run_toy_lwe_sis_probe,
    verify_report_digest,
)


class TestPqaiFrontier(unittest.TestCase):
    def test_deterministic_reproducible_and_tamper_evident(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "score.json").write_text(
                json.dumps({"score": 2402429905, "metrics": {"toffoli": 1773011, "qubits": 1355}}),
                encoding="utf-8",
            )
            r1 = build_pqai_frontier_report([root])
            r2 = build_pqai_frontier_report([root])

            # All three PQAI fronts populated and non-collapsed
            self.assertEqual(set(r1["fronts"].keys()), {"ecc", "lattice_code", "hash_algebraic_vs_conservative"})
            self.assertTrue(r1["all_probes_verified"])
            self.assertEqual(len(r1["fronts"]["ecc"]), 2)
            self.assertEqual(len(r1["fronts"]["lattice_code"]), 3)
            self.assertEqual(len(r1["fronts"]["hash_algebraic_vs_conservative"]), 3)

            # Digest verifies and rejects 1-field tampering
            self.assertTrue(verify_report_digest(r1))
            tampered = copy.deepcopy(r1)
            tampered["fronts"]["ecc"][0]["primary_metric_value"] = 1.0
            self.assertFalse(verify_report_digest(tampered))

            # Evidence classes strictly distinguished
            ev_classes = {
                row["evidence_class"]
                for rows in r1["fronts"].values()
                for row in rows
            }
            self.assertEqual(
                ev_classes,
                {"EvaluatorVerifiedCircuit", "MeasuredLocalProbe", "AnalyticalSecurityModel"},
            )
            # Reproducible structural metrics
            self.assertEqual(r1["fronts"]["ecc"], r2["fronts"]["ecc"])
            self.assertEqual(
                r1["fronts"]["hash_algebraic_vs_conservative"],
                r2["fronts"]["hash_algebraic_vs_conservative"],
            )

    def test_live_probes_pass(self) -> None:
        seed = bytes.fromhex("20261123" + "00" * 28)
        lwe = run_toy_lwe_sis_probe(seed)
        self.assertTrue(lwe.passed_verification)
        self.assertTrue(lwe.metrics["recovered_matches_secret"])

        pts, receipts = run_hash_algebraic_vs_conservative_probes(seed)
        self.assertEqual(len(pts), 3)
        self.assertTrue(all(r.passed_verification for r in receipts))
        # Poseidon2 2-round x^5 exact algebraic degree == 25
        self.assertEqual(receipts[0].metrics["observed_exact_degree"], 25)


if __name__ == "__main__":
    unittest.main()
