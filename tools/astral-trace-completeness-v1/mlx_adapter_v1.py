"""MLX-native attachment boundary for trace completeness V1.

State slice: astral-trace-completeness-native-instrument-v1.

This module is importable without MLX.  When MLX is available it validates the
declared decoder-layer and nested-module boundaries in the supplied model and
provides the callbacks that the native forward must invoke; anything not
present in the frozen registry is a hard error.  Cache/state observers are
explicit because opaque cache implementations cannot be proven complete by a
generic Python hook.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

import native_adapter
import protocol


@dataclass(frozen=True)
class ModuleSpec:
    layer_index: int
    module_path: str


@dataclass(frozen=True)
class ModuleRegistry:
    """Frozen module paths and call census for one forward invocation."""

    modules: tuple[ModuleSpec, ...]
    layer_count: int
    cache_read_count: int = 0
    cache_write_count: int = 0
    state_transition_count: int = 0
    intervention_count: int = 0

    def expectation(self, *, token_count: int, output_count: int = 1) -> protocol.EventExpectation:
        return protocol.EventExpectation(
            token_count=token_count,
            layer_count=self.layer_count,
            module_count=len(self.modules),
            cache_read_count=self.cache_read_count,
            cache_write_count=self.cache_write_count,
            state_transition_count=self.state_transition_count,
            intervention_count=self.intervention_count,
            output_count=output_count,
            expected_module_paths=tuple((item.layer_index, item.module_path) for item in self.modules),
        )

    def validate(self) -> None:
        if self.layer_count <= 0 or not self.modules:
            raise protocol.ProtocolError("module registry cannot be empty")
        if len({(item.layer_index, item.module_path) for item in self.modules}) != len(self.modules):
            raise protocol.ProtocolError("module registry contains duplicates")
        if any(item.layer_index < 0 or not item.module_path for item in self.modules):
            raise protocol.ProtocolError("module registry contains invalid paths")
        if any(value < 0 for value in (self.cache_read_count, self.cache_write_count, self.state_transition_count, self.intervention_count)):
            raise protocol.ProtocolError("state and intervention counts must be nonnegative")


def _shape_dtype(value: Any) -> tuple[tuple[int, ...], str]:
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    if shape is None or dtype is None:
        raise protocol.ProtocolError("native MLX boundary did not expose shape and dtype")
    return tuple(int(item) for item in shape), str(dtype)


def _resolve(root: Any, path: str) -> Any:
    current = root
    for component in path.split("."):
        if component.isdigit():
            current = current[int(component)]
        elif isinstance(current, Mapping):
            current = current[component]
        else:
            current = getattr(current, component)
    return current


def _resolve_parent(root: Any, path: str) -> tuple[Any, str]:
    components = path.split(".")
    if not components or any(not component for component in components):
        raise protocol.ProtocolError(f"invalid module path: {path}")
    parent = root
    for component in components[:-1]:
        parent = parent[int(component)] if component.isdigit() else (parent[component] if isinstance(parent, Mapping) else getattr(parent, component))
    return parent, components[-1]


def _get_child(parent: Any, component: str) -> Any:
    return parent[int(component)] if component.isdigit() else (parent[component] if isinstance(parent, Mapping) else getattr(parent, component))


def _set_child(parent: Any, component: str, value: Any) -> None:
    if component.isdigit():
        parent[int(component)] = value
    elif isinstance(parent, dict):
        parent[component] = value
    else:
        setattr(parent, component, value)


def _value_list(value: Any) -> Any:
    converter = getattr(value, "tolist", None)
    return converter() if callable(converter) else value


class _ModuleProxy:
    def __init__(self, adapter: "NativeMLXAdapter", target: Any, layer_index: int, module_path: str) -> None:
        self.adapter = adapter
        self.target = target
        self.layer_index = layer_index
        self.module_path = module_path

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        emitter = self.adapter._active_emitter
        if emitter is None:
            return self.target(*args, **kwargs)
        if not args:
            raise protocol.ProtocolError(f"module has no input value: {self.module_path}")
        shape, dtype = _shape_dtype(args[0])
        with emitter.module(
            self.layer_index,
            self.module_path,
            shape=shape,
            dtype=dtype,
            value_digest=native_adapter.digest_value(_value_list(args[0])),
        ) as complete:
            output = self.target(*args, **kwargs)
            output_shape, output_dtype = _shape_dtype(output)
            complete(
                output_digest=native_adapter.digest_value(_value_list(output)),
                output_shape=output_shape,
                output_dtype=output_dtype,
            )
            return output


class _LayerProxy:
    def __init__(self, adapter: "NativeMLXAdapter", target: Any, layer_index: int) -> None:
        self.adapter = adapter
        self.target = target
        self.layer_index = layer_index

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        emitter = self.adapter._active_emitter
        if emitter is None:
            return self.target(*args, **kwargs)
        if not args:
            raise protocol.ProtocolError(f"layer has no input value: {self.layer_index}")
        shape, dtype = _shape_dtype(args[0])
        with emitter.layer(
            self.layer_index,
            shape=shape,
            dtype=dtype,
            value_digest=native_adapter.digest_value(_value_list(args[0])),
        ) as complete:
            output = self.target(*args, **kwargs)
            output_shape, output_dtype = _shape_dtype(output)
            complete(
                output_digest=native_adapter.digest_value(_value_list(output)),
                output_shape=output_shape,
                output_dtype=output_dtype,
            )
            return output


class NativeMLXAdapter:
    """Attach typed events to a model with a frozen registry.

    The adapter requires a cache observer.  The observer receives the emitter
    and the runtime cache and must emit every cache/state read, write, trim,
    allocation, and recurrent-state transition.  Omitting it is rejected.
    """

    def __init__(
        self,
        model: Any,
        registry: ModuleRegistry,
        *,
        cache_observer: Callable[[native_adapter.TraceEmitter, Any], Any],
        run_id_factory: Callable[[], str] | None = None,
    ) -> None:
        registry.validate()
        if not callable(cache_observer):
            raise protocol.ProtocolError("cache observer is required for native completeness")
        self.model = model
        self.registry = registry
        self.cache_observer = cache_observer
        self.run_id_factory = run_id_factory
        self._attached = False
        self._original_layers: list[Any] | None = None
        self._original_modules: list[tuple[Any, str, Any]] = []
        self._active_emitter: native_adapter.TraceEmitter | None = None

    @classmethod
    def attach(
        cls,
        model: Any,
        registry: ModuleRegistry,
        *,
        cache_observer: Callable[[native_adapter.TraceEmitter, Any], Any],
        run_id_factory: Callable[[], str] | None = None,
    ) -> "NativeMLXAdapter":
        adapter = cls(model, registry, cache_observer=cache_observer, run_id_factory=run_id_factory)
        adapter._attach()
        return adapter

    def _layers(self) -> Any:
        try:
            return self.model.language_model.model.layers
        except AttributeError as exc:
            raise protocol.ProtocolError("model does not expose native language_model.model.layers") from exc

    def _attach(self) -> None:
        if self._attached:
            raise protocol.ProtocolError("adapter is already attached")
        layers = self._layers()
        if len(layers) != self.registry.layer_count:
            raise protocol.ProtocolError("model layer count differs from frozen module registry")
        self._original_layers = list(layers)
        try:
            for spec in sorted(self.registry.modules, key=lambda item: len(item.module_path.split(".")), reverse=True):
                layer = layers[spec.layer_index]
                parent, component = _resolve_parent(layer, spec.module_path)
                target = _get_child(parent, component)
                if not callable(target):
                    raise protocol.ProtocolError(f"declared module is not callable: layer={spec.layer_index} path={spec.module_path}")
                self._original_modules.append((parent, component, target))
                _set_child(parent, component, _ModuleProxy(self, target, spec.layer_index, spec.module_path))
            self.model.language_model.model.layers = [
                _LayerProxy(self, layer, index) for index, layer in enumerate(layers)
            ]
            self._attached = True
        except BaseException:
            self.detach()
            raise

    def detach(self) -> None:
        if self._original_layers is not None:
            for parent, component, target in reversed(self._original_modules):
                _set_child(parent, component, target)
            self.model.language_model.model.layers = self._original_layers
        self._attached = False
        self._original_layers = None
        self._original_modules = []
        self._active_emitter = None

    def forward(
        self,
        input_ids: Any,
        *,
        cache: Any = None,
        native_forward: Callable[[Any, Any], Any] | None = None,
        event_manifest_sha256: str | None = None,
    ) -> native_adapter.NativeRun:
        """Run a model-specific native forward with explicit boundary hooks.

        The declared module paths are wrapped automatically.  Cache/state
        operations remain an explicit context observer because MLX cache
        implementations can mutate through opaque methods.
        """

        if not self._attached:
            raise protocol.ProtocolError("adapter must be attached before forward")
        values = _value_list(input_ids)
        while isinstance(values, list) and values and isinstance(values[0], list):
            values = values[0]
        tokens = list(values) if isinstance(values, list) else [values]
        expectation = self.registry.expectation(token_count=len(tokens))
        adapter = native_adapter.NativeModelAdapter(expectation, run_id_factory=self.run_id_factory)

        def run_forward(emitter: native_adapter.TraceEmitter, values: Sequence[Any]) -> Any:
            self._active_emitter = emitter
            with self.cache_observer(emitter, cache):
                output = native_forward(self.model, cache) if native_forward is not None else self.model(input_ids, cache=cache)
            shape, dtype = _shape_dtype(output)
            emitter.output(output_digest=native_adapter.digest_value(_value_list(output)), shape=shape, dtype=dtype)
            return output

        try:
            return adapter.execute(tokens, run_forward, event_manifest_sha256=event_manifest_sha256)
        finally:
            self.detach()

    def emit_layer(self, emitter: native_adapter.TraceEmitter, layer_index: int, value: Any, callback: Callable[[], Any]) -> Any:
        shape, dtype = _shape_dtype(value)
        with emitter.layer(layer_index, shape=shape, dtype=dtype, value_digest=native_adapter.digest_value(getattr(value, "tolist", lambda: value)())) as complete:
            output = callback()
            output_shape = getattr(output, "shape", shape)
            output_dtype = str(getattr(output, "dtype", dtype))
            complete(output_digest=native_adapter.digest_value(getattr(output, "tolist", lambda: output)()), output_shape=output_shape, output_dtype=output_dtype)
            return output

    def emit_module(self, emitter: native_adapter.TraceEmitter, layer_index: int, module_path: str, value: Any, callback: Callable[[], Any]) -> Any:
        shape, dtype = _shape_dtype(value)
        with emitter.module(layer_index, module_path, shape=shape, dtype=dtype, value_digest=native_adapter.digest_value(getattr(value, "tolist", lambda: value)())) as complete:
            output = callback()
            output_shape = getattr(output, "shape", shape)
            output_dtype = str(getattr(output, "dtype", dtype))
            complete(output_digest=native_adapter.digest_value(getattr(output, "tolist", lambda: output)()), output_shape=output_shape, output_dtype=output_dtype)
            return output

    def __enter__(self) -> "NativeMLXAdapter":
        if not self._attached:
            self._attach()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.detach()


def registry_from_paths(
    paths: Iterable[tuple[int, str]],
    layer_count: int,
    *,
    cache_read_count: int = 0,
    cache_write_count: int = 0,
    state_transition_count: int = 0,
    intervention_count: int = 0,
) -> ModuleRegistry:
    registry = ModuleRegistry(
        tuple(ModuleSpec(layer, path) for layer, path in paths),
        layer_count,
        cache_read_count,
        cache_write_count,
        state_transition_count,
        intervention_count,
    )
    registry.validate()
    return registry
