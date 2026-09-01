"""Fail-closed contracts for the Gemma 3 causal feature-effects slice.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import stat
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "astral-trace-completeness-gemma3-causal-feature-effects-v2"
PROTOCOL_ID = "astral-trace-completeness-gemma3-causal-feature-effects-v2.0"
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ROOT = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
CUSTODY_ROOT = Path(
    "/Users/shaanp/Documents/astral-custody/"
    "trace-completeness-gemma3-causal-feature-effects-v2"
)
ASSET_REPOSITORY = "google/gemma-scope-2-1b-pt"
ASSET_REVISION = "b738dc06961818c011fb2e44a316352ca0f4e873"
ASSET_VARIANT = "transcoder_all/layer_12_width_16k_l0_big_affine"
FEATURE_INPUT_PATH = "model.layers.12.pre_feedforward_layernorm"
FEATURE_OUTPUT_PATH = "model.layers.12.post_feedforward_layernorm"
FEATURE_WIDTH = 16_384
HIDDEN_WIDTH = 1_152
LAYER_COUNT = 26
CORPUS_ID = "gemma3-causal-feature-effects-cross-half-stability-v2-20260901"
CORPUS_SEED = 2026090101
FAMILY_COUNT = 96
SPLIT_SIZE = 32
FIT_HALF_SIZE = 16
FEATURE_SELECTION_COUNT = 4
FEATURE_STABILITY_TOP_K = 16
REPEAT_COUNT = 3
RAW_RETENTION_HOURS = 72
CONSTANT_FEATURE_VALUE = 1.0

# These digests are the exact V2 model, runtime, and asset identities. Each is
# bound again by a fresh external custody receipt for this campaign root.
MODEL_MANIFEST_SHA256 = "5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81"
RUNTIME_MANIFEST_SHA256 = "f9a7697c44765df350baabb9b62f2d83a21f883abdf8555db9bcc8c250814caa"
# These V2 identity digests are frozen only after fresh external custody and
# corpus generation. They are intentionally not imported from V1 scientific
# artifacts.
FRESH_ASSET_QC_SHA256 = "35760a5a4bc47ab3ee11d9082e629f560449644753a8924bda30050351ebc361"
CORPUS_MANIFEST_SHA256 = "3ad84978dd63c240dd242f1b594b0750285b449187365b1904c26ad34a6f6d00"
MODEL_BINDING_RECEIPT = CUSTODY_ROOT / "receipts" / "model-binding-v2.json"
RUNTIME_BINDING_RECEIPT = CUSTODY_ROOT / "receipts" / "runtime-binding-v2.json"
ASSET_BINDING_RECEIPT = CUSTODY_ROOT / "receipts" / "asset-qc-v2.json"
CORPUS_BINDING_RECEIPT = CUSTODY_ROOT / "receipts" / "corpus-custody-v2.json"
TRANSFER_BUCKET = "astral-trace-completeness-gemma3-causal-feature-effects-v2"
TRANSFER_PREFIXES = {
    "model": "model/",
    "asset": "asset/transcoder_all/layer_12_width_16k_l0_big_affine/",
    "source": "source/",
}
REQUIRED_RUNTIME_PAYLOAD = {
    "python": "3.14.5",
    "packages": {
        "circuit-tracer": "0.5.3.dev1+g6018ed8d3",
        "cryptography": "48.0.0",
        "nnsight": "0.6.1",
        "safetensors": "0.7.0",
        "torch": "2.12.0",
        "transformer-lens": "3.2.1",
        "transformers": "4.57.3",
    },
    "offline_execution": True,
}

QUALIFICATION_CEILING = "LocalDevelopmentGemma3CausalFeatureEffectsQualificationV2"
ASSESSMENT_CEILING = "LocalDevelopmentGemma3HeldOutCausalFeatureEffectsAssessmentV2"

NODE_PROVIDER = "GiveMeANode"
NODE_ALLOCATION_RECEIPT = CUSTODY_ROOT / "node" / "allocation-receipt.json"
NODE_ID = "3f4edebf-5601-4de3-be62-fdd87db72906"
HARD_SPEND_CEILING_USD: float | None = 50.0
OPERATOR_ID = "shaanp"
OPERATOR_HOST = "Shaans-MacBook-Pro"
REVIEWER_ROLE = "independent-causal-feature-effects-reviewer-v2"

PRIMARY_ALPHA = 0.05
PRIMARY_FEATURE_EFFECT_SIGN_MIN = 0.80
PRIMARY_PREDICTION_SIGN_MIN = 0.80
SCRUB_BALANCED_ACCURACY_MIN = 0.80
SCRUB_SHUFFLED_BALANCED_ACCURACY_MAX = 0.60
PARITY_MAX_ABS_DELTA = 1e-4
REPEAT_MAX_ABS_DELTA = 1e-5
NOOP_MAX_ABS_DELTA = 1e-5
EXACT_COPY_MAX_ABS_DELTA = 1e-5
NONZERO_EFFECT_MIN = 1e-5
OUTPUT_TV_MIN = 1e-3
RECONSTRUCTION_MAX_NMSE = 0.05
POWER_TARGET = 0.80
POWER_STANDARDIZED_EFFECT = 0.50
POWER_ICC = 0.50
POWER_SIMULATIONS = 10_000

INTERVENTION_KINDS = (
    "natural",
    "feature_ablation",
    "feature_replacement",
    "activation_patch",
    "path_patch",
    "noop",
    "exact_copy",
    "zero",
    "shuffled",
    "constant",
)
EVENT_KINDS = (
    "run_start",
    "generation_step_start",
    "input_token",
    "module_input",
    "module_output",
    "attention_score",
    "attention_pattern",
    "cache_read",
    "cache_write",
    "cache_transition",
    "rng_state",
    "intervention",
    "sae_features",
    "sae_reconstruction",
    "feature_ablation",
    "feature_replacement",
    "activation_patch",
    "path_patch",
    "output_distribution",
    "output_metric",
    "sampled_token",
    "behavioral_outcome",
    "generation_step_end",
    "run_end",
)
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
SUBROOTS = ("raw", "aggregate", "assets", "node", "review", "receipts")


class ProtocolError(ValueError):
    """Raised when a V2 contract or receipt is not admissible."""


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
            "utf-8"
        )
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
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    if not files:
        raise ProtocolError(f"empty manifest root: {root}")
    value = {"root_name": root.name, "files": files}
    return {**value, "manifest_sha256": digest_json(value)}


def custody_receipt(root: Path = CUSTODY_ROOT, repository_root: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    repository_root = (repository_root or Path(__file__).resolve().parents[2]).resolve()
    errors: list[str] = []
    try:
        root.relative_to(repository_root)
        errors.append("custody_inside_repository")
    except ValueError:
        pass
    if not root.is_dir() or root.is_symlink():
        errors.append("custody_root_missing_or_symlink")
    else:
        if root.name != CUSTODY_ROOT.name:
            errors.append("custody_root_name")
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


def binding_paths(root: Path = CUSTODY_ROOT) -> dict[str, Path]:
    return {
        "model": root / "receipts" / MODEL_BINDING_RECEIPT.name,
        "runtime": root / "receipts" / RUNTIME_BINDING_RECEIPT.name,
        "asset": root / "receipts" / ASSET_BINDING_RECEIPT.name,
        "corpus": root / "receipts" / CORPUS_BINDING_RECEIPT.name,
    }


def binding_digest_map(root: Path = CUSTODY_ROOT) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for name, path in binding_paths(root).items():
        if not path.is_file() or path.is_symlink():
            result[name] = None
            continue
        try:
            value = strict_json(path)
        except (OSError, ProtocolError):
            result[name] = None
            continue
        result[name] = value.get("receipt_sha256") if isinstance(value, dict) else None
    return result


def _load_binding(path: Path, name: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ProtocolError(f"V2 {name} binding is missing")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ProtocolError(f"V2 {name} binding mode is not 0600")
    value = strict_json(path)
    if not isinstance(value, dict):
        raise ProtocolError(f"V2 {name} binding is not an object")
    unsigned = {key: child for key, child in value.items() if key != "receipt_sha256"}
    if value.get("protocol") != PROTOCOL_ID or value.get("state_slice") != STATE_SLICE:
        raise ProtocolError(f"V2 {name} binding identity mismatch")
    if value.get("binding_type") != name:
        raise ProtocolError(f"V2 {name} binding type mismatch")
    if value.get("receipt_sha256") != digest_json(unsigned):
        raise ProtocolError(f"V2 {name} binding digest mismatch")
    return value


def validate_external_bindings(root: Path = CUSTODY_ROOT, packet_value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve()
    bindings: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for name, path in binding_paths(root).items():
        try:
            bindings[name] = _load_binding(path, name)
        except (OSError, ProtocolError) as exc:
            errors.append(str(exc))
    if not errors:
        model_payload = bindings["model"].get("payload", {})
        model_manifest = model_payload.get("manifest", {})
        if model_payload.get("model_id") != MODEL_ID or model_payload.get("manifest_sha256") != MODEL_MANIFEST_SHA256:
            errors.append("V2 model binding does not match the frozen model identity")
        if model_manifest.get("manifest_sha256") != MODEL_MANIFEST_SHA256:
            errors.append("V2 model tree manifest digest is not frozen")

        runtime_payload = bindings["runtime"].get("payload", {})
        if runtime_payload.get("runtime_manifest_sha256") != RUNTIME_MANIFEST_SHA256:
            errors.append("V2 runtime binding digest is not frozen")
        expected_runtime = {
            **REQUIRED_RUNTIME_PAYLOAD,
            "manifest_sha256": RUNTIME_MANIFEST_SHA256,
        }
        if runtime_payload.get("runtime") != expected_runtime:
            errors.append("V2 runtime binding payload is not the frozen runtime")

        asset_payload = bindings["asset"].get("payload", {})
        if asset_payload.get("asset_qc_sha256") != FRESH_ASSET_QC_SHA256:
            errors.append("V2 asset QC digest is not frozen")
        asset_qc = {
            key: value
            for key, value in asset_payload.items()
            if key not in {"asset_qc_sha256", "transfer"}
        }
        if asset_payload.get("asset_qc_sha256") != digest_json(asset_qc):
            errors.append("V2 asset QC payload digest is malformed")
        if (
            asset_payload.get("asset_repository") != ASSET_REPOSITORY
            or asset_payload.get("asset_revision") != ASSET_REVISION
            or asset_payload.get("asset_variant") != ASSET_VARIANT
            or asset_payload.get("hidden_width") != HIDDEN_WIDTH
            or asset_payload.get("feature_width") != FEATURE_WIDTH
        ):
            errors.append("V2 asset binding identity mismatch")

        corpus_payload = bindings["corpus"].get("payload", {})
        if (
            corpus_payload.get("corpus_id") != CORPUS_ID
            or corpus_payload.get("manifest_sha256") != CORPUS_MANIFEST_SHA256
            or corpus_payload.get("family_count") != FAMILY_COUNT
        ):
            errors.append("V2 corpus custody binding does not match the frozen corpus")

    digests = {name: value.get("receipt_sha256") for name, value in bindings.items()}
    if packet_value is not None:
        expected = packet_value.get("external_binding_digests")
        if expected != digests:
            errors.append("packet external binding digests do not match custody")
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "root": str(root),
        "digests": digests,
        "valid": not errors,
        "errors": errors,
    }


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


@dataclasses.dataclass(frozen=True)
class TraceEvent:
    run_id: str
    trial_id: str
    sequence: int
    kind: str
    step: int | None = None
    token_index: int | None = None
    layer_index: int | None = None
    module_path: str | None = None
    state_slot: str | None = None
    shape: tuple[int, ...] | None = None
    dtype: str | None = None
    value_sha256: str | None = None
    parent_sequence: int | None = None
    metadata: Mapping[str, Any] = dataclasses.field(default_factory=dict)
    protocol: str = PROTOCOL_ID
    state_slice: str = STATE_SLICE

    def validate(self) -> None:
        if self.protocol != PROTOCOL_ID or self.state_slice != STATE_SLICE:
            raise ProtocolError("event identity mismatch")
        if not self.run_id or not self.trial_id or self.sequence < 0 or self.kind not in EVENT_KINDS:
            raise ProtocolError("invalid event header")
        if any(
            value is not None and value < 0
            for value in (self.step, self.token_index, self.layer_index, self.parent_sequence)
        ):
            raise ProtocolError("negative event coordinate")
        if self.shape is not None and any(
            not isinstance(item, int) or item < 0 for item in self.shape
        ):
            raise ProtocolError("invalid event shape")
        if self.value_sha256 is not None and (
            len(self.value_sha256) != 64
            or any(ch not in "0123456789abcdef" for ch in self.value_sha256)
        ):
            raise ProtocolError("invalid value digest")
        if not all(isinstance(key, str) and _is_scalar(value) for key, value in self.metadata.items()):
            raise ProtocolError("event metadata must be scalar-only")
        lowered = " ".join((*self.metadata.keys(), self.module_path or "", self.state_slot or "")).lower()
        if any(fragment in lowered for fragment in RAW_FIELD_FRAGMENTS):
            raise ProtocolError("raw field name rejected")
        if self.kind == "intervention":
            intervention_kind = self.metadata.get("intervention_kind")
            if intervention_kind not in INTERVENTION_KINDS or intervention_kind == "natural":
                raise ProtocolError("typed intervention kind is missing")
            operator = self.metadata.get("operator")
            expected_operator = f"exact-{intervention_kind}-v2"
            if operator != expected_operator:
                raise ProtocolError("intervention operator is not the frozen typed operator")
            operator_digest = self.metadata.get("operator_digest")
            expected_digest = digest_json(
                {
                    "operator": expected_operator,
                    "module_path": self.module_path,
                    "step": self.step,
                    "feature_index": self.metadata.get("feature_index"),
                    "path_id": self.metadata.get("path_id"),
                }
            )
            if operator_digest != expected_digest:
                raise ProtocolError("intervention operator digest is malformed")
            feature_kinds = {"feature_ablation", "feature_replacement", "shuffled", "constant"}
            feature_index = self.metadata.get("feature_index")
            if intervention_kind in feature_kinds and (
                not isinstance(feature_index, int) or not 0 <= feature_index < FEATURE_WIDTH
            ):
                raise ProtocolError("feature intervention index is invalid")
            if intervention_kind == "path_patch" and not isinstance(self.metadata.get("path_id"), str):
                raise ProtocolError("path intervention path id is missing")
            if intervention_kind not in {"noop", "zero"} and not isinstance(
                self.metadata.get("donor_trial_id"), str
            ):
                raise ProtocolError("intervention donor trial identity is missing")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = dataclasses.asdict(self)
        value["metadata"] = dict(self.metadata)
        return {**value, "event_sha256": digest_json(value)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TraceEvent":
        copy = dict(value)
        expected = copy.pop("event_sha256", None)
        event = cls(**copy)
        event.validate()
        if expected != digest_json(dataclasses.asdict(event)):
            raise ProtocolError("event digest mismatch")
        return event


@dataclasses.dataclass(frozen=True)
class RunExpectation:
    generation_steps: int
    input_token_count: int
    module_input_paths: tuple[str, ...]
    module_output_paths: tuple[str, ...]
    attention_modules: tuple[str, ...]
    cache_updates_per_step: int = LAYER_COUNT
    interventions: int = 0
    sae_feature_events: int = 0
    sae_reconstruction_events: int = 0
    causal_events: int = 0
    graph_prediction_events: int = 0

    def validate(self) -> None:
        if self.generation_steps <= 0 or self.input_token_count <= 0:
            raise ProtocolError("run expectation requires tokens and generation steps")
        if not self.module_input_paths:
            raise ProtocolError("module registry is empty")
        if Counter(self.module_output_paths) != Counter(self.module_input_paths):
            raise ProtocolError("module output registry differs from input registry")
        if len(set(self.attention_modules)) != len(self.attention_modules):
            raise ProtocolError("attention registry is duplicated")
        if any(path not in self.module_input_paths for path in self.attention_modules):
            raise ProtocolError("attention path missing from module registry")
        values = (
            self.cache_updates_per_step,
            self.interventions,
            self.sae_feature_events,
            self.sae_reconstruction_events,
            self.causal_events,
            self.graph_prediction_events,
        )
        if min(values) < 0:
            raise ProtocolError("negative expected event count")

    def counts(self) -> dict[str, int]:
        self.validate()
        module_calls = len(self.module_input_paths) * self.generation_steps
        attention_calls = len(self.attention_modules) * self.generation_steps
        cache_updates = self.cache_updates_per_step * self.generation_steps
        return {
            "run_start": 1,
            "generation_step_start": self.generation_steps,
            "input_token": self.input_token_count + self.generation_steps - 1,
            "module_input": module_calls,
            "module_output": module_calls,
            "attention_score": attention_calls,
            "attention_pattern": attention_calls,
            "cache_read": self.generation_steps,
            "cache_write": cache_updates,
            "cache_transition": cache_updates,
            "rng_state": self.generation_steps,
            "intervention": self.interventions,
            "sae_features": self.sae_feature_events,
            "sae_reconstruction": self.sae_reconstruction_events,
            "feature_ablation": 0,
            "feature_replacement": 0,
            "activation_patch": 0,
            "path_patch": 0,
            "output_distribution": self.generation_steps,
            "output_metric": self.graph_prediction_events,
            "sampled_token": self.generation_steps,
            "behavioral_outcome": self.generation_steps,
            "generation_step_end": self.generation_steps,
            "run_end": 1,
        }

    def digest(self) -> str:
        return digest_json(dataclasses.asdict(self))


def validate_event_stream(events: Sequence[TraceEvent], expectation: RunExpectation) -> dict[str, Any]:
    expectation.validate()
    if not events:
        raise ProtocolError("empty event stream")
    for index, event in enumerate(events):
        event.validate()
        if event.sequence != index:
            raise ProtocolError("event sequence is not contiguous")
        if event.run_id != events[0].run_id or event.trial_id != events[0].trial_id:
            raise ProtocolError("mixed run or trial identity")
    if events[0].kind != "run_start" or events[-1].kind != "run_end":
        raise ProtocolError("run boundaries are incomplete")
    counts = Counter(event.kind for event in events)
    expected = expectation.counts()
    observed = {kind: counts.get(kind, 0) for kind in EVENT_KINDS}
    if observed != expected:
        differences = {
            kind: {"expected": expected[kind], "observed": observed[kind]}
            for kind in EVENT_KINDS
            if observed[kind] != expected[kind]
        }
        raise ProtocolError(f"exact event census mismatch: {differences}")
    for step in range(expectation.generation_steps):
        step_events = [event for event in events if event.step == step]
        if (
            not step_events
            or step_events[0].kind != "generation_step_start"
            or step_events[-1].kind != "generation_step_end"
        ):
            raise ProtocolError("generation step boundaries are incomplete")
        paths_in = [event.module_path for event in step_events if event.kind == "module_input"]
        paths_out = [event.module_path for event in step_events if event.kind == "module_output"]
        if paths_in != list(expectation.module_input_paths) or paths_out != list(expectation.module_output_paths):
            raise ProtocolError("module registry coverage or nesting mismatch")
        attention_paths = [event.module_path for event in step_events if event.kind == "attention_pattern"]
        score_paths = [event.module_path for event in step_events if event.kind == "attention_score"]
        if attention_paths != list(expectation.attention_modules) or score_paths != list(expectation.attention_modules):
            raise ProtocolError("attention coverage mismatch")
        if any(
            event.value_sha256 is None
            for event in step_events
            if event.kind not in {"generation_step_start", "generation_step_end"}
        ):
            raise ProtocolError("digest-bearing event is missing a digest")
    cache_writes = [event for event in events if event.kind == "cache_write"]
    transitions = [event for event in events if event.kind == "cache_transition"]
    if [(event.step, event.layer_index, event.state_slot) for event in cache_writes] != [
        (event.step, event.layer_index, event.state_slot) for event in transitions
    ]:
        raise ProtocolError("cache writes and transitions are not paired")
    stream_digest = digest_json([event.to_dict() for event in events])
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "run_id": events[0].run_id,
        "trial_id": events[0].trial_id,
        "event_count": len(events),
        "event_counts": expected,
        "expectation_sha256": expectation.digest(),
        "module_registry_sha256": digest_json(
            {"inputs": list(expectation.module_input_paths), "outputs": list(expectation.module_output_paths)}
        ),
        "event_stream_sha256": stream_digest,
        "missing_event_count": 0,
        "duplicate_event_count": 0,
        "unaccounted_state_transition_count": 0,
        "behavior_link_missing_count": 0,
        "generation_steps": expectation.generation_steps,
        "input_token_count": expectation.input_token_count,
        "aggregate_only": True,
        "raw_events_retained": False,
    }


def public_contract() -> dict[str, Any]:
    value = {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": QUALIFICATION_CEILING,
        "assessment_ceiling_after_accept": ASSESSMENT_CEILING,
        "model": {
            "id": MODEL_ID,
            "root": str(MODEL_ROOT),
            "manifest_sha256": MODEL_MANIFEST_SHA256,
        },
        "runtime": {
            "required_manifest_sha256": RUNTIME_MANIFEST_SHA256,
            "offline_model_execution": True,
            "native_backend": "PyTorch/Transformers eager attention",
        },
        "feature_asset": {
            "repository": ASSET_REPOSITORY,
            "revision": ASSET_REVISION,
            "variant": ASSET_VARIANT,
            "hidden_width": HIDDEN_WIDTH,
            "feature_width": FEATURE_WIDTH,
            "fresh_v2_slice_qc_required": True,
            "prior_scientific_artifacts_as_inputs": False,
        },
        "roles": {
            "operator": OPERATOR_ID,
            "operator_host": OPERATOR_HOST,
            "runner": "tools/astral-trace-completeness-gemma3-causal-feature-effects-v2/run_v2.py",
            "validator": "tools/astral-trace-completeness-gemma3-causal-feature-effects-v2/validate_v2_slice.py",
            "reviewer_role": REVIEWER_ROLE,
        },
        "node": {
            "provider": NODE_PROVIDER,
            "allocation_receipt": str(NODE_ALLOCATION_RECEIPT),
            "node_id": NODE_ID,
            "hard_spend_ceiling_usd": HARD_SPEND_CEILING_USD,
            "required_before_submission": True,
        },
        "corpus": {
            "id": CORPUS_ID,
            "seed": CORPUS_SEED,
            "family_count": FAMILY_COUNT,
            "split_counts": {"fit": SPLIT_SIZE, "tune": SPLIT_SIZE, "assessment": SPLIT_SIZE},
            "fresh_from_v1_and_v4": True,
            "feature_stability": {
                "estimand": "cross-half replication of top-feature activation rank within the fit split",
                "discovery_half_families": FIT_HALF_SIZE,
                "replication_half_families": FIT_HALF_SIZE,
                "top_k_per_half": FEATURE_STABILITY_TOP_K,
                "minimum_intersection": FEATURE_SELECTION_COUNT,
                "selection": "select exactly four features from the intersection by pooled absolute final-position activation score; otherwise NoCandidate",
                "v1_scientific_inputs": False,
            },
            "answer_token_contract": "clean and corrupted decimal answers are distinct values in 0..9; the bound Gemma tokenizer must encode each as one token",
            "raw_prompt_retention": "external custody only",
        },
        "estimand": {
            "primary": "paired mean change in target-minus-distractor logit margin under feature ablation versus natural execution",
            "secondary": "paired total-variation change in output distribution plus exact feature replacement, activation patch, and path patch effects",
            "assignment": "fixed-seed balanced arm order randomized within each family; every eligible family receives every declared arm",
            "timing": "intervention is applied at generation step 0 after the declared recipient module output and before the unchanged downstream pass",
            "consistency": "one observed run equals the potential outcome under its exact frozen model, feature transform, donor, dtype, and downstream computation",
            "positivity": "all finite sealed families execute every arm and all three repeats; zero missing cells are permitted",
            "interference": "one family per isolated run, cache reset between trials, no shared mutable model or adapter state",
        },
        "interchange_operator": {
            "feature_ablation": "h'_p(t)=h_p(t)+D(E(x),x)-D(E(x with feature j=0),x) at p=layer12 post-feedforward output",
            "feature_replacement": "h'_p(t)=h_p(t)+D(E(x),x with feature j replaced by locked donor value)-D(E(x),x)",
            "activation_patch": "h'_p(t)=h_p^donor(t) for an exact-shape same-position donor run",
            "path_patch": "apply the same exact-shape replacement over the frozen path tuple layer12.post_feedforward -> output_distribution",
            "constant_feature_value": CONSTANT_FEATURE_VALUE,
            "controls": "noop, exact-copy, zero, shuffled donor, constant donor, activation-only donor, and text-only donor",
        },
        "thresholds": {
            "primary_alpha": PRIMARY_ALPHA,
            "primary_feature_effect_sign_agreement_min": PRIMARY_FEATURE_EFFECT_SIGN_MIN,
            "prediction_sign_agreement_min": PRIMARY_PREDICTION_SIGN_MIN,
            "scrubbing_balanced_accuracy_min": SCRUB_BALANCED_ACCURACY_MIN,
            "scrubbing_shuffled_balanced_accuracy_max": SCRUB_SHUFFLED_BALANCED_ACCURACY_MAX,
            "native_parity_max_abs_logit_delta": PARITY_MAX_ABS_DELTA,
            "repeat_max_abs_logit_delta": REPEAT_MAX_ABS_DELTA,
            "noop_max_abs_logit_delta": NOOP_MAX_ABS_DELTA,
            "exact_copy_max_abs_logit_delta": EXACT_COPY_MAX_ABS_DELTA,
            "reconstruction_nmse_max": RECONSTRUCTION_MAX_NMSE,
            "nonzero_effect_min": NONZERO_EFFECT_MIN,
            "output_tv_min": OUTPUT_TV_MIN,
        },
        "statistics": {
            "uncertainty": "10000 fixed-seed bootstrap resamples over family IDs, 95 percent percentile interval",
            "multiplicity": "Holm correction over four selected features for the primary ablation family; controls and secondary effects are separately labeled",
            "power": {
                "target": POWER_TARGET,
                "standardized_paired_effect": POWER_STANDARDIZED_EFFECT,
                "icc": POWER_ICC,
                "assessment_families": SPLIT_SIZE,
                "repeats_per_cell": REPEAT_COUNT,
                "simulations": POWER_SIMULATIONS,
                "rule": "power simulation must pass before assessment effects; otherwise NoCandidate",
            },
            "repeats": REPEAT_COUNT,
            "missingness": "fail closed; no imputation, replacement, or selected-position exclusion",
            "attrition": "zero after corpus sealing; any failed family, arm, repeat, or event accounting closes the slice",
        },
        "custody": {
            "root_name": CUSTODY_ROOT.name,
            "identity": "external-owner-only-ephemeral-per-runner-root",
            "mode": "0700 owner-only",
            "raw_retention_hours": RAW_RETENTION_HOURS,
            "raw_allowed": "prompts, token IDs, activations, logits, cache/state payloads, and per-trial outcomes only below external raw root",
            "publication": "aggregate results and digests only after independent replay and raw deletion",
        },
        "lock_order": [
            "source/runtime/model/asset/corpus/custody digests",
            "fit feature selection",
            "fit causal effects",
            "tune graph prediction and prediction lock",
            "independent signed ACCEPT",
            "fresh held-out causal scrubbing",
            "assessment aggregate publication",
        ],
        "assessment_opened": False,
        "execution_authorization": "AUTHORIZED_FOR_IMPLEMENTATION_AND_QUALIFICATION_ONLY",
    }
    return {**value, "contract_sha256": digest_json(value)}


def reject_raw_fields(value: Mapping[str, Any]) -> None:
    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                lowered = str(key).lower()
                if any(fragment in lowered for fragment in RAW_FIELD_FRAGMENTS):
                    raise ProtocolError("raw field name rejected from aggregate")
                walk(child)
        elif isinstance(item, (tuple, list)):
            for child in item:
                walk(child)

    walk(value)


def require_node_admission(node_receipt: Mapping[str, Any], *, spend_ceiling_usd: float) -> None:
    if node_receipt.get("provider") != NODE_PROVIDER:
        raise ProtocolError("GiveMeANode provider identity is missing")
    if node_receipt.get("state_slice") != STATE_SLICE:
        raise ProtocolError("node receipt state-slice identity is missing")
    if node_receipt.get("mission") != STATE_SLICE:
        raise ProtocolError("node receipt mission is not the V2 state slice")
    if node_receipt.get("node_id") != NODE_ID:
        raise ProtocolError("GiveMeANode node_id is not the packet-bound node")
    if node_receipt.get("execution_authorized") is not True:
        raise ProtocolError("node receipt does not authorize execution")
    if not isinstance(spend_ceiling_usd, (int, float)) or isinstance(spend_ceiling_usd, bool) or not math.isfinite(spend_ceiling_usd) or spend_ceiling_usd <= 0:
        raise ProtocolError("hard USD spend ceiling must be positive")
    if spend_ceiling_usd != HARD_SPEND_CEILING_USD:
        raise ProtocolError("requested spend ceiling is not the frozen V2 ceiling")
    node_ceiling = node_receipt.get("hard_spend_ceiling_usd")
    if not isinstance(node_ceiling, (int, float)) or isinstance(node_ceiling, bool) or not math.isfinite(node_ceiling) or node_ceiling <= 0:
        raise ProtocolError("node receipt hard USD spend ceiling is invalid")
    if node_ceiling != HARD_SPEND_CEILING_USD:
        raise ProtocolError("node receipt spend ceiling is not the frozen V2 ceiling")
    if spend_ceiling_usd > node_ceiling:
        raise ProtocolError("requested spend ceiling exceeds the node receipt ceiling")


def require_external_admission(node_receipt: Mapping[str, Any], reviewer_receipt: Mapping[str, Any], *, spend_ceiling_usd: float) -> None:
    require_node_admission(node_receipt, spend_ceiling_usd=spend_ceiling_usd)
    if reviewer_receipt.get("verdict") != "ACCEPT":
        raise ProtocolError("independent signed ACCEPT is missing")
    if reviewer_receipt.get("reviewer_role") != REVIEWER_ROLE:
        raise ProtocolError("operator cannot serve as independent reviewer")
    if not isinstance(reviewer_receipt.get("packet_sha256"), str) or len(reviewer_receipt["packet_sha256"]) != 64:
        raise ProtocolError("review receipt is not packet-bound")
    if reviewer_receipt.get("signature", {}).get("algorithm") != "ed25519":
        raise ProtocolError("review receipt signature is not Ed25519")
