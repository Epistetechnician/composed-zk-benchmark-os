#!/usr/bin/env python3
"""Build the content-addressed V24 admin and reviewer authorization kit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from review_auth import canonical_bytes, sha256_file, validate_admin_policy


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
KIT_ID = "astral-v24-review-authorization-kit-v2"
MANIFEST_NAME = "KIT-MANIFEST.sha256"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def manifest_identity(root: Path, manifest_name: str, prefix: str) -> str:
    manifest = root / manifest_name
    if root.is_symlink() or not root.is_dir() or manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"{prefix} root or manifest is invalid")
    rows = {}
    for line in manifest.read_text().splitlines():
        expected, separator, relative = line.partition("  ")
        path = Path(relative)
        if (
            not separator
            or not SHA256.fullmatch(expected)
            or path.is_absolute()
            or ".." in path.parts
            or relative in rows
        ):
            raise ValueError(f"{prefix} manifest row is invalid")
        rows[relative] = expected
    if list(rows) != sorted(rows):
        raise ValueError(f"{prefix} manifest rows are not sorted")
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{prefix} symlink is forbidden")
        if path.is_file() and path != manifest:
            actual.add(path.relative_to(root).as_posix())
    if actual != set(rows):
        raise ValueError(f"{prefix} manifest census mismatch")
    for relative, expected in rows.items():
        if sha256_file(root / relative) != expected:
            raise ValueError(f"{prefix} manifest digest mismatch: {relative}")
    identity = sha256_file(manifest)
    if root.name != f"{prefix}-{identity}":
        raise ValueError(f"{prefix} content-addressed name mismatch")
    return identity


def require_external(path: Path) -> None:
    try:
        path.relative_to(REPOSITORY)
    except ValueError:
        return
    raise ValueError("review-kit output must be outside the repository")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capsule", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--author-report", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    if git("status", "--porcelain"):
        raise SystemExit("review-kit builder worktree must be clean")
    capsule = args.capsule.resolve()
    release = args.release.resolve()
    capsule_identity = manifest_identity(
        capsule, "CAPSULE-MANIFEST.sha256", "astral-v24-independent-review-capsule-v2"
    )
    release_identity = manifest_identity(
        release, "RELEASE-MANIFEST.sha256", "astral-v24-validation-release-v2"
    )
    capsule_spec = json.loads((capsule / "metadata/capsule-spec.json").read_text())
    release_spec = json.loads((release / "metadata/release-spec.json").read_text())
    report = args.author_report.resolve()
    report_sha256 = sha256_file(report)
    if (
        capsule_spec["release_identity"] != release_identity
        or capsule_spec["author_report_sha256"] != report_sha256
        or capsule_spec["source_commit"] != release_spec["source_commit"]
    ):
        raise SystemExit("release, capsule, and report binding mismatch")
    policy = json.loads(HERE.with_name("admin-policy.json").read_text())
    validate_admin_policy(policy)
    policy_sha256 = hashlib.sha256(canonical_bytes(policy)).hexdigest()
    gate_spec = {
        "admin_policy_sha256": policy_sha256,
        "artifact_identity": release_spec["artifact_identity"],
        "author_report_sha256": report_sha256,
        "capsule_identity": capsule_identity,
        "claim_ceiling": release_spec["claim_ceiling"],
        "external_states": release_spec["external_states"],
        "release_identity": release_identity,
        "required_roles": ["artifact_reproducibility", "scientific_validity"],
        "required_scientific_sections": [
            "assessment_sealing",
            "claim_ceiling",
            "control_strength",
            "corpus_overlap_and_leakage",
            "preregistration_chronology",
            "statistics_and_uncertainty",
            "stopping_and_selection_rules",
        ],
        "review_namespace": "astral-v24-independent-review-v2",
        "schema_version": 2,
        "source_commit": release_spec["source_commit"],
        "source_tree": release_spec["source_tree"],
    }
    output_parent = args.output_parent.resolve()
    require_external(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".astral-v24-review-kit-v2-", dir=output_parent))
    try:
        for name in ("metadata", "templates", "tools"):
            (staging / name).mkdir()
        for name in (
            "canonicalize_json.py",
            "prepare_review.py",
            "review_auth.py",
            "verify_kit.py",
            "verify_review_gate.py",
        ):
            shutil.copy2(HERE.with_name(name), staging / "tools" / name)
        shutil.copy2(
            HERE.with_name("reviewer-registry.template.json"),
            staging / "templates/reviewer-registry.template.json",
        )
        (staging / "metadata/admin-policy.json").write_bytes(canonical_bytes(policy))
        (staging / "metadata/gate-spec.json").write_bytes(canonical_bytes(gate_spec))
        shutil.copy2(
            REPOSITORY
            / "docs/research/astral-self-modeling/50-v24-independent-validation-release-v2-spec.md",
            staging / "README.md",
        )
        (staging / "ADMIN-SIGNING.txt").write_text(
            "ssh-keygen -Y sign -f <admin-private-key> "
            "-n astral-v24-review-admin-v2 reviewer-registry.json\n"
        )
        rows = []
        for path in sorted(candidate for candidate in staging.rglob("*") if candidate.is_file()):
            rows.append(f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}")
        manifest = "\n".join(rows) + "\n"
        (staging / MANIFEST_NAME).write_text(manifest)
        identity = hashlib.sha256(manifest.encode()).hexdigest()
        destination = output_parent / f"{KIT_ID}-{identity}"
        if destination.exists():
            raise RuntimeError("content-addressed review kit already exists")
        os.replace(staging, destination)
        print(
            json.dumps(
                {
                    "admin_id": policy["admin_id"],
                    "kit": str(destination),
                    "kit_identity": identity,
                },
                sort_keys=True,
            )
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
