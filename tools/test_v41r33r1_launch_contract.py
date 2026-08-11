from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).parent

def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


WRAPPER = load("v41r33r1_wrapper", ROOT / "v41r32r1_history_prelude_wrapper.py")
COORDINATOR = load(
    "v41r33r1_coordinator", ROOT / "v41r33r1_history_dependence_coordinator.py"
)


def test_archive_mismatch_fails_closed(tmp_path: Path) -> None:
    archive = tmp_path / "archive.tar"
    archive.write_bytes(b"not-the-frozen-archive")
    expected = WRAPPER.EXPECTED_ARCHIVE
    try:
        WRAPPER.EXPECTED_ARCHIVE = "sha256:" + hashlib.sha256(b"frozen").hexdigest()
        try:
            WRAPPER.verify_archive(archive)
        except RuntimeError as error:
            assert "archive" in str(error)
        else:
            raise AssertionError("archive mismatch was accepted")
    finally:
        WRAPPER.EXPECTED_ARCHIVE = expected


def test_launcher_rejects_bad_archive_before_wrapper_import(tmp_path: Path) -> None:
    bad_archive = tmp_path / "bad.tar"
    bad_archive.write_bytes(b"bad")
    completed = subprocess.run(
        [sys.executable, str(ROOT / "v41r33r1_history_prelude_launcher.py"),
         "--output", str(tmp_path / "out"), "--archive", str(bad_archive)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert completed.returncode != 0
    assert "before wrapper import" in completed.stderr
    assert "ModuleNotFoundError" not in completed.stderr


def test_tree_mismatch_fails_closed(tmp_path: Path) -> None:
    (tmp_path / "worker.py").write_text("frozen\n")
    expected = WRAPPER.EXPECTED_TREE
    try:
        WRAPPER.EXPECTED_TREE = "sha256:" + "0" * 64
        try:
            WRAPPER.verify_extracted_tree(tmp_path)
        except RuntimeError as error:
            assert "tree" in str(error)
        else:
            raise AssertionError("tree mismatch was accepted")
    finally:
        WRAPPER.EXPECTED_TREE = expected


def test_source_tree_identity_matches_worker_algorithm(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("alpha\n")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "beta.txt").write_text("beta\n")
    (tmp_path / ".astral-source-binding.json").write_text("sidecar\n")
    rows = []
    for candidate in sorted(tmp_path.rglob("*")):
        if not candidate.is_file() or candidate.name == ".astral-source-binding.json":
            continue
        relative = candidate.relative_to(tmp_path).as_posix()
        rows.append({
            "path": relative,
            "sha256": "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest(),
        })
    canonical = json.dumps(
        rows, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    expected = "sha256:" + hashlib.sha256(canonical).hexdigest()
    assert WRAPPER.tree_manifest_sha256(tmp_path) == expected
    assert WRAPPER.EXPECTED_TREE == COORDINATOR.EXPECTED_TREE


def test_imported_module_mismatch_fails_closed(tmp_path: Path) -> None:
    module = tmp_path / "worker.py"
    module.write_text("frozen\n")
    expected = WRAPPER.EXPECTED_SOURCE_FILES.copy()
    try:
        WRAPPER.EXPECTED_SOURCE_FILES = {"worker.py": "sha256:" + "0" * 64}
        try:
            WRAPPER.verify_source_files(tmp_path)
        except RuntimeError as error:
            assert "source file" in str(error)
        else:
            raise AssertionError("source mismatch was accepted")
    finally:
        WRAPPER.EXPECTED_SOURCE_FILES = expected


def test_launcher_and_wrapper_mismatch_fails_closed(tmp_path: Path) -> None:
    launcher = tmp_path / "launcher.py"
    wrapper = tmp_path / "wrapper.py"
    launcher.write_text("launcher\n")
    wrapper.write_text("wrapper\n")
    try:
        COORDINATOR.verify_runtime_hashes(
            launcher,
            wrapper,
            "sha256:" + "0" * 64,
            "sha256:" + hashlib.sha256(wrapper.read_bytes()).hexdigest(),
        )
    except RuntimeError as error:
        assert "launcher" in str(error)
    else:
        raise AssertionError("launcher mismatch was accepted")


def test_wrong_argv_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "out"
    archive = tmp_path / "archive.tar"
    expected = COORDINATOR.command_argv("intervention", output, archive=archive)
    wrong = [*expected[:-1], "wrong-output"]
    try:
        COORDINATOR.verify_command("intervention", wrong, output, archive=archive)
    except RuntimeError as error:
        assert "command" in str(error)
    else:
        raise AssertionError("wrong command was accepted")


def test_custom_launcher_is_bound_into_intervention_argv(tmp_path: Path) -> None:
    launcher = tmp_path / "v41r33r1-launcher.py"
    archive = tmp_path / "archive.tar"
    argv = COORDINATOR.command_argv(
        "intervention", tmp_path / "out", archive=archive, launcher=launcher)
    assert argv[1] == str(launcher)
    COORDINATOR.verify_command(
        "intervention", argv, tmp_path / "out", archive=archive, launcher=launcher)
    relative = COORDINATOR.command_argv(
        "intervention", Path("relative-output"), archive=Path("relative-archive"),
        launcher=Path("relative-launcher"))
    assert Path(relative[1]).is_absolute()
    assert Path(relative[3]).is_absolute()
    assert Path(relative[5]).is_absolute()


def test_validator_commands_are_exact_per_arm(tmp_path: Path) -> None:
    validator = tmp_path / "validate_worker.py"
    root = tmp_path / "rgs"
    control = tmp_path / "control"
    intervention = tmp_path / "intervention"
    assert COORDINATOR.validator_argv(validator, control, root) == [
        COORDINATOR.PYTHON, str(validator.resolve()), "--artifact", str(control.resolve()),
        "--rgs-root", str(root.resolve())]
    assert COORDINATOR.validator_argv(validator, intervention, root)[3] == str(intervention)


def test_reversed_arm_order_fails_closed() -> None:
    try:
        COORDINATOR.require_arm_order(["intervention", "control"])
    except RuntimeError as error:
        assert "order" in str(error)
    else:
        raise AssertionError("reversed arm order was accepted")


def test_same_node_disk_binding_is_recorded(tmp_path: Path) -> None:
    binding = COORDINATOR.verify_same_node_disk(tmp_path, tmp_path / "output")
    assert binding["working_directory"] == str(tmp_path.resolve())
    assert binding["working_directory_device"] == binding["output_parent_device"]


def test_consumed_output_root_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "campaign-ledger.json").write_text("consumed\n")
    try:
        COORDINATOR.require_fresh_output_root(output)
    except RuntimeError as error:
        assert "consumed" in str(error)
    else:
        raise AssertionError("consumed output root was accepted")


def test_wrapper_receipt_missing_or_mismatched_fails_closed(tmp_path: Path) -> None:
    archive = tmp_path / "archive.tar"
    launcher = tmp_path / "launcher.py"
    wrapper = tmp_path / "wrapper.py"
    archive.write_bytes(b"archive")
    launcher.write_text("launcher")
    wrapper.write_text("wrapper")
    output = tmp_path / "output"
    output.mkdir()
    try:
        COORDINATOR.verify_wrapper_receipt(
            output, archive=archive, launcher=launcher, wrapper=wrapper)
    except RuntimeError as error:
        assert "receipt" in str(error)
    else:
        raise AssertionError("missing wrapper receipt was accepted")
    (output / "v41r32r1-wrapper-receipt.json").write_text("{}\n")
    try:
        COORDINATOR.verify_wrapper_receipt(
            output, archive=archive, launcher=launcher, wrapper=wrapper)
    except RuntimeError as error:
        assert "receipt" in str(error)
    else:
        raise AssertionError("mismatched wrapper receipt was accepted")


def test_validator_mismatch_fails_closed(tmp_path: Path) -> None:
    validator = tmp_path / "validate_worker.py"
    validator.write_text("validator\n")
    try:
        COORDINATOR.verify_validator(validator, "sha256:" + "0" * 64)
    except RuntimeError as error:
        assert "validator" in str(error)
    else:
        raise AssertionError("validator mismatch was accepted")


def test_model_custody_manifest_mismatch_fails_closed(tmp_path: Path) -> None:
    model_root = tmp_path / "model"
    cache_root = tmp_path / "cache"
    model_root.mkdir()
    cache_snapshot = cache_root / "hub" / "models--openai--gpt-oss-20b" / "snapshots" / COORDINATOR.EXPECTED_MODEL_REVISION
    cache_snapshot.mkdir(parents=True)
    (model_root / "model-custody-manifest.json").write_text(json.dumps({
        "model_id": COORDINATOR.EXPECTED_MODEL_ID,
        "revision": COORDINATOR.EXPECTED_MODEL_REVISION,
        "manifest_sha256": "sha256:" + "0" * 64,
        "files": [],
    }))
    try:
        COORDINATOR.verify_model_custody(model_root, cache_root)
    except RuntimeError as error:
        assert "file list" in str(error)
    else:
        raise AssertionError("model custody mismatch was accepted")


def test_runtime_custody_manifest_mismatch_fails_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "runtime-custody-manifest.json"
    manifest.write_text("{}\n")
    try:
        COORDINATOR.verify_runtime_custody(manifest)
    except RuntimeError as error:
        assert "runtime custody" in str(error)
    else:
        raise AssertionError("runtime custody mismatch was accepted")


def test_runtime_custody_accepts_exact_identity(tmp_path: Path) -> None:
    record = {
        "runtime_identity": "v41r33r1-runtime-custody-v1",
        "python": "3.10.12",
        "resolved_python": sys.executable,
        "sys_prefix": str(Path(sys.executable).parent.parent),
        "torch_base_version": "2.10.0",
        "cuda": "12.8",
        "transformers": "4.57.6",
        "peft": "0.18.1",
        "model_loaded": False,
        "worker_imported": False,
    }
    manifest = tmp_path / "runtime-custody-manifest.json"
    raw = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    manifest.write_text(raw)
    expected = COORDINATOR.EXPECTED_RUNTIME_MANIFEST
    try:
        COORDINATOR.EXPECTED_RUNTIME_MANIFEST = COORDINATOR.sha256(manifest)
        assert COORDINATOR.verify_runtime_custody(manifest) == record
    finally:
        COORDINATOR.EXPECTED_RUNTIME_MANIFEST = expected


def test_model_custody_requires_hard_bound_cache_files(tmp_path: Path) -> None:
    model_root = tmp_path / "model"
    cache_root = tmp_path / "cache"
    model_root.mkdir()
    cache_snapshot = cache_root / "hub" / "models--openai--gpt-oss-20b" / "snapshots" / COORDINATOR.EXPECTED_MODEL_REVISION
    cache_snapshot.mkdir(parents=True)
    payload = b"frozen-model-file\n"
    file_path = model_root / "config.json"
    file_path.write_bytes(payload)
    row = {
        "path": "config.json",
        "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
    }
    manifest_hash = COORDINATOR.model_manifest_rows_digest([row])
    manifest_path = model_root / "model-custody-manifest.json"
    manifest_path.write_text(json.dumps({
        "model_id": COORDINATOR.EXPECTED_MODEL_ID,
        "revision": COORDINATOR.EXPECTED_MODEL_REVISION,
        "manifest_sha256": manifest_hash,
        "files": [row],
    }))
    cached = cache_snapshot / "config.json"
    cached.write_bytes(payload)
    expected_manifest = COORDINATOR.EXPECTED_MODEL_MANIFEST
    expected_manifest_bytes = COORDINATOR.EXPECTED_MODEL_MANIFEST_BYTES
    try:
        COORDINATOR.EXPECTED_MODEL_MANIFEST = manifest_hash
        COORDINATOR.EXPECTED_MODEL_MANIFEST_BYTES = "sha256:" + "0" * 64
        try:
            COORDINATOR.verify_model_custody(model_root, cache_root)
        except RuntimeError as error:
            assert "bytes hash" in str(error)
        else:
            raise AssertionError("manifest byte mismatch was accepted")
        COORDINATOR.EXPECTED_MODEL_MANIFEST_BYTES = COORDINATOR.sha256(manifest_path)
        try:
            COORDINATOR.verify_model_custody(model_root, cache_root)
        except RuntimeError as error:
            assert "binding" in str(error)
        else:
            raise AssertionError("unbound model cache file was accepted")
    finally:
        COORDINATOR.EXPECTED_MODEL_MANIFEST = expected_manifest
        COORDINATOR.EXPECTED_MODEL_MANIFEST_BYTES = expected_manifest_bytes
