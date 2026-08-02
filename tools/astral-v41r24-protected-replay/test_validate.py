from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py"); SPEC = importlib.util.spec_from_file_location("v41r24_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


def test_contract_rederives_baseline_and_weights() -> None:
    packet = MODULE.expected_contract(MODULE.BASE.INSTRUMENT.expected_packet())
    assert packet["immutable_baseline"]["result_sha256"] == MODULE.BASELINE_SHA
    assert packet["panel_weights"] == {"acquisition": 0.75, "protected": 0.25}
    assert packet["acquisition_examples_per_case"] == 256


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["protected replay artifact files missing"]}


def test_decision_rejects_subthreshold_improvement() -> None:
    score = {"target": "a", "selected": "a", "correct": True,
             "candidate_log_probabilities": {"a": 3.0, "b": 0.0, "c": -1.0, "d": -2.0}}
    receipts = ([{"acquisition_loss": 10.0}] * 8) + ([{"acquisition_loss": 2.0}] * 48) + ([{"acquisition_loss": 0.5}] * 8)
    candidate = {"cases": {f"c{i}": {"exact_after": score, "receipts": receipts} for i in MODULE.INDICES},
                 "reload": {"state_exact": True}, "protected_before": {"accuracy": 1.0},
                 "protected_after": {"accuracy": 0.9375}}
    result = MODULE.decision(candidate)
    assert result["interpretation"] == "ProtectedReplayImprovedButUnqualified"
    assert result["candidate_keep"] is False
