"""Execute the locked V4 fresh-holdout confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import time

import torch

from learned_stage0_v4 import (
    COMPETITIVE, EVALUATION_FAMILIES, METHODS, SCIENTIFIC_SEEDS, STATE_SLICE,
    canonical_json, clean_parity, configure_runtime, examples_for,
    intervention_effects, normalized_regret, reproduce, score_example, selected,
)

PROTOCOL_RELATIVE_PATH = "docs/research/astral-self-modeling/12-stage0-fresh-holdout-scientific-confirmation-v4.md"


def write_new(path: Path, value: object) -> None:
    if path.exists():
        raise ValueError("refusing to overwrite artifact")
    path.write_bytes(canonical_json(value))


def prepare_output(root: Path, repository: Path) -> Path:
    if root.is_symlink():
        raise ValueError("output must be a real directory")
    root = root.resolve()
    repository = repository.resolve()
    if root == repository or repository in root.parents:
        raise ValueError("output must be repository-external")
    if root.exists():
        if not root.is_dir() or any(root.iterdir()):
            raise ValueError("output must be an empty directory")
    else:
        root.mkdir(parents=True)
    return root


def interval(values: list[float]) -> list[float]:
    ordered = sorted(values)
    return [ordered[int(.025 * (len(ordered) - 1))], ordered[int(.975 * (len(ordered) - 1))]]


def bootstrap(values: dict[int, dict[int, float]]) -> list[float]:
    rng = random.Random(20260727)
    seeds = sorted(values)
    estimates = []
    for _ in range(2_000):
        seed_sample = [seeds[rng.randrange(len(seeds))] for _ in seeds]
        seed_means = []
        for seed in seed_sample:
            families = sorted(values[seed])
            sample = [families[rng.randrange(len(families))] for _ in families]
            seed_means.append(sum(values[seed][family] for family in sample) / len(sample))
        estimates.append(sum(seed_means) / len(seed_means))
    return interval(estimates)


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    method_regret = {
        method: sum(row["regrets"][method] for row in records) / len(records)
        for method in METHODS
    }
    per_seed = {}
    evaluation_accuracy = {}
    for seed in SCIENTIFIC_SEEDS:
        rows = [row for row in records if row["seed"] == seed]
        evaluation_accuracy[str(seed)] = sum(row["clean_margin"] > 0 for row in rows) / len(rows)
        per_seed[str(seed)] = {
            "informative_coverage": sum(row["informative"] for row in rows) / len(rows),
            "method_regret": {
                method: sum(row["regrets"][method] for row in rows) / len(rows)
                for method in METHODS
            },
        }
    comparisons = {}
    for baseline in (*COMPETITIVE, "permuted_candidate"):
        by_seed_family = {}
        for seed in SCIENTIFIC_SEEDS:
            by_seed_family[seed] = {}
            for family in EVALUATION_FAMILIES:
                rows = [row for row in records if row["seed"] == seed and row["family"] == family]
                by_seed_family[seed][family] = sum(
                    row["regrets"][baseline] - row["regrets"]["candidate_grad_x_activation"]
                    for row in rows
                ) / len(rows)
        seed_values = {
            str(seed): sum(by_seed_family[seed].values()) / 64 for seed in SCIENTIFIC_SEEDS
        }
        comparisons[baseline] = {
            "interval_95": bootstrap(by_seed_family),
            "mean": sum(seed_values.values()) / 3,
            "per_seed": seed_values,
        }
    patch_by_seed = {
        baseline: {
            str(seed): sum(
                abs(row["patch_effects"][row["selections"]["candidate_grad_x_activation"]])
                - abs(row["patch_effects"][row["selections"][baseline]])
                for row in records if row["seed"] == seed
            ) / 1024
            for seed in SCIENTIFIC_SEEDS
        }
        for baseline in COMPETITIVE
    }
    coverage_gate = all(per_seed[str(seed)]["informative_coverage"] >= .80 for seed in SCIENTIFIC_SEEDS)
    primary_gate = all(
        comparisons[baseline]["mean"] > .05
        and comparisons[baseline]["interval_95"][0] > .05
        and all(value > 0 for value in comparisons[baseline]["per_seed"].values())
        for baseline in COMPETITIVE
    )
    placebo_control = (
        comparisons["permuted_candidate"]["mean"] > 0
        and comparisons["permuted_candidate"]["interval_95"][0] > 0
    )
    patch_control = all(
        all(value > 0 for value in patch_by_seed[baseline].values())
        for baseline in COMPETITIVE
    )
    accuracy_gate = all(value >= .95 for value in evaluation_accuracy.values())
    return {
        "accuracy_gate": accuracy_gate,
        "comparisons": comparisons,
        "coverage_gate": coverage_gate,
        "evaluation_accuracy": evaluation_accuracy,
        "method_regret": method_regret,
        "patch_by_seed": patch_by_seed,
        "patch_control": patch_control,
        "per_seed": per_seed,
        "placebo_control": placebo_control,
        "primary_gate": primary_gate,
    }


def run(output: Path, repository: Path, protocol: Path) -> dict[str, object]:
    configure_runtime()
    if torch.__version__ != "2.12.0":
        raise RuntimeError("frozen torch version mismatch")
    started = time.monotonic()
    output = prepare_output(output, repository)
    protocol_digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    write_new(output / "protocol.lock.json", {
        "protocol_path": PROTOCOL_RELATIVE_PATH,
        "protocol_sha256": protocol_digest,
        "reviewers": ["protocol-audit", "code-audit", "science-audit"],
        "state_slice": STATE_SLICE,
    })
    if not clean_parity():
        raise RuntimeError("V3/V4 clean-forward parity failed")
    actors = {}
    qualification = []
    for seed in SCIENTIFIC_SEEDS:
        model, row = reproduce(seed)
        qualification.append(row)
        write_new(output / f"qualification-{seed}.json", row)
        if not row["eligible"]:
            outcome = {
                "classification": "Inconclusive",
                "holdout_opened": False,
                "qualification": qualification,
                "state_slice": STATE_SLICE,
            }
            write_new(output / "outcome.json", outcome)
            return outcome
        actors[seed] = model
        torch.save(model.state_dict(), output / f"checkpoint-{seed}.pt")
    write_new(output / "qualification.lock.json", {
        "checkpoint_sha256": {
            str(seed): qualification[index]["first"]["checkpoint_sha256"]
            for index, seed in enumerate(SCIENTIFIC_SEEDS)
        },
        "seeds": list(SCIENTIFIC_SEEDS),
        "state_slice": STATE_SLICE,
    })
    evaluation = examples_for(EVALUATION_FAMILIES)
    scored = {}
    score_digests = {}
    for seed in SCIENTIFIC_SEEDS:
        rows = []
        for example in evaluation:
            scores, clean_margin, capture = score_example(actors[seed], example)
            rows.append((example, scores, clean_margin, capture))
        payload = b"".join(canonical_json({
            "capture": capture, "clean_margin": margin,
            "example_id": example.example_id, "scores": scores, "seed": seed,
        }) for example, scores, margin, capture in rows)
        (output / f"scores-{seed}.jsonl").write_bytes(payload)
        score_digests[str(seed)] = hashlib.sha256(payload).hexdigest()
        scored[seed] = rows
    write_new(output / "score-phase.lock.json", {
        "record_census": 3072,
        "score_sha256": score_digests,
        "state_slice": STATE_SLICE,
    })
    records = []
    for seed in SCIENTIFIC_SEEDS:
        checkpoint = qualification[list(SCIENTIFIC_SEEDS).index(seed)]["first"]["checkpoint_sha256"]
        for example, scores, clean_margin, capture in scored[seed]:
            effects, patches = intervention_effects(actors[seed], example)
            regrets, selections = {}, {}
            informative = False
            for method in METHODS:
                regrets[method], informative = normalized_regret(effects, scores[method])
                selections[method] = selected(scores[method])
            records.append({
                "ablation_effects": effects, "bits": list(example.bits),
                "capture": capture, "causal_positions": list(example.causal_positions),
                "checkpoint_sha256": checkpoint, "clean_margin": clean_margin,
                "example_id": example.example_id, "family": example.family,
                "informative": informative, "label": example.label,
                "patch_effects": patches, "record_id": f"s{seed}-{example.example_id}",
                "regrets": regrets, "score_phase_sha256": score_digests[str(seed)],
                "scores": scores, "seed": seed, "selections": selections,
                "split": "evaluation_v4", "tokens": list(example.tokens),
            })
    records.sort(key=lambda row: row["record_id"])
    (output / "records.jsonl").write_bytes(b"".join(canonical_json(row) for row in records))
    metrics = summarize(records)
    control_example = examples_for(range(160, 161))[0]
    control_actor = actors[SCIENTIFIC_SEEDS[0]]
    token = torch.tensor([control_example.tokens])
    with torch.no_grad():
        base, heads, _ = control_actor(token)
        noop = control_actor(token, {0: heads[:, 0, :]})[0]
    controls = {
        "clean_forward_parity": clean_parity(),
        "no_op": bool(torch.equal(base, noop)),
        "repeated_scores": score_example(control_actor, control_example)[0]
        == score_example(control_actor, control_example)[0],
    }
    pass_gate = all((
        metrics["accuracy_gate"], metrics["coverage_gate"], metrics["primary_gate"],
        metrics["placebo_control"], metrics["patch_control"], all(controls.values()),
    ))
    summary = {
        **metrics,
        "claim_boundary": {
            "accepted_evidence": False,
            "independent_replication": False,
            "level": "local_learned_model_measurement_candidate",
            "self_modeling": False,
        },
        "holdout_families": [
            min(EVALUATION_FAMILIES),
            max(EVALUATION_FAMILIES),
        ],
        "record_census": len(records),
        "run_controls": controls,
        "runtime_seconds": time.monotonic() - started,
        "state_slice": STATE_SLICE,
        "verdict": "Pass" if pass_gate else "Null",
    }
    write_new(output / "summary.json", summary)
    write_new(output / "config.json", {
        "competitive_baselines": list(COMPETITIVE),
        "families": [384, 447], "methods": list(METHODS),
        "practical_margin": .05, "seeds": list(SCIENTIFIC_SEEDS),
        "state_slice": STATE_SLICE,
    })
    names = sorted(path.name for path in output.iterdir())
    files = []
    for name in names:
        raw = (output / name).read_bytes()
        files.append({"bytes": len(raw), "path": name, "sha256": hashlib.sha256(raw).hexdigest()})
    if time.monotonic() - started > 1800 or sum(row["bytes"] for row in files) > 256 * 1024 * 1024:
        raise RuntimeError("resource cap exceeded")
    manifest = {
        "files": files,
        "repo_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
        "state_slice": STATE_SLICE,
    }
    write_new(output / "manifest.json", manifest)
    return {"manifest_sha256": hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(), "summary": summary}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
