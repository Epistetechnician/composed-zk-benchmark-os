from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r11_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_expected_packet_passes_all_balancing_gates() -> None:
    report = MODULE.validate(MODULE.expected_packet())
    assert report["valid"] is True
    assert report["query_count"] == 96
    assert set(report["target_counts"].values()) == {8}
    assert set(report["target_position_counts"].values()) == {8}


def test_validator_rejects_target_position_and_seal_tampering() -> None:
    packet = deepcopy(MODULE.expected_packet())
    packet["cases"][0]["target"] = MODULE.LABELS[1]
    packet["assessment_present"] = True
    report = MODULE.validate(packet)
    assert report["valid"] is False
    assert {"canonical_packet", "target_balance", "target_position_balance", "sealed_boundary"} <= set(report["errors"])


def test_validator_rejects_nonpacket() -> None:
    assert MODULE.validate([]) == {
        "valid": False,
        "errors": ["packet_type"],
        "claim_ceiling": None,
    }
