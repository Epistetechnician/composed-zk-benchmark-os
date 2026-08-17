"""Run the frozen repository validator without granting workflow authority.

State slice: ``verified-metacognitive-control-repository-validator-v1``.

This runner is intentionally narrower than an agent runner. It accepts a
validator plan, executes only fixed command profiles with ``shell=False``,
discards command output, and emits a metadata-only preflight report. The
report is not an experiment input because it does not prove paired agent
execution. A future operator may convert independently captured agent records
through ``repository_change_capture.py`` after validator custody is established.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from .protocol import DECISIONS, PROMOTION_ARMS, SIGNAL_SOURCES, SPLITS, digest_json
from .repository_change_capture import (
    CAPTURE_STATE_SLICE,
    CHECK_STATUSES,
    REQUIRED_CHECK_IDS,
    _assert_no_forbidden_keys,
)

VALIDATOR_STATE_SLICE = "verified-metacognitive-control-repository-validator-v1"
VALIDATOR_SCHEMA_VERSION = "verified-metacognitive-repository-validator-plan-v1"
REPORT_SCHEMA_VERSION = "verified-metacognitive-repository-validator-report-v1"
MAX_CHECK_TIMEOUT_SECONDS = 120

FIXED_CHECK_PROFILES: dict[str, dict[str, tuple[str, ...]]] = {
    "zkbench_metacognitive_v1": {
        "format": ("cargo", "fmt", "--all", "--", "--check"),
        "focused_tests": ("cargo", "test", "-p", "zkbench-core", "--test", "metacognitive_monitor_control"),
        "contract_validation": ("cargo", "test", "-p", "zkbench-core", "--test", "repo_hygiene"),
        "diff_hygiene": ("git", "diff", "--check"),
        "claim_boundary": ("cargo", "test", "-p", "zkbench-core", "--test", "repo_claim_boundary_docs"),
    },
}


class ValidatorError(ValueError):
    """Raised when a validator plan is malformed or unsafe."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidatorError(message)


def _nonnegative_integer(value: Any, field: str) -> None:
    _require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"{field} must be a nonnegative integer")


def _validate_relative_path(value: Any, field: str) -> str:
    _require(isinstance(value, str) and value, f"{field} must be a nonempty relative path")
    path = Path(value)
    _require(not path.is_absolute(), f"{field} must be relative")
    _require(".." not in path.parts, f"{field} cannot escape the checkout")
    _require("\\" not in value, f"{field} must use slash-separated paths")
    return value.rstrip("/") or "."


def validate_plan(plan: dict[str, Any]) -> None:
    _require(isinstance(plan, dict), "validator plan must be an object")
    _assert_no_forbidden_keys(plan, "plan")
    _require(plan.get("record_type") == "validator_plan", "record_type must be validator_plan")
    _require(plan.get("schema_version") == VALIDATOR_SCHEMA_VERSION, "wrong validator plan schema")
    _require(plan.get("state_slice") == VALIDATOR_STATE_SLICE, "wrong validator state slice")
    _require(isinstance(plan.get("workflow_id"), str) and plan["workflow_id"], "workflow_id required")
    _require(plan.get("network_access") is False, "network access must be false")
    _require(plan.get("authority_granted") is False, "authority grant must be false")
    _require(plan.get("raw_reasoning_retained") is False, "raw reasoning retention must be false")
    _require(isinstance(plan.get("expected_base_revision"), str) and len(plan["expected_base_revision"]) >= 7, "expected_base_revision required")
    _require(all(character in "0123456789abcdef" for character in plan["expected_base_revision"].lower()), "expected_base_revision must be hexadecimal")
    _require(plan.get("check_profile") in FIXED_CHECK_PROFILES, "unknown fixed check profile")
    root = plan.get("root")
    _require(isinstance(root, str) and root, "root required")
    root_path = Path(root)
    _require(root_path.is_absolute(), "root must be absolute")
    _require(root_path.exists() and root_path.is_dir(), "root must be an existing directory")
    allowed_paths = plan.get("allowed_paths")
    _require(isinstance(allowed_paths, list) and allowed_paths, "allowed_paths required")
    for index, value in enumerate(allowed_paths):
        _validate_relative_path(value, f"allowed_paths[{index}]")
    budget = plan.get("budget")
    _require(isinstance(budget, dict), "budget required")
    for field in ("max_latency_ms", "max_compute_units", "max_tool_calls", "max_attempts"):
        _require(
            isinstance(budget.get(field), int)
            and not isinstance(budget[field], bool)
            and budget[field] > 0,
            f"positive budget required: {field}",
        )
    tasks = plan.get("tasks")
    _require(isinstance(tasks, list) and tasks, "tasks required")
    seen: set[tuple[str, str, str]] = set()
    for index, task in enumerate(tasks):
        _require(isinstance(task, dict), f"task {index} must be an object")
        required = ("case_id", "task_family", "split", "arm", "decision", "monitor_score_milli", "monitor_signal_source")
        for field in required:
            _require(field in task, f"task {index} missing {field}")
        for field in ("case_id", "task_family"):
            _require(isinstance(task[field], str) and task[field], f"task {index} {field} required")
        _require(task["split"] in SPLITS, f"task {index} has invalid split")
        _require(task["arm"] in PROMOTION_ARMS, f"task {index} has invalid promotion arm")
        _require(task["decision"] in DECISIONS, f"task {index} has invalid decision")
        _require(
            isinstance(task["monitor_score_milli"], int)
            and not isinstance(task["monitor_score_milli"], bool)
            and 0 <= task["monitor_score_milli"] <= 1000,
            f"task {index} monitor score out of range",
        )
        _require(task["monitor_signal_source"] in SIGNAL_SOURCES, f"task {index} has invalid monitor signal source")
        key = (task["case_id"], task["split"], task["arm"])
        _require(key not in seen, f"duplicate task-arm row: {key}")
        seen.add(key)


