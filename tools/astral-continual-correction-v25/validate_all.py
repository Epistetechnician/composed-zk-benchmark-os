#!/usr/bin/env python3
"""Holistic, fail-closed Astral claim-validation pipeline."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

import v25 as V25
import validator_v25 as V25_VALIDATOR


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
LEDGER = REPOSITORY / "docs/research/astral-self-modeling/03-claim-ledger.md"
CLAIM_CONTRACT = HERE / "claim-contract.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CLAIM_ID = re.compile(r"^C\d{3}$")


def run(command: list[str], cwd: Path = REPOSITORY) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "CARGO_NET_OFFLINE": "true",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
        "stdout": completed.stdout.strip(),
    }


def parse_claim_statuses(text: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    current: dict[str, str] = {}
    history: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("| C"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not CLAIM_ID.fullmatch(cells[0]):
            continue
        if len(cells) == 8:
            status = cells[6]
        elif len(cells) == 7:
            status = cells[2]
        elif len(cells) == 5:
            status = cells[3]
        else:
            raise ValueError(f"unsupported claim-ledger row shape: {cells[0]}")
        history.setdefault(cells[0], []).append(status)
        current[cells[0]] = status
    return current, history


def verify_claim_contract(contract: dict[str, Any]) -> tuple[dict[str, str], dict[str, list[str]]]:
    current, history = parse_claim_statuses(LEDGER.read_text())
    expected = contract["expected_claim_statuses"]
    if list(expected) != [f"C{index:03d}" for index in range(1, len(expected) + 1)]:
        raise ValueError("claim contract IDs are not a complete ordered census")
    if current != expected:
        missing = sorted(set(expected) - set(current))
        extra = sorted(set(current) - set(expected))
        mismatched = {
            claim: {"expected": expected[claim], "actual": current.get(claim)}
            for claim in expected
            if current.get(claim) != expected[claim]
        }
        raise ValueError(
            f"claim contract mismatch: missing={missing}, extra={extra}, mismatched={mismatched}"
        )
    return current, history


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return value == path.as_posix() and value not in ("", ".") and not path.is_absolute() and ".." not in path.parts


def verify_sha_manifest(root: Path, manifest_name: str, prefix: str, identity: str) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir() or root.name != f"{prefix}-{identity}":
        raise ValueError(f"invalid content-addressed release root: {prefix}")
    manifest = root / manifest_name
    if manifest.is_symlink() or not manifest.is_file() or V25.sha256(manifest) != identity:
        raise ValueError(f"release manifest identity mismatch: {prefix}")
    rows: dict[str, str] = {}
    for line in manifest.read_text().splitlines():
        expected, separator, relative = line.partition("  ")
        if not separator or not SHA256.fullmatch(expected) or not safe_relative(relative) or relative in rows:
            raise ValueError(f"invalid release manifest row: {prefix}")
        rows[relative] = expected
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"release symlink forbidden: {prefix}")
        if path.is_file() and path != manifest:
            actual.add(path.relative_to(root).as_posix())
    if actual != set(rows):
        raise ValueError(f"release manifest census mismatch: {prefix}")
    for relative, expected in rows.items():
        if V25.sha256(root / relative) != expected:
            raise ValueError(f"release digest mismatch: {prefix}:{relative}")
    return {"file_count": len(rows), "identity": identity, "integrity": "Passed"}


def resolve_commit_for_tree(tree: str) -> str:
    log = run(["git", "log", "--all", "--format=%H %T"])["stdout"]
    matches = [line.split()[0] for line in log.splitlines() if line.split()[1] == tree]
    if not matches:
        raise ValueError("no local commit matches legacy release tree")
    return matches[0]


def validate_legacy_release(package: Path, report: Path) -> dict[str, Any]:
    build = json.loads((package / "metadata/build-record.json").read_text())
    commit = resolve_commit_for_tree(build["git_staged_tree"])
    parent = Path(tempfile.mkdtemp(prefix="astral-v25-legacy-worker-"))
    worker = parent / "source"
    try:
        run(["git", "worktree", "add", "--detach", str(worker), commit])
        outcome = run(
            [
                sys.executable,
                str(worker / "tools/astral-validation-release-v1/validate_release.py"),
                "--package",
                str(package),
                "--report",
                str(report),
                "--in-detached-worker",
            ],
            worker,
        )
        retained = json.loads(report.read_text())
        if retained["status"] != "local_immutable_validation_passed":
            raise ValueError("legacy release authoritative validation did not pass")
        return {"bound_commit": commit, "report_sha256": V25.sha256(report), "run": outcome}
    finally:
        if worker.exists():
            run(["git", "worktree", "remove", "--force", str(worker)])
        shutil.rmtree(parent, ignore_errors=True)


def validate_v24_release(package: Path, report: Path) -> dict[str, Any]:
    outcome = run(
        [
            sys.executable,
            str(REPOSITORY / "tools/astral-v24-validation-release-v2/validate_release.py"),
            "--package",
            str(package),
            "--report",
            str(report),
        ]
    )
    retained = json.loads(report.read_text())
    if retained["status"] != "V24ImmutableValidationPassed":
        raise ValueError("V24 authoritative validation did not pass")
    return {"report_sha256": V25.sha256(report), "run": outcome}


def claim_disposition(
    claim: str,
    status: str,
    release_claims: set[str],
) -> str:
    if claim == "C045":
        return "MachineValidatedSyntheticHarnessOnly"
    if claim in release_claims:
        return "ImmutableAuthorArtifactValidatedWithinCeiling"
    if status == "Refuted":
        return "RetainedSetupScopedRefutation"
    if status == "Not refuted":
        return "LedgerEvidenceNotRefutedNotProven"
    if status == "Weakened":
        return "Weakened"
    if status == "Accepted-as-design-choice":
        return "DesignPolicy"
    return "Unresolved"


def validate_all(
    artifact: Path,
    legacy_release: Path,
    v24_release: Path,
    report: Path,
) -> dict[str, Any]:
    if run(["git", "status", "--porcelain"])["stdout"]:
        raise ValueError("holistic validation requires a clean launcher worktree")
    if report.exists() or report.with_suffix(report.suffix + ".sha256").exists():
        raise ValueError("holistic report destination already exists")
    contract = json.loads(CLAIM_CONTRACT.read_text())
    claims, history = verify_claim_contract(contract)
    v25 = V25_VALIDATOR.validate(artifact)
    if v25["classification"] != contract["claim_ceiling"]:
        raise ValueError("V25 claim ceiling mismatch")
    bindings = contract["immutable_release_bindings"]
    legacy_integrity = verify_sha_manifest(
        legacy_release,
        bindings["legacy_v18_v23"]["manifest"],
        bindings["legacy_v18_v23"]["prefix"],
        bindings["legacy_v18_v23"]["identity"],
    )
    v24_integrity = verify_sha_manifest(
        v24_release,
        bindings["v24"]["manifest"],
        bindings["v24"]["prefix"],
        bindings["v24"]["identity"],
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    legacy_report = report.with_name(report.stem + "-legacy-v18-v23.json")
    v24_report = report.with_name(report.stem + "-v24.json")
    for child in (legacy_report, v24_report):
        if child.exists() or child.with_suffix(child.suffix + ".sha256").exists():
            raise ValueError("child validation report destination already exists")
    legacy_validation = validate_legacy_release(legacy_release, legacy_report)
    v24_validation = validate_v24_release(v24_release, v24_report)
    test_paths = sorted(
        str(path.relative_to(REPOSITORY))
        for directory in (REPOSITORY / "tools").glob("astral-*")
        for path in directory.glob("tests")
        if path.is_dir()
    )
    structural = run([sys.executable, "-m", "pytest", "-q", *test_paths])
    rust = run(["cargo", "test", "-p", "astral-stage0-protocol", "--locked"])
    release_claims = set(bindings["legacy_v18_v23"]["claim_ids"]) | set(bindings["v24"]["claim_ids"])
    claim_matrix = {
        claim: {
            "current_status": status,
            "disposition": claim_disposition(claim, status, release_claims),
            "history": history[claim],
        }
        for claim, status in claims.items()
    }
    thesis_gates = [
        {
            **gate,
            "satisfied": False,
            "reason": "required external or model-backed evidence is absent",
        }
        for gate in contract["required_thesis_gates"]
    ]
    result = {
        "claim_ceiling": contract["claim_ceiling"],
        "claim_count": len(claim_matrix),
        "claim_matrix": claim_matrix,
        "external_releases": {
            "legacy_v18_v23": {"integrity": legacy_integrity, "validation": legacy_validation},
            "v24": {"integrity": v24_integrity, "validation": v24_validation},
        },
        "pipeline_status": "HolisticClaimValidationCompleteWithOpenClaims",
        "source_commit": run(["git", "rev-parse", "HEAD"])["stdout"],
        "structural_tests": structural,
        "rust_protocol_tests": rust,
        "thesis_gates": thesis_gates,
        "thesis_status": contract["thesis_status"],
        "v25": v25,
        "validation_interpretation": (
            "All enumerated claims and supplied immutable artifacts were checked. "
            "Open thesis gates remain open; pipeline success is not thesis proof."
        ),
    }
    V25.write_json(report, result)
    report.with_suffix(report.suffix + ".sha256").write_text(f"{V25.sha256(report)}  {report.name}\n")
    return {
        "claim_count": len(claim_matrix),
        "pipeline_status": result["pipeline_status"],
        "report": str(report),
        "report_sha256": V25.sha256(report),
        "thesis_status": result["thesis_status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--legacy-release", required=True, type=Path)
    parser.add_argument("--v24-release", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = validate_all(
            args.artifact.resolve(),
            args.legacy_release.resolve(),
            args.v24_release.resolve(),
            args.report.resolve(),
        )
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "completed", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
