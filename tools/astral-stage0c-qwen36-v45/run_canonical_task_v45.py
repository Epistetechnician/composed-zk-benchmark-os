#!/usr/bin/env python3
"""Run V45 fit/tune prediction locking with assessment closed.

State slice: astral-stage0c-qwen36-response-anchored-causal-target-v45.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import protocol_v45 as protocol


BATCH_SIZE = protocol.BATCH_SIZE
CLAIM_CEILING_NO_CANDIDATE = "LocalDevelopmentV45CanonicalTaskNoCandidate"
CLAIM_CEILING_REVIEW = "LocalDevelopmentV45CanonicalTaskReviewRequired"


def _summary(values: np.ndarray | list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise protocol.ProtocolError("cannot summarize empty or non-finite values")
    return {
        "count": int(array.size),
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
        "mean_abs": float(np.mean(np.abs(array))),
        "min": float(np.min(array)),
        "max": float(np.max(array)),
    }


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    if left.size != right.size or left.size < 2 or float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def _sign_agreement(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.sign(left) == np.sign(right)))


def _bootstrap_lower(left: np.ndarray, right: np.ndarray, seed: int) -> float:
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(protocol.BOOTSTRAP_RESAMPLES):
        indices = rng.integers(0, left.size, size=left.size)
        values.append(_correlation(left[indices], right[indices]))
    return float(np.quantile(np.asarray(values, dtype=np.float64), 0.025))


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token in protocol.RESPONSE_TOKENS.items():
        encoded = list(tokenizer.encode(token))
        if len(encoded) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
        result[label] = int(encoded[0])
    return result


def _replace_rows(output: Any, positions: list[int], replacements: np.ndarray, mx: Any) -> Any:
    batch_size = int(output.shape[0])
    sequence_length = int(output.shape[1])
    if len(positions) != batch_size or replacements.shape != (batch_size, int(output.shape[-1])):
        raise protocol.ProtocolError("replacement batch shape mismatch")
    if any(position < 0 or position >= sequence_length for position in positions):
        raise protocol.ProtocolError("content anchor is outside the layer sequence")
    position_array = mx.array(positions)
    current = output[mx.arange(batch_size), position_array, :]
    mask = (mx.arange(sequence_length)[None, :] == position_array[:, None])[:, :, None]
    return mx.where(mask, mx.array(replacements.astype(np.float32), dtype=output.dtype)[:, None, :], output)


class LayerProbe:
    def __init__(self, layer: Any, index: int, capture_layers: set[int], positions: list[int], target_layer: int | None, replacements: np.ndarray | None, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.capture_layers = capture_layers
        self.positions = positions
        self.target_layer = target_layer
        self.replacements = replacements
        self.mx = mx
        self.captured = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        if self.index in self.capture_layers:
            rows = self.mx.arange(int(output.shape[0]))
            self.captured = output[rows, self.mx.array(self.positions), :]
        if self.target_layer == self.index:
            if self.replacements is None:
                raise protocol.ProtocolError("target layer replacements are missing")
            output = _replace_rows(output, self.positions, self.replacements, self.mx)
        return output


def _forward_batch(
    model: Any,
    base_layers: list[Any],
    token_rows: list[list[int]],
    positions: list[int],
    response_ids: dict[str, int],
    mx: Any,
    target_layer: int | None = None,
    replacements: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    capture_layers = set(protocol.CANDIDATE_LAYERS) if target_layer is None else set()
    probes = [LayerProbe(layer, index, capture_layers, positions, target_layer, replacements, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array(token_rows))
        captures = [probe.captured for probe in probes if probe.captured is not None]
        if len(captures) != len(capture_layers):
            raise protocol.ProtocolError("not all candidate layers were captured")
        selected = mx.stack([logits[:, -1, response_ids["A"]], logits[:, -1, response_ids["B"]]], axis=1)
        mx.eval(selected, *captures)
        capture_map: dict[str, np.ndarray] = {}
        if target_layer is not None:
            logits_np = np.array(selected.astype(mx.float32), dtype=np.float64, copy=True)
            if logits_np.shape != (len(token_rows), 2) or not np.isfinite(logits_np).all():
                raise protocol.ProtocolError("invalid selected logits")
            return capture_map, logits_np
        for layer in protocol.CANDIDATE_LAYERS:
            captured = probes[layer].captured
            if captured is None:
                raise protocol.ProtocolError(f"candidate layer was not captured: {layer}")
            value = np.array(captured.astype(mx.float32), dtype=np.float32, copy=True)
            expected = (len(token_rows), protocol.EXPECTED_HIDDEN_WIDTH)
            if value.shape != expected or not np.isfinite(value).all():
                raise protocol.ProtocolError(f"invalid capture shape/value: {layer}:{value.shape}")
            capture_map[str(layer)] = value
        logits_np = np.array(selected.astype(mx.float32), dtype=np.float64, copy=True)
        if logits_np.shape != (len(token_rows), 2) or not np.isfinite(logits_np).all():
            raise protocol.ProtocolError("invalid selected logits")
        return capture_map, logits_np
    finally:
        model.language_model.model.layers = base_layers


def _capture_clean(model: Any, base_layers: list[Any], families: list[dict[str, Any]], tokenizer: Any, response_ids: dict[str, int], mx: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for start in range(0, len(families), BATCH_SIZE // 2):
        batch = families[start : start + BATCH_SIZE // 2]
        token_rows: list[list[int]] = []
        positions: list[int] = []
        for family in batch:
            for condition in ("ordinary", "counterfactual"):
                prompt = family[f"{condition}_prompt"]
                token_rows.append(list(tokenizer.encode(prompt)))
                positions.append(int(family[f"{condition}_content_anchor_index"]))
        captures, logits = _forward_batch(model, base_layers, token_rows, positions, response_ids, mx)
        for offset, family in enumerate(batch):
            ordinary_index = 2 * offset
            counterfactual_index = ordinary_index + 1
            result[family["family_id"]] = {
                "ordinary_logits": logits[ordinary_index],
                "counterfactual_logits": logits[counterfactual_index],
                "vectors": {
                    str(layer): {
                        "ordinary": captures[str(layer)][ordinary_index],
                        "counterfactual": captures[str(layer)][counterfactual_index],
                    }
                    for layer in protocol.CANDIDATE_LAYERS
                },
            }
    return result


def _run_replacements(model: Any, base_layers: list[Any], rows: list[list[int]], positions: list[int], replacements: list[np.ndarray], response_ids: dict[str, int], target_layer: int, mx: Any) -> np.ndarray:
    result: list[np.ndarray] = []
    for start in range(0, len(rows), BATCH_SIZE):
        row_batch = rows[start : start + BATCH_SIZE]
        position_batch = positions[start : start + BATCH_SIZE]
        replacement_batch = np.asarray(replacements[start : start + BATCH_SIZE], dtype=np.float32)
        _, logits = _forward_batch(model, base_layers, row_batch, position_batch, response_ids, mx, target_layer, replacement_batch)
        result.append(logits)
    if not result:
        raise protocol.ProtocolError("replacement batch is empty")
    return np.concatenate(result, axis=0)


def _margin(logits: np.ndarray, label: str) -> float:
    return float(logits[0] - logits[1]) if label == "A" else float(logits[1] - logits[0])


def _effect(ordinary_clean: np.ndarray, counterfactual_clean: np.ndarray, ordinary_intervened: np.ndarray, counterfactual_intervened: np.ndarray) -> float:
    return 0.5 * (
        _margin(ordinary_intervened, "A") - _margin(ordinary_clean, "A")
        + _margin(counterfactual_intervened, "B") - _margin(counterfactual_clean, "B")
    )


def _text_only_effect(ordinary_clean: np.ndarray, counterfactual_clean: np.ndarray) -> float:
    return 0.5 * (
        _margin(ordinary_clean, "A") - _margin(counterfactual_clean, "A")
        + _margin(counterfactual_clean, "B") - _margin(ordinary_clean, "B")
    )


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> tuple[np.ndarray, float]:
    source_norm = float(np.linalg.norm(source.astype(np.float64)))
    receiver_norm = float(np.linalg.norm(receiver.astype(np.float64)))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise protocol.ProtocolError("cannot norm-match a zero activation")
    replacement = source * np.float32(receiver_norm / source_norm)
    relative_error = abs(float(np.linalg.norm(replacement.astype(np.float64))) - receiver_norm) / receiver_norm
    if relative_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
        raise protocol.ProtocolError("matched norm error exceeds tolerance")
    return replacement, relative_error


def _feature(vector_pair: dict[str, np.ndarray]) -> np.ndarray:
    difference = vector_pair["counterfactual"].astype(np.float64) - vector_pair["ordinary"].astype(np.float64)
    blocks = difference.reshape(protocol.BLOCK_COUNT, protocol.BLOCK_WIDTH).mean(axis=1)
    blocks[1::2] *= -1.0
    return blocks


def _donor(family: dict[str, Any], families: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = sorted((other for other in families if other["family_id"] != family["family_id"] and other["gutenberg_id"] != family["gutenberg_id"]), key=lambda item: item["family_id"])
    if not candidates:
        raise protocol.ProtocolError("no document-disjoint donor exists")
    return candidates[0]


def _measure_cell(model: Any, base_layers: list[Any], families: list[dict[str, Any]], clean: dict[str, dict[str, Any]], tokenizer: Any, response_ids: dict[str, int], layer: int, mx: Any) -> tuple[dict[str, np.ndarray], float, int, float]:
    means = {
        "ordinary": np.mean([clean[family["family_id"]]["vectors"][str(layer)]["ordinary"] for family in families], axis=0),
        "counterfactual": np.mean([clean[family["family_id"]]["vectors"][str(layer)]["counterfactual"] for family in families], axis=0),
    }
    conditions = ("activation_repeat_1", "activation_repeat_2", "exact_copy", "shuffled", "constant", "matched")
    rows: list[list[int]] = []
    positions: list[int] = []
    replacements: list[np.ndarray] = []
    descriptors: list[tuple[str, str]] = []
    max_norm_error = 0.0
    violations = 0
    for family in families:
        family_id = family["family_id"]
        donor = _donor(family, families)
        own = clean[family_id]["vectors"][str(layer)]
        donor_vectors = clean[donor["family_id"]]["vectors"][str(layer)]
        matched_cf, cf_error = _norm_match(donor_vectors["counterfactual"], own["ordinary"])
        matched_ord, ord_error = _norm_match(donor_vectors["ordinary"], own["counterfactual"])
        max_norm_error = max(max_norm_error, cf_error, ord_error)
        violations += int(cf_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE) + int(ord_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE)
        replacement_pairs = {
            "activation_repeat_1": (own["counterfactual"], own["ordinary"]),
            "activation_repeat_2": (own["counterfactual"], own["ordinary"]),
            "exact_copy": (own["ordinary"], own["counterfactual"]),
            "shuffled": (donor_vectors["counterfactual"], donor_vectors["ordinary"]),
            "constant": (means["counterfactual"], means["ordinary"]),
            "matched": (matched_cf, matched_ord),
        }
        ordinary_tokens = list(tokenizer.encode(family["ordinary_prompt"]))
        counterfactual_tokens = list(tokenizer.encode(family["counterfactual_prompt"]))
        for condition in conditions:
            rows.extend([ordinary_tokens, counterfactual_tokens])
            positions.extend([int(family["ordinary_content_anchor_index"]), int(family["counterfactual_content_anchor_index"])])
            replacements.extend(replacement_pairs[condition])
            descriptors.extend([(family_id, condition), (family_id, condition)])
    intervened = _run_replacements(model, base_layers, rows, positions, replacements, response_ids, layer, mx)
    effects = {condition: [] for condition in conditions}
    for row_index in range(0, len(descriptors), 2):
        family_id, condition = descriptors[row_index]
        if descriptors[row_index + 1] != (family_id, condition):
            raise protocol.ProtocolError("intervention row pairing changed")
        clean_family = clean[family_id]
        effects[condition].append(_effect(clean_family["ordinary_logits"], clean_family["counterfactual_logits"], intervened[row_index], intervened[row_index + 1]))
    repeat_delta = max(abs(left - right) for left, right in zip(effects["activation_repeat_1"], effects["activation_repeat_2"]))
    return {name: np.asarray(values, dtype=np.float64) for name, values in effects.items()}, max_norm_error, violations, repeat_delta


def _measure_split(model: Any, base_layers: list[Any], families: list[dict[str, Any]], tokenizer: Any, response_ids: dict[str, int], mx: Any, clean: dict[str, dict[str, Any]] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    if clean is None:
        clean = _capture_clean(model, base_layers, families, tokenizer, response_ids, mx)
    cells: dict[str, Any] = {}
    raw: dict[str, Any] = {}
    for layer in protocol.CANDIDATE_LAYERS:
        cell_key = f"{layer}:{protocol.POSITION_NAME}"
        effects, max_norm_error, violations, repeat_delta = _measure_cell(model, base_layers, families, clean, tokenizer, response_ids, layer, mx)
        activation = effects["activation_repeat_1"]
        controls = {name: _summary(effects[name]) for name in ("exact_copy", "shuffled", "constant", "matched")}
        target_summary = _summary(activation)
        gates = {
            "target_effect_non_degenerate": target_summary["std"] >= protocol.MIN_TARGET_EFFECT_STD,
            "exact_copy_control": controls["exact_copy"]["mean_abs"] <= protocol.MAX_EXACT_COPY_ABS_EFFECT,
            "shuffled_control": abs(controls["shuffled"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
            "constant_control": abs(controls["constant"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
            "matched_control": abs(controls["matched"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
            "repeatability": repeat_delta <= protocol.MAX_REPEAT_ABS_EFFECT_DELTA,
        }
        family_features = np.asarray([_feature(clean[family["family_id"]]["vectors"][str(layer)]) for family in families], dtype=np.float64)
        text_only = np.asarray([_text_only_effect(clean[family["family_id"]]["ordinary_logits"], clean[family["family_id"]]["counterfactual_logits"]) for family in families], dtype=np.float64)
        raw[cell_key] = {"features": family_features, "effects": activation, "controls": effects, "text_only": text_only}
        cells[cell_key] = {
            "layer": layer,
            "position": protocol.POSITION_NAME,
            "position_rule": protocol.POSITION_RULE,
            "family_count": len(families),
            "document_count": len({int(family["gutenberg_id"]) for family in families}),
            "activation_only": target_summary,
            "text_only": _summary(text_only),
            "controls": controls,
            "matched_norm_relative_error_max": max_norm_error,
            "matched_donor_violations": violations,
            "repeat_max_abs_effect_delta": repeat_delta,
            "reliability": {"gates": gates},
        }
    return {"family_count": len(families), "document_count": len({int(family["gutenberg_id"]) for family in families}), "candidate_layers": list(protocol.CANDIDATE_LAYERS), "position_name": protocol.POSITION_NAME, "cell_summaries": cells}, raw


def _fit_ridge(features: np.ndarray, labels: np.ndarray, alpha: float) -> tuple[np.ndarray, float]:
    if features.ndim != 2 or labels.ndim != 1 or features.shape[0] != labels.size:
        raise protocol.ProtocolError("ridge input shape mismatch")
    mean_x = np.mean(features, axis=0)
    mean_y = float(np.mean(labels))
    centered = features - mean_x
    identity = np.eye(features.shape[1], dtype=np.float64)
    weights = np.linalg.solve(centered.T @ centered + alpha * identity, centered.T @ (labels - mean_y))
    intercept = mean_y - float(mean_x @ weights)
    return weights, intercept


def _prediction_metrics(predicted: np.ndarray, observed: np.ndarray, seed: int) -> dict[str, Any]:
    correlation = _correlation(predicted, observed)
    sign_agreement = _sign_agreement(predicted, observed)
    bootstrap = _bootstrap_lower(predicted, observed, seed)
    return {
        "correlation": correlation,
        "sign_agreement": sign_agreement,
        "bootstrap_correlation_lower_95": bootstrap,
        "gates": {
            "prediction_correlation": correlation >= protocol.MIN_PREDICTION_CORRELATION,
            "prediction_sign_agreement": sign_agreement >= protocol.MIN_PREDICTION_SIGN_AGREEMENT,
            "bootstrap_correlation": bootstrap >= protocol.MIN_BOOTSTRAP_CORRELATION_LOWER,
        },
    }


def _load_custody(panel_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    for path in (panel_root, qualification_root, model_root):
        protocol.assert_external(path, repository_root)
    panel_manifest = protocol.read_json(panel_root / "panel-manifest.json")
    qualification = protocol.read_json(qualification_root / "qualification-result.json")
    panel_receipt = protocol.read_json(panel_root / "validator-receipt.json")
    qualification_receipt = protocol.read_json(qualification_root / "validator-receipt.json")
    registry_doc = protocol.read_json(panel_root / "concept-registry.json")
    if panel_receipt.get("valid") is not True or qualification_receipt.get("valid") is not True:
        raise protocol.ProtocolError("independent panel and qualification receipts are required")
    if panel_manifest.get("protocol") != protocol.PROTOCOL_ID or qualification.get("protocol") != protocol.PROTOCOL_ID or registry_doc.get("protocol") != protocol.PROTOCOL_ID:
        raise protocol.ProtocolError("V45 custody protocol mismatch")
    if panel_manifest.get("state_slice") != protocol.STATE_SLICE or qualification.get("state_slice") != protocol.STATE_SLICE or registry_doc.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("V45 custody state-slice mismatch")
    if qualification.get("classification") != "InstrumentFeasibility" or not all(qualification.get("gates", {}).values()):
        raise protocol.ProtocolError("V45 qualification is not fully passing")
    if qualification.get("protocol_source_sha256") != protocol.sha256_file(Path(protocol.__file__).resolve()):
        raise protocol.ProtocolError("V45 qualification protocol source digest is stale")
    model_manifest = protocol.model_manifest(model_root)
    if panel_manifest.get("model_manifest_sha256") != model_manifest["manifest_sha256"] or qualification.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
        raise protocol.ProtocolError("model manifest binding mismatch")
    families = registry_doc.get("families")
    if not isinstance(families, list) or len(families) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("V45 family registry is invalid")
    return panel_manifest, qualification, model_manifest, families


def run(panel_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path) -> Path:
    panel_root = panel_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite measurement root: {output_root}")
    panel_manifest, qualification, model_manifest, families = _load_custody(panel_root, qualification_root, model_root, repository_root)
    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("model layer count differs from custody")
    response_ids = _strict_response_ids(tokenizer)
    by_split = {split: [family for family in families if family["split"] == split] for split in protocol.SPLITS}
    fit_summary, fit_raw = _measure_split(model, base_layers, by_split["fit"], tokenizer, response_ids, mx)
    models: dict[str, tuple[np.ndarray, float, str]] = {}
    for layer in protocol.CANDIDATE_LAYERS:
        cell_key = f"{layer}:{protocol.POSITION_NAME}"
        for alpha in protocol.RIDGE_ALPHAS:
            weights, intercept = _fit_ridge(fit_raw[cell_key]["features"], fit_raw[cell_key]["effects"], alpha)
            models[f"{cell_key}:alpha={alpha:g}"] = (weights, intercept, protocol.canonical_digest(weights.tolist() + [intercept]))
    tune_clean = _capture_clean(model, base_layers, by_split["tune"], tokenizer, response_ids, mx)
    tune_features = {
        f"{layer}:{protocol.POSITION_NAME}": np.asarray([_feature(tune_clean[family["family_id"]]["vectors"][str(layer)]) for family in by_split["tune"]], dtype=np.float64)
        for layer in protocol.CANDIDATE_LAYERS
    }
    tune_predictions: dict[str, np.ndarray] = {}
    for layer in protocol.CANDIDATE_LAYERS:
        cell_key = f"{layer}:{protocol.POSITION_NAME}"
        for alpha in protocol.RIDGE_ALPHAS:
            model_key = f"{cell_key}:alpha={alpha:g}"
            weights, intercept, _ = models[model_key]
            # Prediction is produced before any tune intervention effect is
            # generated, preserving the preregistered lock ordering.
            tune_predictions[model_key] = tune_features[cell_key] @ weights + intercept
    tune_summary, tune_raw = _measure_split(model, base_layers, by_split["tune"], tokenizer, response_ids, mx, clean=tune_clean)
    for layer in protocol.CANDIDATE_LAYERS:
        cell_key = f"{layer}:{protocol.POSITION_NAME}"
        for alpha in protocol.RIDGE_ALPHAS:
            model_key = f"{cell_key}:alpha={alpha:g}"
            metrics = _prediction_metrics(tune_predictions[model_key], tune_raw[cell_key]["effects"], protocol.BOOTSTRAP_SEED + layer * 100 + int(alpha * 10))
            tune_summary["cell_summaries"][cell_key].setdefault("predictors", {})[f"alpha={alpha:g}"] = metrics
    passing: list[dict[str, Any]] = []
    for layer in protocol.CANDIDATE_LAYERS:
        cell_key = f"{layer}:{protocol.POSITION_NAME}"
        cell = tune_summary["cell_summaries"][cell_key]
        for alpha in protocol.RIDGE_ALPHAS:
            alpha_key = f"alpha={alpha:g}"
            predictor = cell["predictors"][alpha_key]
            gates = {**cell["reliability"]["gates"], **predictor["gates"]}
            if all(gates.values()):
                passing.append({"layer": layer, "position": protocol.POSITION_NAME, "alpha": alpha, "gates": gates})
    selected = passing[0] if passing else None
    prediction_digests = {key: protocol.canonical_digest(value.tolist()) for key, value in tune_predictions.items()}
    lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_name": protocol.POSITION_NAME,
        "position_rule": protocol.POSITION_RULE,
        "content_anchor_offset": protocol.CONTENT_ANCHOR_OFFSET,
        "feature_map_id": protocol.FEATURE_MAP_ID,
        "ridge_alphas": list(protocol.RIDGE_ALPHAS),
        "selected_target": selected,
        "passing_targets": passing,
        "prediction_digests": prediction_digests,
        "measured_splits": ["fit", "tune"],
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "assessment_opened": False,
        "prediction_lock_before_assessment": True,
    }
    lock["configuration_lock_sha256"] = protocol.canonical_digest(lock)
    classification = "ReviewRequired" if selected is not None else "CanonicalTaskNoCandidate"
    claim_ceiling = CLAIM_CEILING_REVIEW if selected is not None else CLAIM_CEILING_NO_CANDIDATE
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": classification,
        "claim_ceiling": claim_ceiling,
        "aggregate_only_retention": True,
        "assessment_opened": False,
        "assessment_effects_present": False,
        "review_required_before_assessment": selected is not None,
        "review_verified": False,
        "prediction_lock_before_assessment": True,
        "panel_manifest_sha256": lock["panel_manifest_sha256"],
        "qualification_result_sha256": lock["qualification_result_sha256"],
        "model_manifest_sha256": lock["model_manifest_sha256"],
        "configuration_lock_sha256": lock["configuration_lock_sha256"],
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_name": protocol.POSITION_NAME,
        "position_rule": protocol.POSITION_RULE,
        "content_anchor_offset": protocol.CONTENT_ANCHOR_OFFSET,
        "feature_map_id": protocol.FEATURE_MAP_ID,
        "ridge_alphas": list(protocol.RIDGE_ALPHAS),
        "measured_splits": ["fit", "tune"],
        "selection_rule": "lowest_numeric_layer_then_lowest_alpha_passing_all_tune_gates",
        "passing_targets": passing,
        "selected_target": selected,
        "splits": {"fit": fit_summary, "tune": tune_summary},
        "source_sha256": {"protocol": protocol.sha256_file(Path(protocol.__file__).resolve()), "runner": protocol.sha256_file(Path(__file__).resolve())},
    }
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        protocol.write_json(staging / "configuration-lock.json", lock)
        protocol.write_json(staging / "canonical-task-result.json", result)
        if output_root.exists():
            raise protocol.ProtocolError(f"measurement root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = run(args.panel_root, args.qualification_root, args.model, args.output_root, args.repository_root.resolve())
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    result = protocol.read_json(root / "canonical-task-result.json")
    print(json.dumps({"measurement_root": str(root), "classification": result["classification"], "selected_target": result["selected_target"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
