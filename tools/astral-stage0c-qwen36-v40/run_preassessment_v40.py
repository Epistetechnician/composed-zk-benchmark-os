#!/usr/bin/env python3
"""Run V40 fit/tune effects and seal estimator-only assessment predictions.

State slice: astral-stage0c-qwen36-intervention-conditioned-target-v40.

The runner measures direct effects only on fit and tune, selects the fixed
ridge candidates using tune error, and stores fit-only estimator states rather
than per-family assessment predictions. Assessment features and predictions
are recomputed in memory only after the review gate.
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

import panel_v40 as panel
import protocol_v40 as protocol
import validate_panel_v40 as panel_validator
import validate_qualification_v40 as qualification_validator


def _hash_int(*parts: object) -> int:
    return int.from_bytes(hashlib.sha256(":".join(str(part) for part in parts).encode("utf-8")).digest()[:8], "big")


def _hash_sign(*parts: object) -> float:
    return 1.0 if _hash_int(*parts) & 1 else -1.0


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_digest(value: Any) -> str:
    return _digest(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _feature_vector(values: list[np.ndarray], scalars: list[float], prefix: str) -> np.ndarray:
    vector = np.zeros(protocol.FEATURE_WIDTH, dtype=np.float64)
    block_width = 62
    for block, values_for_block in enumerate(values):
        for dimension, value in enumerate(values_for_block.astype(np.float64)):
            bucket = block * block_width + (_hash_int(protocol.PROTOCOL_ID, prefix, block, dimension) % block_width)
            vector[bucket] += _hash_sign(protocol.PROTOCOL_ID, prefix, "sign", block, dimension) * value
    for index, value in enumerate(scalars[:8]):
        vector[248 + index] = float(value)
    return vector


def _pair_activation_features(ordinary: np.ndarray, counterfactual: np.ndarray) -> np.ndarray:
    delta = ordinary.astype(np.float64) - counterfactual.astype(np.float64)
    ordinary64 = ordinary.astype(np.float64)
    counterfactual64 = counterfactual.astype(np.float64)
    cosine_denominator = float(np.linalg.norm(ordinary64) * np.linalg.norm(counterfactual64))
    cosine = float(ordinary64 @ counterfactual64 / cosine_denominator) if cosine_denominator > 0.0 else 0.0
    return _feature_vector(
        [ordinary, counterfactual, delta, np.abs(delta)],
        [float(np.linalg.norm(ordinary64)), float(np.linalg.norm(counterfactual64)), float(np.linalg.norm(delta)), cosine],
        "pair",
    )


def _clean_activation_features(ordinary: np.ndarray, counterfactual: np.ndarray) -> np.ndarray:
    return _feature_vector([ordinary, counterfactual], [float(np.linalg.norm(ordinary)), float(np.linalg.norm(counterfactual))], "clean")


def _text_features(ordinary_prompt: str, counterfactual_prompt: str) -> np.ndarray:
    vector = np.zeros(protocol.FEATURE_WIDTH, dtype=np.float64)
    for label, text in (("ordinary", ordinary_prompt), ("counterfactual", counterfactual_prompt)):
        for word in panel.WORD_RE.findall(text.lower()):
            bucket = _hash_int(protocol.PROTOCOL_ID, "text", label, word) % protocol.FEATURE_WIDTH
            vector[bucket] += _hash_sign(protocol.PROTOCOL_ID, "text-sign", label, word)
    return vector


def _row_permutation(family_ids: list[str], split: str, panel_digest: str) -> np.ndarray:
    order = sorted(range(len(family_ids)), key=lambda index: _hash_int(protocol.PROTOCOL_ID, "shuffle", split, panel_digest, family_ids[index]))
    return np.asarray(order, dtype=np.int64)


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
                replacement = self.mx.array(self.replacement.astype(np.float32), dtype=output.dtype).reshape((1, 1, -1))
                output = self.mx.concatenate([output[:, :-1, :], replacement], axis=1)
        return output


def _forward(model: Any, base_layers: list[Any], token_ids: list[int], replacement: np.ndarray | None, response_ids: dict[str, int], mx: Any) -> tuple[np.ndarray, np.ndarray]:
    probes = [LayerProbe(layer, index, replacement, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([token_ids]))
        captured = probes[protocol.TARGET_LAYER].captured
        if captured is None:
            raise protocol.ProtocolError("target layer capture was not reached")
        selected = mx.stack([logits[0, -1, response_ids["A"]], logits[0, -1, response_ids["B"]]])
        vector = captured[0, -1, :].astype(mx.float32)
        mx.eval(logits, selected, vector)
        vector_np = np.array(vector, dtype=np.float32, copy=True)
        logits_np = np.array(selected.astype(mx.float32), dtype=np.float64, copy=True)
        if vector_np.shape != (protocol.EXPECTED_HIDDEN_WIDTH,) or not np.isfinite(vector_np).all() or not np.isfinite(logits_np).all():
            raise protocol.ProtocolError("non-finite or incorrectly shaped forward result")
        return vector_np, logits_np
    finally:
        model.language_model.model.layers = base_layers


def _margin(logits: np.ndarray, correct_label: str) -> float:
    return float(logits[0] - logits[1]) if correct_label == "A" else float(logits[1] - logits[0])


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> np.ndarray:
    source_norm = float(np.linalg.norm(source.astype(np.float64)))
    receiver_norm = float(np.linalg.norm(receiver.astype(np.float64)))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise protocol.ProtocolError("cannot norm-match a zero activation")
    return source * np.float32(receiver_norm / source_norm)


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token_text in protocol.RESPONSE_TOKENS.items():
        token_ids = list(tokenizer.encode(token_text))
        if len(token_ids) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
        result[label] = int(token_ids[0])
    return result


def _token_cache(registry: list[dict[str, Any]], tokenizer: Any) -> dict[str, dict[str, Any]]:
    cache: dict[str, dict[str, Any]] = {}
    for family in registry:
        ordinary = list(tokenizer.encode(family["ordinary_prompt"]))
        counterfactual = list(tokenizer.encode(family["counterfactual_prompt"]))
        if len(ordinary) < 2 or len(counterfactual) < 2:
            raise protocol.ProtocolError(f"family tokenization too short: {family['family_id']}")
        if len(ordinary) != protocol.FIXED_TOKEN_LENGTH or len(counterfactual) != protocol.FIXED_TOKEN_LENGTH:
            raise protocol.ProtocolError(f"family violates fixed tokenizer length: {family['family_id']}")
        cache[family["family_id"]] = {"ordinary": ordinary, "counterfactual": counterfactual, "ordinary_length": len(ordinary), "counterfactual_length": len(counterfactual)}
    return cache


def _matched_family(family: dict[str, Any], kind: str, same_split: list[dict[str, Any]], cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    length_key = f"{kind}_length"
    receiver_length = cache[family["family_id"]][length_key]
    candidates = [
        other for other in same_split
        if other["family_id"] != family["family_id"] and other["gutenberg_id"] != family["gutenberg_id"] and cache[other["family_id"]][length_key] == receiver_length
    ]
    if not candidates:
        raise protocol.ProtocolError(f"no exact-length cross-document donor for {family['family_id']}:{kind}")
    return min(candidates, key=lambda other: (abs(other["source_word_count"] - family["source_word_count"]), _hash_int(protocol.PROTOCOL_ID, "donor", family["family_id"], kind, other["family_id"])))


def _capture_clean(model: Any, base_layers: list[Any], families: list[dict[str, Any]], cache: dict[str, dict[str, Any]], response_ids: dict[str, int], mx: Any) -> dict[str, dict[str, Any]]:
    clean: dict[str, dict[str, Any]] = {}
    for family in families:
        family_id = family["family_id"]
        ordinary_vector, ordinary_logits = _forward(model, base_layers, cache[family_id]["ordinary"], None, response_ids, mx)
        counterfactual_vector, counterfactual_logits = _forward(model, base_layers, cache[family_id]["counterfactual"], None, response_ids, mx)
        clean[family_id] = {"ordinary_vector": ordinary_vector, "counterfactual_vector": counterfactual_vector, "ordinary_logits": ordinary_logits, "counterfactual_logits": counterfactual_logits}
    return clean


def _measure_effects(model: Any, base_layers: list[Any], families: list[dict[str, Any]], split_families: list[dict[str, Any]], cache: dict[str, dict[str, Any]], response_ids: dict[str, int], mx: Any) -> dict[str, Any]:
    if not families or families[0]["split"] == "assessment":
        raise protocol.ProtocolError("assessment effects are forbidden before review")
    clean = _capture_clean(model, base_layers, families, cache, response_ids, mx)
    pair_features: list[np.ndarray] = []
    clean_features: list[np.ndarray] = []
    text_features: list[np.ndarray] = []
    target_effects: list[float] = []
    matched_effects: list[float] = []
    matched_donors: list[str] = []
    for family in families:
        family_id = family["family_id"]
        current = clean[family_id]
        ordinary = current["ordinary_vector"]
        counterfactual = current["counterfactual_vector"]
        ordinary_clean_margin = _margin(current["ordinary_logits"], "A")
        counterfactual_clean_margin = _margin(current["counterfactual_logits"], "B")
        _, ordinary_pair_logits = _forward(model, base_layers, cache[family_id]["ordinary"], counterfactual, response_ids, mx)
        _, counterfactual_pair_logits = _forward(model, base_layers, cache[family_id]["counterfactual"], ordinary, response_ids, mx)
        target_effects.append(0.5 * (_margin(ordinary_pair_logits, "A") - ordinary_clean_margin + _margin(counterfactual_pair_logits, "B") - counterfactual_clean_margin))
        ordinary_donor = _matched_family(family, "ordinary", split_families, cache)
        counterfactual_donor = _matched_family(family, "counterfactual", split_families, cache)
        matched_donors.extend([ordinary_donor["family_id"], counterfactual_donor["family_id"]])
        _, ordinary_match_logits = _forward(model, base_layers, cache[family_id]["ordinary"], _norm_match(clean[ordinary_donor["family_id"]]["ordinary_vector"], ordinary), response_ids, mx)
        _, counterfactual_match_logits = _forward(model, base_layers, cache[family_id]["counterfactual"], _norm_match(clean[counterfactual_donor["family_id"]]["counterfactual_vector"], counterfactual), response_ids, mx)
        matched_effects.append(0.5 * (_margin(ordinary_match_logits, "A") - ordinary_clean_margin + _margin(counterfactual_match_logits, "B") - counterfactual_clean_margin))
        pair_features.append(_pair_activation_features(ordinary, counterfactual))
        clean_features.append(_clean_activation_features(ordinary, counterfactual))
        text_features.append(_text_features(family["ordinary_prompt"], family["counterfactual_prompt"]))
    return {"family_ids": [family["family_id"] for family in families], "documents": [int(family["gutenberg_id"]) for family in families], "pair_features": np.asarray(pair_features), "clean_features": np.asarray(clean_features), "text_features": np.asarray(text_features), "target_effects": np.asarray(target_effects), "matched_effects": np.asarray(matched_effects), "matched_donors": matched_donors}


def _measure_features(model: Any, base_layers: list[Any], families: list[dict[str, Any]], cache: dict[str, dict[str, Any]], response_ids: dict[str, int], mx: Any) -> dict[str, Any]:
    clean = _capture_clean(model, base_layers, families, cache, response_ids, mx)
    pair_features: list[np.ndarray] = []
    clean_features: list[np.ndarray] = []
    text_features: list[np.ndarray] = []
    for family in families:
        current = clean[family["family_id"]]
        pair_features.append(_pair_activation_features(current["ordinary_vector"], current["counterfactual_vector"]))
        clean_features.append(_clean_activation_features(current["ordinary_vector"], current["counterfactual_vector"]))
        text_features.append(_text_features(family["ordinary_prompt"], family["counterfactual_prompt"]))
    return {"family_ids": [family["family_id"] for family in families], "pair_features": np.asarray(pair_features), "clean_features": np.asarray(clean_features), "text_features": np.asarray(text_features)}


def _fit_ridge(features: np.ndarray, targets: np.ndarray, alpha: float) -> dict[str, Any]:
    if features.shape != (len(targets), protocol.FEATURE_WIDTH):
        raise protocol.ProtocolError("feature panel shape mismatch")
    mean = features.mean(axis=0)
    scale = np.where(features.std(axis=0) < 1e-12, 1.0, features.std(axis=0))
    centered = (features - mean) / scale
    target_mean = float(targets.mean())
    coefficients = np.linalg.solve(centered.T @ centered + alpha * np.eye(protocol.FEATURE_WIDTH), centered.T @ (targets - target_mean))
    return {"feature_mean": mean, "feature_scale": scale, "target_mean": target_mean, "coefficients": coefficients, "alpha": float(alpha)}


def _predict(state: dict[str, Any], features: np.ndarray) -> np.ndarray:
    return state["target_mean"] + ((features - state["feature_mean"]) / state["feature_scale"]) @ state["coefficients"]


def _select(name: str, fit_features: np.ndarray, fit_targets: np.ndarray, tune_features: np.ndarray, tune_targets: np.ndarray) -> tuple[dict[str, Any], dict[str, Any]]:
    choices = []
    for alpha in protocol.RIDGE_ALPHAS:
        state = _fit_ridge(fit_features, fit_targets, alpha)
        fit_error = float(np.mean((_predict(state, fit_features) - fit_targets) ** 2))
        tune_error = float(np.mean((_predict(state, tune_features) - tune_targets) ** 2))
        choices.append((tune_error, alpha, state, fit_error))
    tune_mse, alpha, selected, fit_mse = min(choices, key=lambda item: (item[0], item[1]))
    return selected, {"name": name, "candidate_alphas": list(protocol.RIDGE_ALPHAS), "selected_alpha": alpha, "fit_count": len(fit_targets), "tune_count": len(tune_targets), "fit_rmse": math.sqrt(fit_mse), "tune_rmse": math.sqrt(tune_mse), "fit_target_mean": float(fit_targets.mean()), "fit_target_std": float(fit_targets.std()), "tune_target_mean": float(tune_targets.mean()), "tune_target_std": float(tune_targets.std())}


def _state_json(state: dict[str, Any]) -> dict[str, Any]:
    if "coefficients" not in state:
        return {"target_mean": state["target_mean"]}
    return {"alpha": state["alpha"], "feature_mean": state["feature_mean"].tolist(), "feature_scale": state["feature_scale"].tolist(), "target_mean": state["target_mean"], "coefficients": state["coefficients"].tolist()}


def _load_inputs(panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    panel_receipt = panel_validator.validate(panel_root, corpus_root, model_root, repository_root)
    if not panel_receipt["valid"]:
        raise protocol.ProtocolError("panel validation failed")
    qualification_receipt = qualification_validator.validate(qualification_root, model_root, repository_root)
    if not qualification_receipt["valid"]:
        raise protocol.ProtocolError("qualification validation failed")
    registry_document = protocol.read_json(panel_root / "concept-registry.json")
    registry = registry_document.get("families")
    if not isinstance(registry, list) or len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("concept registry is invalid")
    digests = {
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "concept_registry_sha256": protocol.sha256_file(panel_root / "concept-registry.json"),
        "split_manifest_sha256": protocol.sha256_file(panel_root / "split-manifest.json"),
        "panel_validator_receipt_sha256": protocol.sha256_file(panel_root / "validator-receipt.json") if (panel_root / "validator-receipt.json").is_file() else None,
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "qualification_validator_receipt_sha256": protocol.sha256_file(qualification_root / "validator-receipt.json") if (qualification_root / "validator-receipt.json").is_file() else None,
        "model_manifest_sha256": protocol.model_manifest(model_root)["manifest_sha256"],
    }
    return registry, digests, {"panel_receipt": panel_receipt, "qualification_receipt": qualification_receipt}


def run_preassessment(panel_root: Path, corpus_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path) -> Path:
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite preassessment root: {output_root}")
    registry, digests, _ = _load_inputs(panel_root.resolve(), corpus_root.resolve(), qualification_root.resolve(), model_root.resolve(), repository_root)
    by_split = {split: [family for family in registry if family["split"] == split] for split in protocol.SPLITS}
    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root.resolve()), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("model layer count mismatch")
    response_ids = _strict_response_ids(tokenizer)
    cache = _token_cache(registry, tokenizer)
    fit = _measure_effects(model, base_layers, by_split["fit"], by_split["fit"], cache, response_ids, mx)
    tune = _measure_effects(model, base_layers, by_split["tune"], by_split["tune"], cache, response_ids, mx)
    assessment = _measure_features(model, base_layers, by_split["assessment"], cache, response_ids, mx)
    panel_inputs = {
        protocol.PRIMARY_CONTROL: (fit["pair_features"], tune["pair_features"]),
        "clean_activation_only": (fit["clean_features"], tune["clean_features"]),
        "text_only": (fit["text_features"], tune["text_features"]),
    }
    panel_states: dict[str, dict[str, Any]] = {}
    summaries: dict[str, dict[str, Any]] = {}
    panel_digest = digests["panel_manifest_sha256"]
    for name, (fit_features, tune_features) in panel_inputs.items():
        state, summary = _select(name, fit_features, fit["target_effects"], tune_features, tune["target_effects"])
        panel_states[name] = state
        summaries[name] = summary
    shuffled_fit = fit["pair_features"][_row_permutation(fit["family_ids"], "fit", panel_digest)]
    shuffled_tune = tune["pair_features"][_row_permutation(tune["family_ids"], "tune", panel_digest)]
    shuffled_state, shuffled_summary = _select("shuffled", shuffled_fit, fit["target_effects"], shuffled_tune, tune["target_effects"])
    panel_states["shuffled"] = shuffled_state
    summaries["shuffled"] = shuffled_summary
    fit_mean = float(fit["target_effects"].mean())
    constant_predictions_fit = np.full(len(fit["target_effects"]), fit_mean)
    constant_predictions_tune = np.full(len(tune["target_effects"]), fit_mean)
    summaries["constant"] = {"name": "constant", "candidate_alphas": [], "selected_alpha": None, "fit_count": len(fit["target_effects"]), "tune_count": len(tune["target_effects"]), "fit_rmse": math.sqrt(float(np.mean((constant_predictions_fit - fit["target_effects"]) ** 2))), "tune_rmse": math.sqrt(float(np.mean((constant_predictions_tune - tune["target_effects"]) ** 2))), "fit_target_mean": fit_mean, "fit_target_std": float(fit["target_effects"].std()), "tune_target_mean": float(tune["target_effects"].mean()), "tune_target_std": float(tune["target_effects"].std())}
    panel_states["constant"] = {"target_mean": fit_mean}

    assessment_features = {protocol.PRIMARY_CONTROL: assessment["pair_features"], "clean_activation_only": assessment["clean_features"], "text_only": assessment["text_features"], "shuffled": assessment["pair_features"][_row_permutation(assessment["family_ids"], "assessment", panel_digest)], "constant": np.empty((len(assessment["family_ids"]), 0))}
    # Compute locked predictions in memory; the lock stores only estimator states and family order.
    _ = {name: (_predict(panel_states[name], features) if name != "constant" else np.full(len(assessment["family_ids"]), fit_mean)) for name, features in assessment_features.items()}
    prediction_lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "lock_id": "astral-stage0c-qwen36-intervention-conditioned-target-v40-prediction-lock-v1",
        **digests,
        "panel_id": panel.PANEL_ID,
        "target_layer": protocol.TARGET_LAYER,
        "feature_width": protocol.FEATURE_WIDTH,
        "ridge_candidate_alphas": list(protocol.RIDGE_ALPHAS),
        "controls": list(protocol.CONTROL_NAMES),
        "assessment_family_ids": assessment["family_ids"],
        "estimator_states": {name: _state_json(state) for name, state in panel_states.items()},
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
        "claim_ceiling": "LocalDevelopmentV40PreassessmentPredictionLocked",
        **digests,
        "target_layer": protocol.TARGET_LAYER,
        "feature_width": protocol.FEATURE_WIDTH,
        "fit_family_count": len(fit["family_ids"]),
        "tune_family_count": len(tune["family_ids"]),
        "assessment_family_count": len(assessment["family_ids"]),
        "panels": summaries,
        "target_effects": {"fit_mean": float(fit["target_effects"].mean()), "fit_std": float(fit["target_effects"].std()), "tune_mean": float(tune["target_effects"].mean()), "tune_std": float(tune["target_effects"].std())},
        "matched_control": {"fit_mean": float(fit["matched_effects"].mean()), "fit_std": float(fit["matched_effects"].std()), "tune_mean": float(tune["matched_effects"].mean()), "tune_std": float(tune["matched_effects"].std()), "used_for_tuning": False},
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
        "runner_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        **digests,
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
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
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
        root = run_preassessment(args.panel_root, args.corpus_root, args.qualification_root, args.model, args.output_root, args.repository_root)
    except (OSError, ImportError, KeyError, json.JSONDecodeError, protocol.ProtocolError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({"preassessment_root": str(root), "classification": "PreassessmentPredictionLocked", "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
