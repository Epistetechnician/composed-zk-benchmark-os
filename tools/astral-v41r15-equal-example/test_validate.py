from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r15_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def metric(value: float) -> dict:
    return {
        "overall_accuracy": value,
        "accuracy_by_class": {key: value for key in MODULE.BASE.CLASSES},
    }


def test_contract_is_independent_and_equal_example() -> None:
    packet = MODULE.expected_contract("sha256:instrument")
    assert packet["loss_weighting"] == "equal_example"
    assert packet["expected_example_weight"] == 0.25
    assert packet["contract_sha256"] == MODULE.BASE.canonical_hash(
        {key: value for key, value in packet.items() if key != "contract_sha256"}
    )


def test_decision_preserves_gates_but_marks_development() -> None:
    assert MODULE.decision(metric(0.25), metric(0.75), 1.0, 1.0, True, 64) == (
        "EqualExampleDevelopmentSignal",
        [],
    )
    classification, errors = MODULE.decision(metric(0.25), metric(0.5), 1.0, 0.75, True, 64)
    assert classification == "EqualExampleDevelopmentNoSignal"
    assert {"acquisition_overall", "protected_drop"} <= set(errors)


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {
        "valid": False,
        "errors": ["pilot artifact files missing"],
    }


def test_equal_weight_gate_rejects_token_weighted_receipt() -> None:
    receipts = [{"microbatch_weights": [0.25] * 4} for _ in range(64)]
    assert MODULE.equal_weight_errors(receipts) == []
    receipts[12]["microbatch_weights"] = [0.4, 0.2, 0.2, 0.2]
    assert MODULE.equal_weight_errors(receipts) == ["equal_example_weights"]
