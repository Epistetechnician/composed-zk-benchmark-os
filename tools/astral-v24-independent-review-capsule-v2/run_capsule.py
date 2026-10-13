#!/usr/bin/env python3
"""Verify, clone, and replay the portable Astral V24 review capsule."""

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


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    environment = dict(os.environ)
    environment["CARGO_NET_OFFLINE"] = "true"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
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


def ensure_new_workspace(workspace: Path) -> None:
    if not workspace.is_absolute() or workspace.exists():
        raise ValueError("workspace must be a new absolute path")
    try:
        workspace.relative_to(CAPSULE)
    except ValueError:
        return
    raise ValueError("workspace must be outside the capsule")


def verify_capsule(spec: dict[str, Any]) -> dict[str, Any]:
    state = verify_manifest(CAPSULE, MANIFEST_NAME)
    if CAPSULE.name != f"{spec['capsule_id']}-{state['identity']}":
        raise ValueError("capsule content-addressed name mismatch")
    release = CAPSULE / "release" / f"{spec['release_id']}-{spec['release_identity']}"
    release_state = verify_content_addressed_directory(
        release,
        "RELEASE-MANIFEST.sha256",
        spec["release_id"],
        spec["release_identity"],
    )
    reports = [path for path in (CAPSULE / "author-report").glob("*.json")]
    if len(reports) != 1 or sha256(reports[0]) != spec["author_report_sha256"]:
        raise ValueError("author report binding mismatch")
    if reports[0].with_suffix(reports[0].suffix + ".sha256").read_text() != (
        f"{spec['author_report_sha256']}  {reports[0].name}\n"
    ):
        raise ValueError("author report sidecar mismatch")
    return {
        "capsule": state,
        "release": release_state,
        "release_path": release,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--allow-environment-drift", action="store_true")
    args = parser.parse_args()
    spec = json.loads((CAPSULE / "metadata/capsule-spec.json").read_text())
    state = verify_capsule(spec)
    workspace = args.workspace.resolve()
    ensure_new_workspace(workspace)
    workspace.mkdir(mode=0o700, parents=True)
    expected_runtime = json.loads((CAPSULE / "metadata/runtime-contract.json").read_text())
    actual_runtime = observed_runtime()
    differences = runtime_differences(expected_runtime, actual_runtime)
    write_sealed_json(
        workspace / "environment-observation.json",
        {
            "actual": actual_runtime,
            "differences": differences,
            "exact_match": not differences,
            "override_used": bool(differences and args.allow_environment_drift),
        },
    )
    if differences and not args.allow_environment_drift:
        write_sealed_json(
            workspace / "capsule-run.json",
            {
                "claim_ceiling": spec["claim_ceiling"],
                "independence_status": "Unasserted",
                "status": "EnvironmentMismatch",
            },
        )
        print(json.dumps({"status": "EnvironmentMismatch"}, sort_keys=True))
        return 2

    repository = workspace / "repository"
    bundle = CAPSULE / "source/astral-v24-release.bundle"
    clone = run(["git", "clone", "--no-checkout", str(bundle), str(repository)], workspace)
    bundle_check = run(["git", "bundle", "verify", str(bundle)], repository)
    checkout = run(["git", "checkout", "--detach", spec["source_commit"]], repository)
    if (
        run(["git", "rev-parse", "HEAD"], repository)["stdout"] != spec["source_commit"]
        or run(["git", "rev-parse", "HEAD^{tree}"], repository)["stdout"]
        != spec["source_tree"]
        or run(["git", "status", "--porcelain"], repository)["stdout"]
    ):
        raise ValueError("clean clone identity mismatch")
    report = workspace / "reviewer-report.json"
    validation = run(
        [
            sys.executable,
            str(CAPSULE / "tools/release_validator/validate_release.py"),
            "--package",
            str(state["release_path"]),
            "--report",
            str(report),
            "--source-repository",
            str(repository),
            "--in-detached-worker",
        ],
        repository,
    )
    report_value = json.loads(report.read_text())
    if (
        report_value.get("status") != "V24ImmutableValidationPassed"
        or report_value.get("release", {}).get("identity") != spec["release_identity"]
        or report_value.get("source_commit") != spec["source_commit"]
        or report_value.get("source_tree") != spec["source_tree"]
        or report_value.get("external_states") != spec["external_states"]
    ):
        raise ValueError("reviewer report content mismatch")
    report_digest = sha256(report)
    reviews = workspace / "reviews"
    reviews.mkdir()
    for template in sorted((CAPSULE / "reviews").glob("*.template.json")):
        shutil.copy2(template, reviews / template.name.replace(".template", ""))
    run_state = {
        "capsule_identity": state["capsule"]["identity"],
        "claim_ceiling": spec["claim_ceiling"],
        "commands": {
            "bundle_verification": bundle_check,
            "checkout": checkout,
            "clone": clone,
            "validation": validation,
        },
        "environment_differences": differences,
        "external_states": spec["external_states"],
        "independence_status": "Unasserted",
        "release_identity": spec["release_identity"],
        "reviewer_report_sha256": report_digest,
        "source_commit": spec["source_commit"],
        "source_tree": spec["source_tree"],
        "status": "V24CapsuleReplayPassed",
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
