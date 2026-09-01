"""Fail-closed contracts for Gemma 3 end-to-end trace completeness V2.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "astral-trace-completeness-gemma3-end-to-end-v2"
PROTOCOL_ID = "astral-trace-completeness-gemma3-v2.1"
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ROOT = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
CUSTODY_ROOT = Path("/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v2")
ASSET_ROOT = CUSTODY_ROOT / "assets" / "gemma-scope-2-1b-pt"
ASSET_REPOSITORY = "google/gemma-scope-2-1b-pt"
ASSET_REVISION = "b738dc06961818c011fb2e44a316352ca0f4e873"
CIRCUIT_TRACER_REVISION = "6018ed8d35e40f2c50062822e8dde422b8e52e2d"
CORPUS_ID = "gemma3-trace-causal-families-v2-2026-08-30"
QUALIFICATION_CEILING = "LocalDevelopmentGemma3EndToEndCausalTraceQualification"
ASSESSMENT_CEILING = "LocalDevelopmentGemma3HeldOutCausalTraceAssessment"
LAYER_COUNT = 26
HIDDEN_WIDTH = 1152
FEATURE_WIDTH = 16384
RAW_RETENTION_HOURS = 72

PARITY_MAX_ABS_DELTA = 1e-4
REPEAT_MAX_ABS_DELTA = 1e-5
NOOP_MAX_ABS_DELTA = 1e-5
SAE_RECONSTRUCTION_NMSE_MAX = 0.05
FEATURE_STABILITY_COSINE_MIN = 0.90
FEATURE_ABLATION_SIGN_MIN = 0.80
FEATURE_TO_LOGIT_SIGN_MIN = 0.80
SCRUB_BALANCED_ACCURACY_MIN = 0.80
SCRUB_SHUFFLED_MARGIN_MIN = 0.10

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
    "graph_prediction",
    "output_distribution",
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


class ProtocolError(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise ProtocolError(f"nonstandard JSON constant: {value}")


def strict_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


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

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        value = dataclasses.asdict(self)
        value["metadata"] = dict(self.metadata)
        value["event_sha256"] = digest_json(value)
        return value

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TraceEvent":
        copy = dict(value)
        expected_digest = copy.pop("event_sha256", None)
        event = cls(**copy)
        event.validate()
        if expected_digest != digest_json(dataclasses.asdict(event)):
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
    graph_prediction_events: int = 0

    def validate(self) -> None:
        if self.generation_steps <= 0 or self.input_token_count <= 0:
            raise ProtocolError("run expectation requires tokens and generation steps")
        if not self.module_input_paths:
            raise ProtocolError("module input call registry is empty")
        if Counter(self.module_output_paths) != Counter(self.module_input_paths):
            raise ProtocolError("module output registry differs from input registry")
        if len(set(self.attention_modules)) != len(self.attention_modules):
            raise ProtocolError("attention registry is duplicated")
        if any(path not in self.module_input_paths for path in self.attention_modules):
            raise ProtocolError("attention path missing from module registry")
        if min(self.cache_updates_per_step, self.interventions, self.sae_feature_events, self.sae_reconstruction_events, self.graph_prediction_events) < 0:
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
            "graph_prediction": self.graph_prediction_events,
            "output_distribution": self.generation_steps,
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
        if not step_events or step_events[0].kind != "generation_step_start" or step_events[-1].kind != "generation_step_end":
            raise ProtocolError("generation step boundaries are incomplete")
        paths_in = [event.module_path for event in step_events if event.kind == "module_input"]
        paths_out = [event.module_path for event in step_events if event.kind == "module_output"]
        if paths_in != list(expectation.module_input_paths) or paths_out != list(expectation.module_output_paths):
            input_index = next(
                (index for index, pair in enumerate(zip(paths_in, expectation.module_input_paths)) if pair[0] != pair[1]),
                min(len(paths_in), len(expectation.module_input_paths)),
            )
            output_index = next(
                (index for index, pair in enumerate(zip(paths_out, expectation.module_output_paths)) if pair[0] != pair[1]),
                min(len(paths_out), len(expectation.module_output_paths)),
            )
            detail = {
                "input_index": input_index,
                "input_observed": paths_in[input_index] if input_index < len(paths_in) else None,
                "input_expected": expectation.module_input_paths[input_index] if input_index < len(expectation.module_input_paths) else None,
                "output_index": output_index,
                "output_observed": paths_out[output_index] if output_index < len(paths_out) else None,
                "output_expected": expectation.module_output_paths[output_index] if output_index < len(expectation.module_output_paths) else None,
            }
            raise ProtocolError(f"module registry coverage or nesting mismatch: {detail}")
        attention_paths = [event.module_path for event in step_events if event.kind == "attention_pattern"]
        if attention_paths != list(expectation.attention_modules):
            raise ProtocolError("attention pattern coverage mismatch")
        score_paths = [event.module_path for event in step_events if event.kind == "attention_score"]
        if score_paths != list(expectation.attention_modules):
            raise ProtocolError("attention score coverage mismatch")
        if any(event.value_sha256 is None for event in step_events if event.kind not in {"generation_step_start", "generation_step_end"}):
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
