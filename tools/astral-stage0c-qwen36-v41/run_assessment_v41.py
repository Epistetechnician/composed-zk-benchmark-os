#!/usr/bin/env python3
"""Measure V41 assessment effects after accepted independent review.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

The runner requires valid V41 custody, a prediction lock, and an accepted
review receipt. It materializes assessment predictions and direct effects only
after those gates, then retains aggregate metrics and document-cluster
sufficient statistics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import protocol_v41 as protocol
import run_preassessment_v41 as preassessment
import validate_preassessment_v41 as preassessment_validator


ASSESSMENT_CLASSIFICATION = "AssessmentEffectsMeasured"
ASSESSMENT_CLAIM_CEILING = "LocalDevelopmentV41AssessmentAggregateEffects"


def _sha256_file(path: Path) -> str:
    return protocol.sha256_file(path)


def _canonical_digest(value: Any) -> str:
    return protocol.canonical_digest(value)


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


def _write_json(path: Path, value: Any) -> None:
    protocol.write_json(path, value)


def _state_from_json(value: dict[str, Any]) -> dict[str, Any]:
    if set(value) == {"target_mean"}:
        return {"target_mean": float(value["target_mean"])}
    return {
        "alpha": float(value["alpha"]),
        "feature_mean": np.asarray(value["feature_mean"], dtype=np.float64),
        "feature_scale": np.asarray(value["feature_scale"], dtype=np.float64),
        "target_mean": float(value["target_mean"]),
        "coefficients": np.asarray(value["coefficients"], dtype=np.float64),
    }


def _metric(predictions: np.ndarray, targets: np.ndarray) -> dict[str, float | int]:
    errors = predictions - targets
    return {
        "count": int(len(targets)),
        "mse": float(np.mean(errors**2)),
        "rmse": float(math.sqrt(np.mean(errors**2))),
        "mae": float(np.mean(np.abs(errors))),
        "mean_error": float(np.mean(errors)),
    }


def _aggregate(values: np.ndarray) -> dict[str, float | int]:
    if len(values) == 0 or not np.isfinite(values).all():
        raise protocol.ProtocolError("cannot aggregate empty or non-finite values")
    return {
        "count": int(len(values)),
        "mean": float(values.mean()),
        "std": float(values.std()),
        "min": float(values.min()),
        "max": float(values.max()),
        "mean_abs": float(np.abs(values).mean()),
    }


def _verify_review(
    review_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
) -> dict[str, Any]:
    packet_path = review_root / "independent-review-packet.json"
    receipt_path = review_root / "independent-review-receipt.json"
    sidecar_path = review_root / "independent-review-packet.sha256"
    packet = _strict_json(packet_path)
    receipt = _strict_json(receipt_path)
    if not isinstance(packet, dict) or not isinstance(receipt, dict):
        raise protocol.ProtocolError("review documents must be objects")
    if packet.get("protocol") != protocol.PROTOCOL_ID or receipt.get("protocol") != protocol.PROTOCOL_ID:
        raise protocol.ProtocolError("review protocol mismatch")
    if packet.get("state_slice") != protocol.STATE_SLICE or receipt.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("review state slice mismatch")
    if packet.get("review_status") != "ACCEPTED_FOR_ASSESSMENT" or packet.get("independent_reviewer_receipt_present") is not True:
        raise protocol.ProtocolError("review is not accepted")
    if receipt.get("classification") != "IndependentReviewAccepted" or receipt.get("review_decision") != "APPROVED_FOR_ASSESSMENT":
        raise protocol.ProtocolError("review decision is not accepted")
    if receipt.get("assessment_effects_present") is not False or receipt.get("assessment_effects_measured") is not False:
        raise protocol.ProtocolError("review receipt was created after assessment effects")
    if sidecar_path.read_text(encoding="utf-8") != f"{_sha256_file(packet_path)}  independent-review-packet.json\n":
        raise protocol.ProtocolError("review packet sidecar mismatch")
    expected_sources = {
        "corpus_root": str(corpus_root.resolve()),
        "panel_root": str(panel_root.resolve()),
        "preassessment_root": str(preassessment_root.resolve()),
        "qualification_root": str(qualification_root.resolve()),
        "model_root": str(model_root.resolve()),
    }
    if packet.get("source_bundles") != expected_sources:
        raise protocol.ProtocolError("review packet source bundle mismatch")
    if packet.get("review_decision_digest") != _canonical_digest(receipt) or packet.get("review_receipt_sha256") != _canonical_digest(receipt):
        raise protocol.ProtocolError("review receipt digest mismatch")
    expected = {
        "corpus_manifest_sha256": _sha256_file(corpus_root / "corpus-manifest.json"),
        "corpus_validator_receipt_sha256": _sha256_file(corpus_root / "validator-receipt.json"),
        "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
        "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
        "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
        "panel_validator_receipt_sha256": _sha256_file(panel_root / "validator-receipt.json"),
        "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_root / "validator-receipt.json"),
        "preassessment_run_manifest_sha256": _sha256_file(preassessment_root / "run-manifest.json"),
        "fit_tune_summary_sha256": _sha256_file(preassessment_root / "fit-tune-summary.json"),
        "prediction_lock_sha256": _sha256_file(preassessment_root / "prediction-lock.json"),
        "preassessment_validator_receipt_sha256": _sha256_file(preassessment_root / "validator-receipt.json"),
        "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
    }
    if packet.get("digests") != expected:
        raise protocol.ProtocolError("review packet digest map mismatch")
    return receipt


def _measure_assessment_effects(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    split_families: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    if len(families) != protocol.FAMILIES_PER_SPLIT or any(family["split"] != "assessment" for family in families):
        raise protocol.ProtocolError("assessment family census or split is invalid")
    clean = preassessment._capture_clean(model, base_layers, families, cache, response_ids, mx)
    target_effects: list[float] = []
    matched_effects: list[float] = []
    documents: list[int] = []
    norm_errors: list[float] = []
    donor_violations = 0
    for family in families:
        family_id = family["family_id"]
        current = clean[family_id]
        ordinary = current["ordinary_vector"]
        counterfactual = current["counterfactual_vector"]
        ordinary_clean_margin = preassessment._margin(current["ordinary_logits"], "A")
        counterfactual_clean_margin = preassessment._margin(current["counterfactual_logits"], "B")
        _, ordinary_pair_logits = preassessment._forward(model, base_layers, cache[family_id]["ordinary"], counterfactual, response_ids, mx)
        _, counterfactual_pair_logits = preassessment._forward(model, base_layers, cache[family_id]["counterfactual"], ordinary, response_ids, mx)
        target_effects.append(
            0.5
            * (
                preassessment._margin(ordinary_pair_logits, "A")
                - ordinary_clean_margin
                + preassessment._margin(counterfactual_pair_logits, "B")
                - counterfactual_clean_margin
            )
        )
        ordinary_donor = preassessment._matched_family(family, split_families)
        counterfactual_donor = preassessment._matched_family(family, split_families)
        if ordinary_donor["gutenberg_id"] == family["gutenberg_id"] or counterfactual_donor["gutenberg_id"] == family["gutenberg_id"]:
            donor_violations += 1
        ordinary_replacement, ordinary_error = preassessment._norm_match(
            clean[ordinary_donor["family_id"]]["ordinary_vector"], ordinary
        )
        counterfactual_replacement, counterfactual_error = preassessment._norm_match(
            clean[counterfactual_donor["family_id"]]["counterfactual_vector"], counterfactual
        )
        norm_errors.extend([ordinary_error, counterfactual_error])
        _, ordinary_match_logits = preassessment._forward(model, base_layers, cache[family_id]["ordinary"], ordinary_replacement, response_ids, mx)
        _, counterfactual_match_logits = preassessment._forward(model, base_layers, cache[family_id]["counterfactual"], counterfactual_replacement, response_ids, mx)
        matched_effects.append(
            0.5
            * (
                preassessment._margin(ordinary_match_logits, "A")
                - ordinary_clean_margin
                + preassessment._margin(counterfactual_match_logits, "B")
                - counterfactual_clean_margin
            )
        )
        documents.append(int(family["gutenberg_id"]))
    return {
        "target_effects": np.asarray(target_effects, dtype=np.float64),
        "matched_effects": np.asarray(matched_effects, dtype=np.float64),
        "documents": documents,
        "matched_norm_relative_error_max": max(norm_errors, default=0.0),
        "matched_donor_violations": donor_violations,
    }


def _cluster_bootstrap(document_stats: list[dict[str, Any]]) -> dict[str, Any]:
    if len(document_stats) != protocol.DOCUMENTS_PER_SPLIT:
        raise protocol.ProtocolError("assessment document cluster census mismatch")
    rng = np.random.default_rng(protocol.BOOTSTRAP_SEED)
    indices = rng.integers(0, len(document_stats), size=(10000, len(document_stats)))
    pair_sums = np.asarray([float(row["pair_squared_error_sum"]) for row in document_stats])
    constant_sums = np.asarray([float(row["constant_squared_error_sum"]) for row in document_stats])
    counts = np.asarray([int(row["count"]) for row in document_stats], dtype=np.float64)
    sampled_counts = counts[indices].sum(axis=1)
    deltas = np.sqrt(pair_sums[indices].sum(axis=1) / sampled_counts) - np.sqrt(constant_sums[indices].sum(axis=1) / sampled_counts)
    return {
        "seed": protocol.BOOTSTRAP_SEED,
        "replicates": int(len(deltas)),
        "document_clusters": len(document_stats),
        "rmse_delta_025": float(np.quantile(deltas, 0.025)),
        "rmse_delta_050": float(np.quantile(deltas, 0.5)),
        "rmse_delta_095_upper": float(np.quantile(deltas, 0.95)),
    }


def run_assessment(
    preassessment_root: Path,
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    review_root: Path,
    model_root: Path,
    output_root: Path,
    repository_root: Path,
) -> Path:
    preassessment_root = preassessment_root.resolve()
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    review_root = review_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    protocol.assert_external(review_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite assessment root: {output_root}")
    pre_receipt = preassessment_validator.validate(
        preassessment_root, panel_root, corpus_root, qualification_root, model_root, repository_root
    )
    if not pre_receipt["valid"]:
        raise protocol.ProtocolError("preassessment failed independent validation")
    review_receipt = _verify_review(
        review_root, preassessment_root, panel_root, corpus_root, qualification_root, model_root
    )
    lock = _strict_json(preassessment_root / "prediction-lock.json")
    summary_before = _strict_json(preassessment_root / "fit-tune-summary.json")
    tune_delta = float(summary_before["panels"][protocol.PRIMARY_CONTROL]["tune_rmse"]) - float(summary_before["panels"]["constant"]["tune_rmse"])
    if tune_delta > -protocol.UTILITY_RMSE_MARGIN:
        raise protocol.ProtocolError("tune utility gate failed; assessment remains closed")
    registry_document = _strict_json(panel_root / "concept-registry.json")
    registry = registry_document.get("families")
    if not isinstance(registry, list) or len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("assessment panel registry is invalid")
    assessment_families = sorted(
        [family for family in registry if family.get("split") == "assessment"],
        key=lambda family: family["family_id"],
    )
    expected_ids = [family["family_id"] for family in assessment_families]
    if lock.get("assessment_family_ids") != expected_ids:
        raise protocol.ProtocolError("assessment family order does not match prediction lock")
    states_document = lock.get("estimator_states")
    if not isinstance(states_document, dict) or set(states_document) != set(preassessment.ESTIMATOR_NAMES):
        raise protocol.ProtocolError("prediction lock estimator controls mismatch")
    states = {name: _state_from_json(value) for name, value in states_document.items()}

    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("assessment layer count mismatch")
    response_ids = preassessment._strict_response_ids(tokenizer)
    token_cache = preassessment._token_cache(registry, tokenizer)

    # This is the locked-prediction phase. It precedes every assessment
    # replacement execution below.
    assessment_features = preassessment._measure_features(
        model, base_layers, assessment_families, token_cache, response_ids, mx
    )
    panel_digest = _sha256_file(panel_root / "panel-manifest.json")
    shuffled_order = preassessment._row_permutation(
        assessment_features["family_ids"], "assessment", panel_digest
    )
    prediction_features = {
        protocol.PRIMARY_CONTROL: assessment_features["pair_features"],
        "clean_activation_only": assessment_features["clean_features"],
        "text_only": assessment_features["text_features"],
        "shuffled": assessment_features["pair_features"][shuffled_order],
        "constant": np.empty((len(assessment_families), 0)),
    }
    predictions = {
        name: preassessment._predict(states[name], values)
        for name, values in prediction_features.items()
    }
    locked_prediction_digest = _canonical_digest(
        {
            "family_ids": assessment_features["family_ids"],
            "prediction_digest_inputs": {
                name: {
                    "count": int(len(values)),
                    "feature_width": int(values.shape[1]),
                }
                for name, values in prediction_features.items()
            },
        }
    )

    measured = _measure_assessment_effects(
        model,
        base_layers,
        assessment_families,
        assessment_families,
        token_cache,
        response_ids,
        mx,
    )
    effects = measured["target_effects"]
    matched_effects = measured["matched_effects"]
    metrics = {name: _metric(prediction, effects) for name, prediction in predictions.items()}
    matched_summary = _aggregate(matched_effects)
    matched_summary.update(
        {
            "norm_relative_error_max": measured["matched_norm_relative_error_max"],
            "donor_violations": measured["matched_donor_violations"],
            "used_for_tuning": False,
        }
    )
    document_stats: list[dict[str, Any]] = []
    for document_id in sorted(set(measured["documents"])):
        mask = np.asarray([value == document_id for value in measured["documents"]])
        document_stats.append(
            {
                "gutenberg_id": document_id,
                "count": int(mask.sum()),
                "pair_squared_error_sum": float(np.sum((predictions[protocol.PRIMARY_CONTROL][mask] - effects[mask]) ** 2)),
                "constant_squared_error_sum": float(np.sum((predictions["constant"][mask] - effects[mask]) ** 2)),
            }
        )
    assessment_delta = metrics[protocol.PRIMARY_CONTROL]["rmse"] - metrics["constant"]["rmse"]
    bootstrap = _cluster_bootstrap(document_stats)
    gates = {
        "tune_utility": tune_delta <= -protocol.UTILITY_RMSE_MARGIN,
        "assessment_utility": assessment_delta <= -protocol.UTILITY_RMSE_MARGIN,
        "bootstrap": bootstrap["rmse_delta_095_upper"] < -protocol.BOOTSTRAP_RMSE_MARGIN,
        "beats_clean_activation": metrics[protocol.PRIMARY_CONTROL]["rmse"] <= metrics["clean_activation_only"]["rmse"] - protocol.CONTROL_RMSE_MARGIN,
        "beats_shuffled": metrics[protocol.PRIMARY_CONTROL]["rmse"] <= metrics["shuffled"]["rmse"] - protocol.CONTROL_RMSE_MARGIN,
        "text_not_better": metrics["text_only"]["rmse"] >= metrics[protocol.PRIMARY_CONTROL]["rmse"],
        "matched_control": abs(float(matched_effects.mean())) <= protocol.MATCHED_CONTROL_MEAN_ABS_MAX and measured["matched_donor_violations"] == 0,
        "assessment_target_non_degenerate": float(effects.std()) >= protocol.MIN_ASSESSMENT_TARGET_STD,
        "document_family_census": len(document_stats) == protocol.DOCUMENTS_PER_SPLIT and all(row["count"] == protocol.FAMILIES_PER_DOCUMENT for row in document_stats),
    }
    summary = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": ASSESSMENT_CLAIM_CEILING,
        "classification": ASSESSMENT_CLASSIFICATION,
        "protocol_source_sha256": _sha256_file(Path(protocol.__file__).resolve()),
        "runner_source_sha256": _sha256_file(Path(__file__).resolve()),
        "features_source_sha256": _sha256_file(Path(preassessment.features.__file__).resolve()),
        "corpus_manifest_sha256": _sha256_file(corpus_root / "corpus-manifest.json"),
        "corpus_validator_receipt_sha256": _sha256_file(corpus_root / "validator-receipt.json"),
        "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
        "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
        "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
        "preassessment_run_manifest_sha256": _sha256_file(preassessment_root / "run-manifest.json"),
        "preassessment_prediction_lock_sha256": _sha256_file(preassessment_root / "prediction-lock.json"),
        "preassessment_validator_receipt_sha256": _sha256_file(preassessment_root / "validator-receipt.json"),
        "independent_review_receipt_sha256": _sha256_file(review_root / "independent-review-receipt.json"),
        "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_root / "validator-receipt.json"),
        "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
        "feature_map_sha256": protocol.feature_map_digest(),
        "target_layer": protocol.TARGET_LAYER,
        "assessment_family_count": len(assessment_families),
        "panels": metrics,
        "matched_control": matched_summary,
        "target_effect": _aggregate(effects),
        "document_squared_error_sufficient_statistics": document_stats,
        "primary_metric": {
            "name": "delta_rmse",
            "tune": tune_delta,
            "assessment": assessment_delta,
            "definition": "rmse(directional_block_primary)-rmse(constant)",
        },
        "cluster_bootstrap": bootstrap,
        "gates": gates,
        "locked_prediction_digest": locked_prediction_digest,
        "review_receipt_digest": _canonical_digest(review_receipt),
        "prediction_lock_preserved": True,
        "assessment_effects_present": True,
        "assessment_effects_measured": True,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
    }
    run_manifest = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": ASSESSMENT_CLAIM_CEILING,
        "classification": ASSESSMENT_CLASSIFICATION,
        "protocol_source_sha256": summary["protocol_source_sha256"],
        "runner_source_sha256": summary["runner_source_sha256"],
        "corpus_manifest_sha256": summary["corpus_manifest_sha256"],
        "corpus_validator_receipt_sha256": summary["corpus_validator_receipt_sha256"],
        "panel_manifest_sha256": summary["panel_manifest_sha256"],
        "preassessment_run_manifest_sha256": summary["preassessment_run_manifest_sha256"],
        "preassessment_prediction_lock_sha256": summary["preassessment_prediction_lock_sha256"],
        "preassessment_validator_receipt_sha256": summary["preassessment_validator_receipt_sha256"],
        "independent_review_receipt_sha256": summary["independent_review_receipt_sha256"],
        "qualification_result_sha256": summary["qualification_result_sha256"],
        "qualification_validator_receipt_sha256": summary["qualification_validator_receipt_sha256"],
        "model_manifest_sha256": summary["model_manifest_sha256"],
        "assessment_family_count": len(assessment_families),
        "assessment_effects_present": True,
        "assessment_effects_measured": True,
        "prediction_locked_before_assessment": True,
        "independent_review_accepted": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "summary_sha256": _canonical_digest(summary),
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent))
    )
    try:
        _write_json(staging / "assessment-summary.json", summary)
        _write_json(staging / "assessment-run-manifest.json", run_manifest)
        if output_root.exists():
            raise protocol.ProtocolError(f"assessment root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preassessment-root", type=Path, required=True)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = run_assessment(
            args.preassessment_root,
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.review_root,
            args.model,
            args.output_root,
            args.repository_root,
        )
    except (OSError, ImportError, KeyError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"classification": "AssessmentFailed", "reason": f"{type(exc).__name__}:{exc}"}))
        return 2
    print(json.dumps({"assessment_root": str(root), "classification": ASSESSMENT_CLASSIFICATION, "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
