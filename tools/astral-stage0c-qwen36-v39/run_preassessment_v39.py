#!/usr/bin/env python3
"""Run V39 fit/tune measurements and lock assessment predictions.

State slice: astral-stage0c-qwen36-layer-effect-v39.

This runner consumes a validated external V39 panel and passed qualification
bundle. It measures direct layer-19 replacement effects only on fit and tune,
selects the preregistered estimators, materializes aggregate-only assessment
predictions, and stops before assessment intervention effects. Raw prompts,
tokens, activations, logits, traces, and per-family effects never leave the
process.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import platform
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
import validate_gutenberg_panel_v39 as panel_validator
import validator_v39 as qualification_validator


PREASSESSMENT_CLAIM_CEILING = "LocalDevelopmentV39PreassessmentPredictionLocked"
CONTROL_NAMES = ("activation_only", "text_only", "shuffled", "constant")
RIDGE_ALPHAS = (1e-4, 1e-3, 1e-2, 1e-1)
FEATURE_WIDTH = 64
TARGET_LAYER = protocol.TARGET_LAYER


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_digest(value: Any) -> str:
    return _sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _hash_int(*parts: object) -> int:
    payload = ":".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _hash_sign(*parts: object) -> float:
    return 1.0 if _hash_int(*parts) & 1 else -1.0


def _hash_bucket(*parts: object) -> int:
    return _hash_int(*parts) % FEATURE_WIDTH


def _hash_bow(text: str) -> np.ndarray:
    features = np.zeros(FEATURE_WIDTH, dtype=np.float64)
    for word in panel.WORD_RE.findall(text.lower()):
        bucket = _hash_bucket(protocol.PROTOCOL_ID, "text-feature", word)
        features[bucket] += _hash_sign(protocol.PROTOCOL_ID, "text-sign", word)
    norm = float(np.linalg.norm(features))
    return features / norm if norm > 0.0 else features


def _text_pair_features(ordinary_prompt: str, counterfactual_prompt: str) -> np.ndarray:
    return _hash_bow(ordinary_prompt) - _hash_bow(counterfactual_prompt)


def _activation_features(ordinary_vector: np.ndarray, counterfactual_vector: np.ndarray) -> np.ndarray:
    """Project the paired final activations with a fixed count-sketch map."""

    difference = ordinary_vector.astype(np.float64) - counterfactual_vector.astype(np.float64)
    features = np.zeros(FEATURE_WIDTH, dtype=np.float64)
    counts = np.zeros(FEATURE_WIDTH, dtype=np.float64)
    for dimension, value in enumerate(difference):
        bucket = _hash_bucket(protocol.PROTOCOL_ID, "activation-bucket", TARGET_LAYER, dimension)
        sign = _hash_sign(protocol.PROTOCOL_ID, "activation-sign", TARGET_LAYER, dimension)
        features[bucket] += sign * value
        counts[bucket] += 1.0
    features /= np.sqrt(np.maximum(counts, 1.0))
    norm = float(np.linalg.norm(features))
    return features / norm if norm > 0.0 else features


def _row_permutation(family_ids: list[str], split: str, panel_digest: str) -> list[int]:
    return sorted(
        range(len(family_ids)),
        key=lambda index: _hash_int(protocol.PROTOCOL_ID, "shuffle", split, panel_digest, family_ids[index]),
    )


def _shuffled_features(features: np.ndarray, family_ids: list[str], split: str, panel_digest: str) -> np.ndarray:
    permutation = _row_permutation(family_ids, split, panel_digest)
    return features[np.asarray(permutation, dtype=np.int64)]


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token_text in panel.RESPONSE_TOKENS.items():
        token_ids = list(tokenizer.encode(token_text))
        if len(token_ids) != 1:
            raise ValueError(f"response token is not exactly one tokenizer token: {label}")
        result[label] = int(token_ids[0])
    return result


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
        if self.index == TARGET_LAYER:
            self.captured = output
            if self.replacement is not None:
                replacement = self.mx.array(
                    self.replacement.astype(np.float32),
                    dtype=output.dtype,
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
        target_probe = probes[TARGET_LAYER]
        if target_probe.captured is None:
            raise RuntimeError("target layer capture was not reached")
        response_logits = mx.stack(
            [
                logits[0, -1, response_ids["A"]],
                logits[0, -1, response_ids["B"]],
            ]
        )
        captured_vector = target_probe.captured[0, -1, :].astype(mx.float32)
        response_logits_float = response_logits.astype(mx.float32)
        mx.eval(logits, target_probe.captured, captured_vector, response_logits_float)
        vector = np.array(captured_vector, dtype=np.float32, copy=True)
        selected_logits = np.array(response_logits_float, dtype=np.float64, copy=True)
        if vector.shape != (protocol.EXPECTED_HIDDEN_WIDTH,):
            raise ValueError(f"target layer vector shape mismatch: {vector.shape}")
        if not np.isfinite(vector).all() or not np.isfinite(selected_logits).all():
            raise ValueError("non-finite model output")
        return vector, selected_logits
    finally:
        model.language_model.model.layers = base_layers


def _margin(logits: np.ndarray, correct_label: str) -> float:
    if correct_label == "A":
        return float(logits[0] - logits[1])
    if correct_label == "B":
        return float(logits[1] - logits[0])
    raise ValueError(f"unsupported response label: {correct_label}")


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> np.ndarray:
    source_norm = float(np.linalg.norm(source.astype(np.float64)))
    receiver_norm = float(np.linalg.norm(receiver.astype(np.float64)))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise ValueError("cannot norm-match a zero layer vector")
    return source * np.float32(receiver_norm / source_norm)


def _token_cache(registry: list[dict[str, Any]], tokenizer: Any) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    for family in registry:
        family_id = family["family_id"]
        ordinary = list(tokenizer.encode(family["ordinary_prompt"]))
        counterfactual = list(tokenizer.encode(family["counterfactual_prompt"]))
        if len(ordinary) < 2 or len(counterfactual) < 2:
            raise ValueError(f"family tokenization is too short: {family_id}")
        cache[family_id] = {
            "ordinary": ordinary,
            "counterfactual": counterfactual,
            "ordinary_length": len(ordinary),
            "counterfactual_length": len(counterfactual),
        }
    return cache


def _matched_family(
    family: dict[str, Any],
    kind: str,
    all_families: list[dict[str, Any]],
    token_cache: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    candidates = [
        other
        for other in all_families
        if other["gutenberg_id"] == family["gutenberg_id"]
        and other["family_id"] != family["family_id"]
    ]
    if not candidates:
        raise ValueError(f"no same-document matched control for {family['family_id']}")
    length_key = f"{kind}_length"
    receiver_length = token_cache[family["family_id"]][length_key]
    return min(
        candidates,
        key=lambda other: (
            abs(token_cache[other["family_id"]][length_key] - receiver_length),
            abs(other["source_word_count"] - family["source_word_count"]),
            _hash_int(protocol.PROTOCOL_ID, "matched", family["family_id"], kind, other["family_id"]),
        ),
    )


def _capture_clean_split(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    token_cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, dict[str, Any]]:
    clean: dict[str, dict[str, Any]] = {}
    for family in families:
        family_id = family["family_id"]
        ordinary_vector, ordinary_logits = _forward(
            model,
            base_layers,
            token_cache[family_id]["ordinary"],
            None,
            response_ids,
            mx,
        )
        counterfactual_vector, counterfactual_logits = _forward(
            model,
            base_layers,
            token_cache[family_id]["counterfactual"],
            None,
            response_ids,
            mx,
        )
        clean[family_id] = {
            "ordinary_vector": ordinary_vector,
            "counterfactual_vector": counterfactual_vector,
            "ordinary_logits": ordinary_logits,
            "counterfactual_logits": counterfactual_logits,
        }
    return clean


def _measure_split(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    all_families: list[dict[str, Any]],
    token_cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    split = families[0]["split"] if families else ""
    if split == "assessment":
        raise ValueError("assessment effect measurement is forbidden before independent review")
    clean = _capture_clean_split(model, base_layers, families, token_cache, response_ids, mx)
    activation_rows: list[np.ndarray] = []
    text_rows: list[np.ndarray] = []
    target_effects: list[float] = []
    matched_effects: list[float] = []
    match_length_deltas: list[int] = []

    for family in families:
        family_id = family["family_id"]
        current = clean[family_id]
        ordinary_vector = current["ordinary_vector"]
        counterfactual_vector = current["counterfactual_vector"]
        ordinary_clean_margin = _margin(current["ordinary_logits"], "A")
        counterfactual_clean_margin = _margin(current["counterfactual_logits"], "B")

        ordinary_pair_vector = _norm_match(counterfactual_vector, ordinary_vector)
        counterfactual_pair_vector = _norm_match(ordinary_vector, counterfactual_vector)
        _, ordinary_pair_logits = _forward(
            model,
            base_layers,
            token_cache[family_id]["ordinary"],
            ordinary_pair_vector,
            response_ids,
            mx,
        )
        _, counterfactual_pair_logits = _forward(
            model,
            base_layers,
            token_cache[family_id]["counterfactual"],
            counterfactual_pair_vector,
            response_ids,
            mx,
        )
        pair_effect = 0.5 * (
            _margin(ordinary_pair_logits, "A") - ordinary_clean_margin
            + _margin(counterfactual_pair_logits, "B") - counterfactual_clean_margin
        )

        ordinary_match = _matched_family(family, "ordinary", all_families, token_cache)
        counterfactual_match = _matched_family(family, "counterfactual", all_families, token_cache)
        ordinary_match_source = clean[ordinary_match["family_id"]]["ordinary_vector"]
        counterfactual_match_source = clean[counterfactual_match["family_id"]]["counterfactual_vector"]
        _, ordinary_match_logits = _forward(
            model,
            base_layers,
            token_cache[family_id]["ordinary"],
            _norm_match(ordinary_match_source, ordinary_vector),
            response_ids,
            mx,
        )
        _, counterfactual_match_logits = _forward(
            model,
            base_layers,
            token_cache[family_id]["counterfactual"],
            _norm_match(counterfactual_match_source, counterfactual_vector),
            response_ids,
            mx,
        )
        matched_effect = 0.5 * (
            _margin(ordinary_match_logits, "A") - ordinary_clean_margin
            + _margin(counterfactual_match_logits, "B") - counterfactual_clean_margin
        )

        activation_rows.append(_activation_features(ordinary_vector, counterfactual_vector))
        text_rows.append(_text_pair_features(family["ordinary_prompt"], family["counterfactual_prompt"]))
        target_effects.append(pair_effect)
        matched_effects.append(matched_effect)
        match_length_deltas.extend(
            [
                abs(token_cache[ordinary_match["family_id"]]["ordinary_length"] - token_cache[family_id]["ordinary_length"]),
                abs(token_cache[counterfactual_match["family_id"]]["counterfactual_length"] - token_cache[family_id]["counterfactual_length"]),
            ]
        )

    return {
        "family_ids": [family["family_id"] for family in families],
        "activation_features": np.asarray(activation_rows, dtype=np.float64),
        "text_features": np.asarray(text_rows, dtype=np.float64),
        "target_effects": np.asarray(target_effects, dtype=np.float64),
        "matched_effects": np.asarray(matched_effects, dtype=np.float64),
        "matched_sequence_length_delta_max": max(match_length_deltas, default=0),
    }


def _measure_assessment_features(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    token_cache: dict[str, dict[str, Any]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    activation_rows: list[np.ndarray] = []
    text_rows: list[np.ndarray] = []
    family_ids: list[str] = []
    for family in families:
        family_id = family["family_id"]
        ordinary_vector, _ = _forward(
            model,
            base_layers,
            token_cache[family_id]["ordinary"],
            None,
            response_ids,
            mx,
        )
        counterfactual_vector, _ = _forward(
            model,
            base_layers,
            token_cache[family_id]["counterfactual"],
            None,
            response_ids,
            mx,
        )
        activation_rows.append(_activation_features(ordinary_vector, counterfactual_vector))
        text_rows.append(_text_pair_features(family["ordinary_prompt"], family["counterfactual_prompt"]))
        family_ids.append(family_id)
    return {
        "family_ids": family_ids,
        "activation_features": np.asarray(activation_rows, dtype=np.float64),
        "text_features": np.asarray(text_rows, dtype=np.float64),
    }


def _fit_ridge(features: np.ndarray, targets: np.ndarray, alpha: float) -> dict[str, Any]:
    if features.ndim != 2 or features.shape[1] != FEATURE_WIDTH:
        raise ValueError("feature panel shape is invalid")
    if len(features) != len(targets) or len(targets) == 0:
        raise ValueError("feature and target counts are invalid")
    feature_mean = features.mean(axis=0)
    feature_scale = features.std(axis=0)
    feature_scale = np.where(feature_scale < 1e-12, 1.0, feature_scale)
    centered = (features - feature_mean) / feature_scale
    target_mean = float(targets.mean())
    response = targets - target_mean
    gram = centered.T @ centered + float(alpha) * np.eye(FEATURE_WIDTH, dtype=np.float64)
    coefficients = np.linalg.solve(gram, centered.T @ response)
    return {
        "feature_mean": feature_mean,
        "feature_scale": feature_scale,
        "target_mean": target_mean,
        "coefficients": coefficients,
        "alpha": float(alpha),
    }


def _predict(state: dict[str, Any], features: np.ndarray) -> np.ndarray:
    centered = (features - state["feature_mean"]) / state["feature_scale"]
    return state["target_mean"] + centered @ state["coefficients"]


def _mse(predictions: np.ndarray, targets: np.ndarray) -> float:
    return float(np.mean((predictions - targets) ** 2))


def _select_model(
    name: str,
    fit_features: np.ndarray,
    fit_targets: np.ndarray,
    tune_features: np.ndarray,
    tune_targets: np.ndarray,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates: list[tuple[float, float, dict[str, Any], float]] = []
    for alpha in RIDGE_ALPHAS:
        state = _fit_ridge(fit_features, fit_targets, alpha)
        tune_mse = _mse(_predict(state, tune_features), tune_targets)
        candidates.append((tune_mse, alpha, state, _mse(_predict(state, fit_features), fit_targets)))
    tune_mse, alpha, selected, fit_mse = min(candidates, key=lambda item: (item[0], item[1]))
    summary = {
        "name": name,
        "candidate_alphas": list(RIDGE_ALPHAS),
        "selected_alpha": alpha,
        "fit_count": int(len(fit_targets)),
        "tune_count": int(len(tune_targets)),
        "fit_mse": fit_mse,
        "fit_rmse": math.sqrt(fit_mse),
        "tune_mse": tune_mse,
        "tune_rmse": math.sqrt(tune_mse),
        "fit_target_mean": float(fit_targets.mean()),
        "fit_target_std": float(fit_targets.std()),
        "tune_target_mean": float(tune_targets.mean()),
        "tune_target_std": float(tune_targets.std()),
    }
    return selected, summary


def _constant_state(targets: np.ndarray) -> dict[str, Any]:
    return {"target_mean": float(targets.mean())}


def _constant_predict(state: dict[str, Any], count: int) -> np.ndarray:
    return np.full(count, state["target_mean"], dtype=np.float64)


def _load_panel(
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    repository_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    receipt = panel_validator.validate(
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if not receipt["valid"]:
        raise ValueError("panel failed independent validation: " + "; ".join(receipt["errors"]))
    panel_manifest_path = panel_root / "panel-manifest.json"
    registry_path = panel_root / "concept-registry.json"
    split_path = panel_root / "split-manifest.json"
    manifest = corpus.read_strict_json(panel_manifest_path)
    registry_document = corpus.read_strict_json(registry_path)
    split_manifest = corpus.read_strict_json(split_path)
    registry = registry_document.get("families") if isinstance(registry_document, dict) else None
    if not isinstance(manifest, dict) or not isinstance(registry, list) or not isinstance(split_manifest, dict):
        raise ValueError("panel files have invalid structure")
    if manifest.get("assessment_effects_present") is not False or manifest.get("assessment_ready") is not False:
        raise ValueError("panel is not assessment-closed")
    return manifest, registry, {
        "panel_manifest_sha256": _sha256_file(panel_manifest_path),
        "concept_registry_sha256": _sha256_file(registry_path),
        "split_manifest_sha256": _sha256_file(split_path),
        "panel_validator_receipt_sha256": _sha256_file(panel_root / "validator-receipt.json")
        if (panel_root / "validator-receipt.json").is_file()
        else None,
        "split_manifest": split_manifest,
        "panel_receipt": receipt,
    }


def run_preassessment(
    panel_root: Path,
    corpus_root: Path,
    qualification_root: Path,
    model_root: Path,
    output_root: Path,
    repository_root: Path,
) -> Path:
    panel_root = panel_root.resolve()
    corpus_root = corpus_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise ValueError(f"refusing to overwrite existing preassessment root: {output_root}")

    panel_manifest, registry, panel_digests = _load_panel(
        panel_root,
        corpus_root,
        qualification_root,
        model_root,
        repository_root,
    )
    if panel_manifest.get("model_root") != str(model_root):
        raise ValueError("panel model root does not match requested model")
    qualification_result_path = qualification_root / "qualification-result.json"
    qualification_receipt_path = qualification_root / "validator-receipt.json"
    qualification_result = qualification_validator._strict_json(qualification_result_path)
    recomputed_qualification_receipt = qualification_validator.validate(
        qualification_result,
        qualification_result_path,
        model_root,
        repository_root,
    )
    stored_qualification_receipt = qualification_validator._strict_json(qualification_receipt_path)
    if not recomputed_qualification_receipt["valid"] or stored_qualification_receipt != recomputed_qualification_receipt:
        raise ValueError("qualification receipt is missing, stale, or invalid")

    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise ValueError(f"unexpected layer count: {len(base_layers)}")
    response_ids = _strict_response_ids(tokenizer)
    token_cache = _token_cache(registry, tokenizer)
    by_split = {
        split: sorted(
            [family for family in registry if family.get("split") == split],
            key=lambda family: family["family_id"],
        )
        for split in protocol_splits()
    }
    if any(len(families) != panel.EXPECTED_FAMILIES_PER_SPLIT for families in by_split.values()):
        raise ValueError("panel split census changed")

    fit = _measure_split(model, base_layers, by_split["fit"], registry, token_cache, response_ids, mx)
    tune = _measure_split(model, base_layers, by_split["tune"], registry, token_cache, response_ids, mx)

    panel_digest = panel_digests["panel_manifest_sha256"]
    fit_ids = fit["family_ids"]
    tune_ids = tune["family_ids"]
    fit_activation = fit["activation_features"]
    tune_activation = tune["activation_features"]
    fit_text = fit["text_features"]
    tune_text = tune["text_features"]
    fit_shuffled = _shuffled_features(fit_activation, fit_ids, "fit", panel_digest)
    tune_shuffled = _shuffled_features(tune_activation, tune_ids, "tune", panel_digest)
    fit_targets = fit["target_effects"]
    tune_targets = tune["target_effects"]

    model_states: dict[str, dict[str, Any]] = {}
    panel_summaries: dict[str, dict[str, Any]] = {}
    for name, fit_features, tune_features in (
        ("activation_only", fit_activation, tune_activation),
        ("text_only", fit_text, tune_text),
        ("shuffled", fit_shuffled, tune_shuffled),
    ):
        state, summary = _select_model(name, fit_features, fit_targets, tune_features, tune_targets)
        model_states[name] = state
        panel_summaries[name] = summary
    constant = _constant_state(fit_targets)
    constant_fit_mse = _mse(_constant_predict(constant, len(fit_targets)), fit_targets)
    constant_tune_mse = _mse(_constant_predict(constant, len(tune_targets)), tune_targets)
    panel_summaries["constant"] = {
        "name": "constant",
        "candidate_alphas": [],
        "selected_alpha": None,
        "fit_count": int(len(fit_targets)),
        "tune_count": int(len(tune_targets)),
        "fit_mse": constant_fit_mse,
        "fit_rmse": math.sqrt(constant_fit_mse),
        "tune_mse": constant_tune_mse,
        "tune_rmse": math.sqrt(constant_tune_mse),
        "fit_target_mean": float(fit_targets.mean()),
        "fit_target_std": float(fit_targets.std()),
        "tune_target_mean": float(tune_targets.mean()),
        "tune_target_std": float(tune_targets.std()),
    }
    model_states["constant"] = constant

    assessment = _measure_assessment_features(
        model,
        base_layers,
        by_split["assessment"],
        token_cache,
        response_ids,
        mx,
    )
    assessment_ids = assessment["family_ids"]
    assessment_activation = assessment["activation_features"]
    assessment_text = assessment["text_features"]
    assessment_shuffled = _shuffled_features(assessment_activation, assessment_ids, "assessment", panel_digest)
    assessment_predictions = {
        "activation_only": _predict(model_states["activation_only"], assessment_activation),
        "text_only": _predict(model_states["text_only"], assessment_text),
        "shuffled": _predict(model_states["shuffled"], assessment_shuffled),
        "constant": _constant_predict(model_states["constant"], len(assessment_ids)),
    }
    prediction_rows = []
    for index, family_id in enumerate(assessment_ids):
        prediction_rows.append(
            {
                "family_id": family_id,
                "predictions": {
                    name: float(assessment_predictions[name][index])
                    for name in CONTROL_NAMES
                },
            }
        )

    prediction_lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": PREASSESSMENT_CLAIM_CEILING,
        "classification": "PreassessmentPredictionLocked",
        "panel_id": panel_manifest["panel_id"],
        "panel_manifest_sha256": panel_digests["panel_manifest_sha256"],
        "concept_registry_sha256": panel_digests["concept_registry_sha256"],
        "split_manifest_sha256": panel_digests["split_manifest_sha256"],
        "qualification_result_sha256": _sha256_file(qualification_result_path),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_receipt_path),
        "model_root": str(model_root),
        "model_manifest_sha256": qualification_result["model_manifest_sha256"],
        "target_layer": TARGET_LAYER,
        "feature_width": FEATURE_WIDTH,
        "controls": list(CONTROL_NAMES),
        "ridge_candidate_alphas": list(RIDGE_ALPHAS),
        "assessment_family_count": len(prediction_rows),
        "predictions": prediction_rows,
        "assessment_effects_absent": True,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
    }

    fit_tune_summary = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": PREASSESSMENT_CLAIM_CEILING,
        "classification": "PreassessmentPredictionLocked",
        "panel_manifest_sha256": panel_digests["panel_manifest_sha256"],
        "concept_registry_sha256": panel_digests["concept_registry_sha256"],
        "split_manifest_sha256": panel_digests["split_manifest_sha256"],
        "model_manifest_sha256": qualification_result["model_manifest_sha256"],
        "target_layer": TARGET_LAYER,
        "feature_width": FEATURE_WIDTH,
        "fit_family_count": len(fit_targets),
        "tune_family_count": len(tune_targets),
        "assessment_family_count": len(assessment_ids),
        "panels": panel_summaries,
        "matched_control": {
            "fit_mean": float(fit["matched_effects"].mean()),
            "fit_std": float(fit["matched_effects"].std()),
            "tune_mean": float(tune["matched_effects"].mean()),
            "tune_std": float(tune["matched_effects"].std()),
            "fit_sequence_length_delta_max": fit["matched_sequence_length_delta_max"],
            "tune_sequence_length_delta_max": tune["matched_sequence_length_delta_max"],
            "used_for_tuning": False,
        },
        "target_effects": {
            "fit_mean": float(fit_targets.mean()),
            "fit_std": float(fit_targets.std()),
            "tune_mean": float(tune_targets.mean()),
            "tune_std": float(tune_targets.std()),
            "formula": "mean_pair_margin(do(layer_19_final:=paired_opposite_final))-mean_pair_margin(clean)",
        },
        "assessment_effects_absent": True,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
    }

    run_manifest = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "claim_ceiling": PREASSESSMENT_CLAIM_CEILING,
        "classification": "PreassessmentPredictionLocked",
        "panel_root": str(panel_root),
        "panel_manifest_sha256": panel_digests["panel_manifest_sha256"],
        "panel_validator_receipt_sha256": panel_digests["panel_validator_receipt_sha256"],
        "concept_registry_sha256": panel_digests["concept_registry_sha256"],
        "split_manifest_sha256": panel_digests["split_manifest_sha256"],
        "qualification_root": str(qualification_root),
        "qualification_result_sha256": _sha256_file(qualification_result_path),
        "qualification_validator_receipt_sha256": _sha256_file(qualification_receipt_path),
        "model_root": str(model_root),
        "model_manifest_sha256": qualification_result["model_manifest_sha256"],
        "runtime": {
            "python": platform.python_version(),
            "mlx": importlib.metadata.version("mlx"),
            "mlx_lm": importlib.metadata.version("mlx-lm"),
        },
        "source": {
            "runner_sha256": _sha256_file(Path(__file__).resolve()),
            "protocol_sha256": _sha256_file(Path(protocol.__file__).resolve()),
            "panel_source_sha256": _sha256_file(Path(panel.__file__).resolve()),
        },
        "fit_family_count": len(fit_targets),
        "tune_family_count": len(tune_targets),
        "assessment_family_count": len(assessment_ids),
        "assessment_predictions_materialized": True,
        "assessment_effects_present": False,
        "assessment_effects_measured": False,
        "prediction_locked_before_assessment": True,
        "raw_intermediates_retained": False,
        "aggregate_only": True,
        "network_access": False,
        "model_training": False,
        "stage_0c": False,
        "stage_1": False,
        "accepted_evidence": False,
        "prediction_lock_sha256": _json_digest(prediction_lock),
        "fit_tune_summary_sha256": _json_digest(fit_tune_summary),
    }

    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        _write_json(staging / "fit-tune-summary.json", fit_tune_summary)
        _write_json(staging / "prediction-lock.json", prediction_lock)
        _write_json(staging / "run-manifest.json", run_manifest)
        if output_root.exists():
            raise ValueError(f"preassessment root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def protocol_splits() -> tuple[str, str, str]:
    return ("fit", "tune", "assessment")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
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
    except (OSError, ValueError, corpus.CorpusError) as exc:
        print(json.dumps({"classification": "PreassessmentFailed", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
