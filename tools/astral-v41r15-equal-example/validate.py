from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


BASE_PATH = Path(__file__).parents[1] / "astral-v41r13-acquisition-pilot" / "validate.py"
SPEC = importlib.util.spec_from_file_location("v41r15_base_validator", BASE_PATH)
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

VERSION = "mesh.astral_v41r15_equal_example_acquisition.v1"
STATE_SLICE = "V41R15AcquisitionFailureDiagnosisAndAlternativeDesign"
CLAIM_CEILING = "RemoteH100EqualExampleAcquisitionDevelopmentV41R15"


def expected_contract(instrument_hash: str) -> dict[str, Any]:
    prior = BASE.expected_contract(instrument_hash)
    body = {
        **{key: value for key, value in prior.items() if key != "contract_sha256"},
        "version": "mesh.astral_v41r15_equal_example_contract.v1",
        "state_slice": STATE_SLICE,
        "loss_weighting": "equal_example",
        "expected_example_weight": 0.25,
        "expected_example_shares": {
            "bridge": 0.375,
            "terminal": 0.375,
            "protected": 0.25,
        },
        "scientific_delta_from_v41r14": "token_weighted_to_equal_example_only",
    }
    return {**body, "contract_sha256": BASE.canonical_hash(body)}


def decision(no_update, persistent, before, after, reload_exact, steps):
    prior, errors = BASE.decision(no_update, persistent, before, after, reload_exact, steps)
    return (
        "EqualExampleDevelopmentSignal"
        if prior == "PilotAcquisitionSignal"
        else "EqualExampleDevelopmentNoSignal",
        errors,
    )


def equal_weight_errors(receipts: Any) -> list[str]:
    if not isinstance(receipts, list) or len(receipts) != 64:
        return ["equal_example_receipts"]
    for receipt in receipts:
        if receipt.get("microbatch_weights") != [0.25, 0.25, 0.25, 0.25]:
            return ["equal_example_weights"]
    return []


def validate(artifact: Path, rgs_root: Path) -> dict[str, Any]:
    report = BASE.validate(
        artifact,
        rgs_root,
        expected_version=VERSION,
        expected_state_slice=STATE_SLICE,
        contract_builder=expected_contract,
        decision_builder=decision,
        expected_claim_ceiling=CLAIM_CEILING,
        runner_relative="scripts/run_v41r15_equal_example_development.py",
        method_relative="mesh_brain/meshmodel/v41r15_equal_example.py",
        report_version="astral.v41r15_equal_example_validation.v1",
    )
    if not (artifact / "pilot-result.json").is_file():
        return report
    result = json.loads((artifact / "pilot-result.json").read_text())
    errors = set(report.get("errors", []))
    receipts = result.get("update", {}).get("receipts")
    errors.update(equal_weight_errors(receipts))
    report["errors"] = sorted(errors)
    report["valid"] = not errors
    report["claim_ceiling"] = result.get("claim_ceiling") if not errors else None
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
