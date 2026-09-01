"""PyTorch-native synchronized generation trace adapter for Gemma 3 V2.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
"""

from __future__ import annotations

import contextlib
import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

import protocol_v2 as protocol
import registry_v2 as registry


def _torch():
    import torch

    return torch


def _first_tensor(value: Any) -> Any | None:
    torch = _torch()
    if isinstance(value, torch.Tensor):
        return value
    if isinstance(value, Mapping):
        for item in value.values():
            if (tensor := _first_tensor(item)) is not None:
                return tensor
    if isinstance(value, (tuple, list)):
        for item in value:
            if (tensor := _first_tensor(item)) is not None:
                return tensor
    for attribute in ("logits", "last_hidden_state"):
        if hasattr(value, attribute) and (tensor := _first_tensor(getattr(value, attribute))) is not None:
            return tensor
    return None


def tensor_digest(value: Any) -> str:
    torch = _torch()
    digest = hashlib.sha256()

    def update(item: Any) -> None:
        if isinstance(item, torch.Tensor):
            tensor = item.detach().contiguous().cpu()
            digest.update(str(tuple(tensor.shape)).encode("ascii"))
            digest.update(str(tensor.dtype).encode("ascii"))
            digest.update(tensor.view(torch.uint8).numpy().tobytes())
        elif isinstance(item, Mapping):
            for key in sorted(item):
                digest.update(str(key).encode("utf-8"))
                update(item[key])
        elif isinstance(item, (tuple, list)):
            for child in item:
                update(child)
        elif item is None or isinstance(item, (bool, int, float, str)):
            digest.update(protocol.canonical_bytes(item))
        elif hasattr(item, "logits"):
            update(item.logits)
        elif hasattr(item, "last_hidden_state"):
            update(item.last_hidden_state)
        else:
            digest.update(type(item).__qualname__.encode("utf-8"))

    update(value)
    return digest.hexdigest()


def shape_dtype(value: Any) -> tuple[tuple[int, ...], str]:
    tensor = _first_tensor(value)
    if tensor is None:
        raise protocol.ProtocolError("module boundary did not expose a tensor")
    return tuple(int(item) for item in tensor.shape), str(tensor.dtype)


@dataclass(frozen=True)
class InterventionPlan:
    module_path: str
    step: int
    mode: str
    donor: Any | None = None

    def validate(self, paths: Sequence[str]) -> None:
        if self.module_path not in paths or self.step < 0:
            raise protocol.ProtocolError("intervention boundary is outside the frozen registry")
        if self.mode not in {"noop", "replace", "zero"}:
            raise protocol.ProtocolError("unsupported intervention mode")
        if self.mode == "replace" and self.donor is None:
            raise protocol.ProtocolError("replacement intervention requires a donor")


class TraceEmitter:
    def __init__(self, run_id: str, trial_id: str) -> None:
        self.run_id = run_id
        self.trial_id = trial_id
        self.events: list[protocol.TraceEvent] = []
        self.step: int | None = None
        self._module_parents: dict[str, list[int]] = {}

    def emit(self, kind: str, **kwargs: Any) -> protocol.TraceEvent:
        event = protocol.TraceEvent(
            run_id=self.run_id,
            trial_id=self.trial_id,
            sequence=len(self.events),
            kind=kind,
            step=self.step,
            **kwargs,
        )
        event.validate()
        self.events.append(event)
        return event

    def module_input(self, path: str, value: Any) -> None:
        shape, dtype = shape_dtype(value)
        event = self.emit("module_input", module_path=path, shape=shape, dtype=dtype, value_sha256=tensor_digest(value))
        self._module_parents.setdefault(path, []).append(event.sequence)

    def module_output(self, path: str, value: Any) -> None:
        parents = self._module_parents.get(path)
        if not parents:
            raise protocol.ProtocolError(f"module output without input: {path}")
        shape, dtype = shape_dtype(value)
        self.emit(
            "module_output",
            module_path=path,
            shape=shape,
            dtype=dtype,
            value_sha256=tensor_digest(value),
            parent_sequence=parents.pop(),
        )


