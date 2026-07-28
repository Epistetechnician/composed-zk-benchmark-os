from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
PROTOCOL_PATH = HERE / "protocol.json"
LEDGER_PATH = REPOSITORY / "docs/research/astral-self-modeling/03-claim-ledger.md"
CLAIM_ID = re.compile(r"^C\d{3}$")
SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

STATS_SPEC = importlib.util.spec_from_file_location("astral_v27_statistics", HERE / "statistics_v2.py")
assert STATS_SPEC and STATS_SPEC.loader
STATS = importlib.util.module_from_spec(STATS_SPEC)
STATS_SPEC.loader.exec_module(STATS)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prefixed_sha256(path: Path) -> str:
    return "sha256:" + sha256(path)


def load_object(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file() or path.is_symlink():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def protocol() -> dict[str, Any]:
    return load_object(PROTOCOL_PATH)


def claim_statuses() -> dict[str, str]:
    current: dict[str, str] = {}
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| C"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not CLAIM_ID.fullmatch(cells[0]):
            continue
        if len(cells) == 8:
            current[cells[0]] = cells[6]
        elif len(cells) == 7:
            current[cells[0]] = cells[2]
        elif len(cells) == 5:
            current[cells[0]] = cells[3]
        else:
            raise ValueError(f"unsupported claim row: {cells[0]}")
    return current


def validate_historical_report(report: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = contract["historical_baseline"]
    if report.get("thesis_status") != expected["thesis_status"]:
        errors.append("historical.thesis_status")
    if report.get("pipeline_status") != "HolisticClaimValidationCompleteWithOpenClaims":
        errors.append("historical.pipeline_status")
    return errors


def validate_tencent_packet(packet: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = contract["tencent_clbench"]
    if packet.get("version") != expected["packet_version"]:
        errors.append("tencent.version")
    if packet.get("state_slice") != f"{contract['state_slice']}:tencent-clbench":
        errors.append("tencent.state_slice")
    if packet.get("status") != "valid_frozen_external_evaluation" or packet.get("errors") != []:
        errors.append("tencent.status")
    core = dict(packet)
    digest = core.pop("packet_sha256", None)
    if digest != stable_hash(core):
        errors.append("tencent.packet_sha256")
    source = _dict(packet.get("source"))
    dataset = _dict(packet.get("dataset"))
    execution = _dict(packet.get("execution"))
    grading = _dict(packet.get("grading"))
    if source.get("repository") != expected["repository"] or source.get("commit") != expected["commit"]:
        errors.append("tencent.source")
    errors.extend(_file_binding_errors(source, "license_path", "license_sha256", "tencent.source.license"))
    if dataset.get("revision") != expected["dataset_revision"] or dataset.get("license") != expected["license"]:
        errors.append("tencent.dataset_identity")
    if dataset.get("scope") not in ("deterministic_diagnostic_subset", "full_official_release"):
        errors.append("tencent.dataset.scope")
    if dataset.get("parameter_updates_from_dataset") is not False:
        errors.append("tencent.parameter_updates_from_dataset")
    if dataset.get("calibration_from_dataset") is not False:
        errors.append("tencent.calibration_from_dataset")
    errors.extend(_file_binding_errors(dataset, "path", "sha256", "tencent.dataset.bytes"))
    errors.extend(
        _file_binding_errors(dataset, "license_path", "license_sha256", "tencent.dataset.license_bytes")
    )
    if execution.get("model_hash_status") != "byte_bound":
        errors.append("tencent.execution.model_hash_status")
    if execution.get("frozen_system") is not True:
        errors.append("tencent.execution.frozen_system")
    if not isinstance(execution.get("command"), list) or not execution.get("command"):
        errors.append("tencent.execution.command")
    if not isinstance(execution.get("runtime_inventory"), dict) or not execution.get("runtime_inventory"):
        errors.append("tencent.execution.runtime_inventory")
    errors.extend(
        _file_binding_errors(execution, "model_path", "model_sha256", "tencent.execution.model_bytes")
    )
    errors.extend(
        _file_binding_errors(
            execution,
            "raw_output_path",
            "raw_output_sha256",
            "tencent.execution.raw_output_bytes",
        )
    )
    if grading.get("performed") is True:
        if not isinstance(grading.get("command"), list) or not grading.get("command"):
            errors.append("tencent.grading.command")
        errors.extend(
            _file_binding_errors(
                grading,
                "graded_output_path",
                "graded_output_sha256",
                "tencent.grading.output_bytes",
            )
        )
    claims = _dict(packet.get("claim_boundary"))
    if claims.get("full_official_benchmark_execution") is True and (
        dataset.get("row_count") != 1899 or execution.get("evaluated_task_count") != 1899
    ):
        errors.append("tencent.claim_boundary.full_official_benchmark_execution")
    if claims.get("canonical_clbench_score") is True and grading.get("canonical_judge") is not True:
        errors.append("tencent.claim_boundary.canonical_clbench_score")
    for key in (
        "parametric_continual_learning",
        "cross_context_retention",
        "catastrophic_forgetting_measured",
        "recoverable_update_measured",
        "continual_learning_solved",
        "autonomous_self_improvement",
        "external_benchmark_dominance",
        "production_readiness",
    ):
        if claims.get(key) is not False:
            errors.append(f"tencent.claim_boundary.{key}")
    return errors


def validate_subset_manifest(
    manifest: dict[str, Any],
    packet: dict[str, Any],
    contract: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected = contract["tencent_clbench"]
    dataset = _dict(packet.get("dataset"))
    execution = _dict(packet.get("execution"))
    if manifest.get("version") != "mesh.tencent_clbench_subset_manifest.v1":
        errors.append("tencent_subset.version")
    if manifest.get("source_sha256") != "sha256:" + expected["dataset_sha256"]:
        errors.append("tencent_subset.source_sha256")
    if manifest.get("subset_sha256") != dataset.get("sha256"):
        errors.append("tencent_subset.subset_sha256")
    if manifest.get("selected_count") != execution.get("evaluated_task_count"):
        errors.append("tencent_subset.selected_count")
    if manifest.get("selection_uses_model_outputs_or_rubric_scores") is not False:
        errors.append("tencent_subset.selection_independence")
    claims = _dict(manifest.get("claim_boundary"))
    if claims.get("deterministic_diagnostic_subset") is not True:
        errors.append("tencent_subset.claim_boundary.diagnostic")
    for key in ("full_official_benchmark", "leaderboard_comparable"):
        if claims.get(key) is not False:
            errors.append(f"tencent_subset.claim_boundary.{key}")
    return errors


def validate_rgs_report(
    report: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[list[str], bool]:
    errors: list[str] = []
    expected = contract["rgs_exchange"]
    if report.get("version") != expected["report_version"]:
        return ["rgs.version"], False
    if report.get("state_slice") != contract["state_slice"]:
        errors.append("rgs.state_slice")
    core = dict(report)
    digest = core.pop("report_sha256", None)
    if digest != stable_hash(core):
        errors.append("rgs.report_sha256")
    if report.get("input_errors") != []:
        errors.append("rgs.input_errors")
    if _dict(report.get("thresholds")) != contract["scientific_thresholds"]:
        errors.append("rgs.thresholds")

    summary = _dict(report.get("summary"))
    if int(summary.get("seed_count") or 0) < int(expected["minimum_seeds"]):
        errors.append("rgs.seed_count")
    if int(summary.get("task_order_count") or 0) < int(expected["minimum_task_orders"]):
        errors.append("rgs.task_order_count")
    if int(summary.get("assessment_family_count") or 0) < int(expected["minimum_assessment_families"]):
        errors.append("rgs.assessment_family_count")
    if int(summary.get("execution_count") or 0) < int(expected["minimum_execution_count"]):
        errors.append("rgs.execution_count")
    if summary.get("protocol_complete") is not True:
        errors.append("rgs.protocol_complete")

    integrity = _dict(report.get("integrity_evidence"))
    method_registry = _registry_by_id(integrity.get("method_registry"), "method_id")
    selector_registry = _registry_by_id(integrity.get("selector_registry"), "selector_id")
    controls = _registry_by_id(integrity.get("controls"), "control_id")
    if set(method_registry) != set(contract["required_method_ids"]):
        errors.append("rgs.integrity.method_census")
    if any(row.get("execution_status") != "native_observed" for row in method_registry.values()):
        errors.append("rgs.integrity.method_native")
    required_selectors = {
        "astral",
        *contract["confirmatory_selector_ids"],
        *contract["null_selector_ids"],
    }
    if set(selector_registry) != required_selectors:
        errors.append("rgs.integrity.selector_census")
    if set(controls) != set(contract["required_control_ids"]):
        errors.append("rgs.integrity.control_census")
    if any(row.get("execution_status") != "native_observed" for row in controls.values()):
        errors.append("rgs.integrity.control_native")
    for key in (
        "protocol_sha256",
        "prediction_lock_sha256",
        "assessment_manifest_sha256",
        "split_manifest_sha256",
    ):
        if not _sha256(integrity.get(key)):
            errors.append(f"rgs.integrity.{key}")
    if integrity.get("execution_count") != summary.get("execution_count"):
        errors.append("rgs.integrity.execution_count")
    if integrity.get("all_required_arms_native") is not True:
        errors.append("rgs.integrity.all_required_arms_native")
    if integrity.get("all_required_controls_native") is not True:
        errors.append("rgs.integrity.all_required_controls_native")
    if integrity.get("prediction_lock_preceded_outcomes") is not True:
        errors.append("rgs.integrity.prediction_lock_preceded_outcomes")
    if integrity.get("bootstrap_seed") != expected["bootstrap_seed"]:
        errors.append("rgs.integrity.bootstrap_seed")
    if integrity.get("bootstrap_replicates") != expected["bootstrap_replicates"]:
        errors.append("rgs.integrity.bootstrap_replicates")
    strongest_selector = integrity.get("strongest_nonprivileged_selector_id")
    if strongest_selector not in contract["confirmatory_selector_ids"]:
        errors.append("rgs.integrity.strongest_nonprivileged_selector_id")

    recomputed, recompute_errors = _recompute_scientific_results(report, contract)
    errors.extend(recompute_errors)
    if not recompute_errors:
        if report.get("statistical_results") != recomputed["statistical_results"]:
            errors.append("rgs.statistical_results")
        expected_candidate = recomputed["scientific_candidate_qualified"]
        if summary.get("local_harness_candidate") is not recomputed["local_harness_candidate"]:
            errors.append("rgs.summary.local_harness_candidate")
        if summary.get("scientific_candidate_qualified") is not expected_candidate:
            errors.append("rgs.summary.scientific_candidate_qualified")
        if summary.get("bootstrap_sample_index_stream_sha256") != recomputed["bootstrap_digest"]:
            errors.append("rgs.summary.bootstrap_digest")
        expected_disposition = (
            contract["claim_ceiling"] if expected_candidate else "CompleteNegativeOrNoCandidate"
        )
        if report.get("disposition") != expected_disposition:
            errors.append("rgs.disposition")
    else:
        expected_candidate = False

    claims = _dict(report.get("claim_boundary"))
    if claims.get("local_development_holistic_evaluator") is not True:
        errors.append("rgs.claim_boundary.local_development_holistic_evaluator")
    if claims.get("local_author_development_scientific_candidate") is not expected_candidate:
        errors.append("rgs.claim_boundary.local_author_development_scientific_candidate")
    for key in contract["required_false_claims"]:
        if claims.get(key) is not False:
            errors.append(f"rgs.claim_boundary.{key}")
    return errors, bool(not errors and expected_candidate)


def build_validation(
    *,
    historical_report: dict[str, Any],
    tencent_packet: dict[str, Any] | None,
    tencent_subset_manifest: dict[str, Any] | None,
    rgs_report: dict[str, Any] | None,
    historical_report_sha256: str,
) -> dict[str, Any]:
    contract = protocol()
    claims = claim_statuses()
    errors: list[str] = []
    if list(claims) != [f"C{index:03d}" for index in range(1, 49)]:
        errors.append("ledger.exact_C001_C048_census")
    for claim_id in contract["claim_ids"]:
        if claims.get(claim_id) != "In test":
            errors.append(f"ledger.{claim_id}.status")
    if historical_report_sha256 != contract["historical_baseline"]["report_sha256"]:
        errors.append("historical.sha256")
    errors.extend(validate_historical_report(historical_report, contract))
    tencent_supplied = tencent_packet is not None
    tencent = tencent_packet or {}
    if tencent_supplied:
        errors.extend(validate_tencent_packet(tencent, contract))
        if _dict(tencent.get("dataset")).get("scope") == "deterministic_diagnostic_subset":
            errors.extend(
                validate_subset_manifest(tencent_subset_manifest or {}, tencent, contract)
            )

    rgs_supplied = rgs_report is not None
    rgs_errors: list[str] = []
    candidate = False
    if rgs_supplied:
        rgs_errors, candidate = validate_rgs_report(rgs_report or {}, contract)
        errors.extend(rgs_errors)
    base_valid = not errors
    if not base_valid:
        status = "Invalid"
    elif not rgs_supplied:
        status = "ValidatedWithOpenGates"
    elif candidate:
        status = "ValidatedModelBackedScientificCandidate"
    else:
        status = "ValidatedModelBackedNegative"
    tencent_valid = tencent_supplied and not any(
        error.startswith("tencent.") or error.startswith("tencent_subset.")
        for error in errors
    )
    rgs_valid = rgs_supplied and not rgs_errors
    rgs = rgs_report or {}
    report_core = {
        "version": "astral.rgs_continual_v27.validation.v2",
        "state_slice": contract["state_slice"],
        "status": status,
        "errors": errors,
        "open_gates": [
            *([] if tencent_supplied else ["tencent.valid_v2_packet_not_supplied"]),
            *([] if rgs_supplied else ["rgs.model_backed_report_not_supplied"]),
        ],
        "claim_census": {"first": "C001", "last": "C048", "count": len(claims)},
        "historical_baseline": {
            "status": historical_report.get("pipeline_status"),
            "thesis_status": historical_report.get("thesis_status"),
            "sha256": historical_report_sha256,
        },
        "tencent_clbench": {
            "status": "Valid" if tencent_valid else "NotRun" if not tencent_supplied else "Invalid",
            "valid": tencent_valid,
            "scope": _dict(tencent.get("dataset")).get("scope"),
            "evaluated_task_count": _dict(tencent.get("execution")).get(
                "evaluated_task_count"
            ),
            "canonical_score": _dict(tencent.get("claim_boundary")).get(
                "canonical_clbench_score"
            )
            is True,
        },
        "rgs_model_backed": {
            "status": "NotRun" if not rgs_supplied else "Valid" if rgs_valid else "Invalid",
            "valid": rgs_valid,
            "scientific_candidate_qualified": candidate,
            "disposition": rgs.get("disposition", "NotRun"),
        },
        "gate_state": {
            "model_backed_correction_gain": (
                "Candidate"
                if candidate
                else "Negative"
                if rgs_valid
                else "NotRun"
                if not rgs_supplied
                else "Invalid"
            ),
            "fresh_stage0c_confirmation": "Blocked",
            "stage1": "BlockedByStage0C",
            "independent_human_review": "NotRun",
            "independent_replication": "NotRun",
            "thesis": "NotValidated",
        },
        "claim_boundary": {
            "local_v27_validation_pipeline": base_valid,
            "frozen_external_context_learning_observation": tencent_valid,
            "model_backed_local_scientific_candidate": candidate,
            **{key: False for key in contract["required_false_claims"]},
        },
    }
    return {**report_core, "report_sha256": stable_hash(report_core)}


def _recompute_scientific_results(
    report: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    cells = report.get("matched_cell_results")
    if not isinstance(cells, list) or not cells:
        return {}, ["rgs.matched_cell_results"]
    candidate_by_cell: dict[str, dict[str, dict[str, Any]]] = {}
    decision_by_cell: dict[str, dict[str, dict[str, Any]]] = {}
    cell_keys: dict[str, tuple[str, int, str]] = {}
    family_categories: dict[str, str] = {}
    coordinates: set[tuple[str, int, str]] = set()
    required_methods = set(contract["required_method_ids"])
    required_selectors = {
        "astral",
        *contract["confirmatory_selector_ids"],
        *contract["null_selector_ids"],
    }
    thresholds = contract["scientific_thresholds"]
    for index, raw_cell in enumerate(cells):
        prefix = f"rgs.matched_cell_results[{index}]"
        cell = _dict(raw_cell)
        cell_id = cell.get("cell_id")
        family_id = cell.get("task_family_id")
        category = cell.get("task_family_category")
        seed = cell.get("seed")
        order_id = cell.get("task_order_id")
        if (
            not isinstance(cell_id, str)
            or not isinstance(family_id, str)
            or not isinstance(category, str)
            or not isinstance(seed, int)
            or not isinstance(order_id, str)
        ):
            errors.append(f"{prefix}.identity")
            continue
        coordinate = (family_id, seed, order_id)
        if cell_id in cell_keys or coordinate in coordinates:
            errors.append(f"{prefix}.duplicate")
            continue
        coordinates.add(coordinate)
        cell_keys[cell_id] = coordinate
        if family_id in family_categories and family_categories[family_id] != category:
            errors.append(f"{prefix}.family_category")
        family_categories[family_id] = category
        candidates = _registry_by_id(cell.get("candidate_results"), "method_id")
        if set(candidates) != required_methods:
            errors.append(f"{prefix}.candidate_census")
            continue
        for method_id, candidate in candidates.items():
            gates, gate_errors = _candidate_gates(candidate, thresholds, f"{prefix}.{method_id}")
            errors.extend(gate_errors)
            if candidate.get("gates") != gates:
                errors.append(f"{prefix}.{method_id}.gates")
            if candidate.get("feasible") is not all(gates.values()):
                errors.append(f"{prefix}.{method_id}.feasible")
            expected_failed = [key for key, passed in gates.items() if not passed]
            if candidate.get("failed_gate_ids") != expected_failed:
                errors.append(f"{prefix}.{method_id}.failed_gate_ids")
        feasible_scores = [
            float(candidate["primary_future_unseen_score"])
            for candidate in candidates.values()
            if candidate.get("feasible") is True
        ]
        oracle = max(feasible_scores) if feasible_scores else None
        if cell.get("oracle_future_unseen_score") != oracle:
            errors.append(f"{prefix}.oracle_future_unseen_score")
        if cell.get("no_feasible_candidate") is not (oracle is None):
            errors.append(f"{prefix}.no_feasible_candidate")
        decisions = _registry_by_id(cell.get("selector_results"), "selector_id")
        if set(decisions) != required_selectors:
            errors.append(f"{prefix}.selector_census")
            continue
        for selector_id, decision in decisions.items():
            selected_method = decision.get("selected_method_id")
            if selected_method not in candidates:
                errors.append(f"{prefix}.{selector_id}.selected_method_id")
                continue
            selected = candidates[selected_method]
            expected_regret = (
                1.0
                if oracle is None or selected.get("feasible") is not True
                else round(max(0.0, oracle - float(selected["primary_future_unseen_score"])), 10)
            )
            if decision.get("selected_candidate_feasible") is not selected.get("feasible"):
                errors.append(f"{prefix}.{selector_id}.selected_candidate_feasible")
            if decision.get("selection_regret") != expected_regret:
                errors.append(f"{prefix}.{selector_id}.selection_regret")
        candidate_by_cell[cell_id] = candidates
        decision_by_cell[cell_id] = decisions
    families = set(family_categories)
    seeds = {coordinate[1] for coordinate in coordinates}
    orders = {coordinate[2] for coordinate in coordinates}
    if len(cells) != len(families) * len(seeds) * len(orders):
        errors.append("rgs.matched_cell_results.cross_product")
    if errors:
        return {}, errors

    contrasts: dict[str, dict[tuple[str, int, str], float]] = {}
    for method_id in contract["architecture_candidate_ids"]:
        contrasts[f"c047:{method_id}"] = {
            cell_keys[cell_id]: float(candidates[method_id]["primary_future_unseen_score"])
            - float(candidates["naive_sequential_lora"]["primary_future_unseen_score"])
            for cell_id, candidates in candidate_by_cell.items()
        }
    for selector_id in contract["confirmatory_selector_ids"]:
        contrasts[f"c048:{selector_id}"] = {
            cell_keys[cell_id]: float(decisions[selector_id]["selection_regret"])
            - float(decisions["astral"]["selection_regret"])
            for cell_id, decisions in decision_by_cell.items()
        }
    strongest = _dict(report.get("integrity_evidence")).get(
        "strongest_nonprivileged_selector_id"
    )
    upper_margins: dict[str, float] = {}
    for selector_id in contract["null_selector_ids"]:
        contrast_id = f"specificity:{selector_id}"
        contrasts[contrast_id] = {
            cell_keys[cell_id]: float(decisions[strongest]["selection_regret"])
            - float(decisions[selector_id]["selection_regret"])
            for cell_id, decisions in decision_by_cell.items()
        }
        upper_margins[contrast_id] = float(thresholds["specificity_advantage_max"])
    exchange = contract["rgs_exchange"]
    bootstrap = STATS.clustered_bootstrap_all(
        contrasts,
        family_categories=family_categories,
        seed=exchange["bootstrap_seed"],
        replicates=exchange["bootstrap_replicates"],
        upper_margins=upper_margins,
    )
    alpha = float(thresholds["alpha"])
    c047_adjusted = STATS.holm_adjust(
        {
            method_id: float(bootstrap[f"c047:{method_id}"]["one_sided_p_value_positive"])
            for method_id in contract["architecture_candidate_ids"]
        }
    )
    c048_adjusted = STATS.holm_adjust(
        {
            selector_id: float(bootstrap[f"c048:{selector_id}"]["one_sided_p_value_positive"])
            for selector_id in contract["confirmatory_selector_ids"]
        }
    )
    specificity_adjusted = STATS.holm_adjust(
        {
            selector_id: float(
                bootstrap[f"specificity:{selector_id}"][
                    "one_sided_p_value_at_most_margin"
                ]
            )
            for selector_id in contract["null_selector_ids"]
        }
    )
    c047_rows = []
    for method_id in contract["architecture_candidate_ids"]:
        stats = bootstrap[f"c047:{method_id}"]
        all_feasible = all(
            candidates[method_id]["feasible"] for candidates in candidate_by_cell.values()
        )
        gate = (
            all_feasible
            and float(stats["mean"]) >= float(thresholds["c047_practical_margin"])
            and float(stats["basic_lower_95"]) > 0.0
            and c047_adjusted[method_id] <= alpha
        )
        c047_rows.append(
            {
                "method_id": method_id,
                **stats,
                "holm_adjusted_p_value": c047_adjusted[method_id],
                "all_cells_feasible": all_feasible,
                "gate_passed": gate,
            }
        )
    c047_passed = any(row["gate_passed"] for row in c047_rows)
    c048_rows = []
    for selector_id in contract["confirmatory_selector_ids"]:
        stats = bootstrap[f"c048:{selector_id}"]
        all_astral_feasible = all(
            decisions["astral"]["selected_candidate_feasible"]
            for decisions in decision_by_cell.values()
        )
        gate = (
            all_astral_feasible
            and float(stats["mean"]) >= float(thresholds["c048_regret_advantage_margin"])
            and float(stats["basic_lower_95"]) > 0.0
            and c048_adjusted[selector_id] <= alpha
        )
        c048_rows.append(
            {
                "selector_id": selector_id,
                **stats,
                "holm_adjusted_p_value": c048_adjusted[selector_id],
                "gate_passed": gate,
            }
        )
    c048_passed = all(row["gate_passed"] for row in c048_rows)
    specificity_rows = []
    for selector_id in contract["null_selector_ids"]:
        stats = bootstrap[f"specificity:{selector_id}"]
        gate = (
            float(stats["basic_upper_95"]) <= float(thresholds["specificity_advantage_max"])
            and specificity_adjusted[selector_id] <= alpha
        )
        specificity_rows.append(
            {
                "selector_id": selector_id,
                **stats,
                "holm_adjusted_p_value": specificity_adjusted[selector_id],
                "gate_passed": gate,
            }
        )
    specificity_passed = all(row["gate_passed"] for row in specificity_rows)
    astral_results = [decisions["astral"] for decisions in decision_by_cell.values()]
    local_candidate = all(
        row["selected_candidate_feasible"]
        and float(row["selection_regret"]) <= float(thresholds["selection_regret_max"])
        for row in astral_results
    )
    scientific_candidate = local_candidate and c047_passed and c048_passed and specificity_passed
    statistical_results = {
        "c047_architecture_family": {
            "fixed_sequence_position": 2,
            "holm_alpha": alpha,
            "comparisons": c047_rows,
            "gate_passed": c047_passed,
        },
        "c048_selector_family": {
            "fixed_sequence_position": 3,
            "holm_alpha": alpha,
            "comparisons": c048_rows,
            "statistical_gate_passed": c048_passed,
            "claim_gate_passed": c047_passed and c048_passed,
        },
        "specificity_family": {
            "fixed_sequence_position": 4,
            "holm_alpha": alpha,
            "comparisons": specificity_rows,
            "gate_passed": specificity_passed,
        },
    }
    return {
        "statistical_results": statistical_results,
        "local_harness_candidate": local_candidate,
        "scientific_candidate_qualified": scientific_candidate,
        "bootstrap_digest": next(iter(bootstrap.values()))["sample_index_stream_sha256"],
    }, []


def _candidate_gates(
    candidate: dict[str, Any],
    thresholds: dict[str, Any],
    prefix: str,
) -> tuple[dict[str, bool], list[str]]:
    errors: list[str] = []
    unit_metrics = (
        "primary_future_unseen_score",
        "acquisition",
        "average_final_accuracy",
        "protected_retention",
        "maximum_protected_retention_drop",
        "forgetting",
        "calibration_mae",
        "brier_score",
    )
    signed_metrics = ("backward_transfer", "forward_transfer", "brier_degradation")
    for key in unit_metrics:
        if not _unit(candidate.get(key)):
            errors.append(f"{prefix}.{key}")
    for key in signed_metrics:
        if not _signed(candidate.get(key)):
            errors.append(f"{prefix}.{key}")
    violations = candidate.get("hard_governance_violations")
    if not isinstance(violations, int) or violations < 0:
        errors.append(f"{prefix}.hard_governance_violations")
    event_rows = candidate.get("recovery_events")
    event_success: list[bool] = []
    if not isinstance(event_rows, list) or not event_rows:
        errors.append(f"{prefix}.recovery_events")
    else:
        for index, raw_event in enumerate(event_rows):
            event = _dict(raw_event)
            event_prefix = f"{prefix}.recovery_events[{index}]"
            if not _unit(event.get("corruption_drop")):
                errors.append(f"{event_prefix}.corruption_drop")
            if not _unit(event.get("recovered_score_loss")):
                errors.append(f"{event_prefix}.recovered_score_loss")
            success = (
                _unit(event.get("corruption_drop"))
                and float(event["corruption_drop"]) >= float(thresholds["minimum_corruption_drop"])
                and event.get("rollback_digest_match") is True
                and event.get("replay_digest_match") is True
                and _unit(event.get("recovered_score_loss"))
                and float(event["recovered_score_loss"])
                <= float(thresholds["recovered_score_loss_max"])
            )
            if event.get("success") is not success:
                errors.append(f"{event_prefix}.success")
            event_success.append(success)
    if errors:
        return {}, errors
    gates = {
        "acquisition": candidate["acquisition"] >= float(thresholds["acquisition_min"]),
        "protected_retention": candidate["protected_retention"]
        >= float(thresholds["retention_min"]),
        "forgetting": candidate["forgetting"] <= float(thresholds["forgetting_max"]),
        "calibration_mae": candidate["calibration_mae"]
        <= float(thresholds["calibration_mae_max"]),
        "maximum_protected_retention_drop": candidate[
            "maximum_protected_retention_drop"
        ]
        <= float(thresholds["maximum_protected_retention_drop_max"]),
        "brier_degradation": candidate["brier_degradation"]
        <= float(thresholds["brier_degradation_max"]),
        "exact_recovery": all(event_success),
        "governance": candidate["hard_governance_violations"] == 0,
    }
    return gates, []


def _file_binding_errors(
    record: dict[str, Any],
    path_key: str,
    digest_key: str,
    label: str,
) -> list[str]:
    path_value = record.get(path_key)
    digest_value = record.get(digest_key)
    if not isinstance(path_value, str) or not path_value:
        return [f"{label}.path"]
    path = Path(path_value)
    if not path.is_file() or path.is_symlink():
        return [f"{label}.missing_or_symlink"]
    if not _sha256(digest_value) or prefixed_sha256(path) != digest_value:
        return [f"{label}.sha256"]
    return []


def _registry_by_id(value: Any, key: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for raw_row in value:
        row = _dict(raw_row)
        identifier = row.get(key)
        if isinstance(identifier, str) and identifier and identifier not in result:
            result[identifier] = row
    return result


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _unit(value: Any) -> bool:
    return _finite(value) and 0.0 <= float(value) <= 1.0


def _signed(value: Any) -> bool:
    return _finite(value) and -1.0 <= float(value) <= 1.0


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA256_PATTERN.fullmatch(value))
