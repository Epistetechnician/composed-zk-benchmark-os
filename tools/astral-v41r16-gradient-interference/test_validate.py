from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import torch


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r16_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def panels() -> dict:
    result = {panel: {} for panel in MODULE.PANELS}
    for layer in range(24):
        for index in range(8):
            name = f"base.layers.{layer}.probe.{index}"
            result["bridge"][name] = torch.tensor([1.0, 0.0])
            result["terminal"][name] = torch.tensor([1.0, 0.0])
            result["protected"][name] = torch.tensor([-1.0, 0.0]) if layer < 12 else torch.tensor([1.0, 0.0])
    return result


def test_independent_geometry_recomputation() -> None:
    summary, errors = MODULE.recompute(panels())
    assert errors == []
    assert summary["negative_layer_counts"]["acquisition_protected"] == 12
    assert summary["global"]["bridge_terminal"]["cosine"] == pytest.approx(1.0)
    assert summary["global"]["acquisition_protected"]["cosine"] == pytest.approx(0.0)


def test_nonfinite_gradient_fails_closed() -> None:
    packet = panels()
    packet["protected"][next(iter(packet["protected"]))] = torch.tensor([float("nan")])
    summary, errors = MODULE.recompute(packet)
    assert summary is None
    assert "tensor_finite" in errors


def test_contract_and_missing_artifact() -> None:
    packet = MODULE.expected_contract("sha256:instrument")
    assert packet["optimizer_steps"] == 0
    assert packet["selection_rule"] is None
    assert MODULE.validate(Path("/nonexistent-v41r16"), Path("/nonexistent-rgs")) == {
        "valid": False,
        "errors": ["profile artifact files missing"],
    }
