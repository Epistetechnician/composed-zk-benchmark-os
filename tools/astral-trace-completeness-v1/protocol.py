"""Fail-closed contract and typed event schema for trace completeness V1.

State slice: astral-trace-completeness-native-instrument-v1.

This module is deliberately dependency-free.  It defines the public event
envelope and aggregate-only checks; it does not load a model, access a cache,
or write raw activations.  Runtime adapters must provide the declared native
boundaries and are rejected when the event census is incomplete.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PROTOCOL_ID = "astral-trace-completeness-native-instrument-v1"
STATE_SLICE = PROTOCOL_ID
CLAIM_CEILING = "LocalDevelopmentTraceCompletenessInstrumentFeasibilityOnly"
AUTHORIZATION_DATE = "2026-08-30"
AUTHORIZATION_SCOPE = "contract_and_hermetic_fixture_only"

MODEL_ID = "Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ROOT = "/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit"
MODEL_ARCHITECTURE = "Qwen3_5MoeForConditionalGeneration"
RUNTIME_CONTRACT = {
    "python": "3.14.5",
    "mlx": "0.31.2",
    "mlx_lm": "0.31.3",
}

OPERATOR_ID = "exact-activation-and-path-interchange-v1"
OPERATOR_SEMANTICS = (
    "replace the declared recipient boundary state with the donor state at the "
    "same token/layer/module/state-slot key, emit an intervention event before "
    "the next downstream consumer, and compare the locked output event"
)
RUNNER_ID = "NativeModelAdapter.execute"
VALIDATOR_ID = "validate_trace_bundle_v1.validate_aggregate_file"

CUSTODY_ROOT = "/Users/shaanp/Documents/astral-custody/trace-completeness-native-instrument-v1"
RAW_CUSTODY_ROOT = f"{CUSTODY_ROOT}/raw"
AGGREGATE_CUSTODY_ROOT = f"{CUSTODY_ROOT}/aggregate"
RAW_RETENTION_HOURS = 72
RAW_RETENTION_POLICY = (
    "raw event payloads may exist only below the external 0700 custody root; "
    "delete within 72 hours after validation; never commit or publish raw "
    "tokens, activations, logits, prompts, or transcripts"
)

FRESH_CORPUS_ID = "trace-completeness-deterministic-fixture-corpus-v1-2026-08-30"
FRESH_CORPUS_DESCRIPTION = (
    "Eight deterministic non-semantic event fixtures generated from the V1 "
    "fixture seed; this is an instrument contract corpus, not a model-bearing "
    "assessment corpus"
)
FRESH_CORPUS_RETENTION = "fixture identifiers and aggregate digests retained; no raw payload retained"

EVENT_KINDS = (
    "run_start",
    "token",
    "layer_enter",
    "layer_output",
    "module_enter",
    "module_output",
    "cache_read",
    "cache_write",
    "state_transition",
    "intervention",
    "module_exit",
    "layer_exit",
    "output",
    "run_end",
)
EVENT_FIELDS = frozenset(
    {
        "protocol",
        "state_slice",
        "run_id",
        "sequence",
        "event_id",
        "kind",
        "token_index",
        "layer_index",
        "module_path",
        "state_slot",
        "value_digest",
        "shape",
        "dtype",
        "parent_sequence",
        "metadata",
    }
)
RAW_FIELD_MARKERS = (
    "prompt",
    "prompts",
    "tokens",
    "activation",
    "activations",
    "logit",
    "logits",
    "trace",
    "traces",
    "transcript",
    "payload",
    "secret",
    "credential",
)
RAW_METADATA_KEY_MARKERS = (
    "prompt",
    "activation",
    "logit",
    "trace",
    "transcript",
    "payload",
    "secret",
    "credential",
)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

# Qualification gates.  These are fixed before any model-bearing execution.
MAX_NATIVE_PARITY_ABS_LOGIT_DELTA = 1e-4
MAX_DETERMINISTIC_REPEAT_ABS_LOGIT_DELTA = 1e-5
MAX_NOOP_IDENTITY_ABS_LOGIT_DELTA = 1e-5
MAX_EVENT_MISSINGNESS = 0.0
MAX_EVENT_DUPLICATION = 0.0
MAX_UNACCOUNTED_STATE_TRANSITIONS = 0
MAX_OUTPUT_MISSINGNESS = 0.0

# Scientific gates are specified but sealed from this instrument-only slice.
SAE_MAX_NORMALIZED_RECONSTRUCTION_MSE = 0.05
SAE_MIN_FEATURE_STABILITY_COSINE = 0.90
SAE_MIN_ABLATION_SIGN_AGREEMENT = 0.80
SAE_MIN_FEATURE_TO_LOGIT_SIGN_AGREEMENT = 0.80
GRAPH_MIN_HELD_OUT_SCRUB_BALANCED_ACCURACY = 0.80
GRAPH_MIN_SCRUB_MARGIN_OVER_SHUFFLE = 0.10
STATISTICAL_ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260830
POWER_TARGET = 0.90
POWER_STANDARDIZED_EFFECT = 0.35
ICC_SENSITIVITY = (0.10, 0.30)
REPEATS_REQUIRED = 2
MAX_ASSESSMENT_ATTRITION = 0.05

CONTROLS = (
    "native_no_trace",
    "instrumented_noop",
    "zero_replacement",
    "shuffled_donor",
    "constant_replacement",
    "matched_norm",
    "activation_only",
    "text_only",
    "access_null",
)
FALSIFIERS = (
    "native_parity_failure",
    "nonzero_replacement_no_reach",
    "no_op_identity_failure",
    "event_count_mismatch",
    "unpaired_cache_transition",
    "unpaired_state_transition",
    "missing_output_event",
    "raw_field_in_aggregate",
    "prediction_lock_after_effect",
)


class ProtocolError(ValueError):
    """Raised when a V1 contract or event-accounting invariant fails."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path: Path) -> Any:
    def reject_constant(value: str) -> Any:
        raise ProtocolError(f"non-standard JSON constant: {value}")

    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProtocolError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_external(path: Path, repository_root: Path) -> None:
    resolved = path.resolve()
    repository = repository_root.resolve()
    if resolved == repository or repository in resolved.parents:
        raise ProtocolError(f"path must be repository-external: {resolved}")


