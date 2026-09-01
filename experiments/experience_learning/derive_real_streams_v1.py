"""Derive declared nonstationary tasks from immutable real panels.

State slice: ``oaklab-experience-learning-benchmark-v2``.

These are not relabeled as new source datasets. Each output manifest records
the parent custody digest and the exact deterministic transformation: target
drift, a feature-relevance change, and a delayed-reward TD task. No future
row is used to choose a transformation parameter.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from .acquire_real_data_v1 import validate_manifest as validate_parent_manifest
from .custody import load_custodied_jsonl, sha256_file
from .types import Experience


STATE_SLICE = "oaklab-experience-learning-benchmark-v2"
SCHEMA_VERSION = "oaklab.experience-learning.real-derived-custody.v1"


def _digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _write(path: Path, rows: list[dict]) -> tuple[str, int]:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    return sha256_file(str(path)), path.stat().st_size


def _row(item: Experience, *, target: float, reward: float = 0.0,
         next_features: tuple[float, ...] | None = None, done: bool | None = None,
         task_id: int | None = None, source_id: str) -> dict:
    return {
        "step": item.step,
        "features": list(item.features),
        "target": target,
        "reward": reward,
        "next_features": None if next_features is None else list(next_features),
        "done": item.done if done is None else done,
        "task_id": item.task_id if task_id is None else task_id,
        "event_indices": list(item.event_indices),
        "source_id": source_id,
    }


def _parent_rows(root: Path, name: str) -> tuple[tuple[Experience, ...], dict]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    record = next((value for value in manifest["datasets"] if value["name"] == name), None)
    if record is None:
        raise ValueError(f"parent dataset missing: {name}")
    rows, _ = load_custodied_jsonl(str(root / record["derived_file"]), record["kind"], record["derived_sha256"])
    return rows, manifest


def derive(input_root: Path, output_root: Path, limit: int = 5120) -> dict:
    if limit < 2:
        raise ValueError("limit must be at least two")
    parent_status = validate_parent_manifest(input_root)
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty derived root: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "derived").mkdir(exist_ok=True)
    power_rows, parent_manifest = _parent_rows(input_root, "long_horizon")
    sensor_rows, _ = _parent_rows(input_root, "sensor")
    if len(power_rows) < limit or len(sensor_rows) < limit:
        raise ValueError("parent panels are shorter than requested derived limit")
    power_rows = power_rows[:limit]
    sensor_rows = sensor_rows[:limit]
    drift_rows = []
    for item in power_rows:
        drift = 0.05 * item.step / max(1, limit - 1)
        drift_rows.append(_row(item, target=item.target + drift,
                               next_features=item.next_features,
                               source_id=f"target-drift:{item.source_id}"))
    relevance_rows = []
    midpoint = limit // 2
    for item in sensor_rows:
        shift = 0.5 * item.features[0] if item.step >= midpoint else 0.0
        relevance_rows.append(_row(item, target=item.target + shift,
                                   task_id=0 if item.step < midpoint else 1,
                                   source_id=f"feature-relevance-shift:{item.source_id}"))
    delay = 3
    delayed_rows = []
    for index, item in enumerate(power_rows):
        delayed_reward = power_rows[index - delay].target if index >= delay else 0.0
        next_features = None if index == limit - 1 else power_rows[index + 1].features
        delayed_rows.append(_row(item, target=delayed_reward, reward=delayed_reward,
                                 next_features=next_features, done=index == limit - 1,
                                 task_id=index // 128,
                                 source_id=f"delayed-reward-{delay}:{item.source_id}"))
    generated = {
        "target_drift": (drift_rows, {
            "parent_dataset": "long_horizon", "transformation": "target += 0.05 * step/(limit-1)",
            "target_drift_max": 0.05,
        }),
        "feature_relevance_shift": (relevance_rows, {
            "parent_dataset": "sensor", "transformation": "target += 0.5 * feature[0] after midpoint",
            "change_at": midpoint,
        }),
        "delayed_reward": (delayed_rows, {
            "parent_dataset": "long_horizon", "transformation": "reward and target are source target delayed by three rows",
            "delay_rows": delay, "td_gamma": 0.9,
        }),
    }
    records = []
    for name, (rows, derivation) in generated.items():
        path = output_root / "derived" / f"{name}.jsonl"
        digest, size = _write(path, rows)
        records.append({"name": name, "kind": "long_horizon" if name != "feature_relevance_shift" else "sensor",
                        "derived_file": str(Path("derived") / path.name), "derived_sha256": digest,
                        "derived_bytes": size, "rows": len(rows), "feature_dim": len(rows[0]["features"]),
                        "derivation": derivation})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "state_slice": STATE_SLICE,
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "parent_manifest_sha256": parent_status["manifest_sha256"],
        "parent_root": str(input_root),
        "panel_limit": limit,
        "datasets": records,
    }
    manifest["manifest_sha256"] = _digest(manifest)
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (output_root / "README.md").write_text(
        f"# Oak Lab real-derived stream custody\n\nState slice: `{STATE_SLICE}`.\n\n"
        f"Parent manifest: `{parent_status['manifest_sha256']}`. Outputs are deterministic task transforms, not new source datasets.\n",
        encoding="utf-8",
    )
    seal(output_root)
    return {"status": "acquired", "manifest_sha256": manifest["manifest_sha256"], "parent_manifest_sha256": parent_status["manifest_sha256"],
            "datasets": [{"name": item["name"], "rows": item["rows"], "feature_dim": item["feature_dim"]} for item in records]}


def seal(root: Path) -> None:
    """Make the derived custody root read-only after writing its manifest."""
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(0o444)
    for path in sorted((item for item in root.rglob("*") if path_is_dir(item)), key=lambda item: len(item.parts), reverse=True):
        path.chmod(0o555)


def path_is_dir(path: Path) -> bool:
    return path.is_dir()


def validate_manifest(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("derived custody schema or state mismatch")
    if manifest.get("manifest_sha256") != _digest({key: value for key, value in manifest.items() if key != "manifest_sha256"}):
        raise ValueError("derived custody manifest digest mismatch")
    parent = Path(manifest["parent_root"])
    parent_status = validate_parent_manifest(parent)
    if parent_status["manifest_sha256"] != manifest["parent_manifest_sha256"]:
        raise ValueError("derived parent manifest mismatch")
    checked = []
    for record in manifest.get("datasets", []):
        path = (root / record["derived_file"]).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise FileNotFoundError(record["derived_file"])
        rows, custody = load_custodied_jsonl(str(path), record["kind"], record["derived_sha256"])
        if len(rows) != record["rows"] or path.stat().st_size != record["derived_bytes"] or custody.sha256 != record["derived_sha256"]:
            raise ValueError(f"derived readback mismatch: {record['name']}")
        checked.append({"name": record["name"], "rows": len(rows), "feature_dim": len(rows[0].features)})
    return {"status": "valid", "state_slice": STATE_SLICE, "manifest_sha256": manifest["manifest_sha256"], "datasets": checked}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=5120)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_manifest(args.output_root), sort_keys=True, allow_nan=False))
    else:
        if args.input_root is None:
            parser.error("--input-root is required unless --validate is supplied")
        print(json.dumps(derive(args.input_root, args.output_root, args.limit), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
