"""Run the one-attempt learned-transformer Stage 0 study."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

from learned_stage0 import (
    COMPETITIVE, METHODS, SEEDS, STATE_SLICE, canonical_json,
    checkpoint_digest, configure_runtime, examples_for, intervention_effects,
    normalized_regret, score_example, selected, train_actor,
)
from learned_validator import validate


def _interval(values: list[float]) -> list[float]:
    ordered = sorted(values)
    return [
        ordered[int(0.025 * (len(ordered) - 1))],
        ordered[int(0.975 * (len(ordered) - 1))],
    ]


def _bootstrap(by_seed_family: dict[int, dict[int, float]]) -> list[float]:
    rng = random.Random(20260727)
    seeds = sorted(by_seed_family)
    estimates = []
    for _ in range(2_000):
        seed_sample = [seeds[rng.randrange(len(seeds))] for _ in seeds]
        seed_means = []
        for seed in seed_sample:
            families = sorted(by_seed_family[seed])
            family_sample = [
                families[rng.randrange(len(families))] for _ in families
            ]
            seed_means.append(
                sum(by_seed_family[seed][family] for family in family_sample)
                / len(family_sample)
            )
        estimates.append(sum(seed_means) / len(seed_means))
    return _interval(estimates)


def _write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise ValueError("refusing to overwrite output")
    path.write_bytes(data)


def run(output: Path, repo: Path, protocol: Path) -> dict[str, object]:
    configure_runtime()
    import torch
    if torch.__version__ != "2.12.0":
        raise RuntimeError("frozen torch version mismatch")
    started = time.monotonic()
    if output.resolve().is_relative_to(repo.resolve()):
        raise ValueError("output must be repository-external")
    if output.exists():
        if output.is_symlink() or not output.is_dir() or any(output.iterdir()):
            raise ValueError("output must be a real empty directory")
    else:
        output.mkdir(parents=True)
    protocol_raw = protocol.read_bytes()
    protocol_digest = hashlib.sha256(protocol_raw).hexdigest()
    _write_new(
        output / "protocol.lock.json",
        canonical_json({
            "disposition": "approved_after_blocker_corrections",
            "protocol_path": "docs/research/astral-self-modeling/09-learned-transformer-stage0-preregistration.md",
            "protocol_sha256": protocol_digest,
            "reviewer": "independent-agent-pre-evaluation-review",
            "schema": "astral.learned-stage0.protocol-lock.v1",
        }),
    )
    eval_rows = examples_for(range(256, 320))
    records: list[dict[str, object]] = []
    checkpoints: dict[str, str] = {}
    training_by_seed: dict[str, dict[str, float]] = {}
    for seed in SEEDS:
        model, training = train_actor(seed)
        training_by_seed[str(seed)] = training
        digest = checkpoint_digest(model)
        torch.save(model.state_dict(), output / f"checkpoint-{seed}.pt")
        checkpoints[str(seed)] = digest
        if min(training.values()) < 0.95:
            continue
        # Phase 1: freeze all scores before the intervention oracle is called.
        score_rows = []
        for example in eval_rows:
            scores, clean_margin, capture = score_example(model, example)
            score_rows.append((example, scores, clean_margin, capture))
        score_digest = hashlib.sha256(
            b"".join(
                canonical_json(
                    {"example_id": row.example_id, "scores": scores, "seed": seed}
                )
                for row, scores, _, _ in score_rows
            )
        ).hexdigest()
        _write_new(
            output / f"scores-{seed}.jsonl",
            b"".join(
                canonical_json({
                    "capture": capture,
                    "clean_margin": clean_margin,
                    "example_id": example.example_id,
                    "scores": scores,
                    "seed": seed,
                })
                for example, scores, clean_margin, capture in score_rows
            ),
        )
        # Phase 2: independent reruns measure ablation and patch effects.
        for example, scores, clean_margin, capture in score_rows:
            effects, patches = intervention_effects(model, example)
            regrets = {}
            selections = {}
            informative = False
            for method in METHODS:
                regrets[method], informative = normalized_regret(
                    effects, scores[method]
                )
                selections[method] = selected(scores[method])
            records.append(
                {
                    "record_id": f"s{seed}-{example.example_id}",
                    "ablation_effects": effects,
                    "bits": list(example.bits),
                    "capture": capture,
                    "causal_positions": list(example.causal_positions),
                    "checkpoint_sha256": digest,
                    "clean_margin": clean_margin,
                    "example_id": example.example_id,
                    "family": example.family,
                    "informative": informative,
                    "label": example.label,
                    "patch_effects": patches,
                    "regrets": regrets,
                    "score_phase_sha256": score_digest,
                    "scores": scores,
                    "seed": seed,
                    "selections": selections,
                    "split": example.split,
                    "tokens": list(example.tokens),
                }
            )
    records.sort(key=lambda row: str(row["record_id"]))
    eligible = len(records) == len(SEEDS) * len(eval_rows)
    method_regret = {
        method: sum(float(row["regrets"][method]) for row in records) / len(records)
        for method in METHODS
    } if records else {}
    per_seed = {}
    evaluation_accuracy = {}
    for seed in SEEDS:
        seed_rows = [row for row in records if row["seed"] == seed]
        evaluation_accuracy[str(seed)] = (
            sum(float(row["clean_margin"]) > 0 for row in seed_rows)
            / len(seed_rows) if seed_rows else 0.0
        )
        per_seed[str(seed)] = {
            "informative_coverage": (
                sum(bool(row["informative"]) for row in seed_rows) / len(seed_rows)
                if seed_rows else 0.0
            ),
            "method_regret": {
                method: (
                    sum(float(row["regrets"][method]) for row in seed_rows)
                    / len(seed_rows) if seed_rows else 0.0
                )
                for method in METHODS
            },
        }
    comparisons = {}
    for baseline in (*COMPETITIVE, "permuted_candidate"):
        by_seed_family: dict[int, dict[int, float]] = {}
        for seed in SEEDS:
            by_seed_family[seed] = {}
            for family in range(256, 320):
                family_rows = [
                    row for row in records
                    if row["seed"] == seed and row["family"] == family
                ]
                by_seed_family[seed][family] = (
                    sum(
                        float(row["regrets"][baseline])
                        - float(row["regrets"]["candidate_grad_x_activation"])
                        for row in family_rows
                    ) / len(family_rows) if family_rows else 0.0
                )
        seed_values = {
            str(seed): sum(by_seed_family[seed].values()) / 64 for seed in SEEDS
        }
        comparisons[baseline] = {
            "interval_95": _bootstrap(by_seed_family),
            "mean": sum(seed_values.values()) / 3,
            "per_seed": seed_values,
        }
    coverage_ok = eligible and all(
        per_seed[str(seed)]["informative_coverage"] >= 0.80 for seed in SEEDS
    )
    primary_ok = eligible and all(
        comparisons[baseline]["mean"] > 0.05
        and comparisons[baseline]["interval_95"][0] > 0.05
        and all(value > 0 for value in comparisons[baseline]["per_seed"].values())
        for baseline in COMPETITIVE
    )
    placebo_ok = (
        eligible
        and comparisons["permuted_candidate"]["mean"] > 0
        and comparisons["permuted_candidate"]["interval_95"][0] > 0
    )
    patch_by_seed = {
        baseline: {
            str(seed): (
                sum(
                    abs(row["patch_effects"][
                        row["selections"]["candidate_grad_x_activation"]
                    ])
                    - abs(row["patch_effects"][row["selections"][baseline]])
                    for row in records if row["seed"] == seed
                ) / (len(records) // 3) if records else 0.0
            )
            for seed in SEEDS
        }
        for baseline in COMPETITIVE
    }
    patch_ok = eligible and all(
        all(value > 0 for value in patch_by_seed[baseline].values())
        for baseline in COMPETITIVE
    )
    control_model, _ = train_actor(SEEDS[0])
    control_example = examples_for(range(160, 161))[0]
    torch = __import__("torch")
    control_tokens = torch.tensor([control_example.tokens])
    with torch.no_grad():
        base_logits, base_heads, _ = control_model(control_tokens)
        noop_logits = control_model(
            control_tokens, {0: base_heads[:, 0, :]}
        )[0]
    no_op_ok = bool(torch.equal(base_logits, noop_logits))
    repeated_scores_ok = (
        score_example(control_model, control_example)[0]
        == score_example(control_model, control_example)[0]
    )
    split_tokens = {
        "train": {row.tokens for row in examples_for(range(160))},
        "development": {
            row.tokens for row in examples_for(range(160, 192))
        },
        "evaluation": {
            row.tokens for row in examples_for(range(256, 320))
        },
    }
    overlap_ok = not (
        split_tokens["train"] & split_tokens["development"]
        or split_tokens["train"] & split_tokens["evaluation"]
        or split_tokens["development"] & split_tokens["evaluation"]
    )
    controls_ok = no_op_ok and repeated_scores_ok and overlap_ok
    accuracy_ok = all(value >= 0.95 for value in evaluation_accuracy.values())
    verdict = (
        "Inconclusive" if not eligible
        else "Pass" if (
            primary_ok and coverage_ok and placebo_ok and patch_ok
            and controls_ok and accuracy_ok
        )
        else "Null"
    )
    boundary = {
        "accepted_evidence": False,
        "level": "local_learned_model_measurement_candidate",
        "mechanistic_understanding": False,
        "self_modeling": False,
    }
    config = {
        "schema": "astral.learned-stage0.config.v1",
        "competitive_baselines": list(COMPETITIVE),
        "evaluation_families": [256, 319],
        "methods": list(METHODS),
        "practical_margin": 0.05,
        "seeds": list(SEEDS),
        "state_slice": STATE_SLICE,
    }
    summary = {
        "schema": "astral.learned-stage0.summary.v1",
        "checkpoint_sha256": checkpoints,
        "claim_boundary": boundary,
        "comparisons": comparisons,
        "coverage_gate": coverage_ok,
        "eligibility": eligible,
        "method_regret": method_regret,
        "patch_control": patch_ok,
        "patch_by_seed": patch_by_seed,
        "per_seed": per_seed,
        "placebo_control": placebo_ok,
        "primary_gate": primary_ok,
        "record_census": len(records),
        "run_controls": {
            "no_op": no_op_ok,
            "repeated_scores": repeated_scores_ok,
            "split_overlap_absent": overlap_ok,
        },
        "runtime_seconds": time.monotonic() - started,
        "training_by_seed": training_by_seed,
        "evaluation_accuracy": evaluation_accuracy,
        "protocol_sha256": protocol_digest,
        "verdict": verdict,
    }
    _write_new(output / "config.json", canonical_json(config))
    _write_new(
        output / "records.jsonl",
        b"".join(canonical_json(row) for row in records),
    )
    _write_new(output / "summary.json", canonical_json(summary))
    file_rows = []
    artifact_names = [
        "config.json", "records.jsonl", "summary.json", "protocol.lock.json",
        *(f"checkpoint-{seed}.pt" for seed in SEEDS),
        *(
            f"scores-{seed}.jsonl"
            for seed in SEEDS
            if (output / f"scores-{seed}.jsonl").exists()
        ),
    ]
    for name in artifact_names:
        raw = (output / name).read_bytes()
        file_rows.append({
            "bytes": len(raw), "path": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    manifest = {
        "schema": "astral.learned-stage0.manifest.v1",
        "claim_boundary": boundary,
        "files": file_rows,
        "repo_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
        "state_slice": STATE_SLICE,
    }
    total_bytes = sum(row["bytes"] for row in file_rows)
    if time.monotonic() - started > 1_800 or total_bytes > 256 * 1024 * 1024:
        raise RuntimeError("frozen compute or artifact cap exceeded")
    _write_new(output / "manifest.json", canonical_json(manifest))
    validation = validate(output)
    return {
        "manifest_sha256": hashlib.sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        "summary": summary,
        "validation": validation,
    }


def finalize_existing(output: Path, repo: Path) -> dict[str, object]:
    """Finalize the exact partial attempt after an inventory-only failure."""
    if (output / "manifest.json").exists():
        raise ValueError("manifest already exists")
    required = {"config.json", "records.jsonl", "summary.json", "protocol.lock.json"}
    if not required.issubset({path.name for path in output.iterdir()}):
        raise ValueError("partial attempt lacks required scientific payload")
    artifact_names = sorted(path.name for path in output.iterdir())
    file_rows = []
    for name in artifact_names:
        path = output / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("partial artifact must be a regular file")
        raw = path.read_bytes()
        file_rows.append({
            "bytes": len(raw), "path": name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    summary = json.loads((output / "summary.json").read_text())
    manifest = {
        "schema": "astral.learned-stage0.manifest.v1",
        "claim_boundary": summary["claim_boundary"],
        "files": file_rows,
        "repo_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
        "state_slice": STATE_SLICE,
    }
    _write_new(output / "manifest.json", canonical_json(manifest))
    validation = validate(output)
    return {
        "manifest_sha256": hashlib.sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        "summary": summary,
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--finalize-existing", action="store_true")
    args = parser.parse_args()
    result = (
        finalize_existing(args.output.resolve(), args.repo.resolve())
        if args.finalize_existing
        else run(args.output.resolve(), args.repo.resolve(), args.protocol.resolve())
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
