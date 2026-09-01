"""Native-boundary adapter for typed trace capture and exact interchange.

State slice: astral-trace-completeness-native-instrument-v1.

The adapter never serializes a raw value.  A model-specific native forward
implementation calls the typed boundary methods; the adapter then fails
closed unless the runtime manifest's exact event census is satisfied.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Iterator, Mapping, Sequence

import protocol


def digest_value(value: Any) -> str:
    """Digest a caller-provided value without retaining it in an event."""

    if isinstance(value, bytes):
        payload = value
    else:
        try:
            payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise protocol.ProtocolError("value must be digestible before event emission") from exc
    return hashlib.sha256(payload).hexdigest()


class TraceCompletenessError(protocol.ProtocolError):
    """Raised when a native run does not account for its declared boundaries."""


class TraceEmitter:
    """In-memory typed emitter; callers must explicitly export aggregates only."""

    def __init__(self, run_id: str) -> None:
        if not run_id:
            raise protocol.ProtocolError("run_id is required")
        self.run_id = run_id
        self._events: list[protocol.TraceEvent] = []

    @property
    def events(self) -> tuple[protocol.TraceEvent, ...]:
        return tuple(self._events)

    def emit(
        self,
        kind: str,
        *,
        token_index: int | None = None,
        layer_index: int | None = None,
        module_path: str | None = None,
        state_slot: str | None = None,
        value: Any = None,
        value_digest: str | None = None,
        shape: Sequence[int] | None = None,
        dtype: str | None = None,
        parent_sequence: int | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> protocol.TraceEvent:
        if value is not None and value_digest is not None:
            raise protocol.ProtocolError("provide value or value_digest, never both")
        if value is not None:
            value_digest = digest_value(value)
        event = protocol.TraceEvent(
            run_id=self.run_id,
            sequence=len(self._events),
            kind=kind,
            token_index=token_index,
            layer_index=layer_index,
            module_path=module_path,
            state_slot=state_slot,
            value_digest=value_digest,
            shape=tuple(shape) if shape is not None else None,
            dtype=dtype,
            parent_sequence=parent_sequence,
            metadata=dict(metadata or {}),
        )
        self._events.append(event)
        return event

    def begin(self, *, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit("run_start", metadata=metadata)

    def token(self, token_index: int, *, token_digest: str, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit("token", token_index=token_index, value_digest=token_digest, metadata=metadata)

    @contextlib.contextmanager
    def layer(self, layer_index: int, *, shape: Sequence[int], dtype: str, value_digest: str | None = None) -> Iterator[Callable[..., protocol.TraceEvent]]:
        enter = self.emit("layer_enter", layer_index=layer_index, shape=shape, dtype=dtype, value_digest=value_digest)
        completed = False

        def complete(*, output_digest: str, output_shape: Sequence[int], output_dtype: str) -> protocol.TraceEvent:
            nonlocal completed
            if completed:
                raise protocol.ProtocolError("layer output was emitted twice")
            completed = True
            return self.emit(
                "layer_output",
                layer_index=layer_index,
                value_digest=output_digest,
                shape=output_shape,
                dtype=output_dtype,
                parent_sequence=enter.sequence,
            )

        try:
            yield complete
        finally:
            if not completed:
                raise protocol.ProtocolError("layer output was not emitted")
            self.emit("layer_exit", layer_index=layer_index, shape=shape, dtype=dtype, parent_sequence=enter.sequence)

    @contextlib.contextmanager
    def module(self, layer_index: int, module_path: str, *, shape: Sequence[int], dtype: str, value_digest: str | None = None) -> Iterator[Callable[..., protocol.TraceEvent]]:
        enter = self.emit(
            "module_enter",
            layer_index=layer_index,
            module_path=module_path,
            shape=shape,
            dtype=dtype,
            value_digest=value_digest,
        )
        completed = False

        def complete(*, output_digest: str, output_shape: Sequence[int], output_dtype: str) -> protocol.TraceEvent:
            nonlocal completed
            if completed:
                raise protocol.ProtocolError("module output was emitted twice")
            completed = True
            return self.emit(
                "module_output",
                layer_index=layer_index,
                module_path=module_path,
                value_digest=output_digest,
                shape=output_shape,
                dtype=output_dtype,
                parent_sequence=enter.sequence,
            )

        try:
            yield complete
        finally:
            if not completed:
                raise protocol.ProtocolError("module output was not emitted")
            self.emit(
                "module_exit",
                layer_index=layer_index,
                module_path=module_path,
                shape=shape,
                dtype=dtype,
                parent_sequence=enter.sequence,
            )

    def cache_read(self, state_slot: str, *, value_digest: str, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit("cache_read", state_slot=state_slot, value_digest=value_digest, metadata=metadata)

    def cache_write(self, state_slot: str, *, value_digest: str, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit("cache_write", state_slot=state_slot, value_digest=value_digest, metadata=metadata)

    def state_transition(self, state_slot: str, *, before_digest: str, after_digest: str, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit(
            "state_transition",
            state_slot=state_slot,
            value_digest=after_digest,
            metadata={"before_sha256": before_digest, **dict(metadata or {})},
        )

    def intervention(
        self,
        *,
        token_index: int,
        layer_index: int,
        module_path: str,
        state_slot: str,
        donor_digest: str,
        recipient_digest: str,
        mode: str,
        boundary: str,
        operator_digest: str,
    ) -> protocol.TraceEvent:
        return self.emit(
            "intervention",
            token_index=token_index,
            layer_index=layer_index,
            module_path=module_path,
            state_slot=state_slot,
            value_digest=donor_digest,
            metadata={
                "recipient_sha256": recipient_digest,
                "mode": mode,
                "operator": protocol.OPERATOR_ID,
                "boundary": boundary,
                "operator_digest": operator_digest,
            },
        )

    def output(self, *, output_digest: str, shape: Sequence[int], dtype: str, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit("output", value_digest=output_digest, shape=shape, dtype=dtype, metadata=metadata)

    def end(self, *, metadata: Mapping[str, Any] | None = None) -> protocol.TraceEvent:
        return self.emit("run_end", metadata=metadata)


@dataclass(frozen=True)
class NativeRun:
    output: Any
    events: tuple[protocol.TraceEvent, ...]
    aggregate: Mapping[str, Any]


class NativeModelAdapter:
    """Adapter boundary for a model's native forward implementation.

    ``native_forward`` receives ``(hooks, tokens)`` and must call every native
    boundary method exposed by the locked runtime manifest.  This requirement
    is intentional: a generic hook library cannot prove coverage of opaque or
    compiled model internals.
    """

    def __init__(self, expectation: protocol.EventExpectation, *, run_id_factory: Callable[[], str] | None = None) -> None:
        self.expectation = expectation
        self.run_id_factory = run_id_factory or (lambda: uuid.uuid4().hex)

    def execute(
        self,
        tokens: Sequence[Any],
        native_forward: Callable[[TraceEmitter, Sequence[Any]], Any],
        *,
        event_manifest_sha256: str | None = None,
    ) -> NativeRun:
        if len(tokens) != self.expectation.token_count:
            raise TraceCompletenessError("token count differs from locked runtime manifest")
        emitter = TraceEmitter(self.run_id_factory())
        emitter.begin(metadata={"runner": protocol.RUNNER_ID})
        for index, token in enumerate(tokens):
            emitter.token(index, token_digest=digest_value(token))
        output = native_forward(emitter, tokens)
        if not emitter.events or emitter.events[-1].kind == "run_end":
            raise TraceCompletenessError("native forward must emit output before adapter closes the run")
        emitter.end()
        try:
            aggregate = protocol.validate_event_stream(emitter.events, self.expectation, event_manifest_sha256=event_manifest_sha256)
        except protocol.ProtocolError as exc:
            raise TraceCompletenessError(str(exc)) from exc
        return NativeRun(output=output, events=emitter.events, aggregate=aggregate)


class ActivationInterchangeOperator:
    """Executable exact activation/path replacement operator."""

    def __init__(self, *, boundary: str, mode: str = "replace") -> None:
        if not boundary or mode not in {"replace", "noop", "zero", "constant", "shuffle"}:
            raise protocol.ProtocolError("invalid interchange operator")
        self.boundary = boundary
        self.mode = mode
        self.operator_digest = protocol.canonical_digest(
            {"id": protocol.OPERATOR_ID, "boundary": boundary, "mode": mode, "semantics": protocol.OPERATOR_SEMANTICS}
        )

    def apply(
        self,
        recipient: Any,
        donor: Any,
        *,
        emitter: TraceEmitter,
        token_index: int,
        layer_index: int,
        module_path: str,
        state_slot: str,
    ) -> Any:
        recipient_digest = digest_value(recipient)
        donor_digest = digest_value(donor)
        expected_boundary = f"layer{layer_index}.{module_path}"
        if self.boundary != expected_boundary:
            raise protocol.ProtocolError("interchange boundary does not match event coordinates")
        emitter.intervention(
            token_index=token_index,
            layer_index=layer_index,
            module_path=module_path,
            state_slot=state_slot,
            donor_digest=donor_digest,
            recipient_digest=recipient_digest,
            mode=self.mode,
            boundary=self.boundary,
            operator_digest=self.operator_digest,
        )
        if self.mode == "noop":
            return recipient
        if self.mode == "replace":
            return donor
        if self.mode == "zero":
            if isinstance(recipient, (int, float)):
                return type(recipient)(0)
            if isinstance(recipient, list):
                return [0 for _ in recipient]
            raise protocol.ProtocolError("zero operator requires a scalar or list fixture")
        if self.mode == "constant":
            return 0.0
        if self.mode == "shuffle":
            if isinstance(donor, list):
                return list(reversed(donor))
            raise protocol.ProtocolError("shuffle operator requires a list fixture")
        raise protocol.ProtocolError("unreachable interchange mode")

    def patch_path(
        self,
        recipient_state: Mapping[str, Any],
        donor_state: Mapping[str, Any],
        path_edges: Sequence[str],
        *,
        emitter: TraceEmitter,
        token_index: int,
        layer_index: int,
        module_path: str,
    ) -> dict[str, Any]:
        result = dict(recipient_state)
        for state_slot in path_edges:
            if state_slot not in result or state_slot not in donor_state:
                raise protocol.ProtocolError(f"path edge is absent from recipient or donor state: {state_slot}")
            result[state_slot] = self.apply(
                result[state_slot],
                donor_state[state_slot],
                emitter=emitter,
                token_index=token_index,
                layer_index=layer_index,
                module_path=module_path,
                state_slot=state_slot,
            )
        return result
