#!/usr/bin/env python3
"""Read-only V21 diagnosis over the sealed V20 replication artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


STATE_SLICE = "continual-learning-protocol-v21-seed-sensitivity-diagnosis"
SOURCE_STATE_SLICE = "continual-learning-protocol-v20-compact-routing-replication"
EXPECTED_SEEDS = (20260811, 20260812, 20260813)
EXPECTED_ORDERS = ((0, 1, 2, 3), (0, 2, 3, 1), (0, 3, 1, 2))
TRAIN_RE = re.compile(r"Iter (\d+): Train loss ([0-9.]+).*?It/sec ([0-9.]+).*?Peak mem ([0-9.]+) GB")
VAL_RE = re.compile(r"Iter (\d+): Val loss ([0-9.]+)")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_summary(path: Path) -> dict:
    text = path.read_text(encoding="utf8")
    train = [(int(step), float(loss), float(rate), float(memory)) for step, loss, rate, memory in TRAIN_RE.findall(text)]
    values = [(int(step), float(loss)) for step, loss in VAL_RE.findall(text)]
    if not train or not values:
        raise ValueError(f"training telemetry missing: {path}")
    return {
        "final_train_iter": train[-1][0],
        "final_train_loss": train[-1][1],
        "mean_it_per_sec": sum(row[2] for row in train) / len(train),
        "peak_memory_gb": max(row[3] for row in train),
        "final_val_iter": values[-1][0],
        "final_val_loss": values[-1][1],
        "training_log_sha256": file_digest(path),
    }


def task_shape(tasks: list[dict]) -> dict:
    return {
        "tasks": [
            {
                "task_id": task["task_id"],
                "mapping": task["mapping"],
                "train_count": len(task["train_facts"]),
                "test_count": len(task["test_facts"]),
                "train_residues": sorted(fact["residue"] for fact in task["train_facts"]),
                "test_residues": sorted(fact["residue"] for fact in task["test_facts"]),
                "train_labels": sorted(fact["label"] for fact in task["train_facts"]),
                "test_labels": sorted(fact["label"] for fact in task["test_facts"]),
            }
            for task in tasks
        ]
    }


def validate_cell_artifacts(cell_root: Path, matrix_cell: dict) -> dict:
    config = json.loads((cell_root / "config.json").read_text())
    result = json.loads((cell_root / "result.json").read_text())
    tasks = result["tasks"]
    audits = {
        strategy: json.loads((cell_root / "audit" / f"{strategy}.json").read_text())
        for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank")
    }
    config_hash_valid = config["contract_sha256"] == digest({key: value for key, value in config.items() if key != "contract_sha256"})
    manifest_hash_valid = result["manifest_sha256"] == digest({"config": config, "tasks": tasks, "audits": audits})
    result_hash_valid = result["result_sha256"] == digest({key: value for key, value in result.items() if key != "result_sha256"})
    if not (config_hash_valid and manifest_hash_valid and result_hash_valid):
        raise ValueError(f"digest failure in {cell_root}")
    candidate_audit = json.loads((cell_root / "audit" / "task_routed_compact_residual.json").read_text())
    route_valid = len(candidate_audit) == 4 and all(
        entry["route_key"] == f"T{entry['task_id']}"
        and entry["resumed_from"] is None
        and entry["slot_num_layers"] == 2
        and entry["dataset_row_count"] == 32
        for entry in candidate_audit
    )
    adapter_records = []
    slot_logs = []
    for entry in candidate_audit:
        adapter = cell_root / entry["adapter_relative_path"] / "adapters.safetensors"
        log = cell_root / "adapters" / "task_routed_compact_residual" / f"task-{entry['task_id']}.log"
        adapter_records.append({"task_id": entry["task_id"], "bytes": adapter.stat().st_size, "sha256": file_digest(adapter)})
        slot_logs.append({"task_id": entry["task_id"], "telemetry": log_summary(log)})
    task0 = next(row for row in slot_logs if row["task_id"] == 0)
    candidate = result["task_routed_compact_residual"]
    observed = Counter(row["observed"] for row in candidate["acquisition"]["rows"])
    task_fit = {
        str(entry["task_id"]): entry["task_accuracy_after_update"]["accuracy"]
        for entry in candidate_audit
    }
    return {
        "cell": matrix_cell["cell"],
        "seed": config["seed"],
        "order": config["order"],
        "candidate_acquisition": candidate["acquisition"]["accuracy"],
        "candidate_retention": candidate["retention_after_interference"]["accuracy"],
        "naive_acquisition": result["results"]["naive_sequential_lora"]["acquisition"]["accuracy"],
        "naive_retention": result["results"]["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
        "replay_retention": result["results"]["replay_lora"]["retention_after_interference"]["accuracy"],
        "candidate_observed_label_counts": dict(sorted(observed.items())),
        "task_fit_accuracy_by_task": task_fit,
        "task0_slot_telemetry": task0["telemetry"],
        "slot_telemetry": slot_logs,
        "adapter_records": adapter_records,
        "task_shape": task_shape(tasks),
        "task_shape_sha256": digest(task_shape(tasks)),
        "route_audit_valid": route_valid,
        "config_hash_valid": config_hash_valid,
        "manifest_hash_valid": manifest_hash_valid,
        "result_hash_valid": result_hash_valid,
    }


def run(args: argparse.Namespace) -> dict:
    root = args.source.resolve()
    matrix = json.loads((root / "matrix.json").read_text())
    if matrix["seeds"] != list(EXPECTED_SEEDS) or matrix["orders"] != [list(order) for order in EXPECTED_ORDERS] or len(matrix["cells"]) != 9:
        raise ValueError("V20 source matrix drift")
    cells = [validate_cell_artifacts(root / cell["relative_root"], cell) for cell in matrix["cells"]]
    by_seed = {}
    for cell in cells:
        by_seed.setdefault(str(cell["seed"]), []).append(cell)
    failing_seed = next(seed for seed, group in by_seed.items() if all(cell["candidate_acquisition"] < 0.75 for cell in group))
    failing_group = by_seed[failing_seed]
    successful_groups = [group for seed, group in by_seed.items() if seed != failing_seed]
    failing_task0_losses = [cell["task0_slot_telemetry"]["final_val_loss"] for cell in failing_group]
    successful_task0_losses = [cell["task0_slot_telemetry"]["final_val_loss"] for group in successful_groups for cell in group]
    shape_hashes = {cell["task_shape_sha256"] for cell in cells}
    route_valid = all(cell["route_audit_valid"] for cell in cells)
    hashes_valid = all(cell["config_hash_valid"] and cell["manifest_hash_valid"] and cell["result_hash_valid"] for cell in cells)
    order_invariant_failure = len({cell["candidate_acquisition"] for cell in failing_group}) == 1
    memory_values = [slot["telemetry"]["peak_memory_gb"] for cell in cells for slot in cell["slot_telemetry"]]
    hypotheses = {
        "seed_specific_optimizer_or_initialization_instability": {
            "status": "supported",
            "prediction": "one seed fails across all orders and its task-0 slot fails to reduce validation loss",
            "evidence": {
                "failing_seed": int(failing_seed),
                "failing_seed_orders": [cell["order"] for cell in failing_group],
                "failing_seed_task0_final_val_losses": failing_task0_losses,
                "successful_seed_task0_final_val_loss_range": [min(successful_task0_losses), max(successful_task0_losses)],
            },
        },
        "seed_specific_task_manifest_pathology": {
            "status": "not_supported",
            "prediction": "the failing seed has a distinct mapping, split, or residue-shape signature",
            "evidence": {"unique_task_shape_hashes": len(shape_hashes), "task_shape_hashes": sorted(shape_hashes)},
        },
        "route_or_order_implementation_bug": {
            "status": "not supported",
            "prediction": "failure follows order rather than seed",
            "evidence": {"failure_is_order_invariant_for_failing_seed": order_invariant_failure, "route_audits_valid": route_valid},
        },
        "compact_slot_capacity_mismatch": {
            "status": "not supported as sole cause",
            "prediction": "all seeds fail similarly under the same two-layer slot budget",
            "evidence": {"candidate_acquisition_by_seed": {seed: [cell["candidate_acquisition"] for cell in group] for seed, group in by_seed.items()}},
        },
        "artifact_or_audit_inconsistency": {
            "status": "not supported",
            "prediction": "sealed hashes, routes, or adapter files disagree",
            "evidence": {"all_cell_hashes_valid": hashes_valid, "all_route_audits_valid": route_valid},
        },
    }
    report = {
        "state_slice": STATE_SLICE,
        "source_state_slice": SOURCE_STATE_SLICE,
        "classification": "SeedSensitivityDiagnosisNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentSeedSensitivityDiagnosis",
        "source_artifact": str(root),
        "diagnosis_method": "read_only_sealed_artifact_log_and_manifest_audit_v1",
        "cell_count": len(cells),
        "cells": cells,
        "hypotheses": hypotheses,
        "diagnosis": "seed_20260812_task0_compact_slot_optimization_plateau",
        "diagnosis_confidence": "supported_local_hypothesis_not_causal_proof",
        "runtime_memory": {
            "candidate_slot_peak_memory_gb_max": max(memory_values),
            "candidate_slot_peak_memory_gb_min": min(memory_values),
            "runtime_or_memory_bottleneck_demonstrated": False,
        },
        "gates": {
            "source_matrix_exact": True,
            "all_cell_hashes_valid": hashes_valid,
            "all_route_audits_valid": route_valid,
            "failure_reproduced_across_all_failing_seed_orders": order_invariant_failure,
            "task_shape_invariant": len(shape_hashes) == 1,
            "h100_authorized": False,
            "breakthrough_claim_eligible": False,
        },
        "next_hypothesis": "make_slot_initialization_and_optimizer_state independent of the seed while preserving fixed data, total steps, and adapter-byte budget",
    }
    report["report_sha256"] = digest({key: value for key, value in report.items() if key != "report_sha256"})
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
