"""Run Stage 0 into a caller-selected empty directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

from artifact_validator import DECLARED_FILES, validate_bundle
from stage0 import (
    BOOTSTRAP_DRAWS,
    COMPONENTS,
    DEAD_ZONE,
    FAMILY_COUNT,
    METHODS,
    PRACTICAL_MARGIN,
    SEEDS,
    STATE_SLICE,
    PlantedTwoHeadActor,
    canonical_json_bytes,
    family_bootstrap_interval,
    generate_examples,
    matched_donor,
    method_predictions,
    selected_component,
    selection_regret,
)


def _write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise ValueError(f"refusing to overwrite {path}")
    path.write_bytes(data)


def _repo_state(repo: Path) -> dict[str, object]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return {"commit": commit, "dirty": bool(status), "dirty_paths": sorted(status)}


def run(output: Path, repo: Path) -> dict[str, object]:
    started = time.monotonic()
    if output.exists():
        if output.is_symlink() or not output.is_dir() or any(output.iterdir()):
            raise ValueError("output must be a real empty directory")
    else:
        output.mkdir(parents=True)
    examples = generate_examples()
    records: list[dict[str, object]] = []
    regrets: dict[str, list[float]] = {method: [] for method in METHODS}
    family_differences: dict[int, list[float]] = {}
    per_seed: dict[int, dict[str, list[float]]] = {
        seed: {method: [] for method in METHODS} for seed in SEEDS
    }
    patch_direction_ok = True
    for example in examples:
        actor = PlantedTwoHeadActor(example.seed)
        base = actor.forward(example)
        if base.label != example.expected_label:
            raise AssertionError("frozen actor task failure")
        if example.split != "evaluation":
            continue
        donor = matched_donor(example, examples)
        measured = {
            component: actor.ablation_effect(example, component)
            for component in COMPONENTS
        }
        patch = {
            component: actor.patch_effect(example, donor, component)
            for component in COMPONENTS
        }
        predictions = method_predictions(actor, example)
        tracer_top = selected_component(predictions["candidate_tracer"])
        patch_top = max(
            COMPONENTS, key=lambda component: (abs(patch[component]), component)
        )
        patch_direction_ok &= tracer_top == patch_top
        row_regrets = {
            method: selection_regret(measured, predictions[method])
            for method in METHODS
        }
        for method, value in row_regrets.items():
            regrets[method].append(value)
            per_seed[example.seed][method].append(value)
        difference = (
            row_regrets["activation_magnitude"]
            - row_regrets["candidate_tracer"]
        )
        family_differences.setdefault(example.family, []).append(difference)
        records.append(
            {
                "record_id": example.example_id,
                "ablation_effects": measured,
                "base_label": base.label,
                "base_logits": list(base.logits),
                "distractor": example.distractor,
                "donor_example_id": donor.example_id,
                "expected_label": example.expected_label,
                "family": example.family,
                "hooks": base.hooks,
                "patch_effects": patch,
                "predictions": predictions,
                "regrets": row_regrets,
                "seed": example.seed,
                "signal": example.signal,
                "split": example.split,
            }
        )
    records.sort(key=lambda row: str(row["record_id"]))
    family_means = {
        family: sum(values) / len(values)
        for family, values in family_differences.items()
    }
    interval = family_bootstrap_interval(family_means)
    per_method = {
        method: {
            "mean_selection_regret": sum(values) / len(values),
            "n": len(values),
        }
        for method, values in regrets.items()
    }
    baseline_method = "activation_magnitude"
    improvement = (
        per_method[baseline_method]["mean_selection_regret"]
        - per_method["candidate_tracer"]["mean_selection_regret"]
    )
    each_seed_favorable = all(
        sum(per_seed[seed][baseline_method])
        / len(per_seed[seed][baseline_method])
        > sum(per_seed[seed]["candidate_tracer"])
        / len(per_seed[seed]["candidate_tracer"])
        for seed in SEEDS
    )
    positive_control_pass = (
        improvement > PRACTICAL_MARGIN
        and interval[0] > PRACTICAL_MARGIN
        and each_seed_favorable
        and patch_direction_ok
    )
    config = {
        "schema": "astral.stage0.config.v1",
        "actor_id": PlantedTwoHeadActor.actor_id,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "candidate_components": list(COMPONENTS),
        "dead_zone": DEAD_ZONE,
        "development_family_rule": "family_mod_4_equals_0",
        "evaluation_family_rule": "family_mod_4_not_0",
        "family_count": FAMILY_COUNT,
        "methods": list(METHODS),
        "network_allowed": False,
        "practical_margin": PRACTICAL_MARGIN,
        "seeds": list(SEEDS),
        "state_slice": STATE_SLICE,
        "training_allowed": False,
    }
    boundary = {
        "accepted_evidence": False,
        "level": "local_measurement_regression",
        "mechanistic_understanding": False,
        "self_modeling": False,
    }
    summary = {
        "schema": "astral.stage0.summary.v1",
        "baseline_method": baseline_method,
        "bootstrap_interval_95": list(interval),
        "census": {
            "evaluation_families": len(family_means),
            "records": len(records),
            "seeds": len(SEEDS),
        },
        "claim_boundary": boundary,
        "each_seed_favorable": each_seed_favorable,
        "gate": "positive_control_pass" if positive_control_pass else "positive_control_fail",
        "mean_baseline_minus_tracer_regret": improvement,
        "patch_direction_confirmed": patch_direction_ok,
        "thresholds_registered_for_scientific_exit": False,
        "per_method": per_method,
        "runtime_seconds": time.monotonic() - started,
        "stopping_reason": "complete",
    }
    _write_new(output / "config.json", canonical_json_bytes(config))
    _write_new(
        output / "records.jsonl",
        b"".join(canonical_json_bytes(row) for row in records),
    )
    _write_new(output / "summary.json", canonical_json_bytes(summary))
    files = []
    for name in DECLARED_FILES:
        raw = (output / name).read_bytes()
        files.append(
            {
                "bytes": len(raw),
                "path": name,
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    manifest = {
        "schema": "astral.stage0.manifest.v1",
        "claim_boundary": boundary,
        "files": files,
        "repo": _repo_state(repo),
        "runtime": {"platform": platform.platform(), "python": sys.version.split()[0]},
        "state_slice": STATE_SLICE,
    }
    _write_new(output / "manifest.json", canonical_json_bytes(manifest))
    return validate_bundle(output) | {"summary": summary}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.output.resolve(), args.repo.resolve())
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
