from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path


IMPLEMENTATION_ROOT = Path(
    "/Users/shaanp/.codex/worktrees/"
    "composed-zk-benchmark-os-astral-v28r2-validator"
)
IMPLEMENTATION_COMMIT = "8cf75d745c20afa885286fecfbd8d67c253b8707"
TOOL_ROOT = IMPLEMENTATION_ROOT / "tools/astral-rgs-acquisition-v28r2"
BUILDER = TOOL_ROOT / "build_retired_v28r1_fingerprint.py"
PROTOCOL = TOOL_ROOT / "protocol.json"
VALIDATOR_CORE = TOOL_ROOT / "v28r2.py"
VALIDATOR_CLI = TOOL_ROOT / "validate_packet.py"
INPUT_ROOT = Path(
    "/Users/shaanp/Documents/ResearchArtifacts/"
    "astral-rgs-v28-acquisition-novelty-a4e9dd0-r1"
)
PACKET = INPUT_ROOT / "acquisition-packet.json"
VALIDATION_REPORT = INPUT_ROOT / "astral-validation-report.json"
ARTIFACT_MANIFEST = INPUT_ROOT / "artifact-manifest.json"
OUTPUT = Path(
    "/Users/shaanp/Documents/ResearchArtifacts/"
    "astral-rgs-v28r1-retired-fingerprint-8cf75d7-r2.json"
)
GIT = Path("/usr/bin/git")
IMPLEMENTATION_FILE_SHA256 = {
    PROTOCOL: (
        "sha256:8ea8841769f7364fc3c0cc5e935f0eb24843f84ca95aa99b8cee9a1863117430"
    ),
    VALIDATOR_CORE: (
        "sha256:044fee8a7f3fc8fdb6d7bc474cb378c227d088c431a62448863c2aef3e935556"
    ),
    VALIDATOR_CLI: (
        "sha256:5e3cfda4f0aff0ab44f505a9e51ef6edff6e2b5798660c77f32580331cbddbc0"
    ),
    BUILDER: (
        "sha256:2bac334ee634c59a290a12784a52321d6fe7f80513d94d540ae07c17f4190324"
    ),
}
CANONICAL_PROTOCOL_SHA256 = (
    "sha256:236d7a2f4d8f81fdd1990c746cdfff0d3de85c191781bb7c3fde9d84d5b1aaf2"
)
INPUT_FILE_SHA256 = {
    PACKET: (
        "sha256:f3b5217e725322d2cf964267b63af4fb956a0232507ac646f07fbaf12a31c121"
    ),
    VALIDATION_REPORT: (
        "sha256:0ec4215734583566f593c6214eec2317523e0bc7471e6d9f837ca3e0337b53e9"
    ),
    ARTIFACT_MANIFEST: (
        "sha256:7ca7e09302aff508368d53335aa47c90564fa6393e262ecadc8db51e401ce5f7"
    ),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _canonical_sha256(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _absolute_prefixes(path: Path) -> list[Path]:
    if not path.is_absolute():
        raise ValueError(f"path is not absolute: {path}")
    prefixes = [path]
    prefixes.extend(path.parents)
    return list(reversed(prefixes))


def _validate_existing_path(path: Path, terminal: str) -> None:
    prefixes = _absolute_prefixes(path)
    for index, prefix in enumerate(prefixes):
        metadata = os.lstat(prefix)
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"symlink path component: {prefix}")
        is_terminal = index == len(prefixes) - 1
        if not is_terminal and not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"non-directory path ancestor: {prefix}")
        if is_terminal:
            if terminal == "directory" and not stat.S_ISDIR(metadata.st_mode):
                raise ValueError(f"terminal is not a directory: {prefix}")
            if terminal == "file" and not stat.S_ISREG(metadata.st_mode):
                raise ValueError(f"terminal is not a regular file: {prefix}")


def _validate_absent_output(path: Path) -> None:
    _validate_existing_path(path.parent, "directory")
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    raise ValueError(f"output already exists: {path}")


