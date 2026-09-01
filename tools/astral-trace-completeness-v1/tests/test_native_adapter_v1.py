"""State slice: astral-trace-completeness-native-instrument-v1."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import native_adapter
import protocol


def _fixture_forward(hooks, tokens):
    for layer_index in range(2):
        with hooks.layer(layer_index, shape=(1, len(tokens), 4), dtype="float32", value_digest=native_adapter.digest_value([layer_index, "layer-input"])) as complete_layer:
            with hooks.module(layer_index, "attention", shape=(1, len(tokens), 4), dtype="float32", value_digest=native_adapter.digest_value([layer_index, "attention-input"])) as complete_attention:
                if layer_index == 0:
                    hooks.cache_read("kv.layer0", value_digest=native_adapter.digest_value([1, 2]))
                else:
                    hooks.state_transition(
                        "residual.layer1",
                        before_digest=native_adapter.digest_value([1]),
                        after_digest=native_adapter.digest_value([2]),
                    )
                complete_attention(output_digest=native_adapter.digest_value([layer_index, 0]), output_shape=(1, len(tokens), 4), output_dtype="float32")
            with hooks.module(layer_index, "mlp", shape=(1, len(tokens), 4), dtype="float32", value_digest=native_adapter.digest_value([layer_index, "mlp-input"])) as complete_mlp:
                if layer_index == 1:
                    hooks.cache_write("kv.layer1", value_digest=native_adapter.digest_value([3, 4]))
                complete_mlp(output_digest=native_adapter.digest_value([layer_index, 1]), output_shape=(1, len(tokens), 4), output_dtype="float32")
            complete_layer(output_digest=native_adapter.digest_value([layer_index]), output_shape=(1, len(tokens), 4), output_dtype="float32")
    hooks.output(output_digest=native_adapter.digest_value([0.1, 0.2]), shape=(1, 2), dtype="float32")
    return [0.1, 0.2]


def test_native_adapter_accounts_tokens_layers_modules_cache_state_and_output():
    expectation = protocol.EventExpectation(
        3,
        2,
        4,
        1,
        1,
        1,
        0,
        expected_module_paths=((0, "attention"), (0, "mlp"), (1, "attention"), (1, "mlp")),
    )
    adapter = native_adapter.NativeModelAdapter(expectation, run_id_factory=lambda: "fixture-run")
    run = adapter.execute([11, 12, 13], _fixture_forward)
    assert run.output == [0.1, 0.2]
    assert run.aggregate["event_counts"]["token"] == 3
    assert run.aggregate["event_counts"]["module_enter"] == 4
    assert run.aggregate["raw_events_retained"] is False


def test_noop_interchange_is_identity_and_emits_typed_intervention():
    expectation = protocol.EventExpectation(1, 1, 1, 0, 0, 0, 1)
    adapter = native_adapter.NativeModelAdapter(expectation, run_id_factory=lambda: "intervention-run")

    def forward(hooks, tokens):
        with hooks.layer(0, shape=(1, 1, 2), dtype="float32", value_digest=native_adapter.digest_value(["layer-input"])) as complete_layer:
            with hooks.module(0, "mlp", shape=(1, 1, 2), dtype="float32", value_digest=native_adapter.digest_value(["module-input"])) as complete_module:
                operator = native_adapter.ActivationInterchangeOperator(boundary="layer0.mlp", mode="noop")
                assert operator.apply(
                    [1, 2],
                    [9, 9],
                    emitter=hooks,
                    token_index=0,
                    layer_index=0,
                    module_path="mlp",
                    state_slot="residual",
                ) == [1, 2]
                complete_module(output_digest=native_adapter.digest_value([1, 2]), output_shape=(1, 1, 2), output_dtype="float32")
            complete_layer(output_digest=native_adapter.digest_value([1, 2]), output_shape=(1, 1, 2), output_dtype="float32")
        hooks.output(output_digest=native_adapter.digest_value([1, 2]), shape=(1, 2), dtype="float32")

    run = adapter.execute([7], forward)
    interventions = [event for event in run.events if event.kind == "intervention"]
    assert len(interventions) == 1
    assert interventions[0].metadata["mode"] == "noop"


def test_incomplete_native_census_fails_closed():
    expectation = protocol.EventExpectation(1, 1, 1, 0, 0, 0, 0)
    adapter = native_adapter.NativeModelAdapter(expectation, run_id_factory=lambda: "incomplete-run")

    def incomplete(hooks, tokens):
        hooks.output(output_digest=native_adapter.digest_value([0]), shape=(1, 1), dtype="float32")

    try:
        adapter.execute([7], incomplete)
    except native_adapter.TraceCompletenessError as exc:
        assert "event census mismatch" in str(exc)
    else:
        raise AssertionError("incomplete native event census was accepted")