def _validate_digest(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not DIGEST_RE.fullmatch(value):
        raise ProtocolError(f"{field_name} must be a lowercase SHA-256 digest")


def _validate_metadata(value: Mapping[str, Any]) -> None:
    for key, item in value.items():
        if not isinstance(key, str) or any(marker in key.lower() for marker in RAW_METADATA_KEY_MARKERS):
            raise ProtocolError(f"raw or sensitive metadata key: {key!r}")
        if not isinstance(item, (str, int, float, bool)) and item is not None:
            raise ProtocolError(f"metadata must contain scalar values: {key!r}")


@dataclass(frozen=True)
class TraceEvent:
    """Public typed event envelope; raw values are intentionally absent."""

    run_id: str
    sequence: int
    kind: str
    token_index: int | None = None
    layer_index: int | None = None
    module_path: str | None = None
    state_slot: str | None = None
    value_digest: str | None = None
    shape: tuple[int, ...] | None = None
    dtype: str | None = None
    parent_sequence: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    protocol: str = PROTOCOL_ID
    state_slice: str = STATE_SLICE
    event_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.protocol != PROTOCOL_ID or self.state_slice != STATE_SLICE:
            raise ProtocolError("event protocol/state-slice identity mismatch")
        if not self.run_id or self.sequence < 0 or self.kind not in EVENT_KINDS:
            raise ProtocolError("invalid event identity or kind")
        if self.token_index is not None and self.token_index < 0:
            raise ProtocolError("token index must be nonnegative")
        if self.layer_index is not None and self.layer_index < 0:
            raise ProtocolError("layer index must be nonnegative")
        if self.parent_sequence is not None and self.parent_sequence < 0:
            raise ProtocolError("parent sequence must be nonnegative")
        if self.value_digest is not None:
            _validate_digest(self.value_digest, "value_digest")
        if self.kind in {
            "token",
            "layer_enter",
            "layer_output",
            "module_enter",
            "module_output",
            "cache_read",
            "cache_write",
            "state_transition",
            "intervention",
            "output",
        } and self.value_digest is None:
            raise ProtocolError(f"{self.kind} event requires a value digest")
        if self.shape is not None and any(not isinstance(item, int) or item < 0 for item in self.shape):
            raise ProtocolError("shape must contain nonnegative integers")
        if not isinstance(self.metadata, Mapping):
            raise ProtocolError("metadata must be a mapping")
        _validate_metadata(self.metadata)
        object.__setattr__(self, "event_id", canonical_digest(self._identity_dict()))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "protocol": self.protocol,
            "state_slice": self.state_slice,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "kind": self.kind,
            "token_index": self.token_index,
            "layer_index": self.layer_index,
            "module_path": self.module_path,
            "state_slot": self.state_slot,
            "value_digest": self.value_digest,
            "shape": list(self.shape) if self.shape is not None else None,
            "dtype": self.dtype,
            "parent_sequence": self.parent_sequence,
            "metadata": dict(self.metadata),
        }

    def to_dict(self) -> dict[str, Any]:
        value = self._identity_dict()
        value["event_id"] = self.event_id
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TraceEvent":
        if set(value) != EVENT_FIELDS:
            raise ProtocolError("event schema mismatch")
        event = cls(
            run_id=value["run_id"],
            sequence=value["sequence"],
            kind=value["kind"],
            token_index=value["token_index"],
            layer_index=value["layer_index"],
            module_path=value["module_path"],
            state_slot=value["state_slot"],
            value_digest=value["value_digest"],
            shape=tuple(value["shape"]) if value["shape"] is not None else None,
            dtype=value["dtype"],
            parent_sequence=value["parent_sequence"],
            metadata=value["metadata"],
            protocol=value["protocol"],
            state_slice=value["state_slice"],
        )
        if event.event_id != value["event_id"]:
            raise ProtocolError("event identity digest mismatch")
        return event


