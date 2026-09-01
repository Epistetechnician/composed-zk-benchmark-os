#!/usr/bin/env python3
"""Run V41 fit/tune effects and seal estimator-only assessment predictions.

State slice: astral-stage0c-qwen36-directional-block-target-v41.

The runner consumes only independently validated V41 custody roots. It
measures direct intervention and matched-control effects for fit and tune,
selects the preregistered estimators, and locks assessment predictions before
any assessment intervention effect is measured. Raw intermediates never leave
memory.
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

import features_v41 as features
import protocol_v41 as protocol
import validate_panel_v41 as panel_validator
import validate_qualification_v41 as qualification_validator


ESTIMATOR_NAMES = (
    protocol.PRIMARY_CONTROL,
    "clean_activation_only",
    "text_only",
    "shuffled",
    "constant",
)
CLAIM_CEILING = "LocalDevelopmentV41PreassessmentPredictionLocked"


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


def _sha256_file(path: Path) -> str:
    return protocol.sha256_file(path)


def _json_digest(value: Any) -> str:
    return protocol.canonical_digest(value)


def _write_json(path: Path, value: Any) -> None:
    protocol.write_json(path, value)


class LayerProbe:
    def __init__(self, layer: Any, index: int, replacement: np.ndarray | None, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.replacement = replacement
        self.mx = mx
        self.captured = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        if self.index == protocol.TARGET_LAYER:
            self.captured = output
            if self.replacement is not None:
                replacement = self.mx.array(
                    self.replacement.astype(np.float32), dtype=output.dtype
                ).reshape((1, 1, -1))
                output = self.mx.concatenate([output[:, :-1, :], replacement], axis=1)
        return output


def _forward(
    model: Any,
    base_layers: list[Any],
    token_ids: list[int],
    replacement: np.ndarray | None,
    response_ids: dict[str, int],
    mx: Any,
) -> tuple[np.ndarray, np.ndarray]:
    probes = [LayerProbe(layer, index, replacement, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([token_ids]))
        captured = probes[protocol.TARGET_LAYER].captured
        if captured is None:
            raise protocol.ProtocolError("target layer capture was not reached")
        selected = mx.stack(
            [logits[0, -1, response_ids["A"]], logits[0, -1, response_ids["B"]]]
        )
        vector = captured[0, -1, :].astype(mx.float32)
        mx.eval(logits, selected, vector)
        vector_np = np.array(vector, dtype=np.float32, copy=True)
        logits_np = np.array(selected.astype(mx.float32), dtype=np.float64, copy=True)
        if (
            vector_np.shape != (protocol.EXPECTED_HIDDEN_WIDTH,)
            or not np.isfinite(vector_np).all()
            or not np.isfinite(logits_np).all()
        ):
            raise protocol.ProtocolError("non-finite or incorrectly shaped forward result")
        return vector_np, logits_np
    finally:
        model.language_model.model.layers = base_layers


def _margin(logits: np.ndarray, correct_label: str) -> float:
    if correct_label == "A":
        return float(logits[0] - logits[1])
    return float(logits[1] - logits[0])


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> tuple[np.ndarray, float]:
    source_value = source.astype(np.float64)
    receiver_value = receiver.astype(np.float64)
    source_norm = float(np.linalg.norm(source_value))
    receiver_norm = float(np.linalg.norm(receiver_value))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise protocol.ProtocolError("cannot norm-match a zero activation")
    scale = receiver_norm / source_norm
    replacement = source * np.float32(scale)
    replacement_norm = float(np.linalg.norm(replacement.astype(np.float64)))
    relative_error = abs(replacement_norm - receiver_norm) / receiver_norm
    if relative_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
        raise protocol.ProtocolError("matched replacement norm is outside tolerance")
    return replacement, relative_error


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token_text in protocol.RESPONSE_TOKENS.items():
        token_ids = list(tokenizer.encode(token_text))
        if len(token_ids) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
        result[label] = int(token_ids[0])
    return result


def _token_cache(
    registry: list[dict[str, Any]], tokenizer: Any
) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    for family in registry:
        family_id = family["family_id"]
        ordinary = list(tokenizer.encode(family["ordinary_prompt"]))
        counterfactual = list(tokenizer.encode(family["counterfactual_prompt"]))
        if len(ordinary) != protocol.FIXED_TOKEN_LENGTH or len(counterfactual) != protocol.FIXED_TOKEN_LENGTH:
            raise protocol.ProtocolError(f"fixed tokenizer length mismatch: {family_id}")
        cache[family_id] = {
            "ordinary": ordinary,
            "counterfactual": counterfactual,
        }
    return cache


def _capture_clean(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, dict[str, np.ndarray]]:
    clean: dict[str, dict[str, np.ndarray]] = {}
    for family in families:
        family_id = family["family_id"]
        ordinary_vector, ordinary_logits = _forward(
            model, base_layers, cache[family_id]["ordinary"], None, response_ids, mx
        )
        counterfactual_vector, counterfactual_logits = _forward(
            model, base_layers, cache[family_id]["counterfactual"], None, response_ids, mx
        )
        clean[family_id] = {
            "ordinary_vector": ordinary_vector,
            "counterfactual_vector": counterfactual_vector,
            "ordinary_logits": ordinary_logits,
            "counterfactual_logits": counterfactual_logits,
        }
    return clean


def _matched_family(
    family: dict[str, Any],
    same_split: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates = [
        other
        for other in same_split
        if other["family_id"] != family["family_id"]
        and other["gutenberg_id"] != family["gutenberg_id"]
    ]
    if not candidates:
        raise protocol.ProtocolError(f"no cross-document donor: {family['family_id']}")
    return min(
        candidates,
        key=lambda other: (
            abs(int(other["source_word_count"]) - int(family["source_word_count"])),
            protocol.canonical_digest(
                [protocol.PROTOCOL_ID, "donor", family["family_id"], other["family_id"]]
            ),
        ),
    )


def _measure_effects(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    split_families: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    if not families or families[0]["split"] == "assessment":
        raise protocol.ProtocolError("assessment effects are forbidden before review")
    clean = _capture_clean(model, base_layers, families, cache, response_ids, mx)
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
        ordinary_clean_margin = _margin(current["ordinary_logits"], "A")
        counterfactual_clean_margin = _margin(current["counterfactual_logits"], "B")
        _, ordinary_pair_logits = _forward(
            model, base_layers, cache[family_id]["ordinary"], counterfactual, response_ids, mx
        )
        _, counterfactual_pair_logits = _forward(
            model, base_layers, cache[family_id]["counterfactual"], ordinary, response_ids, mx
        )
        target_effects.append(
            0.5
            * (
                _margin(ordinary_pair_logits, "A")
                - ordinary_clean_margin
                + _margin(counterfactual_pair_logits, "B")
                - counterfactual_clean_margin
            )
        )
        ordinary_donor = _matched_family(family, split_families)
        counterfactual_donor = _matched_family(family, split_families)
        if ordinary_donor["gutenberg_id"] == family["gutenberg_id"] or counterfactual_donor["gutenberg_id"] == family["gutenberg_id"]:
            donor_violations += 1
        ordinary_replacement, ordinary_error = _norm_match(
            clean[ordinary_donor["family_id"]]["ordinary_vector"], ordinary
        )
        counterfactual_replacement, counterfactual_error = _norm_match(
            clean[counterfactual_donor["family_id"]]["counterfactual_vector"], counterfactual
        )
        norm_errors.extend([ordinary_error, counterfactual_error])
        _, ordinary_match_logits = _forward(
            model,
            base_layers,
            cache[family_id]["ordinary"],
            ordinary_replacement,
            response_ids,
            mx,
        )
        _, counterfactual_match_logits = _forward(
            model,
            base_layers,
            cache[family_id]["counterfactual"],
            counterfactual_replacement,
            response_ids,
            mx,
        )
        matched_effects.append(
            0.5
            * (
                _margin(ordinary_match_logits, "A")
                - ordinary_clean_margin
                + _margin(counterfactual_match_logits, "B")
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


def _measure_features(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    clean = _capture_clean(model, base_layers, families, cache, response_ids, mx)
    pair_values: list[np.ndarray] = []
    clean_values: list[np.ndarray] = []
    text_values: list[np.ndarray] = []
    for family in families:
        family_id = family["family_id"]
        ordinary = clean[family_id]["ordinary_vector"]
        counterfactual = clean[family_id]["counterfactual_vector"]
        pair_values.append(features.pair_features(ordinary, counterfactual))
        clean_values.append(features.clean_activation_features(ordinary, counterfactual))
        text_values.append(
            features.text_features(family["ordinary_prompt"], family["counterfactual_prompt"])
        )
    return {
        "family_ids": [family["family_id"] for family in families],
        "pair_features": np.asarray(pair_values, dtype=np.float64),
        "clean_features": np.asarray(clean_values, dtype=np.float64),
        "text_features": np.asarray(text_values, dtype=np.float64),
    }


def _row_permutation(family_ids: list[str], split: str, panel_digest: str) -> np.ndarray:
    keyed = [
        (
            protocol.canonical_digest([protocol.PROTOCOL_ID, "shuffle", split, panel_digest, family_id]),
            index,
        )
        for index, family_id in enumerate(family_ids)
    ]
    return np.asarray([index for _, index in sorted(keyed)], dtype=np.int64)


def _fit_ridge(features_value: np.ndarray, targets: np.ndarray, alpha: float) -> dict[str, Any]:
    if features_value.shape != (len(targets), protocol.FEATURE_WIDTH):
        raise protocol.ProtocolError("feature panel shape mismatch")
    if not np.isfinite(features_value).all() or not np.isfinite(targets).all():
        raise protocol.ProtocolError("non-finite fit values")
    mean = features_value.mean(axis=0)
    scale = np.where(features_value.std(axis=0) < 1e-12, 1.0, features_value.std(axis=0))
    centered = (features_value - mean) / scale
    target_mean = float(targets.mean())
    coefficients = np.linalg.solve(
        centered.T @ centered + alpha * np.eye(protocol.FEATURE_WIDTH),
        centered.T @ (targets - target_mean),
    )
    return {
        "feature_mean": mean,
        "feature_scale": scale,
        "target_mean": target_mean,
        "coefficients": coefficients,
        "alpha": float(alpha),
    }


def _predict(state: dict[str, Any], feature_values: np.ndarray) -> np.ndarray:
    if "coefficients" not in state:
        return np.full(len(feature_values), float(state["target_mean"]), dtype=np.float64)
    return state["target_mean"] + (
        (feature_values - state["feature_mean"]) / state["feature_scale"]
    ) @ state["coefficients"]


def _select(
    name: str,
    fit_features: np.ndarray,
    fit_targets: np.ndarray,
    tune_features: np.ndarray,
    tune_targets: np.ndarray,
) -> tuple[dict[str, Any], dict[str, Any]]:
    choices: list[tuple[float, float, dict[str, Any], float]] = []
    for alpha in protocol.RIDGE_ALPHAS:
        state = _fit_ridge(fit_features, fit_targets, alpha)
        fit_mse = float(np.mean((_predict(state, fit_features) - fit_targets) ** 2))
        tune_mse = float(np.mean((_predict(state, tune_features) - tune_targets) ** 2))
        choices.append((tune_mse, alpha, state, fit_mse))
    tune_mse, alpha, selected, fit_mse = min(choices, key=lambda item: (item[0], item[1]))
    return selected, {
        "name": name,
        "kind": "fit_only_ridge",
        "candidate_alphas": list(protocol.RIDGE_ALPHAS),
        "selected_alpha": alpha,
        "fit_count": len(fit_targets),
        "tune_count": len(tune_targets),
        "fit_rmse": math.sqrt(fit_mse),
        "tune_rmse": math.sqrt(tune_mse),
        "fit_target_mean": float(fit_targets.mean()),
        "fit_target_std": float(fit_targets.std()),
        "tune_target_mean": float(tune_targets.mean()),
        "tune_target_std": float(tune_targets.std()),
    }


def _state_json(state: dict[str, Any]) -> dict[str, Any]:
    if "coefficients" not in state:
        return {"target_mean": float(state["target_mean"])}
    return {
        "alpha": float(state["alpha"]),
        "feature_mean": state["feature_mean"].tolist(),
        "feature_scale": state["feature_scale"].tolist(),
        "target_mean": float(state["target_mean"]),
        "coefficients": state["coefficients"].tolist(),
    }


def _load_inputs(
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    panel_receipt_path = panel_root / "validator-receipt.json"
    qualification_receipt_path = qualification_root / "validator-receipt.json"
    if not panel_receipt_path.is_file() or not qualification_receipt_path.is_file():
        raise protocol.ProtocolError("independent panel and qualification receipts are required")
    panel_receipt = panel_validator.validate(panel_root, corpus_root, model_root, repository_root)
    qualification_receipt = qualification_validator.validate(
        qualification_root, model_root, repository_root
    )
    if not panel_receipt["valid"] or not qualification_receipt["valid"]:
        raise protocol.ProtocolError("panel or qualification validation failed")
    if _strict_json(panel_receipt_path) != panel_receipt or _strict_json(qualification_receipt_path) != qualification_receipt:
        raise protocol.ProtocolError("recorded independent receipt does not match recomputation")
    registry_document = _strict_json(panel_root / "concept-registry.json")
    registry = registry_document.get("families")
    if not isinstance(registry, list) or len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("concept registry is invalid")
    digests = {
        "protocol_source_sha256": _sha256_file(Path(protocol.__file__).resolve()),
        "feature_map_sha256": protocol.feature_map_digest(),
        "corpus_manifest_sha256": _sha256_file(corpus_root / "corpus-manifest.json"),
        "corpus_validator_receipt_sha256": _sha256_file(corpus_root / "validator-receipt.json"),
        "panel_manifest_sha256": _sha256_file(panel_root / "panel-manifest.json"),
        "concept_registry_sha256": _sha256_file(panel_root / "concept-registry.json"),
        "split_manifest_sha256": _sha256_file(panel_root / "split-manifest.json"),
        "panel_validator_receipt_sha256": _sha256_file(panel_receipt_path),
        "qualification_result_sha256": _sha256_file(qualification_root / "qualification-result.json"),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_receipt_path),
        "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
    }
    return registry, digests


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


def run_preassessment(
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    output_root: Path,
    repository_root: Path,
) -> Path:
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite preassessment root: {output_root}")
    registry, digests = _load_inputs(
        panel_root, corpus_root, qualification_root, model_root, repository_root
    )
    by_split = {
        split: sorted(
            [family for family in registry if family["split"] == split],
            key=lambda family: family["family_id"],
        )
        for split in protocol.SPLITS
    }
    if any(len(by_split[split]) != protocol.FAMILIES_PER_SPLIT for split in protocol.SPLITS):
        raise protocol.ProtocolError("split family census mismatch")

    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root.resolve()), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("model layer count mismatch")
    response_ids = _strict_response_ids(tokenizer)
    cache = _token_cache(registry, tokenizer)
    fit_effects = _measure_effects(
        model, base_layers, by_split["fit"], by_split["fit"], cache, response_ids, mx
    )
    tune_effects = _measure_effects(
        model, base_layers, by_split["tune"], by_split["tune"], cache, response_ids, mx
    )
    feature_panels = {
        protocol.PRIMARY_CONTROL: ("pair_features", "pair_features"),
        "clean_activation_only": ("clean_features", "clean_features"),
        "text_only": ("text_features", "text_features"),
    }
    fit_features = _measure_features(
        model, base_layers, by_split["fit"], cache, response_ids, mx
    )
    tune_features = _measure_features(
        model, base_layers, by_split["tune"], cache, response_ids, mx
    )
    panel_digest = digests["panel_manifest_sha256"]
    states: dict[str, dict[str, Any]] = {}
    summaries: dict[str, dict[str, Any]] = {}
    for name, (fit_key, tune_key) in feature_panels.items():
        state, summary = _select(
            name,
            fit_features[fit_key],
            fit_effects["target_effects"],
            tune_features[tune_key],
            tune_effects["target_effects"],
        )
        states[name] = state
        summaries[name] = summary
    fit_order = _row_permutation(fit_features["family_ids"], "fit", panel_digest)
    tune_order = _row_permutation(tune_features["family_ids"], "tune", panel_digest)
    states["shuffled"], summaries["shuffled"] = _select(
        "shuffled",
        fit_features["pair_features"][fit_order],
        fit_effects["target_effects"],
        tune_features["pair_features"][tune_order],
        tune_effects["target_effects"],
    )
    fit_mean = float(fit_effects["target_effects"].mean())
    fit_constant = np.full(len(fit_effects["target_effects"]), fit_mean)
    tune_constant = np.full(len(tune_effects["target_effects"]), fit_mean)
    states["constant"] = {"target_mean": fit_mean}
    summaries["constant"] = {
        "name": "constant",
        "kind": "fit_target_mean",
        "candidate_alphas": [],
        "selected_alpha": None,
        "fit_count": len(fit_constant),
        "tune_count": len(tune_constant),
        "fit_rmse": math.sqrt(float(np.mean((fit_constant - fit_effects["target_effects"]) ** 2))),
        "tune_rmse": math.sqrt(float(np.mean((tune_constant - tune_effects["target_effects"]) ** 2))),
        "fit_target_mean": fit_mean,
        "fit_target_std": float(fit_effects["target_effects"].std()),
        "tune_target_mean": float(tune_effects["target_effects"].mean()),
        "tune_target_std": float(tune_effects["target_effects"].std()),
    }
    summaries["matched"] = {
        "name": "matched",
        "kind": "unrelated_donor_effect_distribution",
        "fit": _aggregate(fit_effects["matched_effects"]),
        "tune": _aggregate(tune_effects["matched_effects"]),
        "used_for_tuning": False,
        "norm_relative_error_max": max(
            fit_effects["matched_norm_relative_error_max"],
            tune_effects["matched_norm_relative_error_max"],
        ),
        "donor_violations": fit_effects["matched_donor_violations"]
        + tune_effects["matched_donor_violations"],
    }
    tune_delta = summaries[protocol.PRIMARY_CONTROL]["tune_rmse"] - summaries["constant"]["tune_rmse"]
    assessment_features = _measure_features(
        model, base_layers, by_split["assessment"], cache, response_ids, mx
    )

    assessment_order = _row_permutation(
        assessment_features["family_ids"], "assessment", panel_digest
    )
    # Assessment features and locked predictions are transient. Only estimator
    # states and canonical family order are published.
    assessment_prediction_features = {
        protocol.PRIMARY_CONTROL: assessment_features["pair_features"],
        "clean_activation_only": assessment_features["clean_features"],
        "text_only": assessment_features["text_features"],
        "shuffled": assessment_features["pair_features"][assessment_order],
        "constant": np.empty((len(assessment_features["family_ids"]), 0)),
    }
    _ = {
        name: _predict(states[name], values)
        for name, values in assessment_prediction_features.items()
    }
    prediction_lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "lock_id": f"{protocol.PROTOCOL_ID}-prediction-lock-v1",
        **digests,
        "panel_id": protocol.PANEL_ID,
        "target_layer": protocol.TARGET_LAYER,
        "feature_width": protocol.FEATURE_WIDTH,
        "feature_map_sha256": protocol.feature_map_digest(),
        "ridge_candidate_alphas": list(protocol.RIDGE_ALPHAS),
        "controls": list(protocol.CONTROL_NAMES),
        "estimator_controls": list(ESTIMATOR_NAMES),
        "assessment_family_ids": assessment_features["family_ids"],
        "estimator_states": {name: _state_json(states[name]) for name in ESTIMATOR_NAMES},
        "assessment_effects_absent": True,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "per_family_predictions_retained": False,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
    }
    fit_tune_summary = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": "PreassessmentPredictionLocked",
        "claim_ceiling": CLAIM_CEILING,
        **digests,
        "target_layer": protocol.TARGET_LAYER,
        "feature_width": protocol.FEATURE_WIDTH,
        "controls": list(protocol.CONTROL_NAMES),
        "fit_family_count": len(fit_effects["target_effects"]),
        "tune_family_count": len(tune_effects["target_effects"]),
        "assessment_family_count": len(assessment_features["family_ids"]),
        "tune_delta_rmse": tune_delta,
        "tune_utility_gate_passed": tune_delta <= -protocol.UTILITY_RMSE_MARGIN,
        "panels": summaries,
        "target_effects": {
            "fit": _aggregate(fit_effects["target_effects"]),
            "tune": _aggregate(tune_effects["target_effects"]),
        },
        "assessment_effects_absent": True,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "per_family_effects_retained": False,
        "per_family_predictions_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
    }
    run_manifest = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "runner_source_sha256": _sha256_file(Path(__file__).resolve()),
        "features_source_sha256": _sha256_file(Path(features.__file__).resolve()),
        **digests,
        "assessment_features_materialized_in_memory": True,
        "assessment_predictions_materialized_in_memory": True,
        "assessment_effects_present": False,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "per_family_effects_retained": False,
        "per_family_predictions_retained": False,
        "aggregate_only": True,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "prediction_lock_sha256": _json_digest(prediction_lock),
        "fit_tune_summary_sha256": _json_digest(fit_tune_summary),
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent))
    )
    try:
        _write_json(staging / "fit-tune-summary.json", fit_tune_summary)
        _write_json(staging / "prediction-lock.json", prediction_lock)
        _write_json(staging / "run-manifest.json", run_manifest)
        if output_root.exists():
            raise protocol.ProtocolError(f"preassessment root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = run_preassessment(
            args.panel_root,
            args.corpus_root,
            args.qualification_root,
            args.model,
            args.output_root,
            args.repository_root,
        )
    except (OSError, ImportError, KeyError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(
        json.dumps(
            {
                "preassessment_root": str(root),
                "classification": "PreassessmentPredictionLocked",
                "valid": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
