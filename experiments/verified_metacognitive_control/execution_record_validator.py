"""Validate independently captured agent records against a frozen plan.

State slice: ``verified-metacognitive-control-execution-record-validation-v1``.

This is a structural custody gate. It does not execute an agent, inspect raw
model material, validate semantic task success, or grant authority. It proves
only that an external record bundle has complete coverage of the plan and that
each record carries the plan's immutable digest bindings.
"""

from __future__ import annotations

from typing import Any, Iterable

from .corpus_execution_launcher import LauncherError, validate_execution_plan
from .protocol import PROMOTION_ARMS
from .repository_change_capture import _assert_no_forbidden_keys


VALIDATION_STATE_SLICE = "verified-metacognitive-control-execution-record-validation-v1"


class ExecutionRecordError(ValueError):
    """Raised when captured records do not match the frozen execution plan."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ExecutionRecordError(message)


def _digest(value: Any, field: str) -> None:
    _require(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value),
        f"{field} must be lowercase SHA-256",
    )


def validate_plan_bound_records(
    execution_plan: dict[str, Any],
    execution_manifest: dict[str, Any],
    agent_records: Iterable[dict[str, Any]],
) -> None:
    """Require complete, digest-bound coverage of every planned row."""

    _require(isinstance(execution_manifest, dict), "agent execution manifest must be an object")
    try:
        validate_execution_plan(execution_plan)
    except LauncherError as exc:
        raise ExecutionRecordError(f"invalid execution plan: {exc}") from exc

    _assert_no_forbidden_keys(execution_manifest, "agent_execution_manifest")
    _require(
        execution_manifest.get("execution_plan_digest") == execution_plan["plan_digest"],
        "agent manifest execution plan digest mismatch",
    )
    _require(
        execution_manifest.get("workflow_id") == execution_plan["workflow_id"],
        "agent manifest workflow id mismatch",
    )
    _digest(execution_manifest.get("execution_plan_digest"), "execution_plan_digest")

    plan_rows = {
        (row["case_id"], row["split"], row["arm"]): row
        for row in execution_plan["rows"]
    }
    records = tuple(agent_records)
    _require(len(records) == len(plan_rows), "agent records must cover all 300 planned rows")
    seen: set[tuple[str, str, str]] = set()
    for index, record in enumerate(records, start=1):
        _require(isinstance(record, dict), f"agent record {index} must be an object")
        _assert_no_forbidden_keys(record, f"agent_execution_record[{index}]")
        key = (record.get("case_id"), record.get("split"), record.get("arm"))
        _require(
            isinstance(record.get("workflow_id"), str) and record["workflow_id"],
            f"agent record {index} workflow id required",
        )
        _require(
            isinstance(record.get("case_id"), str) and record["case_id"],
            f"agent record {index} case id required",
        )
        _require(isinstance(record.get("split"), str), f"agent record {index} split must be text")
        _require(isinstance(record.get("arm"), str), f"agent record {index} arm must be text")
        _require(key in plan_rows, f"agent record {index} is not in the frozen execution plan: {key}")
        _require(key not in seen, f"duplicate plan-bound agent record: {key}")
        expected = plan_rows[key]
        _require(record.get("workflow_id") == execution_plan["workflow_id"], f"agent record {index} workflow mismatch")
        _require(record.get("task_family") == expected["task_family"], f"agent record {index} task family mismatch")
        for field in (
            "source_corpus_digest",
            "task_digest",
            "arm_digest",
            "task_spec_digest",
            "controller_config_digest",
        ):
            _digest(record.get(field), f"agent record {index}.{field}")
        for field in (
            "source_corpus_digest",
            "task_digest",
            "arm_digest",
            "task_spec_digest",
            "controller_config_digest",
        ):
            _require(record[field] == expected[field], f"agent record {index}.{field} binding mismatch")
        _require(record["execution_plan_digest"] == execution_plan["plan_digest"], f"agent record {index} plan mismatch")
        _require(record["arm_digest"] == execution_plan["arm_digests"][record["arm"]], f"agent record {index} arm mismatch")
        _require(record["arm"] in PROMOTION_ARMS, f"agent record {index} arm is not frozen")
        seen.add(key)
    _require(seen == set(plan_rows), "agent record coverage does not equal the frozen plan")
