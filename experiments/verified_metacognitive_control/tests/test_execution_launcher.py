import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.verified_metacognitive_control.corpus_execution_launcher import (
    CLAIM_CEILING,
    LauncherError,
    build_execution_plan,
    main,
    validate_execution_plan,
)
from experiments.verified_metacognitive_control.corpus_preflight import (
    PreflightError,
    validate_plan as validate_corpus_plan,
)
from experiments.verified_metacognitive_control.campaign_verifier import (
    CampaignVerificationError,
    main as campaign_main,
    verify_campaign,
)
from experiments.verified_metacognitive_control.campaign_ledger import (
    CampaignLedgerError,
    append_event,
    build_verified_ledger,
    initialize_ledger,
    main as ledger_main,
    validate_ledger,
)
from experiments.verified_metacognitive_control.campaign_review import (
    CampaignReviewError,
    build_review_packet,
    main as review_main,
    validate_review_packet,
)
from experiments.verified_metacognitive_control.campaign_review_decision import (
    CampaignReviewDecisionError,
    main as review_decision_main,
    record_review_decision,
    validate_review_decision,
)
from experiments.verified_metacognitive_control.sealed_pilot_preflight import (
    SealedPilotPreflightError,
    build_sealed_pilot_preflight,
    main as sealed_pilot_main,
    validate_preflight,
)
from experiments.verified_metacognitive_control.fresh_corpus_admission import (
    FreshCorpusAdmissionError,
    build_admission,
    main as fresh_corpus_admission_main,
    validate_admission,
)
from experiments.verified_metacognitive_control.repository_change_validator import (
    ValidatorError,
    validate_plan as validate_validator_plan,
)
from experiments.verified_metacognitive_control.sealed_pilot_execution_request import (
    SealedPilotExecutionRequestError,
    build_execution_request,
    main as sealed_pilot_execution_request_main,
    validate_execution_request,
)
from experiments.verified_metacognitive_control.execution_record_validator import (
    ExecutionRecordError,
    validate_plan_bound_records,
)
from experiments.verified_metacognitive_control.paired_execution_join import (
    JoinError,
    join_files,
    validate_agent_record,
    validate_execution_manifest,
    validate_validator_row,
)
from experiments.verified_metacognitive_control.protocol import PROMOTION_ARMS, digest_json, evaluate, load_input
from experiments.verified_metacognitive_control.repository_change_capture import convert


def valid_corpus_plan() -> dict:
    tasks = []
    split_sizes = (("fit", 24), ("tune", 12), ("assessment", 24))
    family_index = 0
    for split, count in split_sizes:
        for index in range(1, count + 1):
            case_id = f"{split}-{index:02d}"
            family = f"family-{family_index % 5}"
            family_index += 1
            for arm in PROMOTION_ARMS:
                tasks.append(
                    {
                        "record_type": "corpus_task",
                        "case_id": case_id,
                        "task_family": family,
                        "split": split,
                        "arm": arm,
                    }
                )
    return {
        "record_type": "corpus_plan",
        "schema_version": "verified-metacognitive-corpus-plan-v1",
        "state_slice": "verified-metacognitive-control-corpus-preflight-v1",
        "workflow_id": "launcher-test-workflow",
        "arms": list(PROMOTION_ARMS),
        "task_spec_digest": digest_json({"spec": "repository-change-v1"}),
        "controller_config_digest": digest_json({"controller": "fixed-v1"}),
        "arm_digests": {
            arm: digest_json({"arm": arm, "config": "promotion-v1"})
            for arm in PROMOTION_ARMS
        },
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "tasks": tasks,
    }