def _safe_environment() -> dict[str, str]:
    blocked_tokens = ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "API_KEY", "PRIVATE_KEY")
    environment = {
        key: value
        for key, value in os.environ.items()
        if not any(token in key.upper() for token in blocked_tokens)
    }
    environment.update(
        {
            "CARGO_NET_OFFLINE": "true",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "RUSTUP_NO_UPDATE_CHECK": "1",
        }
    )
    return environment


def _run_command(argv: tuple[str, ...], root: Path, timeout_seconds: int) -> dict[str, Any]:
    started_wall = time.monotonic()
    started_cpu = time.process_time()
    try:
        completed = subprocess.run(
            list(argv),
            cwd=root,
            env=_safe_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            check=False,
            timeout=timeout_seconds,
        )
        status = "pass" if completed.returncode == 0 else "fail"
        exit_code: int | None = completed.returncode
        timed_out = False
    except (OSError, subprocess.TimeoutExpired):
        status = "fail"
        exit_code = None
        timed_out = True
    elapsed_ms = max(0.0, (time.monotonic() - started_wall) * 1000.0)
    cpu_ms = max(0.0, (time.process_time() - started_cpu) * 1000.0)
    report = {
        "status": status,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "latency_ms": round(elapsed_ms, 3),
        "compute_units": max(1, math.ceil(cpu_ms)),
    }
    return report


def _git_lines(root: Path, argv: tuple[str, ...]) -> tuple[bool, list[str]]:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=root,
            env=_safe_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            shell=False,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, []
    if completed.returncode != 0:
        return False, []
    return True, [line for line in completed.stdout.splitlines() if line]


def _scope_valid(root: Path, allowed_paths: list[str]) -> tuple[bool, list[str]]:
    commands = (
        ("git", "diff", "--name-only"),
        ("git", "diff", "--cached", "--name-only"),
        ("git", "ls-files", "--others", "--exclude-standard"),
    )
    changed: set[str] = set()
    for command in commands:
        ok, lines = _git_lines(root, command)
        if not ok:
            return False, ["git_state_unavailable"]
        changed.update(lines)
    normalized_allowed = [path.rstrip("/") for path in allowed_paths]
    unexpected = sorted(
        path for path in changed
        if not any(path == allowed or path.startswith(f"{allowed}/") for allowed in normalized_allowed)
    )
    return not unexpected, unexpected


def _provenance_valid(root: Path, expected_base_revision: str) -> tuple[bool, str | None]:
    ok, lines = _git_lines(root, ("git", "rev-parse", "HEAD"))
    if not ok or len(lines) != 1:
        return False, None
    actual = lines[0]
    return actual.startswith(expected_base_revision), actual


def _repository_root(root: Path) -> Path | None:
    """Return the resolved Git top-level when ``root`` is exactly that root."""

    ok, lines = _git_lines(root, ("git", "rev-parse", "--show-toplevel"))
    if not ok or len(lines) != 1:
        return None
    candidate = Path(lines[0]).resolve()
    return candidate if candidate == root else None


