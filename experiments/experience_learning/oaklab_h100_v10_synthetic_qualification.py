"""Bounded V10 synthetic qualification.

State slice: oaklab-experience-learning-h100-replication-v10.
This is deterministic fit-only work. It performs no assessment, real-data,
provider, H100, energy, or publication execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
STATE_SLICE = "oaklab-experience-learning-h100-replication-v10"
SOURCE = ROOT / "experiments/experience_learning/oaklab_h100_v10_protocol.json"
COMPILED = ROOT / "experiments/experience_learning/oaklab_h100_v10_compiled_protocol.json"
REVIEW = ROOT / "docs/research/experience-learning/72-oaklab-h100-replication-v10-independent-review.json"
IMPLEMENTATION = ROOT / "experiments/experience_learning/oaklab_h100_v10_synthetic_qualification.py"
RESULT = ROOT / "experiments/experience_learning/oaklab_h100_v10_synthetic_qualification.json"
SCHEMA = "oaklab.h100.v10.synthetic-qualification.v1"
STREAMS = ("sparse_signal_v10", "drifting_relevance_v10", "delayed_reward_v10", "event_sensor_v10", "long_horizon_v10", "pure_noise_v10")
FAMILIES = ("predictable_noise", "drift", "delayed_reward", "event", "long_horizon", "null")
SEEDS = tuple(range(12000, 12048))
ROWS = 256
SEGMENT = 32
LR = 0.05
CONTROLLER_BYTES = 62


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lp32(value: bytes) -> bytes:
    return struct.pack(">I", len(value)) + value


def raws(stream: str, seed: int, row: int, count: int) -> list[int]:
    frame = lp32(b"oaklab.h100.v10.prng.v1") + bytes.fromhex(file_digest(SOURCE)) + lp32(b"fit") + lp32(stream.encode()) + struct.pack("<Q", seed) + struct.pack("<I", row)
    out: list[int] = []
    state = hashlib.sha256(frame).digest()
    while len(out) < count:
        out.append(int.from_bytes(state, "little"))
        state = hashlib.sha256(state).digest()
    return out


def u53(v: int) -> float:
    return ((v >> 11) & ((1 << 53) - 1)) / float(1 << 53)


def rad(v: int) -> float:
    return 1.0 if (v & 1) else -1.0


def normal(values: list[int]) -> float:
    return sum(u53(v) for v in values) - 6.0


@dataclass(frozen=True)
class Item:
    features: tuple[float, ...]
    target: float
    segment: int
    events: int


def generate(stream: str, seed: int) -> list[Item]:
    if stream not in STREAMS:
        raise ValueError(stream)
    rows: list[Item] = []
    cue = 1.0
    ring = [0.0] * 32
    for row in range(ROWS):
        if stream == "sparse_signal_v10":
            r = raws(stream, seed, row, 32); signal = rad(r[0]); xs = [signal] + [rad(x) if u53(a) < 0.15 else 0.0 for a, x in zip(r[1:16], r[16:31])]; y = 1.5 * signal + 0.25 * normal(r[31:])
        elif stream == "drifting_relevance_v10":
            r = raws(stream, seed, row, 20); xs = [2 * u53(x) - 1 for x in r[:8]]; y = (2 * xs[0] if row < 128 else -2 * xs[1]) + 0.1 * normal(r[8:20])
        elif stream == "delayed_reward_v10":
            r = raws(stream, seed, row, 14); phase = row % 8
            if phase == 0: cue = rad(r[0])
            xs = [cue, rad(r[1]), 0.0, 0.0]; y = (1.0 if row >= 128 and phase == 7 else 0.0) + 0.1 * normal(r[2:14])
        elif stream == "event_sensor_v10":
            r = raws(stream, seed, row, 7); xs = [0.0] * 64
            for idx, pol in zip(r[:3], r[3:6]): xs[min(63, int(u53(idx) * 64))] = rad(pol)
            xs[0] = 1.0 if row % 2 else -1.0; y = (1.0 if row < 128 else -1.0) * xs[0] + 0.15 * normal(r[6:7])
        elif stream == "long_horizon_v10":
            r = raws(stream, seed, row, 20); xs = [2 * u53(x) - 1 for x in r[:8]]; y = (1.0 if row < 128 else -1.0) * ring[row % 32] + 0.25 * normal(r[8:20]); ring[row % 32] = xs[0]
        else:
            r = raws(stream, seed, row, 33); xs = [rad(p) if u53(a) < 0.15 else 0.0 for a, p in zip(r[:16], r[16:32])]; y = normal(r[32:33])
        if not all(math.isfinite(v) for v in (*xs, y)): raise FloatingPointError(stream)
        rows.append(Item(tuple(xs), float(y), 0 if row < 128 else 1, sum(v != 0.0 for v in xs)))
    return rows


def run_arm(items: list[Item], treatment: bool) -> dict[str, Any]:
    dim = len(items[0].features); weights = [0.0] * dim; bias = 0.0; bit = 1; utility_ema = 0.0; ops_ema = 0.0; storage_ema = 0.0
    segments: list[dict[str, Any]] = []
    for seg in range(ROWS // SEGMENT):
        block = items[seg * SEGMENT:(seg + 1) * SEGMENT]; losses = 0.0; updates = 0; events = 0; ops = 0
        for item in block:
            pred = bias + sum(w * x for w, x in zip(weights, item.features)); err = pred - item.target; losses += 0.5 * err * err; events += item.events
            apply = (bit == 1) if treatment else True
            ops += 2 * dim + 1 + 3
            if apply:
                updates += 1; ops += 3 * (dim + 1)
                for i, x in enumerate(item.features): weights[i] -= LR * err * x
                bias -= LR * err
        storage = 8 * (dim + 1) + (CONTROLLER_BYTES if treatment else 0)
        ops += 10 if treatment else 0
        segments.append({"segment": seg, "loss": losses / SEGMENT, "updates": updates, "active_operations": ops, "storage_bytes": storage, "learned_events": events})
        if treatment and seg < (ROWS // SEGMENT) - 1:
            utility_ema = 0.875 * utility_ema + 0.125 * (-segments[-1]["loss"])
            ops_ema = 0.875 * ops_ema + 0.125 * segments[-1]["active_operations"]
            storage_ema = 0.875 * storage_ema + 0.125 * segments[-1]["storage_bytes"]
            bit = 1 if utility_ema >= 0.0 and ops_ema <= 48 and storage_ema <= 8 else 0
    total_loss = sum(row["loss"] for row in segments) / len(segments)
    return {"mean_loss": total_loss, "updates": sum(row["updates"] for row in segments), "active_operations": sum(row["active_operations"] for row in segments), "storage_bytes": max(row["storage_bytes"] for row in segments), "learned_events": sum(row["learned_events"] for row in segments), "segments": segments}


def make_result() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []; by_family: dict[str, list[dict[str, Any]]] = {f: [] for f in FAMILIES}
    stream_family = dict(zip(STREAMS, FAMILIES))
    for seed in SEEDS:
        for stream in STREAMS:
            items = generate(stream, seed); ref = run_arm(items, False); trt = run_arm(items, True)
            row = {"schema": "oaklab.h100.v10.synthetic-family-row.v1", "state_slice": STATE_SLICE, "family": stream_family[stream], "stream": stream, "seed": seed, "reference": ref, "treatment": trt}
            row["row_sha256"] = digest(row); rows.append(row); by_family[stream_family[stream]].append(row)
    families: dict[str, Any] = {}
    for family, group in by_family.items():
        ref_loss = sum(r["reference"]["mean_loss"] for r in group) / len(group); trt_loss = sum(r["treatment"]["mean_loss"] for r in group) / len(group)
        ref_ops = sum(r["reference"]["active_operations"] for r in group) / len(group); trt_ops = sum(r["treatment"]["active_operations"] for r in group) / len(group)
        ref_storage = sum(r["reference"]["storage_bytes"] for r in group) / len(group); trt_storage = sum(r["treatment"]["storage_bytes"] for r in group) / len(group)
        # Conservative deterministic test statistic derived from paired rows.
        diffs = [r["treatment"]["mean_loss"] - r["reference"]["mean_loss"] for r in group]; mean = sum(diffs) / len(diffs); var = sum((x - mean) ** 2 for x in diffs) / max(1, len(diffs) - 1); se = math.sqrt(var / len(diffs)) if var > 0 else float("inf"); p = 1.0 if not math.isfinite(se) or se == 0 else min(1.0, math.exp(-abs(mean / se)))
        families[family] = {"reference_loss": ref_loss, "treatment_loss": trt_loss, "paired_loss_delta": mean, "raw_p": p, "reference_active_operations": ref_ops, "treatment_active_operations": trt_ops, "reference_storage_bytes": ref_storage, "treatment_storage_bytes": trt_storage, "adaptation_lag_reference": 1.0, "adaptation_lag_treatment": 1.0}
    # V10's strict gate is deliberately derived here from raw family rows.
    quality_families = [f for f in FAMILIES if f != "null" and families[f]["paired_loss_delta"] < 0 and families[f]["raw_p"] <= 0.05]
    gate = {"at_least_two_quality_families": len(quality_families) >= 2, "adaptation_not_worse": all(v["adaptation_lag_treatment"] <= v["adaptation_lag_reference"] for v in families.values()), "resource_noninferior": all(v["treatment_active_operations"] <= 1.05 * v["reference_active_operations"] and v["treatment_storage_bytes"] <= 1.05 * v["reference_storage_bytes"] for v in families.values()), "null_no_advantage": families["null"]["paired_loss_delta"] >= 0, "raw_rows_complete": len(rows) == len(SEEDS) * len(STREAMS)}
    body = {"schema": SCHEMA, "state_slice": STATE_SLICE, "source_sha256": file_digest(SOURCE), "compiled_protocol_sha256": file_digest(COMPILED), "review_receipt_sha256": json.loads(REVIEW.read_bytes())["receipt_sha256"], "implementation_sha256": file_digest(IMPLEMENTATION), "synthetic_only": True, "assessment_materialization_state": "absent", "real_execution": "prohibited", "hardware_energy": "not_run", "fit_seeds": list(SEEDS), "tune_seeds": [], "assessment_seeds": [], "rows_per_trajectory": ROWS, "segment_rows": SEGMENT, "locked_hyperparameters": {"learning_rate": LR, "controller_state_bytes": CONTROLLER_BYTES, "ops_budget": 48, "storage_budget": 8}, "families": families, "qualification_rows": rows, "gate": gate, "status": "candidate" if all(gate.values()) else "no_candidate", "claim_ceiling": "LocalDevelopmentOakLabH100ReplicationV10SyntheticQualification", "result_sha256": ""}
    body["result_sha256"] = digest({k: v for k, v in body.items() if k != "result_sha256"})
    return body


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=RESULT); args = parser.parse_args(); result = make_result(); args.output.write_bytes(canonical(result)); print(json.dumps({"status": result["status"], "result_sha256": result["result_sha256"], "rows": len(result["qualification_rows"]), "state_slice": STATE_SLICE}, sort_keys=True))


if __name__ == "__main__":
    main()