@dataclass(frozen=True)
class EventExpectation:
    """Exact run census supplied by the native runtime manifest."""

    token_count: int
    layer_count: int
    module_count: int
    cache_read_count: int
    cache_write_count: int
    state_transition_count: int
    intervention_count: int
    output_count: int = 1
    expected_module_paths: tuple[tuple[int, str], ...] = ()

    def counts(self) -> dict[str, int]:
        return {
            "run_start": 1,
            "token": self.token_count,
            "layer_enter": self.layer_count,
            "layer_output": self.layer_count,
            "module_enter": self.module_count,
            "module_output": self.module_count,
            "cache_read": self.cache_read_count,
            "cache_write": self.cache_write_count,
            "state_transition": self.state_transition_count,
            "intervention": self.intervention_count,
            "module_exit": self.module_count,
            "layer_exit": self.layer_count,
            "output": self.output_count,
            "run_end": 1,
        }

    def __post_init__(self) -> None:
        if any(value < 0 for value in self.counts().values()):
            raise ProtocolError("event expectation counts must be nonnegative")
        if self.token_count == 0 or self.layer_count == 0 or self.module_count == 0:
            raise ProtocolError("native qualification requires token, layer, and module events")
        if self.output_count != 1:
            raise ProtocolError("exactly one output event is required per run")
        if self.expected_module_paths and len(self.expected_module_paths) != self.module_count:
            raise ProtocolError("module registry length differs from module count")


