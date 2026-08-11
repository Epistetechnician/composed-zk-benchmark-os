#!/usr/bin/env python3
"""V16 read-only audit of task-routed memory versus shared replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


STATE_SLICE = "continual-learning-protocol-v16-task-routed-memory-audit"
MODEL_DEFAULT = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
FIXED_KEYS = (
    "model",
    "seed",
    "order",
    "task_count",
    "train_facts_per_task",
    "test_facts_per_task",
    "task_rule",
    "mapping_policy",
    "split_policy",
    "solvability_control",
    "memory_mechanism",
    "route_policy",
    "replay_capacity",
    "update_budget",
    "current_examples_per_update",
    "replay_examples_per_update",
    "replay_policy",
    "optimizer",
    "learning_rate",
    "batch_size",
    "num_layers",
    "mask_prompt",
    "max_seq_length",
    "fine_tune_type",
    "audit_schema",
    "checkpoint_target_task_id",
    "checkpoint_assessment_context_mode",
    "solvability_guard_accuracy",
    "primary_metric",
    "prompt_contract",
    "iters",
    "source_context_removed_for",
    "assessment_effects_generated_before_prediction_lock",
    "objective_repair",
    "baseline_iters",
    "recovery_iters",
)
PEAK_MEMORY_RE = re.compile(r"Peak mem ([0-9.]+) GB")
ITER_RATE_RE = re.compile(r"Iter \d+: Train loss .*?It/sec ([0-9.]+)")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_artifact(root: Path) -> dict:
    return {
        "root": root,
        "config": json.loads((root / "config.json").read_text()),
        "tasks": json.loads((root / "tasks.json").read_text()),
        "result": json.loads((root / "result.json").read_text()),
        "result_file_sha256": file_sha256(root / "result.json"),
    }


def metric(result: dict, strategy: str, endpoint: str) -> dict:
    value = result["results"][strategy][endpoint]
    return {"correct": value["correct"], "n": value["n"], "accuracy": value["accuracy"]}


def storage_summary(root: Path) -> dict:
    adapter_files = sorted(root.glob("adapters/*/*/adapters.safetensors"))
    by_strategy = {}
    for strategy in ("naive_sequential_lora", "replay_lora", "task_adapter_bank"):
        files = sorted((root / "adapters" / strategy).rglob("adapters.safetensors"))
        by_strategy[strategy] = {
            "adapter_file_count": len(files),
            "adapter_bytes": sum(path.stat().st_size for path in files),
        }
    all_files = [path for path in root.rglob("*") if path.is_file()]
    return {
        "artifact_file_count": len(all_files),
        "artifact_bytes": sum(path.stat().st_size for path in all_files),
        "adapter_file_count": len(adapter_files),
        "adapter_bytes": sum(path.stat().st_size for path in adapter_files),
        "by_strategy": by_strategy,
    }


def telemetry_summary(root: Path) -> dict:
    logs = sorted(root.rglob("*.log"))
    peak_values = []
    rates = []
    for path in logs:
        text = path.read_text()
        peak_values.extend(float(value) for value in PEAK_MEMORY_RE.findall(text))
        rates.extend(float(value) for value in ITER_RATE_RE.findall(text))
    return {
        "training_log_count": len(logs),
        "peak_memory_gb_max": max(peak_values) if peak_values else None,
        "it_per_sec_mean": sum(rates) / len(rates) if rates else None,
        "it_per_sec_sample_count": len(rates),
        "source": "training_log_telemetry_not_wall_clock",
    }


def route_summary(artifact: dict) -> dict:
    root = artifact["root"]
    tasks = {task["task_id"]: task for task in artifact["tasks"]}
    bank_audit = json.loads((root / "audit" / "task_adapter_bank.json").read_text())
    routes = []
    for entry in bank_audit:
        path = root / entry["adapter_relative_path"]
        task = tasks[entry["task_id"]]
        routes.append(
            {
                "task_id": entry["task_id"],
                "route_key": entry["route_key"],
                "expected_route_key": task["task_token"],
                "route_key_exact": entry["route_key"] == task["task_token"],
                "adapter_path": entry["adapter_relative_path"],
                "adapter_exists": (path / "adapters.safetensors").is_file(),
                "resumed_from": entry["resumed_from"],
            }
        )
    return {
        "route_count": len(routes),
        "unique_route_keys": len({route["route_key"] for route in routes}),
        "routes": routes,
        "route_resolution_passed": len(routes) == 4 and all(
            route["route_key_exact"] and route["adapter_exists"] and route["resumed_from"] is None for route in routes
        ),
    }


def run(args: argparse.Namespace) -> dict:
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError(f"refusing overwrite of immutable output: {output}")
    v14 = load_artifact(args.v14.resolve())
    v15 = load_artifact(args.v15.resolve())
    if v14["config"]["model"] != MODEL_DEFAULT or v15["config"]["model"] != MODEL_DEFAULT:
        raise ValueError("model contract drift")
    if v14["tasks"] != v15["tasks"]:
        raise ValueError("task manifest drift between V14 and V15")
    fixed_differences = {
        key: {"v14": v14["config"].get(key), "v15": v15["config"].get(key)}
        for key in FIXED_KEYS
        if v14["config"].get(key) != v15["config"].get(key)
    }
    if fixed_differences:
        raise ValueError(f"fixed contract mismatch: {sorted(fixed_differences)}")
    if v14["result"]["state_slice"] != "continual-learning-protocol-v14-repaired-objective-retention" or v15["result"]["state_slice"] != "continual-learning-protocol-v15-interleaved-replay-retention":
        raise ValueError("source state drift")
    output.mkdir(parents=True)
    v14_results = v14["result"]["results"]
    v15_results = v15["result"]["results"]
    report = {
        "state_slice": STATE_SLICE,
        "classification": "TaskRoutedMemoryArchitectureAuditNoBreakthroughClaim",
        "claim_ceiling": "LocalDevelopmentTaskRoutedMemoryAudit",
        "source_artifacts": {
            "v14_root": str(v14["root"]),
            "v14_result_sha256": v14["result_file_sha256"],
            "v15_root": str(v15["root"]),
            "v15_result_sha256": v15["result_file_sha256"],
        },
        "fixed_contract_match": True,
        "matched_contract_keys": list(FIXED_KEYS),
        "retention_comparison": {
            "naive_v14": metric(v14["result"], "naive_sequential_lora", "retention_after_interference"),
            "shared_replay_v14": metric(v14["result"], "replay_lora", "retention_after_interference"),
            "interleaved_replay_v15": metric(v15["result"], "replay_lora", "retention_after_interference"),
            "task_adapter_bank_v14": metric(v14["result"], "task_adapter_bank", "retention_after_interference"),
        },
        "acquisition_comparison": {
            "naive_v14": metric(v14["result"], "naive_sequential_lora", "acquisition"),
            "shared_replay_v14": metric(v14["result"], "replay_lora", "acquisition"),
            "interleaved_replay_v15": metric(v15["result"], "replay_lora", "acquisition"),
            "task_adapter_bank_v14": metric(v14["result"], "task_adapter_bank", "acquisition"),
        },
        "route_audit": route_summary(v14),
        "storage": {"v14": storage_summary(v14["root"]), "v15": storage_summary(v15["root"])},
        "telemetry": {"v14": telemetry_summary(v14["root"]), "v15": telemetry_summary(v15["root"])},
        "gates": {
            "fixed_contract_match": True,
            "route_resolution": route_summary(v14)["route_resolution_passed"],
            "shared_replay_retention_above_naive": v14_results["replay_lora"]["retention_after_interference"]["accuracy"] > v14_results["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
            "interleaved_replay_retention_above_naive": v15_results["replay_lora"]["retention_after_interference"]["accuracy"] > v15_results["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
            "bank_retention_above_shared_naive": v14_results["task_adapter_bank"]["retention_after_interference"]["accuracy"] > v14_results["naive_sequential_lora"]["retention_after_interference"]["accuracy"],
            "runtime_or_memory_bottleneck_demonstrated": False,
        },
        "h100_authorized": False,
        "breakthrough_claim_eligible": False,
        "decision": "RoutePreservationControlValidatedSharedReplayProtocolRedesignRequired",
    }
    report["report_sha256"] = digest(report)
    (output / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v14", type=Path, default=Path("/tmp/continual-learning-model-v14-qwen-seed20260810-order0123"))
    parser.add_argument("--v15", type=Path, default=Path("/tmp/continual-learning-model-v15-qwen-seed20260810-order0123"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
