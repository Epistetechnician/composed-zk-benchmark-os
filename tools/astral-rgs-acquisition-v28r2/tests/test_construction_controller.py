from __future__ import annotations

import importlib.util
import os
import stat
from pathlib import Path

import pytest


TOOL_ROOT = Path(__file__).parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONTROLLER = _load_module(
    "v28r2_construction_controller",
    TOOL_ROOT / "construct_retired_v28r1_fingerprint.py",
)


def test_static_configuration_is_exact() -> None:
    CONTROLLER._validate_static_configuration()
    assert CONTROLLER.builder_argv() == [
        CONTROLLER.sys.executable,
        str(CONTROLLER.BUILDER),
        "--packet",
        str(CONTROLLER.PACKET),
        "--validation-report",
        str(CONTROLLER.VALIDATION_REPORT),
        "--artifact-manifest",
        str(CONTROLLER.ARTIFACT_MANIFEST),
        "--output",
        str(CONTROLLER.OUTPUT),
    ]


def test_existing_path_requires_exact_terminal_kind(tmp_path: Path) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    regular = directory / "regular"
    regular.write_bytes(b"fixed")
    CONTROLLER._validate_existing_path(directory, "directory")
    CONTROLLER._validate_existing_path(regular, "file")
    with pytest.raises(ValueError, match="not a regular file"):
        CONTROLLER._validate_existing_path(directory, "file")
    with pytest.raises(ValueError, match="not a directory"):
        CONTROLLER._validate_existing_path(regular, "directory")


def test_existing_path_rejects_symlink_component(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    target = real / "target"
    target.write_bytes(b"fixed")
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink path component"):
        CONTROLLER._validate_existing_path(link / "target", "file")


def test_absent_output_rejects_any_existing_terminal(tmp_path: Path) -> None:
    output = tmp_path / "output.json"
    CONTROLLER._validate_absent_output(output)
    output.write_bytes(b"fixed")
    with pytest.raises(ValueError, match="already exists"):
        CONTROLLER._validate_absent_output(output)
    output.unlink()
    output.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="already exists"):
        CONTROLLER._validate_absent_output(output)


def test_absolute_prefixes_reject_relative_path() -> None:
    with pytest.raises(ValueError, match="not absolute"):
        CONTROLLER._absolute_prefixes(Path("relative"))


def test_hash_helpers_are_deterministic(tmp_path: Path) -> None:
    value = tmp_path / "value.json"
    value.write_text('{"b":2,"a":1}\n', encoding="utf-8")
    assert CONTROLLER._sha256_file(value).startswith("sha256:")
    assert CONTROLLER._canonical_sha256(value) == (
        "sha256:43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    )


def test_controller_rejects_arguments_before_preflight(monkeypatch) -> None:
    called = False

    def forbidden() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(CONTROLLER, "preflight", forbidden)
    assert CONTROLLER.main(["unexpected"]) == 2
    assert not called


def test_source_has_no_network_or_dynamic_path_surface() -> None:
    source = (
        TOOL_ROOT / "construct_retired_v28r1_fingerprint.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "argparse",
        "input(",
        "eval(",
        "exec(",
    ):
        assert forbidden not in source
    assert stat.S_ISREG(os.lstat(CONTROLLER.GIT).st_mode)