def _cache_layer_digest(cache: Any, layer_index: int) -> str:
    if layer_index >= len(cache.layers):
        return tensor_digest({"layer_index": layer_index, "state": "uninitialized"})
    public_state = {
        key: value
        for key, value in vars(cache.layers[layer_index]).items()
        if not key.startswith("_") or key in {"keys", "values"}
    }
    return tensor_digest(public_state)


def traced_dynamic_cache(config: Any, emitter: TraceEmitter) -> Any:
    from transformers.cache_utils import DynamicCache

    class TracedDynamicCache(DynamicCache):
        def get_seq_length(self, layer_idx: int = 0) -> int:
            value = super().get_seq_length(layer_idx)
            emitter.emit(
                "cache_read",
                layer_index=layer_idx,
                state_slot=f"kv.layer.{layer_idx}.sequence_length",
                value_sha256=tensor_digest(value),
                metadata={"operation": "get_seq_length"},
            )
            return value

        def update(self, key_states: Any, value_states: Any, layer_idx: int, *args: Any, **kwargs: Any) -> Any:
            before = _cache_layer_digest(self, layer_idx)
            result = super().update(key_states, value_states, layer_idx, *args, **kwargs)
            after = _cache_layer_digest(self, layer_idx)
            slot = f"kv.layer.{layer_idx}"
            emitter.emit(
                "cache_write",
                layer_index=layer_idx,
                state_slot=slot,
                shape=shape_dtype(result)[0],
                dtype=shape_dtype(result)[1],
                value_sha256=after,
                metadata={"operation": "append_or_write"},
            )
            emitter.emit(
                "cache_transition",
                layer_index=layer_idx,
                state_slot=slot,
                value_sha256=after,
                metadata={"before_sha256": before, "operation": "append_or_write"},
            )
            return result

        def crop(self, max_length: int) -> None:
            before = tensor_digest([_cache_layer_digest(self, index) for index in range(len(self.layers))])
            super().crop(max_length)
            after = tensor_digest([_cache_layer_digest(self, index) for index in range(len(self.layers))])
            emitter.emit("cache_transition", state_slot="kv.all", value_sha256=after, metadata={"before_sha256": before, "operation": "crop"})

        def reset(self) -> None:
            before = tensor_digest([_cache_layer_digest(self, index) for index in range(len(self.layers))])
            super().reset()
            after = tensor_digest([_cache_layer_digest(self, index) for index in range(len(self.layers))])
            emitter.emit("cache_transition", state_slot="kv.all", value_sha256=after, metadata={"before_sha256": before, "operation": "reset"})

    return TracedDynamicCache(config=config)


@dataclass
class TraceRun:
    run_id: str
    trial_id: str
    events: tuple[protocol.TraceEvent, ...]
    aggregate: Mapping[str, Any]
    logits: tuple[Any, ...]
    sampled_tokens: tuple[int, ...]
    captures: Mapping[str, tuple[Any, ...]] = field(repr=False)


