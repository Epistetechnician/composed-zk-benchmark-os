"""State slice: astral-trace-completeness-gemma3-end-to-end-v2."""

import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol_v2 as protocol
import registry_v2


def test_registry_covers_every_layer_and_all_declared_boundaries():
    inputs = registry_v2.expected_input_paths()
    outputs = registry_v2.expected_output_paths()
    assert Counter(inputs) == Counter(outputs)
    assert "model.rotary_emb" in inputs
    assert "model.rotary_emb_local" in inputs
    assert len(registry_v2.attention_paths()) == protocol.LAYER_COUNT
    for layer in range(protocol.LAYER_COUNT):
        prefix = f"model.layers.{layer}"
        for suffix in ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj", "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj"):
            assert f"{prefix}.{suffix}" in inputs
