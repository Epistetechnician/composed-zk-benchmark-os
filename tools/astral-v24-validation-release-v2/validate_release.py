#!/usr/bin/env python3
"""Fail-closed validator for the immutable Astral V24 release."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from release import (
    observed_runtime,
    runtime_differences,
    sha256,
    verify_content_addressed_directory,
    verify_json_manifest_directory,
    verify_model_inventory,
)


HERE = Path(__file__).resolve()
DEFAULT_REPOSITORY = HERE.parents[2]
MANIFEST_NAME = "RELEASE-MANIFEST.sha256"


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


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def verify_source(repository: Path, package: Path, spec: dict[str, Any]) -> int:
    commit = run(["git", "rev-parse", "HEAD"], repository)["stdout"]
    tree = run(["git", "rev-parse", "HEAD^{tree}"], repository)["stdout"]
    status = run(["git", "status", "--porcelain"], repository)["stdout"]
    if commit != spec["source_commit"] or tree != spec["source_tree"] or status:
        raise ValueError("frozen source checkout identity mismatch")
    retained = json.loads((package / "metadata/source-inventory.json").read_text())
    for relative, expected in retained.items():
        path = repository / relative
        if not path.is_file() or sha256(path) != expected:
            raise ValueError(f"source inventory mismatch: {relative}")
    return len(retained)


def verify_v24(
    repository: Path, package: Path, spec: dict[str, Any]
) -> dict[str, Any]:
    artifact = package / "artifact" / f"astral-v24-{spec['artifact_identity']}"
    artifact_state = verify_json_manifest_directory(
        artifact,
        "manifest.json",
        "astral-v24",
        spec["artifact_identity"],
    )
    retained_model = json.loads((artifact / "model-inventory.json").read_text())
    model_count = verify_model_inventory(package / "model/qwen", retained_model)

    validator = import_module(
        "astral_v24_release_validator",
        repository / "tools/astral-perturbation-readout-v24/validator_v24.py",
    )
    retained_environment = json.loads((artifact / "environment-inventory.json").read_text())
    validator.V24.environment_inventory = lambda: retained_environment
    validator.V24.V17.model_inventory = lambda _path: retained_model
    validation = validator.validate(artifact)
    if (
        validation["classification"] != spec["expected_classification"]
        or validation["independently_verified"] != "NotRun"
        or validation["manifest_sha256"] != spec["artifact_identity"]
    ):
        raise ValueError("V24 validator disposition mismatch")
    return {
        "artifact": artifact_state,
        "model_file_count": model_count,
        "v24_validation": validation,
    }


def verify_ledger(repository: Path, spec: dict[str, Any]) -> None:
    ledger = (
        repository / "docs/research/astral-self-modeling/03-claim-ledger.md"
    ).read_text()
    lines = [
        line
        for line in ledger.splitlines()
        if "| C044 | In test | Not refuted |" in line
    ]
    if (
        len(lines) != 1
        or spec["artifact_identity"] not in lines[0]
        or "independent review `NotRun`" not in lines[0]
    ):
        raise ValueError("V24 claim-ledger correspondence mismatch")


def validate_worker(package: Path, report: Path, repository: Path) -> dict[str, Any]:
    package_state = verify_content_addressed_directory(
        package, MANIFEST_NAME, "astral-v24-validation-release-v2"
    )
    spec = json.loads((package / "metadata/release-spec.json").read_text())
    if (
        spec["schema_version"] != 2
        or spec["claim_ceiling"] != "LocalAuthorDevelopmentPerturbationReadout"
    ):
        raise ValueError("release specification boundary mismatch")
    source_count = verify_source(repository, package, spec)
    v24 = verify_v24(repository, package, spec)
    verify_ledger(repository, spec)
    expected_runtime = json.loads((package / "metadata/runtime-contract.json").read_text())
    actual_runtime = observed_runtime()
    differences = runtime_differences(expected_runtime, actual_runtime)
    test_paths = sorted(
        str(path.relative_to(repository))
        for directory in (repository / "tools").glob("astral-*")
        for path in directory.glob("tests")
        if path.is_dir()
    )
    structural = run([sys.executable, "-m", "pytest", "-q", *test_paths], repository)
    rust = run(
        ["cargo", "test", "-p", "astral-stage0-protocol", "--locked"],
        repository,
    )
    result = {
        "status": "V24ImmutableValidationPassed",
        "claim_ceiling": spec["claim_ceiling"],
        "release": package_state,
        "source_commit": spec["source_commit"],
        "source_tree": spec["source_tree"],
        "source_file_count": source_count,
        "v24": v24,
        "runtime": {
            "actual": actual_runtime,
            "differences": differences,
            "exact_match": not differences,
        },
        "structural_tests": structural,
        "rust_protocol_tests": rust,
        "external_states": spec["external_states"],
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    digest = sha256(report)
    report.with_suffix(report.suffix + ".sha256").write_text(
        f"{digest}  {report.name}\n"
    )
    return {"report": str(report), "report_sha256": digest, "status": result["status"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--source-repository", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--in-detached-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    package = args.package.resolve()
    report = args.report.resolve()
    if report.exists() or report.with_suffix(report.suffix + ".sha256").exists():
        raise SystemExit("report destination already exists")
    if args.in_detached_worker:
        if args.source_repository is None:
            raise SystemExit("detached worker source repository is required")
        output = validate_worker(package, report, args.source_repository.resolve())
        print(json.dumps(output, sort_keys=True))
        return 0

    repository = DEFAULT_REPOSITORY
    if run(["git", "status", "--porcelain"], repository)["stdout"]:
        raise SystemExit("validation launcher worktree must be clean")
    package_spec = json.loads((package / "metadata/release-spec.json").read_text())
    parent = Path(tempfile.mkdtemp(prefix="astral-v24-validation-v2-"))
    worker = parent / "source"
    try:
        run(
            [
                "git",
                "worktree",
                "add",
                "--detach",
                str(worker),
                package_spec["source_commit"],
            ],
            repository,
        )
        command = [
            sys.executable,
            str(HERE),
            "--package",
            str(package),
            "--report",
            str(report),
            "--source-repository",
            str(worker),
            "--in-detached-worker",
        ]
        completed = subprocess.run(command, cwd=repository)
        return completed.returncode
    finally:
        if worker.exists():
            run(["git", "worktree", "remove", "--force", str(worker)], repository)
        shutil.rmtree(parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
