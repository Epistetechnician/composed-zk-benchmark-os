from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r13_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def metric(value: float) -> dict:
    return {"overall_accuracy": value, "accuracy_by_class": {key: value for key in MODULE.CLASSES}}


def test_decision_passes_and_fails_closed() -> None:
    assert MODULE.decision(metric(0.25), metric(0.75), 1.0, 1.0, True, 64) == ("PilotAcquisitionSignal", [])
    classification, errors = MODULE.decision(metric(0.25), metric(0.50), 1.0, 0.875, False, 63)
    assert classification == "PilotNoSignal"
    assert {"acquisition_overall", "protected_drop", "reload_exact", "optimizer_steps"} <= set(errors)


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["pilot artifact files missing"]}
