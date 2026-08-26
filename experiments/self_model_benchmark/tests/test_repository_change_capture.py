import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.self_model_benchmark.protocol import LIVE_SOURCE, SMOKE_SOURCE, VARIANTS, digest_json, evaluate, load_input
from experiments.self_model_benchmark.capture_preflight import (
    CLAIM_CEILING,
    PreflightError,
    main as preflight_main,
    preflight_capture,
    validate_report,
)
from experiments.self_model_benchmark.repository_change_capture import (
    CaptureError,
    _convert_for_contract_test,
    convert,
    load_capture,
    main as capture_main,
    validate_observation,
    write_jsonl,
)
from experiments.self_model_benchmark.run_benchmark import main as benchmark_main
from experiments.self_model_benchmark.validate_benchmark import main as validate_main


CHECKS = {
    "format": "pass",
    "focused_tests": "pass",
    "contract_validation": "pass",
    "diff_hygiene": "pass",
    "claim_boundary": "pass",
}


def _manifest(source_type: str) -> dict:
    return {
        "record_type": "self_model_capture_manifest",
        "schema_version": "verified-self-model-repository-capture-v1",
        "state_slice": "verified-self-model-benchmark-repository-capture-v1",
        "workflow_id": "repository-change-self-model-test",
        "source_type": source_type,
        "fixed_budget": True,
        "budget": {"max_latency_ms": 120000, "max_compute_units": 24000, "max_tool_calls": 12, "max_attempts": 2},
        "variants": list(VARIANTS),
        "required_check_ids": ["format", "focused_tests", "contract_validation", "diff_hygiene", "claim_boundary"],
        "prediction_locked_before_assessment": True,
        "external_outcomes_verified": True,
        "recorded_by_external_validator": True,
        "agent_execution_recorded": True,
        "validator_custody": True,
        "validator_report_digest": "a" * 64,
        "model_digest": "b" * 64,
        "runtime_digest": "c" * 64,
        "checker_digest": "d" * 64,
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "network_access": False,
    }


def _observation(trajectory: int, split: str, variant: str) -> dict:
    failed = variant in {"memory_reset", "policy_restricted"}
    scope_valid = variant != "policy_restricted"
    capability_gap = variant == "memory_reset"
    limitation = "missing_tool" if capability_gap else "out_of_scope" if not scope_valid else "none"
    effect = {"base": 0, "tool_augmented": 100, "budget_extended": 100, "memory_reset": -200, "policy_restricted": -300}[variant]
    checks = dict(CHECKS)
    if capability_gap:
        checks["focused_tests"] = "fail"
    if not scope_valid:
        checks["diff_hygiene"] = "fail"
    observation = {
        "record_type": "self_model_repository_observation",
        "trajectory_id": f"trajectory-{trajectory:02d}",
        "task_family": f"family-{trajectory % 5}",
        "split": split,
        "variant": variant,
        "horizon_step": 1,
        "predicted_success_probability_milli": 300 if failed else 900,
        "predicted_limitation": limitation,
        "predicted_variant_effect_milli": effect,
        "prior_belief_milli": 500,
        "posterior_belief_milli": 300 if failed else 700,
        "validator_update_direction": "decrease" if failed else "increase",
        "check_results": checks,
        "scope_valid": scope_valid,
        "provenance_valid": True,
        "timed_out": False,
        "budget_exhausted": False,
        "capability_gap": capability_gap,
        "validator_limitation": limitation,
        "actual_variant_effect_milli": effect,
        "latency_ms": 700 if failed else 500,
        "compute_units": 70 if failed else 50,
        "tool_calls": 3 if failed else 1,
        "attempts": 2 if failed else 1,
        "prediction_locked_before_outcome": True,
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "network_access": False,
    }
    observation["validator_observation_digest"] = digest_json(observation)
    return observation


def _capture_records(source_type: str = SMOKE_SOURCE) -> list[dict]:
    manifest = _manifest(source_type)
    return [manifest, *[_observation(0, "fit", variant) for variant in VARIANTS]]


def _live_capture_records() -> list[dict]:
    manifest = _manifest(LIVE_SOURCE)
    observations = []
    trajectory = 0
    for split, count in (("fit", 24), ("tune", 12), ("assessment", 24)):
        for _ in range(count):
            observations.extend(_observation(trajectory, split, variant) for variant in VARIANTS)
            trajectory += 1
    return [manifest, *observations]


