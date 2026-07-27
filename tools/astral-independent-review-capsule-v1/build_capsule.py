#!/usr/bin/env python3
"""Build the portable, content-addressed Astral independent-review capsule."""

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
SPEC_PATH = HERE.with_name("capsule-spec.json")
MANIFEST_NAME = "CAPSULE-MANIFEST.sha256"


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def require_external_output(path: Path) -> None:
    try:
        path.relative_to(REPOSITORY)
    except ValueError:
        return
    raise ValueError("capsule output parent must be outside the repository")


def verify_author_report(report: Path, spec: dict[str, str]) -> dict[str, object]:
    if report.is_symlink() or not report.is_file():
        raise ValueError("author report must be a real file")
    if sha256(report) != spec["author_report_sha256"]:
        raise ValueError("author report digest mismatch")
    sidecar = report.with_suffix(report.suffix + ".sha256")
    expected_sidecar = f"{spec['author_report_sha256']}  {report.name}\n"
    if sidecar.is_symlink() or not sidecar.is_file() or sidecar.read_text() != expected_sidecar:
        raise ValueError("author report sidecar mismatch")
    content = json.loads(report.read_text())
    if (
        content.get("status") != "local_immutable_validation_passed"
        or content.get("claim_ceiling") != spec["claim_ceiling"]
        or content.get("git_tree") != spec["release_tree"]
        or content.get("package", {}).get("package_identity")
        != spec["release_package_identity"]
    ):
        raise ValueError("author report binding mismatch")
    return content


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-package", required=True, type=Path)
    parser.add_argument("--author-report", required=True, type=Path)
    parser.add_argument("--output-parent", required=True, type=Path)
    args = parser.parse_args()

    if git("status", "--porcelain"):
        raise SystemExit("capsule builder worktree must be clean")
    spec = json.loads(SPEC_PATH.read_text())
    release_commit = git("rev-parse", spec["release_ref"])
    if release_commit != spec["release_commit"]:
        raise SystemExit("release ref does not resolve to the frozen commit")
    if git("rev-parse", f"{release_commit}^{{tree}}") != spec["release_tree"]:
        raise SystemExit("release tree does not match the capsule specification")

    package = args.release_package.resolve()
    verify_content_addressed_directory(
        package,
        "PACKAGE-MANIFEST.sha256",
        "astral-validation-release-v1",
        spec["release_package_identity"],
    )
    author_report = args.author_report.resolve()
    verify_author_report(author_report, spec)

    output_parent = args.output_parent.resolve()
    require_external_output(output_parent)
    output_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".astral-independent-review-capsule-v1-", dir=output_parent)
    )
    try:
        source_directory = staging / "source"
        release_directory = staging / "release"
        report_directory = staging / "author-report"
        metadata_directory = staging / "metadata"
        tools_directory = staging / "tools"
        reviews_directory = staging / "reviews"
        for directory in (
            source_directory,
            release_directory,
            report_directory,
            metadata_directory,
            tools_directory,
            reviews_directory,
        ):
            directory.mkdir()

        bundle = source_directory / "astral-release.bundle"
        subprocess.run(
            ["git", "bundle", "create", str(bundle), spec["release_ref"]],
            cwd=REPOSITORY,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "bundle", "verify", str(bundle)],
            cwd=REPOSITORY,
            check=True,
            capture_output=True,
            text=True,
        )

        shutil.copytree(package, release_directory / package.name)
        shutil.copy2(author_report, report_directory / author_report.name)
        shutil.copy2(
            author_report.with_suffix(author_report.suffix + ".sha256"),
            report_directory / f"{author_report.name}.sha256",
        )
        shutil.copy2(SPEC_PATH, metadata_directory / SPEC_PATH.name)
        shutil.copy2(
            REPOSITORY
            / "docs/research/astral-self-modeling/46-independent-review-capsule-v1.md",
            staging / "README.md",
        )
        for name in ("capsule.py", "run_capsule.py"):
            shutil.copy2(HERE.with_name(name), tools_directory / name)
        for name in (
            "reproducibility-review.template.json",
            "scientific-review.template.json",
        ):
            shutil.copy2(HERE.with_name(name), reviews_directory / name)

        release_environment = json.loads(
            (package / "metadata/environment.json").read_text()
        )
        runtime = observed_runtime()
        runtime["python"] = release_environment["python"]
        runtime["platform"] = release_environment["platform"]
        runtime["machine"] = release_environment["machine"]
        runtime["processor"] = release_environment["processor"]
        runtime["packages"] = release_environment["packages"]
        write_json(metadata_directory / "runtime-contract.json", runtime)
        requirements = "\n".join(
            f"{name}=={version}"
            for name, version in sorted(release_environment["packages"].items())
            if version != "absent"
        )
        (metadata_directory / "python-requirements.txt").write_text(requirements + "\n")
        write_json(
            metadata_directory / "build-record.json",
            {
                "author_report_sha256": spec["author_report_sha256"],
                "capsule_builder_commit": git("rev-parse", "HEAD"),
                "capsule_builder_tree": git("rev-parse", "HEAD^{tree}"),
                "claim_ceiling": spec["claim_ceiling"],
                "release_commit": release_commit,
                "release_package_identity": spec["release_package_identity"],
                "release_tree": spec["release_tree"],
                "source_bundle_sha256": sha256(bundle),
            },
        )
        identity = write_manifest(staging, MANIFEST_NAME)
        destination = output_parent / f"{spec['capsule_id']}-{identity}"
        if destination.exists():
            raise RuntimeError(f"content-addressed destination exists: {destination}")
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
