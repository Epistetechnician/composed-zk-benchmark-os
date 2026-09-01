"""State slice: astral-trace-completeness-native-instrument-v1."""

import sys
from contextlib import contextmanager
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import mlx_adapter_v1


class _Tensor:
    shape = (1, 2, 4)
    dtype = "float32"

    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class _Module:
    def __init__(self, child=None):
        self.projection = child

    def __call__(self, value):
        return self.projection(value) if self.projection is not None else value


class _Layer:
    def __init__(self):
        self.attention = _Module(_Module())

    def __call__(self, value):
        return self.attention(value)


class _ModelTree:
    def __init__(self):
        self.layers = [_Layer(), _Layer()]


class _LanguageModel:
    def __init__(self):
        self.model = _ModelTree()


class _Model:
    def __init__(self):
        self.language_model = _LanguageModel()

    def __call__(self, input_ids, cache=None):
        value = _Tensor([[1, 2, 3, 4]])
        for layer in self.language_model.model.layers:
            value = layer(value)
        return value


def test_registry_is_frozen_and_duplicate_paths_fail():
    registry = mlx_adapter_v1.registry_from_paths(((0, "attention"), (1, "mlp")), layer_count=2)
    assert registry.expectation(token_count=1).module_count == 2
    try:
        mlx_adapter_v1.registry_from_paths(((0, "attention"), (0, "attention")), layer_count=1)
    except ValueError as exc:
        assert "duplicates" in str(exc)
    else:
        raise AssertionError("duplicate module registry was accepted")


def test_attach_and_detach_restore_native_layer_list():
    model = _Model()
    original = list(model.language_model.model.layers)
    adapter = mlx_adapter_v1.NativeMLXAdapter.attach(
        model,
        mlx_adapter_v1.registry_from_paths(((0, "attention"),), layer_count=2),
        cache_observer=lambda emitter, cache: None,
    )
    adapter.detach()
    assert model.language_model.model.layers == original


def test_native_mlx_adapter_wraps_declared_layers_and_modules_and_restores_after_forward():
    model = _Model()
    original = list(model.language_model.model.layers)

    @contextmanager
    def cache_observer(emitter, cache):
        yield

    adapter = mlx_adapter_v1.NativeMLXAdapter.attach(
        model,
        mlx_adapter_v1.registry_from_paths(((0, "attention"), (1, "attention")), layer_count=2),
        cache_observer=cache_observer,
        run_id_factory=lambda: "mlx-forward",
    )
    run = adapter.forward(_Tensor([[7, 8]]), cache=None)
    assert run.aggregate["event_counts"]["layer_enter"] == 2
    assert run.aggregate["event_counts"]["module_output"] == 2
    assert model.language_model.model.layers == original


def test_native_mlx_adapter_restores_native_tree_after_forward_exception():
    model = _Model()
    original = list(model.language_model.model.layers)

    @contextmanager
    def cache_observer(emitter, cache):
        yield

    adapter = mlx_adapter_v1.NativeMLXAdapter.attach(
        model,
        mlx_adapter_v1.registry_from_paths(((0, "attention"), (1, "attention")), layer_count=2),
        cache_observer=cache_observer,
    )

    def failing_forward(model, cache):
        raise RuntimeError("fixture failure")

    try:
        adapter.forward(_Tensor([[7, 8]]), cache=None, native_forward=failing_forward)
    except RuntimeError as exc:
        assert str(exc) == "fixture failure"
    else:
        raise AssertionError("failing native forward was accepted")
    assert model.language_model.model.layers == original


def test_nested_module_registry_is_attached_deepest_first_and_restored():
    model = _Model()
    original = list(model.language_model.model.layers)

    @contextmanager
    def cache_observer(emitter, cache):
        yield

    adapter = mlx_adapter_v1.NativeMLXAdapter.attach(
        model,
        mlx_adapter_v1.registry_from_paths(((0, "attention"), (0, "attention.projection"), (1, "attention"), (1, "attention.projection")), layer_count=2),
        cache_observer=cache_observer,
        run_id_factory=lambda: "nested-forward",
    )
    run = adapter.forward(_Tensor([[7, 8]]), cache=None)
    assert run.aggregate["event_counts"]["module_enter"] == 4
    assert model.language_model.model.layers == original
