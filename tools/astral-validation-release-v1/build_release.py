#!/usr/bin/env python3
"""Build a content-addressed, repository-external Astral validation package."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
SPEC_PATH = HERE.with_name("release-spec.json")
PACKAGES = ("mlx", "mlx-lm", "numpy", "torch", "pytest", "transformers")


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPOSITORY, check=True, capture_output=True, text=True
    ).stdout.strip()


def source_inventory() -> dict[str, str]:
    paths = []
    for prefix in (
        "AGENTS.md", "Cargo.toml", "Cargo.lock", "README.md",
        "crates/astral-stage0-protocol",
        "docs/research/astral-self-modeling",
    ):
        path = REPOSITORY / prefix
        if path.is_file():
            paths.append(path)
        else:
            paths.extend(sorted(candidate for candidate in path.rglob("*") if candidate.is_file()))
    paths.extend(
        sorted(
            candidate
            for directory in (REPOSITORY / "tools").glob("astral-*")
            for candidate in directory.rglob("*")
            if candidate.is_file() and "__pycache__" not in candidate.parts
        )
    )
    return {str(path.relative_to(REPOSITORY)): sha(path) for path in sorted(set(paths))}


def environment() -> dict[str, object]:
    versions = {}
    for package in PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "absent"
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages": versions,
    }


def package_manifest(root: Path) -> str:
    rows = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path.name == "PACKAGE-MANIFEST.sha256":
            continue
        rows.append(f"{sha(path)}  {path.relative_to(root)}")
    value = "\n".join(rows) + "\n"
    (root / "PACKAGE-MANIFEST.sha256").write_text(value)
    return hashlib.sha256(value.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-parent", required=True, type=Path)
    parser.add_argument(
        "--bundle", action="append", required=True,
        help="Bundle mapping such as v18=/absolute/path",
    )
    args = parser.parse_args()
    mappings = {}
    for item in args.bundle:
        name, separator, raw_path = item.partition("=")
        if not separator or name in mappings:
            raise SystemExit(f"invalid or duplicate bundle mapping: {item}")
        mappings[name] = Path(raw_path).resolve()
    spec = json.loads(SPEC_PATH.read_text())
    if set(mappings) != set(spec["bundles"]):
        raise SystemExit("bundle mapping census differs from release specification")
    if git("diff", "--cached", "--name-only") == "":
        raise SystemExit("release source must be staged before package construction")
    unstaged = git("diff", "--name-only")
    if unstaged:
        raise SystemExit(f"unstaged release changes exist: {unstaged}")
    output_parent = args.output_parent.resolve()
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".astral-validation-release-v1-", dir=output_parent))
    try:
        (staging / "artifacts").mkdir()
        (staging / "metadata").mkdir()
        (staging / "handoff").mkdir()
        for name, source in sorted(mappings.items()):
            if not source.is_dir() or not (source / "manifest.json").is_file():
                raise RuntimeError(f"bundle missing manifest: {name}:{source}")
            expected = spec["bundles"][name]["expected_manifest_sha256"]
            if sha(source / "manifest.json") != expected:
                raise RuntimeError(f"source manifest mismatch: {name}")
            shutil.copytree(source, staging / "artifacts" / name)
        shutil.copy2(SPEC_PATH, staging / "metadata" / "release-spec.json")
        shutil.copy2(
            REPOSITORY / "docs/research/astral-self-modeling/44-immutable-validation-release-v1.md",
            staging / "handoff" / "RELEASE.md",
        )
        shutil.copy2(
            REPOSITORY / "docs/research/astral-self-modeling/45-independent-validation-handoff.md",
            staging / "handoff" / "INDEPENDENT-VALIDATION.md",
        )
        write_json(staging / "metadata" / "environment.json", environment())
        write_json(staging / "metadata" / "source-inventory.json", source_inventory())
        write_json(
            staging / "metadata" / "build-record.json",
            {
                "release_id": spec["release_id"],
                "git_head_before_release_commit": git("rev-parse", "HEAD"),
                "git_staged_tree": git("write-tree"),
                "source_bundle_paths": {name: str(path) for name, path in sorted(mappings.items())},
                "builder_sha256": sha(HERE),
                "validator_sha256": sha(HERE.with_name("validate_release.py")),
                "claim_ceiling": spec["claim_ceiling"],
            },
        )
        identity = package_manifest(staging)
        destination = output_parent / f"{spec['release_id']}-{identity}"
        if destination.exists():
            raise RuntimeError(f"content-addressed destination already exists: {destination}")
        os.replace(staging, destination)
        print(json.dumps({"package": str(destination), "package_identity": identity}, sort_keys=True))
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
