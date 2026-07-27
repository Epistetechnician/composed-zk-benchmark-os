#!/usr/bin/env python3
"""Shared fail-closed helpers for the Astral independent-review capsule."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SHA256 = re.compile(r"^[0-9a-f]{64}$")
RUNTIME_PACKAGES = ("mlx", "mlx-lm", "numpy", "pytest", "torch", "transformers")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def command_version(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    output = completed.stdout.strip() or completed.stderr.strip()
    if not output:
        raise ValueError(f"version command produced no output: {command[0]}")
    return output.splitlines()[0]


def observed_runtime() -> dict[str, Any]:
    packages = {}
    for name in RUNTIME_PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "absent"
    return {
        "python": sys.version,
        "python_executable_name": Path(sys.executable).name,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "packages": packages,
        "commands": {
            "cargo": command_version(["cargo", "--version"]),
            "git": command_version(["git", "--version"]),
            "rustc": command_version(["rustc", "--version"]),
        },
    }


def runtime_differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[dict[str, Any]]:
    differences = []
    for field in ("python", "python_executable_name", "platform", "machine", "processor"):
        if actual.get(field) != expected.get(field):
            differences.append(
                {"field": field, "expected": expected.get(field), "actual": actual.get(field)}
            )
    for group in ("packages", "commands"):
        expected_group = expected.get(group, {})
        actual_group = actual.get(group, {})
        for name in sorted(set(expected_group) | set(actual_group)):
            if actual_group.get(name) != expected_group.get(name):
                differences.append(
                    {
                        "field": f"{group}.{name}",
                        "expected": expected_group.get(name),
                        "actual": actual_group.get(name),
                    }
                )
    return differences


def _safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        value == path.as_posix()
        and not path.is_absolute()
        and value not in ("", ".")
        and ".." not in path.parts
    )


def _file_census(root: Path, manifest_name: str) -> set[str]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("capsule root must be a real directory")
    files = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"symlink forbidden: {path.relative_to(root)}")
        if path.is_file() and path.name != manifest_name:
            files.add(path.relative_to(root).as_posix())
    return files


def write_manifest(root: Path, manifest_name: str) -> str:
    rows = [
        f"{sha256(root / relative)}  {relative}"
        for relative in sorted(_file_census(root, manifest_name))
    ]
    value = "\n".join(rows) + "\n"
    manifest = root / manifest_name
    manifest.write_text(value)
    return hashlib.sha256(value.encode()).hexdigest()


def verify_manifest(root: Path, manifest_name: str) -> dict[str, Any]:
    manifest = root / manifest_name
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError(f"missing real manifest: {manifest_name}")
    rows: dict[str, str] = {}
    raw_lines = manifest.read_text().splitlines()
    for line in raw_lines:
        expected, separator, relative = line.partition("  ")
        if (
            not separator
            or not SHA256.fullmatch(expected)
            or not _safe_relative(relative)
            or relative in rows
            or relative == manifest_name
        ):
            raise ValueError("invalid manifest row")
        rows[relative] = expected
    if list(rows) != sorted(rows):
        raise ValueError("manifest rows are not sorted")
    actual = _file_census(root, manifest_name)
    if actual != set(rows):
        raise ValueError("manifest census mismatch")
    for relative, expected in rows.items():
        if sha256(root / relative) != expected:
            raise ValueError(f"manifest digest mismatch: {relative}")
    return {"file_count": len(rows), "identity": sha256(manifest)}


def verify_content_addressed_directory(
    root: Path, manifest_name: str, prefix: str, expected_identity: str
) -> dict[str, Any]:
    state = verify_manifest(root, manifest_name)
    if state["identity"] != expected_identity:
        raise ValueError("content identity differs from specification")
    if root.name != f"{prefix}-{expected_identity}":
        raise ValueError("content-addressed directory name mismatch")
    return state
