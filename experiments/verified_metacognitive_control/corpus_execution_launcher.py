"""Build a deterministic, plan-only execution matrix for the frozen corpus.

State slice: ``verified-metacognitive-control-execution-launch-v1``.

This module expands a preflight-valid 60-task corpus into the 300 planned
task/arm rows required by the promotion protocol. It binds every row to the
corpus digest, task identity, arm identity, task specification digest, and
controller configuration digest. It never executes an agent, invokes a
provider, mutates a checkout, or emits an execution result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from .corpus_preflight import validate_plan as validate_corpus_plan
from .protocol import PROMOTION_ARMS, SPLITS, digest_json


LAUNCH_STATE_SLICE = "verified-metacognitive-control-execution-launch-v1"
LAUNCH_SCHEMA_VERSION = "verified-metacognitive-execution-plan-v1"
LAUNCH_STATUS = "planned_not_run"
CLAIM_CEILING = "LocalDevelopmentExecutionPlanOnly"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SPLIT_ORDER = {split: index for index, split in enumerate(SPLITS)}


class LauncherError(ValueError):
    """Raised when a corpus cannot be converted into an execution plan."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise LauncherError(message)


def _require_digest(value: Any, field: str) -> str:
    _require(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, f"{field} must be lowercase SHA-256")
    return value


def _static_bindings(corpus_plan: dict[str, Any]) -> tuple[str, str, dict[str, str]]:
    task_spec_digest = _require_digest(corpus_plan.get("task_spec_digest"), "task_spec_digest")
    controller_config_digest = _require_digest(
        corpus_plan.get("controller_config_digest"), "controller_config_digest"
    )
    arm_digests = corpus_plan.get("arm_digests")
    _require(isinstance(arm_digests, dict), "arm_digests must be an object")
    _require(set(arm_digests) == set(PROMOTION_ARMS), "arm_digests keys must match frozen promotion arms")
    normalized = {
        arm: _require_digest(arm_digests.get(arm), f"arm_digests.{arm}")
        for arm in PROMOTION_ARMS
    }
    return task_spec_digest, controller_config_digest, normalized


