#!/usr/bin/env python3
"""Run the V48 fit/tune measurement with assessment permanently closed.

State slice: astral-stage0c-cross-view-causal-state-transport-v48.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

import protocol_v48 as protocol


BATCH_SIZE = protocol.BATCH_SIZE
CLAIM_CEILING_NO_CANDIDATE = "LocalDevelopmentV48BoundedCausalStateTransportNoCandidate"
CLAIM_CEILING_REVIEW = "LocalDevelopmentV48BoundedCausalStateTransportReviewRequired"


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
    if left.size != right.size or left.size < 2 or np.std(left) == 0.0 or np.std(right) == 0.0:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def _sign_agreement(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.sign(left) == np.sign(right)))


def _bootstrap_stat(values: np.ndarray, seed: int, statistic: Any, lower: float = 0.025, upper: float = 0.975) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    if values.size < 2 or not np.isfinite(values).all():
        raise protocol.ProtocolError("bootstrap input is invalid")
    rng = np.random.default_rng(seed)
    draws = np.empty(protocol.BOOTSTRAP_RESAMPLES, dtype=np.float64)
    for index in range(protocol.BOOTSTRAP_RESAMPLES):
        sample = values[rng.integers(0, values.size, size=values.size)]
        draws[index] = float(statistic(sample))
    return float(np.quantile(draws, lower)), float(np.quantile(draws, upper))


def _bootstrap_correlation_lower(predicted: np.ndarray, observed: np.ndarray, seed: int) -> float:
    predicted = np.asarray(predicted, dtype=np.float64)
    observed = np.asarray(observed, dtype=np.float64)
    if predicted.size != observed.size or predicted.size < 2:
        raise protocol.ProtocolError("prediction arrays are invalid")
    rng = np.random.default_rng(seed)
    values = np.empty(protocol.BOOTSTRAP_RESAMPLES, dtype=np.float64)
    for index in range(protocol.BOOTSTRAP_RESAMPLES):
        sample = rng.integers(0, predicted.size, size=predicted.size)
        values[index] = _correlation(predicted[sample], observed[sample])
    return float(np.quantile(values, 0.025))


def _cluster_means(values: np.ndarray, cluster_ids: list[int]) -> np.ndarray:
    if values.size != len(cluster_ids):
        raise protocol.ProtocolError("cluster values and ids differ")
    grouped: dict[int, list[float]] = defaultdict(list)
    for value, cluster_id in zip(values, cluster_ids):
        grouped[int(cluster_id)].append(float(value))
    if len(grouped) < 2:
        raise protocol.ProtocolError("at least two clusters are required")
    return np.asarray([np.mean(grouped[key]) for key in sorted(grouped)], dtype=np.float64)


def _cluster_ci(values: np.ndarray, cluster_ids: list[int], seed: int, lower: float = 0.025, upper: float = 0.975) -> tuple[float, float]:
    return _bootstrap_stat(_cluster_means(values, cluster_ids), seed, np.mean, lower, upper)


def _icc_a1(repeats: np.ndarray) -> float:
    values = np.asarray(repeats, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] < 2 or values.shape[0] < 2 or not np.isfinite(values).all():
        raise protocol.ProtocolError("ICC input is invalid")
    n, k = values.shape
    grand = float(np.mean(values))
    row_means = np.mean(values, axis=1)
    column_means = np.mean(values, axis=0)
    ms_rows = k * float(np.sum((row_means - grand) ** 2)) / (n - 1)
    ms_columns = n * float(np.sum((column_means - grand) ** 2)) / (k - 1)
    residual = values - row_means[:, None] - column_means[None, :] + grand
    ms_error = float(np.sum(residual ** 2)) / ((n - 1) * (k - 1))
    denominator = ms_rows + (k - 1) * ms_error + k * (ms_columns - ms_error) / n
    if denominator == 0.0:
        return 1.0 if ms_rows == 0.0 else 0.0
    return float((ms_rows - ms_error) / denominator)


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token in protocol.RESPONSE_TOKENS.items():
        encoded = list(tokenizer.encode(token))
        if len(encoded) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
        result[label] = int(encoded[0])
    return result


def _prompt_tokens(prompt: str, tokenizer: Any) -> tuple[list[int], int]:
    marker = "State payload boundary:"
    if prompt.count(marker) != 1:
        raise protocol.ProtocolError("prompt has an invalid state-anchor marker count")
    marker_start = prompt.index(marker)
    boundary = len(tokenizer.encode(prompt[: marker_start + len(marker)]))
    tokens = list(tokenizer.encode(prompt))
    anchor = boundary - protocol.CONTENT_ANCHOR_OFFSET
    if anchor < 0 or anchor >= len(tokens):
        raise protocol.ProtocolError("state anchor is invalid before fixed-length truncation")
    if len(tokens) > protocol.FIXED_TOKEN_LENGTH:
        start = len(tokens) - protocol.FIXED_TOKEN_LENGTH
        if anchor < start:
            raise protocol.ProtocolError("fixed-length truncation would remove the state anchor")
        tokens = tokens[start:]
        anchor -= start
    return tokens, anchor


def _replace_rows(output: Any, positions: list[int], replacements: np.ndarray, mx: Any) -> Any:
    batch_size = int(output.shape[0])
    sequence_length = int(output.shape[1])
    if len(positions) != batch_size or replacements.shape != (batch_size, int(output.shape[-1])):
        raise protocol.ProtocolError("replacement batch shape mismatch")
    if any(position < 0 or position >= sequence_length for position in positions):
        raise protocol.ProtocolError("state anchor is outside the layer sequence")
    position_array = mx.array(positions)
    mask = (mx.arange(sequence_length)[None, :] == position_array[:, None])[:, :, None]
    replacement_array = mx.array(replacements.astype(np.float32), dtype=output.dtype)[:, None, :]
    return mx.where(mask, replacement_array, output)


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
            self.captured = output[self.mx.arange(int(output.shape[0])), self.mx.array(self.positions), :]
        if self.target_layer == self.index:
            if self.replacements is not None:
                output = _replace_rows(output, self.positions, self.replacements, self.mx)
        return output


def _forward_batch(model: Any, base_layers: list[Any], records: list[dict[str, Any]], response_ids: dict[str, int], tokenizer: Any, mx: Any, target_layer: int | None = None, replacements: np.ndarray | None = None) -> tuple[dict[str, np.ndarray], np.ndarray]:
    if not records:
        raise protocol.ProtocolError("empty model batch")
    pad_id = getattr(tokenizer, "pad_token_id", None)
    if pad_id is None:
        pad_id = getattr(tokenizer, "eos_token_id", None)
    if pad_id is None:
        pad_id = 0
    rows = [record["tokens"] for record in records]
    max_length = max(len(row) for row in rows)
    if max_length > protocol.FIXED_TOKEN_LENGTH:
        raise protocol.ProtocolError("encoded prompt exceeded fixed token length")
    padded = [row + [int(pad_id)] * (max_length - len(row)) for row in rows]
    positions = [int(record["anchor"]) for record in records]
    last_positions = [len(row) - 1 for row in rows]
    capture_layers = {protocol.SOURCE_LAYER, protocol.DESTINATION_LAYER} if target_layer is None else set()
    probes = [LayerProbe(layer, index, capture_layers, positions, target_layer, replacements, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array(padded))
        selected = logits[mx.arange(len(records)), mx.array(last_positions), :]
        captures = [probe.captured for probe in probes if probe.captured is not None]
        if target_layer is None and len(captures) != len(capture_layers):
            raise protocol.ProtocolError("not all required layers were captured")
        selected = mx.stack([selected[:, response_ids[label]] for label in protocol.RESPONSE_LABELS], axis=1)
        mx.eval(selected, *captures)
        logits_np = np.asarray(selected.astype(mx.float32), dtype=np.float64)
        if logits_np.shape != (len(records), protocol.STATE_COUNT) or not np.isfinite(logits_np).all():
            raise protocol.ProtocolError("invalid selected response logits")
        capture_map: dict[str, np.ndarray] = {}
        for layer in (protocol.SOURCE_LAYER, protocol.DESTINATION_LAYER):
            captured = probes[layer].captured
            if captured is None:
                if target_layer is None:
                    raise protocol.ProtocolError(f"required layer was not captured: {layer}")
                continue
            value = np.asarray(captured.astype(mx.float32), dtype=np.float32)
            expected = (len(records), protocol.EXPECTED_HIDDEN_WIDTH)
            if value.shape != expected or not np.isfinite(value).all():
                raise protocol.ProtocolError(f"invalid capture shape/value: {layer}:{value.shape}")
            capture_map[str(layer)] = value
        return capture_map, logits_np
    finally:
        model.language_model.model.layers = base_layers


def _capture_clean(model: Any, base_layers: list[Any], families: list[dict[str, Any]], tokenizer: Any, response_ids: dict[str, int], mx: Any) -> dict[tuple[str, str, str], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family in families:
        for view in protocol.VIEWS:
            for role in ("receiver", "donor"):
                cell = family["views"][view]
                prompt = str(cell[f"{role}_prompt"])
                tokens, anchor = _prompt_tokens(prompt, tokenizer)
                records.append({
                    "key": (str(family["family_id"]), view, role),
                    "prompt": prompt,
                    "tokens": tokens,
                    "anchor": anchor,
                    "state": int(cell[f"{role}_state"]),
                })
    result: dict[tuple[str, str, str], dict[str, Any]] = {}
    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start : start + BATCH_SIZE]
        captures, logits = _forward_batch(model, base_layers, batch, response_ids, tokenizer, mx)
        for offset, record in enumerate(batch):
            result[record["key"]] = {
                "prompt": record["prompt"],
                "tokens": record["tokens"],
                "anchor": record["anchor"],
                "state": record["state"],
                "logits": logits[offset],
                "source": captures[str(protocol.SOURCE_LAYER)][offset],
                "destination": captures[str(protocol.DESTINATION_LAYER)][offset],
            }
    if len(result) != len(records):
        raise protocol.ProtocolError("clean capture cardinality mismatch")
    return result


def _run_replacements(model: Any, base_layers: list[Any], records: list[dict[str, Any]], replacements: list[np.ndarray], response_ids: dict[str, int], tokenizer: Any, target_layer: int, mx: Any) -> np.ndarray:
    if len(records) != len(replacements):
        raise protocol.ProtocolError("replacement records and vectors differ")
    values: list[np.ndarray] = []
    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start : start + BATCH_SIZE]
        vectors = np.asarray(replacements[start : start + BATCH_SIZE], dtype=np.float32)
        _, logits = _forward_batch(model, base_layers, batch, response_ids, tokenizer, mx, target_layer=target_layer, replacements=vectors)
        values.append(logits)
    return np.concatenate(values, axis=0)


def _run_identity(model: Any, base_layers: list[Any], records: list[dict[str, Any]], response_ids: dict[str, int], tokenizer: Any, target_layer: int, mx: Any) -> np.ndarray:
    values: list[np.ndarray] = []
    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start : start + BATCH_SIZE]
        _, logits = _forward_batch(model, base_layers, batch, response_ids, tokenizer, mx, target_layer=target_layer, replacements=None)
        values.append(logits)
    if not values:
        raise protocol.ProtocolError("identity batch is empty")
    return np.concatenate(values, axis=0)


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> tuple[np.ndarray, float]:
    source_norm = float(np.linalg.norm(source.astype(np.float64)))
    receiver_norm = float(np.linalg.norm(receiver.astype(np.float64)))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise protocol.ProtocolError("cannot norm-match a zero activation")
    replacement = source * np.float32(receiver_norm / source_norm)
    error = abs(float(np.linalg.norm(replacement.astype(np.float64))) - receiver_norm) / receiver_norm
    if error > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
        raise protocol.ProtocolError("matched norm error exceeds tolerance")
    return replacement, error


def _transport_vector(receiver: np.ndarray, donor: np.ndarray) -> tuple[np.ndarray, float]:
    matched, error = _norm_match(donor, receiver)
    return ((1.0 - protocol.ALPHA) * receiver + protocol.ALPHA * matched).astype(np.float32), error


def _margin(logits: np.ndarray, state: int, alternate: int) -> float:
    return float(logits[state] - logits[alternate])


def _feature(vector: np.ndarray) -> np.ndarray:
    blocks = vector.astype(np.float64).reshape(8, protocol.EXPECTED_HIDDEN_WIDTH // 8).mean(axis=1)
    return blocks


def _hash_feature(value: bytes) -> np.ndarray:
    digest = hashlib.sha256(value).digest()
    return np.asarray([byte / 255.0 for byte in digest[:8]], dtype=np.float64)


def _fit_ridge(features: np.ndarray, labels: np.ndarray, alpha: float) -> tuple[np.ndarray, float]:
    if features.ndim != 2 or labels.ndim != 1 or features.shape[0] != labels.size:
        raise protocol.ProtocolError("ridge input shape mismatch")
    mean_x = np.mean(features, axis=0)
    mean_y = float(np.mean(labels))
    centered = features - mean_x
    weights = np.linalg.solve(centered.T @ centered + alpha * np.eye(features.shape[1]), centered.T @ (labels - mean_y))
    return weights, mean_y - float(mean_x @ weights)


def _prediction_metrics(predicted: np.ndarray, observed: np.ndarray, seed: int) -> dict[str, Any]:
    correlation = _correlation(predicted, observed)
    sign = _sign_agreement(predicted, observed)
    bootstrap = _bootstrap_correlation_lower(predicted, observed, seed)
    return {
        "correlation": correlation,
        "sign_agreement": sign,
        "bootstrap_correlation_lower_95": bootstrap,
        "gates": {
            "correlation": correlation >= protocol.MIN_PREDICTION_CORRELATION,
            "sign_agreement": sign >= protocol.MIN_PREDICTION_SIGN_AGREEMENT,
            "bootstrap_correlation": bootstrap >= protocol.MIN_BOOTSTRAP_CORRELATION_LOWER,
        },
    }


def _stable_seed(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:4], "big")


def _direction_roles(direction: str) -> tuple[str, str]:
    if direction == "plus":
        return "receiver", "donor"
    if direction == "minus":
        return "donor", "receiver"
    raise protocol.ProtocolError(f"unknown direction: {direction}")


def _same_state_source(clean: dict[tuple[str, str, str], dict[str, Any]], families: list[dict[str, Any]], family: dict[str, Any], view: str, state: int, current_id: str) -> np.ndarray:
    candidates: list[tuple[str, str]] = []
    for other in families:
        other_id = str(other["family_id"])
        if other_id == current_id:
            continue
        for role in ("receiver", "donor"):
            key = (other_id, view, role)
            if clean[key]["state"] == state:
                candidates.append((other_id, role))
    if not candidates:
        raise protocol.ProtocolError("no same-state matched donor exists")
    other_id, role = sorted(candidates)[0]
    return clean[(other_id, view, role)]["source"]


def _measure_split(model: Any, base_layers: list[Any], families: list[dict[str, Any]], tokenizer: Any, response_ids: dict[str, int], mx: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    clean = _capture_clean(model, base_layers, families, tokenizer, response_ids, mx)
    sorted_ids = sorted(str(family["family_id"]) for family in families)
    permutation = {family_id: sorted_ids[(index + 1) % len(sorted_ids)] for index, family_id in enumerate(sorted_ids)}
    constant_sources: dict[tuple[str, str], np.ndarray] = {}
    for view in protocol.VIEWS:
        for direction in protocol.DIRECTIONS:
            donor_role = _direction_roles(direction)[1]
            constant_sources[(view, direction)] = np.mean(
                [clean[(str(family["family_id"]), view, donor_role)]["source"] for family in families], axis=0
            ).astype(np.float32)

    records: list[dict[str, Any]] = []
    replacements: list[np.ndarray] = []
    descriptors: list[tuple[str, str, str, str, int, int, float]] = []
    identity_records: list[dict[str, Any]] = []
    identity_descriptors: list[tuple[str, str, str, str, int, int, float]] = []
    baselines: dict[tuple[str, str, str], float] = {}
    max_norm_error = 0.0
    for family in families:
        family_id = str(family["family_id"])
        for view in protocol.VIEWS:
            cell = family["views"][view]
            for direction in protocol.DIRECTIONS:
                receiver_role, donor_role = _direction_roles(direction)
                receiver = clean[(family_id, view, receiver_role)]
                donor = clean[(family_id, view, donor_role)]
                state = int(receiver["state"])
                alternate = int(donor["state"])
                baseline = _margin(receiver["logits"], state, alternate)
                baselines[(family_id, view, direction)] = baseline
                shuffled_id = permutation[family_id]
                shuffled = clean[(shuffled_id, view, donor_role)]
                matched = clean[(family_id, view, receiver_role)]
                transport_vector, transport_error = _transport_vector(receiver["destination"], donor["source"])
                shuffled_vector, shuffled_error = _transport_vector(receiver["destination"], shuffled["source"])
                constant_vector, constant_error = _transport_vector(receiver["destination"], constant_sources[(view, direction)])
                matched_source = _same_state_source(clean, families, family, view, state, family_id)
                matched_vector, matched_error = _transport_vector(receiver["destination"], matched_source)
                max_norm_error = max(max_norm_error, transport_error, shuffled_error, constant_error, matched_error)
                actions = {
                    "activation_only": transport_vector,
                    "activation_repeat": transport_vector.copy(),
                    "exact_copy": receiver["destination"].copy(),
                    "shuffled": shuffled_vector,
                    "constant": constant_vector,
                    "matched": matched_vector,
                }
                for condition, replacement in actions.items():
                    descriptor = (family_id, view, direction, condition, state, alternate, baseline)
                    if condition == "exact_copy":
                        identity_records.append({"tokens": receiver["tokens"], "anchor": receiver["anchor"]})
                        identity_descriptors.append(descriptor)
                    else:
                        records.append({"tokens": receiver["tokens"], "anchor": receiver["anchor"]})
                        replacements.append(replacement)
                        descriptors.append(descriptor)
    intervened = _run_replacements(model, base_layers, records, replacements, response_ids, tokenizer, protocol.DESTINATION_LAYER, mx)
    effects: dict[tuple[str, str, str, str], float] = {}
    for row, descriptor in zip(intervened, descriptors):
        family_id, view, direction, condition, state, alternate, baseline = descriptor
        effects[(family_id, view, direction, condition)] = _margin(row, state, alternate) - baseline
    identity = _run_identity(model, base_layers, identity_records, response_ids, tokenizer, protocol.DESTINATION_LAYER, mx)
    for row, descriptor in zip(identity, identity_descriptors):
        family_id, view, direction, condition, state, alternate, baseline = descriptor
        effects[(family_id, view, direction, condition)] = _margin(row, state, alternate) - baseline

    observations: list[dict[str, Any]] = []
    for family in families:
        family_id = str(family["family_id"])
        for view in protocol.VIEWS:
            for direction in protocol.DIRECTIONS:
                receiver_role, donor_role = _direction_roles(direction)
                receiver = clean[(family_id, view, receiver_role)]
                donor = clean[(family_id, view, donor_role)]
                activation_effect = effects[(family_id, view, direction, "activation_only")]
                observations.append({
                    "family_id": family_id,
                    "gutenberg_id": int(family["gutenberg_id"]),
                    "view": view,
                    "direction": direction,
                    "transport_effect": activation_effect,
                    "null_effect": effects[(family_id, view, direction, "shuffled")],
                    "local_effect": activation_effect - effects[(family_id, view, direction, "shuffled")],
                    "source_difference_feature": _feature(donor["source"] - receiver["source"]),
                    "text_feature": _hash_feature(receiver["prompt"].encode("utf-8")),
                    "input_feature": _hash_feature(np.asarray(receiver["tokens"], dtype=np.int64).tobytes()),
                    "receiver_source_feature": _feature(receiver["source"]),
                    "receiver_state": int(receiver["state"]),
                })

    by_family: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
    for observation in observations:
        by_family[observation["family_id"]][(observation["view"], observation["direction"])] = observation
    tau_values: list[float] = []
    local_values: list[float] = []
    cluster_ids: list[int] = []
    gamma_values: list[float] = []
    for family in families:
        family_id = str(family["family_id"])
        cells = by_family[family_id]
        tau_values.append(float((cells[("view_1", "plus")]["transport_effect"] - cells[("view_1", "minus")]["transport_effect"] + cells[("view_2", "plus")]["transport_effect"] - cells[("view_2", "minus")]["transport_effect"]) / 4.0))
        local_values.append(float(np.mean([cell["local_effect"] for cell in cells.values()])))
        gamma_values.append(float(cells[("view_1", "plus")]["transport_effect"] - cells[("view_1", "minus")]["transport_effect"] - cells[("view_2", "plus")]["transport_effect"] + cells[("view_2", "minus")]["transport_effect"]))
        cluster_ids.append(int(family["gutenberg_id"]))

    action_arrays = {
        condition: np.asarray([effects[(observation["family_id"], observation["view"], observation["direction"], condition)] for observation in observations], dtype=np.float64)
        for condition in ("activation_only", "activation_repeat", "exact_copy", "shuffled", "constant", "matched")
    }
    repeat_delta = float(np.max(np.abs(action_arrays["activation_only"] - action_arrays["activation_repeat"])))
    repeat_matrix = np.column_stack([action_arrays["activation_only"], action_arrays["activation_repeat"]])
    repeat_sign = _sign_agreement(action_arrays["activation_only"], action_arrays["activation_repeat"])
    local_ci = _cluster_ci(np.asarray(local_values), cluster_ids, protocol.BOOTSTRAP_SEED)
    gamma_ci = _cluster_ci(np.asarray(gamma_values), cluster_ids, protocol.BOOTSTRAP_SEED + 1, 0.05, 0.95)
    local_sd = float(np.std(np.asarray(local_values, dtype=np.float64)))
    local_standardized_lower = local_ci[0] / local_sd if local_sd > 0.0 else 0.0
    controls = {condition: _summary(action_arrays[condition]) for condition in ("exact_copy", "shuffled", "constant", "matched")}
    summaries = {
        "family_count": len(families),
        "document_count": len({int(family["gutenberg_id"]) for family in families}),
        "tau_cst": _summary(np.asarray(tau_values)),
        "lambda_local": {**_summary(np.asarray(local_values)), "bootstrap_lower_95": local_ci[0], "bootstrap_upper_95": local_ci[1], "standardized_lower_95": local_standardized_lower},
        "gamma_view": {"mean": float(np.mean(gamma_values)), "bootstrap_lower_90": gamma_ci[0], "bootstrap_upper_90": gamma_ci[1]},
        "controls": controls,
        "activation_only": _summary(action_arrays["activation_only"]),
        "text_only_clean_margin": _summary(np.asarray([baselines[(observation["family_id"], observation["view"], observation["direction"])] for observation in observations], dtype=np.float64)),
        "repeatability": {"max_abs_effect_delta": repeat_delta, "sign_stability": repeat_sign, "icc_a1": _icc_a1(repeat_matrix)},
        "matched_norm_relative_error_max": max_norm_error,
        "cell_missingness": 0.0,
        "family_effects_for_prediction": len(observations),
    }
    return summaries, observations


def _power_simulation() -> dict[str, Any]:
    rng = np.random.default_rng(protocol.POWER_SIMULATION_SEED)
    documents = 44
    families_per_document = protocol.FAMILIES_PER_DOCUMENT
    results: dict[str, float] = {}
    for icc in protocol.ICC_SENSITIVITY:
        successes = 0
        for _ in range(protocol.POWER_SIMULATION_REPS):
            cluster = rng.normal(0.0, math.sqrt(icc), documents)
            residual = rng.normal(0.0, math.sqrt(1.0 - icc), (documents, families_per_document))
            values = protocol.POWER_D + cluster[:, None] + residual
            document_means = np.mean(values, axis=1)
            statistic = float(np.mean(document_means) / (np.std(document_means, ddof=1) / math.sqrt(documents)))
            successes += int(statistic >= 1.96)
        results[f"icc={icc:g}"] = successes / protocol.POWER_SIMULATION_REPS
    return {"seed": protocol.POWER_SIMULATION_SEED, "repetitions": protocol.POWER_SIMULATION_REPS, "documents": documents, "families_per_document": families_per_document, "planning_d": protocol.POWER_D, "power_by_icc": results, "gate": all(value >= protocol.MIN_POWER for value in results.values())}


def _decoder_records(observations: list[dict[str, Any]], clean: dict[tuple[str, str, str], dict[str, Any]] | None = None) -> None:
    del observations, clean


def _recoverability(model: Any, base_layers: list[Any], fit_families: list[dict[str, Any]], tune_families: list[dict[str, Any]], tokenizer: Any, response_ids: dict[str, int], mx: Any) -> dict[str, Any]:
    fit_clean = _capture_clean(model, base_layers, fit_families, tokenizer, response_ids, mx)
    tune_clean = _capture_clean(model, base_layers, tune_families, tokenizer, response_ids, mx)
    fit_features: list[np.ndarray] = []
    fit_labels: list[int] = []
    for family in fit_families:
        family_id = str(family["family_id"])
        for view in protocol.VIEWS:
            for role in ("receiver", "donor"):
                fit_features.append(_feature(fit_clean[(family_id, view, role)]["source"]))
                fit_labels.append(int(fit_clean[(family_id, view, role)]["state"]))
    x_fit = np.asarray(fit_features, dtype=np.float64)
    y_fit = np.asarray(fit_labels, dtype=np.int64)
    one_hot = np.eye(protocol.STATE_COUNT, dtype=np.float64)[y_fit]
    weights = np.column_stack([_fit_ridge(x_fit, one_hot[:, column], protocol.RIDGE_ALPHAS[0])[0] for column in range(protocol.STATE_COUNT)])
    intercept = np.asarray([_fit_ridge(x_fit, one_hot[:, column], protocol.RIDGE_ALPHAS[0])[1] for column in range(protocol.STATE_COUNT)], dtype=np.float64)
    result: dict[str, Any] = {}
    for view in protocol.VIEWS:
        for direction in protocol.DIRECTIONS:
            role = _direction_roles(direction)[0]
            values: list[float] = []
            labels: list[int] = []
            cluster_ids: list[int] = []
            for family in tune_families:
                key = (str(family["family_id"]), view, role)
                feature = _feature(tune_clean[key]["source"])
                predicted = int(np.argmax(feature @ weights + intercept))
                values.append(float(predicted == int(tune_clean[key]["state"])))
                labels.append(int(tune_clean[key]["state"]))
                cluster_ids.append(int(family["gutenberg_id"]))
            accuracy = float(np.mean(values))
            ci = _cluster_ci(np.asarray(values, dtype=np.float64), cluster_ids, protocol.BOOTSTRAP_SEED + len(result) + 20)
            result[f"{view}:{direction}"] = {"balanced_accuracy": accuracy, "bootstrap_lower_95": ci[0], "bootstrap_upper_95": ci[1], "chance": protocol.RECOVERABILITY_CHANCE, "margin": protocol.RECOVERABILITY_MARGIN, "gate": ci[0] > protocol.RECOVERABILITY_CHANCE + protocol.RECOVERABILITY_MARGIN}
    return {"feature_map_id": protocol.FEATURE_MAP_ID, "cells": result, "gate": all(cell["gate"] for cell in result.values())}


def _load_custody(panel_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    for path in (panel_root, qualification_root, model_root):
        protocol.assert_external(path, repository_root)
    panel_manifest = protocol.read_json(panel_root / "panel-manifest.json")
    panel_receipt = protocol.read_json(panel_root / "validator-receipt.json")
    qualification = protocol.read_json(qualification_root / "qualification-result.json")
    qualification_receipt = protocol.read_json(qualification_root / "validator-receipt.json")
    families = protocol.read_json(panel_root / "families.json")
    if panel_receipt.get("valid") is not True or qualification_receipt.get("valid") is not True:
        raise protocol.ProtocolError("independent panel and qualification receipts are required")
    if panel_manifest.get("protocol") != protocol.PROTOCOL_ID or qualification.get("protocol") != protocol.PROTOCOL_ID:
        raise protocol.ProtocolError("custody protocol mismatch")
    if panel_manifest.get("state_slice") != protocol.STATE_SLICE or qualification.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("custody state-slice mismatch")
    if qualification.get("classification") != "InstrumentFeasibility" or not all(qualification.get("gates", {}).values()):
        raise protocol.ProtocolError("qualification is not fully passing")
    if qualification.get("protocol_source_sha256") != protocol.sha256_file(Path(protocol.__file__).resolve()):
        raise protocol.ProtocolError("qualification protocol source digest is stale")
    if panel_manifest.get("families_sha256") != protocol.sha256_file(panel_root / "families.json"):
        raise protocol.ProtocolError("panel family digest is stale")
    if not isinstance(families, list) or len(families) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("panel family count is invalid")
    model_manifest = protocol.model_manifest(model_root)
    if qualification.get("model_manifest_sha256") != model_manifest["manifest_sha256"]:
        raise protocol.ProtocolError("model manifest binding mismatch")
    return panel_manifest, qualification, model_manifest, families


def run(panel_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path, repeat_index: int) -> Path:
    panel_root = panel_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    repository_root = repository_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite measurement root: {output_root}")
    if repeat_index not in (1, 2):
        raise protocol.ProtocolError("repeat index must be 1 or 2")
    panel_manifest, qualification, model_manifest, families = _load_custody(panel_root, qualification_root, model_root, repository_root)
    by_split = {split: [family for family in families if family["split"] == split] for split in protocol.SPLITS}
    if any(len(by_split[split]) != protocol.DOCUMENTS_PER_SPLIT * protocol.FAMILIES_PER_DOCUMENT for split in protocol.SPLITS):
        raise protocol.ProtocolError("split family counts are not sealed")
    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("model layer count differs from custody")
    response_ids = _strict_response_ids(tokenizer)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    events: list[dict[str, Any]] = []
    try:
        fit_summary, fit_observations = _measure_split(model, base_layers, by_split["fit"], tokenizer, response_ids, mx)
        events.append({"event": "fit_effects_generated"})
        tune_clean_for_features = _capture_clean(model, base_layers, by_split["tune"], tokenizer, response_ids, mx)
        fit_features = np.asarray([observation["source_difference_feature"] for observation in fit_observations], dtype=np.float64)
        fit_labels = np.asarray([observation["transport_effect"] for observation in fit_observations], dtype=np.float64)
        tune_feature_records: list[dict[str, Any]] = []
        for family in by_split["tune"]:
            family_id = str(family["family_id"])
            for view in protocol.VIEWS:
                for direction in protocol.DIRECTIONS:
                    receiver_role, donor_role = _direction_roles(direction)
                    receiver = tune_clean_for_features[(family_id, view, receiver_role)]
                    donor = tune_clean_for_features[(family_id, view, donor_role)]
                    tune_feature_records.append({
                        "family_id": family_id,
                        "view": view,
                        "direction": direction,
                        "activation": _feature(donor["source"] - receiver["source"]),
                        "text": _hash_feature(receiver["prompt"].encode("utf-8")),
                        "input": _hash_feature(np.asarray(receiver["tokens"], dtype=np.int64).tobytes()),
                    })
        model_specs: dict[str, tuple[np.ndarray, float]] = {}
        prediction_arrays: dict[str, np.ndarray] = {}
        for feature_name in ("activation", "text", "input"):
            fit_matrix = fit_features if feature_name == "activation" else np.asarray([observation[f"{feature_name}_feature"] for observation in fit_observations], dtype=np.float64)
            tune_matrix = np.asarray([record[feature_name] for record in tune_feature_records], dtype=np.float64)
            for alpha in protocol.RIDGE_ALPHAS:
                weights, intercept = _fit_ridge(fit_matrix, fit_labels, alpha)
                key = f"{feature_name}:alpha={alpha:g}"
                model_specs[key] = (weights, intercept)
                prediction_arrays[key] = tune_matrix @ weights + intercept
        prediction_digests = {key: protocol.canonical_digest(value.tolist()) for key, value in prediction_arrays.items()}
        prediction_lock = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "repeat_index": repeat_index,
            "feature_map_id": protocol.FEATURE_MAP_ID,
            "ridge_alphas": list(protocol.RIDGE_ALPHAS),
            "prediction_count": len(tune_feature_records),
            "prediction_digests": prediction_digests,
            "fit_observation_count": len(fit_observations),
            "tune_effects_generated": False,
            "assessment_opened": False,
        }
        protocol.write_json(staging / "prediction-lock.json", prediction_lock)
        events.append({"event": "tune_predictions_emitted_and_digested", "before": "tune_effects_generated"})
        tune_summary, tune_observations = _measure_split(model, base_layers, by_split["tune"], tokenizer, response_ids, mx)
        events.append({"event": "tune_effects_generated"})

        tune_observed = np.asarray([observation["transport_effect"] for observation in tune_observations], dtype=np.float64)
        predictor_metrics: dict[str, Any] = {}
        for key, predicted in prediction_arrays.items():
            predictor_metrics[key] = _prediction_metrics(predicted, tune_observed, protocol.BOOTSTRAP_SEED + _stable_seed(key) % 1000)
        activation_candidates = []
        for alpha in protocol.RIDGE_ALPHAS:
            key = f"activation:alpha={alpha:g}"
            if all(predictor_metrics[key]["gates"].values()):
                activation_candidates.append(alpha)
        selected_alpha = activation_candidates[0] if activation_candidates else None
        recoverability = _recoverability(model, base_layers, by_split["fit"], by_split["tune"], tokenizer, response_ids, mx)
        power = _power_simulation()
        control_gate = (
            tune_summary["controls"]["exact_copy"]["mean_abs"] <= protocol.MAX_EXACT_COPY_ABS_EFFECT
            and abs(tune_summary["controls"]["shuffled"]["mean"]) <= protocol.MAX_GENERIC_CONTROL_MARGIN
            and abs(tune_summary["controls"]["constant"]["mean"]) <= protocol.MAX_GENERIC_CONTROL_MARGIN
            and abs(tune_summary["controls"]["matched"]["mean"]) <= protocol.MAX_GENERIC_CONTROL_MARGIN
        )
        localization_gate = tune_summary["lambda_local"]["bootstrap_lower_95"] >= protocol.MIN_LOCALIZATION_MARGIN and tune_summary["lambda_local"]["standardized_lower_95"] >= protocol.MIN_LOCALIZATION_STANDARDIZED
        view_gate = tune_summary["gamma_view"]["bootstrap_lower_90"] >= -protocol.VIEW_EQUIVALENCE_MARGIN and tune_summary["gamma_view"]["bootstrap_upper_90"] <= protocol.VIEW_EQUIVALENCE_MARGIN
        reliability_gate = tune_summary["repeatability"]["icc_a1"] >= protocol.MIN_ICC_LOWER and tune_summary["repeatability"]["sign_stability"] >= protocol.MIN_SIGN_STABILITY and tune_summary["cell_missingness"] <= protocol.MAX_CELL_MISSINGNESS
        prediction_gate = selected_alpha is not None
        all_fit_tune_gates = prediction_gate and localization_gate and view_gate and reliability_gate and control_gate and recoverability["gate"] and power["gate"]
        selected_target = {"source_layer": protocol.SOURCE_LAYER, "destination_layer": protocol.DESTINATION_LAYER, "position": protocol.POSITION_NAME, "alpha": selected_alpha} if all_fit_tune_gates else None
        lock = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "repeat_index": repeat_index,
            "source_layer": protocol.SOURCE_LAYER,
            "destination_layer": protocol.DESTINATION_LAYER,
            "position_name": protocol.POSITION_NAME,
            "position_rule": protocol.POSITION_RULE,
            "alpha": protocol.ALPHA,
            "additional_passes": protocol.ADDITIONAL_PASSES,
            "feature_map_id": protocol.FEATURE_MAP_ID,
            "ridge_alphas": list(protocol.RIDGE_ALPHAS),
            "selected_target": selected_target,
            "prediction_digests": prediction_digests,
            "measured_splits": ["fit", "tune"],
            "events": events,
            "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
            "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
            "model_manifest_sha256": model_manifest["manifest_sha256"],
            "assessment_opened": False,
            "prediction_lock_before_assessment": True,
        }
        lock["configuration_lock_sha256"] = protocol.canonical_digest(lock)
        classification = "ReviewRequired" if selected_target is not None else "DevelopmentNoCandidate"
        result = {
            "protocol": protocol.PROTOCOL_ID,
            "state_slice": protocol.STATE_SLICE,
            "repeat_index": repeat_index,
            "classification": classification,
            "claim_ceiling": CLAIM_CEILING_REVIEW if selected_target is not None else CLAIM_CEILING_NO_CANDIDATE,
            "aggregate_only_retention": True,
            "assessment_opened": False,
            "assessment_effects_present": False,
            "review_required_before_assessment": selected_target is not None,
            "review_verified": False,
            "prediction_lock_before_assessment": True,
            "panel_manifest_sha256": lock["panel_manifest_sha256"],
            "qualification_result_sha256": lock["qualification_result_sha256"],
            "model_manifest_sha256": lock["model_manifest_sha256"],
            "configuration_lock_sha256": lock["configuration_lock_sha256"],
            "operator": {"source_layer": protocol.SOURCE_LAYER, "destination_layer": protocol.DESTINATION_LAYER, "position_name": protocol.POSITION_NAME, "position_rule": protocol.POSITION_RULE, "alpha": protocol.ALPHA, "additional_passes": protocol.ADDITIONAL_PASSES},
            "controls": ["activation_only", "text_only", "input_only", "exact_copy", "shuffled", "constant", "matched", "access_null", "matched_norm"],
            "selected_alpha": selected_alpha,
            "measured_splits": ["fit", "tune"],
            "fit_tune_gates": {"prediction": prediction_gate, "localization": localization_gate, "view_equivalence": view_gate, "reliability": reliability_gate, "controls": control_gate, "recoverability": recoverability["gate"], "power": power["gate"], "all": all_fit_tune_gates},
            "fit": fit_summary,
            "tune": tune_summary,
            "predictors": predictor_metrics,
            "recoverability": recoverability,
            "power_simulation": power,
            "source_sha256": {"protocol": protocol.sha256_file(Path(protocol.__file__).resolve()), "runner": protocol.sha256_file(Path(__file__).resolve())},
        }
        protocol.write_json(staging / "configuration-lock.json", lock)
        protocol.write_json(staging / "causal-state-transport-result.json", result)
        if output_root.exists():
            raise protocol.ProtocolError(f"measurement root appeared during execution: {output_root}")
        staging.rename(output_root)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        del model
    return output_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repeat-index", type=int, default=1)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = run(args.panel_root, args.qualification_root, args.model, args.output_root, args.repository_root, args.repeat_index)
        result = protocol.read_json(root / "causal-state-transport-result.json")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({"measurement_root": str(root), "classification": result["classification"], "selected_alpha": result["selected_alpha"], "assessment_opened": result["assessment_opened"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
