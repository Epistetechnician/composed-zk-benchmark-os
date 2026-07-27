#!/usr/bin/env python3
"""Verify, clone, and replay the portable Astral review capsule."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from capsule import (
    observed_runtime,
    runtime_differences,
    sha256,
    verify_content_addressed_directory,
    verify_manifest,
    write_json,
)


HERE = Path(__file__).resolve()
CAPSULE = HERE.parents[1]
MANIFEST_NAME = "CAPSULE-MANIFEST.sha256"
EXPECTED_EXTERNAL_GATES = {
    "independent_implementation_replication": "NotRun",
    "reproducibility_reviewer": "NotRun",
    "scientific_reviewer": "NotRun",
    "stage_0c_confirmation": "Blocked",
    "stage_1": "BlockedByStage0C",
}


def run(command: list[str], cwd: Path, environment: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def write_sealed_json(path: Path, value: object) -> str:
    write_json(path, value)
    digest = sha256(path)
    path.with_suffix(path.suffix + ".sha256").write_text(f"{digest}  {path.name}\n")
    return digest


def ensure_new_external_workspace(workspace: Path) -> None:
    if not workspace.is_absolute():
        raise ValueError("workspace path must be absolute")
    if workspace.exists():
        raise ValueError("workspace path already exists")
    try:
        workspace.relative_to(CAPSULE)
    except ValueError:
        return
    raise ValueError("workspace must be outside the capsule")


def verify_capsule(spec: dict[str, str]) -> dict[str, Any]:
    manifest = verify_manifest(CAPSULE, MANIFEST_NAME)
    if CAPSULE.name != f"{spec['capsule_id']}-{manifest['identity']}":
        raise ValueError("capsule content-addressed name mismatch")

    package = CAPSULE / "release" / (
        f"astral-validation-release-v1-{spec['release_package_identity']}"
    )
    package_state = verify_content_addressed_directory(
        package,
        "PACKAGE-MANIFEST.sha256",
        "astral-validation-release-v1",
        spec["release_package_identity"],
    )
    reports = sorted((CAPSULE / "author-report").glob("*.json"))
    if len(reports) != 1 or sha256(reports[0]) != spec["author_report_sha256"]:
        raise ValueError("author report census or digest mismatch")
    expected_sidecar = f"{spec['author_report_sha256']}  {reports[0].name}\n"
    if reports[0].with_suffix(reports[0].suffix + ".sha256").read_text() != expected_sidecar:
        raise ValueError("author report sidecar mismatch")
    report = json.loads(reports[0].read_text())
    if (
        report.get("status") != "local_immutable_validation_passed"
        or report.get("git_tree") != spec["release_tree"]
        or report.get("package", {}).get("package_identity")
        != spec["release_package_identity"]
        or report.get("claim_ceiling") != spec["claim_ceiling"]
        or report.get("external_gates") != EXPECTED_EXTERNAL_GATES
    ):
        raise ValueError("author report content binding mismatch")
    return {
        "capsule": manifest,
        "package": package_state,
        "package_path": package,
        "author_report_path": reports[0],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--allow-environment-drift", action="store_true")
    args = parser.parse_args()

    spec = json.loads((CAPSULE / "metadata/capsule-spec.json").read_text())
    capsule_state = verify_capsule(spec)
    if not args.workspace.is_absolute():
        raise ValueError("workspace path must be absolute")
    workspace = args.workspace.resolve()
    ensure_new_external_workspace(workspace)
    workspace.mkdir(mode=0o700, parents=True)

    expected_runtime = json.loads(
        (CAPSULE / "metadata/runtime-contract.json").read_text()
    )
    actual_runtime = observed_runtime()
    differences = runtime_differences(expected_runtime, actual_runtime)
    environment_state = {
        "actual": actual_runtime,
        "differences": differences,
        "exact_match": not differences,
        "override_used": bool(differences and args.allow_environment_drift),
    }
    write_sealed_json(workspace / "environment-observation.json", environment_state)
    if differences and not args.allow_environment_drift:
        write_sealed_json(
            workspace / "capsule-run.json",
            {
                "status": "EnvironmentMismatch",
                "claim_ceiling": spec["claim_ceiling"],
                "independence_status": "Unasserted",
                "environment_differences": differences,
            },
        )
        print(
            json.dumps(
                {"status": "EnvironmentMismatch", "workspace": str(workspace)},
                sort_keys=True,
            )
        )
        return 2

    repository = workspace / "repository"
    bundle = CAPSULE / "source/astral-release.bundle"
    clone = run(["git", "clone", "--no-checkout", str(bundle), str(repository)], workspace)
    bundle_verification = run(
        ["git", "bundle", "verify", str(bundle)], repository
    )
    checkout = run(
        ["git", "checkout", "--detach", spec["release_commit"]], repository
    )
    commit = run(["git", "rev-parse", "HEAD"], repository)["stdout"]
    tree = run(["git", "rev-parse", "HEAD^{tree}"], repository)["stdout"]
    status = run(["git", "status", "--porcelain"], repository)["stdout"]
    if (
        commit != spec["release_commit"]
        or tree != spec["release_tree"]
        or status
    ):
        raise ValueError("clean-clone release identity mismatch")

    report = workspace / "reviewer-report.json"
    environment = dict(os.environ)
    environment["CARGO_NET_OFFLINE"] = "true"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    validation = run(
        [
            sys.executable,
            str(
                repository
                / "tools/astral-validation-release-v1/validate_release.py"
            ),
            "--package",
            str(capsule_state["package_path"]),
            "--report",
            str(report),
        ],
        repository,
        environment,
    )
    reviewer_report = json.loads(report.read_text())
    if (
        reviewer_report.get("status") != "local_immutable_validation_passed"
        or reviewer_report.get("git_tree") != spec["release_tree"]
        or reviewer_report.get("package", {}).get("package_identity")
        != spec["release_package_identity"]
        or reviewer_report.get("claim_ceiling") != spec["claim_ceiling"]
        or reviewer_report.get("external_gates") != EXPECTED_EXTERNAL_GATES
    ):
        raise ValueError("reviewer report binding mismatch")
    report_digest = sha256(report)
    expected_report_sidecar = f"{report_digest}  {report.name}\n"
    if report.with_suffix(report.suffix + ".sha256").read_text() != expected_report_sidecar:
        raise ValueError("reviewer report sidecar mismatch")

    reviews = workspace / "reviews"
    reviews.mkdir()
    for template in sorted((CAPSULE / "reviews").glob("*.template.json")):
        target = reviews / template.name.replace(".template", "")
        shutil.copy2(template, target)

    run_state = {
        "status": "CapsuleReplayPassed",
        "claim_ceiling": spec["claim_ceiling"],
        "independence_status": "Unasserted",
        "capsule_identity": capsule_state["capsule"]["identity"],
        "release_commit": commit,
        "release_tree": tree,
        "release_package_identity": spec["release_package_identity"],
        "reviewer_report_sha256": report_digest,
        "environment_differences": differences,
        "external_gates": reviewer_report["external_gates"],
        "commands": {
            "bundle_verification": bundle_verification,
            "checkout": checkout,
            "clone": clone,
            "validation": validation,
        },
    }
    run_digest = write_sealed_json(workspace / "capsule-run.json", run_state)
    print(
        json.dumps(
            {
                "capsule_run_sha256": run_digest,
                "reviewer_report_sha256": report_digest,
                "status": run_state["status"],
                "workspace": str(workspace),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
