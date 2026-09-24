"""Run the bounded Jevlike FSM-localization experiment.

State slice: jevlike-variable-option-scoring-v1.

This module orchestrates a pinned external Jevlike checkout. It does not vendor
the upstream package, execute a host model, mutate the Evidence Ledger, or
retain experiment rows in the repository. The input rows are derived from the
existing synthetic Astral FSM archives and are written to a caller-owned
external output root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


STATE_SLICE = "jevlike-variable-option-scoring-v1"
PROTOCOL_ID = "jevlike-variable-option-scoring-v1"
UPSTREAM_REVISION = "94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452"
RUN_GROUPS = {
    "fit": (
        "2026-08-07",
        "2026-08-10-easy-v1",
        "2026-08-10-micro-v1",
        "2026-08-10-short-v1",
    ),
    "tune": (
        "2026-08-10-intermediate-v1",
        "2026-08-10-micro-replication-v1",
    ),
    "test": ("2026-08-10-micro-localize-v2",),
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected object rows in {path}")
            rows.append(value)
    return rows


def _compact_mapping(mapping: dict[str, Any]) -> str:
    return ",".join(
        f"{state}:{','.join(f'{symbol}->{target}' for symbol, target in sorted(edges.items()))}"
        for state, edges in sorted(mapping.items())
    )


def _context(case: dict[str, Any], evaluated: dict[str, Any]) -> str:
    observed = evaluated.get("parsed_response")
    if not isinstance(observed, dict):
        observed = {}
    states = ",".join(str(item) for item in case["states"])
    alphabet = ",".join(str(item) for item in case["alphabet"])
    accepting = ",".join(str(item) for item in case["accepting"])
    transitions = _compact_mapping(case["transitions"])
    trajectory = ",".join(str(item) for item in observed.get("trajectory", ()))
    return (
        f"FSM states={states}; alphabet={alphabet}; start={case['start']}; "
        f"accepting={accepting}; transitions={transitions}; input={case['input']}; "
        f"observed_trajectory={trajectory}; observed_final={observed.get('final_state')}; "
        f"observed_accepted={observed.get('accepted')}"
    )


def _example(case: dict[str, Any], evaluated: dict[str, Any], source_run: str) -> dict[str, Any]:
    input_length = int(evaluated["input_length"])
    divergence = evaluated.get("first_divergence_index")
    if divergence is None:
        label = 0
    else:
        label = int(divergence)
        if not 1 <= label <= input_length:
            raise ValueError(f"invalid divergence index {divergence} for {source_run}")
    options = ["no_divergence", *[f"step_{index}" for index in range(1, input_length + 1)]]
    return {
        "context": _context(case, evaluated),
        "options": options,
        "label": label,
        "example_id": f"{source_run}:{case['case_id']}",
        "source_run": source_run,
    }


def build_examples(repo_root: Path, *, seen_case_ids: set[int] | None = None) -> dict[str, list[dict[str, Any]]]:
    """Build split rows from archived actor observations and hidden oracle labels."""

    seen = seen_case_ids if seen_case_ids is not None else set()
    splits: dict[str, list[dict[str, Any]]] = {name: [] for name in RUN_GROUPS}
    run_to_split = {run: split for split, runs in RUN_GROUPS.items() for run in runs}
    for source_run, split in run_to_split.items():
        run_root = repo_root / "experiments" / "astral_fsm" / "runs" / source_run
        evaluated_rows = _read_jsonl(run_root / "evaluated" / "evaluated.jsonl")
        cases = {
            int(case["case_id"]): case
            for case in json.loads((run_root / "cases_manifest.json").read_text(encoding="utf-8"))
        }
        for evaluated in evaluated_rows:
            case_id = int(evaluated["case_id"])
            if case_id in seen:
                continue
            case = cases[case_id]
            splits[split].append(_example(case, evaluated, source_run))
            seen.add(case_id)
    if any(not rows for rows in splits.values()):
        raise ValueError(f"empty experiment split: { {key: len(value) for key, value in splits.items()} }")
    return splits


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_bytes(row).decode("utf-8"))
            handle.write("\n")


def _permuted(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        order = list(range(len(row["options"])))
        order.sort(key=lambda index: digest({"example_id": row["example_id"], "index": index}))
        inverse = {old: new for new, old in enumerate(order)}
        result.append(
            {
                **row,
                "options": [row["options"][index] for index in order],
                "label": inverse[row["label"]],
            }
        )
    return result


def _baseline(rows: list[dict[str, Any]]) -> dict[str, float]:
    labels = [int(row["label"]) for row in rows]
    majority = Counter(labels).most_common(1)[0][0]
    no_divergence = sum(label == 0 for label in labels) / len(labels)
    first_step = sum(label == 1 for label in labels) / len(labels)
    random_top1 = sum(1.0 / len(row["options"]) for row in rows) / len(rows)
    random_top3 = sum(min(3, len(row["options"])) / len(row["options"]) for row in rows) / len(rows)
    majority_accuracy = sum(label == majority for label in labels) / len(labels)
    return {
        "majority_label_accuracy": majority_accuracy,
        "always_no_divergence_accuracy": no_divergence,
        "always_step_1_accuracy": first_step,
        "uniform_random_expected_top1": random_top1,
        "uniform_random_expected_top3": random_top3,
        "majority_label": float(majority),
    }


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _run_json(command: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    output = _run(command, cwd=cwd, env=env)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"upstream command did not return JSON: {output}") from exc


def _paired_test_comparison(model_path: Path, data_path: Path, upstream_root: Path) -> dict[str, Any]:
    """Compare model top-1 with the strongest simple held-out baseline."""

    sys.path.insert(0, str(upstream_root))
    import torch
    from torch.utils.data import DataLoader

    from jevlike.data import JsonlDataset
    from jevlike.model import load_checkpoint

    model, collator, _ = load_checkpoint(model_path, torch.device("cpu"))
    model.eval()
    outcomes: list[tuple[int, int]] = []
    with torch.no_grad():
        loader = DataLoader(JsonlDataset(data_path), batch_size=64, collate_fn=collator)
        for batch in loader:
            logits = model({name: tensor for name, tensor in batch.items()})
            outcomes.extend(zip(logits.argmax(-1).tolist(), batch["labels"].tolist()))
    model_correct = sum(prediction == label for prediction, label in outcomes)
    baseline_correct = sum(label == 0 for _, label in outcomes)
    model_only = sum(prediction == label and label != 0 for prediction, label in outcomes)
    baseline_only = sum(prediction != label and label == 0 for prediction, label in outcomes)
    discordant = model_only + baseline_only
    if discordant:
        lower_tail = sum(math.comb(discordant, k) for k in range(min(model_only, baseline_only) + 1))
        p_value = min(1.0, 2.0 * lower_tail / (2**discordant))
    else:
        p_value = 1.0
    return {
        "n": len(outcomes),
        "model_correct": model_correct,
        "always_no_divergence_correct": baseline_correct,
        "model_only": model_only,
        "baseline_only": baseline_only,
        "discordant": discordant,
        "mcnemar_two_sided_p": p_value,
    }


def run_experiment(*, repo_root: Path, upstream_root: Path, output_root: Path) -> dict[str, Any]:
    if not (upstream_root / ".git").exists():
        raise ValueError(f"upstream checkout is missing: {upstream_root}")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=upstream_root, check=True, capture_output=True, text=True
    ).stdout.strip()
    if revision != UPSTREAM_REVISION:
        raise ValueError(f"unexpected Jevlike revision: {revision}")

    output_root.mkdir(parents=True, exist_ok=True)
    splits = build_examples(repo_root)
    for split, rows in splits.items():
        write_jsonl(output_root / f"{split}.jsonl", rows)
    permuted_test = _permuted(splits["test"])
    write_jsonl(output_root / "test-permuted.jsonl", permuted_test)

    model_path = output_root / "tiny-fsm-localization.pt"
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(upstream_root) + (os.pathsep + current_pythonpath if current_pythonpath else "")
    train_command = [
        sys.executable,
        "-m",
        "jevlike.train",
        str(output_root / "fit.jsonl"),
        "--validation",
        str(output_root / "tune.jsonl"),
        "--output",
        str(model_path),
        "--encoder",
        "tiny",
        "--context-tokens",
        "512",
        "--option-tokens",
        "32",
        "--epochs",
        "20",
        "--batch-size",
        "32",
        "--learning-rate",
        "0.002",
        "--seed",
        "7",
        "--device",
        "cpu",
    ]
    train_output = _run(train_command, cwd=upstream_root, env=env)
    (output_root / "train.stdout.jsonl").write_text(train_output, encoding="utf-8")

    def evaluate(data_path: Path) -> dict[str, Any]:
        return _run_json(
            [
                sys.executable,
                "-m",
                "jevlike.eval",
                str(model_path),
                str(data_path),
                "--batch-size",
                "64",
                "--device",
                "cpu",
            ],
            cwd=upstream_root,
            env=env,
        )

    evaluations = {
        split: evaluate(output_root / f"{split}.jsonl") for split in ("fit", "tune", "test")
    }
    evaluations["test_permuted_options"] = evaluate(output_root / "test-permuted.jsonl")
    paired_test = _paired_test_comparison(
        model_path, output_root / "test.jsonl", upstream_root
    )
    test_baselines = _baseline(splits["test"])
    strongest_baseline_name, strongest_baseline = max(
        (
            (name, value)
            for name, value in test_baselines.items()
            if name.endswith("_accuracy")
        ),
        key=lambda item: item[1],
    )
    report = {
        "schema_version": "jevlike-variable-option-scoring-report-v1",
        "state_slice": STATE_SLICE,
        "protocol_identity": PROTOCOL_ID,
        "status": "bounded_external_execution_complete",
        "claim_ceiling": "LocalDevelopmentVariableOptionScoringFeasibilityOnly",
        "upstream_revision": revision,
        "source_archives": sorted({row["source_run"] for rows in splits.values() for row in rows}),
        "source_archive_digest": digest(
            [row for split in ("fit", "tune", "test") for row in splits[split]]
        ),
        "split_counts": {split: len(rows) for split, rows in splits.items()},
        "option_count_range": {
            split: [min(len(row["options"]) for row in rows), max(len(row["options"]) for row in rows)]
            for split, rows in splits.items()
        },
        "label_counts": {split: dict(sorted(Counter(row["label"] for row in rows).items())) for split, rows in splits.items()},
        "baselines": {split: _baseline(rows) for split, rows in splits.items()},
        "jevlike_evaluations": evaluations,
        "paired_test_comparison": paired_test,
        "strongest_test_baseline": {
            "name": strongest_baseline_name,
            "top1": strongest_baseline,
        },
        "controls": {
            "shuffled_context": evaluations["test"]["shuffled_context"],
            "option_permutation": evaluations["test_permuted_options"]["model"],
        },
        "execution_policy": {
            "device": "cpu",
            "pretrained_encoder": False,
            "network_during_execution": False,
            "host_model_execution": False,
            "raw_rows_retained_in_repository": False,
            "evidence_ledger_mutated": False,
        },
    }
    (output_root / "aggregate-report.json").write_bytes(canonical_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = run_experiment(
        repo_root=args.repo_root,
        upstream_root=args.upstream_root,
        output_root=args.output_root,
    )
    test_metrics = report["jevlike_evaluations"]["test"]["model"]
    baseline = report["baselines"]["test"]
    print(
        json.dumps(
            {
                "status": report["status"],
                "test_top1": test_metrics["top1"],
                "test_top3": test_metrics["top3"],
                "test_ece": test_metrics["ece"],
                "test_shuffled_context_top1": report["controls"]["shuffled_context"]["top1"],
                "test_permuted_options_top1": report["controls"]["option_permutation"]["top1"],
                "test_random_expected_top1": baseline["uniform_random_expected_top1"],
                "report": str(args.output_root / "aggregate-report.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
