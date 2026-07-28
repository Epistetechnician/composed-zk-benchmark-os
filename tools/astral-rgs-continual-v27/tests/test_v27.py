from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v27", HERE / "v27.py")
assert SPEC and SPEC.loader
V27 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V27)
RGS_CACHE: dict | None = None


def test_missing_model_report_preserves_explicit_open_gate(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    report = _build(packet=packet, rgs=None)

    assert report["status"] == "ValidatedWithOpenGates"
    assert report["errors"] == []
    assert report["open_gates"] == ["rgs.model_backed_report_not_supplied"]
    assert report["rgs_model_backed"]["status"] == "NotRun"
    assert report["gate_state"]["thesis"] == "NotValidated"


def test_missing_tencent_and_model_reports_are_explicit_not_run() -> None:
    report = V27.build_validation(
        historical_report=_historical(),
        tencent_packet=None,
        tencent_subset_manifest=None,
        rgs_report=None,
        historical_report_sha256=V27.protocol()["historical_baseline"]["report_sha256"],
    )

    assert report["status"] == "ValidatedWithOpenGates"
    assert report["errors"] == []
    assert report["tencent_clbench"]["status"] == "NotRun"
    assert report["open_gates"] == [
        "tencent.valid_v2_packet_not_supplied",
        "rgs.model_backed_report_not_supplied",
    ]


def test_valid_scientific_candidate_is_independently_recomputed(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    report = _build(packet=packet, rgs=_rgs())

    assert report["status"] == "ValidatedModelBackedScientificCandidate"
    assert report["rgs_model_backed"]["valid"] is True
    assert report["rgs_model_backed"]["scientific_candidate_qualified"] is True
    assert report["claim_boundary"]["continual_learning_solved"] is False
    assert report["gate_state"]["independent_replication"] == "NotRun"


def test_supplied_malformed_rgs_report_is_invalid(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    rgs = _rgs()
    rgs["summary"]["scientific_candidate_qualified"] = False
    _rehash(rgs, "report_sha256")

    report = _build(packet=packet, rgs=rgs)

    assert report["status"] == "Invalid"
    assert "rgs.summary.scientific_candidate_qualified" in report["errors"]
    assert report["rgs_model_backed"]["status"] == "Invalid"


def test_rgs_digest_tampering_is_rejected(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    rgs = _rgs()
    rgs["summary"]["scientific_candidate_qualified"] = False

    report = _build(packet=packet, rgs=rgs)

    assert report["status"] == "Invalid"
    assert "rgs.report_sha256" in report["errors"]
    assert report["claim_boundary"]["model_backed_local_scientific_candidate"] is False


def test_rehashed_outcome_tamper_is_independently_rejected(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    rgs = _rgs()
    rgs["matched_cell_results"][0]["candidate_results"][-1][
        "primary_future_unseen_score"
    ] = 0.1
    _rehash(rgs, "report_sha256")

    report = _build(packet=packet, rgs=rgs)

    assert report["status"] == "Invalid"
    assert any(
        error.startswith("rgs.matched_cell_results[0]")
        or error == "rgs.statistical_results"
        for error in report["errors"]
    )


def test_tencent_overclaim_fails_validation(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    packet["claim_boundary"]["continual_learning_solved"] = True
    _rehash(packet, "packet_sha256")

    report = _build(packet=packet, rgs=None)

    assert report["status"] == "Invalid"
    assert "tencent.claim_boundary.continual_learning_solved" in report["errors"]


def test_tencent_missing_referenced_bytes_fails_validation(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    Path(packet["execution"]["raw_output_path"]).unlink()

    report = _build(packet=packet, rgs=None)

    assert report["status"] == "Invalid"
    assert "tencent.execution.raw_output_bytes.missing_or_symlink" in report["errors"]


def test_tencent_unbound_model_fails_validation(tmp_path: Path) -> None:
    packet = _tencent(tmp_path)
    packet["execution"]["model_hash_status"] = "missing"
    packet["execution"]["model_sha256"] = None
    _rehash(packet, "packet_sha256")

    report = _build(packet=packet, rgs=None)

    assert report["status"] == "Invalid"
    assert "tencent.execution.model_hash_status" in report["errors"]
    assert "tencent.execution.model_bytes.sha256" in report["errors"]


def _build(*, packet: dict, rgs: dict | None) -> dict:
    return V27.build_validation(
        historical_report=_historical(),
        tencent_packet=packet,
        tencent_subset_manifest=_subset_manifest(packet),
        rgs_report=rgs,
        historical_report_sha256=V27.protocol()["historical_baseline"]["report_sha256"],
    )


def _historical() -> dict:
    return {
        "pipeline_status": "HolisticClaimValidationCompleteWithOpenClaims",
        "thesis_status": "NotValidated",
    }


def _tencent(root: Path) -> dict:
    source_license = root / "LICENSE"
    dataset = root / "subset.jsonl"
    dataset_license = root / "DATASET-LICENSE.txt"
    model = root / "model.gguf"
    raw = root / "raw.jsonl"
    source_license.write_text("Apache-2.0 fixture\n", encoding="utf-8")
    dataset.write_text('{"task":"fixture"}\n', encoding="utf-8")
    dataset_license.write_text("evaluation only\n", encoding="utf-8")
    model.write_bytes(b"model-fixture")
    raw.write_text('{"answer":"fixture"}\n', encoding="utf-8")
    packet = {
        "version": "mesh.tencent_clbench_frozen_evaluation.v2",
        "state_slice": "astral-rgs-nested-recoverable-update-v27:tencent-clbench",
        "status": "valid_frozen_external_evaluation",
        "errors": [],
        "source": {
            "repository": "https://github.com/Tencent-Hunyuan/CL-bench",
            "commit": "16bffd1cfa05927e72ec75c835177d6e23e82172",
            "license_path": str(source_license),
            "license_sha256": V27.prefixed_sha256(source_license),
        },
        "dataset": {
            "revision": "b28a5832a09b0d96c0cf4c22e90d7c60ede25b80",
            "license": "custom-evaluation-only",
            "license_path": str(dataset_license),
            "license_sha256": V27.prefixed_sha256(dataset_license),
            "scope": "deterministic_diagnostic_subset",
            "path": str(dataset),
            "sha256": V27.prefixed_sha256(dataset),
            "row_count": 4,
            "parameter_updates_from_dataset": False,
            "calibration_from_dataset": False,
        },
        "execution": {
            "evaluated_task_count": 4,
            "frozen_system": True,
            "model_hash_status": "byte_bound",
            "model_path": str(model),
            "model_sha256": V27.prefixed_sha256(model),
            "raw_output_path": str(raw),
            "raw_output_sha256": V27.prefixed_sha256(raw),
            "command": ["runner", "--frozen"],
            "runtime_inventory": {"python": "fixture", "hardware": "cpu"},
        },
        "grading": {
            "performed": False,
            "canonical_judge": False,
            "command": [],
        },
        "claim_boundary": {
            "full_official_benchmark_execution": False,
            "canonical_clbench_score": False,
            "parametric_continual_learning": False,
            "cross_context_retention": False,
            "catastrophic_forgetting_measured": False,
            "recoverable_update_measured": False,
            "continual_learning_solved": False,
            "autonomous_self_improvement": False,
            "external_benchmark_dominance": False,
            "production_readiness": False,
        },
    }
    packet["packet_sha256"] = V27.stable_hash(packet)
    return packet


def _rgs() -> dict:
    global RGS_CACHE
    if RGS_CACHE is not None:
        return copy.deepcopy(RGS_CACHE)
    contract = V27.protocol()
    thresholds = contract["scientific_thresholds"]
    qualities = {
        "no_update": 0.40,
        "naive_sequential_lora": 0.74,
        "modular_ghost_state": 0.82,
        "compressed_adapter_recollection": 0.83,
        "representation_time_distillation": 0.84,
        "nested_multiscale_lora": 0.90,
    }
    methods = contract["required_method_ids"]
    selectors = [
        "astral",
        *contract["confirmatory_selector_ids"],
        *contract["null_selector_ids"],
    ]
    cells = []
    for family_index in range(12):
        family_id = f"assessment-family-{family_index:02d}"
        for seed in (101, 103, 107):
            for order_id in ("order-abc", "order-acb", "order-bac"):
                candidates = []
                for method_id in methods:
                    quality = qualities[method_id]
                    gates = {
                        "acquisition": quality >= thresholds["acquisition_min"],
                        "protected_retention": True,
                        "forgetting": True,
                        "calibration_mae": True,
                        "maximum_protected_retention_drop": True,
                        "brier_degradation": True,
                        "exact_recovery": True,
                        "governance": True,
                    }
                    candidates.append(
                        {
                            "method_id": method_id,
                            "execution_id": f"exec::{seed}::{order_id}::{method_id}",
                            "primary_future_unseen_score": quality,
                            "acquisition": quality,
                            "average_final_accuracy": quality,
                            "protected_retention": 0.95,
                            "maximum_protected_retention_drop": 0.01,
                            "forgetting": 0.02,
                            "backward_transfer": -0.01,
                            "forward_transfer": 0.02,
                            "calibration_mae": 0.02,
                            "brier_score": 0.08,
                            "brier_degradation": 0.01,
                            "hard_governance_violations": 0,
                            "recovery_events": [
                                {
                                    "fault_event_id": "fault-1",
                                    "corruption_drop": 0.20,
                                    "recovered_score_loss": 0.0,
                                    "rollback_digest_match": True,
                                    "replay_digest_match": True,
                                    "success": True,
                                }
                            ],
                            "recovery_rate": 1.0,
                            "gates": gates,
                            "failed_gate_ids": [
                                key for key, passed in gates.items() if not passed
                            ],
                            "feasible": all(gates.values()),
                        }
                    )
                decisions = []
                for selector_id in selectors:
                    selected_method = (
                        "nested_multiscale_lora"
                        if selector_id == "astral"
                        else "no_update"
                        if selector_id == "no_update"
                        else "modular_ghost_state"
                    )
                    selected_quality = qualities[selected_method]
                    selected_feasible = selected_method != "no_update"
                    decisions.append(
                        {
                            "selector_id": selector_id,
                            "selected_method_id": selected_method,
                            "selected_candidate_feasible": selected_feasible,
                            "selection_regret": (
                                round(0.90 - selected_quality, 10)
                                if selected_feasible
                                else 1.0
                            ),
                        }
                    )
                cells.append(
                    {
                        "cell_id": f"{family_id}::{seed}::{order_id}",
                        "task_family_id": family_id,
                        "task_family_category": f"category-{family_index % 3}",
                        "seed": seed,
                        "task_order_id": order_id,
                        "oracle_future_unseen_score": 0.90,
                        "candidate_results": candidates,
                        "selector_results": decisions,
                        "no_feasible_candidate": False,
                    }
                )
    method_registry = [
        {
            "method_id": method_id,
            "execution_status": "native_observed",
            "implementation_sha256": V27.stable_hash(f"method:{method_id}"),
        }
        for method_id in methods
    ]
    selector_registry = [
        {
            "selector_id": selector_id,
            "execution_status": "native_observed",
        }
        for selector_id in selectors
    ]
    controls = [
        {
            "control_id": control_id,
            "execution_status": "native_observed",
        }
        for control_id in contract["required_control_ids"]
    ]
    report = {
        "version": contract["rgs_exchange"]["report_version"],
        "state_slice": contract["state_slice"],
        "disposition": contract["claim_ceiling"],
        "input_errors": [],
        "thresholds": thresholds,
        "matched_cell_results": cells,
        "integrity_evidence": {
            "protocol_sha256": V27.stable_hash("protocol"),
            "prediction_lock_sha256": V27.stable_hash("prediction-lock"),
            "assessment_manifest_sha256": V27.stable_hash("assessment"),
            "split_manifest_sha256": V27.stable_hash("splits"),
            "strongest_nonprivileged_selector_id": "activation_only_predictor",
            "bootstrap_seed": contract["rgs_exchange"]["bootstrap_seed"],
            "bootstrap_replicates": contract["rgs_exchange"]["bootstrap_replicates"],
            "method_registry": method_registry,
            "selector_registry": selector_registry,
            "controls": controls,
            "execution_count": 54,
            "all_required_arms_native": True,
            "all_required_controls_native": True,
            "prediction_lock_preceded_outcomes": True,
        },
        "statistical_results": {},
        "summary": {
            "protocol_complete": True,
            "local_harness_candidate": True,
            "scientific_candidate_qualified": True,
            "execution_count": 54,
            "matched_cell_count": 108,
            "assessment_family_count": 12,
            "seed_count": 3,
            "task_order_count": 3,
            "no_feasible_candidate_cell_count": 0,
            "bootstrap_sample_index_stream_sha256": "",
        },
        "claim_boundary": {
            "local_development_holistic_evaluator": True,
            "local_harness_candidate": True,
            "local_author_development_scientific_candidate": True,
            **{key: False for key in contract["required_false_claims"]},
        },
    }
    recomputed, errors = V27._recompute_scientific_results(report, contract)
    assert errors == []
    report["statistical_results"] = recomputed["statistical_results"]
    report["summary"]["bootstrap_sample_index_stream_sha256"] = recomputed[
        "bootstrap_digest"
    ]
    report["report_sha256"] = V27.stable_hash(report)
    RGS_CACHE = copy.deepcopy(report)
    return report


def _subset_manifest(packet: dict) -> dict:
    return {
        "version": "mesh.tencent_clbench_subset_manifest.v1",
        "source_sha256": "sha256:d5fc88d4b2eea75c61dd40862021b6ae2fba26bd21b58e8c5e18377a763943be",
        "subset_sha256": packet["dataset"]["sha256"],
        "selected_count": 4,
        "selection_uses_model_outputs_or_rubric_scores": False,
        "claim_boundary": {
            "deterministic_diagnostic_subset": True,
            "full_official_benchmark": False,
            "leaderboard_comparable": False,
        },
    }


def _rehash(value: dict, digest_key: str) -> None:
    core = dict(value)
    core.pop(digest_key, None)
    value[digest_key] = V27.stable_hash(core)
