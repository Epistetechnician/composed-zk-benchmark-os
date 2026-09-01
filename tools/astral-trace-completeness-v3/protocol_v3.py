"""Frozen V3 contracts for model-matched transcoder quality.

State slice: astral-trace-completeness-gemma3-end-to-end-v3.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import dataclasses
from typing import Mapping, Sequence
from pathlib import Path
from typing import Any


STATE_SLICE = "astral-trace-completeness-gemma3-end-to-end-v3"
PROTOCOL_ID = "astral-trace-completeness-gemma3-v3.1"
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ROOT = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
CUSTODY_ROOT = Path("/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v3")
ASSET_REPOSITORY = "google/gemma-scope-2-1b-pt"
ASSET_REVISION = "b738dc06961818c011fb2e44a316352ca0f4e873"
ASSET_VARIANT = "transcoder_all/layer_12_width_16k_l0_small_affine"
ASSET_ROOT = CUSTODY_ROOT / "assets" / "gemma-scope-2-1b-pt"
CORPUS_ID = "gemma3-trace-causal-families-v3-2026-08-30"
QUALIFICATION_CEILING = "LocalDevelopmentGemma3EndToEndCausalTraceQualificationV3"
ASSESSMENT_CEILING = "LocalDevelopmentGemma3HeldOutCausalTraceAssessmentV3"
HIDDEN_WIDTH = 1152
FEATURE_WIDTH = 16384
RECONSTRUCTION_NMSE_MAX = 0.05
FEATURE_STABILITY_COSINE_MIN = 0.90
RAW_RETENTION_HOURS = 72

SUBROOTS = ("raw", "aggregate", "assets", "review", "receipts")
RAW_FIELD_FRAGMENTS = (
    "prompt",
    "text",
    "token_ids",
    "activation_values",
    "logits",
    "cache_values",
    "generated_output",
    "per_trial",
)


class ProtocolError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ProtocolError(f"value is not canonical JSON: {exc}") from exc


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json(path: Path) -> Any:
    def reject(value: str) -> None:
        raise ProtocolError(f"nonstandard JSON constant: {value}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject)


def tree_manifest(root: Path) -> dict[str, Any]:
    if not root.is_dir() or root.is_symlink():
        raise ProtocolError(f"invalid manifest root: {root}")
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ProtocolError(f"symlink rejected: {path}")
        if path.is_file():
            files.append({
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    if not files:
        raise ProtocolError(f"empty manifest root: {root}")
    value = {"root_name": root.name, "files": files}
    return {**value, "manifest_sha256": digest_json(value)}


def custody_receipt(root: Path = CUSTODY_ROOT, repository_root: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    repository_root = (repository_root or Path(__file__).resolve().parents[2]).resolve()
    errors = []
    try:
        root.relative_to(repository_root)
        errors.append("custody_inside_repository")
    except ValueError:
        pass
    if not root.is_dir() or root.is_symlink():
        errors.append("custody_root_missing_or_symlink")
    else:
        if stat.S_IMODE(root.stat().st_mode) != 0o700:
            errors.append("custody_root_mode")
        if root.stat().st_uid != os.getuid():
            errors.append("custody_root_owner")
    for name in SUBROOTS:
        path = root / name
        if not path.is_dir() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) != 0o700:
            errors.append(f"subroot:{name}")
    value = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "root": str(root),
        "owner_uid": os.getuid(),
        "mode": "0700",
        "valid": not errors,
        "errors": errors,
    }
    return {**value, "receipt_sha256": digest_json(value)}


def public_contract() -> dict[str, Any]:
    value = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "model_id": MODEL_ID,
        "asset_repository": ASSET_REPOSITORY,
        "asset_revision": ASSET_REVISION,
        "asset_variant": ASSET_VARIANT,
        "feature_width": FEATURE_WIDTH,
        "hidden_width": HIDDEN_WIDTH,
        "normalization_estimand": {
            "name": "pooled_global_centered_nmse",
            "formula": "sum((y_hat-y)^2) / sum((y-mean(y_all_coordinates))^2)",
            "coordinates": "all finite model-derived target rows and hidden coordinates in the fresh fit split",
            "mean_scope": "one scalar mean over every target coordinate in the fresh fit split",
            "aggregation": "pooled sums over every captured fit row; no per-row max, median, or selected-position exclusion",
            "zero_variance_rule": "reject",
            "nonfinite_rule": "reject",
        },
        "quality_gate": {
            "pooled_global_centered_nmse_max": RECONSTRUCTION_NMSE_MAX,
            "feature_width_exact": FEATURE_WIDTH,
            "input_width_exact": HIDDEN_WIDTH,
            "output_width_exact": HIDDEN_WIDTH,
            "asset_config_exact": True,
            "asset_parameter_keys_exact": True,
            "asset_examples_schema_exact": True,
            "all_fit_rows_used": True,
        },
        "assignment": "fixed official asset variant and every eligible row in the fresh fit split",
        "timing": "asset-integrity gate before model activation effects; pooled NMSE during qualification before assessment",
        "consistency": "same frozen model, transcoder, dtype conversion, capture boundaries, and formula for all fit rows",
        "positivity": "every finite fresh fit row must contribute; no row may be dropped",
        "interference": "one isolated model run per family with cache reset between trials",
        "assessment_opened": False,
    }
    return {**value, "contract_sha256": digest_json(value)}


def reject_raw_fields(value: dict[str, Any]) -> None:
    lowered = " ".join(value.keys()).lower()
    if any(fragment in lowered for fragment in RAW_FIELD_FRAGMENTS):
        raise ProtocolError("raw field name rejected from aggregate")


# The V2 event census is reused only as source-level infrastructure. The V3
# event type and validator wrapper below bind every event to this new slice.
_V2_ROOT = Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2"
if str(_V2_ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_V2_ROOT))
import protocol_v2 as _legacy_protocol

EVENT_KINDS = _legacy_protocol.EVENT_KINDS
RunExpectation = _legacy_protocol.RunExpectation


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


@dataclasses.dataclass(frozen=True)
class TraceEvent(_legacy_protocol.TraceEvent):
    protocol: str = PROTOCOL_ID
    state_slice: str = STATE_SLICE

    def validate(self) -> None:
        if self.protocol != PROTOCOL_ID or self.state_slice != STATE_SLICE:
            raise ProtocolError("event identity mismatch")
        if not self.run_id or not self.trial_id or self.sequence < 0 or self.kind not in EVENT_KINDS:
            raise ProtocolError("invalid event header")
        if any(value is not None and value < 0 for value in (self.step, self.token_index, self.layer_index, self.parent_sequence)):
            raise ProtocolError("negative event coordinate")
        if self.shape is not None and any(not isinstance(item, int) or item < 0 for item in self.shape):
            raise ProtocolError("invalid event shape")
        if self.value_sha256 is not None and (len(self.value_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.value_sha256)):
            raise ProtocolError("invalid value digest")
        if not all(isinstance(key, str) and _is_scalar(value) for key, value in self.metadata.items()):
            raise ProtocolError("event metadata must be scalar-only")
        lowered = " ".join((*self.metadata.keys(), self.module_path or "", self.state_slot or "")).lower()
        if any(fragment in lowered for fragment in RAW_FIELD_FRAGMENTS):
            raise ProtocolError("raw field name rejected")


def validate_event_stream(events: Sequence[TraceEvent], expectation: RunExpectation) -> dict[str, Any]:
    result = _legacy_protocol.validate_event_stream(events, expectation)
    return {
        **result,
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "module_registry_sha256": digest_json(
            {"inputs": list(expectation.module_input_paths), "outputs": list(expectation.module_output_paths)}
        ),
    }
