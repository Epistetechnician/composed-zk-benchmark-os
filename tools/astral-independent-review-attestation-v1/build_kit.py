#!/usr/bin/env python3
"""Build a small content-addressed kit for signed Astral reviews."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
SPEC_PATH = HERE.with_name("gate-spec.json")
KIT_ID = "astral-independent-review-attestation-kit-v1"
MANIFEST_NAME = "KIT-MANIFEST.sha256"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capsule", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    if git("status", "--porcelain"):
        raise SystemExit("attestation-kit builder worktree must be clean")
    spec = json.loads(SPEC_PATH.read_text())
    capsule = args.capsule.resolve()
    capsule_manifest = capsule / "CAPSULE-MANIFEST.sha256"
    if (
        capsule.is_symlink()
        or not capsule.is_dir()
        or capsule_manifest.is_symlink()
        or not capsule_manifest.is_file()
        or sha256_file(capsule_manifest) != spec["capsule_identity"]
        or capsule.name
        != f"astral-independent-review-capsule-v1-{spec['capsule_identity']}"
    ):
        raise SystemExit("capsule binding mismatch")
    output_parent = args.output_parent.resolve()
    try:
        output_parent.relative_to(REPOSITORY)
    except ValueError:
        pass
    else:
        raise SystemExit("kit output parent must be outside the repository")
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{KIT_ID}-", dir=output_parent))
    try:
        tools = staging / "tools"
        metadata = staging / "metadata"
        templates = staging / "templates"
        for directory in (tools, metadata, templates):
            directory.mkdir()
        for name in (
            "canonicalize_json.py",
            "prepare_review.py",
            "review_gate.py",
            "verify_review_gate.py",
        ):
            shutil.copy2(HERE.with_name(name), tools / name)
        shutil.copy2(SPEC_PATH, metadata / SPEC_PATH.name)
        shutil.copy2(
            HERE.with_name("reviewer-registry.template.json"),
            templates / "reviewer-registry.template.json",
        )
        shutil.copy2(
            REPOSITORY
            / "docs/research/astral-self-modeling/47-signed-independent-review-attestation-gate-v1.md",
            staging / "README.md",
        )
        write_json(
            metadata / "capsule-binding.json",
            {
                "capsule_identity": spec["capsule_identity"],
                "capsule_manifest_sha256": sha256_file(capsule_manifest),
                "claim_ceiling": spec["claim_ceiling"],
                "release_commit": spec["release_commit"],
                "release_package_identity": spec["release_package_identity"],
                "release_tree": spec["release_tree"],
            },
        )
        write_json(
            metadata / "build-record.json",
            {
                "builder_commit": git("rev-parse", "HEAD"),
                "builder_tree": git("rev-parse", "HEAD^{tree}"),
                "capsule_identity": spec["capsule_identity"],
                "claim_ceiling": spec["claim_ceiling"],
                "private_keys_included": False,
            },
        )
        rows = []
        for path in sorted(candidate for candidate in staging.rglob("*") if candidate.is_file()):
            rows.append(f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}")
        manifest = "\n".join(rows) + "\n"
        (staging / MANIFEST_NAME).write_text(manifest)
        identity = hashlib.sha256(manifest.encode()).hexdigest()
        destination = output_parent / f"{KIT_ID}-{identity}"
        if destination.exists():
            raise SystemExit("content-addressed attestation kit already exists")
        os.replace(staging, destination)
        print(
            json.dumps(
                {"kit": str(destination), "kit_identity": identity},
                sort_keys=True,
            )
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
