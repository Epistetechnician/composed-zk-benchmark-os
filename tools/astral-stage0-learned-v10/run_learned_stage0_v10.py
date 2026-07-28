"""Run V10 using the frozen V6 measurement and selection algebra."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import torch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / "astral-stage0-learned"))
sys.path.insert(0, str(TOOLS / "astral-stage0-learned-v6"))
from learned_stage0 import canonical_json  # noqa: E402
from run_learned_stage0_v6 import metrics  # noqa: E402
from learned_stage0_v10 import (  # noqa: E402
    ASSESSMENT_FAMILIES, BASELINES, DEVELOPMENT_FAMILIES, EXPLORATORY_SEEDS,
    METHODS, NEW_METHODS, STATE_SLICE, effects, examples_for, normalized_regret,
    reproduce, score_example, selected,
)


def write(path: Path, value: object) -> None:
    path.write_bytes(canonical_json(value))


def prepare(root: Path, repo: Path) -> Path:
    if root.is_symlink():
        raise ValueError("output must be real")
    root, repo = root.resolve(), repo.resolve()
    if root == repo or repo in root.parents:
        raise ValueError("output must be repository-external")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("output must be empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def finalize(root: Path, summary: dict[str, object]) -> dict[str, object]:
    write(root / "summary.json", summary)
    files = []
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    write(root / "manifest.json", {"files": files, "state_slice": STATE_SLICE})
    return summary


def run(root: Path, repo: Path, protocol: Path):
    started = time.monotonic()
    root = prepare(root, repo)
    write(root / "protocol.lock.json", {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "state_slice": STATE_SLICE,
    })
    actors = {}
    for seed in EXPLORATORY_SEEDS:
        actor, row = reproduce(seed)
        write(root / f"qualification-{seed}.json", row)
        if not row["eligible"]:
            return finalize(root, {
                "classification": "ExploratoryQualificationFailed",
                "failed_seed": seed, "stage0_pass": False, "state_slice": STATE_SLICE,
            })
        actors[seed] = actor
        torch.save(actor.state_dict(), root / f"checkpoint-{seed}.pt")
    examples = examples_for(DEVELOPMENT_FAMILIES)
    scored, hashes = {}, {}
    for seed in EXPLORATORY_SEEDS:
        rows = [(example, score_example(actors[seed], example)) for example in examples]
        payload = b"".join(canonical_json({
            "example_id": example.example_id, "scores": scores, "seed": seed,
        }) for example, scores in rows)
        (root / f"scores-{seed}.jsonl").write_bytes(payload)
        hashes[str(seed)] = hashlib.sha256(payload).hexdigest()
        scored[seed] = rows
    write(root / "score-phase.lock.json", {"census": 1536, "sha256": hashes})
    all_methods = (*METHODS, *BASELINES, *(f"permuted_{method}" for method in NEW_METHODS))
    records = []
    for seed in EXPLORATORY_SEEDS:
        for example, scores in scored[seed]:
            ablations, patches = effects(actors[seed], example)
            regrets, selections = {}, {}
            informative = max(abs(value) for value in ablations) > 1e-4
            for method in all_methods:
                regrets[method], _ = normalized_regret(ablations, scores[method])
                selections[method] = selected(scores[method])
            records.append({
                "ablation_effects": ablations, "example_id": example.example_id,
                "family": example.family,
                "fold": "assessment" if example.family in ASSESSMENT_FAMILIES else "design",
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
    return finalize(root, result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol), indent=2, sort_keys=True))
