"""Red/green contract tests for the cached small-transformer activation adapter.

State slice: proof-carrying-nano-host-activation-boundary-v1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.proof_carrying_nano_host_activation_boundary_v1.adapter import (
    ActivationAdapterError,
    CachedSmallTransformerAdapter,
    MutationPolicy,
    activation_digest_from_raw,
    parameter_digest,
)


torch = pytest.importorskip("torch")


class _Block(torch.nn.Module):
    def __init__(self, width: int, offset: float) -> None:
        super().__init__()
        self.projection = torch.nn.Linear(width, width, bias=False)
        with torch.no_grad():
            self.projection.weight.copy_(torch.eye(width) + offset)

    def forward(self, hidden, **_kwargs):
        return (self.projection(hidden),)


class _Backbone(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.embed_tokens = torch.nn.Embedding(32, 4)
        self.layers = torch.nn.ModuleList((_Block(4, 0.01), _Block(4, 0.02)))

    def forward(self, input_ids, attention_mask=None, use_cache=False):
        del attention_mask, use_cache
        hidden = self.embed_tokens(input_ids)
        for layer in self.layers:
            hidden = layer(hidden)[0]
        return type("Output", (), {"logits": hidden, "hidden_states": None})()


class _Host(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.model = _Backbone()

    def forward(self, input_ids, attention_mask=None, use_cache=False):
        return self.model(input_ids, attention_mask=attention_mask, use_cache=use_cache)


def _adapter() -> CachedSmallTransformerAdapter:
    host = _Host().eval()
    return CachedSmallTransformerAdapter(
        identity="smollm2-135m-activation-nano-v1",
        model=host,
        host_checkpoint_digest="sha256:" + "1" * 64,
        host_runtime_digest="sha256:" + "2" * 64,
        checkpoint_root=Path("/external/smollm2-135m"),
        model_identity="HuggingFaceTB/SmolLM2-135M@93efa2f097d58c2a74874c7e644dbc9b0cee75a2",
        tokenizer_identity="GPT2Tokenizer",
    )


def test_read_only_capture_binds_hook_location_activation_and_parameter_digests() -> None:
    adapter = _adapter()
    before = parameter_digest(adapter.model)
    capture = adapter.capture_tokens(
        input_ids=(1, 2, 3),
        attention_mask=(1, 1, 1),
        layer=1,
        site="decoder_block_output",
        token_position=2,
        replay_seed=17,
        timestamp="2026-09-17T12:00:00Z",
    )

    assert capture.action["outputs"]["status"] == "ActivationCaptured"
    assert capture.action["outputs"]["hook_reached"] is True
    assert capture.action["outputs"]["activation_digest"].startswith("sha256:")
    assert capture.action["outputs"]["activation_shape"] == [4]
    assert capture.action["outputs"]["activation_dtype"] == "torch.float32"
    assert activation_digest_from_raw(
        capture.raw_activation,
        dtype="torch.float32",
        shape=[4],
    ) == capture.action["outputs"]["activation_digest"]
    assert capture.action["outputs"]["parameter_digest_before"] == before
    assert capture.action["outputs"]["parameter_digest_after"] == before
    assert capture.action["mutation_policy"] == MutationPolicy.read_only().to_dict()
    assert parameter_digest(adapter.model) == before


def test_capture_replays_byte_exactly_and_rejects_wrong_site_or_position() -> None:
    adapter = _adapter()
    capture = adapter.capture_tokens(
        input_ids=(1, 2, 3),
        attention_mask=(1, 1, 1),
        layer=1,
        site="decoder_block_output",
        token_position=2,
        replay_seed=17,
        timestamp="2026-09-17T12:00:00Z",
    )

    replay = adapter.replay(capture.action)
    assert replay.action == capture.action
    assert replay.raw_activation == capture.raw_activation

    with pytest.raises(ActivationAdapterError, match="site"):
        adapter.capture_tokens(
            input_ids=(1, 2, 3),
            attention_mask=(1, 1, 1),
            layer=1,
            site="residual_stream_write",
            token_position=2,
            replay_seed=17,
            timestamp="2026-09-17T12:00:00Z",
        )
    with pytest.raises(ActivationAdapterError, match="token position"):
        adapter.capture_tokens(
            input_ids=(1, 2, 3),
            attention_mask=(1, 1, 1),
            layer=1,
            site="decoder_block_output",
            token_position=3,
            replay_seed=17,
            timestamp="2026-09-17T12:00:00Z",
        )


def test_direct_mutation_policy_constructor_and_model_mutation_fail_closed() -> None:
    with pytest.raises(ActivationAdapterError, match="read-only"):
        MutationPolicy(
            schema="read-only-host-mutation-policy-v1",
            adapter_mode="write",
            allow_forward_hooks=True,
            activation_mutation=True,
            host_parameter_mutation=False,
        )

    adapter = _adapter()
    original_forward = adapter.model.forward

    def mutating_forward(*args, **kwargs):
        with torch.no_grad():
            next(adapter.model.parameters()).add_(1)
        return original_forward(*args, **kwargs)

    adapter.model.forward = mutating_forward
    with pytest.raises(ActivationAdapterError, match="mutated"):
        adapter.capture_tokens(
            input_ids=(1, 2, 3),
            attention_mask=(1, 1, 1),
            layer=1,
            site="decoder_block_output",
            token_position=2,
            replay_seed=17,
            timestamp="2026-09-17T12:00:00Z",
        )
