from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any


SEEDS = (411017, 411031, 411043)
Z = 1.959963984540054
LABELS = ("zavren", "kelvix", "morqen", "tulvash")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def expected_acquisition() -> dict[str, Any]:
    cases = []
    for index in range(64):
        subject = "v41r26-subject-" + hashlib.sha256(f"subject|{index}|v41r26".encode()).hexdigest()[:16]
        bridge = "v41r26-bridge-" + hashlib.sha256(f"bridge|{index}|v41r26".encode()).hexdigest()[:16]
        target = LABELS[index % 4]; rotation = (index // 4) % 4
        candidates = list(LABELS[rotation:] + LABELS[:rotation])
        cases.append({"case_id": f"v41r26-acquisition-{index:03d}", "subject": subject,
                      "bridge": bridge, "target": target, "candidates": candidates,
                      "training_rows": [{"prompt": f"In sealed registry R26, what does {subject} point to? Return only the entry.", "answer": bridge},
                                        {"prompt": f"In sealed registry R26, what does {bridge} resolve to? Return only the value.", "answer": target}],
                      "composition_prompt": (f"In sealed registry R26, {subject} points to an intermediate entry. "
                                             "What terminal label does that entry resolve to? Return only the label.")})
    body = {"version": "mesh.astral_v41r26_acquisition_instrument.v1", "cases": cases,
            "source_text_present": False, "assessment_present": False}
    return {**body, "instrument_sha256": canonical_hash(body)}


def expected_protected() -> dict[str, Any]:
    rows = []
    for index in range(256):
        left, right = 101 + index, 23 + ((index * 17) % 71); target = left + right
        rows.append({"case_id": f"v41r26-protected-{index:03d}",
                     "prompt": f"Compute {left} + {right}. Return only the integer.",
                     "target": str(target),
                     "candidates": [str(target), str(target + 1), str(target - 1), str(target + 2)]})
    body = {"version": "mesh.astral_v41r26_protected_instrument.v1", "rows": rows,
            "source_text_present": False, "assessment_present": False}
    return {**body, "instrument_sha256": canonical_hash(body)}


def expected_contract() -> dict[str, Any]:
    acquisition = expected_acquisition(); protected = expected_protected(); panels = []
    for panel in range(16):
        a0, p0 = panel * 4, panel * 16
        panels.append({"panel_id": f"v41r26-panel-{panel}",
                       "acquisition_indices": list(range(a0, a0 + 4)),
                       "acquisition_case_ids": [row["case_id"] for row in acquisition["cases"][a0:a0 + 4]],
                       "protected_indices": list(range(p0, p0 + 16)),
                       "protected_case_ids": [row["case_id"] for row in protected["rows"][p0:p0 + 16]]})
    body = {"version": "mesh.astral_v41r26_multipanel_contract.v1",
            "state_slice": "V41R26MultiPanelReplayQualificationDesign",
            "acquisition_instrument_sha256": acquisition["instrument_sha256"],
            "protected_instrument_sha256": protected["instrument_sha256"],
            "panels": panels, "seeds": list(SEEDS), "run_count": 48,
            "method": {"acquisition_weight": 0.75, "protected_weight": 0.25,
                       "optimizer_steps": 256, "examples_per_panel_per_step": 4,
                       "lora": {"rank": 8, "alpha": 16, "targets": "qkvo_all24"},
                       "optimizer": "AdamW", "learning_rate": 2.0e-4, "gradient_clip": 1.0},
            "preflight": {"protected_accuracy_required": 1.0,
                          "minimum_incorrect_acquisition_cases_per_panel": 3,
                          "failure_aborts_before_training": True},
            "per_run_gate": {"acquisition_cases_passing": 4,
                             "protected_accuracy_minimum": 0.98, "reload_exact": True},
            "primary_estimand": "panel_all_seeds_qualification_probability",
            "qualification": {"wilson_95_lower_bound_strictly_above": 0.80,
                              "every_panel_all_seeds_pass": True, "governance_violations": 0},
            "historical_results_in_primary_estimator": False,
            "adaptive_stopping": False, "tune_opened": False, "assessment_opened": False}
    return {**body, "contract_sha256": canonical_hash(body)}


def wilson_lower(successes: int, total: int) -> float:
    if total <= 0 or not 0 <= successes <= total: raise ValueError("V41R26 Wilson census")
    p, z2 = successes / total, Z * Z
    return (p + z2 / (2 * total) - Z * math.sqrt(p * (1 - p) / total + z2 / (4 * total * total))) / (1 + z2 / total)


def validate(rgs_root: Path) -> dict[str, Any]:
    method = rgs_root / "mesh_brain/meshmodel/v41r26_multipanel_qualification.py"
    errors = []; packet = expected_contract()
    if not method.is_file(): errors.append("method_missing")
    else:
        try:
            code = ("import json; from mesh_brain.meshmodel.v41r11_novelty_instrument import build_instrument; "
                    "from mesh_brain.meshmodel.v41r26_multipanel_qualification import contract; "
                    "print(json.dumps(contract(), sort_keys=True))")
            completed = subprocess.run([sys.executable, "-c", code], cwd=rgs_root, check=True,
                                       capture_output=True, text=True)
            if json.loads(completed.stdout) != packet: errors.append("contract_mismatch")
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            errors.append("producer_import")
    if wilson_lower(16, 16) <= 0.80 or wilson_lower(15, 16) > 0.80: errors.append("statistical_gate")
    return {"version": "astral.v41r26_multipanel_local_validation.v1", "valid": not errors,
            "errors": errors, "contract_sha256": packet["contract_sha256"],
            "run_count": 48, "minimum_successful_panels": 16, "runtime_authorized": False,
            "claim_ceiling": "LocalMultiPanelReplayQualificationProtocolV41R26" if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--rgs-root", type=Path, required=True)
    args = parser.parse_args(); report = validate(args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
