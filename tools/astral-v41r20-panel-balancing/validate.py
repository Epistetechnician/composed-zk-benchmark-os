from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


BASE_PATH = Path(__file__).parents[1] / "astral-v41r13-acquisition-pilot" / "validate.py"
SPEC = importlib.util.spec_from_file_location("v41r20_base_validator", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

VERSION = "mesh.astral_v41r20_panel_balancing.v1"
STATE_SLICE = "V41R20ProspectiveGradientBalancingIntervention"
CLAIM_CEILING = "RemoteH100PanelBalancedAcquisitionDevelopmentV41R20"
PANELS = ("bridge", "terminal", "protected")
SHARES = {"bridge": 0.375, "terminal": 0.375, "protected": 0.25}
BASELINE_SHA256 = "sha256:893451b417e6654096e87e7494e638f37daf0efe5cb73c2eacf28a6b415966b3"


def expected_contract(instrument_hash: str) -> dict[str, Any]:
    prior = BASE.expected_contract(instrument_hash)
    prior.update(
        {
            "version": "mesh.astral_v41r15_equal_example_contract.v1",
            "state_slice": "V41R15AcquisitionFailureDiagnosisAndAlternativeDesign",
            "loss_weighting": "equal_example",
            "expected_example_weight": 0.25,
            "expected_example_shares": SHARES,
            "scientific_delta_from_v41r14": "token_weighted_to_equal_example_only",
        }
    )
    prior.pop("contract_sha256", None)
    body = {
        **prior,
        "version": "mesh.astral_v41r20_panel_balancing_contract.v1",
        "state_slice": STATE_SLICE,
        "baseline": {"method": "V41R15_equal_example", "result_sha256": BASELINE_SHA256},
        "scientific_delta_from_baseline": "panel_gradient_l2_normalization_only",
        "panel_order": list(PANELS),
        "panel_shares": SHARES,
        "normalization": "whole_adapter_panel_l2_then_weighted_sum_then_unit_l2",
        "normalization_epsilon": 1.0e-12,
        "all_trainable_tensors": True,
        "layer_selection": None,
        "diagnostic_layer_statistics_used": False,
        "tuning_permitted": False,
        "assessment_opened": False,
    }
    return {**body, "contract_sha256": BASE.canonical_hash(body)}


def decision(no_update, persistent, before, after, reload_exact, steps):
    prior, errors = BASE.decision(no_update, persistent, before, after, reload_exact, steps)
    return ("PanelBalancedSignal" if prior == "PilotAcquisitionSignal" else "PanelBalancedNoSignal", errors)


def receipt_errors(receipts: Any) -> list[str]:
    if not isinstance(receipts, list) or len(receipts) != 64:
        return ["panel_balanced_receipts"]
    errors: set[str] = set()
    for step, receipt in enumerate(receipts):
        if receipt.get("step") != step or receipt.get("microbatch_count") != 4:
            errors.add("panel_balanced_step_census")
        rows = receipt.get("accumulator_receipts")
        if not isinstance(rows, list) or len(rows) != 4:
            errors.add("panel_balanced_accumulator_receipts")
            continue
        by_panel = {panel: [] for panel in PANELS}
        for row in rows:
            panel = row.get("panel")
            if panel not in by_panel:
                errors.add("panel_balanced_panel_names")
                continue
            by_panel[panel].append(row)
            norm = row.get("panel_raw_norm")
            combined = row.get("combined_pre_unit_norm")
            if not isinstance(norm, (int, float)) or not math.isfinite(norm) or norm <= 1.0e-12:
                errors.add("panel_balanced_panel_norm")
            if not isinstance(combined, (int, float)) or not math.isfinite(combined) or combined <= 1.0e-12:
                errors.add("panel_balanced_combined_norm")
        for panel, panel_rows in by_panel.items():
            if not panel_rows:
                errors.add("panel_balanced_panel_census")
                continue
            if abs(sum(row.get("weight", -1.0) for row in panel_rows) - SHARES[panel]) > 1.0e-12:
                errors.add("panel_balanced_panel_share")
            if len({row.get("panel_raw_norm") for row in panel_rows}) != 1:
                errors.add("panel_balanced_norm_binding")
        if abs(sum(row.get("weight", -1.0) for row in rows) - 1.0) > 1.0e-12:
            errors.add("panel_balanced_total_share")
        if receipt.get("microbatch_weights") != [row.get("weight") for row in rows]:
            errors.add("panel_balanced_receipt_binding")
    return sorted(errors)


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    report = BASE.validate(
        artifact,
        rgs_root,
        expected_version=VERSION,
        expected_state_slice=STATE_SLICE,
        contract_builder=expected_contract,
        decision_builder=decision,
        expected_claim_ceiling=CLAIM_CEILING,
        runner_relative="scripts/run_v41r20_panel_balancing.py",
        method_relative="mesh_brain/meshmodel/v41r20_panel_balancing.py",
        report_version="astral.v41r20_panel_balancing_validation.v1",
    )
    if not (artifact / "pilot-result.json").is_file():
        return report
    result = json.loads((artifact / "pilot-result.json").read_text())
    errors = set(report.get("errors", []))
    errors.update(receipt_errors(result.get("update", {}).get("receipts")))
    report["errors"] = sorted(errors)
    report["valid"] = not errors
    report["claim_ceiling"] = result.get("claim_ceiling") if not errors else None
    if not errors:
        persistent = result["persistent"]["metrics"]["overall_accuracy"]
        report["comparison"] = {
            "baseline_result_sha256": BASELINE_SHA256,
            "baseline_persistent_accuracy": 25 / 96,
            "candidate_persistent_accuracy": persistent,
            "candidate_minus_baseline": persistent - 25 / 96,
            "all_hard_gates_pass": result["classification"] == "PanelBalancedSignal",
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.artifact.resolve(), args.rgs_root.resolve())
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.write_text(text)
    print(text, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
