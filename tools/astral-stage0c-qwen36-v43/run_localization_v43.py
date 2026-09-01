#!/usr/bin/env python3
"""Run V43 fit/tune layer localization with assessment closed by default.

State slice: astral-stage0c-qwen36-causal-target-localization-v43.

All forward effects stay in memory. Only aggregate statistics, custody
digests, a pre-assessment configuration lock, and a narrow disposition are
written. Assessment requires an independently authored review receipt and a
configuration lock supplied before assessment effects are generated.
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

import protocol_v43 as protocol


CLAIM_CEILING_NO_CANDIDATE = "LocalDevelopmentV43TargetLocalizationNoCandidate"
CLAIM_CEILING_REVIEW = "LocalDevelopmentV43TargetLocalizationReviewRequired"
CLAIM_CEILING_RESULT = "LocalDevelopmentV43CausalTargetLocalization"


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
    def __init__(self, layer: Any, index: int, target_layer: int, replacement: np.ndarray | None, mx: Any) -> None:
        self.layer = layer
        self.index = index
        self.target_layer = target_layer
        self.replacement = replacement
        self.mx = mx
        self.captured = None
        self.is_linear = layer.is_linear

    def __call__(self, x: Any, mask: Any = None, cache: Any = None) -> Any:
        output = self.layer(x, mask=mask, cache=cache)
        if self.index == self.target_layer:
            self.captured = output
            if self.replacement is not None:
                replacement = self.mx.array(self.replacement.astype(np.float32), dtype=output.dtype).reshape((1, 1, -1))
                output = self.mx.concatenate([output[:, :-1, :], replacement], axis=1)
        return output


def _forward(
    model: Any,
    base_layers: list[Any],
    token_ids: list[int],
    target_layer: int,
    replacement: np.ndarray | None,
    response_ids: dict[str, int],
    mx: Any,
) -> tuple[np.ndarray, np.ndarray]:
    probes = [LayerProbe(layer, index, target_layer, replacement, mx) for index, layer in enumerate(base_layers)]
    model.language_model.model.layers = probes
    try:
        logits = model(mx.array([token_ids]))
        captured = probes[target_layer].captured
        if captured is None:
            raise protocol.ProtocolError(f"layer {target_layer} capture was not reached")
        selected = mx.stack([logits[0, -1, response_ids["A"]], logits[0, -1, response_ids["B"]]])
        vector = captured[0, -1, :].astype(mx.float32)
        mx.eval(selected, vector)
        vector_np = np.array(vector, dtype=np.float32, copy=True)
        logits_np = np.array(selected.astype(mx.float32), dtype=np.float64, copy=True)
        if vector_np.shape != (protocol.EXPECTED_HIDDEN_WIDTH,) or not np.isfinite(vector_np).all() or not np.isfinite(logits_np).all():
            raise protocol.ProtocolError("non-finite or incorrectly shaped forward result")
        return vector_np, logits_np
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


def _token_cache(registry: list[dict[str, Any]], tokenizer: Any) -> dict[str, dict[str, list[int]]]:
    cache: dict[str, dict[str, list[int]]] = {}
    for family in registry:
        family_cache: dict[str, list[int]] = {}
        for wrapper in protocol.WRAPPER_NAMES:
            for condition in ("ordinary", "counterfactual"):
                key = f"{wrapper}_{condition}_prompt"
                tokens = list(tokenizer.encode(family[key]))
                if len(tokens) != protocol.FIXED_TOKEN_LENGTH:
                    raise protocol.ProtocolError(f"fixed tokenizer length mismatch: {family['family_id']}:{key}")
                family_cache[key] = tokens
        cache[family["family_id"]] = family_cache
    return cache


def _capture_clean(model: Any, base_layers: list[Any], families: list[dict[str, Any]], tokens: dict[str, dict[str, list[int]]], response_ids: dict[str, int], wrapper: str, mx: Any) -> dict[str, dict[str, dict[str, Any]]]:
    clean: dict[str, dict[str, dict[str, Any]]] = {}
    for family in families:
        family_id = family["family_id"]
        clean[family_id] = {}
        for target_layer in protocol.CANDIDATE_LAYERS:
            ordinary_vector, ordinary_logits = _forward(model, base_layers, tokens[family_id][f"{wrapper}_ordinary_prompt"], target_layer, None, response_ids, mx)
            counterfactual_vector, counterfactual_logits = _forward(model, base_layers, tokens[family_id][f"{wrapper}_counterfactual_prompt"], target_layer, None, response_ids, mx)
            clean[family_id][str(target_layer)] = {
                "ordinary_vector": ordinary_vector,
                "counterfactual_vector": counterfactual_vector,
                "ordinary_logits": ordinary_logits,
                "counterfactual_logits": counterfactual_logits,
            }
    return clean


def _pair_effect(
    model: Any,
    base_layers: list[Any],
    family: dict[str, Any],
    family_clean: dict[str, Any],
    tokens: dict[str, dict[str, list[int]]],
    wrapper: str,
    target_layer: int,
    response_ids: dict[str, int],
    mx: Any,
    ordinary_replacement: np.ndarray,
    counterfactual_replacement: np.ndarray,
) -> float:
    family_id = family["family_id"]
    _, ordinary_intervened = _forward(model, base_layers, tokens[family_id][f"{wrapper}_ordinary_prompt"], target_layer, ordinary_replacement, response_ids, mx)
    _, counterfactual_intervened = _forward(model, base_layers, tokens[family_id][f"{wrapper}_counterfactual_prompt"], target_layer, counterfactual_replacement, response_ids, mx)
    return _effect(family_clean["ordinary_logits"], family_clean["counterfactual_logits"], ordinary_intervened, counterfactual_intervened)


def _donor(family: dict[str, Any], families: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = sorted(
        (other for other in families if other["family_id"] != family["family_id"] and other["gutenberg_id"] != family["gutenberg_id"]),
        key=lambda other: other["family_id"],
    )
    if not candidates:
        raise protocol.ProtocolError("no document-disjoint donor exists")
    return candidates[0]


def _measure_split(model: Any, base_layers: list[Any], families: list[dict[str, Any]], tokens: dict[str, dict[str, list[int]]], response_ids: dict[str, int], mx: Any) -> dict[str, Any]:
    activation: dict[str, dict[str, list[float]]] = {wrapper: {str(layer): [] for layer in protocol.CANDIDATE_LAYERS} for wrapper in protocol.WRAPPER_NAMES}
    text_only: dict[str, dict[str, list[float]]] = {wrapper: {str(layer): [] for layer in protocol.CANDIDATE_LAYERS} for wrapper in protocol.WRAPPER_NAMES}
    controls: dict[str, dict[str, dict[str, list[float]]]] = {
        wrapper: {str(layer): {name: [] for name in ("exact_copy", "shuffled", "constant", "matched")} for layer in protocol.CANDIDATE_LAYERS}
        for wrapper in protocol.WRAPPER_NAMES
    }
    matched_norm_max = 0.0
    matched_violations = 0
    repeat_max = 0.0
    for wrapper in protocol.WRAPPER_NAMES:
        clean = _capture_clean(model, base_layers, families, tokens, response_ids, wrapper, mx)
        means: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for layer in protocol.CANDIDATE_LAYERS:
            layer_key = str(layer)
            means[layer_key] = (
                np.mean([clean[family["family_id"]][layer_key]["ordinary_vector"] for family in families], axis=0),
                np.mean([clean[family["family_id"]][layer_key]["counterfactual_vector"] for family in families], axis=0),
            )
        for family_index, family in enumerate(families):
            family_id = family["family_id"]
            donor = _donor(family, families)
            for layer in protocol.CANDIDATE_LAYERS:
                layer_key = str(layer)
                family_clean = clean[family_id][layer_key]
                own_ord = family_clean["ordinary_vector"]
                own_cf = family_clean["counterfactual_vector"]
                donor_clean = clean[donor["family_id"]][layer_key]
                activation_value = _pair_effect(model, base_layers, family, family_clean, tokens, wrapper, layer, response_ids, mx, own_cf, own_ord)
                activation[wrapper][layer_key].append(activation_value)
                text_only[wrapper][layer_key].append(_text_only_effect(family_clean["ordinary_logits"], family_clean["counterfactual_logits"]))
                controls[wrapper][layer_key]["exact_copy"].append(_pair_effect(model, base_layers, family, family_clean, tokens, wrapper, layer, response_ids, mx, own_ord, own_cf))
                controls[wrapper][layer_key]["shuffled"].append(_pair_effect(model, base_layers, family, family_clean, tokens, wrapper, layer, response_ids, mx, donor_clean["counterfactual_vector"], donor_clean["ordinary_vector"]))
                mean_ord, mean_cf = means[layer_key]
                controls[wrapper][layer_key]["constant"].append(_pair_effect(model, base_layers, family, family_clean, tokens, wrapper, layer, response_ids, mx, mean_cf, mean_ord))
                matched_cf, cf_error = _norm_match(donor_clean["counterfactual_vector"], own_ord)
                matched_ord, ord_error = _norm_match(donor_clean["ordinary_vector"], own_cf)
                matched_norm_max = max(matched_norm_max, cf_error, ord_error)
                if cf_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE or ord_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
                    matched_violations += 1
                controls[wrapper][layer_key]["matched"].append(_pair_effect(model, base_layers, family, family_clean, tokens, wrapper, layer, response_ids, mx, matched_cf, matched_ord))
                if family_index == 0:
                    repeated = _pair_effect(model, base_layers, family, family_clean, tokens, wrapper, layer, response_ids, mx, own_cf, own_ord)
                    repeat_max = max(repeat_max, abs(repeated - activation_value))

    layer_summaries: dict[str, Any] = {}
    for layer in protocol.CANDIDATE_LAYERS:
        layer_key = str(layer)
        alpha = np.asarray(activation["wrapper_alpha"][layer_key], dtype=np.float64)
        beta = np.asarray(activation["wrapper_beta"][layer_key], dtype=np.float64)
        reliability = {
            "wrapper_correlation": _correlation(alpha, beta),
            "wrapper_sign_agreement": _sign_agreement(alpha, beta),
            "bootstrap_correlation_lower_95": _bootstrap_lower(alpha, beta, protocol.BOOTSTRAP_SEED + layer),
            "wrapper_alpha_effect_std": float(np.std(alpha)),
            "wrapper_beta_effect_std": float(np.std(beta)),
            "target_effect_std_min": float(min(np.std(alpha), np.std(beta))),
        }
        control_summaries: dict[str, Any] = {}
        for control_name in ("exact_copy", "shuffled", "constant", "matched"):
            values = np.concatenate([controls[wrapper][layer_key][control_name] for wrapper in protocol.WRAPPER_NAMES])
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
            "repeatability": repeat_max <= protocol.MAX_REPEAT_ABS_EFFECT_DELTA,
        }
        layer_summaries[layer_key] = {
            "layer": layer,
            "family_count": len(families),
            "document_count": len({int(family["gutenberg_id"]) for family in families}),
            "activation_only": {wrapper: _summary(activation[wrapper][layer_key]) for wrapper in protocol.WRAPPER_NAMES},
            "text_only": {wrapper: _summary(text_only[wrapper][layer_key]) for wrapper in protocol.WRAPPER_NAMES},
            "controls": control_summaries,
            "matched_norm_relative_error_max": matched_norm_max,
            "matched_donor_violations": matched_violations,
            "repeat_max_abs_effect_delta": repeat_max,
            "reliability": {**reliability, "gates": gates},
        }
    return {
        "family_count": len(families),
        "document_count": len({int(family["gutenberg_id"]) for family in families}),
        "layer_summaries": layer_summaries,
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
    }


def _load_registry(panel_root: Path) -> list[dict[str, Any]]:
    document = protocol.read_json(panel_root / "concept-registry.json")
    if not isinstance(document, dict) or document.get("protocol") != protocol.PROTOCOL_ID or document.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("panel registry binding is invalid")
    families = document.get("families")
    if not isinstance(families, list) or len(families) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("panel family census is invalid")
    return families


def _review_ok(review_path: Path, lock: dict[str, Any]) -> bool:
    review = protocol.read_json(review_path)
    required = ("custody_verified", "fresh_data_verified", "controls_verified", "prediction_lock_verified", "privacy_retention_verified", "claim_ceiling_verified", "validator_behavior_verified")
    return (
        isinstance(review, dict)
        and review.get("protocol") == protocol.PROTOCOL_ID
        and review.get("state_slice") == protocol.STATE_SLICE
        and review.get("approved") is True
        and review.get("assessment_authorized") is True
        and review.get("configuration_lock_sha256") == lock.get("configuration_lock_sha256")
        and all(review.get(key) is True for key in required)
    )


def run(panel_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path, review_receipt: Path | None = None) -> Path:
    panel_root = panel_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite localization root: {output_root}")
    panel_manifest, qualification, model_manifest = _load_custody(panel_root, qualification_root, model_root, repository_root)
    registry = _load_registry(panel_root)
    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    response_ids = _strict_response_ids(tokenizer)
    tokens = _token_cache(registry, tokenizer)
    by_split = {split: [family for family in registry if family["split"] == split] for split in protocol.SPLITS}
    measured_splits = ("fit", "tune")
    split_results = {split: _measure_split(model, base_layers, by_split[split], tokens, response_ids, mx) for split in measured_splits}
    tune_layers = split_results["tune"]["layer_summaries"]
    passing_layers = [layer for layer in protocol.CANDIDATE_LAYERS if all(tune_layers[str(layer)]["reliability"]["gates"].values())]
    selected_layer = min(passing_layers) if passing_layers else None
    lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "selection_rule": "lowest_numeric_candidate_layer_passing_all_tune_gates",
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "selected_layer": selected_layer,
        "measured_splits": list(measured_splits),
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "assessment_effects_locked": True,
        "prediction_lock_before_assessment": True,
        "assessment_opened": False,
    }
    lock["configuration_lock_sha256"] = _configuration_lock_digest(lock)
    assessment_opened = False
    review_verified = False
    classification = "TargetLocalizationNoCandidate"
    claim_ceiling = CLAIM_CEILING_NO_CANDIDATE
    if selected_layer is not None:
        classification = "ReviewRequired"
        claim_ceiling = CLAIM_CEILING_REVIEW
        if review_receipt is not None and _review_ok(review_receipt.resolve(), lock):
            # V43 intentionally leaves assessment unopened in this bounded
            # command unless a separately reviewed assessment execution is
            # invoked. The receipt is recorded only as a gate observation.
            review_verified = True
        elif review_receipt is not None:
            raise protocol.ProtocolError("review receipt does not authorize the sealed configuration")
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "classification": classification,
        "claim_ceiling": claim_ceiling,
        "aggregate_only_retention": True,
        "assessment_opened": assessment_opened,
        "assessment_effects_present": False,
        "prediction_lock_before_assessment": True,
        "review_verified": review_verified,
        "panel_manifest_sha256": lock["panel_manifest_sha256"],
        "qualification_result_sha256": lock["qualification_result_sha256"],
        "model_manifest_sha256": lock["model_manifest_sha256"],
        "configuration_lock_sha256": lock["configuration_lock_sha256"],
        "candidate_layers": list(protocol.CANDIDATE_LAYERS),
        "fixed_position": protocol.FIXED_POSITION,
        "measured_splits": list(measured_splits),
        "selection_rule": lock["selection_rule"],
        "passing_layers": passing_layers,
        "selected_layer": selected_layer,
        "splits": split_results,
        "tune_passed": bool(passing_layers),
        "source_sha256": {
            "protocol": protocol.sha256_file(Path(protocol.__file__).resolve()),
            "runner": protocol.sha256_file(Path(__file__).resolve()),
        },
    }
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        protocol.write_json(staging / "configuration-lock.json", lock)
        protocol.write_json(staging / "localization-result.json", result)
        if output_root.exists():
            raise protocol.ProtocolError(f"localization root appeared during execution: {output_root}")
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
    parser.add_argument("--review-receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        root = run(args.panel_root, args.qualification_root, args.model, args.output_root, args.repository_root.resolve(), args.review_receipt)
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    result = protocol.read_json(root / "localization-result.json")
    print(json.dumps({"localization_root": str(root), "classification": result["classification"], "selected_layer": result["selected_layer"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
