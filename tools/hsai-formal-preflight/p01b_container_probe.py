#!/usr/bin/env python3
"""Retained P01B native/container probe for Phase 796-A3L6.

State slice: phase-796a3l6-hsai-p01b-execution-evidence-implementation.

The module has three closed modes.  ``native-reference`` and ``normal`` build
the same synthetic gzip/USTAR bytes and exercise the existing transactional
archive-ledger publisher.  ``oom-child`` deliberately avoids importing the
archive parser and proves one survivor-collector/child OOM topology.
"""

import base64
import binascii
import hashlib
import json
import os
import pathlib
import platform
import re
import resource
import selectors
import signal
import stat
import struct
import subprocess
import sys
import sysconfig
import tempfile
import time
import zlib
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


PROBE_SCHEMA = "hsai-p01b-probe-result-v2"
ERROR_SCHEMA = "hsai-p01b-container-probe-error-v1"
PROJECTION_DOMAIN = b"hsai:p01b-container-projection:v1\0"
STDLIB_DOMAIN = b"hsai:p01b-container-stdlib:v1\0"
DEPENDENCIES_DOMAIN = b"hsai:p01b-container-dependencies:v1\0"
PACKAGES_DOMAIN = b"hsai:p01b-container-packages:v1\0"
MAX_RESULT_BYTES = 1_048_576
IDENTITY_STDOUT_CAP = 262_144
IDENTITY_STDERR_CAP = 262_144
WORKLOAD_STDOUT_CAP = 65_536
WORKLOAD_STDERR_CAP = 65_536
PROCESS_REAP_TIMEOUT_SECONDS = 5
ALLOCATION_BYTES = 640 * 1024 * 1024
EXPECTED_INPUT_FILES = 22
EXPECTED_TESTS = 151
OUTPUT_PATH = "/work/result.json"
READY_PREFIX = b"P01B_RESULT_READY "
OOM_READY_TOKEN = b"P01B_OOM_CHILD_READY\n"
OOM_RELEASE_TOKEN = b"P01B_OOM_CHILD_RELEASE\n"

MANIFEST_EXCLUDED_FIELDS = (
    "python_version",
    "zlib_version",
    "archive_device",
    "archive_inode",
    "archive_mode",
    "archive_owner_uid",
    "archive_link_count",
    "archive_modified_seconds",
    "archive_modified_nanoseconds",
    "archive_changed_seconds",
    "archive_changed_nanoseconds",
)
STATUS_EXCLUDED_FIELDS = ("manifest_bytes", "manifest_sha256")

CGROUP_FILES = (
    "cgroup.procs",
    "cgroup.events",
    "memory.current",
    "memory.max",
    "memory.swap.current",
    "memory.peak",
    "memory.min",
    "memory.low",
    "memory.high",
    "memory.swap.max",
    "memory.swap.events",
    "memory.oom.group",
    "memory.events",
    "memory.events.local",
    "pids.current",
    "pids.max",
    "pids.events",
    "cpu.max",
    "cpu.stat",
)
NAMESPACE_KINDS = ("pid", "uts", "mnt", "net", "ipc", "cgroup", "user")

INPUT_PATHS = (
    "docs/796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md",
    "tools/hsai-formal-preflight/bounded_runner.py",
    "tools/hsai-formal-preflight/execution_state_machine.py",
    "tools/hsai-formal-preflight/fixture_validator.py",
    "tools/hsai-formal-preflight/p01b_archive_ledger.py",
    "tools/hsai-formal-preflight/raw_archive_validator.py",
    "tools/hsai-formal-preflight/tests/test_bounded_runner.py",
    "tools/hsai-formal-preflight/tests/test_execution_state_machine.py",
    "tools/hsai-formal-preflight/tests/test_fixture_validator.py",
    "tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py",
    "tools/hsai-formal-preflight/tests/test_p01b_container_corpus.py",
    "tools/hsai-formal-preflight/tests/test_raw_archive_validator.py",
    "tools/hsai-formal-preflight/p01b_container_corpus.py",
    "tools/hsai-formal-preflight/p01b_container_test_corpus.json",
    "tools/hsai-formal-preflight/p01b_container_seccomp.json",
    "tools/hsai-formal-preflight/p01b_container_seccomp_license.txt",
    "tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json",
    "tools/hsai-formal-preflight/p01b_container_probe.py",
    "tools/hsai-formal-preflight/p01b_container_evidence.py",
    "tools/hsai-formal-preflight/p01b_container_execution.py",
    "tools/hsai-formal-preflight/p01b_container_execution_tests.py",
    "tools/hsai-formal-preflight/p01b_container_evidence_tests.py",
)
INPUT_FILE_LIMIT = 16_777_216
SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")

NATIVE_FIELDS = {
    "schema",
    "mode",
    "probe_sha256",
    "fixture_base64",
    "header_ledger_base64",
    "inventory_ledger_base64",
    "manifest_projection",
    "status_projection",
    "excluded_telemetry",
    "projection_sha256",
    "runtime",
}
NORMAL_FIELDS = NATIVE_FIELDS | {
    "input_manifest_sha256",
    "corpus_validation",
    "workload",
    "security",
    "cgroup_pre",
    "cgroup_terminal",
    "mounts",
    "rlimits",
}
OOM_FIELDS = {
    "schema",
    "mode",
    "probe_sha256",
    "input_manifest_sha256",
    "security",
    "cgroup_pre",
    "cgroup_terminal",
    "mounts",
    "rlimits",
    "parent",
    "child",
    "workload",
}


class ProbeError(Exception):
    """One fail-closed probe rejection."""


class _BoundedProcessError(subprocess.SubprocessError):
    """One bounded child-process supervision failure."""


def _validate_json(value: Any, seen: Optional[Set[int]] = None) -> None:
    if value is None or isinstance(value, (bool, str)) or type(value) is int:
        return
    if isinstance(value, float):
        raise ProbeError("floating-point JSON is forbidden")
    if seen is None:
        seen = set()
    if isinstance(value, list):
        identity = id(value)
        if identity in seen:
            raise ProbeError("cyclic JSON")
        seen.add(identity)
        for item in value:
            _validate_json(item, seen)
        seen.remove(identity)
        return
    if isinstance(value, dict):
        identity = id(value)
        if identity in seen:
            raise ProbeError("cyclic JSON")
        seen.add(identity)
        for key, item in value.items():
            if not isinstance(key, str):
                raise ProbeError("non-string JSON key")
            _validate_json(item, seen)
        seen.remove(identity)
        return
    raise ProbeError("unsupported JSON value")


def canonical_json_bytes(value: Any) -> bytes:
    """Return the closed ASCII, sorted-key, newline-free JSON encoding."""
    _validate_json(value)
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ProbeError("canonical JSON failure") from error


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _domain_sha256(domain: bytes, value: Any) -> str:
    return _sha256(domain + canonical_json_bytes(value))


def _base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _monotonic_ns() -> int:
    value = time.monotonic_ns()
    if type(value) is not int or value <= 0:
        raise ProbeError("monotonic clock differs")
    return value


def _stat_identity(value: os.stat_result, include_size: bool = True) -> Tuple[int, ...]:
    """Return the stable descriptor fields used around one bounded read."""
    identity = (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_uid,
        value.st_gid,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )
    return identity + ((value.st_size,) if include_size else ())


