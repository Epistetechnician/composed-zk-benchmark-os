#!/usr/bin/env python3
"""Measure the V39 assessment effects after independent review.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This runner requires the digest-bound preassessment prediction lock and an
accepted independent-review receipt. It measures assessment target and
matched-control effects using the sealed configuration, computes aggregate
prediction metrics, and retains no per-family effects or raw intermediates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus_v39 as corpus
import panel_v39 as panel
import protocol_v39 as protocol
import run_preassessment_v39 as preassessment
import validate_preassessment_v39 as preassessment_validator


ASSESSMENT_CLAIM_CEILING = "LocalDevelopmentV39AssessmentAggregateEffects"
ASSESSMENT_CLASSIFICATION = "AssessmentEffectsMeasured"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )


def _verify_review(
    review_root: Path,
    preassessment_root: Path,
    panel_root: Path,
    qualification_root: Path,
    model_root: Path,
) -> dict[str, Any]:
    packet_path = review_root / "independent-review-packet.json"
    receipt_path = review_root / "independent-review-receipt.json"
    sidecar_path = review_root / "independent-review-packet.sha256"
    packet = _strict_json(packet_path)
    receipt = _strict_json(receipt_path)
    if not isinstance(packet, dict) or not isinstance(receipt, dict):
        raise ValueError("independent review documents must be objects")
    if packet.get("state_slice") != protocol.STATE_SLICE or receipt.get("state_slice") != protocol.STATE_SLICE:
        raise ValueError("independent review state slice mismatch")
    if packet.get("review_status") != "ACCEPTED_FOR_ASSESSMENT":
        raise ValueError("independent review has not accepted assessment")
    if packet.get("independent_reviewer_receipt_present") is not True:
        raise ValueError("independent review receipt flag is absent")
    if receipt.get("classification") != "IndependentReviewAccepted" or receipt.get("review_decision") != "APPROVED_FOR_ASSESSMENT":
        raise ValueError("independent review decision is not accepted")
    if receipt.get("assessment_effects_present") is not False or receipt.get("assessment_effects_measured") is not False:
        raise ValueError("review receipt was created after assessment effects")
    sidecar = sidecar_path.read_text(encoding="utf-8")
    if sidecar != f"{_sha256_file(packet_path)}  independent-review-packet.json\n":
        raise ValueError("independent review packet sidecar mismatch")
    receipt_digest = _canonical_digest(receipt)
    if packet.get("review_decision_digest") != receipt_digest or packet.get("review_receipt_sha256") != receipt_digest:
        raise ValueError("independent review receipt binding mismatch")
    if receipt.get("panel_manifest_sha256") != _sha256_file(panel_root / "panel-manifest.json"):
        raise ValueError("review panel binding mismatch")
    if receipt.get("concept_registry_sha256") != _sha256_file(panel_root / "concept-registry.json"):
        raise ValueError("review registry binding mismatch")
    if receipt.get("split_manifest_sha256") != _sha256_file(panel_root / "split-manifest.json"):
        raise ValueError("review split binding mismatch")
    if receipt.get("preassessment_validator_receipt_sha256") != _sha256_file(preassessment_root / "validator-receipt.json"):
        raise ValueError("review preassessment binding mismatch")
    if receipt.get("qualification_result_sha256") != _sha256_file(qualification_root / "qualification-result.json"):
        raise ValueError("review qualification binding mismatch")
    if receipt.get("qualification_validator_receipt_sha256") != _sha256_file(qualification_root / "validator-receipt.json"):
        raise ValueError("review qualification receipt binding mismatch")
    pre_result = _strict_json(qualification_root / "qualification-result.json")
    if receipt.get("model_manifest_sha256") != pre_result.get("model_manifest_sha256"):
        raise ValueError("review model binding mismatch")
    return receipt


def _measure_assessment_effects(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    all_families: list[dict[str, Any]],
    token_cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    clean = preassessment._capture_clean_split(
        model,
        base_layers,
        families,
        token_cache,
        response_ids,
        mx,
    )
    target_effects: list[float] = []
    matched_effects: list[float] = []
    match_length_deltas: list[int] = []
    for family in families:
        family_id = family["family_id"]
        current = clean[family_id]
        ordinary_vector = current["ordinary_vector"]
        counterfactual_vector = current["counterfactual_vector"]
        ordinary_clean_margin = preassessment._margin(current["ordinary_logits"], "A")
        counterfactual_clean_margin = preassessment._margin(current["counterfactual_logits"], "B")
        _, ordinary_pair_logits = preassessment._forward(
            model,
            base_layers,
            token_cache[family_id]["ordinary"],
            preassessment._norm_match(counterfactual_vector, ordinary_vector),
            response_ids,
            mx,
        )
        _, counterfactual_pair_logits = preassessment._forward(
            model,
            base_layers,
            token_cache[family_id]["counterfactual"],
            preassessment._norm_match(ordinary_vector, counterfactual_vector),
            response_ids,
            mx,
        )
        target_effects.append(
            0.5 * (
                preassessment._margin(ordinary_pair_logits, "A") - ordinary_clean_margin
                + preassessment._margin(counterfactual_pair_logits, "B") - counterfactual_clean_margin
            )
        )
        ordinary_match = preassessment._matched_family(
            family, "ordinary", all_families, token_cache
        )
        counterfactual_match = preassessment._matched_family(
            family, "counterfactual", all_families, token_cache
        )
        _, ordinary_match_logits = preassessment._forward(
            model,
            base_layers,
            token_cache[family_id]["ordinary"],
            preassessment._norm_match(
                clean[ordinary_match["family_id"]]["ordinary_vector"],
                ordinary_vector,
            ),
            response_ids,
            mx,
        )
        _, counterfactual_match_logits = preassessment._forward(
            model,
            base_layers,
            token_cache[family_id]["counterfactual"],
            preassessment._norm_match(
                clean[counterfactual_match["family_id"]]["counterfactual_vector"],
                counterfactual_vector,
            ),
            response_ids,
            mx,
        )
        matched_effects.append(
            0.5 * (
                preassessment._margin(ordinary_match_logits, "A") - ordinary_clean_margin
                + preassessment._margin(counterfactual_match_logits, "B") - counterfactual_clean_margin
            )
        )
        match_length_deltas.extend(
            [
                abs(
                    token_cache[ordinary_match["family_id"]]["ordinary_length"]
                    - token_cache[family_id]["ordinary_length"]
                ),
                abs(
                    token_cache[counterfactual_match["family_id"]]["counterfactual_length"]
                    - token_cache[family_id]["counterfactual_length"]
                ),
            ]
        )
    return {
        "target_effects": np.asarray(target_effects, dtype=np.float64),
        "matched_effects": np.asarray(matched_effects, dtype=np.float64),
        "matched_sequence_length_delta_max": max(match_length_deltas, default=0),
    }


def _metric(predictions: np.ndarray, effects: np.ndarray) -> dict[str, float | int]:
    error = predictions - effects
    mse = float(np.mean(error**2))
    return {
        "count": int(len(effects)),
        "mse": mse,
        "rmse": math.sqrt(mse),
        "mae": float(np.mean(np.abs(error))),
        "mean_error": float(np.mean(error)),
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
    if output_root.exists():
        raise ValueError(f"refusing to overwrite existing assessment root: {output_root}")

    pre_receipt = preassessment_validator.validate(
        preassessment_root,
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not pre_receipt["valid"]:
        raise ValueError("preassessment failed independent validation")
    review_receipt = _verify_review(
        review_root,
        preassessment_root,
        panel_root,
        qualification_root,
        model_root,
    )
    lock_path = preassessment_root / "prediction-lock.json"
    run_path = preassessment_root / "run-manifest.json"
    lock = _strict_json(lock_path)
    pre_run = _strict_json(run_path)
    if lock.get("prediction_locked_before_assessment") is not True:
        raise ValueError("prediction lock is not sealed")
    if lock.get("assessment_effects_measured") is not False:
        raise ValueError("prediction lock was created after assessment effects")
    if lock.get("panel_manifest_sha256") != pre_run.get("panel_manifest_sha256"):
        raise ValueError("prediction lock and run panel binding mismatch")

    panel_manifest = _strict_json(panel_root / "panel-manifest.json")
    registry_document = _strict_json(panel_root / "concept-registry.json")
    registry = registry_document.get("families")
    if not isinstance(panel_manifest, dict) or not isinstance(registry, list):
        raise ValueError("panel files are invalid")
    by_split = {
        split: sorted(
            [family for family in registry if family.get("split") == split],
            key=lambda family: family["family_id"],
        )
        for split in preassessment.protocol_splits()
    }
    if len(by_split["assessment"]) != 16:
        raise ValueError("assessment census is not 16 families")

    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise ValueError("assessment model layer count mismatch")
    response_ids = preassessment._strict_response_ids(tokenizer)
    token_cache = preassessment._token_cache(registry, tokenizer)
    measured = _measure_assessment_effects(
        model,
        base_layers,
        by_split["assessment"],
        registry,
        token_cache,
        response_ids,
        mx,
    )
    effect_map = {
        family_id: float(effect)
        for family_id, effect in zip(
            [family["family_id"] for family in by_split["assessment"]],
            measured["target_effects"],
        )
    }
    matched_map = {
        family_id: float(effect)
        for family_id, effect in zip(
            [family["family_id"] for family in by_split["assessment"]],
            measured["matched_effects"],
        )
    }
    predictions = lock.get("predictions")
    if not isinstance(predictions, list) or len(predictions) != 16:
        raise ValueError("prediction lock assessment census mismatch")
    ids = [row.get("family_id") for row in predictions if isinstance(row, dict)]
    expected_ids = [family["family_id"] for family in by_split["assessment"]]
    if ids != expected_ids:
        raise ValueError("prediction lock family order mismatch")
    effect_array = np.asarray([effect_map[family_id] for family_id in ids], dtype=np.float64)
    matched_array = np.asarray([matched_map[family_id] for family_id in ids], dtype=np.float64)
    panel_predictions = {
        name: np.asarray(
            [float(row["predictions"][name]) for row in predictions],
            dtype=np.float64,
        )
        for name in preassessment.CONTROL_NAMES
    }
    summary = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": ASSESSMENT_CLAIM_CEILING,
        "classification": ASSESSMENT_CLASSIFICATION,
        "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
        "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
        "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
        "preassessment_run_manifest_sha256": _sha256_file(run_path),
        "preassessment_prediction_lock_sha256": _sha256_file(lock_path),
        "preassessment_validator_receipt_sha256": _sha256_file(preassessment_root / "validator-receipt.json"),
        "independent_review_receipt_sha256": _sha256_file(review_root / "independent-review-receipt.json"),
        "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_root / "validator-receipt.json"),
        "model_manifest_sha256": lock["model_manifest_sha256"],
        "target_layer": protocol.TARGET_LAYER,
        "assessment_family_count": 16,
        "panels": {
            name: _metric(panel_predictions[name], effect_array)
            for name in preassessment.CONTROL_NAMES
        },
        "target_effect": {
            "mean": float(effect_array.mean()),
            "std": float(effect_array.std()),
            "min": float(effect_array.min()),
            "max": float(effect_array.max()),
            "formula": "mean_pair_margin(do(layer_19_final:=paired_opposite_final))-mean_pair_margin(clean)",
        },
        "matched_control": {
            "mean": float(matched_array.mean()),
            "std": float(matched_array.std()),
            "min": float(matched_array.min()),
            "max": float(matched_array.max()),
            "sequence_length_delta_max": measured["matched_sequence_length_delta_max"],
            "used_for_tuning": False,
        },
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
        "assessment_root": str(output_root),
        "panel_root": str(panel_root),
        "preassessment_root": str(preassessment_root),
        "qualification_root": str(qualification_root),
        "review_root": str(review_root),
        "model_root": str(model_root),
        "panel_manifest_sha256": summary["panel_manifest_sha256"],
        "concept_registry_sha256": summary["concept_registry_sha256"],
        "split_manifest_sha256": summary["split_manifest_sha256"],
        "preassessment_run_manifest_sha256": summary["preassessment_run_manifest_sha256"],
        "preassessment_prediction_lock_sha256": summary["preassessment_prediction_lock_sha256"],
        "preassessment_validator_receipt_sha256": summary["preassessment_validator_receipt_sha256"],
        "independent_review_receipt_sha256": summary["independent_review_receipt_sha256"],
        "qualification_result_sha256": summary["qualification_result_sha256"],
        "qualification_validator_receipt_sha256": summary["qualification_validator_receipt_sha256"],
        "model_manifest_sha256": summary["model_manifest_sha256"],
        "assessment_family_count": 16,
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
        "source": {
            "runner_sha256": _sha256_file(Path(__file__).resolve()),
            "preassessment_runner_sha256": _sha256_file(HERE / "run_preassessment_v39.py"),
            "protocol_sha256": _sha256_file(Path(protocol.__file__).resolve()),
            "panel_source_sha256": _sha256_file(HERE / "panel_v39.py"),
        },
        "summary_sha256": _canonical_digest(summary),
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        _write_json(staging / "assessment-summary.json", summary)
        _write_json(staging / "assessment-run-manifest.json", run_manifest)
        if output_root.exists():
            raise ValueError(f"assessment root appeared during execution: {output_root}")
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
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
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
    except (OSError, ValueError, corpus.CorpusError) as exc:
        print(json.dumps({"classification": "AssessmentFailed", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
