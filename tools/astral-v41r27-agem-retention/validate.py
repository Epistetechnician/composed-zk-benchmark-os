from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence


SEEDS = (412003, 412007, 412019)
SENTINELS = (0, 7, 15)
LABELS = ("bravik", "solven", "nareth", "quorin")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=True).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def acquisition() -> dict[str, Any]:
    rows = []
    for index in range(64):
        subject = "v41r27-subject-" + hashlib.sha256(f"subject|{index}|v41r27".encode()).hexdigest()[:16]
        bridge = "v41r27-bridge-" + hashlib.sha256(f"bridge|{index}|v41r27".encode()).hexdigest()[:16]
        target = LABELS[index % 4]; rotation = (index // 4) % 4
        candidates = list(LABELS[rotation:] + LABELS[:rotation])
        rows.append({"case_id": f"v41r27-acquisition-{index:03d}", "subject": subject,
                     "bridge": bridge, "target": target, "candidates": candidates,
                     "training_rows": [
                         {"prompt": f"In sealed registry R27, what does {subject} point to? Return only the entry.", "answer": bridge},
                         {"prompt": f"In sealed registry R27, what does {bridge} resolve to? Return only the value.", "answer": target}],
                     "composition_prompt": (f"In sealed registry R27, {subject} points to an intermediate entry. "
                                            "What terminal label does that entry resolve to? Return only the label.")})
    body = {"version": "mesh.astral_v41r27_acquisition_instrument.v1", "cases": rows,
            "source_text_present": False, "assessment_present": False}
    return {**body, "instrument_sha256": canonical_hash(body)}


def protected() -> dict[str, Any]:
    rows = []
    for index in range(256):
        left = 401 + index; right = 37 + ((index * 19) % 83); target = left + right
        rows.append({"case_id": f"v41r27-protected-{index:03d}",
                     "prompt": f"Compute {left} + {right}. Return only the integer.",
                     "target": str(target),
                     "candidates": [str(target), str(target - 2), str(target + 1), str(target - 1)]})
    body = {"version": "mesh.astral_v41r27_protected_instrument.v1", "rows": rows,
            "source_text_present": False, "assessment_present": False}
    return {**body, "instrument_sha256": canonical_hash(body)}


def expected_contract() -> dict[str, Any]:
    a = acquisition(); p = protected(); panels = []
    for panel in range(16):
        panels.append({"panel_id": f"v41r27-panel-{panel}",
                       "acquisition_indices": list(range(panel * 4, panel * 4 + 4)),
                       "acquisition_case_ids": [row["case_id"] for row in a["cases"][panel * 4:panel * 4 + 4]],
                       "protected_indices": list(range(panel * 16, panel * 16 + 16)),
                       "protected_case_ids": [row["case_id"] for row in p["rows"][panel * 16:panel * 16 + 16]]})
    body = {"version": "mesh.astral_v41r27_agem_contract.v2",
            "state_slice": "V41R27ProspectiveRetentionStabilityMechanism",
            "acquisition_instrument_sha256": a["instrument_sha256"],
            "protected_instrument_sha256": p["instrument_sha256"],
            "panels": panels, "seeds": list(SEEDS), "run_count": 48,
            "mechanism": {"id": "averaged_gradient_episodic_memory_projection",
                          "reference_gradient": "matched_protected_replay_microbatch",
                          "projection_condition": "acquisition_dot_protected_strictly_below_zero",
                          "projected_update": "g_a-(dot(g_a,g_p)/dot(g_p,g_p))*g_p",
                          "combined_gradient": "0.75*projected_acquisition+0.25*protected",
                          "gradient_clip": 1.0,
                          "geometry_accumulator": "float64",
                          "projection_roundoff_bound": "64*dtype_epsilon*max(sqrt(projected_norm_sq*protected_norm_sq),1)"},
            "optimizer": {"id": "AdamW", "learning_rate": 2.0e-4, "steps": 256},
            "lora": {"rank": 8, "alpha": 16, "targets": "qkvo_all24"},
            "preflight": {"protected_accuracy_required": 1.0,
                          "minimum_incorrect_acquisition_cases_per_panel": 3},
            "per_run_gate": {"acquisition_cases_passing": 4,
                             "protected_accuracy_minimum": 0.98, "reload_exact": True},
            "stages": {"sentinel_panels": list(SENTINELS), "sentinel_run_count": 9,
                       "sentinel_requires_every_run_pass": True,
                       "remainder_authorized_only_after_sentinel": True},
            "qualification": {"every_panel_all_seeds_pass": True,
                              "wilson_95_lower_bound_strictly_above": 0.80,
                              "governance_violations": 0},
            "v41r26_data_or_seeds_reused": False, "adaptive_stopping": False,
            "tune_opened": False, "assessment_opened": False}
    return {**body, "contract_sha256": canonical_hash(body)}


def project(acquisition_gradient: Sequence[float], protected_gradient: Sequence[float]) -> list[float]:
    dot = sum(a * p for a, p in zip(acquisition_gradient, protected_gradient))
    if dot >= 0: return list(acquisition_gradient)
    norm = sum(p * p for p in protected_gradient)
    if norm <= 0: raise ValueError("zero protected gradient")
    return [a - dot / norm * p for a, p in zip(acquisition_gradient, protected_gradient)]


def validate(rgs_root: Path) -> dict[str, Any]:
    errors = []; expected = expected_contract()
    code = "import json; from mesh_brain.meshmodel.v41r27_agem_retention import contract; print(json.dumps(contract(),sort_keys=True))"
    try:
        completed = subprocess.run([sys.executable, "-c", code], cwd=rgs_root,
                                   check=True, capture_output=True, text=True)
        if json.loads(completed.stdout) != expected: errors.append("contract_mismatch")
    except (subprocess.CalledProcessError, json.JSONDecodeError): errors.append("producer_import")
    conflicting = project([1.0, -2.0], [0.0, 1.0])
    if conflicting != [1.0, 0.0] or sum(a * p for a, p in zip(conflicting, [0.0, 1.0])) < -1e-12:
        errors.append("projection_invariant")
    if set(SEEDS) & {411017, 411031, 411043}: errors.append("seed_reuse")
    return {"version": "astral.v41r27_agem_local_validation.v1", "valid": not errors,
            "errors": errors, "contract_sha256": expected["contract_sha256"],
            "sentinel_run_count": 9, "full_run_count": 48, "runtime_authorized": False,
            "claim_ceiling": "LocalProspectiveRetentionStabilityProtocolV41R27" if not errors else None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--rgs-root", type=Path, required=True)
    args = parser.parse_args(); report = validate(args.rgs_root.resolve())
    print(json.dumps(report, indent=2, sort_keys=True)); return 0 if report["valid"] else 1


if __name__ == "__main__": raise SystemExit(main())
