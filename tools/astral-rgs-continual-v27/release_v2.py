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
RELEASE_VERSION = "astral.rgs_v27_immutable_release.v2"
MANIFEST_NAME = "RELEASE-MANIFEST.sha256"
STATE_SLICE = "astral-rgs-v27-model-backed-qualification-r1"
REQUIRED_NATIVE_METHODS = (
    "no_update",
    "naive_sequential_lora",
    "modular_ghost_state",
    "compressed_adapter_recollection",
    "representation_time_distillation",
    "nested_multiscale_lora",
)
NATIVE_RUNTIME_SCRIPT = """import importlib.metadata
import json
import platform
import sys
packages = {}
for name in ("mlx", "mlx-lm", "mlx-lm-lora", "numpy"):
    try:
        packages[name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        packages[name] = "not-installed"
modules = {}
for name in ("mlx", "mlx_lm", "mlx_lm_lora"):
    try:
        __import__(name)
        modules[name] = True
    except Exception as exc:
        modules[name] = False
        modules[name + "_error"] = type(exc).__name__ + ": " + str(exc)
print(json.dumps({"python": sys.version, "executable": sys.executable, "platform": platform.platform(), "packages": packages, "modules": modules}, sort_keys=True))
"""


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
    native_smoke_root: Path,
    native_model_path: Path,
    native_python: Path,
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
    native_errors = validate_native_smoke(
        smoke_root=native_smoke_root,
        model_root=native_model_path,
        rgs_checkout=repositories["recoverable-ghost-states"],
        expected_source=source_records["recoverable-ghost-states"],
    )
    if native_errors:
        raise ValueError("native smoke validation failed: " + ", ".join(native_errors))
    native_runtime = _native_runtime_inventory(native_python)
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
    with tempfile.TemporaryDirectory(prefix=".astral-rgs-v27-r2-", dir=output_parent) as temporary:
        root = Path(temporary)
        (root / "sources").mkdir()
        evidence = root / "evidence"
        tencent_root = evidence / "tencent"
        tencent_files = tencent_root / "files"
        tencent_files.mkdir(parents=True)
        (root / "runtime").mkdir()
        native_smoke_target = evidence / "native-smoke"
        native_model_target = root / "models" / "native-qwen"
        native_smoke_files = _materialize_directory(
            native_smoke_root,
            native_smoke_target,
            release_root=root,
        )
        native_model_files = _materialize_directory(
            native_model_path,
            native_model_target,
            release_root=root,
        )

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
            "native_arm_development_smoke": "SuppliedValidated",
            "native_smoke_root": native_smoke_target.relative_to(root).as_posix(),
            "native_smoke_files": native_smoke_files,
            "native_probe": _file_record(native_smoke_target / "native-probe.json", root),
            "native_preflight": _file_record(
                native_smoke_target / "native-preflight.json", root
            ),
            "native_run_config": _file_record(native_smoke_target / "run-config.json", root),
            "native_model_root": native_model_target.relative_to(root).as_posix(),
            "native_model_files": native_model_files,
            "native_model_inventory_sha256": _model_inventory(native_model_target)[
                "inventory_sha256"
            ],
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
        native_runtime_path = root / "runtime" / "native-mlx-inventory.json"
        _write_json(native_runtime_path, native_runtime)
        release_spec_target = root / "release-spec.json"
        shutil.copyfile(RELEASE_SPEC_PATH, release_spec_target)
        release_core = {
            "version": RELEASE_VERSION,
            "state_slice": STATE_SLICE,
            "sources": source_records,
            "evidence": evidence_record,
            "runtime_inventory": _file_record(runtime_path, root),
            "native_runtime_inventory": _file_record(native_runtime_path, root),
            "release_spec": _file_record(release_spec_target, root),
            "gate_state": {
                "native_arm_development_smoke": "SuppliedValidated",
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
                "native_arm_development_smoke": True,
                "model_backed_assessment": False,
                "scientific_candidate_qualified": False,
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
        final_path = output_parent / f"astral-rgs-v27-r2-{manifest_digest[:16]}"
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
    native_python: Path,
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
    native_validation: dict[str, Any] = {
        "supplied_smoke": "NotChecked",
        "detached_rerun": "NotRun",
        "normalized_probe_match": False,
    }
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
                evidence = _dict(release.get("evidence"))
                supplied_smoke = release_root / str(evidence.get("native_smoke_root") or "")
                native_model = release_root / str(evidence.get("native_model_root") or "")
                supplied_errors = validate_native_smoke(
                    smoke_root=supplied_smoke,
                    model_root=native_model,
                    rgs_checkout=checkouts["recoverable-ghost-states"],
                    expected_source=_dict(release.get("sources")).get(
                        "recoverable-ghost-states", {}
                    ),
                )
                native_validation["supplied_smoke"] = (
                    "Validated" if not supplied_errors else "Invalid"
                )
                native_validation["supplied_errors"] = supplied_errors
                errors.extend(f"replay.native_supplied.{error}" for error in supplied_errors)

                runtime_result = _run_record(
                    [str(native_python), "-c", NATIVE_RUNTIME_SCRIPT],
                    cwd=replay_root,
                )
                command_results.append(runtime_result)
                runtime_ready = False
                if runtime_result["returncode"] == 0:
                    try:
                        runtime_record = json.loads(runtime_result["stdout"])
                        runtime_ready = all(
                            _dict(runtime_record.get("modules")).get(name) is True
                            for name in ("mlx", "mlx_lm", "mlx_lm_lora")
                        )
                        native_validation["runtime"] = runtime_record
                    except (json.JSONDecodeError, AttributeError):
                        errors.append("replay.native_runtime_json")
                else:
                    errors.append("replay.native_runtime")
                if not runtime_ready:
                    errors.append("replay.native_runtime_not_ready")

                if not supplied_errors and runtime_ready:
                    run_config = _read_object(supplied_smoke / "run-config.json")
                    rerun_root = replay_root / "native-smoke-rerun"
                    rerun_command = [
                        str(native_python),
                        str(
                            checkouts["recoverable-ghost-states"]
                            / "scripts/run_v27_native_arm_smoke.py"
                        ),
                        "--model",
                        str(native_model),
                        "--output",
                        str(rerun_root),
                        "--seed",
                        str(run_config["seed"]),
                        "--task-order",
                        ",".join(run_config["task_order"]),
                        "--steps-per-task",
                        str(run_config["steps_per_task"]),
                        "--lora-rank",
                        str(run_config["lora_rank"]),
                        "--num-layers",
                        str(run_config["num_layers"]),
                        "--learning-rate",
                        str(run_config["learning_rate"]),
                        "--representation-weight",
                        str(run_config["representation_weight"]),
                        "--json",
                    ]
                    native_rerun = _run_record(
                        rerun_command,
                        cwd=checkouts["recoverable-ghost-states"],
                    )
                    command_results.append(native_rerun)
                    if native_rerun["returncode"] != 0:
                        errors.append("replay.native_rerun")
                        native_validation["detached_rerun"] = "Failed"
                    else:
                        rerun_errors = validate_native_smoke(
                            smoke_root=rerun_root,
                            model_root=native_model,
                            rgs_checkout=checkouts["recoverable-ghost-states"],
                            expected_source=_dict(release.get("sources")).get(
                                "recoverable-ghost-states", {}
                            ),
                        )
                        errors.extend(
                            f"replay.native_rerun.{error}" for error in rerun_errors
                        )
                        native_validation["detached_rerun"] = (
                            "Validated" if not rerun_errors else "Invalid"
                        )
                        supplied_probe = _read_object(supplied_smoke / "native-probe.json")
                        rerun_probe = _read_object(rerun_root / "native-probe.json")
                        probes_match = _normalized_native_probe(supplied_probe) == _normalized_native_probe(
                            rerun_probe
                        )
                        native_validation["normalized_probe_match"] = probes_match
                        if not probes_match:
                            errors.append("replay.native_probe_nondeterministic")

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
        "version": "astral.rgs_v27_immutable_replay_report.v2",
        "state_slice": STATE_SLICE,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "release": str(release_root),
        "release_manifest_sha256": after_manifest,
        "commands": command_results,
        "astral_validation": astral_validation,
        "native_validation": native_validation,
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
    shutil.copyfile(source, target)
    return "copy"


def _materialize_directory(
    source: Path,
    target: Path,
    *,
    release_root: Path,
) -> list[dict[str, Any]]:
    source = source.expanduser().resolve()
    if not source.is_dir() or source.is_symlink():
        raise ValueError(f"materialization source must be a real directory: {source}")
    target.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_symlink():
            raise ValueError(f"symlink forbidden in materialization: {relative.as_posix()}")
        if path.is_dir():
            destination.mkdir(exist_ok=True)
        elif path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            records.append({**_file_record(destination, release_root), "materialization": "copy"})
        else:
            raise ValueError(f"unsupported materialization entry: {relative.as_posix()}")
    return records


def _model_inventory(model_root: Path) -> dict[str, Any]:
    root = model_root.expanduser().resolve()
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": "sha256:" + sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    ] if root.is_dir() and not root.is_symlink() else []
    present = {row["path"] for row in files}
    weight_count = sum(Path(row["path"]).suffix in (".safetensors", ".gguf") for row in files)
    identity = {
        "files": files,
        "required_files": ["config.json", "tokenizer.json", "tokenizer_config.json"],
        "weight_file_count": weight_count,
        "complete": root.is_dir()
        and not root.is_symlink()
        and all(name in present for name in ("config.json", "tokenizer.json", "tokenizer_config.json"))
        and weight_count > 0,
    }
    return {"path": str(root), **identity, "inventory_sha256": stable_hash(identity)}


def validate_native_smoke(
    *,
    smoke_root: Path,
    model_root: Path,
    rgs_checkout: Path,
    expected_source: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if not smoke_root.is_dir() or smoke_root.is_symlink():
        return ["smoke_root.missing_or_symlink"]
    if not model_root.is_dir() or model_root.is_symlink():
        return ["model_root.missing_or_symlink"]
    required = ("development-corpus.json", "run-config.json", "native-probe.json", "native-preflight.json")
    if any(not (smoke_root / name).is_file() for name in required):
        return ["smoke_root.required_files"]
    run_config = _read_object(smoke_root / "run-config.json")
    probe = _read_object(smoke_root / "native-probe.json")
    preflight = _read_object(smoke_root / "native-preflight.json")
    model = _model_inventory(model_root)
    if not model["complete"]:
        errors.append("model.complete")
    if run_config.get("model_inventory_sha256") != model["inventory_sha256"]:
        errors.append("run_config.model_inventory_sha256")
    if probe.get("model_inventory_sha256") != model["inventory_sha256"]:
        errors.append("probe.model_inventory_sha256")
    probe_core = {key: value for key, value in probe.items() if key != "probe_sha256"}
    if probe.get("probe_sha256") != stable_hash(probe_core):
        errors.append("probe.probe_sha256")
    preflight_core = {key: value for key, value in preflight.items() if key != "report_sha256"}
    if preflight.get("report_sha256") != stable_hash(preflight_core):
        errors.append("preflight.report_sha256")
    if preflight.get("status") != "NativeDevelopmentSmokePassed":
        errors.append("preflight.status")
    if preflight.get("assessment_state") != "SealedNotOpened":
        errors.append("preflight.assessment_state")
    if preflight.get("native_probe_sha256") != probe.get("probe_sha256"):
        errors.append("preflight.native_probe_sha256")
    checks = _dict(preflight.get("checks"))
    if any(checks.get(key) is not True for key in ("model_inventory_complete", "runtime_ready", "six_distinct_native_contracts", "native_development_probe_passed")):
        errors.append("preflight.checks")
    if checks.get("assessment_opened") is not False:
        errors.append("preflight.assessment_opened")
    claim = _dict(preflight.get("claim_boundary"))
    if claim.get("native_arm_development_smoke") is not True:
        errors.append("preflight.claim.native_arm_development_smoke")
    for key in ("model_backed_assessment", "scientific_candidate_qualified", "continual_learning_solved", "autonomous_self_improvement", "independently_replicated"):
        if claim.get(key) is not False:
            errors.append(f"preflight.claim.{key}")
    if probe.get("assessment_opened") is not False or run_config.get("assessment_opened") is not False:
        errors.append("smoke.assessment_opened")
    if probe.get("failure_count") != 0 or probe.get("failures") != []:
        errors.append("probe.failures")
    source = _dict(probe.get("source_binding"))
    if run_config.get("source_binding") != source:
        errors.append("run_config.source_binding")
    if source.get("repository_commit") != expected_source.get("commit"):
        errors.append("source.commit")
    if source.get("repository_tree") != expected_source.get("tree"):
        errors.append("source.tree")
    if source.get("worktree_dirty") is not False:
        errors.append("source.worktree_dirty")
    source_files = {
        "implementation_source_sha256": rgs_checkout / "mesh_brain/meshmodel/v27_native_mlx.py",
        "contract_source_sha256": rgs_checkout / "mesh_brain/meshmodel/v27_native_arms.py",
    }
    for key, path in source_files.items():
        observed = "sha256:" + sha256_file(path) if path.is_file() else None
        if source.get(key) != observed:
            errors.append(f"source.{key}")
    methods = probe.get("methods") if isinstance(probe.get("methods"), list) else []
    by_id = {row.get("method_id"): row for row in methods if isinstance(row, dict)}
    if tuple(row.get("method_id") for row in methods if isinstance(row, dict)) != REQUIRED_NATIVE_METHODS:
        errors.append("probe.methods")
    methods_root = smoke_root / "methods"
    observed_directories = tuple(sorted(path.name for path in methods_root.iterdir() if path.is_dir())) if methods_root.is_dir() else ()
    if observed_directories != tuple(sorted(REQUIRED_NATIVE_METHODS)):
        errors.append("methods.directories")
    for method_id in REQUIRED_NATIVE_METHODS:
        method = by_id.get(method_id)
        if not isinstance(method, dict) or method.get("execution_status") != "native_observed":
            errors.append(f"method.{method_id}.execution_status")
            continue
        manifest_path = methods_root / method_id / "artifact-manifest.json"
        if not manifest_path.is_file() or manifest_path.is_symlink():
            errors.append(f"method.{method_id}.manifest")
            continue
        manifest = _read_object(manifest_path)
        rows = manifest.get("files") if isinstance(manifest.get("files"), list) else []
        if manifest.get("manifest_sha256") != stable_hash(rows):
            errors.append(f"method.{method_id}.manifest_sha256")
        if method.get("artifact_manifest_sha256") != manifest.get("manifest_sha256"):
            errors.append(f"method.{method_id}.probe_manifest_sha256")
        method_result_path = manifest_path.parent / "method-result.json"
        if not method_result_path.is_file() or _read_object(method_result_path) != method:
            errors.append(f"method.{method_id}.method_result")
        expected_paths = set()
        for row in rows:
            relative = row.get("path") if isinstance(row, dict) else None
            if not isinstance(relative, str):
                errors.append(f"method.{method_id}.manifest_row")
                continue
            expected_paths.add(relative)
            artifact = manifest_path.parent / relative
            if artifact.is_symlink() or not artifact.is_file():
                errors.append(f"method.{method_id}.artifact_missing:{relative}")
            elif row.get("sha256") != "sha256:" + sha256_file(artifact) or row.get("size_bytes") != artifact.stat().st_size:
                errors.append(f"method.{method_id}.artifact_binding:{relative}")
        observed_paths = {
            path.relative_to(manifest_path.parent).as_posix()
            for path in manifest_path.parent.rglob("*")
            if path.is_file()
            and path.name not in ("artifact-manifest.json", "method-result.json")
        }
        if expected_paths != observed_paths:
            errors.append(f"method.{method_id}.artifact_census")
    return errors


def _normalized_native_probe(probe: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(probe))
    normalized.pop("probe_sha256", None)
    for row in normalized.get("methods", []):
        if isinstance(row, dict):
            row.pop("wall_time_seconds", None)
    for row in normalized.get("failures", []):
        if isinstance(row, dict):
            row.pop("wall_time_seconds", None)
    return normalized


def _native_runtime_inventory(native_python: Path) -> dict[str, Any]:
    result = _run_record([str(native_python), "-c", NATIVE_RUNTIME_SCRIPT], cwd=HERE)
    if result["returncode"] != 0:
        raise ValueError("native Python runtime probe failed: " + result["stderr"])
    try:
        inventory = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise ValueError("native Python runtime emitted invalid JSON") from exc
    modules = _dict(inventory.get("modules"))
    if any(modules.get(name) is not True for name in ("mlx", "mlx_lm", "mlx_lm_lora")):
        raise ValueError("native Python runtime is missing MLX dependencies")
    return inventory


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
