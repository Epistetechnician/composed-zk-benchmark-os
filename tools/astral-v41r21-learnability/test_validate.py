from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r21_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def arm(overall=0.8, composition=0.7, bridge=1.0, terminal=1.0, end=0.7, protected=1.0):
    return {"queries": {"metrics": {"overall_accuracy": overall, "accuracy_by_class": {"composition": composition}}}, "relations": {"bridge_relation": {"accuracy": bridge}, "terminal_relation": {"accuracy": terminal}, "end_to_end": {"accuracy": end}}, "protected_before": {"accuracy": 1.0}, "protected_after": {"accuracy": protected}}


def arms():
    return {"no_update": arm(0.25, 0.25, 0.25, 0.25, 0.25), "direct_oracle": arm(end=1.0), "two_edge": arm(), "two_edge_protected": arm()}


def test_contract_is_independently_rederived() -> None:
    packet = MODULE.expected_contract("sha256:instrument")
    assert packet["arms"] == list(MODULE.ARMS)
    assert packet["examples_per_update_arm"] == 256
    assert packet["layer_selection"] is None


def test_interpretation_order_is_fail_closed() -> None:
    packet = arms(); packet["direct_oracle"]["relations"]["end_to_end"]["accuracy"] = 0.5
    assert MODULE.decision(packet)["interpretation"] == "UpdateSubstrateUnqualified"
    packet = arms(); packet["two_edge"]["relations"]["bridge_relation"]["accuracy"] = 0.5
    assert MODULE.decision(packet)["interpretation"] == "PrimitiveRelationAcquisitionBottleneck"
    packet = arms(); packet["two_edge"]["queries"]["metrics"]["accuracy_by_class"]["composition"] = 0.5
    assert MODULE.decision(packet)["interpretation"] == "CompositionalObjectiveBottleneck"
    packet = arms(); packet["two_edge_protected"]["protected_after"]["accuracy"] = 0.9
    assert MODULE.decision(packet)["interpretation"] == "ProtectedReplayInterference"


def test_runtime_short_spelling_requires_cuda_128() -> None:
    assert MODULE.valid_torch_runtime({"torch": "2.10.0", "cuda": "12.8"})
    assert MODULE.valid_torch_runtime({"torch": "2.10.0+cu128", "cuda": "12.8"})
    assert not MODULE.valid_torch_runtime({"torch": "2.10.0", "cuda": "12.4"})


def test_relation_validator_rejects_binding_and_score_drift() -> None:
    expected = [{"case_id": f"c-{index}", "target": "a", "candidates": ["a", "b", "c", "d"]} for index in range(32)]
    rows = [{**row, "selected": "a", "correct": True, "candidate_log_probabilities": {key: -index for index, key in enumerate(row["candidates"])}} for row in expected]
    assert MODULE.relation_accuracy(rows, expected) == (1.0, [])
    rows[0]["target"] = "b"
    assert "relation_binding" in MODULE.relation_accuracy(rows, expected)[1]


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["learnability artifact files missing"]}
