"""Independent validator for V41R28 local surrogate worker artifacts.

Recomputes projection geometry, gates, census, digests, and claim boundaries
from a cell artifact directory without importing the runner's decision path.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

STATE_SLICE = "V41R28LocalSurrogateAcquisitionGateCharacterization"
CLAIM_CEILING = "LocalSurrogateAcquisitionGateCharacterizationV41R28"
FROZEN_CONTRACT = "sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e"
MARGIN_FLOOR = 2.0
LOSS_RATIO_MAXIMUM = 0.10
STEPS_PER_CASE = 64
PROTECTED_ACCURACY_MINIMUM = 0.98

SUBSTRATE_PINS = {
    "llama-3.2-1b": ("35e396644bca888eec399f9c0f843ec7fa78b8f8c5e06841661be62b4edf96dd",
                     "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b"),
    "qwen2.5-0.5b": ("ddffab9cbc7bf6dde941c6724841eeca8981fcfa81ca20ff8efff1396326d153",
                     "a8506e7111b80c6d8635951a02eab0f4e1a8e4e5772da83846579e97b16f61bf"),
}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_cell(artifact_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    artifact_dir = Path(artifact_dir)
    result_path = artifact_dir / "worker-result.json"
    if not result_path.is_file():
        return {"version": "astral.v41r28_surrogate_artifact_validation.v1", "valid": False,
                "errors": ["worker_result_missing"], "artifact_dir": str(artifact_dir)}
    result = json.loads(result_path.read_text())

    def equal(name: str, actual: Any, expected: Any) -> None:
        if actual != expected:
            errors.append(name)

    def flag(name: str, value: Any, expected: bool) -> None:
        if value is not expected:
            errors.append(name)

    equal("state_slice", result.get("state_slice"), STATE_SLICE)
    equal("claim_ceiling", result.get("claim_ceiling"), CLAIM_CEILING)
    flag("tune_opened", result.get("tune_opened"), False)
    flag("assessment_opened", result.get("assessment_opened"), False)
    equal("contract_sha256", result.get("source", {}).get("rgs_contract_sha256"), FROZEN_CONTRACT)

    substrate_key = result.get("substrate", {}).get("key")
    if substrate_key not in SUBSTRATE_PINS:
        errors.append("substrate_unknown")
    else:
        model_sha, tokenizer_sha = SUBSTRATE_PINS[substrate_key]
        equal("substrate_model_pin", result.get("substrate", {}).get("model_safetensors_sha256"), model_sha)
        equal("substrate_tokenizer_pin", result.get("substrate", {}).get("tokenizer_json_sha256"), tokenizer_sha)

    body = {key: value for key, value in result.items() if key != "result_sha256"}
    equal("result_sha256", result.get("result_sha256"), canonical_hash(body))

    manifest_path = artifact_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        errors.append("manifest_missing")
    else:
        for line in manifest_path.read_text().splitlines():
            digest, name = line.split("  ", 1)
            target = artifact_dir / name
            if not target.is_file() or sha256_file(target) != digest:
                errors.append(f"manifest_digest:{name}")

    receipts = result.get("candidate", {}).get("update", {}).get("receipts", [])
    if len(receipts) != 256:
        errors.append("receipt_census")
    cases = result.get("candidate", {}).get("cases", {})
    if len(cases) != 4:
        errors.append("case_census")
    for case_id, packet in cases.items():
        case_receipts = packet.get("receipts", [])
        if len(case_receipts) != STEPS_PER_CASE:
            errors.append(f"case_receipt_census:{case_id}")
            continue
        for row in case_receipts:
            tolerance_expected = 64.0 * row["projection_dtype_epsilon"] * max(
                math.sqrt(row["projected_gradient_norm_sq"] * row["protected_gradient_norm_sq"]), 1.0)
            if abs(row["projection_roundoff_tolerance"] - tolerance_expected) > 1e-12 * max(1.0, tolerance_expected):
                errors.append(f"tolerance_recomputation:{case_id}:{row['step']}")
                break
            if row["post_projection_dot"] < -row["projection_roundoff_tolerance"]:
                errors.append(f"projection_invariant:{case_id}:{row['step']}")
                break
            if row["projection_applied"] != (row["pre_projection_dot"] < 0):
                errors.append(f"projection_condition:{case_id}:{row['step']}")
                break
            if row["projection_applied"]:
                coefficient = row["pre_projection_dot"] / row["protected_gradient_norm_sq"]
                if abs(row["projection_coefficient"] - coefficient) > 1e-12:
                    errors.append(f"coefficient_recomputation:{case_id}:{row['step']}")
                    break

    reload_exact = result.get("candidate", {}).get("reload", {}).get("state_exact")
    gates_recomputed = {}
    for case_id, packet in cases.items():
        exact_after = packet.get("exact_after", {})
        scores = exact_after.get("candidate_log_probabilities", {})
        target = exact_after.get("target")
        margin = float(scores.get(target, -math.inf)) - max(
            (float(value) for key, value in scores.items() if key != target), default=math.inf)
        case_receipts = packet.get("receipts", [])
        if len(case_receipts) == STEPS_PER_CASE:
            first = sum(row["acquisition_loss"] for row in case_receipts[:8]) / 8
            last = sum(row["acquisition_loss"] for row in case_receipts[-8:]) / 8
            ratio = last / first if first > 0 else math.inf
        else:
            ratio = math.inf
        case_errors = []
        if exact_after.get("correct") is not True:
            case_errors.append("selected_target")
        if margin < MARGIN_FLOOR:
            case_errors.append("target_margin")
        if ratio > LOSS_RATIO_MAXIMUM:
            case_errors.append("loss_ratio")
        if reload_exact is not True:
            case_errors.append("reload_exact")
        gates_recomputed[case_id] = {"pass": not case_errors, "errors": case_errors}
        recorded = result.get("case_gates", {}).get(case_id, {})
        if recorded.get("pass") != (not case_errors):
            errors.append(f"gate_recomputation:{case_id}")
        if recorded.get("target_margin_nats") is not None and \
                abs(recorded["target_margin_nats"] - margin) > 1e-9:
            errors.append(f"margin_recomputation:{case_id}")

    passing_recomputed = sum(gate["pass"] for gate in gates_recomputed.values())
    equal("acquisition_cases_passing", result.get("acquisition_cases_passing"), passing_recomputed)

    protected_after = result.get("candidate", {}).get("protected_after", {})
    rows = protected_after.get("rows", [])
    if len(rows) == 16:
        accuracy_recomputed = sum(row.get("correct") is True for row in rows) / 16
        if abs(protected_after.get("accuracy", -1.0) - accuracy_recomputed) > 1e-12:
            errors.append("protected_accuracy_recomputation")
    else:
        errors.append("protected_after_census")

    pass_recomputed = (passing_recomputed == 4
                       and protected_after.get("accuracy", 0.0) >= PROTECTED_ACCURACY_MINIMUM
                       and reload_exact is True)
    equal("pass_recomputation", result.get("pass"), pass_recomputed)
    equal("classification", result.get("classification"), "V41R28SurrogateWorkerComplete")
    equal("status", result.get("status"), "completed")

    return {"version": "astral.v41r28_surrogate_artifact_validation.v1",
            "valid": not errors, "errors": errors,
            "artifact_dir": str(artifact_dir),
            "run_id": result.get("run_id"),
            "substrate": substrate_key,
            "pass": result.get("pass"),
            "claim_ceiling": CLAIM_CEILING,
            "independent_of_runner_decision_path": True}


def validate_blocked(artifact_dir: Path) -> dict[str, Any]:
    artifact_dir = Path(artifact_dir)
    blocked_path = artifact_dir / "preflight-blocked.json"
    if not blocked_path.is_file():
        return {"version": "astral.v41r28_surrogate_artifact_validation.v1", "valid": False,
                "errors": ["preflight_blocked_record_missing"], "artifact_dir": str(artifact_dir)}
    record = json.loads(blocked_path.read_text())
    errors: list[str] = []
    if record.get("classification") != "V41R28SurrogatePreflightBlocked":
        errors.append("blocked_classification")
    if record.get("state_slice") != STATE_SLICE:
        errors.append("blocked_state_slice")
    if record.get("tune_opened") is not False or record.get("assessment_opened") is not False:
        errors.append("blocked_flags")
    preflight = record.get("preflight", {})
    if not isinstance(preflight.get("protected_accuracy"), (int, float)):
        errors.append("blocked_preflight_accuracy")
    return {"version": "astral.v41r28_surrogate_artifact_validation.v1",
            "valid": not errors, "errors": errors,
            "artifact_dir": str(artifact_dir),
            "classification": "V41R28SurrogatePreflightBlocked",
            "claim_ceiling": CLAIM_CEILING}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--blocked", action="store_true",
                        help="validate a preflight-blocked record instead of a worker result")
    args = parser.parse_args()
    report = validate_blocked(args.artifact_dir) if args.blocked else validate_cell(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
