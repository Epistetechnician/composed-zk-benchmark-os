import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from experiments.verified_metacognitive_control.protocol import (
    ProtocolError,
    digest_json,
    evaluate,
    load_input,
)
from experiments.verified_metacognitive_control.controller import recommend_control_action
from experiments.verified_metacognitive_control.repository_change_capture import (
    CaptureError,
    convert,
    derive_outcome,
    load_capture,
)
from experiments.verified_metacognitive_control.repository_change_validator import (
    ValidatorError,
    _run_command,
    _repository_root,
    _safe_environment,
    _provenance_valid,
    _scope_valid,
    validate_and_run as validate_validator_plan_and_run,
    validate_plan as validate_validator_plan,
)
from experiments.verified_metacognitive_control.corpus_preflight import (
    validate_plan as validate_corpus_plan,
)
from experiments.verified_metacognitive_control.paired_execution_join import (
    JoinError,
    join,
    load_validator_report,
    validate_agent_record,
    validate_validator_row,
    validate_execution_manifest,
)
from experiments.verified_metacognitive_control.validate_result import validate


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "fixtures" / "smoke_trials.jsonl"


class ProtocolTests(unittest.TestCase):
    @staticmethod
    def capture_manifest():
        return {
            "record_type": "capture_manifest",
            "schema_version": "verified-metacognitive-repository-observation-v1",
            "state_slice": "verified-metacognitive-control-repository-workflow-v1",
            "workflow_id": "repository-change-capture-test",
            "fixed_budget": True,
            "budget": {"max_latency_ms": 1000, "max_compute_units": 100, "max_tool_calls": 4, "max_attempts": 2},
            "arms": ["baseline", "self_report_control", "external_monitor_control", "shuffled_monitor_control"],
            "required_check_ids": ["format", "focused_tests", "contract_validation", "diff_hygiene", "claim_boundary"],
            "prediction_locked_before_assessment": True,
            "raw_reasoning_retained": False,
            "authority_granted": False,
            "network_access": False,
            "agent_execution_recorded": True,
            "validator_custody": True,
            "validator_report_digest": "a" * 64,
            "model_digest": "b" * 64,
            "runtime_digest": "c" * 64,
            "checker_digest": "d" * 64,
        }

    @staticmethod
    def observation(case_id="case-01", arm="baseline", **overrides):
        observation = {
            "record_type": "observation",
            "case_id": case_id,
            "task_family": "tests",
            "split": "fit",
            "arm": arm,
            "decision": "proceed",
            "monitor_score_milli": 900,
            "monitor_signal_source": "none" if arm == "baseline" else "external_telemetry",
            "check_results": {
                "format": "pass",
                "focused_tests": "pass",
                "contract_validation": "pass",
                "diff_hygiene": "pass",
                "claim_boundary": "pass",
            },
            "scope_valid": True,
            "provenance_valid": True,
            "timed_out": False,
            "budget_exhausted": False,
            "capability_gap": False,
            "safe_abstention": False,
            "latency_ms": 500,
            "compute_units": 50,
            "tool_calls": 1,
            "attempts": 1,
            "monitor_overhead_ms": 0,
            "monitor_compute_units": 0,
            "prediction_locked_before_assessment": True,
            "raw_reasoning_retained": False,
            "authority_granted": False,
            "network_access": False,
        }
        observation.update(overrides)
        return observation

    def test_smoke_is_paired_and_non_evidence(self):
        result = evaluate(load_input(FIXTURE))
        self.assertEqual(result["classification"], "ContractSmokeOnly")
        self.assertEqual(result["decision"], "not_evidence")
        self.assertTrue(result["coverage"]["all_arms_paired"])
        self.assertTrue(result["gates"]["no_authority"])
        self.assertTrue(result["gates"]["no_raw_reasoning"])
        self.assertTrue(result["gates"]["prediction_lock"])
        self.assertGreaterEqual(result["comparison"]["failure_reduction_absolute"], 0.15)

    def test_promotion_metrics_use_sealed_assessment_only(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        for record in records[1:]:
            if (
                record.get("arm") == "external_monitor_control"
                and record.get("split") == "assessment"
            ):
                record["outcome"] = "costly_failure"
                record["costly_failure"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assessment-only.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            result = evaluate(load_input(path))

        self.assertEqual(result["comparison"]["evaluation_split"], "assessment")
        self.assertEqual(result["comparison"]["failure_reduction_absolute"], -0.5)
        self.assertFalse(result["gates"]["costly_failure_reduction"])
        self.assertEqual(
            result["assessment_arm_summaries"]["external_monitor_control"]["n"],
            2,
        )

    def test_shuffled_negative_control_rejects_metric_passing_shuffled_arm(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        for record in records[1:]:
            if (
                record.get("arm") == "shuffled_monitor_control"
                and record.get("split") == "assessment"
                and record.get("case_id") == "task-08"
            ):
                record["outcome"] = "success"
                record["costly_failure"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shuffled-passing.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            result = evaluate(load_input(path))

        self.assertFalse(result["gates"]["shuffled_negative_control"])

    def test_raw_reasoning_is_rejected(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[1]["raw_reasoning_retained"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            with self.assertRaises(ProtocolError):
                load_input(path)

    def test_capture_rejects_non_finite_measurements(self):
        manifest = self.capture_manifest()
        observation = self.observation(latency_ms=float("inf"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "non-finite-capture.jsonl"
            path.write_text(
                "\n".join(json.dumps(record) for record in (manifest, observation)) + "\n"
            )
            with self.assertRaisesRegex(CaptureError, "latency_ms must be finite"):
                load_capture(path)

        observation = self.observation(monitor_score_milli=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boolean-monitor-score.jsonl"
            path.write_text(
                "\n".join(json.dumps(record) for record in (manifest, observation)) + "\n"
            )
            with self.assertRaisesRegex(CaptureError, "monitor score must be in \\[0, 1000\\]"):
                load_capture(path)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "non-object-capture.jsonl"
            path.write_text("[]\n")
            with self.assertRaisesRegex(CaptureError, "capture manifest must be an object"):
                load_capture(path)

    def test_join_rejects_non_finite_validator_measurements(self):
        row = {
            "record_type": "validator_observation",
            "case_id": "case-01",
            "task_family": "tests",
            "split": "fit",
            "arm": "baseline",
            "check_results": {
                "format": "pass",
                "focused_tests": "pass",
                "contract_validation": "pass",
                "diff_hygiene": "pass",
                "claim_boundary": "pass",
            },
            "scope_valid": True,
            "provenance_valid": True,
            "timed_out": False,
            "budget_exhausted": False,
            "capability_gap": False,
            "safe_abstention": False,
            "latency_ms": float("nan"),
            "compute_units": 50,
            "tool_calls": 1,
            "attempts": 1,
            "monitor_overhead_ms": 0,
            "monitor_compute_units": 0,
        }
        with self.assertRaisesRegex(JoinError, "latency_ms must be finite and nonnegative"):
            validate_validator_row(row)

    def test_authority_is_rejected(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[2]["authority_granted"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            with self.assertRaises(ProtocolError):
                load_input(path)

    def test_budget_violation_is_rejected(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[1]["latency_ms"] = 1001
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            with self.assertRaises(ProtocolError):
                load_input(path)

    def test_boolean_numeric_fields_are_rejected(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[1]["tool_calls"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boolean-tool-calls.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            with self.assertRaisesRegex(ProtocolError, "tool_calls must be nonnegative integer"):
                load_input(path)

        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[0]["budget"]["max_attempts"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "boolean-budget.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            with self.assertRaisesRegex(ProtocolError, "positive integer budget required: max_attempts"):
                load_input(path)

    def test_unpaired_arm_is_rejected_by_gate(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records = [record for record in records if not (record.get("record_type") == "trial" and record.get("case_id") == "task-08" and record.get("arm") == "shuffled_monitor_control")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unpaired.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            result = evaluate(load_input(path))
        self.assertFalse(result["gates"]["paired_arm_coverage"])

    def test_live_candidate_requires_scale_and_failing_shuffled_control(self):
        records = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
        records[0]["source_type"] = "live_workflow_capture"
        records[0].update(
            {
                "model_digest": "b" * 64,
                "runtime_digest": "c" * 64,
                "checker_digest": "d" * 64,
                "network_access": False,
                "agent_execution_recorded": True,
                "validator_custody": True,
                "validator_report_digest": "a" * 64,
            }
        )
        for trial in records[1:]:
            trial.update(
                {
                    "model_digest": "b" * 64,
                    "runtime_digest": "c" * 64,
                    "checker_digest": "d" * 64,
                    "network_access": False,
                    "monitor_score_milli": 900,
                }
            )
            trial["record_digest"] = digest_json(trial)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "small-live.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            result = evaluate(load_input(path))

        self.assertEqual(result["classification"], "LocalDevelopmentNoCandidate")
        self.assertEqual(result["decision"], "revert_candidate")
        self.assertEqual(result["claim_ceiling"], "Level0DesignNote")
        self.assertFalse(result["gates"]["promotion_structure"])
        self.assertTrue(result["gates"]["shuffled_negative_control"])
        self.assertEqual(result["promotion_structure"]["paired_task_count"], 8)
        self.assertEqual(result["promotion_structure"]["task_family_count"], 4)

    def test_repository_capture_derives_validator_owned_outcomes(self):
        manifest = self.capture_manifest()
        success = self.observation()
        costly = self.observation(case_id="case-02", scope_valid=False)
        safe_abstention = self.observation(
            case_id="case-03",
            decision="abstain",
            safe_abstention=True,
            check_results={
                "format": "not_run",
                "focused_tests": "not_run",
                "contract_validation": "pass",
                "diff_hygiene": "pass",
                "claim_boundary": "pass",
            },
        )
        self.assertEqual(derive_outcome(success), "success")
        self.assertEqual(derive_outcome(costly), "costly_failure")
        self.assertEqual(derive_outcome(safe_abstention), "safe_abstention")

        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "capture.jsonl"
            capture_path.write_text(
                "\n".join(json.dumps(record) for record in [manifest, success, costly]) + "\n"
            )
            records = convert(capture_path)
            output_path = Path(directory) / "experiment.jsonl"
            output_path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            bundle = load_input(output_path)

        self.assertEqual(bundle.manifest["source_type"], "live_workflow_capture")
        self.assertEqual(bundle.trials[0]["outcome"], "success")
        self.assertEqual(bundle.trials[1]["outcome"], "costly_failure")
        unsigned = dict(bundle.trials[0])
        declared_digest = unsigned.pop("record_digest")
        self.assertEqual(declared_digest, digest_json(unsigned))

    def test_repository_capture_accepts_canonical_json_key_order(self):
        manifest = self.capture_manifest()
        observation = self.observation()
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "sorted-capture.jsonl"
            capture_path.write_text(
                "\n".join(
                    json.dumps(record, sort_keys=True)
                    for record in (manifest, observation)
                )
                + "\n"
            )
            output_path = Path(directory) / "experiment.jsonl"
            output_path.write_text(
                "\n".join(
                    json.dumps(record, sort_keys=True)
                    for record in convert(capture_path)
                )
                + "\n"
            )
            bundle = load_input(output_path)

        self.assertEqual(bundle.trials[0]["case_id"], "case-01")
        self.assertEqual(bundle.trials[0]["outcome"], "success")

    def test_repository_capture_rejects_raw_output_and_requires_live_sample_floor(self):
        manifest = self.capture_manifest()
        bad = self.observation(raw_model_output="must not enter aggregate capture")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad-capture.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in [manifest, bad]) + "\n")
            with self.assertRaises(CaptureError):
                load_capture(path)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "small-capture.jsonl"
            path.write_text("\n".join(json.dumps(record) for record in [manifest, self.observation()]) + "\n")
            experiment_path = Path(directory) / "experiment.jsonl"
            experiment_path.write_text("\n".join(json.dumps(record) for record in convert(path)) + "\n")
            result = evaluate(load_input(experiment_path))
        self.assertEqual(result["classification"], "LocalDevelopmentNoCandidate")
        self.assertFalse(result["promotion_structure"]["minimum_paired_tasks"])
        self.assertFalse(result["promotion_structure"]["minimum_task_families"])
        self.assertFalse(result["promotion_structure"]["minimum_split_tasks"])

    def test_validator_plan_is_fixed_profile_and_scope_fail_closed(self):
        expected_base_revision = subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=Path.cwd(), text=True
        ).strip()
        plan = {
            "record_type": "validator_plan",
            "schema_version": "verified-metacognitive-repository-validator-plan-v1",
            "state_slice": "verified-metacognitive-control-repository-validator-v1",
            "workflow_id": "validator-plan-test",
            "root": str(Path.cwd()),
            "allowed_paths": ["experiments/verified_metacognitive_control"],
            "expected_base_revision": expected_base_revision,
            "check_profile": "zkbench_metacognitive_v1",
            "budget": {"max_latency_ms": 120000, "max_compute_units": 24000, "max_tool_calls": 12, "max_attempts": 2},
            "network_access": False,
            "authority_granted": False,
            "raw_reasoning_retained": False,
            "tasks": [
                {
                    "case_id": "task-01",
                    "task_family": "tests",
                    "split": "fit",
                    "arm": "baseline",
                    "decision": "proceed",
                    "monitor_score_milli": 900,
                    "monitor_signal_source": "none",
                }
            ],
        }
        validate_validator_plan(plan)
        boolean_budget_plan = json.loads(json.dumps(plan))
        boolean_budget_plan["budget"]["max_attempts"] = True
        with self.assertRaisesRegex(ValidatorError, "positive budget required: max_attempts"):
            validate_validator_plan(boolean_budget_plan)
        boolean_score_plan = json.loads(json.dumps(plan))
        boolean_score_plan["tasks"][0]["monitor_score_milli"] = True
        with self.assertRaisesRegex(ValidatorError, "monitor score out of range"):
            validate_validator_plan(boolean_score_plan)
        with patch(
            "experiments.verified_metacognitive_control.repository_change_validator._git_lines",
            return_value=(True, ["README.md"]),
        ):
            scope_valid, unexpected = _scope_valid(Path.cwd(), plan["allowed_paths"])
        self.assertFalse(scope_valid)
        self.assertTrue(unexpected)
        provenance_valid, actual_revision = _provenance_valid(Path.cwd(), plan["expected_base_revision"])
        self.assertTrue(provenance_valid)
        self.assertEqual(actual_revision, expected_base_revision)
        missing_command = _run_command(("command-that-does-not-exist",), Path.cwd(), 1)
        self.assertEqual(missing_command["status"], "fail")
        self.assertIsNone(missing_command["exit_code"])
        safe_environment = _safe_environment()
        self.assertEqual(safe_environment["CARGO_NET_OFFLINE"], "true")
        self.assertEqual(safe_environment["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(safe_environment["GIT_CONFIG_NOSYSTEM"], "1")

        unsafe = dict(plan)
        unsafe["check_profile"] = "arbitrary_shell"
        with self.assertRaises(ValidatorError):
            validate_validator_plan(unsafe)

        self.assertEqual(_repository_root(Path.cwd()), Path.cwd().resolve())
        unsafe_root = dict(plan)
        unsafe_root["root"] = tempfile.gettempdir()
        with patch(
            "experiments.verified_metacognitive_control.repository_change_validator._run_checks",
            side_effect=AssertionError("checks must not run outside a Git checkout"),
        ):
            with self.assertRaisesRegex(ValidatorError, "top-level of a Git checkout"):
                validate_validator_plan_and_run(unsafe_root)

    def test_corpus_preflight_rejects_small_unpaired_plan_without_evidence(self):
        plan = {
            "record_type": "corpus_plan",
            "schema_version": "verified-metacognitive-corpus-plan-v1",
            "state_slice": "verified-metacognitive-control-corpus-preflight-v1",
            "workflow_id": "corpus-plan-test",
            "arms": ["baseline", "self_report_control", "external_monitor_control", "shuffled_monitor_control", "oracle_control"],
            "authority_granted": False,
            "network_access": False,
            "raw_reasoning_retained": False,
            "tasks": [
                {"case_id": "task-01", "task_family": "tests", "split": "fit", "arm": "baseline"},
                {"case_id": "task-01", "task_family": "tests", "split": "fit", "arm": "external_monitor_control"},
            ],
        }
        report = validate_corpus_plan(plan)
        self.assertFalse(report["valid"])
        self.assertFalse(report["checks"]["minimum_paired_tasks"])
        self.assertFalse(report["checks"]["all_promotion_arms_paired"])
        self.assertEqual(report["claim_ceiling"], "LocalDevelopmentCorpusPreflightOnly")

    def test_corpus_preflight_rejects_raw_plan_fields(self):
        plan = {
            "record_type": "corpus_plan",
            "schema_version": "verified-metacognitive-corpus-plan-v1",
            "state_slice": "verified-metacognitive-control-corpus-preflight-v1",
            "workflow_id": "corpus-plan-test",
            "arms": ["baseline", "self_report_control", "external_monitor_control", "shuffled_monitor_control", "oracle_control"],
            "authority_granted": False,
            "network_access": False,
            "raw_reasoning_retained": False,
            "prompt": "forbidden",
            "tasks": [],
        }
        with self.assertRaises(ValueError):
            validate_corpus_plan(plan)

    def test_paired_execution_join_requires_complete_digest_bound_agent_rows(self):
        arms = ["baseline", "self_report_control", "external_monitor_control", "shuffled_monitor_control", "oracle_control"]
        validator_rows = []
        agent_rows = []
        for index, arm in enumerate(arms, 1):
            source = {
                "baseline": "none",
                "self_report_control": "self_report",
                "external_monitor_control": "external_telemetry",
                "shuffled_monitor_control": "shuffled_telemetry",
                "oracle_control": "oracle",
            }[arm]
            validator_rows.append(
                {
                    "record_type": "validator_observation",
                    "case_id": "task-01",
                    "task_family": "tests",
                    "split": "fit",
                    "arm": arm,
                    "check_results": {
                        "format": "pass",
                        "focused_tests": "pass",
                        "contract_validation": "pass",
                        "diff_hygiene": "pass",
                        "claim_boundary": "pass",
                    },
                    "scope_valid": True,
                    "provenance_valid": True,
                    "timed_out": False,
                    "budget_exhausted": False,
                    "capability_gap": False,
                    "safe_abstention": False,
                    "latency_ms": 500,
                    "compute_units": 50,
                    "tool_calls": 1,
                    "attempts": 1,
                    "monitor_overhead_ms": 0,
                    "monitor_compute_units": 0,
                }
            )
            agent_rows.append(
                {
                    "record_type": "agent_execution_record",
                    "workflow_id": "paired-join-test",
                    "case_id": "task-01",
                    "task_family": "tests",
                    "split": "fit",
                    "arm": arm,
                    "decision": "proceed",
                    "monitor_score_milli": 1000 if arm == "oracle_control" else 900,
                    "monitor_signal_source": source,
                    "candidate_workspace_digest": digest_json({"workspace": index}),
                    "agent_run_digest": digest_json({"run": index}),
                    "task_spec_digest": digest_json({"task": "task-01"}),
                    "controller_config_digest": digest_json({"controller": "v1"}),
                    "execution_plan_digest": "e" * 64,
                    "source_corpus_digest": "f" * 64,
                    "task_digest": digest_json({"task": "task-01"}),
                    "arm_digest": digest_json({"arm": arm}),
                    "prediction_locked_before_assessment": True,
                    "raw_reasoning_retained": False,
                    "authority_granted": False,
                    "network_access": False,
                }
            )
        validator_report = {
            "record_type": "validator_report",
            "schema_version": "verified-metacognitive-repository-validator-report-v1",
            "state_slice": "verified-metacognitive-control-repository-validator-v1",
            "capture_state_slice": "verified-metacognitive-control-repository-workflow-v1",
            "workflow_id": "paired-join-test",
            "validator_custody": True,
            "agent_execution_recorded": False,
            "authority_granted": False,
            "network_access": False,
            "raw_reasoning_retained": False,
            "rows": validator_rows,
        }
        validator_report["report_digest"] = digest_json(validator_report)
        execution_manifest = {
            "record_type": "agent_execution_manifest",
            "schema_version": "verified-metacognitive-agent-execution-v1",
            "state_slice": "verified-metacognitive-control-paired-execution-v1",
            "workflow_id": "paired-join-test",
            "fixed_budget": True,
            "budget": {"max_latency_ms": 1000, "max_compute_units": 100, "max_tool_calls": 4, "max_attempts": 2},
            "arms": arms,
            "required_check_ids": ["format", "focused_tests", "contract_validation", "diff_hygiene", "claim_boundary"],
            "prediction_locked_before_assessment": True,
            "agent_execution_recorded": True,
            "validator_custody": True,
            "validator_report_digest": validator_report["report_digest"],
            "execution_plan_digest": "e" * 64,
            "model_digest": "b" * 64,
            "runtime_digest": "c" * 64,
            "checker_digest": "d" * 64,
            "raw_reasoning_retained": False,
            "authority_granted": False,
            "network_access": False,
        }
        validate_execution_manifest(execution_manifest)
        boolean_agent = dict(agent_rows[0])
        boolean_agent["monitor_score_milli"] = True
        with self.assertRaisesRegex(JoinError, "agent monitor score out of range"):
            validate_agent_record(boolean_agent, execution_manifest)
        records = join(validator_report, execution_manifest, tuple(agent_rows))
        self.assertEqual(records[0]["record_type"], "capture_manifest")
        self.assertTrue(records[0]["agent_execution_recorded"])
        with tempfile.TemporaryDirectory() as directory:
            capture_path = Path(directory) / "joined.jsonl"
            capture_path.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            converted_path = Path(directory) / "converted.jsonl"
            converted_path.write_text("\n".join(json.dumps(record) for record in convert(capture_path)) + "\n")
            bundle = load_input(converted_path)
        self.assertEqual(len(bundle.trials), 5)
        self.assertTrue(all(trial["prediction_locked_before_assessment"] for trial in bundle.trials))

        incomplete = tuple(agent_rows[:-1])
        with self.assertRaises(JoinError):
            join(validator_report, execution_manifest, incomplete)

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "validator.json"
            report_path.write_text(json.dumps(validator_report))
            with self.assertRaises(JoinError):
                load_validator_report(report_path, "e" * 64)

            malformed_report = json.loads(json.dumps(validator_report))
            malformed_report["rows"][0].pop("task_family")
            unsigned = dict(malformed_report)
            unsigned.pop("report_digest")
            malformed_report["report_digest"] = digest_json(unsigned)
            report_path.write_text(json.dumps(malformed_report))
            with self.assertRaisesRegex(JoinError, "validator row missing task_family"):
                load_validator_report(report_path, malformed_report["report_digest"])

        mismatched_agent_rows = [dict(row) for row in agent_rows]
        mismatched_agent_rows[0]["task_family"] = "different-family"
        with self.assertRaisesRegex(JoinError, "task family mismatch"):
            join(validator_report, execution_manifest, tuple(mismatched_agent_rows))

    def test_validator_returns_json_for_protocol_error(self):
        invalid_input = ROOT / "fixtures" / "repository_observations_smoke.jsonl"
        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            result_path.write_text("{}\n")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.verified_metacognitive_control.validate_result",
                    str(result_path),
                    "--input",
                    str(invalid_input),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertFalse(payload["valid"])
        self.assertIn("first record must be a manifest", payload["errors"])

    def test_run_experiment_returns_structured_error_for_non_object_input(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "non-object.jsonl"
            output_path = Path(directory) / "result.json"
            input_path.write_text("[]\n")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.verified_metacognitive_control.run_experiment",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("protocol_error: manifest must be an object", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_validator_rejects_non_object_result(self):
        self.assertIn(
            "result must be a JSON object",
            validate([]),
        )

    def test_validator_rejects_non_object_gates(self):
        errors = validate({"gates": []})
        self.assertIn("gates must be a JSON object", errors)

    def test_candidate_requires_campaign_verification(self):
        result = evaluate(load_input(FIXTURE))
        result.update(
            {
                "source_type": "live_workflow_capture",
                "classification": "LocalDevelopmentCandidate",
                "decision": "keep_candidate",
                "claim_ceiling": "LocalDevelopmentMetacognitiveControlCandidate",
            }
        )
        unsigned = dict(result)
        unsigned.pop("result_digest")
        result["result_digest"] = digest_json(unsigned)

        self.assertIn(
            "keep_candidate requires a valid campaign verification report",
            validate(result),
        )
        self.assertEqual(validate(result, allow_campaign_verification_pending=True), [])
        self.assertEqual(validate(result, campaign_verified=True), [])

    def test_cli_requires_recomputation_input(self):
        result = evaluate(load_input(FIXTURE))
        result["workflow_id"] = "forged-without-input"
        unsigned = dict(result)
        unsigned.pop("result_digest")
        result["result_digest"] = digest_json(unsigned)
        with tempfile.TemporaryDirectory() as directory:
            result_path = Path(directory) / "result.json"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "experiments.verified_metacognitive_control.validate_result",
                    str(result_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertFalse(payload["valid"])
        self.assertTrue(any("--input is required" in error for error in payload["errors"]))

    def test_controller_returns_the_four_bounded_actions(self):
        common = {
            "monitor_available": True,
            "required_checks_green": True,
            "evidence_complete": True,
            "in_scope": True,
            "high_risk": False,
            "validator_failure_present": False,
            "attempts_remaining": 1,
            "tool_calls_remaining": 2,
        }
        self.assertEqual(recommend_control_action(monitor_score_milli=900, **common), "proceed")
        self.assertEqual(recommend_control_action(monitor_score_milli=700, **common), "seek_tool")
        self.assertEqual(recommend_control_action(monitor_score_milli=900, validator_failure_present=True, **{k: v for k, v in common.items() if k != "validator_failure_present"}), "revise")
        self.assertEqual(recommend_control_action(monitor_score_milli=900, in_scope=False, **{k: v for k, v in common.items() if k != "in_scope"}), "abstain")

    def test_controller_rejects_invalid_score(self):
        with self.assertRaises(ValueError):
            recommend_control_action(
                monitor_score_milli=1001,
                monitor_available=True,
                required_checks_green=True,
                evidence_complete=True,
                in_scope=True,
                high_risk=False,
                validator_failure_present=False,
                attempts_remaining=1,
                tool_calls_remaining=1,
            )

        with self.assertRaises(ValueError):
            recommend_control_action(
                monitor_score_milli=True,
                monitor_available=True,
                required_checks_green=True,
                evidence_complete=True,
                in_scope=True,
                high_risk=False,
                validator_failure_present=False,
                attempts_remaining=1,
                tool_calls_remaining=1,
            )

        with self.assertRaises(ValueError):
            recommend_control_action(
                monitor_score_milli=900,
                monitor_available=True,
                required_checks_green=True,
                evidence_complete=True,
                in_scope=True,
                high_risk=False,
                validator_failure_present=False,
                attempts_remaining=True,
                tool_calls_remaining=1,
            )

        with self.assertRaises(ValueError):
            recommend_control_action(
                monitor_score_milli=900,
                monitor_available=1,
                required_checks_green=True,
                evidence_complete=True,
                in_scope=True,
                high_risk=False,
                validator_failure_present=False,
                attempts_remaining=1,
                tool_calls_remaining=1,
            )


if __name__ == "__main__":
    unittest.main()
