"""Crash-safe, consuming launcher for the V41R33R1 paired probe.

This module only defines the bounded launch contract and orchestration. It does
not authorize execution; the separate execution authorization remains required.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence


HERE = Path(__file__).resolve().parent
# Preserve the venv entrypoint spelling. Resolving its symlink would escape the
# isolated runtime and silently relaunch arms under the base interpreter.
PYTHON = str(Path(sys.executable))
RUN_ID = "v41r27-panel-8-seed-412019"
LAUNCH_ID = "v41r33r1-source-binding-runtime-custody-v4"
EXPECTED_ARCHIVE = "sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580"
EXPECTED_TREE = "sha256:652633475af44cd6053b9dec6f44c7420c2668eb0e9253c4b994e9199ff9b9f5"
EXPECTED_WRAPPER = "sha256:6b1fe655980033235ac9e925b1b7fdfa321404551c6087a2e05d748b4a001379"
EXPECTED_LAUNCHER = "sha256:1c12648503f39c4c1aae4bcc5cddedcf7c545b37ca50d8e012445e76d3a4169e"
EXPECTED_VALIDATOR = "sha256:f1b9f45cfc7d58812b0f72fba890d3ccb274224b578a74e9f87d584af645dfd4"
EXPECTED_COMMIT = "754220f7fc360d8dd15e5837190b895ea0550f30"
EXPECTED_MODEL_ID = "openai/gpt-oss-20b"
EXPECTED_MODEL_REVISION = "d0e2aa76789354d715f8b22553b9feb6c462fcf0"
EXPECTED_MODEL_MANIFEST = "sha256:5c768d8f240f7a1b6f49b008e6d0f21a235d8509f62fb85b099afdd50a060213"
EXPECTED_MODEL_MANIFEST_BYTES = "sha256:4d9726e0c665de76f960ed3dc77d939374ab60b040351872f0e4c0731f5c3370"
EXPECTED_RUNTIME_MANIFEST = "sha256:65608b8799eab02afc04151ef77cbb45956bbad4dc806a97de8164d36858aa50"
EXPECTED_SOURCE_BINDING = {
    "source_commit": EXPECTED_COMMIT,
    "source_archive_sha256": EXPECTED_ARCHIVE,
    "source_tree_sha256": EXPECTED_TREE,
}


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def command_argv(
    role: str,
    output: Path,
    *,
    archive: Path | None = None,
    launcher: Path = HERE / "v41r33r1_history_prelude_launcher.py",
    rgs_root: Path | None = None,
) -> list[str]:
    output = output.resolve()
    if role == "control":
        if rgs_root is None:
            raise ValueError("control requires RGS root")
        return [
            PYTHON, str((rgs_root.resolve() / "scripts/run_v41r27_worker.py").resolve()), "--output", str(output),
            "--run-id", RUN_ID, "--execute",
        ]
    if role == "intervention":
        if archive is None:
            raise ValueError("intervention requires archive")
        archive = archive.resolve()
        launcher = launcher.resolve()
        return [
            PYTHON, str(launcher), "--output", str(output),
            "--archive", str(archive),
        ]
    raise ValueError(f"unknown arm role: {role}")


def command_bytes(argv: Sequence[str]) -> str:
    return json.dumps(list(argv), separators=(",", ":"), ensure_ascii=True)


def validator_argv(validator: Path, artifact: Path, rgs_root: Path) -> list[str]:
    return [
        PYTHON, str(validator.resolve()), "--artifact", str(artifact.resolve()),
        "--rgs-root", str(rgs_root.resolve()),
    ]


def digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def model_manifest_rows_digest(rows: Sequence[dict[str, object]]) -> str:
    canonical = "".join(
        f"{row['path']}\0{row['sha256']}\0{row['size_bytes']}\n"
        for row in sorted(rows, key=lambda row: str(row["path"]))
    ).encode()
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def verify_model_custody(model_root: Path, hf_cache_root: Path) -> dict[str, object]:
    root = model_root.resolve()
    cache_root = hf_cache_root.resolve()
    manifest_path = root / "model-custody-manifest.json"
    if not root.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
        raise RuntimeError("V41R33R1 model custody manifest missing")
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("V41R33R1 model custody manifest unreadable") from error
    if manifest.get("model_id") != EXPECTED_MODEL_ID:
        raise RuntimeError("V41R33R1 model id mismatch")
    if manifest.get("revision") != EXPECTED_MODEL_REVISION:
        raise RuntimeError("V41R33R1 model revision mismatch")
    rows = manifest.get("files")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("V41R33R1 model custody file list missing")
    if any(
        not isinstance(row, dict) or
        any(key not in row for key in ("path", "sha256", "size_bytes"))
        for row in rows
    ):
        raise RuntimeError("V41R33R1 model manifest row malformed")
    if sha256(manifest_path) != EXPECTED_MODEL_MANIFEST_BYTES:
        raise RuntimeError("V41R33R1 model manifest bytes hash mismatch")
    if manifest.get("manifest_sha256") != EXPECTED_MODEL_MANIFEST:
        raise RuntimeError("V41R33R1 model manifest hash mismatch")
    if model_manifest_rows_digest(rows) != EXPECTED_MODEL_MANIFEST:
        raise RuntimeError("V41R33R1 model manifest rows mismatch")
    expected_paths: set[str] = set()
    snapshot = cache_root / "hub" / "models--openai--gpt-oss-20b" / "snapshots" / EXPECTED_MODEL_REVISION
    if snapshot.is_symlink() or not snapshot.is_dir():
        raise RuntimeError("V41R33R1 local model cache snapshot missing")
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("V41R33R1 model manifest row malformed")
        relative = Path(str(row.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise RuntimeError("V41R33R1 model manifest path unsafe")
        relative_name = relative.as_posix()
        if relative_name in expected_paths:
            raise RuntimeError("V41R33R1 model manifest path duplicated")
        expected_paths.add(relative_name)
        source = root / relative
        cached = snapshot / relative
        if source.is_symlink() or cached.is_symlink() or not source.is_file() or not cached.is_file():
            raise RuntimeError(f"V41R33R1 model custody file missing or symlinked: {relative_name}")
        source_stat = os.stat(source)
        cached_stat = os.stat(cached)
        if (source_stat.st_dev, source_stat.st_ino) != (cached_stat.st_dev, cached_stat.st_ino):
            raise RuntimeError(f"V41R33R1 model cache binding mismatch: {relative_name}")
        expected_size = int(row["size_bytes"])
        if source_stat.st_size != expected_size:
            raise RuntimeError(f"V41R33R1 model size mismatch: {relative_name}")
        if sha256(source) != str(row["sha256"]):
            raise RuntimeError(f"V41R33R1 model file hash mismatch: {relative_name}")
    actual_source_paths = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if not path.is_symlink() and path.is_file() and path != manifest_path
    }
    actual_cache_paths = {
        path.relative_to(snapshot).as_posix()
        for path in snapshot.rglob("*")
        if not path.is_symlink() and path.is_file()
    }
    if any(path.is_symlink() for path in root.rglob("*")):
        raise RuntimeError("V41R33R1 model custody contains symlink")
    if any(path.is_symlink() for path in snapshot.rglob("*")):
        raise RuntimeError("V41R33R1 model cache contains symlink")
    if actual_source_paths != expected_paths or actual_cache_paths != expected_paths:
        raise RuntimeError("V41R33R1 model custody file-set mismatch")
    return {
        "model_id": EXPECTED_MODEL_ID,
        "revision": EXPECTED_MODEL_REVISION,
        "manifest_path": str(manifest_path),
        "manifest_sha256": EXPECTED_MODEL_MANIFEST,
        "manifest_bytes_sha256": EXPECTED_MODEL_MANIFEST_BYTES,
        "file_count": len(expected_paths),
        "model_root": str(root),
        "hf_cache_root": str(cache_root),
        "snapshot_root": str(snapshot),
        "model_device": source_stat.st_dev,
    }


def verify_command(
    role: str,
    argv: Sequence[str],
    output: Path,
    *,
    archive: Path | None = None,
    launcher: Path = HERE / "v41r33r1_history_prelude_launcher.py",
    rgs_root: Path | None = None,
) -> None:
    expected = command_argv(
        role, output, archive=archive, launcher=launcher, rgs_root=rgs_root)
    if list(argv) != expected:
        raise RuntimeError(f"V41R33R1 {role} command mismatch")


def verify_runtime_hashes(
    launcher: Path,
    wrapper: Path,
    expected_launcher: str,
    expected_wrapper: str,
) -> None:
    if sha256(launcher.resolve()) != expected_launcher:
        raise RuntimeError("V41R33R1 launcher hash mismatch")
    if sha256(wrapper.resolve()) != expected_wrapper:
        raise RuntimeError("V41R33R1 wrapper hash mismatch")


def verify_validator(path: Path, expected: str) -> None:
    if not path.is_file() or sha256(path.resolve()) != expected:
        raise RuntimeError("V41R33R1 validator hash mismatch")


def verify_runtime_custody(path: Path) -> dict[str, object]:
    path = path.resolve()
    if not path.is_file() or sha256(path) != EXPECTED_RUNTIME_MANIFEST:
        raise RuntimeError("V41R33R1 runtime custody manifest mismatch")
    try:
        record = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("V41R33R1 runtime custody manifest unreadable") from error
    expected = {
        "runtime_identity": "v41r33r1-runtime-custody-v1",
        "python": "3.10.12",
        "torch_base_version": "2.10.0",
        "cuda": "12.8",
        "transformers": "4.57.6",
        "peft": "0.18.1",
        "model_loaded": False,
        "worker_imported": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            raise RuntimeError(f"V41R33R1 runtime custody mismatch: {key}")
    resolved_python = record.get("resolved_python")
    if not isinstance(resolved_python, str) or not Path(resolved_python).is_file():
        raise RuntimeError("V41R33R1 resolved runtime interpreter missing")
    if record.get("sys_prefix") != str(Path(resolved_python).parent.parent):
        raise RuntimeError("V41R33R1 runtime prefix mismatch")
    return record


def verify_wrapper_receipt(
    output: Path,
    *,
    archive: Path,
    launcher: Path,
    wrapper: Path,
) -> None:
    receipt_path = output / "v41r32r1-wrapper-receipt.json"
    if not receipt_path.is_file():
        raise RuntimeError("V41R33R1 wrapper receipt missing")
    try:
        receipt = json.loads(receipt_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("V41R33R1 wrapper receipt unreadable") from error
    expected = {
        "wrapper_sha256": sha256(wrapper.resolve()),
        "launcher_sha256": sha256(launcher.resolve()),
        "launcher_path": str(launcher.resolve()),
        "implementation_path": str(wrapper.resolve()),
        "archive_path": str(archive.resolve()),
        "archive_sha256": EXPECTED_ARCHIVE,
        "source_commit": EXPECTED_COMMIT,
        "source_archive_sha256": EXPECTED_ARCHIVE,
        "source_tree_sha256": EXPECTED_TREE,
        "run_id": RUN_ID,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise RuntimeError(f"V41R33R1 wrapper receipt mismatch: {key}")


def verify_source_snapshot(archive: Path, rgs_root: Path, wrapper: Path) -> None:
    if not archive.is_file() or sha256(archive.resolve()) != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R33R1 archive custody mismatch before source import")
    spec = importlib.util.spec_from_file_location("v41r33r1_snapshot_wrapper", wrapper)
    if spec is None or spec.loader is None:
        raise RuntimeError("V41R33R1 wrapper cannot be loaded for source preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    setattr(module, "EXPECTED_ARCHIVE", EXPECTED_ARCHIVE)
    setattr(module, "EXPECTED_TREE", EXPECTED_TREE)
    setattr(module, "RGS_ROOT", rgs_root.resolve())
    module.verify_archive(archive.resolve())
    actual_commit = subprocess.run(
        ["git", "get-tar-commit-id"],
        input=archive.resolve().read_bytes(), check=True, capture_output=True,
    ).stdout.decode().strip()
    if actual_commit != EXPECTED_COMMIT:
        raise RuntimeError("V41R33R1 extracted source commit mismatch")
    module.verify_extracted_tree(rgs_root.resolve())
    module.verify_source_files(rgs_root.resolve())
    binding_path = rgs_root.resolve() / ".astral-source-binding.json"
    try:
        binding = json.loads(binding_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError("V41R33R1 source archive binding unavailable") from error
    if binding != EXPECTED_SOURCE_BINDING:
        raise RuntimeError("V41R33R1 source archive binding mismatch")


def require_arm_order(completed: Sequence[str]) -> None:
    if list(completed) != ["control"]:
        raise RuntimeError("V41R33R1 arm order requires completed control first")


def require_fresh_output_root(output_root: Path) -> None:
    if output_root.exists() and any(output_root.iterdir()):
        raise RuntimeError("V41R33R1 execution identity is already consumed")


def verify_same_node_disk(cwd: Path, output_root: Path) -> dict[str, object]:
    cwd = cwd.resolve()
    output_parent = output_root.resolve().parent
    if os.stat(cwd).st_dev != os.stat(output_parent).st_dev:
        raise RuntimeError("V41R33R1 working directory and output are on different disks")
    return {
        "hostname": socket.gethostname(),
        "working_directory": str(cwd),
        "working_directory_device": os.stat(cwd).st_dev,
        "output_parent": str(output_parent),
        "output_parent_device": os.stat(output_parent).st_dev,
    }


def _run_and_validate(
    role: str,
    argv: list[str],
    output: Path,
    *,
    cwd: Path,
    environment: dict[str, str],
    validator: Path,
    rgs_root: Path,
    wrapper_receipt: tuple[Path, Path, Path] | None = None,
    validator_binding: dict[str, object] | None = None,
) -> tuple[int, int]:
    started_ns = time.time_ns()
    output.mkdir(parents=True, exist_ok=False)
    subprocess.run(argv, cwd=cwd.resolve(), env=environment, check=True)
    validator_digest = sha256(validator.resolve())
    if validator_digest != EXPECTED_VALIDATOR:
        raise RuntimeError(f"V41R33R1 {role} validator hash changed before invocation")
    validator_command = validator_argv(validator, output, rgs_root)
    if validator_binding is not None:
        validator_binding.update({
            "validator_sha256": validator_digest,
            "validator_path": str(validator.resolve()),
            "validator_recheck_ns": time.time_ns(),
            "validator_command_bytes": command_bytes(validator_command),
            "validator_command_sha256": digest_text(command_bytes(validator_command)),
        })
        (output / "validator-binding.json").write_text(
            json.dumps(validator_binding, indent=2, sort_keys=True) + "\n"
        )
    validator_started_ns = time.time_ns()
    validation = subprocess.run(
        validator_command,
        cwd=cwd.resolve(), env=environment, check=False, capture_output=True, text=True,
    )
    validator_finished_ns = time.time_ns()
    if validator_binding is not None:
        validator_binding.update({
            "validator_started_ns": validator_started_ns,
            "validator_finished_ns": validator_finished_ns,
            "validator_duration_ns": validator_finished_ns - validator_started_ns,
        })
        (output / "validator-binding.json").write_text(
            json.dumps(validator_binding, indent=2, sort_keys=True) + "\n"
        )
    (output / "validator-report.json").write_text(validation.stdout)
    if validation.returncode != 0:
        raise RuntimeError(f"V41R33R1 {role} validator rejected artifact")
    if wrapper_receipt is not None:
        archive, launcher, wrapper = wrapper_receipt
        verify_wrapper_receipt(output, archive=archive, launcher=launcher, wrapper=wrapper)
    return started_ns, time.time_ns()


def run_campaign(
    archive: Path,
    rgs_root: Path,
    output_root: Path,
    model_root: Path,
    hf_cache_root: Path,
    runtime_manifest: Path,
    *,
    launcher: Path = HERE / "v41r33r1_history_prelude_launcher.py",
    wrapper: Path = HERE / "v41r32r1_history_prelude_wrapper.py",
    validator: Path = HERE / "astral-v41r27-agem-retention" / "validate_worker.py",
    launch_argv: Sequence[str] | None = None,
) -> dict[str, object]:
    if not archive.is_file() or sha256(archive.resolve()) != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R33R1 archive custody mismatch")
    verify_runtime_hashes(launcher, wrapper, EXPECTED_LAUNCHER, EXPECTED_WRAPPER)
    verify_validator(validator, EXPECTED_VALIDATOR)
    verify_source_snapshot(archive, rgs_root, wrapper)
    runtime_custody = verify_runtime_custody(runtime_manifest)
    model_custody = verify_model_custody(model_root, hf_cache_root)
    require_fresh_output_root(output_root)
    execution_binding = verify_same_node_disk(rgs_root, output_root)
    if not output_root.exists():
        output_root.mkdir(parents=True)
    control = output_root / "control"
    intervention = output_root / "intervention"
    environment = {
        "RGS_ROOT": str(rgs_root.resolve()),
        "PYTHONPATH": str((rgs_root / "scripts").resolve()),
        "RGS_SOURCE_COMMIT": EXPECTED_COMMIT,
        "RGS_SOURCE_ARCHIVE_SHA256": EXPECTED_ARCHIVE,
        "V41R33R1_LAUNCHER_SHA256": EXPECTED_LAUNCHER,
        "V41R33R1_WRAPPER_SHA256": EXPECTED_WRAPPER,
        "V41R33R1_LAUNCH_ID": LAUNCH_ID,
        "V41R33R1_MODEL_ID": EXPECTED_MODEL_ID,
        "V41R33R1_MODEL_REVISION": EXPECTED_MODEL_REVISION,
        "V41R33R1_MODEL_MANIFEST_SHA256": EXPECTED_MODEL_MANIFEST,
        "V41R33R1_RUNTIME_IDENTITY": LAUNCH_ID,
        "V41R33R1_RUNTIME_MANIFEST_SHA256": EXPECTED_RUNTIME_MANIFEST,
        "V41R33R1_RUNTIME_MANIFEST": str(runtime_manifest.resolve()),
        "V41R33R1_MODEL_ROOT": str(model_root.resolve()),
        "V41R33R1_HF_CACHE_ROOT": str(hf_cache_root.resolve()),
        "HF_HOME": str(hf_cache_root.resolve()),
        "HF_HUB_CACHE": str((hf_cache_root / "hub").resolve()),
        "TRANSFORMERS_CACHE": str((hf_cache_root / "hub").resolve()),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_DATASETS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
    }
    ledger = output_root / "campaign-ledger.json"
    state: dict[str, object] = {
        "run_id": RUN_ID,
        "launch_id": LAUNCH_ID,
        "completed_arms": [],
        "validator": str(validator.resolve()),
        "execution_binding": execution_binding,
        "import_path": [str((rgs_root / "scripts").resolve())],
        "working_directory": str(rgs_root.resolve()),
        "wrapper_receipt_path": str((intervention / "v41r32r1-wrapper-receipt.json").resolve()),
        "model_custody": model_custody,
        "runtime_custody": runtime_custody,
        "coordinator_argv": list(launch_argv) if launch_argv is not None else None,
    }
    control_argv = command_argv("control", control, rgs_root=rgs_root)
    intervention_argv = command_argv(
        "intervention", intervention, archive=archive, launcher=launcher)
    validator_commands = {
        "control": validator_argv(validator, control, rgs_root),
        "intervention": validator_argv(validator, intervention, rgs_root),
    }
    state["validator_command_bytes"] = {
        role: command_bytes(argv) for role, argv in validator_commands.items()
    }
    state["validator_command_sha256"] = {
        role: digest_text(value) for role, value in state["validator_command_bytes"].items()
    }
    state["validator_sha256"] = {
        "control": EXPECTED_VALIDATOR,
        "intervention": EXPECTED_VALIDATOR,
    }
    state["environment"] = environment
    (output_root / "model-custody-binding.json").write_text(
        json.dumps(model_custody, indent=2, sort_keys=True) + "\n"
    )
    (output_root / "runtime-custody-binding.json").write_text(
        json.dumps(runtime_custody, indent=2, sort_keys=True) + "\n"
    )
    state["arm_command_bytes"] = {
        "control": command_bytes(control_argv),
        "intervention": command_bytes(intervention_argv),
    }
    state["arm_command_sha256"] = {
        role: digest_text(value) for role, value in state["arm_command_bytes"].items()
    }
    state["environment_sha256"] = digest_text(
        json.dumps(sorted(environment.items()), separators=(",", ":"), ensure_ascii=True)
    )
    ledger.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")

    verify_command("control", control_argv, control, rgs_root=rgs_root)
    control_started_ns, control_finished_ns = _run_and_validate(
        "control", control_argv, control, cwd=rgs_root, environment=environment,
        validator=validator, rgs_root=rgs_root,
        validator_binding={
            "arm": "control", "argv": validator_commands["control"],
            "argv_bytes": state["validator_command_bytes"]["control"],
        })
    state["completed_arms"] = ["control"]
    state["arm_timestamps_ns"] = {
        "control": {"started": control_started_ns, "finished": control_finished_ns},
    }
    ledger.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    require_arm_order(state["completed_arms"])

    intervention_execution_binding = verify_same_node_disk(rgs_root, output_root)
    if any(
        intervention_execution_binding[key] != execution_binding[key]
        for key in ("hostname", "working_directory_device", "output_parent_device")
    ):
        raise RuntimeError("V41R33R1 node or disk binding changed before intervention")
    state["execution_binding_before_intervention"] = intervention_execution_binding
    ledger.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")

    verify_command(
        "intervention", intervention_argv, intervention, archive=archive, launcher=launcher)
    intervention_started_ns, intervention_finished_ns = _run_and_validate(
        "intervention", intervention_argv, intervention, cwd=rgs_root,
        environment=environment, validator=validator, rgs_root=rgs_root,
        wrapper_receipt=(archive, launcher, wrapper),
        validator_binding={
            "arm": "intervention", "argv": validator_commands["intervention"],
            "argv_bytes": state["validator_command_bytes"]["intervention"],
        })
    state["completed_arms"] = ["control", "intervention"]
    state["arm_timestamps_ns"]["intervention"] = {
        "started": intervention_started_ns, "finished": intervention_finished_ns,
    }
    state["command_bytes"] = {
        "control": command_bytes(control_argv),
        "intervention": command_bytes(intervention_argv),
    }
    state["command_sha256"] = {
        role: digest_text(value) for role, value in state["command_bytes"].items()
    }
    ledger.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--rgs-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--hf-cache-root", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    launch_argv = [
        PYTHON,
        str(Path(__file__).resolve()),
        "--archive", str(args.archive.resolve()),
        "--rgs-root", str(args.rgs_root.resolve()),
        "--output-root", str(args.output_root.resolve()),
        "--model-root", str(args.model_root.resolve()),
        "--hf-cache-root", str(args.hf_cache_root.resolve()),
        "--runtime-manifest", str(args.runtime_manifest.resolve()),
    ]
    run_campaign(
        args.archive,
        args.rgs_root,
        args.output_root,
        args.model_root,
        args.hf_cache_root,
        args.runtime_manifest,
        launch_argv=launch_argv,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
