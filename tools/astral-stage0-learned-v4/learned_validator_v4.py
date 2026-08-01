"""Semantic validator for V4 fresh-holdout bundles."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import torch

from learned_stage0_v4 import (
    EVALUATION_FAMILIES, METHODS, SCIENTIFIC_SEEDS, STATE_SLICE,
    FrozenScientificTransformer, examples_for, normalized_regret,
    semantic_digest, selected,
)
from run_learned_stage0_v4 import summarize


def pairs(items):
    value = {}
    for key, child in items:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = child
    return value


def load(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=pairs)
    expected = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    if raw != expected:
        raise ValueError("noncanonical JSON")
    return value


def validate(root: Path, protocol: Path) -> dict[str, object]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("invalid bundle root")
    manifest = load(root / "manifest.json")
    if manifest["state_slice"] != STATE_SLICE:
        raise ValueError("state slice drift")
    declared = manifest["files"]
    actual = sorted(path.name for path in root.iterdir() if path.name != "manifest.json")
    if sorted(row["path"] for row in declared) != actual:
        raise ValueError("file census drift")
    for row in declared:
        path = root / row["path"]
        if path.is_symlink() or not path.is_file():
            raise ValueError("artifact must be regular")
        raw = path.read_bytes()
        if row["bytes"] != len(raw) or row["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ValueError("artifact digest drift")
    lock = load(root / "protocol.lock.json")
    if lock["protocol_sha256"] != hashlib.sha256(protocol.read_bytes()).hexdigest():
        raise ValueError("protocol binding drift")
    qualification_lock = load(root / "qualification.lock.json")
    if qualification_lock["seeds"] != list(SCIENTIFIC_SEEDS):
        raise ValueError("qualification seed drift")
    checkpoints = {}
    for seed in SCIENTIFIC_SEEDS:
        actor = FrozenScientificTransformer(seed)
        actor.load_state_dict(torch.load(root / f"checkpoint-{seed}.pt", weights_only=True))
        actor.eval()
        digest = semantic_digest(actor)
        if digest != qualification_lock["checkpoint_sha256"][str(seed)]:
            raise ValueError("checkpoint semantic digest drift")
        checkpoints[seed] = digest
    score_lock = load(root / "score-phase.lock.json")
    score_rows = {}
    for seed in SCIENTIFIC_SEEDS:
        path = root / f"scores-{seed}.jsonl"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != score_lock["score_sha256"][str(seed)]:
            raise ValueError("score phase digest drift")
        rows = [json.loads(line, object_pairs_hook=pairs) for line in raw.splitlines()]
        if len(rows) != 1024:
            raise ValueError("score census drift")
        score_rows[seed] = {row["example_id"]: row for row in rows}
    raw_records = (root / "records.jsonl").read_bytes().splitlines()
    if len(raw_records) != 3072:
        raise ValueError("record census drift")
    records = [json.loads(line, object_pairs_hook=pairs) for line in raw_records]
    expected_examples = {row.example_id: row for row in examples_for(EVALUATION_FAMILIES)}
    seen = set()
    prior = ""
    for row in records:
        if row["record_id"] <= prior or row["record_id"] in seen:
            raise ValueError("record order or uniqueness drift")
        prior = row["record_id"]
        seen.add(row["record_id"])
        if row["seed"] not in SCIENTIFIC_SEEDS or row["family"] not in EVALUATION_FAMILIES:
            raise ValueError("seed or holdout drift")
        example = expected_examples.get(row["example_id"])
        if example is None or (
            row["family"] != example.family
            or row["bits"] != list(example.bits)
            or row["tokens"] != list(example.tokens)
            or row["label"] != example.label
            or row["causal_positions"] != list(example.causal_positions)
        ):
            raise ValueError("example semantics drift")
        if row["checkpoint_sha256"] != checkpoints[row["seed"]]:
            raise ValueError("record checkpoint binding drift")
        scored = score_rows[row["seed"]][row["example_id"]]
        if row["scores"] != scored["scores"] or row["capture"] != scored["capture"]:
            raise ValueError("score lock binding drift")
        for vector_name in ("ablation_effects", "patch_effects"):
            vector = row[vector_name]
            if len(vector) != 4 or not all(math.isfinite(value) for value in vector):
                raise ValueError("effect vector drift")
        for method in METHODS:
            regret, informative = normalized_regret(row["ablation_effects"], row["scores"][method])
            if abs(row["regrets"][method] - regret) > 1e-7:
                raise ValueError("regret drift")
            if row["selections"][method] != selected(row["scores"][method]):
                raise ValueError("selection drift")
            if row["informative"] != informative:
                raise ValueError("informative drift")
    if len(seen) != 3072:
        raise ValueError("record uniqueness drift")
    summary = load(root / "summary.json")
    if summary["holdout_families"] != [
        min(EVALUATION_FAMILIES),
        max(EVALUATION_FAMILIES),
    ]:
        raise ValueError("holdout summary drift")
    recomputed = summarize(records)
    for key, value in recomputed.items():
        if summary[key] != value:
            raise ValueError(f"summary drift: {key}")
    expected_pass = all((
        recomputed["accuracy_gate"], recomputed["coverage_gate"],
        recomputed["primary_gate"], recomputed["placebo_control"],
        recomputed["patch_control"], all(summary["run_controls"].values()),
    ))
    if summary["verdict"] != ("Pass" if expected_pass else "Null"):
        raise ValueError("verdict drift")
    boundary = summary["claim_boundary"]
    if boundary != {
        "accepted_evidence": False,
        "independent_replication": False,
        "level": "local_learned_model_measurement_candidate",
        "self_modeling": False,
    }:
        raise ValueError("claim boundary drift")
    return {"valid": True, "verdict": summary["verdict"], "record_census": len(records)}