class ExecutionLauncherTests(unittest.TestCase):
    def test_all_cli_contract_validators_reject_non_object_inputs(self):
        validators = (
            ("corpus", validate_corpus_plan, PreflightError),
            ("execution", validate_execution_plan, LauncherError),
            ("validator", validate_validator_plan, ValidatorError),
            ("sealed_pilot", validate_preflight, SealedPilotPreflightError),
            ("ledger", validate_ledger, CampaignLedgerError),
            ("review", validate_review_packet, CampaignReviewError),
            ("review_decision", validate_review_decision, CampaignReviewDecisionError),
            ("admission", validate_admission, FreshCorpusAdmissionError),
            ("execution_request", validate_execution_request, SealedPilotExecutionRequestError),
            ("execution_manifest", validate_execution_manifest, JoinError),
            ("validator_row", validate_validator_row, JoinError),
        )
        for value in ([], "invalid", None):
            for name, validator, error_type in validators:
                with self.subTest(value=value, validator=name):
                    with self.assertRaises(error_type):
                        validator(value)
        with self.assertRaises(JoinError):
            validate_agent_record([], {})

    def test_builds_300_plan_only_rows_with_bindings(self):
        plan = build_execution_plan(valid_corpus_plan())
        validate_execution_plan(plan)
        self.assertEqual(plan["planned_execution_count"], 300)
        self.assertEqual(plan["paired_task_count"], 60)
        self.assertEqual(plan["launch_status"], "planned_not_run")
        self.assertEqual(plan["claim_ceiling"], CLAIM_CEILING)
        self.assertFalse(plan["agent_execution_recorded"])
        self.assertEqual(len(plan["rows"]), 300)
        self.assertEqual({row["status"] for row in plan["rows"]}, {"planned_not_run"})
        self.assertEqual({row["task_spec_digest"] for row in plan["rows"]}, {plan["task_spec_digest"]})
        self.assertEqual(
            {row["controller_config_digest"] for row in plan["rows"]},
            {plan["controller_config_digest"]},
        )
        for arm in PROMOTION_ARMS:
            self.assertEqual(sum(row["arm"] == arm for row in plan["rows"]), 60)

    def test_rejects_underpowered_or_mismatched_corpus(self):
        corpus = valid_corpus_plan()
        corpus["tasks"] = corpus["tasks"][:-1]
        with self.assertRaises(LauncherError):
            build_execution_plan(corpus)

        corpus = valid_corpus_plan()
        corpus["tasks"][1]["task_family"] = "different-family"
        with self.assertRaises(LauncherError):
            build_execution_plan(corpus)

    def test_cli_writes_and_revalidates_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "corpus.json"
            output_path = root / "execution-plan.json"
            input_path.write_text(json.dumps(valid_corpus_plan()), encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                ["corpus_execution_launcher", "--input", str(input_path), "--output", str(output_path)],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            plan = json.loads(output_path.read_text(encoding="utf-8"))
            validate_execution_plan(plan)
            self.assertEqual(plan["planned_execution_count"], 300)

    def test_cli_rejects_non_object_corpus_plan_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "invalid-corpus.json"
            output_path = root / "execution-plan.json"
            input_path.write_text("[]\n", encoding="utf-8")
            stderr = io.StringIO()
            with patch.object(
                sys,
                "argv",
                ["corpus_execution_launcher", "--input", str(input_path), "--output", str(output_path)],
            ), contextlib.redirect_stderr(stderr):
                self.assertEqual(main(), 2)
            self.assertIn("execution_launch_error: corpus plan must be an object", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_plan_bound_validator_requires_complete_digest_bound_coverage(self):
        plan = build_execution_plan(valid_corpus_plan())
        manifest = {
            "record_type": "agent_execution_manifest",
            "workflow_id": plan["workflow_id"],
            "execution_plan_digest": plan["plan_digest"],
        }
        records = []
        for planned in plan["rows"]:
            records.append(
                {
                    "record_type": "agent_execution_record",
                    "workflow_id": plan["workflow_id"],
                    "case_id": planned["case_id"],
                    "task_family": planned["task_family"],
                    "split": planned["split"],
                    "arm": planned["arm"],
                    "execution_plan_digest": plan["plan_digest"],
                    "source_corpus_digest": planned["source_corpus_digest"],
                    "task_digest": planned["task_digest"],
                    "arm_digest": planned["arm_digest"],
                    "task_spec_digest": planned["task_spec_digest"],
                    "controller_config_digest": planned["controller_config_digest"],
                }
            )
        validate_plan_bound_records(plan, manifest, records)

        with self.assertRaises(ExecutionRecordError):
            validate_plan_bound_records(plan, manifest, records[:-1])

        tampered = [dict(record) for record in records]
        tampered[0]["task_digest"] = "0" * 64
        with self.assertRaisesRegex(ExecutionRecordError, "binding mismatch"):
            validate_plan_bound_records(plan, manifest, tampered)

    def test_plan_bound_bundle_reaches_join_only_with_full_300_row_coverage(self):
        plan = build_execution_plan(valid_corpus_plan())
        signal_sources = {
            "baseline": "none",
            "self_report_control": "self_report",
            "external_monitor_control": "external_telemetry",
            "shuffled_monitor_control": "shuffled_telemetry",
            "oracle_control": "oracle",
        }
        validator_rows = []
        agent_rows = []
        for ordinal, planned in enumerate(plan["rows"], start=1):
            controlled_costly_failure = (
                planned["split"] == "assessment"
                and planned["arm"] in {"baseline", "shuffled_monitor_control"}
            )
            validator_rows.append(
                {
                    "record_type": "validator_observation",
                    "case_id": planned["case_id"],
                    "task_family": planned["task_family"],
                    "split": planned["split"],
                    "arm": planned["arm"],
                    "check_results": {
                        "format": "pass",
                        "focused_tests": "pass",
                        "contract_validation": "pass",
                        "diff_hygiene": "pass",
                        "claim_boundary": "pass",
                    },
                    "scope_valid": not controlled_costly_failure,
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
                    "workflow_id": plan["workflow_id"],
                    "case_id": planned["case_id"],
                    "task_family": planned["task_family"],
                    "split": planned["split"],
                    "arm": planned["arm"],
                    "decision": "proceed",
                    "monitor_score_milli": 900,
                    "monitor_signal_source": signal_sources[planned["arm"]],
                    "candidate_workspace_digest": digest_json({"workspace": ordinal}),
                    "agent_run_digest": digest_json({"run": ordinal}),
                    "execution_plan_digest": plan["plan_digest"],
                    "source_corpus_digest": planned["source_corpus_digest"],
                    "task_digest": planned["task_digest"],
                    "arm_digest": planned["arm_digest"],
                    "task_spec_digest": planned["task_spec_digest"],
                    "controller_config_digest": planned["controller_config_digest"],
                    "prediction_locked_before_assessment": True,
                    "raw_reasoning_retained": False,
                    "authority_granted": False,
                    "network_access": False,
                }
            )
        report = {
            "record_type": "validator_report",
            "schema_version": "verified-metacognitive-repository-validator-report-v1",
            "state_slice": "verified-metacognitive-control-repository-validator-v1",
            "capture_state_slice": "verified-metacognitive-control-repository-workflow-v1",
            "workflow_id": plan["workflow_id"],
            "validator_custody": True,
            "agent_execution_recorded": False,
            "authority_granted": False,
            "network_access": False,
            "raw_reasoning_retained": False,
            "rows": validator_rows,
        }
        report["report_digest"] = digest_json(report)
        manifest = {
            "record_type": "agent_execution_manifest",
            "schema_version": "verified-metacognitive-agent-execution-v1",
            "state_slice": "verified-metacognitive-control-paired-execution-v1",
            "workflow_id": plan["workflow_id"],
            "fixed_budget": True,
            "budget": {"max_latency_ms": 1000, "max_compute_units": 100, "max_tool_calls": 4, "max_attempts": 2},
            "arms": list(PROMOTION_ARMS),
            "required_check_ids": ["format", "focused_tests", "contract_validation", "diff_hygiene", "claim_boundary"],
            "prediction_locked_before_assessment": True,
            "agent_execution_recorded": True,
            "validator_custody": True,
            "validator_report_digest": report["report_digest"],
            "execution_plan_digest": plan["plan_digest"],
            "model_digest": "b" * 64,
            "runtime_digest": "c" * 64,
            "checker_digest": "d" * 64,
            "raw_reasoning_retained": False,
            "authority_granted": False,
            "network_access": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "execution-plan.json"
            report_path = root / "validator-report.json"
            agent_path = root / "agent-records.jsonl"
            capture_path = root / "capture.jsonl"
            protocol_path = root / "protocol-input.jsonl"
            result_path = root / "result.json"
            verification_path = root / "verification.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            report_path.write_text(json.dumps(report), encoding="utf-8")
            agent_path.write_text(
                "\n".join(json.dumps(record) for record in [manifest, *agent_rows]) + "\n",
                encoding="utf-8",
            )
            joined = join_files(report_path, agent_path, plan_path)
            capture_path.write_text(
                "\n".join(json.dumps(record) for record in joined) + "\n",
                encoding="utf-8",
            )
            protocol_records = convert(capture_path)
            protocol_path.write_text(
                "\n".join(json.dumps(record) for record in protocol_records) + "\n",
                encoding="utf-8",
            )
            result = evaluate(load_input(protocol_path))
            result_path.write_text(json.dumps(result), encoding="utf-8")
            verification = verify_campaign(
                plan_path,
                report_path,
                agent_path,
                capture_path,
                protocol_path,
                result_path,
            )
            verification_path.write_text(json.dumps(verification), encoding="utf-8")
            with patch.object(
                sys,
                "argv",
                [
                    "campaign_verifier",
                    "--execution-plan",
                    str(plan_path),
                    "--validator-report",
                    str(report_path),
                    "--agent-records",
                    str(agent_path),
                    "--capture",
                    str(capture_path),
                    "--protocol-input",
                    str(protocol_path),
                    "--result",
                    str(result_path),
                    "--output",
                    str(verification_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(campaign_main(), 0)
            cli_verification = json.loads(verification_path.read_text(encoding="utf-8"))
            ledger = build_verified_ledger(
                plan_path,
                report_path,
                agent_path,
                capture_path,
                protocol_path,
                result_path,
                verification_path,
            )
            validate_ledger(ledger)
            ledger_path = root / "ledger.json"
            with patch.object(
                sys,
                "argv",
                [
                    "campaign_ledger",
                    "--execution-plan",
                    str(plan_path),
                    "--validator-report",
                    str(report_path),
                    "--agent-records",
                    str(agent_path),
                    "--capture",
                    str(capture_path),
                    "--protocol-input",
                    str(protocol_path),
                    "--result",
                    str(result_path),
                    "--campaign-verification",
                    str(verification_path),
                    "--output",
                    str(ledger_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ledger_main(), 0)
            cli_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            packet = build_review_packet(result_path, verification_path, ledger_path)
            validate_review_packet(packet)
            packet_path = root / "review-packet.json"
            with patch.object(
                sys,
                "argv",
                [
                    "campaign_review",
                    "--result",
                    str(result_path),
                    "--campaign-verification",
                    str(verification_path),
                    "--campaign-ledger",
                    str(ledger_path),
                    "--output",
                    str(packet_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(review_main(), 0)
            cli_packet = json.loads(packet_path.read_text(encoding="utf-8"))
            review_decision_path = root / "review-decision.json"
            decision = record_review_decision(
                packet,
                packet["recommended_disposition"],
                "operator-ref-1",
                "reviewed verified artifact chain and bounded disposition",
            )
            validate_review_decision(decision)
            with patch.object(
                sys,
                "argv",
                [
                    "campaign_review_decision",
                    "--review-packet",
                    str(packet_path),
                    "--decision",
                    packet["recommended_disposition"],
                    "--reviewer-ref",
                    "operator-ref-1",
                    "--notes",
                    "reviewed verified artifact chain and bounded disposition",
                    "--output",
                    str(review_decision_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(review_decision_main(), 0)
            cli_decision = json.loads(review_decision_path.read_text(encoding="utf-8"))
            self.assertEqual(decision["review_status"], "reviewed")
            self.assertTrue(decision["reviewed"])
            self.assertFalse(decision["human_review_required"])
            self.assertFalse(decision["accepted"])
            self.assertFalse(decision["review_notes_retained"])
            self.assertNotIn("reviewed verified artifact chain", json.dumps(decision))
            self.assertEqual(cli_decision, decision)
            decision_path = root / "review-decision.json"
            decision_path.write_text(json.dumps(decision), encoding="utf-8")
            sealed_pilot_path = root / "sealed-pilot-preflight.json"
            preflight = build_sealed_pilot_preflight(
                plan_path,
                report_path,
                agent_path,
                capture_path,
                protocol_path,
                result_path,
                verification_path,
                ledger_path,
                packet_path,
                decision_path,
            )
            validate_preflight(preflight)
            self.assertEqual(preflight["preflight_status"], "ready_for_sealed_pilot_authorization")
            self.assertIsNone(preflight["block_reason"])
            self.assertEqual(preflight["execution_status"], "not_started")
            self.assertEqual(preflight["authorization_status"], "not_granted")
            self.assertFalse(preflight["accepted"])
            with patch.object(
                sys,
                "argv",
                [
                    "sealed_pilot_preflight",
                    "--execution-plan",
                    str(plan_path),
                    "--validator-report",
                    str(report_path),
                    "--agent-records",
                    str(agent_path),
                    "--capture",
                    str(capture_path),
                    "--protocol-input",
                    str(protocol_path),
                    "--result",
                    str(result_path),
                    "--campaign-verification",
                    str(verification_path),
                    "--campaign-ledger",
                    str(ledger_path),
                    "--review-packet",
                    str(packet_path),
                    "--review-decision",
                    str(decision_path),
                    "--output",
                    str(sealed_pilot_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sealed_pilot_main(), 0)
            cli_preflight = json.loads(sealed_pilot_path.read_text(encoding="utf-8"))
            self.assertEqual(cli_preflight, preflight)
            tampered_preflight = json.loads(json.dumps(preflight))
            tampered_preflight["accepted"] = True
            with self.assertRaisesRegex(SealedPilotPreflightError, "cannot accept"):
                validate_preflight(tampered_preflight)
            fresh_corpus = valid_corpus_plan()
            fresh_corpus["workflow_id"] = "fresh-replication-workflow"
            for task in fresh_corpus["tasks"]:
                task["case_id"] = f"replication-{task['split']}-{task['case_id'].split('-')[-1]}"
            fresh_corpus_path = root / "fresh-corpus.json"
            fresh_corpus_path.write_text(json.dumps(fresh_corpus), encoding="utf-8")
            admission = build_admission(sealed_pilot_path, fresh_corpus_path)
            validate_admission(admission)
            self.assertEqual(admission["admission_status"], "ready_for_sealed_pilot_execution_authorization")
            self.assertEqual(admission["execution_status"], "not_started")
            self.assertEqual(admission["authorization_status"], "not_granted")
            self.assertTrue(admission["fresh_corpus_verified"])
            self.assertEqual(admission["fresh_execution_plan"]["planned_execution_count"], 300)
            tampered_admission = json.loads(json.dumps(admission))
            tampered_admission["execution_status"] = "started"
            with self.assertRaisesRegex(FreshCorpusAdmissionError, "cannot start execution"):
                validate_admission(tampered_admission)
            admission_path = root / "fresh-corpus-admission.json"
            with patch.object(
                sys,
                "argv",
                [
                    "fresh_corpus_admission",
                    "--sealed-pilot-preflight",
                    str(sealed_pilot_path),
                    "--fresh-corpus",
                    str(fresh_corpus_path),
                    "--output",
                    str(admission_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(fresh_corpus_admission_main(), 0)
            self.assertEqual(json.loads(admission_path.read_text(encoding="utf-8")), admission)
            reused_corpus = valid_corpus_plan()
            reused_corpus["workflow_id"] = "different-workflow-but-same-cases"
            reused_path = root / "reused-corpus.json"
            reused_path.write_text(json.dumps(reused_corpus), encoding="utf-8")
            with self.assertRaisesRegex(FreshCorpusAdmissionError, "case set"):
                build_admission(sealed_pilot_path, reused_path)
            drifted_corpus = json.loads(json.dumps(fresh_corpus))
            drifted_corpus["controller_config_digest"] = "e" * 64
            drifted_path = root / "drifted-corpus.json"
            drifted_path.write_text(json.dumps(drifted_corpus), encoding="utf-8")
            with self.assertRaisesRegex(FreshCorpusAdmissionError, "controller configuration"):
                build_admission(sealed_pilot_path, drifted_path)
            execution_request = build_execution_request(admission_path)
            validate_execution_request(execution_request)
            self.assertEqual(execution_request["request_status"], "pending_operator_authorization")
            self.assertEqual(execution_request["execution_status"], "not_started")
            self.assertEqual(execution_request["authorization_status"], "not_granted")
            self.assertTrue(execution_request["operator_ack_required"])
            self.assertTrue(execution_request["external_runner_required"])
            request_path = root / "sealed-pilot-execution-request.json"
            with patch.object(
                sys,
                "argv",
                [
                    "sealed_pilot_execution_request",
                    "--fresh-corpus-admission",
                    str(admission_path),
                    "--output",
                    str(request_path),
                ],
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sealed_pilot_execution_request_main(), 0)
            self.assertEqual(json.loads(request_path.read_text(encoding="utf-8")), execution_request)
            tampered_request = json.loads(json.dumps(execution_request))
            tampered_request["authorization_status"] = "granted"
            with self.assertRaisesRegex(SealedPilotExecutionRequestError, "cannot grant authorization"):
                validate_execution_request(tampered_request)
            blocked_decision = record_review_decision(
                packet,
                "revert_candidate",
                "operator-ref-1",
                "reviewed verified artifact chain and bounded disposition",
                "revert pending independent replication",
            )
            blocked_decision_path = root / "blocked-review-decision.json"
            blocked_decision_path.write_text(json.dumps(blocked_decision), encoding="utf-8")
            blocked_preflight = build_sealed_pilot_preflight(
                plan_path,
                report_path,
                agent_path,
                capture_path,
                protocol_path,
                result_path,
                verification_path,
                ledger_path,
                packet_path,
                blocked_decision_path,
            )
            self.assertEqual(blocked_preflight["preflight_status"], "blocked")
            self.assertEqual(blocked_preflight["block_reason"], "review_did_not_keep_candidate")
            alternate = next(
                candidate
                for candidate in ("keep_candidate", "revert_candidate", "not_evidence")
                if candidate != packet["recommended_disposition"]
            )
            with self.assertRaisesRegex(CampaignReviewDecisionError, "override_reason"):
                record_review_decision(
                    packet,
                    alternate,
                    "operator-ref-1",
                    "reviewed verified artifact chain and bounded disposition",
                )
            self.assertTrue(verification["valid"])
            self.assertEqual(verification["claim_ceiling"], "LocalDevelopmentCampaignVerificationOnly")
            self.assertFalse(verification["scientific_evidence"])
            self.assertEqual(cli_verification, verification)
            self.assertEqual(ledger["status"], "verified_local_chain")
            self.assertEqual(len(ledger["events"]), 7)
            self.assertFalse(ledger["scientific_evidence"])
            self.assertEqual(cli_ledger, ledger)
            self.assertEqual(packet["review_status"], "pending_manual_review")
            self.assertFalse(packet["accepted"])
            self.assertTrue(packet["human_review_required"])
            self.assertEqual(cli_packet, packet)

            # State slice: verified-metacognitive-control-campaign-verification-v1.
            # Every artifact handoff must reject a single-link tamper.
            tamper_cases = (
                (plan_path, lambda value: value["rows"][0].update({"task_family": "tampered"})),
                (report_path, lambda value: value["rows"][0].update({"task_family": "tampered"})),
                (agent_path, lambda value: value[1].update({"task_digest": "0" * 64})),
                (capture_path, lambda value: value[1].update({"scope_valid": not value[1]["scope_valid"]})),
                (protocol_path, lambda value: value[1].update({"latency_ms": value[1]["latency_ms"] + 1})),
                (result_path, lambda value: value.update({"decision": "revert_candidate" if value.get("decision") == "keep_candidate" else "keep_candidate"})),
            )
            rejected_tamper_count = 0
            for target_path, mutate in tamper_cases:
                original_text = target_path.read_text(encoding="utf-8")
                if target_path.suffix == ".jsonl":
                    tampered_value = [json.loads(line) for line in original_text.splitlines() if line.strip()]
                    mutate(tampered_value)
                    tampered_text = "\n".join(json.dumps(record) for record in tampered_value) + "\n"
                else:
                    tampered_value = json.loads(original_text)
                    mutate(tampered_value)
                    tampered_text = json.dumps(tampered_value)
                target_path.write_text(tampered_text, encoding="utf-8")
                try:
                    try:
                        verify_campaign(
                            plan_path,
                            report_path,
                            agent_path,
                            capture_path,
                            protocol_path,
                            result_path,
                        )
                    except (CampaignVerificationError, JoinError):
                        rejected_tamper_count += 1
                    else:
                        self.fail(f"campaign verifier accepted tampered {target_path.name}")
                finally:
                    target_path.write_text(original_text, encoding="utf-8")
            self.assertEqual(rejected_tamper_count, len(tamper_cases))
        self.assertEqual(len(joined), 301)
        self.assertEqual(joined[0]["execution_plan_digest"], plan["plan_digest"])
        self.assertTrue(all(record["record_type"] in {"capture_manifest", "observation"} for record in joined))

    def test_ledger_rejects_illegal_transition_and_tampering(self):
        plan = build_execution_plan(valid_corpus_plan())
        ledger = initialize_ledger(plan)
        with self.assertRaisesRegex(CampaignLedgerError, "expected execution_attached"):
            append_event(ledger, "capture_attached", "a" * 64, "capture_bundle", 301)
        advanced = append_event(ledger, "execution_attached", "a" * 64, "agent_execution_bundle", 301)
        tampered = json.loads(json.dumps(advanced))
        tampered["events"][0]["artifact_digest"] = "b" * 64
        with self.assertRaisesRegex(CampaignLedgerError, "event 0 digest mismatch"):
            validate_ledger(tampered)

    def test_review_packet_cannot_self_accept(self):
        packet = {
            "record_type": "campaign_review_packet",
            "schema_version": "verified-metacognitive-campaign-review-v1",
            "state_slice": "verified-metacognitive-control-campaign-review-v1",
            "workflow_id": "review-test",
            "review_status": "pending_manual_review",
            "human_review_required": True,
            "reviewed": False,
            "accepted": True,
            "recommended_disposition": "not_evidence",
            "review_notes_required": True,
            "checklist": {
                "artifact_chain_verified": True,
                "result_recomputed": True,
                "no_authority": True,
                "retention_lock": True,
            },
            "authority_granted": False,
            "network_access": False,
            "raw_reasoning_retained": False,
            "scientific_evidence": False,
            "claim_ceiling": "LocalDevelopmentCampaignReviewOnly",
            "execution_plan_digest": "a" * 64,
            "ledger_digest": "b" * 64,
            "verification_report_digest": "c" * 64,
            "result_digest": "d" * 64,
            "non_claims": ["not_acceptance"],
        }
        unsigned = dict(packet)
        packet["packet_digest"] = digest_json(unsigned)
        with self.assertRaisesRegex(CampaignReviewError, "cannot accept"):
            validate_review_packet(packet)

    def test_review_decision_rejects_tampered_acceptance(self):
        decision = {
            "record_type": "campaign_review_decision",
            "schema_version": "verified-metacognitive-campaign-review-decision-v1",
            "state_slice": "verified-metacognitive-control-campaign-review-decision-v1",
            "workflow_id": "review-decision-test",
            "source_packet_digest": "a" * 64,
            "execution_plan_digest": "b" * 64,
            "ledger_digest": "c" * 64,
            "verification_report_digest": "d" * 64,
            "result_digest": "e" * 64,
            "review_status": "reviewed",
            "reviewed": True,
            "human_review_required": False,
            "decision": "not_evidence",
            "recommended_disposition": "not_evidence",
            "reviewer_ref_digest": "f" * 64,
            "review_notes_digest": "1" * 64,
            "review_notes_retained": False,
            "override_reason_digest": None,
            "accepted": True,
            "authority_granted": False,
            "network_access": False,
            "raw_reasoning_retained": False,
            "scientific_evidence": False,
            "repository_evidence_ledger_appended": False,
            "production_ready": False,
            "claim_ceiling": "LocalDevelopmentCampaignReviewDecisionOnly",
            "non_claims": ["not_candidate_acceptance"],
        }
        decision["decision_digest"] = digest_json(decision)
        with self.assertRaisesRegex(CampaignReviewDecisionError, "cannot accept"):
            validate_review_decision(decision)


if __name__ == "__main__":
    unittest.main()
