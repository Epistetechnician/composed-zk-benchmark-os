from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r9_profile_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def inventory():
    names = [
        f"base_model.model.model.layers.{layer}.self_attn.{projection}."
        f"lora_{side}.default.weight"
        for layer in range(24)
        for projection in MODULE.EXPECTED_TARGETS
        for side in ("A", "B")
    ]
    body = {
        "target_modules": MODULE.EXPECTED_TARGETS,
        "layers": 24,
        "targeted_modules": 96,
        "trainable_tensors": 192,
        "trainable_parameters": 3_981_312,
        "trainable_names": names,
    }
    return {**body, "inventory_sha256": MODULE.canonical_hash(body)}


def test_inventory_accepts_exact_attention_coverage() -> None:
    assert MODULE.validate_inventory(inventory()) == []


def test_inventory_rejects_expert_and_hash_drift() -> None:
    packet = inventory()
    packet["trainable_names"][0] = "model.layers.0.mlp.experts.down_proj"
    errors = MODULE.validate_inventory(packet)
    assert "inventory forbidden name" in errors
    assert "inventory_sha256" in errors


def test_checkpoint_geometry_is_exactly_checkpoint_bound() -> None:
    assert MODULE.EXPECTED_GEOMETRY["num_hidden_layers"] == 24
    assert len(MODULE.EXPECTED_GEOMETRY["layer_types"]) == 24
    assert MODULE.EXPECTED_GEOMETRY["checkpoint_config_sha256"].startswith(
        "sha256:"
    )


def test_memory_and_missing_artifact_fail_closed(tmp_path: Path) -> None:
    assert MODULE.validate_memory(
        {"allocated_bytes": MODULE.MODEL_READY_MAX_BYTES + 1},
        key="allocated_bytes",
        ceiling=MODULE.MODEL_READY_MAX_BYTES,
        label="model_ready",
    ) == ["memory:model_ready"]
    assert MODULE.validate(tmp_path, tmp_path) == {
        "valid": False,
        "errors": ["profile artifact files missing"],
    }
