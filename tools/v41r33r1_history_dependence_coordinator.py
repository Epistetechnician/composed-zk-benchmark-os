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
PYTHON = str(Path(sys.executable).resolve())
RUN_ID = "v41r27-panel-8-seed-412019"
EXPECTED_ARCHIVE = "sha256:1b2d2e6c96b89749cddd2e48a727f08a090a21634bf9c48c12734a2174968580"
EXPECTED_TREE = "sha256:652633475af44cd6053b9dec6f44c7420c2668eb0e9253c4b994e9199ff9b9f5"
EXPECTED_WRAPPER = "sha256:e3fb6e35082d078734375c4e93d070d2ad8a7107c7cf4c0dc320949f24f8b4a5"
EXPECTED_LAUNCHER = "sha256:1c12648503f39c4c1aae4bcc5cddedcf7c545b37ca50d8e012445e76d3a4169e"
EXPECTED_VALIDATOR = "sha256:f1b9f45cfc7d58812b0f72fba890d3ccb274224b578a74e9f87d584af645dfd4"
EXPECTED_COMMIT = "754220f7fc360d8dd15e5837190b895ea0550f30"


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
    *,
    launcher: Path = HERE / "v41r33r1_history_prelude_launcher.py",
    wrapper: Path = HERE / "v41r32r1_history_prelude_wrapper.py",
    validator: Path = HERE / "astral-v41r27-agem-retention" / "validate_worker.py",
) -> dict[str, object]:
    if not archive.is_file() or sha256(archive.resolve()) != EXPECTED_ARCHIVE:
        raise RuntimeError("V41R33R1 archive custody mismatch")
    verify_runtime_hashes(launcher, wrapper, EXPECTED_LAUNCHER, EXPECTED_WRAPPER)
    verify_validator(validator, EXPECTED_VALIDATOR)
    verify_source_snapshot(archive, rgs_root, wrapper)
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
    }
    ledger = output_root / "campaign-ledger.json"
    state: dict[str, object] = {
        "run_id": RUN_ID,
        "completed_arms": [],
        "validator": str(validator.resolve()),
        "execution_binding": execution_binding,
        "import_path": [str((rgs_root / "scripts").resolve())],
        "working_directory": str(rgs_root.resolve()),
        "wrapper_receipt_path": str((intervention / "v41r32r1-wrapper-receipt.json").resolve()),
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
    args = parser.parse_args(argv)
    run_campaign(args.archive, args.rgs_root, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
