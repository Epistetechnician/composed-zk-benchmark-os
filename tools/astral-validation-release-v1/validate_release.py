#!/usr/bin/env python3
"""Fail-closed authoritative validator for the Astral V18-V23 release."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
LEDGER = REPOSITORY / "docs/research/astral-self-modeling/03-claim-ledger.md"
ASSESSMENT_FILES = {
    "v19": "assessment-effects.json",
    "v22": "assessment-results.json",
    "v23": "assessment-results.json",
}
CORPUS_BUILDERS = {
    "v18": ("tools/astral-lm-explainer-v18/v18.py", "build_corpus"),
    "v19": ("tools/astral-lm-explainer-v19/v19.py", "build_corpus"),
    "v20": ("tools/astral-lm-explainer-v20/v20.py", "build_corpus"),
    "v21": ("tools/astral-lm-explainer-v21/v21.py", "build_corpus"),
    "v22": ("tools/astral-activation-discrimination-v22/v22.py", "build_trials"),
    "v23": ("tools/astral-activation-discrimination-v23/v23.py", "V22.build_trials"),
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        command, cwd=REPOSITORY, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    return {
        "command": command,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def verify_package_manifest(package: Path) -> dict[str, Any]:
    manifest = package / "PACKAGE-MANIFEST.sha256"
    rows = {}
    for line in manifest.read_text().splitlines():
        expected, separator, relative = line.partition("  ")
        if not separator or relative in rows:
            raise ValueError("invalid package manifest row")
        rows[relative] = expected
    actual = {
        str(path.relative_to(package))
        for path in package.rglob("*")
        if path.is_file() and path.name != manifest.name
    }
    if actual != set(rows):
        raise ValueError("package manifest census mismatch")
    for relative, expected in rows.items():
        if sha(package / relative) != expected:
            raise ValueError(f"package digest mismatch: {relative}")
    identity = sha(manifest)
    if package.name != f"astral-validation-release-v1-{identity}":
        raise ValueError("content-addressed package name mismatch")
    return {"file_count": len(rows), "package_identity": identity}


def import_module(name: str, relative: str):
    path = REPOSITORY / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def resolve_builder(module: Any, expression: str):
    value = module
    for component in expression.split("."):
        value = getattr(value, component)
    return value


def canonical_rows(rows: list[Any]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if hasattr(row, "__dataclass_fields__"):
            output.append({name: getattr(row, name) for name in row.__dataclass_fields__})
        else:
            output.append(dict(row))
    return output


def verify_corpora(package: Path) -> dict[str, int]:
    counts = {}
    for name, (relative, expression) in CORPUS_BUILDERS.items():
        module = import_module(f"astral_release_{name}", relative)
        generated = canonical_rows(resolve_builder(module, expression)())
        retained = json.loads((package / "artifacts" / name / "corpus.json").read_text())
        if generated != retained:
            raise ValueError(f"deterministic corpus mismatch: {name}")
        counts[name] = len(generated)
    return counts


def calculated_metrics(predicted: list[float], actual: list[float]) -> dict[str, float]:
    p, y = np.asarray(predicted, dtype=float), np.asarray(actual, dtype=float)
    design = np.column_stack([np.ones(len(p)), p])
    calibration = np.linalg.lstsq(design, y, rcond=None)[0]
    correlation = float(np.corrcoef(p, y)[0, 1]) if np.std(p) > 0 and np.std(y) > 0 else 0.0
    return {
        "mse": float(np.mean((p - y) ** 2)),
        "mae": float(np.mean(np.abs(p - y))),
        "pearson": correlation,
        "calibration_intercept": float(calibration[0]),
        "calibration_slope": float(calibration[1]),
    }


def verify_metrics(bundle: Path, target_field: str) -> int:
    result = json.loads((bundle / "result.json").read_text())
    effects = json.loads((bundle / "assessment-effects.json").read_text())
    actual = [row[target_field] for row in effects]
    predictions = json.loads((bundle / "assessment-predictions.json").read_text())
    ensembles = json.loads((bundle / "ensemble-predictions.json").read_text())
    rows = {**predictions, **{f"{name}-ensemble": value for name, value in ensembles.items()}}
    for name, method_rows in rows.items():
        recomputed = calculated_metrics([row["prediction"] for row in method_rows], actual)
        retained = result["metrics"][name]
        for metric, value in recomputed.items():
            if not np.isclose(value, retained[metric], rtol=0, atol=1e-12):
                raise ValueError(f"metric mismatch: {bundle.name}:{name}:{metric}")
    return len(rows)


def verify_source_inventory(package: Path) -> int:
    retained = json.loads((package / "metadata/source-inventory.json").read_text())
    for relative, expected in retained.items():
        path = REPOSITORY / relative
        if not path.is_file() or sha(path) != expected:
            raise ValueError(f"release source mismatch: {relative}")
    return len(retained)


def verify_git_tree(package: Path) -> str:
    build = json.loads((package / "metadata/build-record.json").read_text())
    current_tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"], cwd=REPOSITORY,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if current_tree != build["git_staged_tree"]:
        raise ValueError("release commit tree differs from packaged staged tree")
    if subprocess.run(["git", "status", "--porcelain"], cwd=REPOSITORY, check=True, capture_output=True, text=True).stdout:
        raise ValueError("release worktree is not clean")
    return current_tree


def verify_ledger(spec: dict[str, Any]) -> int:
    text = LEDGER.read_text()
    for name, contract in spec["bundles"].items():
        matching = [line for line in text.splitlines() if f"| {contract['claim_id']} |" in line]
        if len(matching) != 1 or f"| {contract['claim_status']} |" not in matching[0]:
            raise ValueError(f"claim-ledger mismatch: {name}:{contract['claim_id']}")
        if contract["expected_manifest_sha256"] not in matching[0]:
            raise ValueError(f"claim-ledger artifact mismatch: {name}")
    return len(spec["bundles"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--in-detached-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    package, report_path = args.package.resolve(), args.report.resolve()
    if not args.in_detached_worker:
        if subprocess.run(
            ["git", "status", "--porcelain"], cwd=REPOSITORY, check=True,
            capture_output=True, text=True,
        ).stdout:
            raise SystemExit("release launcher worktree is not clean")
        parent = Path(tempfile.mkdtemp(prefix="astral-validation-detached-"))
        worker = parent / "checkout"
        try:
            subprocess.run(
                ["git", "worktree", "add", "--detach", str(worker), "HEAD"],
                cwd=REPOSITORY, check=True, capture_output=True, text=True,
            )
            command = [
                sys.executable,
                str(worker / "tools/astral-validation-release-v1/validate_release.py"),
                "--package", str(package), "--report", str(report_path),
                "--in-detached-worker",
            ]
            completed = subprocess.run(command, cwd=worker)
            return completed.returncode
        finally:
            if worker.exists():
                subprocess.run(
                    ["git", "worktree", "remove", "--force", str(worker)],
                    cwd=REPOSITORY, check=True, capture_output=True, text=True,
                )
            shutil.rmtree(parent, ignore_errors=True)
    if report_path.exists() or report_path.with_suffix(report_path.suffix + ".sha256").exists():
        raise SystemExit("report destination already exists")
    package_state = verify_package_manifest(package)
    spec = json.loads((package / "metadata/release-spec.json").read_text())
    if spec["claim_ceiling"] != "LocalImmutableValidationCandidate":
        raise ValueError("claim ceiling mismatch")
    source_count = verify_source_inventory(package)
    git_tree = verify_git_tree(package)
    corpus_counts = verify_corpora(package)
    ledger_count = verify_ledger(spec)
    validator_runs = {}
    for name, contract in sorted(spec["bundles"].items()):
        bundle = package / "artifacts" / name
        if contract["assessment"] == "absent" and (bundle / ASSESSMENT_FILES[name]).exists():
            raise ValueError(f"sealed assessment unexpectedly present: {name}")
        result = json.loads((bundle / "result.json").read_text())
        if result["classification"] != contract["expected_classification"]:
            raise ValueError(f"classification mismatch: {name}")
        validator_runs[name] = run(
            [sys.executable, str(REPOSITORY / contract["validator"]), str(bundle)]
        )
    metric_methods = {
        "v20": verify_metrics(package / "artifacts/v20", "effect"),
        "v21": verify_metrics(package / "artifacts/v21", "residual_effect"),
    }
    test_paths = sorted(
        str(path.relative_to(REPOSITORY))
        for directory in (REPOSITORY / "tools").glob("astral-*")
        for path in directory.glob("tests")
        if path.is_dir()
    )
    tests = run([sys.executable, "-m", "pytest", "-q", *test_paths])
    rust = run(["cargo", "test", "-p", "astral-stage0-protocol", "--locked"])
    report = {
        "status": "local_immutable_validation_passed",
        "claim_ceiling": spec["claim_ceiling"],
        "package": package_state,
        "git_tree": git_tree,
        "source_file_count": source_count,
        "corpus_counts": corpus_counts,
        "claim_ledger_rows": ledger_count,
        "metric_method_counts": metric_methods,
        "validator_runs": validator_runs,
        "structural_tests": tests,
        "rust_protocol_tests": rust,
        "external_gates": {
            "reproducibility_reviewer": "NotRun",
            "scientific_reviewer": "NotRun",
            "independent_implementation_replication": "NotRun",
            "stage_0c_confirmation": "Blocked",
            "stage_1": "BlockedByStage0C"
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    digest = sha(report_path)
    sidecar = report_path.with_suffix(report_path.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {report_path.name}\n")
    print(json.dumps({"status": report["status"], "report": str(report_path), "report_sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