def _canonical_cases(tasks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Return one canonical task identity per paired case after strict checks."""

    by_case: dict[str, dict[str, dict[str, Any]]] = {}
    for task in tasks:
        case_id = task["case_id"]
        by_case.setdefault(case_id, {})[task["arm"]] = task
    cases: list[dict[str, str]] = []
    for case_id in sorted(by_case):
        rows = by_case[case_id]
        _require(set(rows) == set(PROMOTION_ARMS), f"case {case_id} is not paired across all arms")
        baseline = rows["baseline"]
        for arm in PROMOTION_ARMS:
            row = rows[arm]
            _require(row["task_family"] == baseline["task_family"], f"case {case_id} family differs by arm")
            _require(row["split"] == baseline["split"], f"case {case_id} split differs by arm")
        cases.append(
            {
                "case_id": case_id,
                "task_family": baseline["task_family"],
                "split": baseline["split"],
            }
        )
    cases.sort(key=lambda row: (SPLIT_ORDER[row["split"]], row["case_id"]))
    return cases


def _plan_without_digest(plan: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in plan.items() if key != "plan_digest"}


def build_execution_plan(corpus_plan: dict[str, Any]) -> dict[str, Any]:
    """Validate and expand a corpus plan without running any external work."""

    preflight = validate_corpus_plan(corpus_plan)
    _require(preflight["valid"], "corpus preflight is not valid")
    task_spec_digest, controller_config_digest, arm_digests = _static_bindings(corpus_plan)
    cases = _canonical_cases(corpus_plan["tasks"])
    _require(len(cases) == 60, "execution launcher requires exactly 60 paired cases")

    source_corpus_digest = digest_json(corpus_plan)
    rows: list[dict[str, Any]] = []
    ordinal = 1
    for case in cases:
        task_digest = digest_json(
            {
                "workflow_id": corpus_plan["workflow_id"],
                "case_id": case["case_id"],
                "task_family": case["task_family"],
                "split": case["split"],
            }
        )
        for arm in PROMOTION_ARMS:
            arm_digest = arm_digests[arm]
            rows.append(
                {
                    "record_type": "planned_execution",
                    "ordinal": ordinal,
                    "workflow_id": corpus_plan["workflow_id"],
                    "case_id": case["case_id"],
                    "task_family": case["task_family"],
                    "split": case["split"],
                    "arm": arm,
                    "task_digest": task_digest,
                    "arm_digest": arm_digest,
                    "task_spec_digest": task_spec_digest,
                    "controller_config_digest": controller_config_digest,
                    "source_corpus_digest": source_corpus_digest,
                    "status": LAUNCH_STATUS,
                    "agent_execution_recorded": False,
                    "authority_granted": False,
                    "network_access": False,
                    "raw_reasoning_retained": False,
                }
            )
            ordinal += 1

    _require(len(rows) == 300, "execution launcher must emit exactly 300 rows")
    plan: dict[str, Any] = {
        "record_type": "execution_plan",
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "state_slice": LAUNCH_STATE_SLICE,
        "workflow_id": corpus_plan["workflow_id"],
        "source_corpus_digest": source_corpus_digest,
        "task_spec_digest": task_spec_digest,
        "controller_config_digest": controller_config_digest,
        "arm_digests": arm_digests,
        "arms": list(PROMOTION_ARMS),
        "paired_task_count": len(cases),
        "planned_execution_count": len(rows),
        "launch_status": LAUNCH_STATUS,
        "agent_execution_recorded": False,
        "validator_custody": False,
        "prediction_locked_before_assessment": False,
        "authority_granted": False,
        "network_access": False,
        "raw_reasoning_retained": False,
        "claim_ceiling": CLAIM_CEILING,
        "non_claims": [
            "not_agent_execution",
            "not_validator_custody",
            "not_experiment_evidence",
            "not_production_ready",
        ],
        "rows": rows,
    }
    plan["plan_digest"] = digest_json(_plan_without_digest(plan))
    return plan


def validate_execution_plan(plan: dict[str, Any]) -> None:
    """Validate the launcher output and its deterministic digest binding."""

    _require(isinstance(plan, dict), "execution plan must be an object")
    _require(plan.get("record_type") == "execution_plan", "record_type must be execution_plan")
    _require(plan.get("schema_version") == LAUNCH_SCHEMA_VERSION, "wrong execution plan schema")
    _require(plan.get("state_slice") == LAUNCH_STATE_SLICE, "wrong execution launch state slice")
    _require(isinstance(plan.get("workflow_id"), str) and plan["workflow_id"], "workflow_id required")
    _require(plan.get("launch_status") == LAUNCH_STATUS, "execution plan must remain plan-only")
    _require(plan.get("claim_ceiling") == CLAIM_CEILING, "wrong execution plan claim ceiling")
    _require(plan.get("agent_execution_recorded") is False, "execution plan cannot contain agent execution")
    _require(plan.get("validator_custody") is False, "execution plan cannot claim validator custody")
    _require(plan.get("prediction_locked_before_assessment") is False, "plan cannot claim prediction locking")
    _require(plan.get("authority_granted") is False, "execution plan cannot grant authority")
    _require(plan.get("network_access") is False, "execution plan cannot use network")
    _require(plan.get("raw_reasoning_retained") is False, "execution plan cannot retain raw reasoning")
    for field in ("source_corpus_digest", "task_spec_digest", "controller_config_digest", "plan_digest"):
        _require_digest(plan.get(field), field)
    _require(plan.get("arms") == list(PROMOTION_ARMS), "execution plan arms are not frozen")
    arm_digests = plan.get("arm_digests")
    _require(isinstance(arm_digests, dict), "execution plan arm_digests must be an object")
    _require(set(arm_digests) == set(PROMOTION_ARMS), "execution plan arm digest keys are not frozen")
    for arm in PROMOTION_ARMS:
        _require_digest(arm_digests.get(arm), f"arm_digests.{arm}")
    rows = plan.get("rows")
    _require(isinstance(rows, list) and len(rows) == 300, "execution plan must contain 300 rows")
    _require(plan.get("paired_task_count") == 60, "execution plan must declare 60 cases")
    _require(plan.get("planned_execution_count") == 300, "execution plan must declare 300 rows")
    seen: set[tuple[str, str]] = set()
    case_metadata: dict[str, tuple[str, str]] = {}
    case_arms: dict[str, set[str]] = {}
    for expected_ordinal, row in enumerate(rows, start=1):
        _require(isinstance(row, dict), f"planned row {expected_ordinal} must be an object")
        _require(row.get("record_type") == "planned_execution", f"planned row {expected_ordinal} has wrong type")
        _require(row.get("ordinal") == expected_ordinal, f"planned row ordinal mismatch at {expected_ordinal}")
        _require(row.get("workflow_id") == plan["workflow_id"], f"planned row {expected_ordinal} workflow mismatch")
        _require(row.get("status") == LAUNCH_STATUS, f"planned row {expected_ordinal} was executed")
        _require(row.get("agent_execution_recorded") is False, f"planned row {expected_ordinal} has execution")
        _require(row.get("authority_granted") is False, f"planned row {expected_ordinal} grants authority")
        _require(row.get("network_access") is False, f"planned row {expected_ordinal} uses network")
        _require(row.get("raw_reasoning_retained") is False, f"planned row {expected_ordinal} retains raw reasoning")
        _require(row.get("arm") in PROMOTION_ARMS, f"planned row {expected_ordinal} has invalid arm")
        _require(isinstance(row.get("case_id"), str) and row["case_id"], f"planned row {expected_ordinal} missing case")
        _require(
            isinstance(row.get("task_family"), str) and row["task_family"],
            f"planned row {expected_ordinal} missing task family",
        )
        _require(row.get("split") in SPLITS, f"planned row {expected_ordinal} has invalid split")
        case_id = row["case_id"]
        metadata = (row["task_family"], row["split"])
        _require(
            case_id not in case_metadata or case_metadata[case_id] == metadata,
            f"planned case {case_id} metadata differs by arm",
        )
        case_metadata[case_id] = metadata
        case_arms.setdefault(case_id, set()).add(row["arm"])
        key = (row.get("case_id"), row.get("arm"))
        _require(key not in seen, f"duplicate planned row: {key}")
        seen.add(key)
        for field in (
            "task_digest",
            "arm_digest",
            "task_spec_digest",
            "controller_config_digest",
            "source_corpus_digest",
        ):
            _require_digest(row.get(field), f"planned row {expected_ordinal}.{field}")
        _require(row["arm_digest"] == arm_digests[row["arm"]], f"planned row {expected_ordinal} arm binding mismatch")
        _require(row["task_spec_digest"] == plan["task_spec_digest"], f"planned row {expected_ordinal} spec binding mismatch")
        _require(
            row["controller_config_digest"] == plan["controller_config_digest"],
            f"planned row {expected_ordinal} controller binding mismatch",
        )
        _require(
            row["source_corpus_digest"] == plan["source_corpus_digest"],
            f"planned row {expected_ordinal} corpus binding mismatch",
        )
        _require(
            row["task_digest"]
            == digest_json(
                {
                    "workflow_id": plan["workflow_id"],
                    "case_id": row["case_id"],
                    "task_family": row["task_family"],
                    "split": row["split"],
                }
            ),
            f"planned row {expected_ordinal} task binding mismatch",
        )
    _require(len({row["case_id"] for row in rows}) == 60, "execution plan must contain 60 cases")
    for case_id, arms in case_arms.items():
        _require(arms == set(PROMOTION_ARMS), f"case {case_id} does not have five planned arms")
    _require(
        digest_json(_plan_without_digest(plan)) == plan["plan_digest"],
        "execution plan digest mismatch",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="preflight-valid corpus plan JSON")
    parser.add_argument("--output", required=True, help="plan-only execution plan JSON")
    args = parser.parse_args()
    try:
        corpus_plan = json.loads(Path(args.input).read_text(encoding="utf-8"))
        _require(isinstance(corpus_plan, dict), "corpus plan must be an object")
        plan = build_execution_plan(corpus_plan)
        validate_execution_plan(plan)
        Path(args.output).write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, LauncherError, TypeError, KeyError) as exc:
        print(f"execution_launch_error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "plan": args.output,
                "planned_execution_count": plan["planned_execution_count"],
                "launch_status": plan["launch_status"],
                "claim_ceiling": plan["claim_ceiling"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
