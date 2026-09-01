#!/usr/bin/env python3
"""Measure V42 direct target reliability with assessment held closed by default.

State slice: astral-stage0c-qwen36-causal-target-reliability-v42.

Only aggregate statistics are written. Fit and tune are measured first. If the
sealed tune gate passes, a configuration lock is emitted and assessment still
requires an independently authored review receipt supplied with
``--review-receipt``.
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

import protocol_v42 as protocol


CLAIM_CEILING_NO_CANDIDATE = "LocalDevelopmentV42TargetReliabilityNoCandidate"
CLAIM_CEILING_REVIEW = "LocalDevelopmentV42TargetReliabilityReviewRequired"
CLAIM_CEILING_RESULT = "LocalDevelopmentV42CausalTargetReliability"


def _digest(value: Any) -> str:
    return protocol.canonical_digest(value)


def _configuration_lock_digest(lock: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in lock.items() if key != "configuration_lock_sha256"}
    return _digest(unsigned)


def _write_json(path: Path, value: Any) -> None:
    protocol.write_json(path, value)


def _load_json(path: Path) -> Any:
    return protocol.read_json(path)


def _require_valid_custody(
    panel_root: Path, qualification_root: Path, model_root: Path, repository_root: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    for path in (panel_root, qualification_root, model_root):
        protocol.assert_external(path, repository_root)
    panel_manifest = _load_json(panel_root / "panel-manifest.json")
    panel_receipt = _load_json(panel_root / "validator-receipt.json")
    qualification = _load_json(qualification_root / "qualification-result.json")
    qualification_receipt = _load_json(qualification_root / "validator-receipt.json")
    if not isinstance(panel_manifest, dict) or not isinstance(panel_receipt, dict) or not isinstance(qualification, dict) or not isinstance(qualification_receipt, dict):
        raise protocol.ProtocolError("custody documents must be objects")
    if panel_manifest.get("protocol") != protocol.PROTOCOL_ID or panel_manifest.get("state_slice") != protocol.STATE_SLICE or panel_receipt.get("valid") is not True:
        raise protocol.ProtocolError("panel custody is not independently valid")
    if qualification.get("protocol") != protocol.PROTOCOL_ID or qualification.get("state_slice") != protocol.STATE_SLICE or qualification_receipt.get("valid") is not True or qualification.get("classification") != "InstrumentFeasibility":
        raise protocol.ProtocolError("qualification custody is not independently valid")
    manifest = protocol.model_manifest(model_root)
    if panel_manifest.get("model_manifest_sha256") != manifest.get("manifest_sha256") or qualification.get("model_manifest_sha256") != manifest.get("manifest_sha256"):
        raise protocol.ProtocolError("model custody binding mismatch")
    if not all(qualification.get("gates", {}).values()):
        raise protocol.ProtocolError("qualification gates are not all passing")
    return panel_manifest, qualification, manifest


def _strict_response_ids(tokenizer: Any) -> dict[str, int]:
    result: dict[str, int] = {}
    for label, token_text in protocol.RESPONSE_TOKENS.items():
        token_ids = list(tokenizer.encode(token_text))
        if len(token_ids) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
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
        if self.index == protocol.TARGET_LAYER:
            self.captured = output
            if self.replacement is not None:
                replacement = self.mx.array(self.replacement.astype(np.float32), dtype=output.dtype).reshape((1, 1, -1))
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


def _effect(
    ordinary_clean: np.ndarray,
    counterfactual_clean: np.ndarray,
    ordinary_intervened: np.ndarray,
    counterfactual_intervened: np.ndarray,
) -> float:
    return 0.5 * (
        _margin(ordinary_intervened, "A")
        - _margin(ordinary_clean, "A")
        + _margin(counterfactual_intervened, "B")
        - _margin(counterfactual_clean, "B")
    )


def _norm_match(source: np.ndarray, receiver: np.ndarray) -> tuple[np.ndarray, float]:
    source_value = source.astype(np.float64)
    receiver_value = receiver.astype(np.float64)
    source_norm = float(np.linalg.norm(source_value))
    receiver_norm = float(np.linalg.norm(receiver_value))
    if source_norm <= 0.0 or receiver_norm <= 0.0:
        raise protocol.ProtocolError("cannot norm-match a zero activation")
    replacement = source * np.float32(receiver_norm / source_norm)
    relative_error = abs(float(np.linalg.norm(replacement.astype(np.float64))) - receiver_norm) / receiver_norm
    if relative_error > protocol.MATCH_NORM_RELATIVE_TOLERANCE:
        raise protocol.ProtocolError("matched replacement norm is outside tolerance")
    return replacement, relative_error


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


def _capture_clean(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    tokens: dict[str, dict[str, list[int]]],
    response_ids: dict[str, int],
    wrapper: str,
    mx: Any,
) -> dict[str, dict[str, Any]]:
    clean: dict[str, dict[str, Any]] = {}
    for family in families:
        family_id = family["family_id"]
        ordinary_vector, ordinary_logits = _forward(model, base_layers, tokens[family_id][f"{wrapper}_ordinary_prompt"], None, response_ids, mx)
        counterfactual_vector, counterfactual_logits = _forward(model, base_layers, tokens[family_id][f"{wrapper}_counterfactual_prompt"], None, response_ids, mx)
        clean[family_id] = {
            "ordinary_vector": ordinary_vector,
            "counterfactual_vector": counterfactual_vector,
            "ordinary_logits": ordinary_logits,
            "counterfactual_logits": counterfactual_logits,
        }
    return clean


def _primary_once(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    tokens: dict[str, dict[str, list[int]]],
    response_ids: dict[str, int],
    wrapper: str,
    mx: Any,
) -> tuple[np.ndarray, dict[str, dict[str, Any]]]:
    clean = _capture_clean(model, base_layers, families, tokens, response_ids, wrapper, mx)
    effects: list[float] = []
    for family in families:
        current = clean[family["family_id"]]
        _, ordinary_logits = _forward(model, base_layers, tokens[family["family_id"]][f"{wrapper}_ordinary_prompt"], current["counterfactual_vector"], response_ids, mx)
        _, counterfactual_logits = _forward(model, base_layers, tokens[family["family_id"]][f"{wrapper}_counterfactual_prompt"], current["ordinary_vector"], response_ids, mx)
        effects.append(_effect(current["ordinary_logits"], current["counterfactual_logits"], ordinary_logits, counterfactual_logits))
    return np.asarray(effects, dtype=np.float64), clean


def _donor(family: dict[str, Any], families: list[dict[str, Any]], kind: str) -> dict[str, Any]:
    candidates = [other for other in families if other["family_id"] != family["family_id"] and other["gutenberg_id"] != family["gutenberg_id"]]
    if not candidates:
        raise protocol.ProtocolError(f"no cross-document donor: {family['family_id']}")
    if kind == "matched":
        return min(candidates, key=lambda other: (abs(int(other["source_word_count"]) - int(family["source_word_count"])), _digest([protocol.PROTOCOL_ID, kind, family["family_id"], other["family_id"]])))
    return min(candidates, key=lambda other: _digest([protocol.PROTOCOL_ID, kind, family["family_id"], other["family_id"]]))


def _control_effect(
    model: Any,
    base_layers: list[Any],
    family: dict[str, Any],
    current: dict[str, Any],
    replacement_ordinary: np.ndarray,
    replacement_counterfactual: np.ndarray,
    tokens: dict[str, dict[str, list[int]]],
    response_ids: dict[str, int],
    mx: Any,
) -> float:
    _, ordinary_logits = _forward(model, base_layers, tokens[family["family_id"]]["wrapper_alpha_ordinary_prompt"], replacement_ordinary, response_ids, mx)
    _, counterfactual_logits = _forward(model, base_layers, tokens[family["family_id"]]["wrapper_alpha_counterfactual_prompt"], replacement_counterfactual, response_ids, mx)
    return _effect(current["ordinary_logits"], current["counterfactual_logits"], ordinary_logits, counterfactual_logits)


def _measure_split(
    model: Any,
    base_layers: list[Any],
    families: list[dict[str, Any]],
    tokens: dict[str, dict[str, list[int]]],
    response_ids: dict[str, int],
    mx: Any,
) -> dict[str, Any]:
    if not families:
        raise protocol.ProtocolError("cannot measure an empty split")
    target_by_wrapper: dict[str, list[np.ndarray]] = {wrapper: [] for wrapper in protocol.WRAPPER_NAMES}
    repeat_deltas: list[float] = []
    clean_alpha_first: dict[str, dict[str, Any]] | None = None
    first_by_wrapper: dict[str, np.ndarray] = {}
    for repeat in range(protocol.REPEATS):
        for wrapper in protocol.WRAPPER_NAMES:
            values, clean = _primary_once(model, base_layers, families, tokens, response_ids, wrapper, mx)
            target_by_wrapper[wrapper].append(values)
            if repeat == 0:
                first_by_wrapper[wrapper] = values
                if wrapper == "wrapper_alpha":
                    clean_alpha_first = clean
            else:
                repeat_deltas.append(float(np.max(np.abs(values - target_by_wrapper[wrapper][0]))))
    if clean_alpha_first is None:
        raise protocol.ProtocolError("missing first alpha clean capture")
    controls: dict[str, list[float]] = {name: [] for name in protocol.CONTROL_NAMES}
    text_only: list[float] = []
    alpha_families = sorted(families, key=lambda family: family["family_id"])
    constant_ordinary = np.mean([clean_alpha_first[family["family_id"]]["ordinary_vector"] for family in alpha_families], axis=0)
    constant_counterfactual = np.mean([clean_alpha_first[family["family_id"]]["counterfactual_vector"] for family in alpha_families], axis=0)
    norm_errors: list[float] = []
    donor_violations = 0
    for family in alpha_families:
        family_id = family["family_id"]
        current = clean_alpha_first[family_id]
        text_only.append(float(0.5 * (_margin(current["ordinary_logits"], "A") + _margin(current["counterfactual_logits"], "B"))))
        controls["exact_copy"].append(_control_effect(model, base_layers, family, current, current["ordinary_vector"], current["counterfactual_vector"], tokens, response_ids, mx))
        shuffled = _donor(family, alpha_families, "shuffled")
        matched = _donor(family, alpha_families, "matched")
        for donor, name in ((shuffled, "shuffled"), (matched, "matched")):
            if donor["gutenberg_id"] == family["gutenberg_id"]:
                donor_violations += 1
            donor_clean = clean_alpha_first[donor["family_id"]]
            ordinary_replacement, ordinary_error = _norm_match(donor_clean["ordinary_vector"], current["ordinary_vector"])
            counterfactual_replacement, counterfactual_error = _norm_match(donor_clean["counterfactual_vector"], current["counterfactual_vector"])
            norm_errors.extend([ordinary_error, counterfactual_error])
            controls[name].append(_control_effect(model, base_layers, family, current, ordinary_replacement, counterfactual_replacement, tokens, response_ids, mx))
        controls["constant"].append(_control_effect(model, base_layers, family, current, constant_ordinary, constant_counterfactual, tokens, response_ids, mx))

    target_means = {wrapper: np.mean(np.stack(values), axis=0) for wrapper, values in target_by_wrapper.items()}
    target_summary = {wrapper: _summary(values) for wrapper, values in target_means.items()}
    reliability = _reliability(target_means["wrapper_alpha"], target_means["wrapper_beta"])
    controls_summary = {name: _summary(np.asarray(values, dtype=np.float64)) for name, values in controls.items()}
    controls_summary["text_only"] = _summary(np.asarray(text_only, dtype=np.float64))
    controls_summary["matched_norm_relative_error_max"] = float(max(norm_errors, default=0.0))
    controls_summary["matched_donor_violations"] = donor_violations
    controls_summary["repeat_max_abs_effect_delta"] = float(max(repeat_deltas, default=0.0))
    return {
        "split": families[0]["split"],
        "family_count": len(families),
        "document_count": len({int(family["gutenberg_id"]) for family in families}),
        "target": target_summary,
        "reliability": reliability,
        "controls": controls_summary,
    }


def _summary(values: np.ndarray) -> dict[str, Any]:
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise protocol.ProtocolError("aggregate values are empty or non-finite")
    return {
        "count": int(len(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "mean_abs": float(np.mean(np.abs(values))),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) != len(right) or len(left) < 3:
        raise protocol.ProtocolError("correlation requires paired values")
    if np.std(left) <= 1e-12 or np.std(right) <= 1e-12:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def _bootstrap_lower(left: np.ndarray, right: np.ndarray) -> float:
    rng = np.random.default_rng(protocol.BOOTSTRAP_SEED)
    values: list[float] = []
    for _ in range(protocol.BOOTSTRAP_RESAMPLES):
        indices = rng.integers(0, len(left), size=len(left))
        values.append(_correlation(left[indices], right[indices]))
    return float(np.quantile(np.asarray(values, dtype=np.float64), 0.025))


def _reliability(left: np.ndarray, right: np.ndarray) -> dict[str, Any]:
    correlation = _correlation(left, right)
    sign_agreement = float(np.mean(np.sign(left) == np.sign(right)))
    return {
        "wrapper_correlation": correlation,
        "wrapper_sign_agreement": sign_agreement,
        "bootstrap_correlation_lower_95": _bootstrap_lower(left, right),
        "wrapper_alpha_effect_std": float(np.std(left)),
        "wrapper_beta_effect_std": float(np.std(right)),
        "target_effect_std_min": float(min(np.std(left), np.std(right))),
        "gates": {
            "target_effect_non_degenerate": bool(min(np.std(left), np.std(right)) >= protocol.MIN_TARGET_EFFECT_STD),
            "wrapper_correlation": bool(correlation >= protocol.MIN_TARGET_CORRELATION),
            "wrapper_sign_agreement": bool(sign_agreement >= protocol.MIN_TARGET_SIGN_AGREEMENT),
            "bootstrap_correlation": bool(_bootstrap_lower(left, right) >= protocol.MIN_BOOTSTRAP_CORRELATION_LOWER),
        },
    }


def _split_gates(measured: dict[str, Any]) -> dict[str, bool]:
    reliability_gates = measured["reliability"]["gates"]
    controls = measured["controls"]
    return {
        **{f"reliability:{key}": bool(value) for key, value in reliability_gates.items()},
        "repeatability": controls["repeat_max_abs_effect_delta"] <= protocol.MAX_REPEAT_ABS_EFFECT_DELTA,
        "exact_copy_null": controls["exact_copy"]["mean_abs"] <= protocol.MAX_EXACT_COPY_ABS_EFFECT,
        "shuffled_control_bound": controls["shuffled"]["mean_abs"] <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
        "constant_control_bound": controls["constant"]["mean_abs"] <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
        "matched_control_bound": controls["matched"]["mean_abs"] <= protocol.MAX_CONTROL_MEAN_ABS_EFFECT,
        "matched_donor_integrity": controls["matched_donor_violations"] == 0 and controls["matched_norm_relative_error_max"] <= protocol.MATCH_NORM_RELATIVE_TOLERANCE,
    }


def _review_is_valid(review_receipt: Path, lock: dict[str, Any]) -> bool:
    receipt = _load_json(review_receipt)
    if not isinstance(receipt, dict):
        return False
    required = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "review_status": "approved",
        "reviewed_configuration_lock_sha256": _configuration_lock_digest(lock),
        "assessment_authorized": True,
        "independent_reviewer": True,
        "custody_verified": True,
        "fresh_data_verified": True,
        "controls_verified": True,
        "prediction_lock_verified": True,
        "privacy_retention_verified": True,
        "claim_ceiling_verified": True,
        "validator_behavior_verified": True,
    }
    return all(receipt.get(key) == value for key, value in required.items())


def run(
    panel_root: Path,
    qualification_root: Path,
    model_root: Path,
    output_root: Path,
    repository_root: Path,
    review_receipt: Path | None,
) -> Path:
    panel_root = panel_root.resolve()
    qualification_root = qualification_root.resolve()
    model_root = model_root.resolve()
    output_root = output_root.resolve()
    protocol.assert_external(output_root, repository_root)
    if output_root.exists():
        raise protocol.ProtocolError(f"refusing to overwrite reliability root: {output_root}")
    panel_manifest, qualification, model_manifest = _require_valid_custody(panel_root, qualification_root, model_root, repository_root)
    registry_document = _load_json(panel_root / "concept-registry.json")
    registry = registry_document.get("families") if isinstance(registry_document, dict) else None
    if not isinstance(registry, list) or len(registry) != protocol.TOTAL_FAMILIES:
        raise protocol.ProtocolError("panel registry is invalid")

    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root), lazy=False)
    base_layers = list(model.language_model.model.layers)
    if len(base_layers) != protocol.EXPECTED_LAYER_COUNT:
        raise protocol.ProtocolError("model layer count changed after qualification")
    response_ids = _strict_response_ids(tokenizer)
    tokens = _token_cache(registry, tokenizer)
    measured: dict[str, Any] = {}
    for split in ("fit", "tune"):
        families = [family for family in registry if family.get("split") == split]
        measured[split] = _measure_split(model, base_layers, families, tokens, response_ids, mx)

    tune_gates = _split_gates(measured["tune"])
    tune_passed = all(tune_gates.values())
    configuration_lock = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "lock_kind": "preassessment-target-reliability-configuration-v1",
        "panel_manifest_sha256": protocol.sha256_file(panel_root / "panel-manifest.json"),
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "target_layer": protocol.TARGET_LAYER,
        "wrappers": list(protocol.WRAPPER_NAMES),
        "controls": list(protocol.CONTROL_NAMES),
        "thresholds": protocol.protocol_manifest()["thresholds"],
        "assessment_effects_locked": not tune_passed,
        "predictions_present": False,
        "prediction_lock_before_effects": True,
        "assessment_open_requires_review": True,
    }
    assessment_opened = False
    review_valid = False
    classification = "TargetReliabilityNoCandidate" if not tune_passed else "ReviewRequired"
    claim_ceiling = CLAIM_CEILING_NO_CANDIDATE if not tune_passed else CLAIM_CEILING_REVIEW
    if tune_passed:
        lock_digest = _configuration_lock_digest(configuration_lock)
        configuration_lock["configuration_lock_sha256"] = lock_digest
        if review_receipt is not None:
            review_valid = _review_is_valid(review_receipt.resolve(), configuration_lock)
        if review_valid:
            families = [family for family in registry if family.get("split") == "assessment"]
            measured["assessment"] = _measure_split(model, base_layers, families, tokens, response_ids, mx)
            assessment_opened = True
            assessment_gates = _split_gates(measured["assessment"])
            classification = "BoundedTargetReliability" if all(assessment_gates.values()) else "TargetReliabilityNoCandidate"
            claim_ceiling = CLAIM_CEILING_RESULT if classification == "BoundedTargetReliability" else CLAIM_CEILING_NO_CANDIDATE
        else:
            classification = "ReviewRequired"
    else:
        configuration_lock["configuration_lock_sha256"] = _digest(configuration_lock)
    result = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": f"{protocol.PROTOCOL_ID}-run-v1",
        "claim_ceiling": claim_ceiling,
        "classification": classification,
        "panel_manifest_sha256": panel_manifest.get("model_manifest_sha256") and protocol.sha256_file(panel_root / "panel-manifest.json"),
        "qualification_result_sha256": protocol.sha256_file(qualification_root / "qualification-result.json"),
        "model_manifest_sha256": model_manifest["manifest_sha256"],
        "protocol_source_sha256": protocol.sha256_file(Path(protocol.__file__).resolve()),
        "runner_source_sha256": protocol.sha256_file(Path(__file__).resolve()),
        "target_layer": protocol.TARGET_LAYER,
        "measured_splits": list(measured),
        "splits": measured,
        "tune_gates": tune_gates,
        "tune_passed": tune_passed,
        "review_receipt_supplied": review_receipt is not None,
        "review_receipt_valid": review_valid,
        "assessment_opened": assessment_opened,
        "assessment_effects_present": assessment_opened,
        "aggregate_only_retention": True,
        "prediction_lock": {
            "predictions_present": False,
            "locked_before_assessment_effects": True,
            "configuration_lock_sha256": configuration_lock["configuration_lock_sha256"],
        },
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=str(output_root.parent)))
    try:
        _write_json(staging / "configuration-lock.json", configuration_lock)
        _write_json(staging / "reliability-result.json", result)
        if review_receipt is not None:
            _write_json(staging / "review-receipt.json", _load_json(review_receipt.resolve()))
        if output_root.exists():
            raise protocol.ProtocolError(f"reliability root appeared during execution: {output_root}")
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
    result = _load_json(root / "reliability-result.json")
    valid = result["classification"] in {"TargetReliabilityNoCandidate", "ReviewRequired", "BoundedTargetReliability"}
    print(json.dumps({"reliability_root": str(root), "classification": result["classification"], "assessment_opened": result["assessment_opened"], "valid": valid}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
