from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r8_profile_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def inventory():
    names = [
        f"base_model.model.model.layers.{layer}.self_attn.{projection}."
        f"lora_{side}.default.weight"
        for layer in range(36)
        for projection in MODULE.EXPECTED_TARGETS
        for side in ("A", "B")
    ]
    body = {
        "target_modules": MODULE.EXPECTED_TARGETS,
        "layers": 36,
        "targeted_modules": 144,
        "trainable_tensors": 288,
        "trainable_parameters": 5_971_968,
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
