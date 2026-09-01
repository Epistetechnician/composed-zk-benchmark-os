#!/usr/bin/env python3
"""Bounded autoresearch driver for the information-frontier slice.

State slice: ``continual-learning-information-budget-frontier-v1``.

The driver evaluates only preregistered synthetic candidates on fit and tune,
keeps the best guarded candidate, seals a prediction lock, and then evaluates
that locked candidate once on assessment.  It never changes model weights,
uses external models or corpora, or calls a provider.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import information_budget_frontier_v1 as experiment
from experiments.continual_learning import validate_information_budget_frontier_v1 as validator


STATE_SLICE = experiment.STATE_SLICE
MAX_ITERATIONS = len(experiment.PREDECLARED_CANDIDATES)
CUSTODY_RUN_ROOT = experiment.CUSTODY_RUN_ROOT


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _metric(result: dict[str, Any], split: str, arm: str) -> float:
    return float(result["summary"]["by_split_arm"][f"{split}:{arm}"][experiment.PRIMARY_ENDPOINT])


def _guard(result: dict[str, Any], split: str, arm: str) -> bool:
    return bool(result["summary"]["by_split_arm"][f"{split}:{arm}"]["all_hard_guards_pass"])


def _candidate_guards(result: dict[str, Any]) -> tuple[bool, bool, bool]:
    fit_guard = _guard(result, "fit", "cpsp_frontier")
    tune_guard = _guard(result, "tune", "cpsp_frontier")
    return fit_guard, tune_guard, fit_guard and tune_guard


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_search(output_dir: Path, review_receipt: Path, max_iterations: int = MAX_ITERATIONS) -> dict[str, Any]:
    if not 1 <= max_iterations <= MAX_ITERATIONS:
        raise ValueError(f"max_iterations must be in [1, {MAX_ITERATIONS}]")
    if output_dir.resolve() != CUSTODY_RUN_ROOT:
        raise ValueError(f"output must be the declared custody root: {CUSTODY_RUN_ROOT}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"custody root is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    candidate_dir = output_dir / "candidates"
    results_path = output_dir / "results.tsv"
    results_path.write_text(
        "iteration\tcandidate\ttune_metric\ttune_untouched\tstatus\tfit_guard\ttune_guard\tguard\tartifact_digest\n",
        encoding="utf-8",
    )

    best_name: str | None = None
    best_metric = float("-inf")
    best_artifact_path: Path | None = None
    iteration_rows: list[dict[str, Any]] = []
    for iteration, raw_candidate in enumerate(experiment.PREDECLARED_CANDIDATES[:max_iterations]):
        config = experiment.candidate_config(raw_candidate["name"])
        result = experiment.run_campaign(config, ("fit", "tune"))
        experiment.validate_result(result)
        validator.validate_result(json.loads(json.dumps(result)))
        candidate_path = candidate_dir / f"{iteration:02d}-{config.name}.json"
        _write_json(candidate_path, result)
        tune_metric = _metric(result, "tune", "cpsp_frontier")
        tune_untouched = _metric(result, "tune", "untouched")
        fit_guard, tune_guard, guard = _candidate_guards(result)
        keep = guard and tune_metric > best_metric
        if keep:
            best_name = config.name
            best_metric = tune_metric
            best_artifact_path = candidate_path
        status = "keep" if keep else "discard"
        row = {
            "iteration": iteration,
            "candidate": config.name,
            "tune_metric": tune_metric,
            "tune_untouched": tune_untouched,
            "status": status,
            "fit_guard": fit_guard,
            "tune_guard": tune_guard,
            "guard": guard,
            "artifact_digest": _digest(candidate_path),
        }
        iteration_rows.append(row)
        with results_path.open("a", encoding="utf-8") as handle:
            handle.write(
                "\t".join(
                    str(row[field])
                    for field in ("iteration", "candidate", "tune_metric", "tune_untouched", "status", "fit_guard", "tune_guard", "guard", "artifact_digest")
                )
                + "\n"
            )
        if not guard:
            break

    if best_name is None or best_artifact_path is None:
        raise RuntimeError("no guarded candidate survived fit/tune")
    locked = experiment.candidate_config(best_name)
    review_digest = experiment._validate_review_receipt(review_receipt)
    lock_payload = {
        "state_slice": STATE_SLICE,
        "lock_type": "fit_tune_prediction_lock",
        "candidate": {
            "name": locked.name,
            "alpha_grid_name": locked.alpha_grid_name,
            "alpha_grid": list(locked.alpha_grid),
            "learning_rate": locked.learning_rate,
        },
        "selection_metric": experiment.PRIMARY_ENDPOINT,
        "selection_split": "tune",
        "selected_value": best_metric,
        "candidate_order": [item["name"] for item in experiment.PREDECLARED_CANDIDATES[:max_iterations]],
        "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
        "review_packet_sha256": hashlib.sha256(experiment.REVIEW_PACKET_PATH.read_bytes()).hexdigest(),
        "review_receipt_path": str(review_receipt.resolve()),
        "review_receipt_sha256": review_digest,
        "fit_tune_result_path": str(best_artifact_path.resolve()),
        "fit_tune_result_sha256": _digest(best_artifact_path),
    }
    lock_path = output_dir / "prediction_lock.json"
    _write_json(lock_path, lock_payload)

    assessment = experiment.run_campaign(
        locked,
        ("assessment",),
        review_receipt=review_receipt,
        prediction_lock=lock_path,
    )
    experiment.validate_result(assessment)
    validator.validate_result(json.loads(json.dumps(assessment)))
    assessment_path = output_dir / "assessment.json"
    _write_json(assessment_path, assessment)
    candidate_assessment = _metric(assessment, "assessment", "cpsp_frontier")
    untouched_assessment = _metric(assessment, "assessment", "untouched")
    fixed_assessment = _metric(assessment, "assessment", "fixed_adapter")
    assessment_guard = _guard(assessment, "assessment", "cpsp_frontier")
    status = "Candidate" if assessment_guard and candidate_assessment > untouched_assessment and candidate_assessment > fixed_assessment else "NoCandidate"
    summary = {
        "state_slice": STATE_SLICE,
        "status": status,
        "selection": {
            "candidate": best_name,
            "tune_metric": best_metric,
            "prediction_lock_digest": _digest(lock_path),
        },
        "assessment": {
            "frontier_utility": candidate_assessment,
            "untouched_utility": untouched_assessment,
            "fixed_utility": fixed_assessment,
            "frontier_guard_pass": assessment_guard,
            "beats_untouched": candidate_assessment > untouched_assessment,
            "beats_fixed": candidate_assessment > fixed_assessment,
        },
        "iterations": iteration_rows,
        "claim_ceiling": "LocalDevelopmentInformationBudgetFrontierSyntheticOnly",
        "model_loaded": False,
        "provider_called": False,
        "astral_integration": "not_run",
        "zk_pqc": "not_run",
    }
    summary_path = output_dir / "summary.json"
    _write_json(summary_path, summary)
    (output_dir / "summary.md").write_text(
        "# Information-budget frontier autoresearch summary\n\n"
        f"State slice: `{STATE_SLICE}`.\n\n"
        f"Status: `{status}`.\n\n"
        f"Locked candidate: `{best_name}`.\n\n"
        f"Assessment AFFU: `{candidate_assessment:.12f}`; untouched: `{untouched_assessment:.12f}`; fixed: `{fixed_assessment:.12f}`.\n\n"
        "This is exact-synthetic controller evidence only. It does not authorize model-bearing execution, GiveMeANode, Astral integration, ZK/PQC custody proof, or production claims.\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-receipt", type=Path, required=True)
    parser.add_argument("--max-iterations", type=int, default=MAX_ITERATIONS)
    args = parser.parse_args()
    print(json.dumps(run_search(args.output, args.review_receipt, args.max_iterations), sort_keys=True))


if __name__ == "__main__":
    main()