def _read_all(path: pathlib.Path, limit: int) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise ProbeError("required file stat failed: " + str(path)) from error
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise ProbeError("required file is not regular: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags)
    except OSError as error:
        raise ProbeError("required file open failed: " + str(path)) from error
    try:
        after = os.fstat(fd)
        if _stat_identity(before) != _stat_identity(after):
            raise ProbeError("required file identity drift: " + str(path))
        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65_536, limit + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ProbeError("required file exceeds limit: " + str(path))
            chunks.append(chunk)
        data = b"".join(chunks)
        if len(data) != after.st_size:
            raise ProbeError("required file short read: " + str(path))
        final = os.fstat(fd)
        if _stat_identity(after) != _stat_identity(final):
            raise ProbeError("required file identity drift after read: " + str(path))
        return data
    except OSError as error:
        raise ProbeError("required file read failed: " + str(path)) from error
    finally:
        os.close(fd)


def _read_pseudo_file(path: pathlib.Path, limit: int) -> bytes:
    """Read one procfs/sysfs regular node whose reported size may be zero."""
    try:
        before = path.lstat()
    except OSError as error:
        raise ProbeError("pseudo-file stat failed: " + str(path)) from error
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise ProbeError("pseudo-file is not regular: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags)
    except OSError as error:
        raise ProbeError("pseudo-file open failed: " + str(path)) from error
    try:
        after = os.fstat(fd)
        if _stat_identity(before, include_size=False) != _stat_identity(
            after, include_size=False
        ):
            raise ProbeError("pseudo-file identity drift: " + str(path))
        chunks: List[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65_536, limit + 1 - total))
            if not chunk:
                final = os.fstat(fd)
                if _stat_identity(after, include_size=False) != _stat_identity(
                    final, include_size=False
                ):
                    raise ProbeError(
                        "pseudo-file identity drift after read: " + str(path)
                    )
                return b"".join(chunks)
            total += len(chunk)
            if total > limit:
                raise ProbeError("pseudo-file exceeds limit: " + str(path))
            chunks.append(chunk)
    except OSError as error:
        raise ProbeError("pseudo-file read failed: " + str(path)) from error
    finally:
        os.close(fd)


def _readlink_stable(path: pathlib.Path, label: str) -> bytes:
    """Read one symlink target and reject path identity or target drift."""
    try:
        before = path.lstat()
        if not stat.S_ISLNK(before.st_mode):
            raise ProbeError(label + " is not a symlink")
        target = os.readlink(str(path))
        after = path.lstat()
    except OSError as error:
        raise ProbeError(label + " read failed") from error
    if _stat_identity(before) != _stat_identity(after):
        raise ProbeError(label + " identity drift")
    target_bytes = os.fsencode(target)
    return target_bytes


def _source_path() -> pathlib.Path:
    return pathlib.Path(__file__).absolute()


def _source_root() -> pathlib.Path:
    path = _source_path()
    try:
        return path.parents[2]
    except IndexError as error:
        raise ProbeError("probe path has no source root") from error


def _probe_sha256() -> str:
    return _sha256(_read_all(_source_path(), 2_000_000))


def _string_field(value: bytes, width: int) -> bytes:
    if not value or len(value) >= width or b"\0" in value:
        raise ProbeError("invalid USTAR string")
    return value + bytes(width - len(value))


def _octal_field(value: int, width: int) -> bytes:
    if type(value) is not int or value < 0:
        raise ProbeError("invalid USTAR integer")
    digits = format(value, "o").encode("ascii")
    if len(digits) > width - 1:
        raise ProbeError("USTAR integer overflow")
    return b"0" * (width - 1 - len(digits)) + digits + b"\0"


def _checksum_field(value: int) -> bytes:
    digits = format(value, "06o").encode("ascii")
    if len(digits) != 6:
        raise ProbeError("USTAR checksum overflow")
    return digits + b"\0 "


def _ustar_header(
    name: bytes, size: int, member_type: bytes, prefix: bytes = b""
) -> bytes:
    header = bytearray(512)
    header[0:100] = _string_field(name, 100)
    header[100:108] = _octal_field(0o644 if member_type == b"0" else 0o755, 8)
    header[108:116] = _octal_field(0, 8)
    header[116:124] = _octal_field(0, 8)
    header[124:136] = _octal_field(size, 12)
    header[136:148] = _octal_field(0, 12)
    header[148:156] = b"        "
    header[156:157] = member_type
    header[157:257] = bytes(100)
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    header[265:297] = _string_field(b"root", 32)
    header[297:329] = _string_field(b"root", 32)
    header[329:337] = _octal_field(0, 8)
    header[337:345] = _octal_field(0, 8)
    header[345:500] = _string_field(prefix, 155) if prefix else bytes(155)
    header[500:512] = bytes(12)
    header[148:156] = _checksum_field(sum(header))
    return bytes(header)


def _tar_member(
    name: bytes,
    payload: bytes = b"",
    member_type: bytes = b"0",
    prefix: bytes = b"",
) -> bytes:
    size = 0 if member_type == b"5" else len(payload)
    padding = bytes((-size) % 512)
    return _ustar_header(name, size, member_type, prefix) + payload + padding


def build_safe_fixture() -> bytes:
    """Build fixed USTAR plus a raw stored-DEFLATE gzip member."""
    tar_bytes = (
        _tar_member(b"dir/", member_type=b"5")
        + _tar_member(b"file.txt", b"payload", prefix=b"dir")
        + bytes(1024)
    )
    if len(tar_bytes) > 65_535:
        raise AssertionError("fixture exceeds one stored DEFLATE block")
    length = len(tar_bytes)
    raw_deflate = b"\x01" + struct.pack("<HH", length, length ^ 0xFFFF) + tar_bytes
    header = b"\x1f\x8b\x08\x00" + bytes(4) + b"\x00\xff"
    trailer = struct.pack(
        "<II", binascii.crc32(tar_bytes) & 0xFFFFFFFF, length & 0xFFFFFFFF
    )
    return header + raw_deflate + trailer


def _strict_json_line(data: bytes) -> Dict[str, Any]:
    if not data.endswith(b"\n") or data.count(b"\n") != 1:
        raise ProbeError("candidate JSON line framing differs")

    def reject_duplicates(pairs: Iterable[Tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProbeError("candidate JSON has duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(
            data[:-1].decode("ascii"), object_pairs_hook=reject_duplicates
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ProbeError("candidate JSON decode failed") from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != data[:-1]:
        raise ProbeError("candidate JSON is noncanonical")
    return value


def _archive_projection() -> Dict[str, Any]:
    # Lazy import is a hard mode boundary: oom-child never imports archive code.
    try:
        import p01b_archive_ledger as archive_ledger
    except ImportError as error:
        raise ProbeError("archive-ledger module unavailable") from error

    fixture = build_safe_fixture()
    temporary_parent = os.path.realpath(tempfile.gettempdir())
    try:
        with tempfile.TemporaryDirectory(
            prefix="p01b-probe-", dir=temporary_parent
        ) as temporary:
            parent = pathlib.Path(temporary)
            os.chmod(str(parent), 0o700)
            candidate = pathlib.Path(
                archive_ledger.publish_synthetic_candidate_for_test(
                    fixture, str(parent)
                )
            )
            status = archive_ledger.validate_published_candidate_for_test(
                str(candidate)
            )
            if status.get("decision") != "candidate_generated":
                raise ProbeError("synthetic candidate validation failed")
            manifest_bytes = _read_all(
                candidate / archive_ledger.MANIFEST_FILENAME,
                archive_ledger.MAX_MANIFEST_BYTES,
            )
            header_bytes = _read_all(
                candidate / archive_ledger.HEADER_LEDGER_FILENAME,
                archive_ledger.MAX_HEADER_LEDGER_BYTES,
            )
            inventory_bytes = _read_all(
                candidate / archive_ledger.INVENTORY_LEDGER_FILENAME,
                archive_ledger.MAX_INVENTORY_LEDGER_BYTES,
            )
            status_bytes = _read_all(
                candidate / archive_ledger.STATUS_FILENAME,
                archive_ledger.MAX_STATUS_BYTES,
            )
    except archive_ledger.ArchiveLedgerError as error:
        raise ProbeError(
            "archive-ledger rejected synthetic candidate: " + error.failure_class
        ) from error

    manifest = _strict_json_line(manifest_bytes)
    status_document = _strict_json_line(status_bytes)
    if not set(MANIFEST_EXCLUDED_FIELDS).issubset(manifest):
        raise ProbeError("manifest telemetry fields are missing")
    if not set(STATUS_EXCLUDED_FIELDS).issubset(status_document):
        raise ProbeError("status telemetry fields are missing")
    manifest_projection = {
        key: value
        for key, value in manifest.items()
        if key not in MANIFEST_EXCLUDED_FIELDS
    }
    status_projection = {
        key: value
        for key, value in status_document.items()
        if key not in STATUS_EXCLUDED_FIELDS
    }
    excluded_telemetry = {
        "manifest": {key: manifest[key] for key in MANIFEST_EXCLUDED_FIELDS},
        "status": {key: status_document[key] for key in STATUS_EXCLUDED_FIELDS},
    }
    projection_subject = {
        "header_ledger_sha256": _sha256(header_bytes),
        "inventory_ledger_sha256": _sha256(inventory_bytes),
        "normalized_manifest_sha256": _sha256(
            canonical_json_bytes(manifest_projection)
        ),
        "normalized_status_sha256": _sha256(canonical_json_bytes(status_projection)),
    }
    return {
        "fixture_base64": _base64(fixture),
        "header_ledger_base64": _base64(header_bytes),
        "inventory_ledger_base64": _base64(inventory_bytes),
        "manifest_projection": manifest_projection,
        "status_projection": status_projection,
        "excluded_telemetry": excluded_telemetry,
        "projection_sha256": _domain_sha256(PROJECTION_DOMAIN, projection_subject),
    }


def _inventory_regular_files(
    root: pathlib.Path,
    reject_nonregular: bool = True,
    file_limit: int = MAX_RESULT_BYTES * 256,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        root_stat = root.lstat()
    except OSError as error:
        raise ProbeError("inventory root stat failed") from error
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
        raise ProbeError("inventory root is not a directory")
    for directory, directory_names, file_names in os.walk(str(root), followlinks=False):
        directory_names.sort()
        file_names.sort()
        retained_directories: List[str] = []
        for name in directory_names:
            candidate = pathlib.Path(directory) / name
            if candidate.is_symlink():
                if reject_nonregular:
                    raise ProbeError("inventory contains directory symlink")
                continue
            retained_directories.append(name)
        directory_names[:] = retained_directories
        for name in file_names:
            path = pathlib.Path(directory) / name
            relative = path.relative_to(root).as_posix()
            path_stat = path.lstat()
            if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
                if reject_nonregular:
                    raise ProbeError("inventory contains nonregular file")
                continue
            data = _read_all(path, file_limit)
            rows.append(
                {
                    "path": relative,
                    "mode": format(stat.S_IMODE(path_stat.st_mode), "04o"),
                    "bytes": len(data),
                    "sha256": _sha256(data),
                }
            )
    rows.sort(key=lambda row: row["path"])
    if len({row["path"] for row in rows}) != len(rows):
        raise ProbeError("inventory paths are not unique")
    return rows


def _validate_input_manifest_sha256(value: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ProbeError("input manifest digest must be 64 lowercase hex characters")
    return value


def _validate_mounted_input_tree(root: pathlib.Path) -> None:
    """Validate the exact immutable container-visible 22-file tree."""
    entries = _inventory_regular_files(root, file_limit=INPUT_FILE_LIMIT)
    paths = [entry["path"] for entry in entries]
    expected_paths = sorted(INPUT_PATHS)
    if (
        len(INPUT_PATHS) != EXPECTED_INPUT_FILES
        or len(set(INPUT_PATHS)) != EXPECTED_INPUT_FILES
        or paths != expected_paths
    ):
        raise ProbeError("input snapshot path census differs")
    if any(entry["mode"] != "0444" for entry in entries):
        raise ProbeError("input snapshot file mode differs")
    for entry in entries:
        path = root.joinpath(*pathlib.PurePosixPath(entry["path"]).parts)
        try:
            metadata = path.lstat()
        except OSError as error:
            raise ProbeError("input snapshot file restat failed") from error
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size != entry["bytes"]
        ):
            raise ProbeError("input snapshot file identity differs")
    expected_directories = {"."}
    for relative in INPUT_PATHS:
        parts = pathlib.PurePosixPath(relative).parts[:-1]
        for count in range(1, len(parts) + 1):
            expected_directories.add(pathlib.PurePosixPath(*parts[:count]).as_posix())
    actual_directories: Set[str] = set()
    for directory, directory_names, _file_names in os.walk(
        str(root), followlinks=False
    ):
        directory_names.sort()
        path = pathlib.Path(directory)
        relative = path.relative_to(root).as_posix()
        try:
            metadata = path.lstat()
        except OSError as error:
            raise ProbeError("input snapshot directory stat failed") from error
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o555
        ):
            raise ProbeError("input snapshot directory identity differs")
        actual_directories.add(relative)
    if actual_directories != expected_directories:
        raise ProbeError("input snapshot directory census differs")


def _symlink_chain(path: str) -> Tuple[List[Dict[str, Any]], pathlib.Path]:
    current = pathlib.Path(path)
    if not current.is_absolute():
        raise ProbeError("executable path is not absolute")
    chain: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for _ in range(32):
        current_string = str(current)
        if current_string in seen:
            raise ProbeError("symlink cycle")
        seen.add(current_string)
        try:
            current_stat = current.lstat()
        except OSError as error:
            raise ProbeError("executable chain stat failed") from error
        if stat.S_ISLNK(current_stat.st_mode):
            target_bytes = _readlink_stable(current, "executable chain link")
            target = os.fsdecode(target_bytes)
            chain.append(
                {
                    "kind": "symlink",
                    "path": current_string,
                    "mode": stat.S_IMODE(current_stat.st_mode),
                    "target_base64": _base64(target_bytes),
                    "bytes": len(target_bytes),
                    "sha256": _sha256(target_bytes),
                }
            )
            current = (
                pathlib.Path(target)
                if pathlib.Path(target).is_absolute()
                else current.parent / target
            )
            current = pathlib.Path(os.path.normpath(str(current)))
            continue
        if not stat.S_ISREG(current_stat.st_mode):
            raise ProbeError("executable terminal is not regular")
        terminal_bytes = _read_all(current, 256 * 1024 * 1024)
        try:
            final_stat = current.lstat()
        except OSError as error:
            raise ProbeError("executable terminal restat failed") from error
        if _stat_identity(current_stat) != _stat_identity(final_stat):
            raise ProbeError("executable terminal identity drift")
        chain.append(
            {
                "kind": "regular",
                "path": current_string,
                "mode": stat.S_IMODE(current_stat.st_mode),
                "target_base64": None,
                "bytes": len(terminal_bytes),
                "sha256": _sha256(terminal_bytes),
            }
        )
        return chain, current
    raise ProbeError("executable symlink chain is too deep")


def _file_identity(path: str) -> Dict[str, Any]:
    chain, terminal = _symlink_chain(path)
    terminal_rows = [row for row in chain if row["path"] == str(terminal)]
    if len(terminal_rows) != 1:
        raise ProbeError("terminal executable inventory differs")
    return {
        "path": path,
        "chain": chain,
        "terminal_path": str(terminal),
        "bytes": terminal_rows[0]["bytes"],
        "sha256": terminal_rows[0]["sha256"],
    }


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    """Kill one isolated process group and reap its leader within a fixed bound."""
    group_error: Optional[OSError] = None
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as error:
        group_error = error
        try:
            process.kill()
        except ProcessLookupError:
            pass
        except OSError as kill_error:
            raise _BoundedProcessError("process termination failed") from kill_error
    try:
        process.wait(timeout=PROCESS_REAP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        except OSError as error:
            raise _BoundedProcessError("process termination failed") from error
        try:
            process.wait(timeout=PROCESS_REAP_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as error:
            raise _BoundedProcessError("process reaping timed out") from error
    if group_error is not None:
        raise _BoundedProcessError("process-group termination failed") from group_error


def _run_bounded_command(
    argv: Sequence[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    timeout_seconds: int,
    stdout_cap: int,
    stderr_cap: int,
) -> Tuple[int, bytes, bytes]:
    """Run direct argv with concurrent cap+1 stream reads and a hard deadline."""
    if (
        not argv
        or not all(isinstance(item, str) and "\x00" not in item for item in argv)
        or type(timeout_seconds) is not int
        or timeout_seconds <= 0
        or type(stdout_cap) is not int
        or stdout_cap < 0
        or type(stderr_cap) is not int
        or stderr_cap < 0
    ):
        raise _BoundedProcessError("bounded command contract differs")
    started_ns = _monotonic_ns()
    deadline_ns = started_ns + timeout_seconds * 1_000_000_000
    process = subprocess.Popen(
        list(argv),
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        start_new_session=True,
    )
    if process.stdout is None or process.stderr is None:
        _terminate_process_group(process)
        raise _BoundedProcessError("bounded command pipes unavailable")
    streams = {
        "stdout": (process.stdout, stdout_cap, bytearray()),
        "stderr": (process.stderr, stderr_cap, bytearray()),
    }
    selector = selectors.DefaultSelector()
    try:
        for name, (pipe, cap, _buffer) in streams.items():
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, (name, cap))
        while selector.get_map():
            remaining_ns = deadline_ns - _monotonic_ns()
            if remaining_ns <= 0:
                _terminate_process_group(process)
                raise _BoundedProcessError("bounded command timed out")
            events = selector.select(remaining_ns / 1_000_000_000)
            if not events:
                if _monotonic_ns() >= deadline_ns:
                    _terminate_process_group(process)
                    raise _BoundedProcessError("bounded command timed out")
                continue
            for key, _event_mask in events:
                name, cap = key.data
                pipe = key.fileobj
                buffer = streams[name][2]
                read_limit = min(65_536, cap + 1 - len(buffer))
                if read_limit <= 0:
                    _terminate_process_group(process)
                    raise _BoundedProcessError(name + " cap exceeded")
                try:
                    chunk = os.read(pipe.fileno(), read_limit)
                except BlockingIOError:
                    continue
                except OSError as error:
                    _terminate_process_group(process)
                    raise _BoundedProcessError(name + " read failed") from error
                if chunk:
                    buffer.extend(chunk)
                    if len(buffer) > cap:
                        _terminate_process_group(process)
                        raise _BoundedProcessError(name + " cap exceeded")
                    continue
                selector.unregister(pipe)
                pipe.close()
        remaining_ns = deadline_ns - _monotonic_ns()
        if remaining_ns <= 0:
            _terminate_process_group(process)
            raise _BoundedProcessError("bounded command timed out")
        try:
            returncode = process.wait(timeout=remaining_ns / 1_000_000_000)
        except subprocess.TimeoutExpired as error:
            _terminate_process_group(process)
            raise _BoundedProcessError("bounded command timed out") from error
    except _BoundedProcessError:
        raise
    except (OSError, ProbeError, ValueError) as error:
        _terminate_process_group(process)
        raise _BoundedProcessError("bounded command supervision failed") from error
    except BaseException:
        _terminate_process_group(process)
        raise
    finally:
        selector.close()
        for pipe, _cap, _buffer in streams.values():
            if not pipe.closed:
                pipe.close()
    return returncode, bytes(streams["stdout"][2]), bytes(streams["stderr"][2])


def _run_identity_command(argv: Sequence[str]) -> bytes:
    try:
        returncode, stdout, stderr = _run_bounded_command(
            argv,
            cwd="/",
            env={
                "HOME": "/nonexistent",
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": "/usr/bin:/bin",
            },
            timeout_seconds=30,
            stdout_cap=IDENTITY_STDOUT_CAP,
            stderr_cap=IDENTITY_STDERR_CAP,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ProbeError("runtime identity command failed") from error
    if returncode != 0 or stderr:
        raise ProbeError("runtime identity command rejected")
    return stdout


def _dependency_paths(output: bytes, darwin: bool) -> List[str]:
    try:
        text = output.decode("ascii")
    except UnicodeDecodeError as error:
        raise ProbeError("dependency output is not ASCII") from error
    paths: Set[str] = set()
    for line in text.splitlines()[1 if darwin else 0 :]:
        if darwin:
            candidate = line.strip().split(" ", 1)[0]
            if candidate.startswith("/"):
                paths.add(candidate)
            continue
        match = re.search(r"(?:=>\s+)?(/[^\s(]+)", line)
        if match is not None:
            paths.add(match.group(1))
    return sorted(paths)


def _stdlib_inventory(root: pathlib.Path) -> List[Dict[str, Any]]:
    source_entries = _inventory_regular_files(root, reject_nonregular=False)
    return [
        {
            "path": str(root.joinpath(*pathlib.PurePosixPath(entry["path"]).parts)),
            "mode": int(entry["mode"], 8),
            "bytes": entry["bytes"],
            "sha256": entry["sha256"],
        }
        for entry in source_entries
    ]


def _package_inventory() -> List[str]:
    executable = pathlib.Path("/usr/bin/dpkg-query")
    if not executable.exists():
        return []
    output = _run_identity_command(
        ["/usr/bin/dpkg-query", "-W", "-f=${binary:Package}\\t${Version}\\n"]
    )
    try:
        rows = output.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ProbeError("package inventory is not ASCII") from error
    if any(not row or row.count("\t") != 1 for row in rows):
        raise ProbeError("package inventory row is malformed")
    if rows != sorted(set(rows)):
        raise ProbeError("package inventory is not canonical")
    return rows


def _runtime_provenance(mode: str) -> Dict[str, Any]:
    if mode == "native-reference":
        executable = "/usr/bin/python3"
    elif mode == "normal":
        executable = "/usr/local/bin/python3"
    else:
        raise ProbeError("runtime provenance mode differs")
    executable_identity = _file_identity(executable)
    reached_runtime = os.path.abspath(sys.executable)
    if not os.path.isabs(reached_runtime):
        raise ProbeError("reached runtime path is not absolute")
    darwin = sys.platform == "darwin"
    if pathlib.Path("/usr/bin/ldd").is_file():
        ldd_argv = ["/usr/bin/ldd", reached_runtime]
    elif darwin and pathlib.Path("/usr/bin/otool").is_file():
        ldd_argv = ["/usr/bin/otool", "-L", reached_runtime]
    else:
        ldd_argv = []
    ldd_stdout = _run_identity_command(ldd_argv) if ldd_argv else b""
    dependency_paths = _dependency_paths(ldd_stdout, darwin)
    # macOS reports shared-cache install names that intentionally have no
    # filesystem object.  The raw otool bytes retain those names; only actual
    # regular-file dependencies can have descriptor-stable byte identities.
    dependencies: List[Dict[str, Any]] = []
    for path in dependency_paths:
        dependencies.append(
            {
                "reported_path": path,
                "identity": _file_identity(path) if os.path.lexists(path) else None,
            }
        )
    stdlib_value = sysconfig.get_path("stdlib")
    if not isinstance(stdlib_value, str) or not os.path.isabs(stdlib_value):
        raise ProbeError("stdlib root is unavailable")
    stdlib_root = pathlib.Path(stdlib_value)
    stdlib_entries = _stdlib_inventory(stdlib_root)
    packages = _package_inventory()
    os_release = (
        _read_all(pathlib.Path("/etc/os-release"), 65_536)
        if pathlib.Path("/etc/os-release").is_file()
        else b""
    )
    libc_name, libc_version = platform.libc_ver()
    libc = " ".join(value for value in (libc_name, libc_version) if value) or "unknown"
    sysconfig_paths = sysconfig.get_paths()
    if not isinstance(sysconfig_paths, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in sysconfig_paths.items()
    ):
        raise ProbeError("sysconfig paths differ")
    linker_version_argv = ["/usr/bin/ldd", "--version"] if not darwin else []
    linker_version_stdout = (
        _run_identity_command(linker_version_argv) if linker_version_argv else b""
    )
    return {
        "python_version": platform.python_version(),
        "sys_version": sys.version,
        "sysconfig_paths": {
            key: sysconfig_paths[key] for key in sorted(sysconfig_paths)
        },
        "implementation": sys.implementation.name,
        "executable": executable,
        "executable_chain": executable_identity["chain"],
        "interpreter_sha256": executable_identity["sha256"],
        "stdlib_root": str(stdlib_root),
        "stdlib_entries": stdlib_entries,
        "stdlib_sha256": _domain_sha256(STDLIB_DOMAIN, stdlib_entries),
        "ldd_argv": ldd_argv,
        "ldd_stdout_base64": _base64(ldd_stdout),
        "linker_version_argv": linker_version_argv,
        "linker_version_stdout_base64": _base64(linker_version_stdout),
        "dependencies": dependencies,
        "dependencies_sha256": _domain_sha256(DEPENDENCIES_DOMAIN, dependencies),
        "zlib_compile": zlib.ZLIB_VERSION,
        "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION,
        "libc": libc,
        "os_release_base64": _base64(os_release),
        "packages": packages,
        "packages_sha256": _domain_sha256(PACKAGES_DOMAIN, packages),
    }


def _proc_bytes(pid: int, relative: str, limit: int = 1_048_576) -> bytes:
    return _read_pseudo_file(pathlib.Path("/proc") / str(pid) / relative, limit)


def _parse_proc_cgroup(data: bytes) -> Dict[str, Any]:
    if not data or not data.endswith(b"\n"):
        raise ProbeError("proc cgroup framing differs")
    rows: List[Tuple[int, Tuple[str, ...], str]] = []
    for raw_line in data.splitlines():
        match = re.fullmatch(
            rb"(0|[1-9][0-9]*):([a-z0-9_=,.-]*):(/[^\x00\r\n]*)", raw_line
        )
        if match is None:
            raise ProbeError("proc cgroup row grammar differs")
        try:
            hierarchy = int(match.group(1))
            controller_text = match.group(2).decode("ascii")
            controllers = tuple(controller_text.split(",")) if controller_text else ()
            path = match.group(3).decode("ascii")
        except UnicodeDecodeError as error:
            raise ProbeError("proc cgroup row is not ASCII") from error
        rows.append((hierarchy, controllers, path))
        pure_path = pathlib.PurePosixPath(path)
        if (
            not pure_path.is_absolute()
            or str(pure_path) != path
            or path.startswith("//")
            or any(part in (".", "..") for part in pure_path.parts)
        ):
            raise ProbeError("proc cgroup path is noncanonical")
    if len(rows) == 1 and rows[0][0] == 0 and rows[0][1] == ():
        return {"version": 2, "path": rows[0][2], "controllers": {}}
    controllers: Dict[str, str] = {}
    for hierarchy, names, path in rows:
        if hierarchy <= 0 or not names or any(not name for name in names):
            raise ProbeError("mixed cgroup membership differs")
        for name in names:
            if name in controllers:
                raise ProbeError("duplicate cgroup controller")
            controllers[name] = path
    if not controllers:
        raise ProbeError("cgroup membership is empty")
    return {
        "version": 1,
        "path": None,
        "controllers": {key: controllers[key] for key in sorted(controllers)},
    }


def _cgroup_path_for(pid: int) -> str:
    data = _proc_bytes(pid, "cgroup", 65_536)
    membership = _parse_proc_cgroup(data)
    if membership["version"] != 2 or not isinstance(membership["path"], str):
        raise ProbeError("unified cgroup path is unavailable")
    return membership["path"]


def _validate_status(data: bytes) -> None:
    if not data or not data.endswith(b"\n") or b"\r" in data or b"\0" in data:
        raise ProbeError("status framing differs")
    rows: Dict[bytes, bytes] = {}
    for line in data.splitlines():
        if b":" not in line:
            raise ProbeError("status row grammar differs")
        key = line.split(b":", 1)[0]
        if re.fullmatch(rb"[A-Za-z][A-Za-z0-9_]*", key) is None or key in rows:
            raise ProbeError("status key differs")
        rows[key] = line
    for key in (b"Uid", b"Gid"):
        if rows.get(key) != key + b":\t65532\t65532\t65532\t65532":
            raise ProbeError("status identity row differs")
    for key in (b"CapInh", b"CapPrm", b"CapEff", b"CapBnd", b"CapAmb"):
        if rows.get(key) != key + b":\t0000000000000000":
            raise ProbeError("status capability row differs")
    if rows.get(b"NoNewPrivs") != b"NoNewPrivs:\t1":
        raise ProbeError("status no-new-privileges row differs")
    if rows.get(b"Seccomp") != b"Seccomp:\t2":
        raise ProbeError("status seccomp row differs")
    filters = rows.get(b"Seccomp_filters")
    if (
        filters is None
        or re.fullmatch(rb"Seccomp_filters:\t[1-9][0-9]*", filters) is None
    ):
        raise ProbeError("status seccomp-filter row differs")


def _namespace_identities(pid: int) -> Dict[str, str]:
    namespaces: Dict[str, str] = {}
    for kind in NAMESPACE_KINDS:
        path = pathlib.Path("/proc") / str(pid) / "ns" / kind
        try:
            value = _readlink_stable(path, "namespace identity").decode("ascii")
        except UnicodeDecodeError as error:
            raise ProbeError("namespace identity is not ASCII") from error
        if re.fullmatch(kind + r":\[[0-9]+\]", value) is None:
            raise ProbeError("namespace identity grammar differs")
        namespaces[kind] = value
    return namespaces


def _parse_proc_integer(data: bytes, label: str, minimum: int, maximum: int) -> int:
    if re.fullmatch(rb"(?:0|-?[1-9][0-9]*)\n", data) is None:
        raise ProbeError(label + " grammar differs")
    value = int(data)
    if value < minimum or value > maximum:
        raise ProbeError(label + " range differs")
    return value


def _security(pid: int) -> Dict[str, Any]:
    if pid != os.getpid():
        raise ProbeError("security census is not the collector")
    namespaces = _namespace_identities(pid)
    cgroup = _proc_bytes(pid, "cgroup", 65_536)
    membership = _parse_proc_cgroup(cgroup)
    if membership["version"] != 2 or not isinstance(membership["path"], str):
        raise ProbeError("security census requires unified cgroup")
    status = _proc_bytes(pid, "status", 65_536)
    _validate_status(status)
    oom_score_adj = _proc_bytes(pid, "oom_score_adj", 128)
    oom_score = _parse_proc_integer(oom_score_adj, "collector OOM score", -1000, 1000)
    proc_map = b"         0          0 4294967295\n"
    uid_map = _proc_bytes(pid, "uid_map", 4096)
    gid_map = _proc_bytes(pid, "gid_map", 4096)
    if uid_map != proc_map or gid_map != proc_map:
        raise ProbeError("container identity map differs")
    attr_current = _proc_bytes(pid, "attr/current", 4096)
    if attr_current not in (b"docker-default (enforce)\n", b"unconfined\n"):
        raise ProbeError("container LSM identity differs")
    if os.getuid() != 65532 or os.getgid() != 65532:
        raise ProbeError("container uid/gid differs")
    if oom_score != 0:
        raise ProbeError("collector OOM score differs")
    return {
        "pid": pid,
        "uid": os.getuid(),
        "gid": os.getgid(),
        "uid_map_base64": _base64(uid_map),
        "gid_map_base64": _base64(gid_map),
        "status_base64": _base64(status),
        "attr_current_base64": _base64(attr_current),
        "cgroup_base64": _base64(cgroup),
        "oom_score_adj_base64": _base64(oom_score_adj),
        "namespaces": namespaces,
        "oom_score_adj": oom_score,
    }


def _normalize_cgroup_file(name: str, data: bytes) -> Any:
    if name == "cgroup.procs":
        return _decimal_lines(data)
    if name == "cpu.max":
        match = re.fullmatch(rb"(max|[1-9][0-9]*) ([1-9][0-9]*)\n", data)
        if match is None:
            raise ProbeError("cpu.max grammar differs")
        quota: Any = "max" if match.group(1) == b"max" else int(match.group(1))
        return [quota, int(match.group(2))]
    if name in (
        "cgroup.events",
        "memory.swap.events",
        "memory.events",
        "memory.events.local",
        "pids.events",
        "cpu.stat",
    ):
        parsed = _key_value_lines(data)
        if name == "cgroup.events" and (
            set(parsed) != {"populated", "frozen"}
            or any(value not in (0, 1) for value in parsed.values())
        ):
            raise ProbeError("cgroup.events state differs")
        return parsed
    allow_max = name in ("memory.max", "memory.high", "memory.swap.max", "pids.max")
    grammar = rb"(max|0|[1-9][0-9]*)\n" if allow_max else rb"(0|[1-9][0-9]*)\n"
    match = re.fullmatch(grammar, data)
    if match is None:
        raise ProbeError("cgroup scalar grammar differs: " + name)
    return "max" if match.group(1) == b"max" else int(match.group(1))


def _cgroup_snapshot(phase: str) -> Dict[str, Any]:
    if phase not in ("pre", "terminal"):
        raise ProbeError("cgroup snapshot phase differs")
    cgroup_path = _cgroup_path_for(os.getpid())
    relative = pathlib.PurePosixPath(cgroup_path.lstrip("/"))
    if ".." in relative.parts:
        raise ProbeError("cgroup path traverses")
    root = pathlib.Path("/sys/fs/cgroup").joinpath(*relative.parts)
    files: Dict[str, Any] = {}
    raw_files: Dict[str, str] = {}
    for name in CGROUP_FILES:
        data = _read_pseudo_file(root / name, 1_048_576)
        raw_files[name] = _base64(data)
        files[name] = _normalize_cgroup_file(name, data)
    if _cgroup_path_for(os.getpid()) != cgroup_path:
        raise ProbeError("cgroup membership drifted during snapshot")
    if (
        files["memory.max"] != 536_870_912
        or files["memory.swap.max"] != 0
        or files["memory.min"] != 0
        or files["memory.low"] != 0
        or files["memory.high"] != "max"
        or files["memory.oom.group"] != 0
        or files["pids.max"] != 16
        or files["cpu.max"] != [100_000, 100_000]
        or files["memory.peak"] < files["memory.current"]
    ):
        raise ProbeError("cgroup resource contract differs")
    return {
        "phase": phase,
        "path": cgroup_path,
        "observed_monotonic_ns": _monotonic_ns(),
        "raw_files_base64": raw_files,
        "files": files,
    }


def _mount_options(raw: bytes, label: str) -> List[str]:
    if not raw:
        raise ProbeError(label + " is empty")
    parts = raw.split(b",")
    if any(re.fullmatch(rb"[!-+\--~]+", part) is None for part in parts):
        raise ProbeError(label + " grammar differs")
    try:
        decoded = [part.decode("ascii") for part in parts]
    except UnicodeDecodeError as error:
        raise ProbeError(label + " is not ASCII") from error
    if len(decoded) != len(set(decoded)):
        raise ProbeError(label + " contains a duplicate")
    return decoded


def _mount_setting(
    options: Sequence[str], name: str, required: bool = True
) -> Optional[str]:
    values = [item.split("=", 1)[1] for item in options if item.startswith(name + "=")]
    if len(values) > 1 or (required and len(values) != 1):
        raise ProbeError("mount setting differs: " + name)
    return values[0] if values else None


def _tmpfs_size(value: str) -> int:
    match = re.fullmatch(r"(0|[1-9][0-9]*)([kKmMgG]?)", value)
    if match is None:
        raise ProbeError("tmpfs size grammar differs")
    multiplier = {"": 1, "k": 1024, "m": 1024**2, "g": 1024**3}[
        match.group(2).lower()
    ]
    return int(match.group(1)) * multiplier


def _parse_mountinfo(data: bytes) -> Dict[str, Dict[str, Any]]:
    if not data or not data.endswith(b"\n") or b"\r" in data or b"\0" in data:
        raise ProbeError("mountinfo framing differs")
    matches: Dict[str, Dict[str, Any]] = {}
    mount_ids: Set[int] = set()
    for line in data[:-1].split(b"\n"):
        if line.count(b" - ") != 1:
            raise ProbeError("mountinfo separator differs")
        left, right = line.split(b" - ", 1)
        left_fields = left.split(b" ")
        right_fields = right.split(b" ")
        if len(left_fields) < 6 or len(right_fields) != 3 or any(
            not field for field in left_fields + right_fields
        ):
            raise ProbeError("mountinfo row field count differs")
        root_and_target = left_fields[3:5]
        if (
            re.fullmatch(rb"[1-9][0-9]*", left_fields[0]) is None
            or re.fullmatch(rb"[1-9][0-9]*", left_fields[1]) is None
            or re.fullmatch(rb"(?:0|[1-9][0-9]*):(?:0|[1-9][0-9]*)", left_fields[2])
            is None
            or any(re.fullmatch(rb"/[!-~]*", field) is None for field in root_and_target)
            or any(
                b"\\" in re.sub(rb"\\(?:011|012|040|134)", b"", field)
                for field in root_and_target
            )
            or any(
                re.fullmatch(rb"[!-~]+", field) is None
                for field in left_fields[6:] + right_fields
            )
        ):
            raise ProbeError("mountinfo identity grammar differs")
        mount_id = int(left_fields[0])
        if mount_id in mount_ids:
            raise ProbeError("mountinfo mount id is duplicated")
        mount_ids.add(mount_id)
        mountpoint = left_fields[4]
        key = (
            "work"
            if mountpoint == b"/work"
            else "shm"
            if mountpoint == b"/dev/shm"
            else None
        )
        if key is None:
            continue
        if key in matches:
            raise ProbeError("required tmpfs mount is duplicated")
        try:
            target = mountpoint.decode("ascii")
            fs_type = right_fields[0].decode("ascii")
        except UnicodeDecodeError as error:
            raise ProbeError("required mount row is not ASCII") from error
        mount_options = _mount_options(left_fields[5], "mount options")
        super_options = _mount_options(right_fields[2], "super options")
        matches[key] = {
            "mount_id": mount_id,
            "root": left_fields[3],
            "target": target,
            "fs_type": fs_type,
            "mount_options": mount_options,
            "super_options": super_options,
        }
    return matches


def _mounts() -> Dict[str, Any]:
    data = _read_pseudo_file(pathlib.Path("/proc/self/mountinfo"), 4_194_304)
    parsed = _parse_mountinfo(data)
    if set(parsed) != {"work", "shm"}:
        raise ProbeError("required tmpfs mount is absent")
    matches: Dict[str, Dict[str, Any]] = {}
    required_options = {"rw", "nosuid", "nodev", "noexec"}
    for key in ("work", "shm"):
        row = parsed[key]
        options = row["mount_options"] + row["super_options"]
        if row["fs_type"] != "tmpfs" or row["root"] != b"/":
            raise ProbeError("required mount is not a tmpfs root")
        if not required_options.issubset(set(options)):
            raise ProbeError("required tmpfs flags differ")
        raw_size = _tmpfs_size(_mount_setting(options, "size") or "")
        raw_mode_text = _mount_setting(options, "mode", required=key == "work")
        if raw_mode_text is not None and re.fullmatch(
            r"0?[0-7]{3,4}", raw_mode_text
        ) is None:
            raise ProbeError("tmpfs mode grammar differs")
        raw_mode = int(raw_mode_text, 8) if raw_mode_text is not None else None
        target = row["target"]
        flags = (
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            before = pathlib.Path(target).lstat()
            descriptor = os.open(target, flags)
            target_status = os.fstat(descriptor)
            filesystem = os.fstatvfs(descriptor)
            final = os.fstat(descriptor)
        except OSError as error:
            raise ProbeError("required tmpfs descriptor identity failed") from error
        finally:
            if "descriptor" in locals():
                os.close(descriptor)
                del descriptor
        if (
            not stat.S_ISDIR(target_status.st_mode)
            or _stat_identity(before) != _stat_identity(target_status)
            or _stat_identity(target_status) != _stat_identity(final)
        ):
            raise ProbeError("required tmpfs target identity drifted")
        size_bytes = filesystem.f_frsize * filesystem.f_blocks
        mode = stat.S_IMODE(target_status.st_mode)
        if raw_size != size_bytes or (raw_mode is not None and raw_mode != mode):
            raise ProbeError("tmpfs raw row and descriptor disagree")
        for owner_name, owner_value in (
            ("uid", target_status.st_uid),
            ("gid", target_status.st_gid),
        ):
            raw_owner = _mount_setting(options, owner_name, required=key == "work")
            if raw_owner is not None and (
                re.fullmatch(r"0|[1-9][0-9]*", raw_owner) is None
                or int(raw_owner) != owner_value
            ):
                raise ProbeError("tmpfs owner setting differs")
        matches[key] = {
            "target": target,
            "fs_type": row["fs_type"],
            "options": sorted(set(options)),
            "size_bytes": size_bytes,
            "mode": mode,
            "uid": target_status.st_uid,
            "gid": target_status.st_gid,
        }
    if set(matches) != {"work", "shm"}:
        raise ProbeError("required tmpfs mount is absent")
    work = matches["work"]
    shm = matches["shm"]
    if (
        work["size_bytes"] != 16 * 1024 * 1024
        or work["mode"] != 0o700
        or work["uid"] != 65532
        or work["gid"] != 65532
        or not required_options.issubset(work["options"])
    ):
        raise ProbeError("work tmpfs contract differs")
    if (
        shm["size_bytes"] != 1024 * 1024
        or shm["mode"] != 0o1777
        or not required_options.issubset(shm["options"])
    ):
        raise ProbeError("shared-memory tmpfs contract differs")
    return {
        "mountinfo_base64": _base64(data),
        "mountinfo_sha256": _sha256(data),
        "work": matches["work"],
        "shm": matches["shm"],
    }


def _parse_proc_limits(data: bytes) -> Dict[str, List[int]]:
    if not data or not data.endswith(b"\n") or b"\r" in data or b"\0" in data:
        raise ProbeError("proc limits framing differs")
    lines = data.splitlines()
    header = (
        b"Limit                     Soft Limit           Hard Limit           Units     "
    )
    if not lines or lines[0] != header:
        raise ProbeError("proc limits header differs")
    soft_offset = 26
    hard_offset = 47
    units_offset = 68
    wanted = {
        b"Max cpu time": ("cpu", b"seconds"),
        b"Max file size": ("fsize", b"bytes"),
        b"Max open files": ("nofile", b"files"),
        b"Max core file size": ("core", b"bytes"),
    }
    parsed: Dict[str, List[int]] = {}
    seen_labels: Set[bytes] = set()
    for line in lines[1:]:
        if len(line) != len(header) or any(byte < 0x20 or byte > 0x7E for byte in line):
            raise ProbeError("proc limits row differs")
        fields = (
            line[:soft_offset],
            line[soft_offset:hard_offset],
            line[hard_offset:units_offset],
            line[units_offset:],
        )
        if any(
            field != field.rstrip() + b" " * (len(field) - len(field.rstrip()))
            for field in fields
        ):
            raise ProbeError("proc limits field padding differs")
        label = fields[0].rstrip()
        if not label or label in seen_labels:
            raise ProbeError("proc limits label differs")
        seen_labels.add(label)
        soft_raw = fields[1].rstrip()
        hard_raw = fields[2].rstrip()
        units_raw = fields[3].rstrip()
        if (
            re.fullmatch(rb"(?:unlimited|0|[1-9][0-9]*)", soft_raw) is None
            or re.fullmatch(rb"(?:unlimited|0|[1-9][0-9]*)", hard_raw) is None
            or re.fullmatch(rb"[A-Za-z ]*", units_raw) is None
        ):
            raise ProbeError("proc limits value grammar differs")
        if label not in wanted:
            continue
        if (
            re.fullmatch(rb"(?:0|[1-9][0-9]*)", soft_raw) is None
            or re.fullmatch(rb"(?:0|[1-9][0-9]*)", hard_raw) is None
        ):
            raise ProbeError("required proc limit is not finite")
        key, expected_units = wanted[label]
        if units_raw != expected_units:
            raise ProbeError("required proc limit units differ")
        if key in parsed:
            raise ProbeError("required proc limit is duplicated")
        parsed[key] = [int(soft_raw), int(hard_raw)]
    if set(parsed) != {value[0] for value in wanted.values()}:
        raise ProbeError("required proc limits are absent")
    return parsed


def _rlimits() -> Dict[str, Any]:
    def pair(kind: int) -> List[int]:
        soft, hard = resource.getrlimit(kind)
        return [soft, hard]

    proc_limits = _proc_bytes(os.getpid(), "limits", 65_536)
    normalized = {
        "cpu": pair(resource.RLIMIT_CPU),
        "fsize": pair(resource.RLIMIT_FSIZE),
        "nofile": pair(resource.RLIMIT_NOFILE),
        "core": pair(resource.RLIMIT_CORE),
    }
    expected = {
        "cpu": [900, 900],
        "fsize": [67_108_864, 67_108_864],
        "nofile": [32, 32],
        "core": [0, 0],
    }
    if normalized != expected:
        raise ProbeError("container resource limits differ")
    if _parse_proc_limits(proc_limits) != normalized:
        raise ProbeError("proc and resource limits disagree")
    result: Dict[str, Any] = dict(normalized)
    result["proc_limits_base64"] = _base64(proc_limits)
    return result


def _snapshot_file(snapshot: Mapping[str, Any], name: str) -> bytes:
    files = snapshot.get("raw_files_base64")
    if not isinstance(files, dict) or set(files) != set(CGROUP_FILES):
        raise ProbeError("cgroup snapshot field set differs")
    value = files.get(name)
    if not isinstance(value, str):
        raise ProbeError("cgroup snapshot value differs")
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, binascii.Error) as error:
        raise ProbeError("cgroup snapshot base64 differs") from error


def _decimal_lines(data: bytes) -> List[int]:
    if not data or re.fullmatch(rb"(?:[1-9][0-9]*\n)+", data) is None:
        raise ProbeError("decimal line grammar differs")
    values = [int(line) for line in data.splitlines()]
    if len(values) != len(set(values)):
        raise ProbeError("decimal line value is duplicated")
    return values


def _key_value_lines(data: bytes) -> Dict[str, int]:
    result: Dict[str, int] = {}
    if not data.endswith(b"\n"):
        raise ProbeError("key/value framing differs")
    for line in data.splitlines():
        match = re.fullmatch(rb"([a-z_]+) (0|[1-9][0-9]*)", line)
        if match is None:
            raise ProbeError("key/value grammar differs")
        key = match.group(1).decode("ascii")
        if key in result:
            raise ProbeError("duplicate key/value row")
        result[key] = int(match.group(2))
    return result


def _event_deltas(
    pre: Mapping[str, Any], terminal: Mapping[str, Any], name: str
) -> Dict[str, int]:
    before = _key_value_lines(_snapshot_file(pre, name))
    after = _key_value_lines(_snapshot_file(terminal, name))
    if set(before) != set(after):
        raise ProbeError("memory event keys drifted")
    deltas: Dict[str, int] = {}
    for key in sorted(before):
        if after[key] < before[key]:
            raise ProbeError("memory event counter decreased")
        deltas[key] = after[key] - before[key]
    return deltas


def _validate_cgroup_transition(
    pre: Mapping[str, Any], terminal: Mapping[str, Any]
) -> None:
    if pre.get("phase") != "pre" or terminal.get("phase") != "terminal":
        raise ProbeError("cgroup snapshot phase differs")
    if pre.get("path") != terminal.get("path"):
        raise ProbeError("cgroup path drifted between snapshots")
    if (
        type(pre.get("observed_monotonic_ns")) is not int
        or type(terminal.get("observed_monotonic_ns")) is not int
        or pre["observed_monotonic_ns"] >= terminal["observed_monotonic_ns"]
    ):
        raise ProbeError("cgroup snapshot ordering differs")
    for name in (
        "memory.events",
        "memory.events.local",
        "memory.swap.events",
        "pids.events",
        "cpu.stat",
    ):
        _event_deltas(pre, terminal, name)
    pre_state = _key_value_lines(_snapshot_file(pre, "cgroup.events"))
    terminal_state = _key_value_lines(_snapshot_file(terminal, "cgroup.events"))
    if (
        pre_state != {"populated": 1, "frozen": 0}
        or terminal_state != {"populated": 1, "frozen": 0}
    ):
        raise ProbeError("cgroup lifecycle state differs")


def _process_record(
    pid: int,
    ready: bool,
    wait_signal: Optional[int],
    survived: bool,
) -> Dict[str, Any]:
    if not (survived or ready):
        raise ProbeError("process record requires retained pre-release inputs")
    cgroup = _proc_bytes(pid, "cgroup", 65_536)
    membership = _parse_proc_cgroup(cgroup)
    if membership["version"] != 2 or not isinstance(membership["path"], str):
        raise ProbeError("process record requires unified cgroup")
    oom_score_adj = _proc_bytes(pid, "oom_score_adj", 128)
    oom_score = _parse_proc_integer(
        oom_score_adj, "process OOM score", -1000, 1000
    )
    return {
        "pid": pid,
        "cgroup_path": membership["path"],
        "cgroup_base64": _base64(cgroup),
        "oom_score_adj": oom_score,
        "oom_score_adj_base64": _base64(oom_score_adj),
        "namespaces": _namespace_identities(pid),
        "ready": ready,
        "wait_signal": wait_signal,
        "survived": survived,
    }


def _read_exact_fd(fd: int, expected: bytes) -> None:
    data = bytearray()
    while len(data) < len(expected):
        chunk = os.read(fd, len(expected) - len(data))
        if not chunk:
            break
        data.extend(chunk)
    if bytes(data) != expected:
        raise ProbeError("OOM barrier token differs")


def _read_json_fd(fd: int, limit: int = 65_536) -> Dict[str, Any]:
    data = bytearray()
    while len(data) <= limit:
        chunk = os.read(fd, min(4096, limit + 1 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if data.endswith(b"\n"):
            break
    if len(data) > limit:
        raise ProbeError("OOM metadata exceeds limit")
    return _strict_json_line(bytes(data))


def _wait_signal_from_status(wait_status: int) -> int:
    if type(wait_status) is not int or wait_status < 0:
        raise ProbeError("OOM raw wait status differs")
    if not os.WIFSIGNALED(wait_status):
        raise ProbeError("OOM child did not terminate by signal")
    wait_signal = os.WTERMSIG(wait_status)
    if wait_signal != signal.SIGKILL:
        raise ProbeError("OOM child signal differs")
    if hasattr(os, "WCOREDUMP") and os.WCOREDUMP(wait_status):
        raise ProbeError("OOM child unexpectedly dumped core")
    return wait_signal


def _oom_allocation_child(
    ready_fd: int, release_fd: int, metadata_fd: int, allocation_fd: int
) -> None:
    try:
        cgroup = _proc_bytes(os.getpid(), "cgroup", 65_536)
        _parse_proc_cgroup(cgroup)
        child_cgroup_read = _monotonic_ns()
        score_fd = os.open(
            "/proc/self/oom_score_adj",
            os.O_WRONLY | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            _write_all(score_fd, b"1000\n")
        finally:
            os.close(score_fd)
        score_write = _monotonic_ns()
        score_readback = _proc_bytes(os.getpid(), "oom_score_adj", 128)
        score_readback_time = _monotonic_ns()
        if score_readback != b"1000\n":
            os._exit(71)
        child_ready = _monotonic_ns()
        metadata = {
            "child_cgroup_base64": _base64(cgroup),
            "oom_score_adj_base64": _base64(score_readback),
            "child_cgroup_read_monotonic_ns": child_cgroup_read,
            "score_write_monotonic_ns": score_write,
            "score_readback_monotonic_ns": score_readback_time,
            "child_ready_monotonic_ns": child_ready,
        }
        _write_all(ready_fd, OOM_READY_TOKEN)
        _write_all(metadata_fd, canonical_json_bytes(metadata) + b"\n")
        _read_exact_fd(release_fd, OOM_RELEASE_TOKEN)
        allocation_started = _monotonic_ns()
        _write_all(allocation_fd, struct.pack(">Q", allocation_started))
        allocation = bytearray(ALLOCATION_BYTES)
        for offset in range(0, ALLOCATION_BYTES, 4096):
            allocation[offset] = 1
        if allocation[-1] != 0:
            os._exit(72)
        while True:
            signal.pause()
    except BaseException:
        os._exit(73)


def _oom_result(root: pathlib.Path, input_manifest_sha256: str) -> Dict[str, Any]:
    if not sys.platform.startswith("linux"):
        raise ProbeError("oom-child requires Linux")
    manifest_sha256 = _validate_input_manifest_sha256(input_manifest_sha256)
    _validate_mounted_input_tree(root)
    _corpus_validation(root)
    parent_pid = os.getpid()
    ready_read, ready_write = os.pipe()
    release_read, release_write = os.pipe()
    metadata_read, metadata_write = os.pipe()
    allocation_read, allocation_write = os.pipe()
    child_pid = os.fork()
    if child_pid == 0:
        os.close(ready_read)
        os.close(release_write)
        os.close(metadata_read)
        os.close(allocation_read)
        _oom_allocation_child(
            ready_write, release_read, metadata_write, allocation_write
        )
        os._exit(74)

    os.close(ready_write)
    os.close(release_read)
    os.close(metadata_write)
    os.close(allocation_write)
    child_reaped = False
    try:
        child_metadata = _read_json_fd(metadata_read)
        if set(child_metadata) != {
            "child_cgroup_base64",
            "oom_score_adj_base64",
            "child_cgroup_read_monotonic_ns",
            "score_write_monotonic_ns",
            "score_readback_monotonic_ns",
            "child_ready_monotonic_ns",
        }:
            raise ProbeError("OOM child metadata field set differs")
        _read_exact_fd(ready_read, OOM_READY_TOKEN)
        child_record_pre = _process_record(child_pid, True, None, True)
        parent_record = _process_record(parent_pid, True, None, True)
        if child_record_pre["cgroup_base64"] != child_metadata.get(
            "child_cgroup_base64"
        ) or child_record_pre["oom_score_adj_base64"] != child_metadata.get(
            "oom_score_adj_base64"
        ):
            raise ProbeError("OOM child retained proc bytes disagree")
        if child_record_pre["oom_score_adj"] != 1000:
            raise ProbeError("OOM child score adjustment differs")
        if child_record_pre["cgroup_path"] != parent_record["cgroup_path"]:
            raise ProbeError("OOM processes do not share one cgroup")
        if child_record_pre["namespaces"] != parent_record["namespaces"]:
            raise ProbeError("OOM process namespace identities differ")
        pre = _cgroup_snapshot("pre")
        if pre["path"] != parent_record["cgroup_path"]:
            raise ProbeError("OOM process and cgroup snapshot paths disagree")
        pre_processes = sorted(_decimal_lines(_snapshot_file(pre, "cgroup.procs")))
        if pre_processes != sorted([parent_pid, child_pid]):
            raise ProbeError("pre-release cgroup process set differs")
        if _snapshot_file(pre, "memory.oom.group") != b"0\n":
            raise ProbeError("memory.oom.group differs")
        release_monotonic_ns = _monotonic_ns()
        _write_all(release_write, OOM_RELEASE_TOKEN)
        allocation_bytes = bytearray()
        while len(allocation_bytes) < 8:
            chunk = os.read(allocation_read, 8 - len(allocation_bytes))
            if not chunk:
                break
            allocation_bytes.extend(chunk)
        if len(allocation_bytes) != 8:
            raise ProbeError("OOM allocation timing is absent")
        allocation_started_monotonic_ns = struct.unpack(">Q", allocation_bytes)[0]
        waited_pid, wait_status = os.waitpid(child_pid, 0)
        child_wait_monotonic_ns = _monotonic_ns()
        child_reaped = True
        if waited_pid != child_pid:
            raise ProbeError("OOM wait returned a different child")
        wait_signal = _wait_signal_from_status(wait_status)
        terminal = _cgroup_snapshot("terminal")
        _validate_cgroup_transition(pre, terminal)
        terminal_processes = sorted(
            _decimal_lines(_snapshot_file(terminal, "cgroup.procs"))
        )
        if terminal_processes != [parent_pid]:
            raise ProbeError("terminal cgroup process set differs")
        all_deltas = _event_deltas(pre, terminal, "memory.events.local")
        global_deltas = _event_deltas(pre, terminal, "memory.events")
        required_oom_keys = {"oom", "oom_kill", "oom_group_kill"}
        if not required_oom_keys.issubset(all_deltas) or not required_oom_keys.issubset(
            global_deltas
        ):
            raise ProbeError("OOM event key census differs")
        deltas = {
            key: all_deltas.get(key, 0) for key in ("oom", "oom_kill", "oom_group_kill")
        }
        if (
            deltas.get("oom", 0) < 1
            or deltas.get("oom_kill") != 1
            or deltas.get("oom_group_kill") != 0
        ):
            raise ProbeError("OOM local event deltas differ")
        if (
            global_deltas.get("oom", 0) < 1
            or global_deltas.get("oom_kill", 0) != 1
            or global_deltas.get("oom_group_kill", 0) != 0
        ):
            raise ProbeError("OOM global event deltas differ")
        timing_names = (
            "child_cgroup_read_monotonic_ns",
            "score_write_monotonic_ns",
            "score_readback_monotonic_ns",
            "child_ready_monotonic_ns",
        )
        if not all(type(child_metadata.get(name)) is int for name in timing_names):
            raise ProbeError("OOM child timing metadata differs")
        timing = [child_metadata[name] for name in timing_names]
        if not (
            timing[0]
            < timing[1]
            < timing[2]
            <= timing[3]
            < release_monotonic_ns
            < allocation_started_monotonic_ns
            < child_wait_monotonic_ns
        ):
            raise ProbeError("OOM event ordering differs")
        child_record = dict(child_record_pre)
        child_record["wait_signal"] = wait_signal
        child_record["survived"] = False
        security = _security(parent_pid)
        if (
            security["cgroup_base64"] != parent_record["cgroup_base64"]
            or security["oom_score_adj_base64"]
            != parent_record["oom_score_adj_base64"]
            or security["namespaces"] != parent_record["namespaces"]
        ):
            raise ProbeError("OOM parent security records disagree")
        result = {
            "schema": PROBE_SCHEMA,
            "mode": "oom-child",
            "probe_sha256": _probe_sha256(),
            "input_manifest_sha256": manifest_sha256,
            "security": security,
            "cgroup_pre": pre,
            "cgroup_terminal": terminal,
            "mounts": _mounts(),
            "rlimits": _rlimits(),
            "parent": parent_record,
            "child": child_record,
            "workload": {
                "barrier_sha256": _sha256(OOM_READY_TOKEN + OOM_RELEASE_TOKEN),
                "barrier_transcript_base64": _base64(
                    OOM_READY_TOKEN + OOM_RELEASE_TOKEN
                ),
                "allocation_bytes": ALLOCATION_BYTES,
                "child_wait_signal": wait_signal,
                "parent_survived": True,
                "local_event_deltas": deltas,
                "terminal_processes": terminal_processes,
                "child_cgroup_read_monotonic_ns": timing[0],
                "score_write_monotonic_ns": timing[1],
                "score_readback_monotonic_ns": timing[2],
                "child_ready_monotonic_ns": timing[3],
                "release_monotonic_ns": release_monotonic_ns,
                "allocation_started_monotonic_ns": allocation_started_monotonic_ns,
                "child_wait_monotonic_ns": child_wait_monotonic_ns,
                "raw_wait_status": wait_status,
            },
        }
        if set(result) != OOM_FIELDS:
            raise AssertionError("OOM result field-set mismatch")
        return result
    finally:
        if not child_reaped:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(child_pid, 0)
            except ChildProcessError:
                pass
        for descriptor in (
            ready_read,
            release_write,
            metadata_read,
            allocation_read,
        ):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _copy_validation_tree(source: pathlib.Path, destination: pathlib.Path) -> None:
    entries = _inventory_regular_files(source)
    if len(entries) != EXPECTED_INPUT_FILES:
        raise ProbeError(
            "validation source must contain exactly %d files" % EXPECTED_INPUT_FILES
        )
    for entry in entries:
        relative = pathlib.PurePosixPath(entry["path"])
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        data = _read_all(source.joinpath(*relative.parts), MAX_RESULT_BYTES * 256)
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(str(target), flags, 0o644)
        except OSError as error:
            raise ProbeError("validation mirror create failed") from error
        try:
            os.fchmod(descriptor, 0o644)
            _write_all(descriptor, data)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _corpus_validation(root: pathlib.Path) -> Dict[str, Any]:
    try:
        import p01b_container_corpus as corpus
    except ImportError as error:
        raise ProbeError("container corpus module unavailable") from error
    temporary_parent = os.path.realpath(tempfile.gettempdir())
    try:
        with tempfile.TemporaryDirectory(
            prefix="p01b-corpus-", dir=temporary_parent
        ) as temporary:
            validation_root = pathlib.Path(temporary)
            os.chmod(str(validation_root), 0o700)
            _copy_validation_tree(root, validation_root)
            summary = corpus.validate_repository(validation_root)
    except ProbeError:
        raise
    except Exception as error:
        raise ProbeError("container corpus validation failed") from error
    result = {
        "focused_test_count": summary.get("focused_test_count"),
        "full_test_count": summary.get("full_test_count"),
        "source_file_count": summary.get("source_file_count"),
        "test_id_digest": summary.get("test_id_digest"),
    }
    if (
        result["focused_test_count"] != 68
        or result["full_test_count"] != EXPECTED_TESTS
    ):
        raise ProbeError("container corpus counts differ")
    return result


def _run_normal_workload(root: pathlib.Path) -> Dict[str, Any]:
    corpus_path = root / "tools/hsai-formal-preflight/p01b_container_test_corpus.json"
    corpus_bytes = _read_all(corpus_path, 2_000_000)
    try:
        corpus = json.loads(corpus_bytes.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProbeError("container corpus JSON failed") from error
    argv = corpus.get("full", {}).get("argv")
    environment = corpus.get("container_environment")
    if not isinstance(argv, list) or not all(isinstance(item, str) for item in argv):
        raise ProbeError("full corpus argv differs")
    if not isinstance(environment, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in environment.items()
    ):
        raise ProbeError("container corpus environment differs")
    try:
        returncode_value, stdout, stderr = _run_bounded_command(
            argv,
            cwd=str(root),
            env=environment,
            timeout_seconds=1_200,
            stdout_cap=WORKLOAD_STDOUT_CAP,
            stderr_cap=WORKLOAD_STDERR_CAP,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ProbeError("normal workload execution failed") from error
    returncode: Optional[int] = (
        returncode_value if returncode_value >= 0 else None
    )
    wait_signal: Optional[int] = (
        -returncode_value if returncode_value < 0 else None
    )
    stderr_match = re.fullmatch(
        rb"\.{" + str(EXPECTED_TESTS).encode("ascii") + rb"}\n"
        rb"-{70}\nRan ([0-9]+) tests in [0-9]+\.[0-9]{3}s\n\nOK\n",
        stderr,
    )
    discovered = int(stderr_match.group(1)) if stderr_match is not None else -1
    if (
        returncode_value != 0
        or stdout != b""
        or len(stderr) > WORKLOAD_STDERR_CAP
        or discovered != EXPECTED_TESTS
    ):
        raise ProbeError("normal workload result differs")
    return {
        "argv": argv,
        "returncode": returncode,
        "signal": wait_signal,
        "stdout_base64": _base64(stdout),
        "stderr_base64": _base64(stderr),
        "discovered_count": discovered,
        "expected_count": EXPECTED_TESTS,
    }


def build_native_reference() -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "schema": PROBE_SCHEMA,
        "mode": "native-reference",
        "probe_sha256": _probe_sha256(),
        "runtime": _runtime_provenance("native-reference"),
    }
    result.update(_archive_projection())
    if set(result) != NATIVE_FIELDS:
        raise AssertionError("native result field-set mismatch")
    return result


def build_normal_result(
    input_manifest_sha256: str, root: Optional[pathlib.Path] = None
) -> Dict[str, Any]:
    source_root = _source_root() if root is None else root
    manifest_sha256 = _validate_input_manifest_sha256(input_manifest_sha256)
    _validate_mounted_input_tree(source_root)
    pre = _cgroup_snapshot("pre")
    corpus_validation = _corpus_validation(source_root)
    workload = _run_normal_workload(source_root)
    runtime = _runtime_provenance("normal")
    projection = _archive_projection()
    security = _security(os.getpid())
    mounts = _mounts()
    rlimits = _rlimits()
    terminal = _cgroup_snapshot("terminal")
    _validate_cgroup_transition(pre, terminal)
    try:
        security_cgroup = base64.b64decode(
            security["cgroup_base64"].encode("ascii"), validate=True
        )
    except (ValueError, binascii.Error) as error:
        raise ProbeError("security cgroup base64 differs") from error
    security_membership = _parse_proc_cgroup(security_cgroup)
    if (
        security_membership["version"] != 2
        or security_membership["path"] != pre["path"]
        or terminal["path"] != pre["path"]
    ):
        raise ProbeError("normal security and cgroup paths disagree")
    expected_processes = [os.getpid()]
    if (
        sorted(_decimal_lines(_snapshot_file(pre, "cgroup.procs")))
        != expected_processes
        or sorted(_decimal_lines(_snapshot_file(terminal, "cgroup.procs")))
        != expected_processes
    ):
        raise ProbeError("normal cgroup process census differs")
    result: Dict[str, Any] = {
        "schema": PROBE_SCHEMA,
        "mode": "normal",
        "probe_sha256": _probe_sha256(),
        "input_manifest_sha256": manifest_sha256,
        "corpus_validation": corpus_validation,
        "workload": workload,
        "security": security,
        "cgroup_pre": pre,
        "cgroup_terminal": terminal,
        "mounts": mounts,
        "rlimits": rlimits,
        "runtime": runtime,
    }
    result.update(projection)
    if set(result) != NORMAL_FIELDS:
        raise AssertionError("normal result field-set mismatch")
    return result


def build_oom_result(
    input_manifest_sha256: str, root: Optional[pathlib.Path] = None
) -> Dict[str, Any]:
    return _oom_result(
        _source_root() if root is None else root, input_manifest_sha256
    )


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise ProbeError("result write made no progress")
        offset += written


def _write_container_result(result: Dict[str, Any], output: str) -> None:
    if output != OUTPUT_PATH:
        raise ProbeError("container output path differs")
    data = canonical_json_bytes(result)
    if len(data) > MAX_RESULT_BYTES:
        raise ProbeError("result exceeds byte cap")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(output, flags, 0o600)
    except OSError as error:
        raise ProbeError("result create failed") from error
    try:
        os.fchmod(fd, 0o600)
        _write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    try:
        os.utime(output, ns=(0, 0), follow_symlinks=False)
    except OSError as error:
        raise ProbeError("result timestamp normalization failed") from error
    read_flags = (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        metadata_fd = os.open(output, read_flags)
        os.fsync(metadata_fd)
    except OSError as error:
        raise ProbeError("result metadata fsync failed") from error
    finally:
        if "metadata_fd" in locals():
            os.close(metadata_fd)
    retained = _read_all(pathlib.Path(output), MAX_RESULT_BYTES)
    try:
        retained_stat = pathlib.Path(output).lstat()
    except OSError as error:
        raise ProbeError("result identity stat failed") from error
    if (
        retained != data
        or not stat.S_ISREG(retained_stat.st_mode)
        or stat.S_IMODE(retained_stat.st_mode) != 0o600
        or retained_stat.st_nlink != 1
        or retained_stat.st_uid != 65532
        or retained_stat.st_gid != 65532
        or retained_stat.st_size != len(data)
        or retained_stat.st_mtime_ns != 0
    ):
        raise ProbeError("result descriptor contract differs")

    released = [False]

    def release_handler(_signum: int, _frame: Any) -> None:
        released[0] = True

    signal.signal(signal.SIGUSR1, release_handler)
    digest = _sha256(data)
    _write_all(
        sys.stdout.fileno(),
        READY_PREFIX
        + str(len(data)).encode("ascii")
        + b" "
        + digest.encode("ascii")
        + b"\n",
    )
    while not released[0]:
        signal.pause()
    observed = _read_all(pathlib.Path(output), MAX_RESULT_BYTES)
    if observed != data or _sha256(observed) != digest:
        raise ProbeError("released result bytes drifted")


def _parse_cli(argv: Sequence[str]) -> Tuple[str, Optional[str], Optional[str]]:
    if len(argv) == 3 and argv[1] == "--mode" and argv[2] == "native-reference":
        return "native-reference", None, None
    if (
        len(argv) == 7
        and argv[1] == "--mode"
        and argv[2] in ("normal", "oom-child")
        and argv[3] == "--input-manifest-sha256"
        and argv[5] == "--output"
        and argv[6] == OUTPUT_PATH
    ):
        return argv[2], _validate_input_manifest_sha256(argv[4]), argv[6]
    raise ProbeError("closed CLI grammar rejected argv")


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = sys.argv if argv is None else argv
    try:
        mode, input_manifest_sha256, output = _parse_cli(arguments)
        if mode == "native-reference":
            data = canonical_json_bytes(build_native_reference())
            if len(data) > MAX_RESULT_BYTES:
                raise ProbeError("native result exceeds byte cap")
            _write_all(sys.stdout.fileno(), data)
            return 0
        if input_manifest_sha256 is None or output is None:
            raise ProbeError("container input binding is missing")
        result = (
            build_normal_result(input_manifest_sha256)
            if mode == "normal"
            else build_oom_result(input_manifest_sha256)
        )
        _write_container_result(result, output)
        return 0
    except BaseException as error:
        message = str(error)
        if not isinstance(error, (ProbeError, OSError, ValueError)):
            message = "unexpected " + type(error).__name__ + ": " + message
        failure = (
            canonical_json_bytes({"error": message, "schema": ERROR_SCHEMA}) + b"\n"
        )
        try:
            _write_all(sys.stderr.fileno(), failure)
        except (ProbeError, OSError):
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
