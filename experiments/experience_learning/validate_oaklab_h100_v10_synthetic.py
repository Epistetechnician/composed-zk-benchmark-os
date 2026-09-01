"""Independent V10 synthetic-result validator.

State slice: oaklab-experience-learning-h100-replication-v10.
No real, provider, H100, energy, or assessment execution is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "oaklab-experience-learning-h100-replication-v10"
RESULT = ROOT / "experiments/experience_learning/oaklab_h100_v10_synthetic_qualification.json"
SOURCE = ROOT / "experiments/experience_learning/oaklab_h100_v10_protocol.json"
COMPILED = ROOT / "experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json"
IMPLEMENTATION = ROOT / "experiments/experience_learning/oaklab_h100_v10_synthetic_qualification.py"
REVIEW = ROOT / "docs/research/experience-learning/72-oaklab-h100-replication-v10-independent-review.json"
FAMILIES = ("predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null")
STREAMS = ("sparse_signal_v10", "drifting_relevance_v10", "delayed_reward_v10", "event_sensor_v10", "long_horizon_v10", "pure_noise_v10")
SEEDS = tuple(range(12000, 12048))


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> dict[str, Any]:
    result = json.loads(RESULT.read_bytes())
    expected = {"schema", "state_slice", "source_sha256", "compiled_protocol_sha256", "review_receipt_sha256", "implementation_sha256", "synthetic_only", "assessment_materialization_state", "real_execution", "hardware_energy", "fit_seeds", "tune_seeds", "assessment_seeds", "rows_per_trajectory", "segment_rows", "locked_hyperparameters", "families", "qualification_rows", "gate", "status", "claim_ceiling", "result_sha256"}
    require(set(result) == expected, "synthetic result root is not closed")
    require(result["schema"] == "oaklab.h100.v10.synthetic-qualification.v1" and result["state_slice"] == STATE_SLICE, "synthetic result identity mismatch")
    require(result["result_sha256"] == digest({k: v for k, v in result.items() if k != "result_sha256"}), "synthetic result digest mismatch")
    require(result["source_sha256"] == file_digest(SOURCE) and result["compiled_protocol_sha256"] == file_digest(COMPILED) and result["implementation_sha256"] == file_digest(IMPLEMENTATION), "synthetic result stale against code")
    review = json.loads(REVIEW.read_bytes()); require(review["review_decision"] == "ACCEPT" and review["effects_run"] is False and result["review_receipt_sha256"] == review["receipt_sha256"], "review binding invalid")
    require(result["synthetic_only"] is True and result["assessment_materialization_state"] == "absent" and result["real_execution"] == "prohibited" and result["hardware_energy"] == "not_run", "forbidden boundary crossed")
    require(result["fit_seeds"] == list(SEEDS) and result["tune_seeds"] == [] and result["assessment_seeds"] == [] and result["rows_per_trajectory"] == 256 and result["segment_rows"] == 32, "cohort/split changed")
    require(set(result["families"]) == set(FAMILIES) and len(result["qualification_rows"]) == 288, "family matrix incomplete")
    seen: set[tuple[str, int]] = set()
    for row in result["qualification_rows"]:
        require(set(row) == {"schema", "state_slice", "family", "stream", "seed", "reference", "treatment", "row_sha256"}, "qualification row schema changed")
        require(row["schema"] == "oaklab.h100.v10.synthetic-family-row.v1" and row["state_slice"] == STATE_SLICE and row["family"] in FAMILIES and row["stream"] in STREAMS and row["seed"] in SEEDS, "qualification row identity mismatch")
        require(row["row_sha256"] == digest({k: v for k, v in row.items() if k != "row_sha256"}), "qualification row digest mismatch")
        for arm in (row["reference"], row["treatment"]):
            require(set(arm) == {"mean_loss", "updates", "active_operations", "storage_bytes", "learned_events", "segments"}, "arm schema changed")
            require(len(arm["segments"]) == 8 and all(math.isfinite(float(arm[k])) for k in ("mean_loss", "updates", "active_operations", "storage_bytes", "learned_events")), "arm metrics invalid")
        seen.add((row["stream"], row["seed"]))
    require(len(seen) == 288, "duplicate or missing seed/stream rows")
    families = result["families"]
    quality = [f for f in FAMILIES if f != "null" and families[f]["paired_loss_delta"] < 0 and families[f]["raw_p"] <= 0.05]
    derived = {"at_least_two_quality_families": len(quality) >= 2, "adaptation_not_worse": all(v["adaptation_lag_treatment"] <= v["adaptation_lag_reference"] for v in families.values()), "resource_noninferior": all(v["treatment_active_operations"] <= 1.05 * v["reference_active_operations"] and v["treatment_storage_bytes"] <= 1.05 * v["reference_storage_bytes"] for v in families.values()), "null_no_advantage": families["null"]["paired_loss_delta"] >= 0, "raw_rows_complete": len(result["qualification_rows"]) == 288}
    require(result["gate"] == derived, "gate is not derived from raw family records")
    require(result["status"] == ("candidate" if all(derived.values()) else "no_candidate"), "status is not derived from gate")
    return {"valid": True, "state_slice": STATE_SLICE, "qualification_status": result["status"], "result_sha256": result["result_sha256"], "assessment_materialization_state": "absent", "real_execution": "prohibited", "hardware_energy": "not_run"}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("receipt", type=Path, nargs="?", default=RESULT); parser.parse_args(); print(json.dumps(validate(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