def protocol_manifest() -> dict[str, Any]:
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "authorization": {
            "date": AUTHORIZATION_DATE,
            "scope": AUTHORIZATION_SCOPE,
            "model_execution_authorized": False,
            "sae_or_transcoder_training_authorized": False,
            "assessment_authorized": False,
            "reason": "V48 terminal stop does not authorize execution; independent ACCEPT is required before model-bearing work",
        },
        "model": {
            "id": MODEL_ID,
            "root": MODEL_ROOT,
            "architecture": MODEL_ARCHITECTURE,
            "model_manifest_sha256": None,
        },
        "runtime": {
            "locked": dict(RUNTIME_CONTRACT),
            "observed": None,
            "source_digests": None,
        },
        "custody": {
            "root": CUSTODY_ROOT,
            "raw_root": RAW_CUSTODY_ROOT,
            "aggregate_root": AGGREGATE_CUSTODY_ROOT,
            "permissions": "0700 owner-only",
            "retention_hours": RAW_RETENTION_HOURS,
            "policy": RAW_RETENTION_POLICY,
        },
        "corpus": {
            "id": FRESH_CORPUS_ID,
            "description": FRESH_CORPUS_DESCRIPTION,
            "retention": FRESH_CORPUS_RETENTION,
            "raw_corpus_sha256": None,
        },
        "operator": {
            "id": OPERATOR_ID,
            "semantics": OPERATOR_SEMANTICS,
            "assignment": "fixed counterbalanced donor assignment by fixture_id using seed 20260830; no adaptive reassignment",
            "timing": "intervention is emitted before the downstream consumer and output is emitted after the final consumer",
            "consistency": "the recorded replacement is the declared donor state for the exact boundary key",
            "positivity": "each declared intervention boundary has at least one donor and one no-op/control realization",
            "interference": "runs use isolated state and caches; no mutable state is shared across run_ids",
        },
        "execution": {
            "runner": RUNNER_ID,
            "validator": VALIDATOR_ID,
            "operator": OPERATOR_ID,
            "operator_source_sha256": None,
            "runner_source_sha256": None,
            "validator_source_sha256": None,
            "operator_digest": None,
            "execution_authorized": False,
        },
        "qualification_gates": {
            "native_parity_max_abs_logit_delta": MAX_NATIVE_PARITY_ABS_LOGIT_DELTA,
            "deterministic_repeat_max_abs_logit_delta": MAX_DETERMINISTIC_REPEAT_ABS_LOGIT_DELTA,
            "no_op_identity_max_abs_logit_delta": MAX_NOOP_IDENTITY_ABS_LOGIT_DELTA,
            "event_missingness_max": MAX_EVENT_MISSINGNESS,
            "event_duplication_max": MAX_EVENT_DUPLICATION,
            "unaccounted_state_transitions_max": MAX_UNACCOUNTED_STATE_TRANSITIONS,
            "output_missingness_max": MAX_OUTPUT_MISSINGNESS,
        },
        "scientific_gates_sealed": {
            "sae_normalized_reconstruction_mse_max": SAE_MAX_NORMALIZED_RECONSTRUCTION_MSE,
            "sae_feature_stability_cosine_min": SAE_MIN_FEATURE_STABILITY_COSINE,
            "sae_ablation_sign_agreement_min": SAE_MIN_ABLATION_SIGN_AGREEMENT,
            "sae_feature_to_logit_sign_agreement_min": SAE_MIN_FEATURE_TO_LOGIT_SIGN_AGREEMENT,
            "graph_held_out_scrub_balanced_accuracy_min": GRAPH_MIN_HELD_OUT_SCRUB_BALANCED_ACCURACY,
            "graph_scrub_margin_over_shuffle_min": GRAPH_MIN_SCRUB_MARGIN_OVER_SHUFFLE,
            "alpha": STATISTICAL_ALPHA,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "power_target": POWER_TARGET,
            "power_standardized_effect": POWER_STANDARDIZED_EFFECT,
            "icc_sensitivity": list(ICC_SENSITIVITY),
            "repeats_required": REPEATS_REQUIRED,
            "assessment_attrition_max": MAX_ASSESSMENT_ATTRITION,
        },
        "controls": list(CONTROLS),
        "falsifiers": list(FALSIFIERS),
        "prediction_lock_before_assessment": True,
        "independent_review_receipt": "PENDING_SIGNED_ACCEPT",
        "assessment_opened": False,
    }


