"""Independent aggregate and raw-event validator for V1.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import custody_v1 as custody
import protocol_v1 as protocol
import registry_v1 as registry


def _no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise protocol.ProtocolError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _strict_line(line: str) -> Any:
    return json.loads(
        line,
        object_pairs_hook=_no_duplicate_pairs,
        parse_constant=lambda item: (_ for _ in ()).throw(
            protocol.ProtocolError(f"nonstandard JSON constant: {item}")
        ),
    )


def validate_run(
    aggregate: dict[str, Any],
    manifest: dict[str, Any],
    *,
    custody_root: Path,
    repository_root: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    if not custody.validate_root(custody_root, repository_root)["valid"]:
        errors.append("custody")
    expected_manifest = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if manifest.get("manifest_sha256") != protocol.digest_json(expected_manifest):
        errors.append("manifest_digest")
    try:
        raw_path = (custody_root / str(manifest["raw_relative_path"])).resolve()
        raw_path.relative_to((custody_root / "raw").resolve())
        if raw_path.is_symlink() or not raw_path.is_file():
            raise protocol.ProtocolError("raw event path invalid")
        if protocol.sha256_file(raw_path) != manifest.get("raw_sha256"):
            raise protocol.ProtocolError("raw event hash mismatch")
        events = [
            protocol.TraceEvent.from_dict(_strict_line(line))
            for line in raw_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        counts = aggregate["event_counts"]
        expectation = protocol.RunExpectation(
            generation_steps=int(aggregate["generation_steps"]),
            input_token_count=int(aggregate["input_token_count"]),
            module_input_paths=registry.expected_input_paths(),
            module_output_paths=registry.expected_output_paths(),
            attention_modules=registry.attention_paths(),
            interventions=int(counts["intervention"]),
            sae_feature_events=int(counts["sae_features"]),
            sae_reconstruction_events=int(counts["sae_reconstruction"]),
            causal_events=int(counts.get("feature_ablation", 0))
            + int(counts.get("feature_replacement", 0))
            + int(counts.get("activation_patch", 0))
            + int(counts.get("path_patch", 0)),
            graph_prediction_events=int(counts.get("output_metric", 0)),
        )
        recomputed = protocol.validate_event_stream(events, expectation)
        if recomputed != aggregate:
            errors.append("aggregate_recomputation")
        if len(events) != manifest.get("event_count"):
            errors.append("manifest_event_count")
        if recomputed.get("event_stream_sha256") != manifest.get("event_stream_sha256"):
            errors.append("manifest_stream_digest")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        errors.append(f"event_replay:{type(exc).__name__}:{exc}")
    try:
        protocol.reject_raw_fields(aggregate)
    except protocol.ProtocolError:
        errors.append("raw_aggregate_field")
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": aggregate.get("run_id"),
        "valid": not errors,
        "errors": errors,
        "aggregate_sha256": protocol.digest_json(aggregate),
        "manifest_sha256": manifest.get("manifest_sha256"),
        "validator": "validate_v1.validate_run",
    }
    return {**value, "receipt_sha256": protocol.digest_json(value)}


def validate_aggregate(aggregate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        protocol.reject_raw_fields(aggregate)
    except protocol.ProtocolError:
        errors.append("raw_aggregate_field")
    if aggregate.get("protocol") != protocol.PROTOCOL_ID:
        errors.append("protocol")
    if aggregate.get("state_slice") != protocol.STATE_SLICE:
        errors.append("state_slice")
    if aggregate.get("classification") not in {"HeldOutCausalFeatureEffectsAccepted", "NoCandidate"}:
        errors.append("classification")
    if aggregate.get("aggregate_sha256") != protocol.digest_json(
        {key: value for key, value in aggregate.items() if key != "aggregate_sha256"}
    ):
        errors.append("aggregate_digest")
    if aggregate.get("assessment_opened") is True and aggregate.get("review_accept_sha256") is None:
        errors.append("assessment_without_review_accept")
    if aggregate.get("raw_expiry_pending") is not False:
        errors.append("raw_expiry_pending")
    parity = aggregate.get("native_instrumented_parity")
    if isinstance(parity, dict) and parity.get("pass") is True and parity.get("sample_match") is not True:
        errors.append("parity_sample_mismatch")
    if aggregate.get("classification") == "HeldOutCausalFeatureEffectsAccepted":
        if aggregate.get("assessment_opened") is not True:
            errors.append("accepted_without_assessment")
        scrub = aggregate.get("assessment_causal_scrub")
        if not isinstance(scrub, dict) or scrub.get("pass") is not True:
            errors.append("accepted_without_scrub")
        if aggregate.get("claim_ceiling") != protocol.ASSESSMENT_CEILING:
            errors.append("accepted_claim_ceiling")
    elif aggregate.get("claim_ceiling") != protocol.QUALIFICATION_CEILING:
        errors.append("qualification_claim_ceiling")
    required = (
        "arms",
        "primary_effect",
        "prediction_lock",
        "statistics",
        "controls",
        "model",
        "runtime",
        "source",
        "module_registry",
        "corpus_manifest_sha256",
        "native_instrumented_parity",
        "reconstruction_gate",
        "power_gate",
        "fit_effect_summary",
        "tune_prediction_gate",
        "tune_effect_summary",
        "tune_controls",
        "assessment_causal_scrub",
        "assessment_controls",
        "raw_expiry_pending",
    )
    errors.extend(f"missing:{key}" for key in required if key not in aggregate)
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "valid": not errors,
        "errors": errors,
        "aggregate_sha256": protocol.digest_json(aggregate),
    }
    return {**value, "receipt_sha256": protocol.digest_json(value)}


def validate_raw_expired(root: Path, repository_root: Path) -> dict[str, Any]:
    receipt = protocol.custody_receipt(root, repository_root)
    raw_files = sorted(path.relative_to(root).as_posix() for path in (root / "raw").iterdir()) if (root / "raw").is_dir() else []
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "custody_valid": receipt["valid"],
        "raw_files": raw_files,
        "raw_root_empty": not raw_files,
        "valid": receipt["valid"] and not raw_files,
    }
    return {**value, "receipt_sha256": protocol.digest_json(value)}
