"""Preflight the frozen live corpus shape before any agent execution.

State slice: ``verified-metacognitive-control-corpus-preflight-v1``.

This module validates task identities, arm pairing, family/split coverage, and
metadata retention rules. It does not execute an agent, run a checker, or
convert a plan into evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .protocol import MIN_PAIRED_TASKS, MIN_SPLIT_TASKS, MIN_TASK_FAMILIES, PROMOTION_ARMS, SPLITS
from .repository_change_capture import _assert_no_forbidden_keys

PREFLIGHT_STATE_SLICE = "verified-metacognitive-control-corpus-preflight-v1"
PREFLIGHT_SCHEMA_VERSION = "verified-metacognitive-corpus-plan-v1"
REPORT_SCHEMA_VERSION = "verified-metacognitive-corpus-preflight-report-v1"


class PreflightError(ValueError):
    """Raised when a corpus plan is malformed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(plan, dict), "corpus plan must be an object")
    _assert_no_forbidden_keys(plan, "corpus_plan")
    _require(plan.get("record_type") == "corpus_plan", "record_type must be corpus_plan")
    _require(plan.get("schema_version") == PREFLIGHT_SCHEMA_VERSION, "wrong corpus plan schema")
    _require(plan.get("state_slice") == PREFLIGHT_STATE_SLICE, "wrong corpus preflight state slice")
    _require(isinstance(plan.get("workflow_id"), str) and plan["workflow_id"], "workflow_id required")
    _require(plan.get("authority_granted") is False, "authority grant must be false")
    _require(plan.get("raw_reasoning_retained") is False, "raw reasoning retention must be false")
    _require(plan.get("network_access") is False, "network access must be false")
    _require(plan.get("arms") == list(PROMOTION_ARMS), "corpus must declare the frozen promotion arms in order")
    tasks = plan.get("tasks")
    _require(isinstance(tasks, list) and tasks, "tasks required")
    rows: set[tuple[str, str, str]] = set()
    case_splits: dict[str, set[str]] = {}
    baseline_rows: list[dict[str, Any]] = []
    for index, task in enumerate(tasks):
        _require(isinstance(task, dict), f"task {index} must be an object")
        for field in ("case_id", "task_family", "split", "arm"):
            _require(isinstance(task.get(field), str) and task[field], f"task {index} missing {field}")
        _require(task["split"] in SPLITS, f"task {index} has invalid split")
        _require(task["arm"] in PROMOTION_ARMS, f"task {index} has invalid arm")
        key = (task["case_id"], task["split"], task["arm"])
        _require(key not in rows, f"duplicate row: {key}")
        rows.add(key)
        case_splits.setdefault(task["case_id"], set()).add(task["split"])
        if task["arm"] == "baseline":
            baseline_rows.append(task)
    baseline_cases = {task["case_id"] for task in baseline_rows}
    baseline_families = {task["task_family"] for task in baseline_rows}
    split_counts = {split: sum(task["split"] == split for task in baseline_rows) for split in SPLITS}
    arm_cases = {
        arm: {task["case_id"] for task in tasks if task["arm"] == arm}
        for arm in PROMOTION_ARMS
    }
    checks = {
        "minimum_paired_tasks": len(baseline_cases) >= MIN_PAIRED_TASKS,
        "minimum_task_families": len(baseline_families) >= MIN_TASK_FAMILIES,
        "minimum_split_tasks": all(split_counts[split] >= MIN_SPLIT_TASKS[split] for split in SPLITS),
        "task_ids_are_split_disjoint": all(len(splits) == 1 for splits in case_splits.values()),
        "all_promotion_arms_paired": all(arm_cases[arm] == baseline_cases for arm in PROMOTION_ARMS),
        "unique_arm_rows": len(rows) == len(tasks),
    }
    return {
        "record_type": "corpus_preflight_report",
        "schema_version": REPORT_SCHEMA_VERSION,
        "state_slice": PREFLIGHT_STATE_SLICE,
        "workflow_id": plan["workflow_id"],
        "valid": all(checks.values()),
        "claim_ceiling": "LocalDevelopmentCorpusPreflightOnly",
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "checks": checks,
        "paired_task_count": len(baseline_cases),
        "task_family_count": len(baseline_families),
        "baseline_split_counts": split_counts,
        "required_split_counts": dict(MIN_SPLIT_TASKS),
        "arm_counts": {arm: len(arm_cases[arm]) for arm in PROMOTION_ARMS},
        "non_claims": [
            "not_agent_execution",
            "not_validator_custody",
            "not_experiment_evidence",
            "not_production_ready",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="corpus plan JSON")
    parser.add_argument("--output", required=True, help="preflight report JSON")
    args = parser.parse_args()
    try:
        plan = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = validate_plan(plan)
        Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, PreflightError) as exc:
        print(f"preflight_error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"report": args.output, "valid": report["valid"], "claim_ceiling": report["claim_ceiling"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
