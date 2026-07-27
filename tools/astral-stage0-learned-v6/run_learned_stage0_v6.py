"""Run the complete V6 development-only attribution panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import sys

import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned"))
from learned_stage0 import canonical_json
from learned_stage0_v6 import (
    ASSESSMENT_FAMILIES, BASELINES, DEVELOPMENT_FAMILIES, EXPLORATORY_SEEDS,
    METHODS, NEW_METHODS, STATE_SLICE, effects, examples_for, normalized_regret,
    reproduce, score_example, selected,
)


def write(path: Path, value: object) -> None:
    path.write_bytes(canonical_json(value))


def prepare(root: Path, repository: Path) -> Path:
    if root.is_symlink():
        raise ValueError("output must be real")
    root, repository = root.resolve(), repository.resolve()
    if root == repository or repository in root.parents:
        raise ValueError("output must be repository-external")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("output must be empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def metrics(records: list[dict[str, object]]) -> dict[str, object]:
    assessment = [row for row in records if row["family"] in ASSESSMENT_FAMILIES]
    method_results = {}
    eligible = []
    for method in METHODS:
        comparisons = {}
        cells = []
        for baseline in BASELINES:
            per_seed = {}
            for seed in EXPLORATORY_SEEDS:
                rows = [row for row in assessment if row["seed"] == seed]
                value = sum(
                    row["regrets"][baseline] - row["regrets"][method] for row in rows
                ) / len(rows)
                per_seed[str(seed)] = value
                cells.append(value)
            comparisons[baseline] = {
                "mean": sum(per_seed.values()) / len(per_seed),
                "per_seed": per_seed,
            }
        coverage = {
            str(seed): sum(row["informative"] for row in assessment if row["seed"] == seed)
            / len([row for row in assessment if row["seed"] == seed])
            for seed in EXPLORATORY_SEEDS
        }
        permutation = None
        is_eligible = False
        if method in NEW_METHODS:
            permutation = {}
            control = f"permuted_{method}"
            for seed in EXPLORATORY_SEEDS:
                rows = [row for row in assessment if row["seed"] == seed]
                permutation[str(seed)] = sum(
                    row["regrets"][control] - row["regrets"][method] for row in rows
                ) / len(rows)
            is_eligible = (
                all(value >= .80 for value in coverage.values())
                and all(item["mean"] > .05 for item in comparisons.values())
                and all(value > 0 for item in comparisons.values() for value in item["per_seed"].values())
                and sum(permutation.values()) / 3 > 0
                and all(value > 0 for value in permutation.values())
            )
            if is_eligible:
                eligible.append((min(cells), sum(cells) / len(cells), method))
        method_results[method] = {
            "comparisons": comparisons, "coverage": coverage,
            "eligible": is_eligible, "permutation_advantage": permutation,
        }
    order = {method: index for index, method in enumerate(NEW_METHODS)}
    winner = max(eligible, key=lambda row: (row[0], row[1], -order[row[2]]))[2] if eligible else None
    return {
        "classification": "ExploratoryMethodSelected" if winner else "ExploratoryNoSelection",
        "method_results": method_results,
        "selected_method": winner,
    }


def run(root: Path, repository: Path, protocol: Path) -> dict[str, object]:
    started = time.monotonic()
    root = prepare(root, repository)
    protocol_sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
    write(root / "protocol.lock.json", {
        "protocol_sha256": protocol_sha, "state_slice": STATE_SLICE,
    })
    actors, qualification = {}, []
    for seed in EXPLORATORY_SEEDS:
        actor, row = reproduce(seed)
        qualification.append(row)
        write(root / f"qualification-{seed}.json", row)
        if not row["eligible"]:
            outcome = {"classification": "ExploratoryQualificationFailed", "qualification": qualification}
            write(root / "summary.json", outcome)
            files = []
            for path in sorted(root.iterdir()):
                raw = path.read_bytes()
                files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
            write(root / "manifest.json", {"files": files, "state_slice": STATE_SLICE})
            return outcome
        actors[seed] = actor
        torch.save(actor.state_dict(), root / f"checkpoint-{seed}.pt")
    examples = examples_for(DEVELOPMENT_FAMILIES)
    scored = {}
    score_hashes = {}
    for seed in EXPLORATORY_SEEDS:
        rows = [(example, score_example(actors[seed], example)) for example in examples]
        payload = b"".join(canonical_json({
            "example_id": example.example_id, "scores": scores, "seed": seed,
        }) for example, scores in rows)
        (root / f"scores-{seed}.jsonl").write_bytes(payload)
        score_hashes[str(seed)] = hashlib.sha256(payload).hexdigest()
        scored[seed] = rows
    write(root / "score-phase.lock.json", {"sha256": score_hashes, "census": 1536})
    records = []
    all_methods = (*METHODS, *BASELINES, *(f"permuted_{method}" for method in NEW_METHODS))
    for seed in EXPLORATORY_SEEDS:
        for example, scores in scored[seed]:
            ablations, patches = effects(actors[seed], example)
            regrets, selections = {}, {}
            informative = False
            for method in all_methods:
                regrets[method], informative = normalized_regret(ablations, scores[method])
                selections[method] = selected(scores[method])
            records.append({
                "ablation_effects": ablations, "example_id": example.example_id,
                "family": example.family, "fold": "assessment" if example.family in ASSESSMENT_FAMILIES else "design",
                "informative": informative, "patch_effects": patches, "regrets": regrets,
                "scores": scores, "seed": seed, "selections": selections,
            })
    records.sort(key=lambda row: (row["seed"], row["family"], row["example_id"]))
    (root / "records.jsonl").write_bytes(b"".join(canonical_json(row) for row in records))
    result = {
        **metrics(records),
        "accepted_evidence": False,
        "claim_class": "LocalExploratoryAttributionMethodDiagnostic",
        "record_census": len(records),
        "runtime_seconds": time.monotonic() - started,
        "stage0_pass": False,
        "state_slice": STATE_SLICE,
    }
    write(root / "summary.json", result)
    files = []
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    write(root / "manifest.json", {"files": files, "state_slice": STATE_SLICE})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
