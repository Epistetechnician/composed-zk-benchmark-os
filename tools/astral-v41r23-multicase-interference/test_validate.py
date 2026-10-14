from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r23_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def score(correct=True, margin=3.0):
    return {"target": "a", "selected": "a" if correct else "b", "correct": correct,
            "candidate_log_probabilities": {"a": margin, "b": 0.0, "c": -1.0, "d": -2.0}}


def receipts(ratio=0.05):
    return ([{"loss": 10.0}] * 8) + ([{"loss": 2.0}] * 48) + ([{"loss": 10.0 * ratio}] * 8)


def arm(shared=True, passing=4, protected=0.99):
    cases = {f"c{i}": {"exact_after": score(i < passing), "receipts": receipts(),
                        "reload": {"state_exact": True},
                        "protected_before": {"accuracy": 1.0},
                        "protected_after": {"accuracy": protected}} for i in MODULE.INDICES}
    if shared:
        return {"cases": cases, "reload": {"state_exact": True},
                "protected_before": {"accuracy": 1.0}, "protected_after": {"accuracy": protected}}
    return {"cases": cases}


def test_contract_is_independently_rederived() -> None:
    instrument = MODULE.BASE.INSTRUMENT.expected_packet(); packet = MODULE.expected_contract(instrument)
    assert packet["examples_per_case_per_arm"] == 256
    assert packet["oracle_module_routing"] is True
    assert packet["gates"]["maximum_protected_retention_drop"] == 0.02


def test_decision_requires_effect_and_retention() -> None:
    result = MODULE.decision(arm(passing=2), arm(shared=False))
    assert result["candidate_keep"] is True
    assert result["primary_metric_modular_minus_shared_passing_cases"] == 2
    result = MODULE.decision(arm(passing=2), arm(shared=False, protected=0.5))
    assert result["interpretation"] == "ModularAcquisitionOnlyRetentionBlocked"
    assert result["candidate_keep"] is False


def test_shared_success_does_not_claim_interference() -> None:
    result = MODULE.decision(arm(protected=0.5), arm(shared=False, protected=0.5))
    assert result["interpretation"] == "FourCaseAcquisitionRetentionBlocked"
    assert result["primary_metric_modular_minus_shared_passing_cases"] == 0


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["interference artifact files missing"]}