class InstrumentedGenerator:
    def __init__(self, model: Any, *, run_id_factory: Any | None = None) -> None:
        self.model = model
        self.registry = registry.validate_model(model)
        self.run_id_factory = run_id_factory or (lambda: uuid.uuid4().hex)

    @contextlib.contextmanager
    def _hooks(
        self,
        emitter: TraceEmitter,
        captures: dict[str, list[Any]],
        capture_paths: set[str],
        intervention: InterventionPlan | None,
    ) -> Iterable[None]:
        handles = []
        modules = dict(self.model.named_modules())
        attention_paths = set(self.registry["attention_paths"])

        def pre(path: str):
            def hook(module: Any, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> None:
                value = args if args else kwargs
                emitter.module_input(path, value)
                if path in capture_paths:
                    tensor = _first_tensor(value)
                    if tensor is not None:
                        captures.setdefault(f"{path}.input", []).append(tensor.detach().clone())

            return hook

        def post(path: str):
            def hook(module: Any, args: tuple[Any, ...], kwargs: Mapping[str, Any], output: Any) -> Any:
                emitted_output = output
                if intervention is not None and emitter.step == intervention.step and path == intervention.module_path:
                    recipient = _first_tensor(output)
                    if recipient is None:
                        raise protocol.ProtocolError("intervention recipient is not a tensor")
                    if intervention.mode == "noop":
                        replacement = recipient
                    elif intervention.mode == "zero":
                        replacement = _torch().zeros_like(recipient)
                    else:
                        replacement = intervention.donor.to(device=recipient.device, dtype=recipient.dtype)
                        if replacement.shape != recipient.shape:
                            raise protocol.ProtocolError("intervention donor shape mismatch")
                    if isinstance(output, tuple):
                        emitted_output = (replacement, *output[1:])
                    else:
                        emitted_output = replacement
                    emitter.emit(
                        "intervention",
                        module_path=path,
                        value_sha256=tensor_digest(replacement),
                        metadata={
                            "mode": intervention.mode,
                            "recipient_sha256": tensor_digest(recipient),
                            "operator": "exact-module-output-interchange-v2",
                        },
                    )
                emitter.module_output(path, emitted_output)
                if path in attention_paths:
                    pattern = output[1] if isinstance(output, tuple) and len(output) > 1 else None
                    if pattern is None:
                        raise protocol.ProtocolError(f"attention pattern missing at {path}")
                    shape, dtype = shape_dtype(pattern)
                    emitter.emit("attention_pattern", module_path=path, shape=shape, dtype=dtype, value_sha256=tensor_digest(pattern))
                if path in capture_paths:
                    tensor = _first_tensor(emitted_output)
                    if tensor is not None:
                        captures.setdefault(f"{path}.output", []).append(tensor.detach().clone())
                return emitted_output

            return hook

        try:
            for path in self.registry["hook_paths"]:
                handles.append(modules[path].register_forward_pre_hook(pre(path), with_kwargs=True))
                handles.append(modules[path].register_forward_hook(post(path), with_kwargs=True))
            yield
        finally:
            for handle in reversed(handles):
                handle.remove()

    @contextlib.contextmanager
    def _attention_scores(self, emitter: TraceEmitter) -> Iterable[None]:
        torch = _torch()
        from transformers.models.gemma3 import modeling_gemma3

        original = modeling_gemma3.eager_attention_forward

        def traced(module: Any, query: Any, key: Any, value: Any, attention_mask: Any, **kwargs: Any) -> Any:
            key_states = modeling_gemma3.repeat_kv(key, module.num_key_value_groups)
            scores = torch.matmul(query, key_states.transpose(2, 3)) * kwargs.get("scaling", module.scaling)
            softcap = kwargs.get("softcap")
            if softcap is not None:
                scores = torch.tanh(scores / softcap) * softcap
            if attention_mask is not None:
                scores = scores + attention_mask[:, :, :, : key_states.shape[-2]]
            path = f"model.layers.{module.layer_idx}.self_attn"
            emitter.emit(
                "attention_score",
                layer_index=int(module.layer_idx),
                module_path=path,
                shape=tuple(int(item) for item in scores.shape),
                dtype=str(scores.dtype),
                value_sha256=tensor_digest(scores),
                metadata={"boundary": "masked_pre_softmax"},
            )
            return original(module, query, key, value, attention_mask, **kwargs)

        modeling_gemma3.eager_attention_forward = traced
        try:
            yield
        finally:
            modeling_gemma3.eager_attention_forward = original

    def run(
        self,
        input_ids: Any,
        *,
        trial_id: str,
        max_new_tokens: int = 1,
        target_token_ids: Sequence[int] | None = None,
        intervention: InterventionPlan | None = None,
        capture_paths: Sequence[str] = (),
        feature_observer: Any | None = None,
        sae_feature_events_per_step: int = 0,
        sae_reconstruction_events_per_step: int = 0,
        graph_prediction_events_per_step: int = 0,
    ) -> TraceRun:
        torch = _torch()
        if input_ids.ndim != 2 or input_ids.shape[0] != 1:
            raise protocol.ProtocolError("V2 requires one prompt per isolated run")
        if max_new_tokens <= 0:
            raise protocol.ProtocolError("generation length must be positive")
        paths = tuple(self.registry["module_input_paths"])
        if intervention is not None:
            intervention.validate(paths)
            if intervention.step >= max_new_tokens:
                raise protocol.ProtocolError("intervention step is outside generation")
        run_id = self.run_id_factory()
        emitter = TraceEmitter(run_id, trial_id)
        emitter.emit("run_start", metadata={"runner": "InstrumentedGenerator.run", "sampling": "greedy"})
        cache = traced_dynamic_cache(self.model.config, emitter)
        captures: dict[str, list[Any]] = {}
        logits_history = []
        sampled_tokens = []
        current = input_ids
        target_token_ids = tuple(target_token_ids or ())
        self.model.eval()
        with torch.no_grad(), self._hooks(emitter, captures, set(capture_paths), intervention), self._attention_scores(emitter):
            for step in range(max_new_tokens):
                emitter.step = step
                emitter.emit("generation_step_start", metadata={"sampling": "greedy"})
                for offset, token in enumerate(current[0].tolist()):
                    token_index = offset if step == 0 else int(input_ids.shape[1]) + step - 1
                    emitter.emit("input_token", token_index=token_index, value_sha256=tensor_digest(int(token)))
                emitter.emit("rng_state", value_sha256=tensor_digest(torch.random.get_rng_state()), metadata={"device": "cpu_generator"})
                outputs = self.model(
                    input_ids=current,
                    past_key_values=cache,
                    use_cache=True,
                    output_attentions=True,
                    logits_to_keep=1,
                    return_dict=True,
                )
                logits = outputs.logits[:, -1, :].float()
                logits_history.append(logits.detach().clone())
                if feature_observer is not None:
                    feature_observer(emitter, captures, step, logits)
                emitter.emit("output_distribution", shape=tuple(logits.shape), dtype=str(logits.dtype), value_sha256=tensor_digest(logits))
                token = int(torch.argmax(logits, dim=-1).item())
                sampled_tokens.append(token)
                emitter.emit("sampled_token", token_index=int(input_ids.shape[1]) + step, value_sha256=tensor_digest(token), metadata={"sampling": "argmax"})
                expected = target_token_ids[step] if step < len(target_token_ids) else None
                outcome = {"expected_present": expected is not None, "correct": expected is not None and token == expected}
                emitter.emit("behavioral_outcome", value_sha256=protocol.digest_json(outcome), metadata=outcome)
                emitter.emit("generation_step_end", value_sha256=tensor_digest(token))
                current = torch.tensor([[token]], dtype=input_ids.dtype, device=input_ids.device)
        emitter.step = None
        emitter.emit("run_end", metadata={"generated_tokens": max_new_tokens})
        expectation = protocol.RunExpectation(
            generation_steps=max_new_tokens,
            input_token_count=int(input_ids.shape[1]),
            module_input_paths=tuple(self.registry["module_input_paths"]),
            module_output_paths=tuple(self.registry["module_output_paths"]),
            attention_modules=tuple(self.registry["attention_paths"]),
            interventions=1 if intervention is not None else 0,
            sae_feature_events=sae_feature_events_per_step * max_new_tokens,
            sae_reconstruction_events=sae_reconstruction_events_per_step * max_new_tokens,
            graph_prediction_events=graph_prediction_events_per_step * max_new_tokens,
        )
        aggregate = protocol.validate_event_stream(emitter.events, expectation)
        return TraceRun(
            run_id,
            trial_id,
            tuple(emitter.events),
            aggregate,
            tuple(logits_history),
            tuple(sampled_tokens),
            {key: tuple(value) for key, value in captures.items()},
        )


def native_generate(model: Any, input_ids: Any, *, max_new_tokens: int = 1) -> tuple[tuple[Any, ...], tuple[int, ...]]:
    torch = _torch()
    from transformers.cache_utils import DynamicCache

    model.eval()
    cache = DynamicCache(config=model.config)
    current = input_ids
    logits_history = []
    tokens = []
    with torch.no_grad():
        for _ in range(max_new_tokens):
            outputs = model(
                input_ids=current,
                past_key_values=cache,
                use_cache=True,
                output_attentions=True,
                logits_to_keep=1,
                return_dict=True,
            )
            logits = outputs.logits[:, -1, :].float()
            logits_history.append(logits.detach().clone())
            token = int(torch.argmax(logits, dim=-1).item())
            tokens.append(token)
            current = torch.tensor([[token]], dtype=input_ids.dtype, device=input_ids.device)
    return tuple(logits_history), tuple(tokens)
