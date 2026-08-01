"""Qualify training and run the untouched Stage 0 V2 holdout once."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

import torch

HERE = Path(__file__).resolve().parent
V1_ROOT = HERE.parents[0] / "astral-stage0-learned"
sys.path.insert(0, str(V1_ROOT))
from learned_stage0 import (  # noqa: E402
    COMPETITIVE, METHODS, canonical_json, examples_for, intervention_effects,
    normalized_regret, score_example, selected,
)
from learned_stage0_v2 import (  # noqa: E402
    CONFIRMATORY_SEEDS, QUALIFICATION_SEEDS, STATE_SLICE, qualify_seed,
)
from learned_validator_v2 import validate  # noqa: E402


def _write(path: Path, value: object, jsonl: bool = False) -> None:
    if path.exists():
        raise ValueError("refusing overwrite")
    data = (
        b"".join(canonical_json(row) for row in value)
        if jsonl else canonical_json(value)
    )
    path.write_bytes(data)


def _bootstrap(by_seed_family: dict[int, dict[int, float]]) -> list[float]:
    rng = random.Random(20260727)
    seeds = sorted(by_seed_family)
    estimates = []
    for _ in range(2_000):
        sampled_seeds = [seeds[rng.randrange(3)] for _ in seeds]
        seed_means = []
        for seed in sampled_seeds:
            families = sorted(by_seed_family[seed])
            sample = [families[rng.randrange(64)] for _ in families]
            seed_means.append(
                sum(by_seed_family[seed][family] for family in sample) / 64
            )
        estimates.append(sum(seed_means) / 3)
    estimates.sort()
    return [estimates[49], estimates[1949]]


def run(output: Path, repo: Path, protocol: Path) -> dict[str, object]:
    started = time.monotonic()
    if torch.__version__ != "2.12.0":
        raise RuntimeError("torch version drift")
    if output.resolve().is_relative_to(repo.resolve()):
        raise ValueError("output must be repository-external")
    if output.exists():
        if output.is_symlink() or not output.is_dir() or any(output.iterdir()):
            raise ValueError("output must be a real empty directory")
    else:
        output.mkdir(parents=True)
    protocol_digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    _write(output / "protocol.lock.json", {
        "protocol_sha256": protocol_digest,
        "reviewer": "independent-v2-scientific-audit",
        "schema": "astral.learned-stage0-v2.protocol-lock.v1",
        "state_slice": STATE_SLICE,
    })
    qualification = {}
    for seed in QUALIFICATION_SEEDS:
        _, result = qualify_seed(seed)
        qualification[str(seed)] = result
    qualification_pass = all(row["eligible"] for row in qualification.values())
    _write(output / "qualification.json", {
        "evaluation_materialized": False,
        "passed": qualification_pass,
        "schema": "astral.learned-stage0-v2.qualification.v1",
        "seeds": qualification,
    })
    if not qualification_pass:
        return _finalize_early(
            output, repo, protocol_digest, "QualificationFailed", started
        )
    models = {}
    confirmatory = {}
    for seed in CONFIRMATORY_SEEDS:
        model, result = qualify_seed(seed)
        models[seed] = model
        confirmatory[str(seed)] = result
        torch.save(model.state_dict(), output / f"checkpoint-{seed}.pt")
    confirmatory_pass = all(row["eligible"] for row in confirmatory.values())
    _write(output / "confirmatory-training.json", {
        "passed": confirmatory_pass,
        "schema": "astral.learned-stage0-v2.confirmatory-training.v1",
        "seeds": confirmatory,
    })
    _write(output / "qualification.lock.json", {
        "confirmatory_passed": confirmatory_pass,
        "evaluation_families": [320, 383],
        "protocol_sha256": protocol_digest,
        "qualification_sha256": hashlib.sha256(
            (output / "qualification.json").read_bytes()
        ).hexdigest(),
        "schema": "astral.learned-stage0-v2.qualification-lock.v1",
    })
    if not confirmatory_pass:
        return _finalize_early(
            output, repo, protocol_digest, "Inconclusive", started
        )
    eval_rows = examples_for(range(320, 384))
    score_rows = []
    for seed, model in models.items():
        for example in eval_rows:
            scores, clean_margin, capture = score_example(model, example)
            score_rows.append({
                "capture": capture,
                "clean_margin": clean_margin,
                "example_id": example.example_id,
                "scores": scores,
                "seed": seed,
            })
    _write(output / "scores.jsonl", score_rows, jsonl=True)
    score_digest = hashlib.sha256((output / "scores.jsonl").read_bytes()).hexdigest()
    _write(output / "score-phase.lock.json", {
        "record_census": len(score_rows),
        "schema": "astral.learned-stage0-v2.score-lock.v1",
        "scores_sha256": score_digest,
    })
    records = []
    lookup = {(row["seed"], row["example_id"]): row for row in score_rows}
    for seed, model in models.items():
        for example in eval_rows:
            score_row = lookup[(seed, example.example_id)]
            effects, patches = intervention_effects(model, example)
            regrets = {}
            selections = {}
            informative = False
            for method in METHODS:
                regrets[method], informative = normalized_regret(
                    effects, score_row["scores"][method]
                )
                selections[method] = selected(score_row["scores"][method])
            records.append({
                "ablation_effects": effects,
                "clean_margin": score_row["clean_margin"],
                "example_id": example.example_id,
                "family": example.family,
                "informative": informative,
                "patch_effects": patches,
                "record_id": f"s{seed}-{example.example_id}",
                "regrets": regrets,
                "score_phase_sha256": score_digest,
                "scores": score_row["scores"],
                "seed": seed,
                "selections": selections,
                "split": "evaluation_v2",
            })
    records.sort(key=lambda row: row["record_id"])
    _write(output / "records.jsonl", records, jsonl=True)
    summary = _summarize(records, confirmatory, protocol_digest, started)
    _write(output / "summary.json", summary)
    return _manifest(output, repo, summary)


def _summarize(records, training, protocol_digest, started):
    method_regret = {
        method: sum(row["regrets"][method] for row in records) / len(records)
        for method in METHODS
    }
    comparisons = {}
    for baseline in (*COMPETITIVE, "permuted_candidate"):
        values = {}
        for seed in CONFIRMATORY_SEEDS:
            values[seed] = {}
            for family in range(320, 384):
                rows = [
                    row for row in records
                    if row["seed"] == seed and row["family"] == family
                ]
                values[seed][family] = sum(
                    row["regrets"][baseline]
                    - row["regrets"]["candidate_grad_x_activation"]
                    for row in rows
                ) / 16
        per_seed = {
            str(seed): sum(values[seed].values()) / 64
            for seed in CONFIRMATORY_SEEDS
        }
        comparisons[baseline] = {
            "interval_95": _bootstrap(values),
            "mean": sum(per_seed.values()) / 3,
            "per_seed": per_seed,
        }
    coverage = {
        str(seed): sum(
            row["informative"] for row in records if row["seed"] == seed
        ) / 1024 for seed in CONFIRMATORY_SEEDS
    }
    primary = all(
        comparisons[b]["mean"] > 0.05
        and comparisons[b]["interval_95"][0] > 0.05
        and all(value > 0 for value in comparisons[b]["per_seed"].values())
        for b in COMPETITIVE
    )
    placebo = (
        comparisons["permuted_candidate"]["mean"] > 0
        and comparisons["permuted_candidate"]["interval_95"][0] > 0
    )
    patch_by_seed = {
        baseline: {
            str(seed): sum(
                abs(row["patch_effects"][
                    row["selections"]["candidate_grad_x_activation"]
                ])
                - abs(row["patch_effects"][row["selections"][baseline]])
                for row in records if row["seed"] == seed
            ) / 1024
            for seed in CONFIRMATORY_SEEDS
        }
        for baseline in COMPETITIVE
    }
    patch = all(
        all(value > 0 for value in rows.values())
        for rows in patch_by_seed.values()
    )
    verdict = (
        "Pass" if primary and placebo and patch
        and all(value >= 0.80 for value in coverage.values())
        else "Null"
    )
    return {
        "schema": "astral.learned-stage0-v2.summary.v1",
        "claim_boundary": {
            "accepted_evidence": False,
            "level": "local_learned_model_measurement_candidate",
            "mechanistic_understanding": False,
            "self_modeling": False,
        },
        "comparisons": comparisons,
        "informative_coverage": coverage,
        "method_regret": method_regret,
        "patch_by_seed": patch_by_seed,
        "patch_gate": patch,
        "placebo_gate": placebo,
        "primary_gate": primary,
        "protocol_sha256": protocol_digest,
        "record_census": len(records),
        "runtime_seconds": time.monotonic() - started,
        "training": training,
        "verdict": verdict,
    }


def _finalize_early(output, repo, protocol_digest, verdict, started):
    summary = {
        "schema": "astral.learned-stage0-v2.summary.v1",
        "claim_boundary": {
            "accepted_evidence": False,
            "level": "local_learned_model_measurement_candidate",
            "mechanistic_understanding": False,
            "self_modeling": False,
        },
        "protocol_sha256": protocol_digest,
        "runtime_seconds": time.monotonic() - started,
        "verdict": verdict,
    }
    _write(output / "summary.json", summary)
    return _manifest(output, repo, summary)


def _manifest(output, repo, summary):
    files = []
    for path in sorted(output.iterdir()):
        raw = path.read_bytes()
        files.append({
            "bytes": len(raw), "path": path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    if sum(row["bytes"] for row in files) > 256 * 1024 * 1024:
        raise RuntimeError("artifact cap exceeded")
    manifest = {
        "schema": "astral.learned-stage0-v2.manifest.v1",
        "claim_boundary": summary["claim_boundary"],
        "files": files,
        "repo_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
        "state_slice": STATE_SLICE,
    }
    _write(output / "manifest.json", manifest)
    validation = validate(output)
    return {
        "manifest_sha256": hashlib.sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        "summary": summary,
        "validation": validation,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(
        args.output.resolve(), args.repo.resolve(), args.protocol.resolve()
    ), sort_keys=True))


if __name__ == "__main__":
    main()