class RepositoryChangeCaptureTests(unittest.TestCase):
    def test_checked_in_capture_fixture_round_trips_to_contract_smoke(self):
        records = convert("experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl")
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.jsonl"
            write_jsonl(input_path, records)
            manifest, trials = load_input(input_path)
        result = evaluate(manifest, trials)
        self.assertEqual(result["classification"], "ContractSmokeOnly")
        self.assertFalse(result["scientific_evidence"])
        self.assertEqual(len(trials), 5)

    def test_private_contract_helper_reaches_candidate_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            input_path = Path(directory) / "input.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            write_jsonl(input_path, _convert_for_contract_test(capture_path))
            manifest, trials = load_input(input_path)
        result = evaluate(manifest, trials)
        self.assertEqual(result["classification"], "LocalDevelopmentSelfModelBenchmarkCandidate")
        self.assertEqual(result["decision"], "keep_candidate")
        self.assertTrue(all(result["gates"].values()))
        self.assertEqual(result["trial_count"], 300)

    def test_public_live_conversion_requires_separate_release(self):
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            with self.assertRaisesRegex(CaptureError, "separately authorized release"):
                convert(capture_path)

    def test_cli_live_conversion_requires_separate_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture_path = root / "capture.jsonl"
            output_path = root / "input.jsonl"
            write_jsonl(capture_path, _live_capture_records())
            with patch.object(
                sys,
                "argv",
                ["capture", "--input", str(capture_path), "--output", str(output_path)],
            ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(capture_main(), 2)
            self.assertFalse(output_path.exists())

    def test_live_shaped_capture_passes_corpus_preflight_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, _live_capture_records())
            report = preflight_capture(path)
        validate_report(report)
        self.assertEqual(report["status"], "preflight_valid")
        self.assertEqual(report["claim_ceiling"], CLAIM_CEILING)
        self.assertFalse(report["scientific_evidence"])
        self.assertEqual(report["counts"]["trajectory_count"], 60)
        self.assertEqual(report["counts"]["split_trajectory_counts"], {"fit": 24, "tune": 12, "assessment": 24})

    def test_smoke_capture_is_rejected_without_being_malformed(self):
        fixture = Path("experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl")
        report = preflight_capture(fixture)
        self.assertEqual(report["status"], "preflight_rejected")
        self.assertIn("source_type_is_live", report["failure_reasons"])
        self.assertIn("minimum_trajectory_count", report["failure_reasons"])
        self.assertFalse(report["scientific_evidence"])

    def test_cli_preflight_emits_validated_rejection_report(self):
        fixture = Path("experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "preflight.json"
            with patch.object(
                sys,
                "argv",
                ["capture-preflight", "--input", str(fixture), "--output", str(output)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(preflight_main(), 0)
            report = json.loads(output.read_text(encoding="utf-8"))
        validate_report(report)
        self.assertEqual(report["status"], "preflight_rejected")

    def test_missing_variant_is_rejected_at_corpus_boundary(self):
        records = _live_capture_records()
        records.pop(1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, records)
            report = preflight_capture(path)
        self.assertFalse(report["valid"])
        self.assertIn("complete_variant_sets", report["failure_reasons"])
        self.assertIn("horizon_sets_match_across_variants", report["failure_reasons"])

    def test_cross_split_trajectory_is_rejected_at_corpus_boundary(self):
        records = _live_capture_records()
        records[1]["split"] = "tune"
        records[1]["validator_observation_digest"] = digest_json(
            {key: value for key, value in records[1].items() if key != "validator_observation_digest"}
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, records)
            report = preflight_capture(path)
        self.assertFalse(report["valid"])
        self.assertIn("trajectory_split_isolation", report["failure_reasons"])
        self.assertIn("trajectory_metadata_is_constant", report["failure_reasons"])

    def test_malformed_capture_fails_closed_before_report(self):
        records = _capture_records(LIVE_SOURCE)
        records[1]["prediction_locked_before_outcome"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, records)
            with self.assertRaises(PreflightError):
                preflight_capture(path)

    def test_observation_validator_rejects_non_object_manifests_with_domain_errors(self):
        # State slice: verified-self-model-benchmark-repository-capture-v1.
        observation = _observation(0, "fit", "base")
        for malformed in (None, [], "not-an-object", 1):
            with self.subTest(value_type=type(malformed).__name__):
                with self.assertRaisesRegex(CaptureError, "capture manifest must be an object"):
                    validate_observation(observation, malformed)

    def test_validator_digest_tampering_is_rejected(self):
        records = _capture_records()
        records[1]["posterior_belief_milli"] = 701
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, records)
            with self.assertRaisesRegex(CaptureError, "digest mismatch"):
                load_capture(path)

    def test_raw_and_authority_fields_fail_closed(self):
        records = _capture_records()
        records[1]["model_output"] = "forbidden"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, records)
            with self.assertRaises(CaptureError):
                load_capture(path)
        records = _capture_records()
        records[0]["authority_granted"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "capture.jsonl"
            write_jsonl(path, records)
            with self.assertRaisesRegex(CaptureError, "authority_granted"):
                load_capture(path)

    # State slice: verified-self-model-benchmark-repository-capture-v1.
    def test_each_resource_budget_rejects_overage_after_digest_rewrite(self):
        budget_cases = (
            ("latency_ms", "max_latency_ms", "latency budget exceeded"),
            ("compute_units", "max_compute_units", "compute budget exceeded"),
            ("tool_calls", "max_tool_calls", "tool-call budget exceeded"),
            ("attempts", "max_attempts", "attempt budget exceeded"),
        )
        for observation_field, budget_field, error_message in budget_cases:
            with self.subTest(resource=observation_field):
                records = _capture_records()
                records[1][observation_field] = records[0]["budget"][budget_field] + 1
                records[1]["validator_observation_digest"] = digest_json(
                    {key: value for key, value in records[1].items() if key != "validator_observation_digest"}
                )
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "capture.jsonl"
                    write_jsonl(path, records)
                    with self.assertRaisesRegex(CaptureError, error_message):
                        load_capture(path)

    def test_cli_capture_benchmark_and_independent_validation(self):
        fixture = Path("experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input.jsonl"
            result_path = root / "result.json"
            with patch.object(sys, "argv", ["capture", "--input", str(fixture), "--output", str(input_path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(capture_main(), 0)
            with patch.object(sys, "argv", ["benchmark", "--input", str(input_path), "--output", str(result_path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(benchmark_main(), 0)
            with patch.object(sys, "argv", ["validate", str(result_path), "--input", str(input_path)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validate_main(), 0)


if __name__ == "__main__":
    unittest.main()
