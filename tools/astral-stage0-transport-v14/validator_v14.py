"""Independent recomputation validator for V14."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from transport_v14 import STATE_SLICE, analyze, canonical


def load(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if raw != canonical(value):
        raise ValueError("noncanonical JSON")
    return value


def validate(root: Path, protocol: Path, v13_root: Path, v13_protocol: Path):
    manifest = load(root / "manifest.json")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("manifest state slice drift")
    expected = {row["path"]: row for row in manifest["files"]}
    actual = {path.name for path in root.iterdir() if path.name != "manifest.json"}
    if set(expected) != actual:
        raise ValueError("manifest census drift")
    for name, row in expected.items():
        raw = (root / name).read_bytes()
        if row != {"bytes": len(raw), "path": name, "sha256": hashlib.sha256(raw).hexdigest()}:
            raise ValueError("manifest digest drift")
    if load(root / "protocol.lock.json") != {
        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(), "state_slice": STATE_SLICE,
    }:
        raise ValueError("protocol drift")
    predictions, summary = analyze(v13_root.resolve(), v13_protocol)
    if (root / "predictions.jsonl").read_bytes() != b"".join(canonical(row) for row in predictions):
        raise ValueError("prediction recomputation drift")
    if load(root / "summary.json") != summary:
        raise ValueError("summary recomputation drift")
    binding = load(root / "source-binding.json")
    if binding != {
        "source_manifest_sha256": summary["source_manifest_sha256"],
        "source_prediction_lock_sha256": summary["source_prediction_lock_sha256"],
        "source_state_slice": "astral-stage0c-prediction-locked-causal-target-v13",
    }:
        raise ValueError("source binding drift")
    if any(summary[key] for key in ("accepted_evidence", "confirmation_authorized", "stage0_pass")):
        raise ValueError("claim escalation")
    return summary