def validate_event_stream(events: Sequence[TraceEvent], expectation: EventExpectation, *, event_manifest_sha256: str | None = None) -> dict[str, Any]:
    """Return aggregate accounting and raise on any completeness failure."""

    if not events:
        raise ProtocolError("empty event stream")
    run_ids = {event.run_id for event in events}
    if len(run_ids) != 1:
        raise ProtocolError("event stream contains multiple run ids")
    sequences = [event.sequence for event in events]
    if sequences != list(range(len(events))):
        raise ProtocolError("event sequence is not contiguous")
    for event in events:
        if event.event_id != canonical_digest(event._identity_dict()):
            raise ProtocolError("event identity digest mismatch")
    counts = {kind: 0 for kind in EVENT_KINDS}
    for event in events:
        counts[event.kind] += 1
    expected = expectation.counts()
    if counts != expected:
        raise ProtocolError(f"event census mismatch: observed={counts!r} expected={expected!r}")
    if events[0].kind != "run_start" or events[-1].kind != "run_end":
        raise ProtocolError("run boundary events are missing")
    token_indices = [event.token_index for event in events if event.kind == "token"]
    if token_indices != list(range(expectation.token_count)):
        raise ProtocolError("token event coverage is incomplete or duplicated")
    if any(event.kind == "output" and event.value_digest is None for event in events):
        raise ProtocolError("output event is missing its digest")
    open_layers: list[tuple[int, int]] = []
    open_modules: list[tuple[tuple[int | None, str | None], int]] = []
    observed_module_paths: list[tuple[int, str]] = []
    layer_enters: dict[int, int] = {}
    for event in events:
        if event.kind == "layer_enter":
            layer = event.layer_index if event.layer_index is not None else -1
            open_layers.append((layer, event.sequence))
            layer_enters[layer] = event.sequence
        elif event.kind == "layer_output":
            layer = event.layer_index if event.layer_index is not None else -1
            if not open_layers or open_layers[-1][0] != layer or event.parent_sequence != layer_enters.get(layer):
                raise ProtocolError("layer output is not bound to its open layer")
        elif event.kind == "module_enter":
            key = (event.layer_index, event.module_path)
            open_modules.append((key, event.sequence))
            if event.layer_index is None or event.module_path is None:
                raise ProtocolError("module event is missing registry identity")
            observed_module_paths.append((event.layer_index, event.module_path))
        elif event.kind == "module_output":
            key = (event.layer_index, event.module_path)
            if not open_modules or open_modules[-1][0] != key or event.parent_sequence != open_modules[-1][1]:
                raise ProtocolError("module output is not bound to its open module")
        elif event.kind == "module_exit":
            key = (event.layer_index, event.module_path)
            if not open_modules or open_modules[-1][0] != key or event.parent_sequence != open_modules[-1][1]:
                raise ProtocolError("module transition is not properly nested")
            open_modules.pop()
        elif event.kind == "layer_exit":
            layer = event.layer_index if event.layer_index is not None else -1
            if not open_layers or open_layers[-1][0] != layer or event.parent_sequence != open_layers[-1][1]:
                raise ProtocolError("layer transition is not properly nested")
            open_layers.pop()
    if open_layers or open_modules:
        raise ProtocolError("unclosed layer or module transition")
    if expectation.expected_module_paths and observed_module_paths != list(expectation.expected_module_paths):
        raise ProtocolError("declared module registry coverage is incomplete or reordered")
    token_events = [event for event in events if event.kind == "token"]
    if any(event.value_digest is None for event in token_events):
        raise ProtocolError("token event is missing its digest")
    state_events = [event for event in events if event.kind in {"cache_read", "cache_write", "state_transition"}]
    if any(event.state_slot is None or event.value_digest is None for event in state_events):
        raise ProtocolError("state/cache event is missing state_slot")
    for event in state_events:
        _validate_digest(event.value_digest or "", f"{event.kind}.value_digest")
    transitions = [event for event in events if event.kind == "state_transition"]
    if any("before_sha256" not in event.metadata for event in transitions):
        raise ProtocolError("state transition is missing its before digest")
    for event in transitions:
        _validate_digest(str(event.metadata["before_sha256"]), "state_transition.before_sha256")
    interventions = [event for event in events if event.kind == "intervention"]
    if any(event.metadata.get("operator") != OPERATOR_ID for event in interventions):
        raise ProtocolError("intervention is not bound to the locked operator")
    for event in interventions:
        _validate_digest(event.value_digest or "", "intervention.donor_digest")
        _validate_digest(str(event.metadata.get("recipient_sha256", "")), "intervention.recipient_digest")
        boundary = str(event.metadata.get("boundary", ""))
        if boundary != f"layer{event.layer_index}.{event.module_path}":
            raise ProtocolError("intervention boundary does not match event coordinates")
        expected_operator_digest = canonical_digest(
            {
                "id": OPERATOR_ID,
                "boundary": boundary,
                "mode": event.metadata.get("mode"),
                "semantics": OPERATOR_SEMANTICS,
            }
        )
        if event.metadata.get("operator_digest") != expected_operator_digest:
            raise ProtocolError("intervention operator digest mismatch")
    expected_counts_digest = canonical_digest(
        {"counts": expected, "expected_module_paths": [list(item) for item in expectation.expected_module_paths]}
    )
    event_digest = canonical_digest([event.to_dict() for event in events])
    return {
        "protocol": PROTOCOL_ID,
        "state_slice": STATE_SLICE,
        "run_id": next(iter(run_ids)),
        "event_count": len(events),
        "event_counts": counts,
        "expected_event_counts": expected,
        "event_expectation_sha256": expected_counts_digest,
        "module_registry": [list(item) for item in expectation.expected_module_paths],
        "module_registry_sha256": canonical_digest([list(item) for item in expectation.expected_module_paths]),
        "event_manifest_sha256": event_manifest_sha256,
        "token_count": expectation.token_count,
        "layer_count": expectation.layer_count,
        "module_count": expectation.module_count,
        "event_stream_sha256": event_digest,
        "raw_events_retained": False,
        "aggregate_only": True,
        "missing_event_count": 0,
        "duplicate_event_count": 0,
        "unaccounted_state_transition_count": 0,
        "output_count": expectation.output_count,
    }


def digest_source_manifest(paths: Iterable[Path], repository_root: Path) -> dict[str, str]:
    """Digest only declared source files; callers must bind the result in a packet."""

    result: dict[str, str] = {}
    for path in sorted((Path(item).resolve() for item in paths), key=str):
        repository = repository_root.resolve()
        if path == repository or repository not in path.parents:
            raise ProtocolError(f"source file must be inside the repository: {path}")
        if not path.is_file() or path.is_symlink():
            raise ProtocolError(f"source file is missing or symlinked: {path}")
        result[path.name] = sha256_file(path)
    if not result:
        raise ProtocolError("source manifest is empty")
    return result
