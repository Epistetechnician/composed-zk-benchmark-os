#!/usr/bin/env python3
"""Read-only forgetting diagnosis for plasticity recovery V1.

State slice: ``continual-learning-plasticity-recovery-v1``.

The diagnosis replays the already-frozen exact synthetic transition kernel and
does not alter thresholds, seeds, orders, source results, or model state. It
explains the failed forgetting guard by protected shard, state unit, replay
target, reinitialization event, and fit-order sensitivity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from experiments.continual_learning import plasticity_recovery_v1 as runner
except ModuleNotFoundError:  # Direct ``python path/to/script.py`` entry point.
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from experiments.continual_learning import plasticity_recovery_v1 as runner


STATE_SLICE = "continual-learning-plasticity-recovery-v1"
DIAGNOSIS_SCHEMA = "continual-learning-plasticity-recovery-diagnosis-v1"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _trace_case(panel: Sequence[runner.Shard], arm: str, seed: int, order_seed: int) -> tuple[list[dict[str, Any]], runner.State, tuple[runner.Shard, ...], list[tuple[runner.Shard, tuple[float, ...]]]]:
    """Reconstruct one frozen case while retaining diagnosis-only state trace."""

    fit_by_id = {shard.shard_id: shard for shard in panel if shard.split == "fit"}
    ordered = runner.make_order(panel, order_seed)
    state = runner._initial_state()
    shadow_state = state
    trace: list[dict[str, Any]] = []
    protected_snapshots: list[tuple[runner.Shard, tuple[float, ...]]] = []
    for step, current in enumerate(ordered):
        work = state
        reinitialized_unit = None
        if arm in ("selective_reinit", "replay_selective_reinit"):
            work, reinitialized_unit = runner._reinitialize(work, step)
        targets = [current, current]
        if arm in ("replay", "replay_selective_reinit"):
            targets[1] = runner._replay_target(work, fit_by_id, current, seed, step)
        shadow = shadow_state if arm == "no_update" else work
        slot_records = []
        for slot, target in enumerate(targets):
            shadow, record = runner._gradient_step(
                shadow,
                target,
                current,
                step,
                slot,
                runner.LEARNING_RATE if slot == 0 else runner.REPLAY_LEARNING_RATE,
                reinitialized_unit if slot == 0 else None,
            )
            slot_records.append(record)
        if arm == "no_update":
            shadow_state = replace(
                shadow,
                gradient_evaluations=shadow.gradient_evaluations + runner.GRADIENT_SLOTS,
                shadow_gradient_evaluations=shadow.shadow_gradient_evaluations + runner.GRADIENT_SLOTS,
            )
            accepted = False
            state_after = replace(
                state,
                gradient_evaluations=state.gradient_evaluations + runner.GRADIENT_SLOTS,
                shadow_gradient_evaluations=state.shadow_gradient_evaluations + runner.GRADIENT_SLOTS,
            )
        else:
            state_after = replace(
                shadow,
                replay_buffer=(state.replay_buffer + (current.shard_id,))[-runner.REPLAY_CAPACITY:]
                if arm in ("replay", "replay_selective_reinit")
                else state.replay_buffer,
                committed_shards=state.committed_shards + (current.shard_id,),
                updates=state.updates + tuple(slot_records),
                gradient_evaluations=state.gradient_evaluations + runner.GRADIENT_SLOTS,
                shadow_gradient_evaluations=state.shadow_gradient_evaluations + runner.GRADIENT_SLOTS,
            )
            accepted = True
        if accepted and step < 4:
            protected_snapshots.append((current, state_after.weights))
        trace.append(
            {
                "step": step,
                "source_shard_id": current.shard_id,
                "target_shard_ids": [target.shard_id for target in targets],
                "reinitialized_unit": reinitialized_unit,
                "accepted": accepted,
                "slot_records": [asdict(record) for record in slot_records],
                "after_weights": list(state_after.weights),
                "after_utility": list(state_after.utility),
                "after_age": list(state_after.age),
            }
        )
        state = state_after
    return trace, state, ordered, protected_snapshots


def _protected_rows(state: runner.State, snapshots: Sequence[tuple[runner.Shard, tuple[float, ...]]]) -> list[dict[str, Any]]:
    base = (0.0,) * runner.DIMENSION
    rows = []
    for shard, protected_weights in snapshots:
        protected_loss = runner._loss(protected_weights, shard.target)
        final_loss = runner._loss(state.weights, shard.target)
        base_loss = runner._loss(base, shard.target)
        degradation = max(0.0, final_loss - protected_loss)
        per_unit = [
            max(
                0.0,
                ((state.weights[index] - shard.target[index]) ** 2 - (protected_weights[index] - shard.target[index]) ** 2)
                / (2.0 * runner.DIMENSION),
            )
            for index in range(runner.DIMENSION)
        ]
        rows.append(
            {
                "shard_id": shard.shard_id,
                "base_loss": round(base_loss, 12),
                "protected_loss": round(protected_loss, 12),
                "final_loss": round(final_loss, 12),
                "degradation": round(degradation, 12),
                "normalized_degradation": round(degradation / max(base_loss, 1e-12), 12),
                "unit_contributions": [round(value, 12) for value in per_unit],
            }
        )
    return rows


def _case_diagnosis(panel: Sequence[runner.Shard], arm: str, seed: int, order_seed: int) -> dict[str, Any]:
    trace, state, ordered, snapshots = _trace_case(panel, arm, seed, order_seed)
    protected = _protected_rows(state, snapshots)
    replay_targets = [
        update["target_shard_ids"][1]
        for update in trace
        if arm in ("replay", "replay_selective_reinit") and update["target_shard_ids"][1] != update["source_shard_id"]
    ]
    reinitializations = [
        {"step": update["step"], "unit": update["reinitialized_unit"]}
        for update in trace
        if update["reinitialized_unit"] is not None
    ]
    return {
        "case": f"seed-{seed}-order-{order_seed}",
        "seed": seed,
        "order_seed": order_seed,
        "arm": arm,
        "fit_order": [shard.shard_id for shard in ordered],
        "protected_shards": protected,
        "replay_target_shard_ids": replay_targets,
        "reinitializations": reinitializations,
        "final_weights": list(state.weights),
    }


def _aggregate_cases(cases: Sequence[Mapping[str, Any]], source_result: Mapping[str, Any]) -> dict[str, Any]:
    per_arm: dict[str, dict[str, Any]] = {}
    result_cases = {(int(case["seed"]), int(case["order_seed"]), str(case["arm"])): case for case in source_result["cases"]}
    for arm in runner.ARMS:
        selected = [case for case in cases if case["arm"] == arm]
        protected_rows = [row for case in selected for row in case["protected_shards"]]
        shard_groups: dict[str, list[float]] = defaultdict(list)
        unit_groups: dict[int, list[float]] = defaultdict(list)
        replay_counts: Counter[str] = Counter()
        reinit_counts: Counter[str] = Counter()
        for case in selected:
            for row in case["protected_shards"]:
                shard_groups[row["shard_id"]].append(float(row["normalized_degradation"]))
                for unit, value in enumerate(row["unit_contributions"]):
                    unit_groups[unit].append(float(value))
            replay_counts.update(case["replay_target_shard_ids"])
            reinit_counts.update(str(item["unit"]) for item in case["reinitializations"])
        order_by_seed: dict[int, list[float]] = defaultdict(list)
        forgetting_by_seed: dict[int, list[float]] = defaultdict(list)
        gain_rows = []
        for case in selected:
            result_case = result_cases[(int(case["seed"]), int(case["order_seed"]), arm)]
            gain_rows.append(
                {
                    "case": case["case"],
                    "seed": case["seed"],
                    "order_seed": case["order_seed"],
                    "adaptation_gain": result_case["adaptation_gain"],
                    "forgetting": result_case["forgetting"],
                }
            )
            order_by_seed[int(case["seed"])].append(float(result_case["adaptation_gain"]))
            forgetting_by_seed[int(case["seed"])].append(float(result_case["forgetting"]))
        per_arm[arm] = {
            "case_count": len(selected),
            "affected_protected_shards": [
                {
                    "shard_id": shard_id,
                    "case_count": len(values),
                    "mean_normalized_degradation": round(sum(values) / len(values), 12),
                    "max_normalized_degradation": round(max(values), 12),
                }
                for shard_id, values in sorted(shard_groups.items(), key=lambda item: (-max(item[1]), item[0]))
                if max(values) > 0.0
            ],
            "unit_contributions": [
                {
                    "unit": unit,
                    "mean_positive_protected_loss_contribution": round(sum(values) / len(values), 12),
                    "max_positive_protected_loss_contribution": round(max(values), 12),
                    "reinitialization_count": reinit_counts.get(str(unit), 0),
                }
                for unit, values in sorted(unit_groups.items())
            ],
            "replay_target_slot_count": sum(replay_counts.values()),
            "replay_target_shard_counts": dict(sorted(replay_counts.items())),
            "reinitialization_count": sum(reinit_counts.values()),
            "reinitialization_unit_counts": dict(sorted(reinit_counts.items())),
            "order_sensitivity": {
                "adaptation_gain_range_by_seed": round(max((max(values) - min(values) for values in order_by_seed.values()), default=0.0), 12),
                "forgetting_range_by_seed": round(max((max(values) - min(values) for values in forgetting_by_seed.values()), default=0.0), 12),
                "adaptation_gain_rows": gain_rows,
            },
            "max_forgetting": round(max((float(row["forgetting"]) for row in gain_rows), default=0.0), 12),
            "mean_forgetting": round(sum(float(row["forgetting"]) for row in gain_rows) / max(1, len(gain_rows)), 12),
            "protected_row_count": len(protected_rows),
        }
    return per_arm


def diagnose(result_path: Path) -> dict[str, Any]:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    _require(isinstance(result, dict), "source result must be a JSON object")
    runner.validate_result(result)
    panels = {seed: runner.make_panel(seed) for seed in runner.SEEDS}
    cases = []
    for seed in runner.SEEDS:
        for order_seed in runner.ORDER_SEEDS:
            for arm in runner.ARMS:
                cases.append(_case_diagnosis(panels[seed], arm, seed, order_seed))
    per_arm = _aggregate_cases(cases, result)
    body = {
        "state_slice": STATE_SLICE,
        "schema_version": DIAGNOSIS_SCHEMA,
        "diagnosis_type": "read_only_forgetting_diagnosis",
        "source_result_sha256": result["result_sha256"],
        "source_result_file_sha256": _sha256_file(result_path),
        "source_case_count": len(result["cases"]),
        "case_count": len(cases),
        "thresholds_changed": False,
        "new_mechanism_preregistered": False,
        "classification": "NoCandidate",
        "arms": per_arm,
        "claims": [
            "read_only_reconstruction",
            "protected_shard_forgetting_attribution",
            "unit_level_positive_loss_contribution",
            "replay_target_accounting",
            "reinitialization_event_accounting",
            "fit_order_sensitivity",
        ],
    }
    return {**body, "diagnosis_sha256": _digest(body)}


def markdown_report(diagnosis: Mapping[str, Any]) -> str:
    lines = [
        "# Plasticity Recovery V1 Forgetting Diagnosis",
        "",
        "Read-only reconstruction of the frozen exact-synthetic learner. No threshold, seed, order, or mechanism was changed.",
        "",
        f"Source result SHA-256: `{diagnosis['source_result_sha256']}`",
        f"Diagnosis SHA-256: `{diagnosis['diagnosis_sha256']}`",
        "",
        "| Arm | Max forgetting | Mean forgetting | Replay slots | Reinitializations | Order gain range |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in runner.ARMS:
        data = diagnosis["arms"][arm]
        lines.append(
            f"| `{arm}` | {data['max_forgetting']:.8f} | {data['mean_forgetting']:.8f} | "
            f"{data['replay_target_slot_count']} | {data['reinitialization_count']} | "
            f"{data['order_sensitivity']['adaptation_gain_range_by_seed']:.8f} |"
        )
    lines.extend(
        [
            "",
            "Interpretation: the local updating arms improved held-out loss but incurred protected-window degradation above the frozen hard guard. This diagnosis does not authorize a new mechanism or model-bearing execution.",
            "Classification: `NoCandidate`.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_artifact(root: Path, diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    diagnosis_path = root / "diagnosis.json"
    report_path = root / "diagnosis.md"
    diagnosis_path.write_text(json.dumps(diagnosis, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(markdown_report(diagnosis), encoding="utf-8")
    body = {
        "state_slice": STATE_SLICE,
        "diagnosis_sha256": diagnosis["diagnosis_sha256"],
        "files": [
            {"path": path.name, "byte_len": path.stat().st_size, "sha256": _sha256_file(path)}
            for path in (diagnosis_path, report_path)
        ],
    }
    manifest = {**body, "manifest_sha256": _digest(body)}
    (root / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    diagnosis = diagnose(args.result)
    manifest = write_artifact(args.output, diagnosis)
    print(json.dumps({"output": str(args.output), "diagnosis_sha256": diagnosis["diagnosis_sha256"], "manifest_sha256": manifest["manifest_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
