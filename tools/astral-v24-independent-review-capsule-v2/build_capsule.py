#!/usr/bin/env python3
"""Build a portable content-addressed V24 independent-review capsule."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from capsule import (
    observed_runtime,
    sha256,
    verify_content_addressed_directory,
    write_json,
    write_manifest,
)


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
CAPSULE_ID = "astral-v24-independent-review-capsule-v2"
MANIFEST_NAME = "CAPSULE-MANIFEST.sha256"


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def require_external(path: Path) -> None:
    try:
        path.relative_to(REPOSITORY)
    except ValueError:
        return
    raise ValueError("capsule output must be outside the repository")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--author-report", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()
    if git("status", "--porcelain"):
        raise SystemExit("capsule builder worktree must be clean")
    release = args.release.resolve()
    release_manifest = release / "RELEASE-MANIFEST.sha256"
    release_identity = sha256(release_manifest)
    release_state = verify_content_addressed_directory(
        release,
        release_manifest.name,
        "astral-v24-validation-release-v2",
        release_identity,
    )
    release_spec = json.loads((release / "metadata/release-spec.json").read_text())
    report = args.author_report.resolve()
    report_digest = sha256(report)
    if report.with_suffix(report.suffix + ".sha256").read_text() != f"{report_digest}  {report.name}\n":
        raise SystemExit("author report sidecar mismatch")
    report_value = json.loads(report.read_text())
    if (
        report_value.get("status") != "V24ImmutableValidationPassed"
        or report_value.get("release", {}).get("identity") != release_identity
        or report_value.get("source_commit") != release_spec["source_commit"]
        or report_value.get("source_tree") != release_spec["source_tree"]
        or report_value.get("external_states") != release_spec["external_states"]
    ):
        raise SystemExit("author report content mismatch")

    output_parent = args.output_parent.resolve()
    require_external(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".astral-v24-capsule-v2-", dir=output_parent))
    try:
        for name in ("author-report", "metadata", "release", "reviews", "source", "tools"):
            (staging / name).mkdir()
        shutil.copytree(release, staging / "release" / release.name)
        shutil.copy2(report, staging / "author-report" / report.name)
        shutil.copy2(
            report.with_suffix(report.suffix + ".sha256"),
            staging / "author-report" / (report.name + ".sha256"),
        )
        bundle = staging / "source/astral-v24-release.bundle"
        subprocess.run(
            ["git", "bundle", "create", str(bundle), "HEAD"],
            cwd=REPOSITORY,
            check=True,
            capture_output=True,
            text=True,
        )
        for name in ("capsule.py", "run_capsule.py"):
            shutil.copy2(HERE.with_name(name), staging / "tools" / name)
        validator_directory = staging / "tools/release_validator"
        validator_directory.mkdir()
        for name in ("release.py", "validate_release.py"):
            shutil.copy2(
                REPOSITORY / "tools/astral-v24-validation-release-v2" / name,
                validator_directory / name,
            )
        for name in (
            "artifact-reproducibility.decision.template.json",
            "scientific-validity.decision.template.json",
        ):
            shutil.copy2(HERE.with_name(name), staging / "reviews" / name)
        shutil.copy2(
            REPOSITORY
            / "docs/research/astral-self-modeling/50-v24-independent-validation-release-v2-spec.md",
            staging / "README.md",
        )
        capsule_spec = {
            "author_report_sha256": report_digest,
            "capsule_id": CAPSULE_ID,
            "claim_ceiling": release_spec["claim_ceiling"],
            "external_states": release_spec["external_states"],
            "release_id": release_spec["release_id"],
            "release_identity": release_identity,
            "schema_version": 2,
            "source_commit": release_spec["source_commit"],
            "source_tree": release_spec["source_tree"],
        }
        write_json(staging / "metadata/capsule-spec.json", capsule_spec)
        write_json(staging / "metadata/runtime-contract.json", observed_runtime())
        write_json(
            staging / "metadata/build-record.json",
            {
                "author_report_sha256": report_digest,
                "builder_commit": git("rev-parse", "HEAD"),
                "builder_tree": git("rev-parse", "HEAD^{tree}"),
                "claim_ceiling": release_spec["claim_ceiling"],
                "release_file_count": release_state["file_count"],
                "release_identity": release_identity,
                "source_bundle_sha256": sha256(bundle),
            },
        )
        identity = write_manifest(staging, MANIFEST_NAME)
        destination = output_parent / f"{CAPSULE_ID}-{identity}"
        if destination.exists():
            raise RuntimeError("content-addressed capsule already exists")
        os.replace(staging, destination)
        print(
            json.dumps(
                {"capsule": str(destination), "capsule_identity": identity},
                sort_keys=True,
            )
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
