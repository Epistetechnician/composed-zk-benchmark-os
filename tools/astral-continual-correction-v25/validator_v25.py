#!/usr/bin/env python3
"""Fail-closed validator for an Astral V25 content-addressed artifact."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import v25 as V25


EXPECTED_FILES = {
    "adaptation.jsonl",
    "determinism.json",
    "experiment-contract.json",
    "observations.jsonl",
    "replay-checks.jsonl",
    "result.json",
    "runtime.json",
    "source-inventory.json",
    "updates.jsonl",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return value == path.as_posix() and value not in ("", ".") and not path.is_absolute() and ".." not in path.parts


def verify_manifest(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("artifact root must be a real directory")
    manifest = root / V25.MANIFEST
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError("artifact manifest missing")
    rows: dict[str, str] = {}
    for line in manifest.read_text().splitlines():
        expected, separator, relative = line.partition("  ")
        if not separator or not SHA256.fullmatch(expected) or not safe_relative(relative) or relative in rows:
            raise ValueError("invalid artifact manifest row")
        rows[relative] = expected
    if list(rows) != sorted(rows) or set(rows) != EXPECTED_FILES:
        raise ValueError("artifact manifest census mismatch")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("artifact symlink forbidden")
        if path.is_file() and path.name != V25.MANIFEST:
            actual.add(path.relative_to(root).as_posix())
    if actual != set(rows):
        raise ValueError("artifact file census mismatch")
    for relative, expected in rows.items():
        if V25.sha256(root / relative) != expected:
            raise ValueError(f"artifact digest mismatch: {relative}")
    identity = V25.sha256(manifest)
    if root.name != f"astral-v25-{identity}":
        raise ValueError("artifact directory is not content addressed")
    return {"file_count": len(rows), "manifest_sha256": identity}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for index, line in enumerate(path.read_text().splitlines(), start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {path.name}:{index}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"non-object JSONL at {path.name}:{index}")
        rows.append(value)
    return rows


def verify_source_inventory(root: Path) -> int:
    retained = json.loads((root / "source-inventory.json").read_text())
    expected = {name: V25.sha256(V25.HERE / name) for name in V25.SOURCE_NAMES}
    if retained != expected:
        raise ValueError("artifact source inventory mismatch")
    return len(retained)


def verify_counts(
    contract: dict[str, Any],
    adaptation: list[dict[str, Any]],
    updates: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    replay: list[dict[str, Any]],
) -> dict[str, int]:
    seed_count = len(contract["seeds"])
    tasks = contract["tasks_per_seed"]
    worlds = len(contract["worlds"])
    conditions = len(contract["conditions"])
    expected = {
        "adaptation": seed_count * tasks * contract["adaptation_examples"],
        "updates": worlds * seed_count * tasks * conditions,
        "observations": worlds * seed_count * tasks * conditions * contract["future_examples"],
        "replay": worlds * seed_count * conditions * (tasks * (tasks - 1) // 2),
    }
    actual = {
        "adaptation": len(adaptation),
        "updates": len(updates),
        "observations": len(observations),
        "replay": len(replay),
    }
    if actual != expected:
        raise ValueError(f"raw record census mismatch: {actual} != {expected}")
    return actual


def validate(root: Path) -> dict[str, Any]:
    manifest = verify_manifest(root)
    retained_contract = json.loads((root / "experiment-contract.json").read_text())
    expected_contract = json.loads(V25.CONTRACT_PATH.read_text())
    if retained_contract != expected_contract:
        raise ValueError("experiment contract mismatch")
    source_count = verify_source_inventory(root)
    adaptation = read_jsonl(root / "adaptation.jsonl")
    updates = read_jsonl(root / "updates.jsonl")
    observations = read_jsonl(root / "observations.jsonl")
    replay = read_jsonl(root / "replay-checks.jsonl")
    counts = verify_counts(retained_contract, adaptation, updates, observations, replay)
    retained_result = json.loads((root / "result.json").read_text())
    recomputed_result = V25.summarize(observations, replay, retained_contract)
    if retained_result != recomputed_result:
        raise ValueError("result does not recompute from raw observations")
    regenerated = V25.simulate(retained_contract)
    for name, retained, generated in (
        ("adaptation", adaptation, regenerated["adaptation"]),
        ("updates", updates, regenerated["updates"]),
        ("observations", observations, regenerated["observations"]),
        ("replay", replay, regenerated["replay"]),
    ):
        if retained != generated:
            raise ValueError(f"deterministic raw replay mismatch: {name}")
    if retained_result != regenerated["result"]:
        raise ValueError("deterministic result replay mismatch")
    determinism = json.loads((root / "determinism.json").read_text())
    result_digest = __import__("hashlib").sha256(V25.canonical_bytes(retained_result)).hexdigest()
    if determinism != {
        "byte_equivalent_structures": True,
        "first_result_sha256": result_digest,
        "second_result_sha256": result_digest,
    }:
        raise ValueError("determinism record mismatch")
    runtime = json.loads((root / "runtime.json").read_text())
    if runtime.get("base_image_digest") == "host-run" or runtime.get("container_image_id") == "host-run":
        raise ValueError("artifact was not produced by the Docker runner")
    if retained_result["classification"] != retained_contract["claim_ceiling"]:
        raise ValueError("V25 synthetic harness did not qualify")
    if retained_result["external_states"] != {
        "confirmation": "NotAuthorized",
        "independently_verified": "NotRun",
        "model_backed_continual_learning": "NotRun",
        "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C",
        "thesis": "NotValidated",
    }:
        raise ValueError("external-state boundary mismatch")
    return {
        "artifact": manifest,
        "classification": retained_result["classification"],
        "claim_ceiling": retained_result["claim_ceiling"],
        "external_states": retained_result["external_states"],
        "raw_counts": counts,
        "runtime": runtime,
        "source_file_count": source_count,
        "worlds": retained_result["worlds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.artifact.resolve())
        if args.report:
            report = args.report.resolve()
            if report.exists() or report.with_suffix(report.suffix + ".sha256").exists():
                raise ValueError("report destination already exists")
            report.parent.mkdir(parents=True, exist_ok=True)
            V25.write_json(report, result)
            report.with_suffix(report.suffix + ".sha256").write_text(f"{V25.sha256(report)}  {report.name}\n")
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "V25ValidationPassed", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
