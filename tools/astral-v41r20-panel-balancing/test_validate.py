from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r20_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def metric(value: float) -> dict:
    return {"overall_accuracy": value, "accuracy_by_class": {key: value for key in MODULE.BASE.CLASSES}}


def valid_receipts() -> list[dict]:
    result = []
    for step in range(64):
        rows = [
            {"panel": "bridge", "weight": 0.1875, "panel_raw_norm": 2.0, "combined_pre_unit_norm": 0.8},
            {"panel": "terminal", "weight": 0.375, "panel_raw_norm": 3.0, "combined_pre_unit_norm": 0.8},
            {"panel": "protected", "weight": 0.25, "panel_raw_norm": 4.0, "combined_pre_unit_norm": 0.8},
            {"panel": "bridge", "weight": 0.1875, "panel_raw_norm": 2.0, "combined_pre_unit_norm": 0.8},
        ]
        result.append({"step": step, "microbatch_count": 4, "microbatch_weights": [row["weight"] for row in rows], "accumulator_receipts": rows})
    return result


def test_contract_is_independently_rederived_and_has_no_layer_selection() -> None:
    packet = MODULE.expected_contract("sha256:instrument")
    assert packet["scientific_delta_from_baseline"] == "panel_gradient_l2_normalization_only"
    assert packet["baseline"]["result_sha256"] == MODULE.BASELINE_SHA256
    assert packet["layer_selection"] is None
    assert packet["diagnostic_layer_statistics_used"] is False


def test_decision_preserves_all_frozen_hard_gates() -> None:
    assert MODULE.decision(metric(0.25), metric(0.75), 1.0, 1.0, True, 64) == ("PanelBalancedSignal", [])
    classification, errors = MODULE.decision(metric(0.25), metric(0.5), 1.0, 0.75, True, 64)
    assert classification == "PanelBalancedNoSignal"
    assert {"acquisition_overall", "protected_drop"} <= set(errors)


def test_receipts_bind_panel_shares_and_norms() -> None:
    receipts = valid_receipts()
    assert MODULE.receipt_errors(receipts) == []
    receipts[3]["accumulator_receipts"][0]["weight"] = 0.2
    assert {"panel_balanced_panel_share", "panel_balanced_total_share", "panel_balanced_receipt_binding"} <= set(MODULE.receipt_errors(receipts))


def test_receipts_reject_nonfinite_norm_and_missing_panel() -> None:
    receipts = valid_receipts()
    receipts[0]["accumulator_receipts"][2]["panel_raw_norm"] = float("nan")
    assert "panel_balanced_panel_norm" in MODULE.receipt_errors(receipts)
    receipts = valid_receipts()
    receipts[0]["accumulator_receipts"][2]["panel"] = "bridge"
    assert "panel_balanced_panel_census" in MODULE.receipt_errors(receipts)


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["pilot artifact files missing"]}


def test_torch_distribution_metadata_requires_exact_cuda_binding() -> None:
    assert MODULE.valid_torch_runtime({"torch": "2.10.0", "cuda": "12.8"})
    assert MODULE.valid_torch_runtime({"torch": "2.10.0+cu128", "cuda": "12.8"})
    assert not MODULE.valid_torch_runtime({"torch": "2.10.0", "cuda": "12.4"})
    assert not MODULE.valid_torch_runtime({"torch": "2.9.0", "cuda": "12.8"})