def _git_stdout(*arguments: str) -> str:
    completed = subprocess.run(
        [str(GIT), "-C", str(IMPLEMENTATION_ROOT), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    )
    return completed.stdout


def _validate_static_configuration() -> None:
    expected = {
        "implementation_root": (
            "/Users/shaanp/.codex/worktrees/"
            "composed-zk-benchmark-os-astral-v28r2-validator"
        ),
        "input_root": (
            "/Users/shaanp/Documents/ResearchArtifacts/"
            "astral-rgs-v28-acquisition-novelty-a4e9dd0-r1"
        ),
        "packet": (
            "/Users/shaanp/Documents/ResearchArtifacts/"
            "astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/"
            "acquisition-packet.json"
        ),
        "validation_report": (
            "/Users/shaanp/Documents/ResearchArtifacts/"
            "astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/"
            "astral-validation-report.json"
        ),
        "artifact_manifest": (
            "/Users/shaanp/Documents/ResearchArtifacts/"
            "astral-rgs-v28-acquisition-novelty-a4e9dd0-r1/"
            "artifact-manifest.json"
        ),
        "output": (
            "/Users/shaanp/Documents/ResearchArtifacts/"
            "astral-rgs-v28r1-retired-fingerprint-8cf75d7-r2.json"
        ),
    }
    observed = {
        "implementation_root": str(IMPLEMENTATION_ROOT),
        "input_root": str(INPUT_ROOT),
        "packet": str(PACKET),
        "validation_report": str(VALIDATION_REPORT),
        "artifact_manifest": str(ARTIFACT_MANIFEST),
        "output": str(OUTPUT),
    }
    if observed != expected:
        raise ValueError("fixed path configuration drift")
    if (
        PACKET.parent != INPUT_ROOT
        or VALIDATION_REPORT.parent != INPUT_ROOT
        or ARTIFACT_MANIFEST.parent != INPUT_ROOT
    ):
        raise ValueError("input root relationship drift")


def preflight() -> None:
    _validate_static_configuration()
    _validate_existing_path(GIT, "file")
    _validate_existing_path(IMPLEMENTATION_ROOT, "directory")
    _validate_existing_path(INPUT_ROOT, "directory")
    for path in (
        PROTOCOL,
        VALIDATOR_CORE,
        VALIDATOR_CLI,
        BUILDER,
        PACKET,
        VALIDATION_REPORT,
        ARTIFACT_MANIFEST,
    ):
        _validate_existing_path(path, "file")
    _validate_absent_output(OUTPUT)
    if _git_stdout("rev-parse", "HEAD").strip() != IMPLEMENTATION_COMMIT:
        raise ValueError("implementation commit drift")
    if _git_stdout("status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("implementation checkout is not clean")
    for path, expected in IMPLEMENTATION_FILE_SHA256.items():
        if _sha256_file(path) != expected:
            raise ValueError(f"implementation file drift: {path.name}")
    if _canonical_sha256(PROTOCOL) != CANONICAL_PROTOCOL_SHA256:
        raise ValueError("canonical protocol drift")
    for path, expected in INPUT_FILE_SHA256.items():
        if _sha256_file(path) != expected:
            raise ValueError(f"retained input drift: {path.name}")


def builder_argv() -> list[str]:
    return [
        sys.executable,
        str(BUILDER),
        "--packet",
        str(PACKET),
        "--validation-report",
        str(VALIDATION_REPORT),
        "--artifact-manifest",
        str(ARTIFACT_MANIFEST),
        "--output",
        str(OUTPUT),
    ]


def main(argv: list[str] | None = None) -> int:
    supplied = sys.argv[1:] if argv is None else argv
    if supplied:
        print("error: this controller accepts no arguments", file=sys.stderr)
        return 2
    try:
        preflight()
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            builder_argv(),
            check=False,
            env=environment,
        )
        if completed.returncode != 0:
            return completed.returncode
        _validate_existing_path(OUTPUT, "file")
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        subprocess.SubprocessError,
        ValueError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
