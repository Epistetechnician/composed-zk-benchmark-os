"""Independent validator for the additive V8 synthetic qualification.

State slice: ``oaklab-experience-learning-h100-replication-v8``.
The validator derives family predicates from raw qualification rows and
counter evidence.  It never authorizes real execution, provider spend, or
assessment materialization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .oaklab_h100_v8_synthetic_qualification import (
    COMPILED,
    CONTROLLER_STATE_BYTES,
    FAMILIES,
    FIT_ROWS,
    IMPLEMENTATION,
    RESULT,
    ROOT,
    ROWS,
    SCHEMA,
    SEEDS,
    SOURCE,
    STATE_SLICE,
    STREAMS,
    canonical,
    digest,
    generate,
    _stable_digest,
)
from .compile_oaklab_h100_v8_protocol import sha256_file
from .validate_oaklab_h100_v8_protocol import verify_ed25519


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _review_is_valid() -> dict[str, Any]:
    path = ROOT / "docs/research/experience-learning/63-oaklab-h100-replication-v8-independent-review.json"
    review = json.loads(path.read_bytes())
    body = {key: value for key, value in review.items() if key not in {"signature_hex", "receipt_sha256"}}
    if review.get("review_decision") != "ACCEPT" or review.get("effects_run") is not False:
        raise ValueError("independent V8 review is not an ACCEPT with effects_run=false")
    if review.get("packet_sha256") != "d2b1d91ebe8a50ddf1c40e5ce698623913837ebd23f7c7a641a99eb737ae23a4":
        raise ValueError("review packet binding changed")
    if review.get("receipt_sha256") != digest(body):
        raise ValueError("independent review receipt self-digest mismatch")
    if not verify_ed25519(bytes.fromhex(review["public_key_hex"]), bytes.fromhex(review["signature_hex"]), canonical(body)):
        raise ValueError("independent review signature mismatch")
    return review


def _validate_arm(stream: str, arm: dict[str, Any], candidate: bool, seed: int) -> None:
    required = {"seed", "mean_loss", "adaptation_lag", "updates", "active_operations", "storage_bytes",
                "learned_events", "latency_ns", "apply_rows", "gated_rows", "counter", "final_state_digest", "row_digest"}
    if set(arm) != required or arm["seed"] != seed:
        raise ValueError(f"arm schema mismatch for {stream}/{seed}")
    if not all(_finite(arm[key]) for key in ("mean_loss", "adaptation_lag", "updates", "active_operations", "storage_bytes", "learned_events", "latency_ns", "apply_rows", "gated_rows")):
        raise ValueError(f"nonfinite arm metric for {stream}/{seed}")
    counter = arm["counter"]
    if set(counter) != {"rows", "updates", "active_operations", "storage_bytes", "learned_events", "latency_ns"}:
        raise ValueError(f"counter schema mismatch for {stream}/{seed}")
    if counter["rows"] != ROWS or counter["updates"] != arm["updates"] or counter["active_operations"] != arm["active_operations"] or counter["storage_bytes"] != arm["storage_bytes"] or counter["learned_events"] != arm["learned_events"] or counter["latency_ns"] != arm["latency_ns"]:
        raise ValueError(f"arm metrics are not counter-derived for {stream}/{seed}")
    if arm["apply_rows"] != arm["updates"] or arm["gated_rows"] != (ROWS - arm["updates"] if candidate else 0):
        raise ValueError(f"action/update accounting mismatch for {stream}/{seed}")
    dimension = len(generate(stream, seed)[0].features)
    expected_ops = ROWS * ((2 * 4 - 1) + (2 * dimension + 1) + 3) + arm["updates"] * 4 * (dimension + 1)
    expected_storage = (8 * (dimension + 1) + CONTROLLER_STATE_BYTES) if candidate else 8 * (dimension + 1)
    if arm["active_operations"] != expected_ops or arm["storage_bytes"] != expected_storage:
        raise ValueError(f"operation/storage counter mismatch for {stream}/{seed}")
    expected_events = sum(len(item.events) for item in generate(stream, seed))
    if arm["learned_events"] != expected_events:
        raise ValueError(f"event denominator mismatch for {stream}/{seed}")
    if not isinstance(arm["row_digest"], str) or len(arm["row_digest"]) != 64:
        raise ValueError(f"row digest missing for {stream}/{seed}")


def _recompute_gate(result: dict[str, Any]) -> dict[str, bool]:
    families = result["families"]
    qualifying = []
    for family in FAMILIES:
        value = families[family]
        candidate = value["candidate_estimate"]["mean"]
        reference = value["reference_estimate"]["mean"]
        adjusted = result["holm_primary"]["adjusted_p_values"].get(family, 1.0)
        if family != "null" and adjusted <= 0.05 and candidate <= reference:
            qualifying.append(family)
    shift_families = ("drift", "delayed_reward", "event", "long_horizon")
    adaptation_no_worse = all(
        families[family]["adaptation"]["candidate"]["mean"] <= families[family]["adaptation"]["reference"]["mean"]
        for family in shift_families
    )
    adaptation_strict = any(
        families[family]["adaptation"]["candidate"]["mean"] < families[family]["adaptation"]["reference"]["mean"]
        for family in shift_families
    )
    resource_noninferior = all(
        families[family]["resources"][metric]["candidate"]["mean"] <= 1.05 * families[family]["resources"][metric]["reference"]["mean"]
        for family in FAMILIES for metric in ("active_operations", "updates", "storage_bytes")
    )
    null_no_advantage = families["null"]["candidate_estimate"]["mean"] >= families["null"]["reference_estimate"]["mean"]
    return {
        "at_least_two_holm_primary_families": len(qualifying) >= 2,
        "adaptation_no_worse_all_shift_families": adaptation_no_worse,
        "adaptation_strictly_better_one_shift_family": adaptation_strict,
        "resources_noninferior_within_5_percent": resource_noninferior,
        "pure_noise_null_no_candidate_advantage": null_no_advantage,
    }


def validate(path: Path = RESULT) -> dict[str, Any]:
    result = json.loads(path.read_bytes())
    if set(result) != {"schema", "state_slice", "source_sha256", "compiled_protocol_sha256", "review_receipt_sha256", "implementation_sha256", "synthetic_only", "assessment_materialization_state", "real_execution", "hardware_energy", "seeds", "rows_per_trajectory", "fit_rows", "hyperparameters", "families", "holm_primary", "qualification_rows", "gate", "status", "claim_ceiling", "result_sha256"}:
        raise ValueError("synthetic result root is not closed")
    if result["schema"] != SCHEMA or result["state_slice"] != STATE_SLICE:
        raise ValueError("synthetic result identity mismatch")
    expected = _stable_digest({key: value for key, value in result.items() if key != "result_sha256"})
    if result["result_sha256"] != expected:
        raise ValueError("synthetic result digest mismatch")
    if result["source_sha256"] != sha256_file(ROOT / SOURCE) or result["compiled_protocol_sha256"] != sha256_file(ROOT / COMPILED):
        raise ValueError("synthetic result is stale against frozen protocol bytes")
    if result["implementation_sha256"] != sha256_file(ROOT / IMPLEMENTATION):
        raise ValueError("synthetic result is stale against implementation bytes")
    review = _review_is_valid()
    if result["review_receipt_sha256"] != review["receipt_sha256"]:
        raise ValueError("synthetic result review binding mismatch")
    if result["synthetic_only"] is not True or result["assessment_materialization_state"] != "absent" or result["hardware_energy"] != "not_run":
        raise ValueError("synthetic qualification crossed a forbidden boundary")
    if result["seeds"] != list(SEEDS) or result["rows_per_trajectory"] != ROWS or result["fit_rows"] != FIT_ROWS:
        raise ValueError("synthetic cohort or split changed")
    if set(result["families"]) != set(FAMILIES) or len(result["qualification_rows"]) != len(FAMILIES) * len(SEEDS):
        raise ValueError("synthetic family/seed matrix incomplete")
    rows_by_family = {family: [] for family in FAMILIES}
    for row in result["qualification_rows"]:
        if set(row) != {"schema", "state_slice", "family", "stream", "seed", "reference", "candidate", "row_sha256"}:
            raise ValueError("qualification row schema is not closed")
        if row["schema"] != "oaklab.h100.v8.synthetic-family-row.v1" or row["state_slice"] != STATE_SLICE or row["family"] not in FAMILIES or row["stream"] not in STREAMS or row["seed"] not in SEEDS:
            raise ValueError("qualification row identity mismatch")
        if _stable_digest({key: value for key, value in row.items() if key != "row_sha256"}) != row["row_sha256"]:
            raise ValueError("qualification row digest mismatch")
        _validate_arm(row["stream"], row["reference"], False, row["seed"])
        _validate_arm(row["stream"], row["candidate"], True, row["seed"])
        rows_by_family[row["family"]].append(row)
    for family in FAMILIES:
        if len(rows_by_family[family]) != len(SEEDS):
            raise ValueError(f"seed count mismatch for {family}")
    derived_gate = _recompute_gate(result)
    if result["gate"] != derived_gate:
        raise ValueError("gate contains caller-supplied or stale booleans")
    expected_status = "candidate" if all(derived_gate.values()) else "no_candidate"
    if result["status"] != expected_status:
        raise ValueError("status is not derived from gate")
    return {"status": "valid", "state_slice": STATE_SLICE, "qualification_status": result["status"],
            "result_sha256": result["result_sha256"], "assessment_materialization_state": "absent",
            "hardware_energy": "not_run"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path, nargs="?", default=RESULT)
    args = parser.parse_args()
    print(json.dumps(validate(args.receipt), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
