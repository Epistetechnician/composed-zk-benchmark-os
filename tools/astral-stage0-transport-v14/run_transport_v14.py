"""Materialize a repository-external V14 diagnostic bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from transport_v14 import STATE_SLICE, analyze, canonical


def prepare(root: Path, repo: Path):
    if root.is_symlink():
        raise ValueError("output must be real")
    root, repo = root.resolve(), repo.resolve()
    if root == repo or repo in root.parents or root in repo.parents:
        raise ValueError("output must be repository-external")
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise ValueError("output must be empty")
    root.mkdir(parents=True, exist_ok=True)
    return root


def run(root: Path, repo: Path, protocol: Path, v13_root: Path, v13_protocol: Path):
    root = prepare(root, repo)
    predictions, summary = analyze(v13_root.resolve(), v13_protocol)
    (root / "protocol.lock.json").write_bytes(canonical({
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
        "state_slice": STATE_SLICE,
    }))
    (root / "source-binding.json").write_bytes(canonical({
        "source_manifest_sha256": summary["source_manifest_sha256"],
        "source_prediction_lock_sha256": summary["source_prediction_lock_sha256"],
        "source_state_slice": "astral-stage0c-prediction-locked-causal-target-v13",
    }))
    (root / "predictions.jsonl").write_bytes(b"".join(canonical(row) for row in predictions))
    (root / "summary.json").write_bytes(canonical(summary))
    files = []
    for path in sorted(root.iterdir()):
        raw = path.read_bytes()
        files.append({"bytes": len(raw), "path": path.name, "sha256": hashlib.sha256(raw).hexdigest()})
    (root / "manifest.json").write_bytes(canonical({"files": files, "state_slice": STATE_SLICE}))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--v13-root", required=True, type=Path)
    parser.add_argument("--v13-protocol", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repo, args.protocol, args.v13_root, args.v13_protocol), indent=2, sort_keys=True))
