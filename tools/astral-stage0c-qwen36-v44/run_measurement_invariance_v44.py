#!/usr/bin/env python3
"""Run V44 fit/tune measurement-invariance effects with assessment closed.

State slice: astral-stage0c-qwen36-causal-target-measurement-invariance-v44.

All activation and logit arrays are bounded to process memory. Only aggregate
statistics, custody digests, a prediction lock, and a narrow disposition are
written. A tune candidate cannot open assessment or establish Stage 0C.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

import protocol_v44 as protocol


CLAIM_CEILING_NO_CANDIDATE = "LocalDevelopmentV44MeasurementInvarianceNoCandidate"
CLAIM_CEILING_REVIEW = "LocalDevelopmentV44MeasurementInvarianceReviewRequired"
CLAIM_CEILING_RESULT = "LocalDevelopmentV44CausalTargetMeasurementInvariance"
INTERVENTION_BATCH_SIZE = 4


def _digest(value: Any) -> str:
    return protocol.canonical_digest(value)


def _configuration_lock_digest(lock: dict[str, Any]) -> str:
    return _digest({key: value for key, value in lock.items() if key != "configuration_lock_sha256"})


def _summary(values: list[float] | np.ndarray) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise protocol.ProtocolError("cannot summarize an empty or non-finite effect array")
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
    if left.size != right.size or left.size < 2:
        raise protocol.ProtocolError("correlation arrays have incompatible size")
    if float(np.std(left)) == 0.0 or float(np.std(right)) == 0.0:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def _sign_agreement(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.sign(left) == np.sign(right)))


def _bootstrap_lower(left: np.ndarray, right: np.ndarray, seed: int) -> float:
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(protocol.BOOTSTRAP_RESAMPLES):
        indices = rng.integers(0, left.size, size=left.size)
        values.append(_correlation(left[indices], right[indices]))
    return float(np.quantile(np.asarray(values, dtype=np.float64), 0.025))


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token_text in protocol.RESPONSE_TOKENS.items():
        token_ids = list(tokenizer.encode(token_text))
        if len(token_ids) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
        result[label] = int(token_ids[0])
    return result


class LayerProbe:
    def __init__(
        self,
        layer: Any,
        index: int,
        capture_layers: set[int],
        target_layer: int | None,
        position_offset: int | None,
        replacement: np.ndarray | None,
        mx: Any,
    ) -> None:
        self.layer = layer
        self.index = index
        self.capture_layers = capture_layers
        self.target_layer = target_layer
        self.position_offset = position_offset
        self.replacement = replacement
        self.mx = mx
        self.captured = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        if self.index in self.capture_layers:
            positions = [int(output.shape[1]) - offset for offset in protocol.POSITION_OFFSETS]
            if any(position < 0 or position >= int(output.shape[1]) for position in positions):
                raise protocol.ProtocolError("measurement position is outside the layer sequence")
            self.captured = self.mx.stack([output[:, position, :] for position in positions], axis=1)
        if self.target_layer == self.index and self.replacement is not None:
            if self.position_offset is None:
                raise protocol.ProtocolError("replacement position is missing")
            position = int(output.shape[1]) - self.position_offset
            replacement = self.mx.array(self.replacement.astype(np.float32), dtype=output.dtype).reshape((output.shape[0], 1, output.shape[-1]))
            output = self.mx.concatenate([output[:, :position, :], replacement, output[:, position + 1 :, :]], axis=1)
        return output


def _forward_batch(
    model: Any,
    base_layers: list[Any],
    token_batch: list[list[int]],
    response_ids: dict[str, int],
    mx: Any,
    target_layer: int | None = None,
    position_offset: int | None = None,
    replacement: np.ndarray | None = None,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    probes = [LayerProbe(layer, index, set(protocol.CANDIDATE_LAYERS), target_layer, position_offset, replacement, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array(token_batch))
        captured_arrays = [probe.captured for probe in probes if probe.captured is not None]
        if len(captured_arrays) != len(protocol.CANDIDATE_LAYERS):
            raise protocol.ProtocolError("not all candidate layers were captured")
        selected = mx.stack([logits[:, -1, response_ids["A"]], logits[:, -1, response_ids["B"]]], axis=1)
        mx.eval(selected, *captured_arrays)
        captures: dict[str, np.ndarray] = {}
        for layer in protocol.CANDIDATE_LAYERS:
            captured = probes[layer].captured
            if captured is None:
                raise protocol.ProtocolError(f"layer {layer} capture was not reached")
            vector = np.array(captured.astype(mx.float32), dtype=np.float32, copy=True)
            expected = (len(token_batch), len(protocol.POSITION_NAMES), protocol.EXPECTED_HIDDEN_WIDTH)
            if vector.shape != expected or not np.isfinite(vector).all():
                raise protocol.ProtocolError(f"invalid capture shape or value at layer {layer}: {vector.shape}")
            captures[str(layer)] = vector
        logits_np = np.array(selected.astype(mx.float32), dtype=np.float64, copy=True)
        if logits_np.shape != (len(token_batch), 2) or not np.isfinite(logits_np).all():
            raise protocol.ProtocolError("invalid selected logits")
        return captures, logits_np
    finally:
        model.language_model.model.layers = base_layers


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
        raise protocol.ProtocolError("matched replacement norm is outside tolerance")
    return replacement, relative_error


def _load_custody(panel_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    for file_path in (panel_root, qualification_root, model_root):
        protocol.assert_external(file_path, repository_root)
    panel_manifest = protocol.read_json(panel_root / "panel-manifest.json")
    qualification = protocol.read_json(qualification_root / "qualification-result.json")
    panel_receipt = protocol.read_json(panel_root / "validator-receipt.json")
    qualification_receipt = protocol.read_json(qualification_root / "validator-receipt.json")
    if not isinstance(panel_manifest, dict) or not isinstance(qualification, dict):
        raise protocol.ProtocolError("custody documents must be objects")
    if panel_manifest.get("protocol") != protocol.PROTOCOL_ID or panel_manifest.get("state_slice") != protocol.STATE_SLICE or panel_receipt.get("valid") is not True:
        raise protocol.ProtocolError("panel custody is not independently valid")
    if qualification.get("protocol") != protocol.PROTOCOL_ID or qualification.get("state_slice") != protocol.STATE_SLICE or qualification_receipt.get("valid") is not True or qualification.get("classification") != "InstrumentFeasibility":
        raise protocol.ProtocolError("qualification custody is not independently valid")
    manifest = protocol.model_manifest(model_root)
    if panel_manifest.get("model_manifest_sha256") != manifest["manifest_sha256"] or qualification.get("model_manifest_sha256") != manifest["manifest_sha256"]:
        raise protocol.ProtocolError("model custody binding mismatch")
    if not all(qualification.get("gates", {}).values()):
        raise protocol.ProtocolError("qualification gates are not all passing")
    return panel_manifest, qualification, manifest


def _load_registry(panel_root: Path) -> list[dict[str, Any]]:
    document = protocol.read_json(panel_root / "concept-registry.json")
    if not isinstance(document, dict) or document.get("protocol") != protocol.PROTOCOL_ID or document.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("panel registry binding is invalid")
    families = document.get("families")
    if not isinstance(families, list) or len(families) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("panel family census is invalid")
    return families


def _token_cache(registry: list[dict[str, Any]], tokenizer: Any) -> dict[str, dict[str, list[int]]]:
    cache: dict[str, dict[str, list[int]]] = {}
    for family in registry:
        family_cache: dict[str, list[int]] = {}
        for wrapper in protocol.WRAPPER_NAMES:
            for condition in ("ordinary", "counterfactual"):
                key = f"{wrapper}_{condition}_prompt"
                token_ids = list(tokenizer.encode(family[key]))
                if len(token_ids) != protocol.FIXED_TOKEN_LENGTH:
                    raise protocol.ProtocolError(f"fixed tokenizer length mismatch: {family['family_id']}:{key}")
                family_cache[key] = token_ids
        cache[family["family_id"]] = family_cache
    return cache


def _capture_clean(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    tokens: dict[str, dict[str, list[int]]],
    response_ids: dict[str, int],
    wrapper: str,
    mx: Any,
) -> dict[str, dict[str, Any]]:
    # MLX Qwen3.6 has batch-size-sensitive numerical behavior at the selected
    # logits. Clean baselines must therefore use the same fixed batch size as
    # intervention chunks; otherwise exact-copy would falsely appear causal.
    family_batch_size = max(1, INTERVENTION_BATCH_SIZE // 2)
    capture_parts: dict[str, list[np.ndarray]] = {str(layer): [] for layer in protocol.CANDIDATE_LAYERS}
    logit_parts: list[np.ndarray] = []
    for start in range(0, len(families), family_batch_size):
        family_batch = families[start : start + family_batch_size]
        token_batch: list[list[int]] = []
        for family in family_batch:
            token_batch.extend([tokens[family["family_id"]][f"{wrapper}_ordinary_prompt"], tokens[family["family_id"]][f"{wrapper}_counterfactual_prompt"]])
        captures, logits = _forward_batch(model, base_layers, token_batch, response_ids, mx)
        for layer in protocol.CANDIDATE_LAYERS:
            capture_parts[str(layer)].append(captures[str(layer)])
        logit_parts.append(logits)
    captures = {layer: np.concatenate(parts, axis=0) for layer, parts in capture_parts.items()}
    logits = np.concatenate(logit_parts, axis=0)
    clean: dict[str, dict[str, Any]] = {}
    for family_index, family in enumerate(families):
        ordinary_index = 2 * family_index
        counterfactual_index = ordinary_index + 1
        clean[family["family_id"]] = {
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
    return clean


def _run_replacements(
    model: Any,
    base_layers: list[Any],
    token_rows: list[list[int]],
    replacement_rows: list[np.ndarray],
    response_ids: dict[str, int],
    target_layer: int,
    position_offset: int,
    mx: Any,
) -> np.ndarray:
    result: list[np.ndarray] = []
    for start in range(0, len(token_rows), INTERVENTION_BATCH_SIZE):
        batch_tokens = token_rows[start : start + INTERVENTION_BATCH_SIZE]
        batch_replacements = np.asarray(replacement_rows[start : start + INTERVENTION_BATCH_SIZE], dtype=np.float32)
        _, logits = _forward_batch(model, base_layers, batch_tokens, response_ids, mx, target_layer, position_offset, batch_replacements)
        result.append(logits)
    if not result:
        raise protocol.ProtocolError("replacement batch is empty")
    return np.concatenate(result, axis=0)


def _donor(family: dict[str, Any], families: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = sorted(
        (other for other in families if other["family_id"] != family["family_id"] and other["gutenberg_id"] != family["gutenberg_id"]),
        key=lambda other: other["family_id"],
    )
    if not candidates:
        raise protocol.ProtocolError("no document-disjoint donor exists")
    return candidates[0]


def _measure_cell(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    clean: dict[str, dict[str, Any]],
    tokens: dict[str, dict[str, list[int]]],
    wrapper: str,
    layer: int,
    position_index: int,
    response_ids: dict[str, int],
    mx: Any,
) -> tuple[dict[str, list[float]], float, int, float]:
    means = {
        "ordinary": np.mean([clean[family["family_id"]]["vectors"][str(layer)]["ordinary"][position_index] for family in families], axis=0),
        "counterfactual": np.mean([clean[family["family_id"]]["vectors"][str(layer)]["counterfactual"][position_index] for family in families], axis=0),
    }
    condition_names = ("activation_repeat_1", "activation_repeat_2", "exact_copy", "shuffled", "constant", "matched")
    token_rows: list[list[int]] = []
    replacement_rows: list[np.ndarray] = []
    row_descriptors: list[tuple[str, str]] = []
    matched_norm_max = 0.0
    matched_violations = 0
    for family in families:
        family_id = family["family_id"]
        donor = _donor(family, families)
        own = clean[family_id]["vectors"][str(layer)]
        donor_vectors = clean[donor["family_id"]]["vectors"][str(layer)]
        matched_cf, cf_error = _norm_match(donor_vectors["counterfactual"][position_index], own["ordinary"][position_index])
        matched_ord, ord_error = _norm_match(donor_vectors["ordinary"][position_index], own["counterfactual"][position_index])
        matched_norm_max = max(matched_norm_max, cf_error, ord_error)
        if cf_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE or ord_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
            matched_violations += 1
        replacements = {
            "activation_repeat_1": (own["counterfactual"][position_index], own["ordinary"][position_index]),
            "activation_repeat_2": (own["counterfactual"][position_index], own["ordinary"][position_index]),
            "exact_copy": (own["ordinary"][position_index], own["counterfactual"][position_index]),
            "shuffled": (donor_vectors["counterfactual"][position_index], donor_vectors["ordinary"][position_index]),
            "constant": (means["counterfactual"], means["ordinary"]),
            "matched": (matched_cf, matched_ord),
        }
        for condition in condition_names:
            ordinary_key = f"{wrapper}_ordinary_prompt"
            counterfactual_key = f"{wrapper}_counterfactual_prompt"
            token_rows.extend([tokens[family_id][ordinary_key], tokens[family_id][counterfactual_key]])
            replacement_rows.extend([replacements[condition][0], replacements[condition][1]])
            row_descriptors.extend([(family_id, condition), (family_id, condition)])
    intervened = _run_replacements(model, base_layers, token_rows, replacement_rows, response_ids, layer, protocol.POSITION_BY_NAME[protocol.POSITION_NAMES[position_index]], mx)
    effects: dict[str, list[float]] = {name: [] for name in condition_names}
    for row_index in range(0, len(row_descriptors), 2):
        family_id, condition = row_descriptors[row_index]
        if row_descriptors[row_index + 1] != (family_id, condition):
            raise protocol.ProtocolError("intervention row pairing changed")
        clean_family = clean[family_id]
        effects[condition].append(_effect(clean_family["ordinary_logits"], clean_family["counterfactual_logits"], intervened[row_index], intervened[row_index + 1]))
    repeat_delta = max(abs(left - right) for left, right in zip(effects["activation_repeat_1"], effects["activation_repeat_2"]))
    return effects, matched_norm_max, matched_violations, repeat_delta


def _pairwise_metrics(activation_by_wrapper: dict[str, list[float]], layer: int, position_index: int) -> dict[str, Any]:
    pairwise: list[dict[str, Any]] = []
    for pair_index, (left_name, right_name) in enumerate(itertools.combinations(protocol.WRAPPER_NAMES, 2)):
        left = np.asarray(activation_by_wrapper[left_name], dtype=np.float64)
        right = np.asarray(activation_by_wrapper[right_name], dtype=np.float64)
        pairwise.append({
            "left_wrapper": left_name,
            "right_wrapper": right_name,
            "correlation": _correlation(left, right),
            "sign_agreement": _sign_agreement(left, right),
            "bootstrap_correlation_lower_95": _bootstrap_lower(left, right, protocol.BOOTSTRAP_SEED + layer * 10 + position_index * 100 + pair_index),
        })
    return {
        "pairwise": pairwise,
        "wrapper_correlation": min(item["correlation"] for item in pairwise),
        "wrapper_sign_agreement": min(item["sign_agreement"] for item in pairwise),
        "bootstrap_correlation_lower_95": min(item["bootstrap_correlation_lower_95"] for item in pairwise),
    }


def _measure_split(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    tokens: dict[str, dict[str, list[int]]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    activation: dict[str, dict[str, dict[str, list[float]]]] = {
        wrapper: {str(layer): {position: [] for position in protocol.POSITION_NAMES} for layer in protocol.CANDIDATE_LAYERS}
        for wrapper in protocol.WRAPPER_NAMES
    }
    text_only: dict[str, dict[str, dict[str, list[float]]]] = {
        wrapper: {str(layer): {position: [] for position in protocol.POSITION_NAMES} for layer in protocol.CANDIDATE_LAYERS}
        for wrapper in protocol.WRAPPER_NAMES
    }
    controls: dict[str, dict[str, dict[str, dict[str, list[float]]]]] = {
        wrapper: {
            str(layer): {position: {name: [] for name in ("exact_copy", "shuffled", "constant", "matched")} for position in protocol.POSITION_NAMES}
            for layer in protocol.CANDIDATE_LAYERS
        }
        for wrapper in protocol.WRAPPER_NAMES
    }
    cell_norms: dict[tuple[int, str], float] = {}
    cell_violations: dict[tuple[int, str], int] = {}
    cell_repeats: dict[tuple[int, str], float] = {}
    for wrapper in protocol.WRAPPER_NAMES:
        clean = _capture_clean(model, base_layers, families, tokens, response_ids, wrapper, mx)
        for layer in protocol.CANDIDATE_LAYERS:
            for position_index, position_name in enumerate(protocol.POSITION_NAMES):
                layer_key = str(layer)
                text_only[wrapper][layer_key][position_name] = [
                    _text_only_effect(clean[family["family_id"]]["ordinary_logits"], clean[family["family_id"]]["counterfactual_logits"])
                    for family in families
                ]
                effects, norm_max, violations, repeat_delta = _measure_cell(model, base_layers, families, clean, tokens, wrapper, layer, position_index, response_ids, mx)
                activation[wrapper][layer_key][position_name] = effects["activation_repeat_1"]
                for control_name in ("exact_copy", "shuffled", "constant", "matched"):
                    controls[wrapper][layer_key][position_name][control_name] = effects[control_name]
                key = (layer, position_name)
                cell_norms[key] = max(cell_norms.get(key, 0.0), norm_max)
                cell_violations[key] = cell_violations.get(key, 0) + violations
                cell_repeats[key] = max(cell_repeats.get(key, 0.0), repeat_delta)

    cells: dict[str, Any] = {}
    for layer in protocol.CANDIDATE_LAYERS:
        for position_name in protocol.POSITION_NAMES:
            layer_key = str(layer)
            cell_key = f"{layer_key}:{position_name}"
            activation_cell = {wrapper: activation[wrapper][layer_key][position_name] for wrapper in protocol.WRAPPER_NAMES}
            reliability = _pairwise_metrics(activation_cell, layer, list(protocol.POSITION_NAMES).index(position_name))
            reliability.update({
                "wrapper_alpha_effect_std": float(np.std(np.asarray(activation_cell[protocol.WRAPPER_NAMES[0]], dtype=np.float64))),
                "wrapper_beta_effect_std": float(np.std(np.asarray(activation_cell[protocol.WRAPPER_NAMES[1]], dtype=np.float64))),
                "wrapper_gamma_effect_std": float(np.std(np.asarray(activation_cell[protocol.WRAPPER_NAMES[2]], dtype=np.float64))),
            })
            reliability["target_effect_std_min"] = min(
                reliability["wrapper_alpha_effect_std"], reliability["wrapper_beta_effect_std"], reliability["wrapper_gamma_effect_std"]
            )
            control_summaries: dict[str, Any] = {}
            for control_name in ("exact_copy", "shuffled", "constant", "matched"):
                values = np.concatenate([controls[wrapper][layer_key][position_name][control_name] for wrapper in protocol.WRAPPER_NAMES])
                control_summaries[control_name] = _summary(values)
            gates = {
                "target_effect_non_degenerate": reliability["target_effect_std_min"] >= protocol.MIN_TARGET_EFFECT_STD,
                "wrapper_correlation": reliability["wrapper_correlation"] >= protocol.MIN_TARGET_CORRELATION,
                "wrapper_sign_agreement": reliability["wrapper_sign_agreement"] >= protocol.MIN_TARGET_SIGN_AGREEMENT,
                "bootstrap_correlation": reliability["bootstrap_correlation_lower_95"] >= protocol.MIN_BOOTSTRAP_CORRELATION_LOWER,
                "exact_copy_control": control_summaries["exact_copy"]["mean_abs"] <= protocol.MAX_EXACT_COPY_ABS_EFFECT,
                "shuffled_control": abs(control_summaries["shuffled"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
                "constant_control": abs(control_summaries["constant"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
                "matched_control": abs(control_summaries["matched"]["mean"]) <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
                "repeatability": cell_repeats[(layer, position_name)] <= protocol.MAX_REPEAT_ABS_EFFECT_DELTA,
            }
            cells[cell_key] = {
                "layer": layer,
                "position": position_name,
                "position_offset": protocol.POSITION_BY_NAME[position_name],
                "family_count": len(families),
                "document_count": len({int(family["gutenberg_id"]) for family in families}),
                "activation_only": {wrapper: _summary(activation_cell[wrapper]) for wrapper in protocol.WRAPPER_NAMES},
                "text_only": {wrapper: _summary(text_only[wrapper][layer_key][position_name]) for wrapper in protocol.WRAPPER_NAMES},
                "controls": control_summaries,
                "matched_norm_relative_error_max": cell_norms[(layer, position_name)],
                "matched_donor_violations": cell_violations[(layer, position_name)],
                "repeat_max_abs_effect_delta": cell_repeats[(layer, position_name)],
                "reliability": {**reliability, "gates": gates},
            }
    return {
        "family_count": len(families),
        "document_count": len({int(family["gutenberg_id"]) for family in families}),
        "cell_summaries": cells,
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_names": list(protocol.POSITION_NAMES),
    }


def run(panel_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path) -> Path:
    panel_root = panel_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite measurement root: {output_root}")
    panel_manifest, qualification, model_manifest = _load_custody(panel_root, qualification_root, model_root, repository_root)
    registry = _load_registry(panel_root)
    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("model layer count differs from qualified custody")
    response_ids = _strict_response_ids(tokenizer)
    tokens = _token_cache(registry, tokenizer)
    by_split = {split: [family for family in registry if family["split"] == split] for split in protocol.SPLITS}
    measured_splits = ("fit", "tune")
    split_results = {
        split: _measure_split(model, base_layers, by_split[split], tokens, response_ids, mx)
        for split in measured_splits
    }
    tune_cells = split_results["tune"]["cell_summaries"]
    ordered_cells = [(layer, position) for layer in protocol.CANDIDATE_LAYERS for position in protocol.POSITION_NAMES]
    passing_targets = [
        {"layer": layer, "position": position}
        for layer, position in ordered_cells
        if all(tune_cells[f"{layer}:{position}"]["reliability"]["gates"].values())
    ]
    selected_target = passing_targets[0] if passing_targets else None
    lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "selection_rule": "lowest_numeric_layer_then_final_before_penultimate_passing_all_tune_gates",
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_names": list(protocol.POSITION_NAMES),
        "position_offsets": list(protocol.POSITION_OFFSETS),
        "position_rule": protocol.FIXED_POSITION_RULE,
        "selected_target": selected_target,
        "passing_targets": passing_targets,
        "measured_splits": list(measured_splits),
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "assessment_effects_locked": True,
        "prediction_lock_before_assessment": True,
        "assessment_opened": False,
    }
    lock["configuration_lock_sha256"] = _configuration_lock_digest(lock)
    classification = "MeasurementInvarianceNoCandidate" if selected_target is None else "ReviewRequired"
    claim_ceiling = CLAIM_CEILING_NO_CANDIDATE if selected_target is None else CLAIM_CEILING_REVIEW
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": classification,
        "claim_ceiling": claim_ceiling,
        "aggregate_only_retention": True,
        "assessment_opened": False,
        "assessment_effects_present": False,
        "prediction_lock_before_assessment": True,
        "review_required_before_assessment": selected_target is not None,
        "review_verified": False,
        "panel_manifest_sha256": lock["panel_manifest_sha256"],
        "qualification_result_sha256": lock["qualification_result_sha256"],
        "model_manifest_sha256": lock["model_manifest_sha256"],
        "configuration_lock_sha256": lock["configuration_lock_sha256"],
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "position_names": list(protocol.POSITION_NAMES),
        "position_offsets": list(protocol.POSITION_OFFSETS),
        "position_rule": protocol.FIXED_POSITION_RULE,
        "measured_splits": list(measured_splits),
        "selection_rule": lock["selection_rule"],
        "passing_targets": passing_targets,
        "selected_target": selected_target,
        "splits": split_results,
        "tune_passed": bool(passing_targets),
        "source_sha256": {
            "protocol": protocol.sha256_file(Path(protocol.__file__).resolve()),
            "runner": protocol.sha256_file(Path(__file__).resolve()),
        },
    }
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        protocol.write_json(staging / "configuration-lock.json", lock)
        protocol.write_json(staging / "invariance-result.json", result)
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
    parser.add_argument("--model", type=Path, default=Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = run(args.panel_root, args.qualification_root, args.model, args.output_root, args.repository_root.resolve())
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    result = protocol.read_json(root / "invariance-result.json")
    print(json.dumps({"measurement_root": str(root), "classification": result["classification"], "selected_target": result["selected_target"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