def _run_checks(root: Path, profile: str, timeout_seconds: int) -> tuple[dict[str, str], bool, float, int, int]:
    check_results: dict[str, str] = {}
    timed_out = False
    total_latency_ms = 0.0
    total_compute_units = 0
    command_count = 0
    for check_id in REQUIRED_CHECK_IDS:
        command = FIXED_CHECK_PROFILES[profile][check_id]
        outcome = _run_command(command, root, timeout_seconds)
        check_results[check_id] = outcome["status"]
        timed_out = timed_out or outcome["timed_out"]
        total_latency_ms += outcome["latency_ms"]
        total_compute_units += outcome["compute_units"]
        command_count += 1
    return check_results, timed_out, round(total_latency_ms, 3), total_compute_units, command_count


def validate_and_run(plan: dict[str, Any]) -> dict[str, Any]:
    validate_plan(plan)
    root = Path(plan["root"]).resolve()
    if _repository_root(root) is None:
        raise ValidatorError("root must be the top-level of a Git checkout")
    scope_ok, unexpected_paths = _scope_valid(root, plan["allowed_paths"])
    provenance_ok, actual_revision = _provenance_valid(root, plan["expected_base_revision"])
    check_results, timed_out, latency_ms, compute_units, command_count = _run_checks(
        root,
        plan["check_profile"],
        max(1, min(int(plan["budget"]["max_latency_ms"] / 1000), MAX_CHECK_TIMEOUT_SECONDS)),
    )
    budget_exhausted = (
        latency_ms > plan["budget"]["max_latency_ms"]
        or compute_units > plan["budget"]["max_compute_units"]
        or command_count > plan["budget"]["max_tool_calls"]
    )
    rows: list[dict[str, Any]] = []
    for task in plan["tasks"]:
        rows.append(
            {
                "record_type": "validator_observation",
                "case_id": task["case_id"],
                "task_family": task["task_family"],
                "split": task["split"],
                "arm": task["arm"],
                "decision": task["decision"],
                "monitor_score_milli": task["monitor_score_milli"],
                "monitor_signal_source": task["monitor_signal_source"],
                "check_results": check_results,
                "scope_valid": scope_ok,
                "provenance_valid": provenance_ok,
                "unexpected_paths": unexpected_paths,
                "timed_out": timed_out,
                "budget_exhausted": budget_exhausted,
                "capability_gap": False,
                "safe_abstention": task["decision"] == "abstain" and not scope_ok,
                "latency_ms": latency_ms,
                "compute_units": compute_units,
                "tool_calls": command_count,
                "attempts": 1,
                "monitor_overhead_ms": 0,
                "monitor_compute_units": 0,
                "prediction_locked_before_assessment": False,
                "raw_reasoning_retained": False,
                "authority_granted": False,
                "network_access": False,
            }
        )
    report = {
        "record_type": "validator_report",
        "schema_version": REPORT_SCHEMA_VERSION,
        "state_slice": VALIDATOR_STATE_SLICE,
        "capture_state_slice": CAPTURE_STATE_SLICE,
        "workflow_id": plan["workflow_id"],
        "root_digest": hashlib.sha256(str(root).encode("utf-8")).hexdigest(),
        "expected_base_revision": plan["expected_base_revision"],
        "actual_base_revision": actual_revision,
        "check_profile": plan["check_profile"],
        "agent_execution_recorded": False,
        "validator_custody": True,
        "claim_ceiling": "LocalDevelopmentValidatorPreflightOnly",
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "scope_valid": scope_ok,
        "provenance_valid": provenance_ok,
        "check_results": check_results,
        "unexpected_paths": unexpected_paths,
        "rows": rows,
        "non_claims": [
            "not_agent_execution",
            "not_paired_experiment_evidence",
            "not_production_ready",
            "not_authority",
        ],
    }
    report["report_digest"] = digest_json(report)
    return report


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, help="validator plan JSON")
    parser.add_argument("--output", required=True, help="metadata-only validator report JSON")
    args = parser.parse_args()
    try:
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        report = validate_and_run(plan)
        write_json(args.output, report)
    except (OSError, json.JSONDecodeError, ValidatorError) as exc:
        print(f"validator_error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"report": args.output, "claim_ceiling": report["claim_ceiling"], "scope_valid": report["scope_valid"], "provenance_valid": report["provenance_valid"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
