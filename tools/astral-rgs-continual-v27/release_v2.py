from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Any


HERE = Path(__file__).resolve().parent
RELEASE_SPEC_PATH = HERE / "release-spec.json"
RELEASE_VERSION = "astral.rgs_v27_immutable_release.v1"
MANIFEST_NAME = "RELEASE-MANIFEST.sha256"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_release(
    *,
    astral_repository: Path,
    rgs_repository: Path,
    historical_report: Path,
    tencent_packet_path: Path,
    tencent_subset_manifest: Path,
    output_parent: Path,
    tencent_source_license: Path | None = None,
    tencent_dataset_license: Path | None = None,
    rgs_input: Path | None = None,
    rgs_report: Path | None = None,
) -> Path:
    if (rgs_input is None) != (rgs_report is None):
        raise ValueError("rgs input and report must be supplied together")
    repositories = {
        "astral": astral_repository.resolve(),
        "recoverable-ghost-states": rgs_repository.resolve(),
    }
    source_records: dict[str, dict[str, Any]] = {}
    for name, repository in repositories.items():
        source_records[name] = _source_record(repository)
    packet = _read_object(tencent_packet_path)
    subset_manifest = _read_object(tencent_subset_manifest)
    if packet.get("version") not in (
        "mesh.tencent_clbench_frozen_evaluation.v1",
        "mesh.tencent_clbench_frozen_evaluation.v2",
    ):
        raise ValueError("Tencent packet V1 or V2 is required")
    if subset_manifest.get("version") != "mesh.tencent_clbench_subset_manifest.v1":
        raise ValueError("Tencent subset manifest V1 is required")

    output_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".astral-rgs-v27-r1-", dir=output_parent) as temporary:
        root = Path(temporary)
        (root / "sources").mkdir()
        evidence = root / "evidence"
        tencent_root = evidence / "tencent"
        tencent_files = tencent_root / "files"
        tencent_files.mkdir(parents=True)
        (root / "runtime").mkdir()

        for name, repository in repositories.items():
            bundle = root / "sources" / f"{name}.bundle"
            _run(["git", "bundle", "create", str(bundle), "--all"], cwd=repository)
            source_records[name]["bundle_path"] = bundle.relative_to(root).as_posix()
            source_records[name]["bundle_sha256"] = "sha256:" + sha256_file(bundle)

        if packet["version"] == "mesh.tencent_clbench_frozen_evaluation.v2":
            rebound_packet, materializations = _materialize_tencent_packet(
                packet,
                release_root=root,
                target_root=tencent_files,
            )
            packet_target = tencent_root / "packet-v2.json"
            _write_json(packet_target, rebound_packet)
            tencent_status = "ReplayableV2"
        else:
            if tencent_source_license is None or tencent_dataset_license is None:
                raise ValueError(
                    "historical Tencent V1 packets require both license paths"
                )
            materializations = _materialize_historical_tencent_packet(
                packet,
                release_root=root,
                target_root=tencent_files,
                source_license=tencent_source_license,
                dataset_license=tencent_dataset_license,
            )
            packet_target = tencent_root / "historical-packet-v1.json"
            shutil.copyfile(tencent_packet_path, packet_target)
            tencent_status = "HistoricalV1NonReplayableMissingExactCommands"
        subset_target = tencent_root / "subset-manifest.json"
        shutil.copyfile(tencent_subset_manifest, subset_target)
        historical_target = evidence / "historical-v25-report.json"
        historical_target.parent.mkdir(exist_ok=True)
        shutil.copyfile(historical_report, historical_target)

        evidence_record: dict[str, Any] = {
            "historical_v25_report": _file_record(historical_target, root),
            "tencent_packet": _file_record(packet_target, root),
            "tencent_subset_manifest": _file_record(subset_target, root),
            "tencent_materializations": materializations,
            "tencent_validation_status": tencent_status,
            "rgs_model_backed": "NotRun",
        }
        if rgs_input is not None and rgs_report is not None:
            rgs_root = evidence / "rgs"
            rgs_root.mkdir()
            input_target = rgs_root / "locked-input.json"
            report_target = rgs_root / "report.json"
            shutil.copyfile(rgs_input, input_target)
            shutil.copyfile(rgs_report, report_target)
            evidence_record.update(
                {
                    "rgs_model_backed": "Supplied",
                    "rgs_locked_input": _file_record(input_target, root),
                    "rgs_report": _file_record(report_target, root),
                }
            )

        runtime_inventory = _runtime_inventory()
        runtime_path = root / "runtime" / "inventory.json"
        _write_json(runtime_path, runtime_inventory)
        release_spec_target = root / "release-spec.json"
        shutil.copyfile(RELEASE_SPEC_PATH, release_spec_target)
        release_core = {
            "version": RELEASE_VERSION,
            "state_slice": "astral-rgs-v27-model-backed-qualification-r1",
            "sources": source_records,
            "evidence": evidence_record,
            "runtime_inventory": _file_record(runtime_path, root),
            "release_spec": _file_record(release_spec_target, root),
            "gate_state": {
                "model_backed_assessment": (
                    "SuppliedForReplay" if rgs_report is not None else "NotRun"
                ),
                "independent_review": "NotRun",
                "independent_replication": "NotRun",
                "stage_0c": "Blocked",
                "stage_1": "BlockedByStage0C",
                "thesis": "NotValidated",
            },
            "claim_boundary": {
                "immutable_author_development_release": True,
                "continual_learning_solved": False,
                "autonomous_self_improvement": False,
                "introspection": False,
                "self_modeling": False,
                "stage_0c": False,
                "stage_1": False,
            },
        }
        release_path = root / "RELEASE.json"
        _write_json(release_path, {**release_core, "release_sha256": stable_hash(release_core)})
        write_manifest(root)
        manifest_digest = sha256_file(root / MANIFEST_NAME)
        final_path = output_parent / f"astral-rgs-v27-r1-{manifest_digest[:16]}"
        if final_path.exists():
            raise FileExistsError(f"immutable release already exists: {final_path}")
        os.rename(root, final_path)
        return final_path


