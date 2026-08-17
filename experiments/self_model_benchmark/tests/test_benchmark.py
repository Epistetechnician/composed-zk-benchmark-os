import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.protocol import (
    BenchmarkProtocolError,
    LIVE_SOURCE,
    VARIANTS,
    digest_json,
    evaluate,
    load_input,
    validate_result,
)
from experiments.self_model_benchmark.run_benchmark import main as run_main
from experiments.self_model_benchmark.validate_benchmark import main as validate_main


def _manifest(source_type: str) -> dict:
    manifest = {
        "record_type": "manifest",
        "schema_version": "verified-self-model-benchmark-input-v1",
        "state_slice": "verified-self-model-benchmark-v1",
        "workflow_id": "self-model-test",
        "source_type": source_type,
        "fixed_budget": True,
        "budget": {"max_latency_ms": 120000, "max_compute_units": 24000, "max_tool_calls": 12, "max_attempts": 2},
        "variants": list(VARIANTS),
        "prediction_locked_before_assessment": True,
        "external_outcomes_verified": True,
        "recorded_by_external_validator": True,
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "network_access": False,
    }
    if source_type == LIVE_SOURCE:
        manifest.update({"model_digest": "a" * 64, "runtime_digest": "b" * 64, "checker_digest": "c" * 64})
    return manifest


def _trial(trajectory: int, split: str, variant: str) -> dict:
    failed = variant in {"memory_reset", "policy_restricted"}
    actual_limitation = "memory" if variant == "memory_reset" else "out_of_scope" if failed else "none"
    effect = {"base": 0, "tool_augmented": 100, "budget_extended": 100, "memory_reset": -200, "policy_restricted": -300}[variant]
    trial = {
        "record_type": "self_model_trial",
        "trajectory_id": f"trajectory-{trajectory:02d}",
        "task_family": f"family-{trajectory % 5}",
        "split": split,
        "variant": variant,
        "horizon_step": 1,
        "predicted_success_probability_milli": 250 if failed else 900,
        "predicted_limitation": actual_limitation,
        "predicted_variant_effect_milli": effect,
        "actual_outcome": (
            "capability_gap"
            if variant == "memory_reset"
            else "scope_violation"
            if variant == "policy_restricted"
            else "success"
        ),
        "actual_success": not failed,
        "actual_limitation": actual_limitation,
        "actual_variant_effect_milli": effect,
        "prior_belief_milli": 500,
        "posterior_belief_milli": 300 if failed else 700,
        "verified_update_direction": "decrease" if failed else "increase",
        "prediction_locked_before_outcome": True,
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "network_access": False,
    }
    return trial


def _live_records() -> tuple[dict, list[dict]]:
    manifest = _manifest(LIVE_SOURCE)
    trials = []
    split_counts = (("fit", 24), ("tune", 12), ("assessment", 24))
    trajectory = 0
    for split, count in split_counts:
        for _ in range(count):
            for variant in VARIANTS:
                trial = _trial(trajectory, split, variant)
                trial["record_digest"] = digest_json(trial)
                trials.append(trial)
            trajectory += 1
    return manifest, trials


class SelfModelBenchmarkTests(unittest.TestCase):
    def test_smoke_fixture_scores_without_claiming_self_model(self):
        manifest, trials = load_input("experiments/self_model_benchmark/fixtures/smoke.jsonl")
        result = evaluate(manifest, trials)
        self.assertEqual(result["classification"], "ContractSmokeOnly")
        self.assertEqual(result["claim_ceiling"], "ContractSmokeOnly")
        self.assertFalse(result["scientific_evidence"])
        self.assertFalse(result["authority_granted"])
        self.assertIn("capability_brier", result["metrics"])

    def test_live_shaped_candidate_requires_all_recursive_gates(self):
        manifest, trials = _live_records()
        result = evaluate(manifest, trials)
        self.assertEqual(result["classification"], "LocalDevelopmentSelfModelBenchmarkCandidate")
        self.assertEqual(result["decision"], "keep_candidate")
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(result["trajectory_count"], 60)
        self.assertEqual(result["trial_count"], 300)
        self.assertEqual(validate_result(result, result), [])

    def test_recursive_continuity_rejects_broken_prior(self):
        manifest, trials = _live_records()
        first_rows = trials[: len(VARIANTS)]
        for row in first_rows:
            continuation = dict(row)
            continuation["horizon_step"] = 2
            continuation["prior_belief_milli"] = 1 if row["variant"] == "base" else row["posterior_belief_milli"]
            continuation["posterior_belief_milli"] = 700
            continuation["record_digest"] = digest_json(
                {key: value for key, value in continuation.items() if key != "record_digest"}
            )
            trials.append(continuation)
        with self.assertRaisesRegex(BenchmarkProtocolError, "recursive belief updates"):
            load_input_from_records(manifest, trials)

    def test_raw_and_authority_fields_fail_closed(self):
        manifest, trials = _live_records()
        trials[0]["chain_of_thought"] = "forbidden"
        with self.assertRaises(BenchmarkProtocolError):
            load_input_from_records(manifest, trials)
        manifest, trials = _live_records()
        trials[0]["authority_granted"] = True
        with self.assertRaisesRegex(BenchmarkProtocolError, "authority_granted"):
            load_input_from_records(manifest, trials)

    def test_cli_round_trip_and_result_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "smoke.jsonl"
            result_path = root / "result.json"
            input_path.write_text(Path("experiments/self_model_benchmark/fixtures/smoke.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
            with patch.object(sys, "argv", ["run_benchmark", "--input", str(input_path), "--output", str(result_path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_main(), 0)
            with patch.object(sys, "argv", ["validate_benchmark", str(result_path), "--input", str(input_path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate_main(), 0)
            tampered = json.loads(result_path.read_text(encoding="utf-8"))
            tampered["metrics"]["capability_brier"] = 1.0
            result_path.write_text(json.dumps(tampered), encoding="utf-8")
            with patch.object(sys, "argv", ["validate_benchmark", str(result_path), "--input", str(input_path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate_main(), 1)


def load_input_from_records(manifest: dict, trials: list[dict]) -> tuple[dict, list[dict]]:
    from experiments.self_model_benchmark.protocol import _trajectory_checks, validate_manifest, validate_trial

    validate_manifest(manifest)
    for trial in trials:
        validate_trial(trial, manifest)
    checks = _trajectory_checks(trials)
    if not checks["trajectory_variant_complete"]:
        raise BenchmarkProtocolError("trajectory variants incomplete")
    if not checks["recursive_update_continuity"]:
        raise BenchmarkProtocolError("recursive belief updates are not continuous")
    return manifest, trials


if __name__ == "__main__":
    unittest.main()
