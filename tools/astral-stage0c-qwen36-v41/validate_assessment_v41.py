#!/usr/bin/env python3
"""Independently validate the aggregate-only V41 assessment bundle.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

The validator checks custody, accepted review, prediction ordering, aggregate
retention, direct-effect gates, and claim boundaries. It never reruns model
effects.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import protocol_v41 as protocol
import run_assessment_v41 as assessment
import run_preassessment_v41 as preassessment
import validate_preassessment_v41 as preassessment_validator


EXPECTED_FILES = {"assessment-summary.json", "assessment-run-manifest.json"}
FORBIDDEN_KEYS = frozenset(
    {
        "prompts",
        "source_excerpts",
        "tokens",
        "raw_activations",
        "activations",
        "raw_logits",
        "logits",
        "raw_traces",
        "traces",
        "per_family_effects",
        "per_family_predictions",
        "credentials",
        "pii",
    }
)


def _scan_forbidden(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{path}.{key}")
            errors.extend(_scan_forbidden(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_forbidden(nested, f"{path}[{index}]"))
    return errors


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=reject_constant,
    )


def validate(
    assessment_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    review_root: Path,
    model_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    assessment_root = assessment_root.resolve()
    try:
        protocol.assert_external(assessment_root, repository_root)
        summary = _strict_json(assessment_root / "assessment-summary.json")
        run = _strict_json(assessment_root / "assessment-run-manifest.json")
        if not isinstance(summary, dict) or not isinstance(run, dict):
            errors.append("assessment_documents_not_objects")
            summary, run = {}, {}
        errors.extend(_scan_forbidden(summary))
        errors.extend(_scan_forbidden(run))
        for document in (summary, run):
            if document.get("protocol") != protocol.PROTOCOL_ID:
                errors.append("protocol_mismatch")
            if document.get("state_slice") != protocol.STATE_SLICE:
                errors.append("state_slice_mismatch")
            if document.get("assessment_effects_present") is not True or document.get("assessment_effects_measured") is not True:
                errors.append("assessment_effect_state_invalid")
            if document.get("prediction_locked_before_assessment") is not True:
                errors.append("prediction_lock_state_invalid")
            if document.get("raw_intermediates_retained") is not False or document.get("aggregate_only") is not True:
                errors.append("retention_state_invalid")
            if document.get("network_access") is not False or document.get("model_training") is not False:
                errors.append("execution_boundary_invalid")
            if document.get("stage_0c") is not False or document.get("stage_1") is not False or document.get("accepted_evidence") is not False:
                errors.append("claim_boundary_invalid")
        if summary.get("classification") != assessment.ASSESSMENT_CLASSIFICATION or run.get("classification") != assessment.ASSESSMENT_CLASSIFICATION:
            errors.append("classification_mismatch")
        if run.get("independent_review_accepted") is not True:
            errors.append("review_gate_missing")

        pre_receipt = preassessment_validator.validate(
            preassessment_root,
            panel_root,
            corpus_root,
            qualification_root,
            model_root,
            repository_root,
        )
        if not pre_receipt["valid"]:
            errors.append("preassessment_validation_failed")
        assessment._verify_review(
            review_root.resolve(),
            preassessment_root.resolve(),
            panel_root.resolve(),
            corpus_root.resolve(),
            qualification_root.resolve(),
            model_root.resolve(),
        )
        expected_digests = {
            "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
            "corpus_manifest_sha256": protocol.sha256_file(corpus_root / "corpus-manifest.json"),
            "corpus_validator_receipt_sha256": protocol.sha256_file(corpus_root / "validator-receipt.json"),
            "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
            "preassessment_run_manifest_sha256": protocol.sha256_file(preassessment_root / "run-manifest.json"),
            "preassessment_prediction_lock_sha256": protocol.sha256_file(preassessment_root / "prediction-lock.json"),
            "preassessment_validator_receipt_sha256": protocol.sha256_file(preassessment_root / "validator-receipt.json"),
            "independent_review_receipt_sha256": protocol.sha256_file(review_root / "independent-review-receipt.json"),
            "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
            "qualification_validator_receipt_sha256": protocol.sha256_file(qualification_root / "validator-receipt.json"),
            "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        }
        for key, expected in expected_digests.items():
            if summary.get(key) != expected:
                errors.append(f"summary_digest_mismatch:{key}")
            if run.get(key) != expected:
                errors.append(f"run_digest_mismatch:{key}")
        if summary.get("feature_map_sha256") != protocol.feature_map_digest():
            errors.append("feature_map_digest_mismatch")
        if run.get("runner_source_sha256") != protocol.sha256_file(Path(assessment.__file__).resolve()):
            errors.append("runner_source_mismatch")
        if run.get("summary_sha256") != protocol.canonical_digest(summary):
            errors.append("summary_digest_binding_mismatch")
        if summary.get("assessment_family_count") != protocol.FAMILIES_PER_SPLIT or run.get("assessment_family_count") != protocol.FAMILIES_PER_SPLIT:
            errors.append("assessment_family_count_mismatch")

        panels = summary.get("panels")
        expected_panel_names = set(preassessment.ESTIMATOR_NAMES)
        if not isinstance(panels, dict) or set(panels) != expected_panel_names:
            errors.append("panel_names_mismatch")
        else:
            for name, metrics in panels.items():
                if not isinstance(metrics, dict) or metrics.get("count") != protocol.FAMILIES_PER_SPLIT:
                    errors.append(f"panel_count_mismatch:{name}")
                for metric_name in ("mse", "rmse", "mae", "mean_error"):
                    if not _finite(metrics.get(metric_name)):
                        errors.append(f"panel_metric_invalid:{name}:{metric_name}")
        matched = summary.get("matched_control", {})
        if matched.get("count") != protocol.FAMILIES_PER_SPLIT or not all(_finite(matched.get(name)) for name in ("mean", "std", "min", "max", "mean_abs")):
            errors.append("matched_aggregate_invalid")
        if matched.get("used_for_tuning") is not False or matched.get("donor_violations") != 0 or not _finite(matched.get("norm_relative_error_max")) or float(matched.get("norm_relative_error_max", 1.0)) > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
            errors.append("matched_control_census_invalid")
        target = summary.get("target_effect", {})
        if target.get("count") != protocol.FAMILIES_PER_SPLIT or not all(_finite(target.get(name)) for name in ("mean", "std", "min", "max", "mean_abs")):
            errors.append("target_aggregate_invalid")
        stats = summary.get("document_squared_error_sufficient_statistics")
        if not isinstance(stats, list) or len(stats) != protocol.DOCUMENTS_PER_SPLIT or sum(int(row.get("count", -1)) for row in stats if isinstance(row, dict)) != protocol.FAMILIES_PER_SPLIT:
            errors.append("document_sufficient_statistics_invalid")
        else:
            seen_documents: set[int] = set()
            for row in stats:
                if set(row) != {"gutenberg_id", "count", "pair_squared_error_sum", "constant_squared_error_sum"} or row.get("count") != protocol.FAMILIES_PER_DOCUMENT or not _finite(row.get("pair_squared_error_sum")) or not _finite(row.get("constant_squared_error_sum")):
                    errors.append("document_sufficient_statistics_row_invalid")
                if row.get("gutenberg_id") in seen_documents:
                    errors.append("document_sufficient_statistics_duplicate")
                seen_documents.add(row.get("gutenberg_id"))
        bootstrap = summary.get("cluster_bootstrap", {})
        if bootstrap.get("seed") != protocol.BOOTSTRAP_SEED or bootstrap.get("replicates") != 10000 or bootstrap.get("document_clusters") != protocol.DOCUMENTS_PER_SPLIT or not _finite(bootstrap.get("rmse_delta_095_upper")):
            errors.append("bootstrap_invalid")
        primary = summary.get("primary_metric", {})
        if primary.get("name") != "delta_rmse" or not _finite(primary.get("tune")) or not _finite(primary.get("assessment")):
            errors.append("primary_metric_invalid")
        gates = summary.get("gates")
        expected_gate_names = {
            "tune_utility",
            "assessment_utility",
            "bootstrap",
            "beats_clean_activation",
            "beats_shuffled",
            "text_not_better",
            "matched_control",
            "assessment_target_non_degenerate",
            "document_family_census",
        }
        if not isinstance(gates, dict) or set(gates) != expected_gate_names or not all(isinstance(value, bool) for value in gates.values()):
            errors.append("gate_record_invalid")
        else:
            tune_summary = _strict_json(preassessment_root / "fit-tune-summary.json")
            expected_gates = {
                "tune_utility": float(tune_summary["tune_delta_rmse"]) <= -protocol.UTILITY_RMSE_MARGIN,
                "assessment_utility": float(primary["assessment"]) <= -protocol.UTILITY_RMSE_MARGIN,
                "bootstrap": float(bootstrap["rmse_delta_095_upper"]) < -protocol.BOOTSTRAP_RMSE_MARGIN,
                "beats_clean_activation": float(panels[protocol.PRIMARY_CONTROL]["rmse"]) <= float(panels["clean_activation_only"]["rmse"]) - protocol.CONTROL_RMSE_MARGIN,
                "beats_shuffled": float(panels[protocol.PRIMARY_CONTROL]["rmse"]) <= float(panels["shuffled"]["rmse"]) - protocol.CONTROL_RMSE_MARGIN,
                "text_not_better": float(panels["text_only"]["rmse"]) >= float(panels[protocol.PRIMARY_CONTROL]["rmse"]),
                "matched_control": abs(float(matched["mean"])) <= protocol.MATCHED_CONTROL_MEAN_ABS_MAX and matched["donor_violations"] == 0,
                "assessment_target_non_degenerate": float(target["std"]) >= protocol.MIN_ASSESSMENT_TARGET_STD,
                "document_family_census": isinstance(stats, list) and len(stats) == protocol.DOCUMENTS_PER_SPLIT and all(row.get("count") == protocol.FAMILIES_PER_DOCUMENT for row in stats),
            }
            if gates != expected_gates:
                errors.append("gate_values_do_not_match_aggregates")
        actual_files = {
            candidate.relative_to(assessment_root).as_posix()
            for candidate in assessment_root.rglob("*")
            if candidate.is_file()
        }
        allowed_files = EXPECTED_FILES | {"validator-receipt.json"}
        if not EXPECTED_FILES <= actual_files or not actual_files <= allowed_files:
            errors.append("output_census_mismatch")
    except (OSError, json.JSONDecodeError, TypeError, KeyError, AttributeError, protocol.ProtocolError, ValueError) as exc:
        errors.append(f"validator_error:{type(exc).__name__}:{exc}")
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": assessment.ASSESSMENT_CLAIM_CEILING,
        "classification": assessment.ASSESSMENT_CLASSIFICATION if not errors else "AssessmentInvalid",
        "valid": not errors,
        "errors": errors,
        "assessment_run_manifest_sha256": protocol.sha256_file(assessment_root / "assessment-run-manifest.json") if (assessment_root / "assessment-run-manifest.json").is_file() else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment_root", type=Path)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(
        args.assessment_root,
        args.preassessment_root,
        args.panel_root,
        args.corpus_root,
        args.qualification_root,
        args.review_root,
        args.model,
        args.repository_root,
    )
    if args.write_receipt:
        protocol.write_json(args.assessment_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
