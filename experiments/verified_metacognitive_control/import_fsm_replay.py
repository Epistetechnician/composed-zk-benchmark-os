#!/usr/bin/env python3
"""Convert the existing FSM retry pilot into aggregate-only v1 trial rows.

This is historical reanalysis. It is intentionally not a fresh experiment and
cannot satisfy the live promotion gate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .protocol import INPUT_SCHEMA_VERSION, STATE_SLICE


CONDITION_TO_ARM = {
    "control": ("generic_retry_control", "none"),
    "localize": ("external_monitor_control", "external_telemetry"),
    "corrective": ("oracle_control", "oracle"),
    "sham": ("sham_control", "shuffled_telemetry"),
    "random_fact": ("random_fact_control", "shuffled_telemetry"),
}


def read_jsonl(path: Path) -> dict[int, dict]:
    rows = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[int(row["case_id"])] = row
    return rows


def retry_rows(root: Path, condition: str) -> dict[int, dict]:
    raw = {}
    for path in (root / "retry" / "raw").glob(f"*_{condition}.json"):
        row = json.loads(path.read_text(encoding="utf-8"))
        raw[int(row["case_id"])] = row
    evaluated = {}
    for path in (root / "retry" / "evaluated").glob(f"*_{condition}.json"):
        row = json.loads(path.read_text(encoding="utf-8"))
        evaluated[int(row["case_id"])] = row
    return {case_id: {"raw": raw[case_id], "evaluated": evaluated[case_id]} for case_id in raw}


def outcome(success: bool) -> tuple[str, bool]:
    return ("success", False) if success else ("costly_failure", True)


def make_trial(case_id: int, task_family: str, split: str, arm: str, decision: str, result: str, base: dict, retry: dict | None, signal: str) -> dict:
    retry_raw = retry["raw"] if retry else None
    retry_eval = retry["evaluated"] if retry else None
    final_success = bool(result)
    final_outcome, costly = outcome(final_success)
    usage = base["response"]["usage"]
    latency = float(base["latency_ms"])
    compute = int(usage["total_tokens"])
    attempts = 1
    if retry_raw is not None:
        latency += float(retry_raw["latency_ms"])
        compute += int(retry_raw["response"]["usage"]["total_tokens"])
        attempts = 2
    return {
        "record_type": "trial",
        "case_id": str(case_id),
        "task_family": task_family,
        "split": split,
        "arm": arm,
        "decision": decision,
        "outcome": final_outcome,
        "costly_failure": costly,
        "latency_ms": round(latency, 3),
        "compute_units": compute,
        "tool_calls": 0,
        "attempts": attempts,
        "monitor_overhead_ms": 0,
        "monitor_compute_units": 0,
        "monitor_signal_source": signal,
        "prediction_locked_before_assessment": False,
        "raw_reasoning_retained": False,
        "authority_granted": False,
    }


def convert(root: Path) -> list[dict]:
    base_raw = read_jsonl(root / "raw" / "actor_raw.jsonl")
    base_eval = read_jsonl(root / "evaluated" / "evaluated.jsonl")
    case_ids = sorted(base_raw)
    # The original pilot has no preregistered family split. Treat it as historical fit data.
    records = [{
        "record_type": "manifest",
        "schema_version": INPUT_SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "workflow_id": "astral_fsm_retry_v2",
        "source_type": "historical_replay_reanalysis",
        "fixed_budget": False,
        "budget": {"max_latency_ms": 12000, "max_compute_units": 100000, "max_tool_calls": 2, "max_attempts": 2},
        "arms": ["baseline", "generic_retry_control", "external_monitor_control", "oracle_control", "sham_control", "random_fact_control"],
        "prediction_locked_before_assessment": False,
        "raw_reasoning_retained": False,
        "authority_granted": False,
        "source_note": "Historical FSM retry pilot; not preregistered under this PRD.",
    }]
    for case_id in case_ids:
        base = base_raw[case_id]
        base_result = base_eval[case_id]
        task_family = f"fsm_stage_{base.get('stage', 'unknown')}"
        records.append(make_trial(case_id, task_family, "fit", "baseline", "proceed", base_result["overall_exact"], base, None, "none"))
        for condition, (arm, signal) in CONDITION_TO_ARM.items():
            retry = retry_rows(root, condition).get(case_id)
            retry_success = bool(retry["evaluated"]["overall_exact"]) if retry else False
            final_success = bool(base_result["overall_exact"] or retry_success)
            decision = "revise" if retry else "proceed"
            records.append(make_trial(case_id, task_family, "fit", arm, decision, final_success, base, retry, signal))
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    records = convert(Path(args.root))
    output = Path(args.output)
    with output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
    print(json.dumps({"records_written": len(records), "output": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