def verify_manifest(root: Path) -> list[str]:
    errors: list[str] = []
    manifest = root / MANIFEST_NAME
    if not manifest.is_file() or manifest.is_symlink():
        return ["release.manifest.missing"]
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64 or parts[1] in expected:
            errors.append("release.manifest.syntax")
            continue
        expected[parts[1]] = parts[0]
    observed: set[str] = set()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f"release.symlink:{relative}")
        elif path.is_file() and relative != MANIFEST_NAME:
            observed.add(relative)
    if observed != set(expected):
        for missing in sorted(set(expected) - observed):
            errors.append(f"release.file_missing:{missing}")
        for extra in sorted(observed - set(expected)):
            errors.append(f"release.file_undeclared:{extra}")
    for relative in sorted(observed & set(expected)):
        if sha256_file(root / relative) != expected[relative]:
            errors.append(f"release.file_sha256:{relative}")
    return errors


def write_manifest(root: Path) -> None:
    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError(f"symlink forbidden in release: {relative}")
        if path.is_file() and relative != MANIFEST_NAME:
            entries.append(f"{sha256_file(path)}  {relative}")
    (root / MANIFEST_NAME).write_text("\n".join(entries) + "\n", encoding="utf-8")


def verify_source_checkout(
    *,
    checkout: Path,
    expected: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if _git(checkout, "rev-parse", "HEAD") != expected.get("commit"):
        errors.append("source.commit")
    if _git(checkout, "rev-parse", "HEAD^{tree}") != expected.get("tree"):
        errors.append("source.tree")
    if _source_inventory(checkout) != expected.get("inventory"):
        errors.append("source.inventory")
    return errors


def replay_release(
    *,
    release_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    release_root = release_root.resolve()
    before_manifest = sha256_file(release_root / MANIFEST_NAME) if (release_root / MANIFEST_NAME).is_file() else None
    errors = verify_manifest(release_root)
    release = _read_object(release_root / "RELEASE.json")
    core = dict(release)
    digest = core.pop("release_sha256", None)
    if release.get("version") != RELEASE_VERSION:
        errors.append("release.version")
    if digest != stable_hash(core):
        errors.append("release.release_sha256")
    command_results: list[dict[str, Any]] = []
    astral_validation: dict[str, Any] = {}
    if not errors:
        with tempfile.TemporaryDirectory(prefix="astral-rgs-v27-replay-") as temporary:
            replay_root = Path(temporary)
            checkouts: dict[str, Path] = {}
            for name, source in _dict(release.get("sources")).items():
                checkout = replay_root / name
                bundle = release_root / source["bundle_path"]
                result = _run_record(
                    ["git", "clone", "--no-checkout", str(bundle), str(checkout)],
                    cwd=replay_root,
                )
                command_results.append(result)
                if result["returncode"] != 0:
                    errors.append(f"replay.clone:{name}")
                    continue
                result = _run_record(
                    ["git", "checkout", "--detach", source["commit"]],
                    cwd=checkout,
                )
                command_results.append(result)
                if result["returncode"] != 0:
                    errors.append(f"replay.checkout:{name}")
                    continue
                errors.extend(
                    f"replay.{name}.{error}"
                    for error in verify_source_checkout(checkout=checkout, expected=source)
                )
                checkouts[name] = checkout
            if set(checkouts) == {"astral", "recoverable-ghost-states"}:
                astral_test = _run_record(
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "-p",
                        "no:cacheprovider",
                        "tools/astral-rgs-continual-v27/tests/test_v27.py",
                        "-q",
                    ],
                    cwd=checkouts["astral"],
                )
                command_results.append(astral_test)
                if astral_test["returncode"] != 0:
                    errors.append("replay.astral_tests")
                rgs_test = _run_record(
                    ["pnpm", "run", "test:holistic"],
                    cwd=checkouts["recoverable-ghost-states"],
                )
                command_results.append(rgs_test)
                if rgs_test["returncode"] != 0:
                    errors.append("replay.rgs_tests")
                rgs_fast = _run_record(
                    ["pnpm", "run", "lint:fast"],
                    cwd=checkouts["recoverable-ghost-states"],
                )
                command_results.append(rgs_fast)
                if rgs_fast["returncode"] != 0:
                    errors.append("replay.rgs_fast_gate")

                evidence = _dict(release.get("evidence"))
                output = replay_root / "astral-validation.json"
                command = [
                    sys.executable,
                    str(
                        checkouts["astral"]
                        / "tools/astral-rgs-continual-v27/validate_all_v2.py"
                    ),
                    "--historical-report",
                    str(release_root / evidence["historical_v25_report"]["path"]),
                ]
                if evidence.get("tencent_validation_status") == "ReplayableV2":
                    command.extend(
                        [
                        "--tencent-packet",
                        str(release_root / evidence["tencent_packet"]["path"]),
                        "--tencent-subset-manifest",
                        str(release_root / evidence["tencent_subset_manifest"]["path"]),
                        ]
                    )
                if evidence.get("rgs_model_backed") == "Supplied":
                    command.extend(
                        ["--rgs-report", str(release_root / evidence["rgs_report"]["path"])]
                    )
                    rgs_verify = _run_record(
                        [
                            sys.executable,
                            str(
                                checkouts["recoverable-ghost-states"]
                                / "scripts/verify_holistic_continual_eval.py"
                            ),
                            "--input",
                            str(release_root / evidence["rgs_locked_input"]["path"]),
                            "--report",
                            str(release_root / evidence["rgs_report"]["path"]),
                        ],
                        cwd=release_root,
                    )
                    command_results.append(rgs_verify)
                    if rgs_verify["returncode"] != 0:
                        errors.append("replay.rgs_report")
                command.extend(["--output", str(output)])
                astral_run = _run_record(command, cwd=release_root)
                command_results.append(astral_run)
                if astral_run["returncode"] != 0:
                    errors.append("replay.astral_validation")
                astral_validation = _read_object(output)
                if astral_validation.get("status") == "Invalid":
                    errors.append("replay.astral_validation_status")
    after_manifest = sha256_file(release_root / MANIFEST_NAME) if (release_root / MANIFEST_NAME).is_file() else None
    if before_manifest != after_manifest:
        errors.append("release.mutated_during_replay")
    report_core = {
        "version": "astral.rgs_v27_immutable_replay_report.v1",
        "state_slice": "astral-rgs-v27-model-backed-qualification-r1",
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "release": str(release_root),
        "release_manifest_sha256": after_manifest,
        "commands": command_results,
        "astral_validation": astral_validation,
        "attestation": {
            "content_digest_present": True,
            "human_signature": "NotRun",
            "independent_review": "NotRun",
        },
    }
    report = {**report_core, "report_sha256": stable_hash(report_core)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"replay output already exists: {output_path}")
    _write_json(output_path, report)
    return report


def _source_record(repository: Path) -> dict[str, Any]:
    if not (repository / ".git").exists():
        raise ValueError(f"not a git worktree: {repository}")
    status = _run(["git", "status", "--porcelain"], cwd=repository).stdout
    if status.strip():
        raise ValueError(f"source worktree must be clean: {repository}")
    return {
        "repository_path": str(repository),
        "commit": _git(repository, "rev-parse", "HEAD"),
        "tree": _git(repository, "rev-parse", "HEAD^{tree}"),
        "inventory": _source_inventory(repository),
    }


def _source_inventory(repository: Path) -> list[dict[str, str]]:
    output = _run(
        ["git", "ls-tree", "-r", "--full-tree", "HEAD"],
        cwd=repository,
    ).stdout
    inventory: list[dict[str, str]] = []
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        mode, kind, object_id = metadata.split(" ")
        inventory.append(
            {"mode": mode, "kind": kind, "object_id": object_id, "path": path}
        )
    return inventory


def _materialize_tencent_packet(
    packet: dict[str, Any],
    *,
    release_root: Path,
    target_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rebound = json.loads(json.dumps(packet))
    mappings = (
        ("source", "license_path", "source-license.txt"),
        ("dataset", "path", "dataset.jsonl"),
        ("dataset", "license_path", "dataset-license.txt"),
        ("execution", "model_path", "model.gguf"),
        ("execution", "raw_output_path", "raw-output.jsonl"),
    )
    if _dict(rebound.get("grading")).get("performed") is True:
        mappings = (*mappings, ("grading", "graded_output_path", "graded-output.jsonl"))
    records: list[dict[str, Any]] = []
    for section, key, target_name in mappings:
        source_value = _dict(rebound.get(section)).get(key)
        if not isinstance(source_value, str):
            raise ValueError(f"Tencent packet missing {section}.{key}")
        source_path = Path(source_value)
        if not source_path.is_file() or source_path.is_symlink():
            raise ValueError(f"Tencent packet file unavailable: {source_path}")
        target = target_root / target_name
        mode = _materialize(source_path, target)
        relative = target.relative_to(release_root).as_posix()
        rebound[section][key] = relative
        records.append({**_file_record(target, release_root), "materialization": mode})
    core = dict(rebound)
    core.pop("packet_sha256", None)
    rebound["packet_sha256"] = stable_hash(core)
    return rebound, records


def _materialize_historical_tencent_packet(
    packet: dict[str, Any],
    *,
    release_root: Path,
    target_root: Path,
    source_license: Path,
    dataset_license: Path,
) -> list[dict[str, Any]]:
    mappings: list[tuple[Path, str]] = [
        (source_license, "source-license.txt"),
        (Path(_dict(packet.get("dataset"))["path"]), "dataset.jsonl"),
        (dataset_license, "dataset-license.txt"),
        (Path(_dict(packet.get("execution"))["model_path"]), "model.gguf"),
        (Path(_dict(packet.get("execution"))["raw_output_path"]), "raw-output.jsonl"),
    ]
    if _dict(packet.get("grading")).get("performed") is True:
        mappings.append(
            (
                Path(_dict(packet.get("grading"))["graded_output_path"]),
                "graded-output.jsonl",
            )
        )
    records: list[dict[str, Any]] = []
    for source, target_name in mappings:
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"historical Tencent byte unavailable: {source}")
        target = target_root / target_name
        mode = _materialize(source, target)
        records.append({**_file_record(target, release_root), "materialization": mode})
    return records


def _materialize(source: Path, target: Path) -> str:
    try:
        os.link(source, target)
        return "hardlink"
    except OSError:
        shutil.copyfile(source, target)
        return "copy"


def _runtime_inventory() -> dict[str, Any]:
    packages: dict[str, str] = {}
    for package in ("mlx", "mlx-lm", "numpy", "torch"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "not-installed"
    return {
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "packages": packages,
    }


def _file_record(path: Path, root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": "sha256:" + sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def _file_binding_errors(record: dict[str, Any], root: Path) -> list[str]:
    path = root / str(record.get("path") or "")
    if not path.is_file() or path.is_symlink():
        return ["file.missing_or_symlink"]
    if record.get("sha256") != "sha256:" + sha256_file(path):
        return ["file.sha256"]
    if record.get("size_bytes") != path.stat().st_size:
        return ["file.size"]
    return []


def _git(repository: Path, *args: str) -> str:
    return _run(["git", *args], cwd=repository).stdout.strip()


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _run_record(command: list[str], *, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
