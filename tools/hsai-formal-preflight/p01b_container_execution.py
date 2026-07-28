#!/usr/bin/env python3
"""Hermetic execution primitives for the retained P01B container campaign.

This module contains the only future host-authority surface for Phase 796-A3L.
It does not contact Docker, a registry, or the network at import time. Runtime
entry points require caller-supplied, evidence-validated A3L7 material.
"""

from __future__ import annotations

import argparse
import ast
import base64
import ctypes
import hashlib
import json
import math
import os
import plistlib
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple


READINESS_PLAN_SCHEMA = "hsai-p01b-container-readiness-plan-v2"
READINESS_RESULT_SCHEMA = "hsai-p01b-container-readiness-result-v2"
CAMPAIGN_PLAN_SCHEMA = "hsai-p01b-container-campaign-plan-v1"
ATTEMPT_PLAN_SCHEMA = "hsai-p01b-container-plan-v2"
OBSERVATION_SCHEMA = "hsai-p01b-container-observation-v2"
READINESS_EVENT_SCHEMA = "hsai-p01b-container-readiness-event-v1"
PUBLICATION_SCHEMA = "hsai-p01b-container-publication-v2"
PREAUTHORIZATION_SCHEMA = "hsai-p01b-container-preauthorization-plan-v2"
AUTHORIZATION_ROOT_SCHEMA = "hsai-p01b-local-authorization-root-v1"
AUTHORIZATION_SCHEMA = "hsai-p01b-container-authorization-v3"
EXPECTED_BINDINGS_SCHEMA = "hsai-p01b-expected-bindings-v1"
SNAPSHOT_PAIR_SCHEMA = "hsai-p01b-snapshot-manifest-pair-v1"
SNAPSHOT_SOURCE_SCHEMA = "hsai-p01b-snapshot-source-manifest-v1"
SNAPSHOT_COPY_SCHEMA = "hsai-p01b-snapshot-copy-manifest-v1"
SNAPSHOT_DESCRIPTOR_SCHEMA = "hsai-p01b-snapshot-descriptor-set-v1"
TRANSCRIPT_BINDING_SCHEMA = "hsai-p01b-transcript-binding-v1"
HOST_PROVENANCE_SCHEMA = "hsai-p01b-host-provenance-v1"

READINESS_PLAN_DOMAIN = "hsai:p01b-container-readiness-plan:v2"
OBSERVATION_DOMAIN = "hsai:p01b-container-observation:v2"
READINESS_EVENT_DOMAIN = "hsai:p01b-container-readiness-event:v1"

DOCKER_BIN_DIR = "/Applications/Docker.app/Contents/Resources/bin"
DOCKER_EXE = DOCKER_BIN_DIR + "/docker"
DOCKER_SHA256 = "73206884cd100a165e20fbab2b1f9e09e0ae8fc959ec9b02fed46152a99c5e79"
BUILDX_EXE = "/Applications/Docker.app/Contents/Resources/cli-plugins/docker-buildx"
BUILDX_SHA256 = "9d594c8c396e02385b8de8d7594ede893a64ceebbaefb37f7fa99fcd991cf94e"
CODE_SIGN_EXE = "/usr/bin/codesign"
CODE_SIGN_SHA256 = "c91d293ec824037dc4fcb204c5aae32545f73a79a4d6b5f0d113cc856465f209"
DOCKER_APP_PATH = "/Applications/Docker.app"
SANDBOX_EXEC_PATH = "/usr/bin/sandbox-exec"
SANDBOX_EXEC_SHA256 = "556b22a255f0c6d5f3811194a2622c165cfcfabbfbe50f95d92190ff81e99470"
NATIVE_PYTHON_SHA256 = (
    "7f30f076d0e9c38f772a76449fca9da8cf97f6a3d43b94c90a00e4f9ce7ad39e"
)
INDEX_REFERENCE = (
    "docker.io/library/python@sha256:"
    "8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438"
)
IMAGE_CONFIG_DIGEST = (
    "sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4"
)
PLATFORM_PLACEHOLDER = "${PLATFORM}"
CID_PLACEHOLDER = "${CID}"

METADATA_CAP = 262_144
REGISTRY_CAP = 262_144
TAR_CAP = 16_777_216
RESULT_CAP = 1_048_576
GATE_JSON_CAP = 4_194_304
STREAM_CAP = 16_384
ATTEMPT_TIMEOUT_NS = 1_800_000_000_000
TERMINATION_GRACE_SECONDS = 1.0
READ_CHUNK_BYTES = 65_536
SNAPSHOT_FILE_LIMIT = 16_777_216
SNAPSHOT_FILE_COUNT = 22
CANDIDATE_PAYLOAD_COUNT = 201
CANDIDATE_FILE_COUNT = 202
CANDIDATE_DIRECTORY_COUNT = 62
PUBLICATION_EVENT_COUNT = 271

READY_RE = re.compile(rb"\AP01B_RESULT_READY ([1-9][0-9]{0,6}) ([0-9a-f]{64})\n\Z")
HEX64_RE = re.compile(r"\A[0-9a-f]{64}\Z")
GIT_RE = re.compile(r"\A[0-9a-f]{40}\Z")
ID_RE = re.compile(r"\A[a-z][a-z0-9-]{0,126}[a-z0-9]\Z")
OCI_REFERENCE_RE = re.compile(
    r"\A(?:[a-z0-9]+(?:(?:[._]|__|[-]+)[a-z0-9]+)*/)*"
    r"[a-z0-9]+(?:(?:[._]|__|[-]+)[a-z0-9]+)*@sha256:[0-9a-f]{64}\Z"
)

ROOTFS_DIFF_IDS = (
    "sha256:3bfd0b5a99a1f25a488230217defd5c2781ad861f692f5df22d9734bbddfc53d",
    "sha256:e3866ac24baf965b1d6445dab2a6697dc8c5e633e961cdeb8664e947af0afcd8",
    "sha256:58c826d6f8b6c49949dcff1a49bcc504e95bdd68a1e7822c397599576ca5842e",
    "sha256:4a0f4c378bc5afc903ba2f580dd5e0a2e45fb6599e4635133e6662c7acad0e7a",
)
DOCKER_CONTEXT_PATH = "/Users/shaanp/.docker/contexts/meta/fe9c6bd7a66301f49ca9b6a70b217107cd1284598bfc254700c989b916da791e/meta.json"
READINESS_PREDECESSOR_COMMIT = "e443797acbbd73b321253f799a84e6794c924794"
READINESS_TEMP_BASENAME = "runtime-tmp"
HOST_HOME_BASENAME = "host-home"
CLOSED_HOST_PATH = "/usr/bin:/bin:" + DOCKER_BIN_DIR
DOCKER_CONTEXT_SHA256 = "c36db611bb2256cd052f36471538d4c8d1ff3dc36a978d325391c3813072cb2c"
READINESS_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_P01B_REGISTRY_AND_DOCKER_AUTHORITY"
RUN_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_P01B_LOCAL_CONTAINER_EXECUTION"
RECOVERY_ACKNOWLEDGEMENT = "I_ACKNOWLEDGE_P01B_EXACT_RECOVERY_ONLY"
DOCKER_DESKTOP_VM_PATH = "/Applications/Docker.app/Contents/Resources/linuxkit/desktop.img"
DOCKER_DESKTOP_VM_SHA256 = "be2274863e3e008de42f38c6d746a6090b31619715a3c02b4134e1889cdbc9d9"
DOCKER_DESKTOP_KERNEL_PATH = "/Applications/Docker.app/Contents/Resources/linuxkit/kernel"
DOCKER_DESKTOP_KERNEL_SHA256 = "420cd7ac96572498e74d8593f9bb3e2ed0dbf06d61dc5214be3e5c5f08763d0b"
DOCKER_DESKTOP_INFO_PLIST = "/Applications/Docker.app/Contents/Info.plist"
PROTECTED_ADMISSION_PATH = (
    "/Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/"
    "crates/hsai-agent-admission/src/lib.rs"
)
PROTECTED_ADMISSION_SHA256 = (
    "41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de"
)

INSPECT_FIELDS = (
    "Id",
    "Name",
    "Path",
    "Args",
    "Platform",
    "AppArmorProfile",
    "Config.Image",
    "Config.User",
    "Config.Entrypoint",
    "Config.Cmd",
    "Config.Env",
    "Config.WorkingDir",
    "Config.Hostname",
    "Config.Healthcheck",
    "Config.OpenStdin",
    "Config.Tty",
    "Config.Labels",
    "HostConfig.Runtime",
    "HostConfig.NetworkMode",
    "HostConfig.IpcMode",
    "HostConfig.PidMode",
    "HostConfig.UTSMode",
    "HostConfig.CgroupnsMode",
    "HostConfig.CgroupParent",
    "HostConfig.UsernsMode",
    "HostConfig.ReadonlyRootfs",
    "HostConfig.Privileged",
    "HostConfig.CapAdd",
    "HostConfig.CapDrop",
    "HostConfig.SecurityOpt",
    "HostConfig.Memory",
    "HostConfig.MemorySwap",
    "HostConfig.MemorySwappiness",
    "HostConfig.OomKillDisable",
    "HostConfig.PidsLimit",
    "HostConfig.CpuPeriod",
    "HostConfig.CpuQuota",
    "HostConfig.Ulimits",
    "HostConfig.Tmpfs",
    "HostConfig.ShmSize",
    "HostConfig.LogConfig",
    "HostConfig.RestartPolicy",
    "HostConfig.AutoRemove",
    "HostConfig.Devices",
    "HostConfig.DeviceRequests",
    "HostConfig.GroupAdd",
    "Mounts",
    "NetworkSettings.Networks",
    "State.Status",
    "State.Running",
    "State.ExitCode",
    "State.OOMKilled",
    "State.Error",
    "State.Pid",
    "State.StartedAt",
    "State.FinishedAt",
)
INSPECT_TEMPLATE = (
    "[" + ",".join("{{json .%s}}" % field for field in INSPECT_FIELDS) + "]"
)

SOURCE_PATHS = (
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
REVIEWED_PATHS = tuple(
    "tools/hsai-formal-preflight/" + name
    for name in (
        "p01b_container_probe.py",
        "p01b_container_evidence.py",
        "p01b_container_execution.py",
        "p01b_container_evidence_tests.py",
        "p01b_container_execution_tests.py",
    )
)

CLAIM_ASSUMPTIONS = (
    "signed-docker-app-honest",
    "docker-daemon-honest",
    "probe-code-honest",
    "host-driver-honest",
    "native-python-runtime-stdlib-honest",
    "host-system-tool-honest",
    "reviewed-gate-test-code-honest",
    "formal-discovery-under-seatbelt-is-stubbed-census-not-full-suite-semantics",
)
CLAIM_NONCLAIMS = (
    "not-level2",
    "not-external-reproduction",
    "not-benchmark-evidence",
    "not-semantic-proof",
    "not-production-readiness",
    "not-sota",
    "not-breakthrough",
    "not-full-security",
    "not-external-audit",
    "not-accepted-evidence-ledger-evidence",
    "not-full-suite-execution-under-seatbelt",
)
CLASS_ORDER = ("C02", "C03", "C04", "C05", "C06", "C07", "C09", "C10")
REVIEW_ROLE_ORDER = ("security-capability", "correspondence-reproducibility")
A3L9_ENVIRONMENT = {
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "PYTHONDONTWRITEBYTECODE": "1",
}
A3L9_TIMEOUT_NS = 60_000_000_000
A3L9_STREAM_CAP = 16_384
A3L9_REVIEWER_IDS = {
    "security-capability": "security-capability-reviewer",
    "correspondence-reproducibility": "correspondence-reproducibility-reviewer",
}


class ExecutionError(Exception):
    """A plan or host action failed closed."""


def canonical_json_bytes(value: object) -> bytes:
    """Encode deterministic ASCII JSON without a trailing newline."""
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise ExecutionError("value is not canonical JSON") from error


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def domain_sha256(domain: str, value: object) -> str:
    return sha256_bytes(domain.encode("ascii") + b"\0" + canonical_json_bytes(value))


def _require_hex64(value: str, field: str) -> None:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        raise ExecutionError("%s must be lowercase sha256" % field)


def _require_identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or ID_RE.fullmatch(value) is None:
        raise ExecutionError("%s is not a closed identifier" % field)


def _require_git(value: str, field: str) -> None:
    if not isinstance(value, str) or GIT_RE.fullmatch(value) is None:
        raise ExecutionError("%s must be a lowercase git object id" % field)


def _require_absolute(path: str, field: str) -> None:
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or os.path.normpath(path) != path
    ):
        raise ExecutionError("%s must be a canonical absolute path" % field)
    if "\0" in path or "\n" in path or "\r" in path:
        raise ExecutionError("%s contains forbidden bytes" % field)


def _validate_argv(argv: Sequence[str]) -> Tuple[str, ...]:
    if not isinstance(argv, (list, tuple)) or not argv:
        raise ExecutionError("argv must be a nonempty array")
    result: List[str] = []
    for item in argv:
        if (
            not isinstance(item, str)
            or not item
            or any(char in item for char in "\0\n\r")
        ):
            raise ExecutionError("argv contains an invalid argument")
        result.append(item)
    _require_absolute(result[0], "argv[0]")
    return tuple(result)


def _validate_environment(environment: Mapping[str, str]) -> Dict[str, str]:
    if not isinstance(environment, Mapping) or not environment:
        raise ExecutionError("replacement environment is required")
    result: Dict[str, str] = {}
    for key, value in environment.items():
        if not isinstance(key, str) or not key or "=" in key or "\0" in key:
            raise ExecutionError("invalid environment key")
        if not isinstance(value, str) or any(char in value for char in "\0\n\r"):
            raise ExecutionError("invalid environment value")
        result[key] = value
    return dict(sorted(result.items()))


def closed_host_environment(config_root: str, temporary_root: str) -> Dict[str, str]:
    _require_absolute(config_root, "config_root")
    _require_absolute(temporary_root, "temporary_root")
    return {
        "DOCKER_CONFIG": config_root,
        "HOME": temporary_root + "/" + HOST_HOME_BASENAME,
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": CLOSED_HOST_PATH,
        "TMPDIR": temporary_root,
        "TZ": "UTC",
    }


def gate_environment(gate_temp_root: str) -> Dict[str, str]:
    """Return the exact replacement environment for the immutable A3L6 gates."""
    _require_absolute(gate_temp_root, "gate_temp_root")
    return {
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        # Marks the A3L6 execution-focused gate so hermetic tests can avoid
        # host-only paths (/private/tmp gate parents, A3L9 absolute traversal)
        # without widening Seatbelt allow rules.
        "P01B_GATE_SANDBOX_ACTIVE": "1",
        "TMPDIR": gate_temp_root,
    }


def render_gate_sandbox_profile(materialized_root: str, gate_temp_root: str) -> bytes:
    """Render the byte-exact Seatbelt profile; no unsandboxed fallback exists."""
    for field, value in (
        ("materialized_root", materialized_root),
        ("gate_temp_root", gate_temp_root),
    ):
        _require_absolute(value, field)
        if re.fullmatch(r"/[A-Za-z0-9._/-]+", value) is None:
            raise ExecutionError(field + " is not safe for the frozen profile")
    lines = (
        "(version 1)",
        "(deny default)",
        "(allow process*)",
        "(allow signal)",
        "(allow sysctl-read)",
        "(allow file-read-metadata)",
        '(allow file-read-data (literal "/"))',
        '(allow file-read* (subpath "%s") (subpath "%s") (subpath "/System/Library") (subpath "/usr/lib") (subpath "/usr/bin") (subpath "/bin") (subpath "/Library/Developer/CommandLineTools") (subpath "/private/etc") (literal "/dev/null") (literal "/dev/urandom"))'
        % (materialized_root, gate_temp_root),
        '(allow file-write* (subpath "%s") (literal "/dev/null"))'
        % gate_temp_root,
        "(deny network*)",
    )
    return ("\n".join(lines) + "\n").encode("ascii")


def run_gate_sandbox_denial_checks(
    *, materialized_root: Path, gate_temp_root: Path, profile_path: Path
) -> Tuple["RawObservation", ...]:
    """Exercise the frozen profile's positive control and four denied surfaces."""
    roots = tuple(Path(os.path.abspath(str(item))) for item in (materialized_root, gate_temp_root, profile_path))
    source, scratch, profile = roots
    expected_profile = render_gate_sandbox_profile(str(source), str(scratch))
    if _read_nofollow_regular(profile, METADATA_CAP) != expected_profile:
        raise ExecutionError("denial-check profile bytes drifted")
    helper = scratch / "gate-denial-probe.py"
    helper_raw = b"""import ctypes, errno, os, socket, subprocess, sys, tempfile
mode = sys.argv[1]
if mode == 'positive':
    fd, path = tempfile.mkstemp(dir=os.environ['TMPDIR'])
    os.write(fd, b'ok')
    os.close(fd)
    subprocess.run(['/usr/bin/true'], check=True)
    os.unlink(path)
elif mode in ('ipv4', 'ipv6'):
    family, address = (socket.AF_INET, ('127.0.0.1', 9)) if mode == 'ipv4' else (socket.AF_INET6, ('::1', 9))
    try:
        value = socket.socket(family, socket.SOCK_STREAM)
        value.settimeout(0.1)
        value.connect(address)
    except OSError as error:
        if error.errno not in (errno.EPERM, errno.EACCES):
            raise
    else:
        raise SystemExit(91)
elif mode == 'dns':
    value = None
    try:
        value = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        value.settimeout(0.1)
        value.connect(('127.0.0.1', 53))
        value.send(bytes.fromhex('123401000001000000000000076578616d706c6503636f6d0000010001'))
    except OSError as error:
        if error.errno not in (errno.EPERM, errno.EACCES):
            raise
    else:
        raise SystemExit(92)
    finally:
        if value is not None:
            value.close()
elif mode == 'mach':
    libc = ctypes.CDLL(None)
    bootstrap = ctypes.c_uint.in_dll(libc, 'bootstrap_port').value
    service = ctypes.c_uint(0)
    libc.bootstrap_look_up.argtypes = (ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint))
    libc.bootstrap_look_up.restype = ctypes.c_int
    if libc.bootstrap_look_up(bootstrap, b'com.apple.cfprefsd.daemon', ctypes.byref(service)) == 0:
        raise SystemExit(94)
else:
    raise SystemExit(95)
"""
    _write_fsync(helper, helper_raw)
    environment = gate_environment(str(scratch))
    prefix = (
        SANDBOX_EXEC_PATH,
        "-f",
        str(profile),
        "/usr/bin/python3",
        "-E",
        "-s",
        "-S",
        "-B",
        str(helper),
    )
    observations: List[RawObservation] = []
    try:
        for ordinal, mode in enumerate(("positive", "ipv4", "ipv6", "dns", "mach")):
            command = CommandSpec(
                ordinal=ordinal,
                role="gate-denial-" + mode,
                argv=prefix + (mode,),
                environment=environment,
                cwd=str(source),
                stdin_policy="closed-null",
                stdout_cap=16_384,
                stderr_cap=16_384,
                timeout_ns=10_000_000_000,
                activation="always",
                expected_outcomes=("exit_zero",),
            )
            observation = execute_direct(
                command,
                plan_sha256="0" * 64,
                completion_ordinal=ordinal,
                expected_executable_sha256=SANDBOX_EXEC_SHA256,
            )
            if (
                observation.value.get("outcome") != "exit"
                or observation.value.get("exit_code") != 0
                or observation.stdout != b""
                or observation.stderr != b""
            ):
                raise ExecutionError(
                    "gate sandbox denial probe failed: %s value=%r stdout=%r stderr=%r"
                    % (mode, observation.value, observation.stdout, observation.stderr)
                )
            observations.append(observation)
        return tuple(observations)
    finally:
        try:
            helper.unlink()
        except FileNotFoundError:
            pass


def _identity(metadata: os.stat_result) -> Dict[str, int]:
    return {
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "mode": stat.S_IMODE(metadata.st_mode),
        "uid": metadata.st_uid,
        "gid": metadata.st_gid,
        "link_count": metadata.st_nlink,
    }


def _capture_open_descriptor_observation(
    descriptor: int,
    *,
    absolute_path: str,
    role: str,
    relative_path: Optional[str],
) -> Dict[str, object]:
    if role not in {
        "source",
        "snapshot",
        "gate-source-pre",
        "gate-source-post",
        "gate-sandbox-exec",
        "gate-sandbox-profile",
        "docker-client",
        "buildx",
        "codesign",
        "docker-desktop-info-plist",
        "docker-desktop-vm",
        "docker-desktop-kernel",
        "docker-context",
        "protected",
        "review-python",
    }:
        raise ExecutionError("descriptor role is not allowed")
    _require_absolute(absolute_path, "descriptor path")
    if role in {"source", "snapshot", "gate-source-pre", "gate-source-post"}:
        if relative_path is None:
            raise ExecutionError("source descriptor requires a relative path")
        _validate_relative_path(relative_path)
    elif relative_path is not None:
        raise ExecutionError("tool/profile descriptor relative path must be null")
    before = os.fstat(descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink < 1
        or (role != "review-python" and before.st_nlink != 1)
    ):
        raise ExecutionError("descriptor path is not a single-link regular file")
    digest = hashlib.sha256()
    while True:
        chunk = os.read(descriptor, READ_CHUNK_BYTES)
        if not chunk:
            break
        digest.update(chunk)
    after = os.fstat(descriptor)
    before_identity = {
        **_identity(before),
        "size": before.st_size,
        "mtime_ns": before.st_mtime_ns,
        "ctime_ns": before.st_ctime_ns,
    }
    after_identity = {
        **_identity(after),
        "size": after.st_size,
        "mtime_ns": after.st_mtime_ns,
        "ctime_ns": after.st_ctime_ns,
    }
    if before_identity != after_identity:
        raise ExecutionError("descriptor identity changed during read")
    return {
        "schema": "hsai-p01b-descriptor-observation-v1",
        "role": role,
        "path": absolute_path,
        "relative_path": relative_path,
        "before": before_identity,
        "after": after_identity,
        "sha256": digest.hexdigest(),
    }


def capture_descriptor_observation(
    path: Path, role: str, *, relative_path: Optional[str] = None
) -> Dict[str, object]:
    """Read one single-link regular file once through a no-follow descriptor."""
    absolute = os.path.abspath(str(path))
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = os.open(absolute, flags)
    try:
        return _capture_open_descriptor_observation(
            descriptor,
            absolute_path=absolute,
            role=role,
            relative_path=relative_path,
        )
    finally:
        os.close(descriptor)


def _read_observed_regular(
    path: Path, role: str, relative_path: Optional[str], cap: int
) -> Tuple[Dict[str, object], bytes]:
    """Retain bounded bytes and their complete descriptor identity in one read."""
    absolute = os.path.abspath(str(path))
    _require_absolute(absolute, "observed path")
    if relative_path is not None:
        _validate_relative_path(relative_path)
    descriptor = os.open(
        absolute,
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ExecutionError("observed path is not a single-link regular file")
        raw = bytearray()
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, cap + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
            digest.update(chunk)
            if len(raw) > cap:
                raise ExecutionError("observed path exceeds its byte cap")
        after = os.fstat(descriptor)
        before_identity = {
            **_identity(before),
            "size": before.st_size,
            "mtime_ns": before.st_mtime_ns,
            "ctime_ns": before.st_ctime_ns,
        }
        after_identity = {
            **_identity(after),
            "size": after.st_size,
            "mtime_ns": after.st_mtime_ns,
            "ctime_ns": after.st_ctime_ns,
        }
        if before_identity != after_identity or before.st_size != len(raw):
            raise ExecutionError("observed path changed during read")
        observation = {
            "schema": "hsai-p01b-descriptor-observation-v1",
            "role": role,
            "path": absolute,
            "relative_path": relative_path,
            "before": before_identity,
            "after": after_identity,
            "sha256": digest.hexdigest(),
        }
        _load_evidence_module().validate_descriptor_observation(observation)
        return observation, bytes(raw)
    finally:
        os.close(descriptor)


def _descriptor_observations_match(
    before: Mapping[str, object], after: Mapping[str, object]
) -> bool:
    """Compare immutable descriptor facts while retaining distinct phase roles."""
    return (
        before.get("role") == "gate-source-pre"
        and after.get("role") == "gate-source-post"
        and {key: value for key, value in before.items() if key != "role"}
        == {key: value for key, value in after.items() if key != "role"}
    )


def _git_blob_oid(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def _gate_command_rows(source_root: str, scratch_root: str, profile_path: str) -> List[Dict[str, object]]:
    environment = gate_environment(scratch_root)
    prefix = (
        SANDBOX_EXEC_PATH,
        "-f",
        profile_path,
        "/usr/bin/python3",
        "-E",
        "-s",
        "-S",
        "-B",
    )
    commands = (
        (
            "evidence-focused",
            prefix
            + (
                "tools/hsai-formal-preflight/p01b_container_evidence_tests.py",
                "-v",
            ),
        ),
        (
            "execution-focused",
            prefix
            + (
                "tools/hsai-formal-preflight/p01b_container_execution_tests.py",
                "-v",
            ),
        ),
        (
            "formal-discovery",
            prefix
            + (
                "-m",
                "unittest",
                "discover",
                "-s",
                "tools/hsai-formal-preflight/tests",
                "-p",
                "test_*.py",
                "-v",
            ),
        ),
    )
    return [
        {
            "role": role,
            "argv": list(argv),
            "environment": environment,
            "cwd": source_root,
            "stdin_policy": "closed",
            "timeout_ns": 600_000_000_000,
            "stdout_cap_bytes": 262_144,
            "stderr_cap_bytes": 262_144,
            "activation": "always",
            "expected_exit_code": 0,
            "expected_signal": None,
        }
        for role, argv in commands
    ]


def _focused_ids_from_source(path: str, raw: bytes) -> List[str]:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=path)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ExecutionError("focused test source is not valid UTF-8 Python") from error
    identifiers: List[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test_"):
                identifiers.append("__main__.%s.%s" % (node.name, child.name))
    identifiers.sort()
    if path == SOURCE_PATHS[-1]:
        expected = 32
    elif path == SOURCE_PATHS[-2]:
        expected = 33
    else:
        raise ExecutionError("focused test source path is not a reviewed focused suite")
    if len(identifiers) != expected or len(set(identifiers)) != expected:
        raise ExecutionError(
            "focused test source must contain exactly %d unique test methods" % expected
        )
    return identifiers


def census_focused_test_ids(ordered_sources: Mapping[str, bytes]) -> Tuple[str, ...]:
    """Derive, rather than accept, the exact 65 immutable focused test ids."""
    if tuple(ordered_sources) != SOURCE_PATHS:
        raise ExecutionError("focused test census is not over the exact source set")
    paths = SOURCE_PATHS[-2:]
    identifiers: List[str] = []
    for path in paths:
        identifiers.extend(_focused_ids_from_source(path, ordered_sources[path]))
    identifiers.sort()
    if len(identifiers) != 65 or len(set(identifiers)) != 65:
        raise ExecutionError("combined focused test census is not 65 sorted unique ids")
    return tuple(identifiers)


def _complete_command_observation(
    raw: "RawObservation",
    command: "CommandSpec",
    *,
    role: Optional[str] = None,
    cwd_identity_before: Optional[Mapping[str, object]] = None,
    cwd_identity_after: Optional[Mapping[str, object]] = None,
) -> Dict[str, object]:
    value = raw.value
    if (
        value.get("outcome") != "exit"
        or value.get("exit_code") != 0
        or value.get("signal") is not None
        or value.get("stdout_truncated") is not False
        or value.get("stderr_truncated") is not False
    ):
        raise ExecutionError("bounded gate/source command did not complete")
    result: Dict[str, object] = {
        "role": command.role if role is None else role,
        "argv": list(command.argv),
        "environment": dict(command.environment),
        "cwd": command.cwd,
        "stdin_policy": "closed",
        "executable_path": command.argv[0],
        "executable_sha256": value["executable_sha256"],
        "timeout_ns": command.timeout_ns,
        "stdout_cap_bytes": command.stdout_cap,
        "stderr_cap_bytes": command.stderr_cap,
        "started_monotonic_ns": value["started_monotonic_ns"],
        "ended_monotonic_ns": value["ended_monotonic_ns"],
        "outcome": "completed",
        "exit_code": 0,
        "signal": None,
        "stdout_total_bytes": len(raw.stdout),
        "stdout_retained_bytes": len(raw.stdout),
        "stdout_truncated": False,
        "stdout_base64": base64.b64encode(raw.stdout).decode("ascii"),
        "stdout_sha256": sha256_bytes(raw.stdout),
        "stderr_total_bytes": len(raw.stderr),
        "stderr_retained_bytes": len(raw.stderr),
        "stderr_truncated": False,
        "stderr_base64": base64.b64encode(raw.stderr).decode("ascii"),
        "stderr_sha256": sha256_bytes(raw.stderr),
    }
    if cwd_identity_before is not None or cwd_identity_after is not None:
        if cwd_identity_before is None or cwd_identity_after is None:
            raise ExecutionError("gate cwd identity pair is incomplete")
        result["cwd_identity_before"] = dict(cwd_identity_before)
        result["cwd_identity_after"] = dict(cwd_identity_after)
    return result


def _source_command(
    *,
    role: str,
    argv: Sequence[str],
    environment: Mapping[str, str],
    cwd: str,
    stdout_cap: int,
    expected_executable_sha256: str,
) -> Tuple[Dict[str, object], bytes]:
    command = CommandSpec(
        ordinal=0,
        role=role,
        argv=tuple(argv),
        environment=environment,
        cwd=cwd,
        stdin_policy="closed-null",
        stdout_cap=stdout_cap,
        stderr_cap=16_384,
        timeout_ns=60_000_000_000,
        activation="always",
        expected_outcomes=("exit_zero",),
    )
    raw = execute_direct(
        command,
        plan_sha256="0" * 64,
        completion_ordinal=0,
        expected_executable_sha256=expected_executable_sha256,
    )
    observation = _complete_command_observation(raw, command)
    if raw.stderr != b"":
        raise ExecutionError("Git/source command stderr is not empty")
    return observation, raw.stdout


def _status_paths(raw: bytes) -> Tuple[str, ...]:
    """Extract complete porcelain-v2 -z paths without lossy shell parsing."""
    records = raw.split(b"\0")
    if records and records[-1] == b"":
        records.pop()
    paths: List[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        if record.startswith((b"? ", b"! ")):
            path = record[2:]
        elif record.startswith(b"1 "):
            fields = record.split(b" ", 8)
            if len(fields) != 9:
                raise ExecutionError("porcelain-v2 ordinary record is malformed")
            path = fields[8]
        elif record.startswith(b"2 "):
            fields = record.split(b" ", 9)
            if len(fields) != 10 or index + 1 >= len(records):
                raise ExecutionError("porcelain-v2 rename record is malformed")
            path = fields[9]
            index += 1
            original = records[index]
            try:
                paths.append(original.decode("utf-8"))
            except UnicodeDecodeError as error:
                raise ExecutionError("porcelain-v2 path is not UTF-8") from error
        elif record.startswith(b"u "):
            fields = record.split(b" ", 10)
            if len(fields) != 11:
                raise ExecutionError("porcelain-v2 unmerged record is malformed")
            path = fields[10]
        elif record.startswith(b"# "):
            index += 1
            continue
        else:
            raise ExecutionError("unknown porcelain-v2 record")
        try:
            paths.append(path.decode("utf-8"))
        except UnicodeDecodeError as error:
            raise ExecutionError("porcelain-v2 path is not UTF-8") from error
        index += 1
    return tuple(paths)


def _validate_gate_status_scope(raw: bytes, repository_root: Path) -> None:
    protected = {".gitmodules"}
    for source in SOURCE_PATHS:
        protected.add(source)
        parts = source.split("/")[:-1]
        for count in range(1, len(parts) + 1):
            protected.add("/".join(parts[:count]))
    for path in _status_paths(raw):
        if path in protected:
            raise ExecutionError("gate source or ancestor is dirty: " + path)
    for relative in sorted(protected - {".gitmodules"}, key=lambda item: item.encode("ascii")):
        path = repository_root / relative
        if relative in SOURCE_PATHS:
            continue
        metadata = os.lstat(path)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise ExecutionError("gate source ancestor is not a real directory")


def _capture_gate_tree(
    root: Path, role: str
) -> Tuple[Tuple[Mapping[str, object], ...], Tuple[Mapping[str, object], ...], Tuple[Tuple[int, int], ...]]:
    if role not in {"gate-source-pre", "gate-source-post"}:
        raise ExecutionError("gate tree descriptor role is invalid")
    absolute = Path(os.path.abspath(str(root)))
    expected_kinds: Dict[str, str] = {".": "directory"}
    expected_children: Dict[str, Dict[str, str]] = {".": {}}
    for relative in SOURCE_PATHS:
        parts = _validate_relative_path(relative)
        parent = "."
        for index, name in enumerate(parts):
            child = "/".join(parts[: index + 1])
            kind = "regular" if index == len(parts) - 1 else "directory"
            prior = expected_kinds.setdefault(child, kind)
            if prior != kind:
                raise ExecutionError("gate source grammar has a path-type collision")
            expected_children.setdefault(parent, {})[name] = kind
            if kind == "directory":
                expected_children.setdefault(child, {})
            parent = child
    rows: List[Mapping[str, object]] = []
    observations: Dict[str, Mapping[str, object]] = {}
    timings: Dict[str, Tuple[int, int]] = {}

    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )

    def visit(directory_fd: int, relative_directory: str) -> None:
        metadata = os.fstat(directory_fd)
        directory_identity = _identity(metadata)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or directory_identity["mode"] != 0o555
        ):
            raise ExecutionError("gate source directory identity drifted")
        rows.append(
            {
                "path": relative_directory,
                "type": "directory",
                **directory_identity,
                "bytes": None,
                "sha256": None,
            }
        )
        try:
            names = os.listdir(directory_fd)
            ordered_names = sorted(names, key=lambda item: item.encode("ascii"))
        except (OSError, UnicodeEncodeError) as error:
            raise ExecutionError("gate source directory listing failed") from error
        expected = expected_children[relative_directory]
        if ordered_names != sorted(expected, key=lambda item: item.encode("ascii")):
            raise ExecutionError("gate source contains an unexpected or missing entry")
        for name in ordered_names:
            relative = (
                name
                if relative_directory == "."
                else relative_directory + "/" + name
            )
            listed = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISLNK(listed.st_mode):
                raise ExecutionError("gate source contains a symlink")
            if expected[name] == "directory":
                if not stat.S_ISDIR(listed.st_mode):
                    raise ExecutionError("gate source directory type drifted")
                child_fd = os.open(name, directory_flags, dir_fd=directory_fd)
                try:
                    if _identity(os.fstat(child_fd)) != _identity(listed):
                        raise ExecutionError("gate source directory changed before open")
                    visit(child_fd, relative)
                    if _identity(os.fstat(child_fd)) != _identity(listed):
                        raise ExecutionError("gate source directory changed during traversal")
                finally:
                    os.close(child_fd)
                continue
            if not stat.S_ISREG(listed.st_mode):
                raise ExecutionError("gate source file type drifted")
            started = time.monotonic_ns()
            descriptor = os.open(name, file_flags, dir_fd=directory_fd)
            try:
                observation = _capture_open_descriptor_observation(
                    descriptor,
                    absolute_path=str(absolute / relative),
                    role=role,
                    relative_path=relative,
                )
            finally:
                os.close(descriptor)
            ended = time.monotonic_ns()
            identity = observation["before"]
            assert isinstance(identity, dict)
            listed_identity = {
                **_identity(listed),
                "size": listed.st_size,
                "mtime_ns": listed.st_mtime_ns,
                "ctime_ns": listed.st_ctime_ns,
            }
            if identity != listed_identity:
                raise ExecutionError("gate source file changed before descriptor open")
            if identity["mode"] != 0o444:
                raise ExecutionError("gate source file is not mode 0444")
            rows.append(
                {
                    "path": relative,
                    "type": "regular",
                    "device": identity["device"],
                    "inode": identity["inode"],
                    "mode": identity["mode"],
                    "uid": identity["uid"],
                    "gid": identity["gid"],
                    "link_count": identity["link_count"],
                    "bytes": identity["size"],
                    "sha256": observation["sha256"],
                }
            )
            observations[relative] = observation
            timings[relative] = (started, ended)
        if _identity(os.fstat(directory_fd)) != directory_identity:
            raise ExecutionError("gate source directory changed during traversal")

    root_fd = os.open(str(absolute), directory_flags)
    try:
        visit(root_fd, ".")
    finally:
        os.close(root_fd)
    rows.sort(key=lambda row: (str(row["path"]) != ".", str(row["path"]).encode("ascii")))
    files = tuple(str(row["path"]) for row in rows if row["type"] == "regular")
    expected_files = tuple(sorted(SOURCE_PATHS, key=lambda path: path.encode("ascii")))
    if files != expected_files:
        raise ExecutionError(
            "gate source inventory is not the exact %d-file set" % len(SOURCE_PATHS)
        )
    identities = [(row["device"], row["inode"]) for row in rows if row["type"] == "regular"]
    if len(identities) != len(set(identities)):
        raise ExecutionError("gate source files are not inode-unique")
    return (
        tuple(rows),
        tuple(observations[path] for path in SOURCE_PATHS),
        tuple(timings[path] for path in SOURCE_PATHS),
    )


@dataclass(frozen=True)
class GateMaterialization:
    parent: str
    source_root: str
    scratch_root: str
    profile_path: str
    profile_sha256: str
    inventory: Tuple[Mapping[str, object], ...]
    source_observations: Tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class A3L6GateCapture:
    materialization: GateMaterialization
    implementation_commit: str
    implementation_tree: str
    audit_commit: str
    git_path: str
    git_sha256: str
    environment: Mapping[str, str]
    repository_cwd: str
    head_observation: Mapping[str, object]
    tree_observation: Mapping[str, object]
    status_before_observation: Mapping[str, object]
    ordered_blob_observations: Tuple[Mapping[str, object], ...]
    ordered_sources: Tuple[Mapping[str, object], ...]
    focused_test_ids: Tuple[str, ...]
    pre_gate_capture_ended_monotonic_ns: int


@dataclass(frozen=True)
class A3L6GateRun:
    gate_plan: Mapping[str, object]
    gate_source_manifest: Mapping[str, object]
    python_version_observation: Mapping[str, object]
    ordered_gate_observations: Tuple[Mapping[str, object], ...]
    focused_test_ids: Tuple[str, ...]
    focused_test_count: int
    discovery_test_count: int


def capture_a3l6_gate_sources(
    *,
    repository_root: Path,
    parent: Path,
    implementation_commit: str,
    implementation_tree: str,
    audit_commit: str,
) -> A3L6GateCapture:
    """Capture exact Git objects and materialize only their verified blob bytes."""
    for field, value in (
        ("implementation_commit", implementation_commit),
        ("implementation_tree", implementation_tree),
        ("audit_commit", audit_commit),
    ):
        _require_git(value, field)
    repository_root = Path(os.path.abspath(str(repository_root)))
    parent = Path(os.path.abspath(str(parent)))
    if re.fullmatch(r"/private/tmp/hsai-p01b-gate-[0-9a-f]{32}", str(parent)) is None:
        raise ExecutionError("gate parent path is not the frozen /private/tmp grammar")
    parent.mkdir(mode=0o700, parents=False, exist_ok=False)
    source = parent / "source"
    scratch = parent / "scratch"
    profile = parent / "gate.sb"
    source.mkdir(mode=0o700)
    scratch.mkdir(mode=0o700)
    environment = gate_environment(str(scratch))
    git_path = "/usr/bin/git"
    git_sha256 = _executable_sha256(git_path)
    try:
        head_observation, head_raw = _source_command(
            role="gate-head",
            argv=(git_path, "rev-parse", "HEAD"),
            environment=environment,
            cwd=str(repository_root),
            stdout_cap=4_096,
            expected_executable_sha256=git_sha256,
        )
        if head_raw != (audit_commit + "\n").encode("ascii"):
            raise ExecutionError("gate audit HEAD drifted")
        tree_observation, tree_raw = _source_command(
            role="gate-tree",
            argv=(git_path, "rev-parse", implementation_commit + "^{tree}"),
            environment=environment,
            cwd=str(repository_root),
            stdout_cap=4_096,
            expected_executable_sha256=git_sha256,
        )
        if tree_raw != (implementation_tree + "\n").encode("ascii"):
            raise ExecutionError("gate implementation tree drifted")
        status_observation, status_raw = _source_command(
            role="gate-status-before",
            argv=(git_path, "status", "--porcelain=v2", "-z", "--untracked-files=all"),
            environment=environment,
            cwd=str(repository_root),
            stdout_cap=1_048_576,
            expected_executable_sha256=git_sha256,
        )
        _validate_gate_status_scope(status_raw, repository_root)
        directories = {source}
        blobs: List[Mapping[str, object]] = []
        source_rows: List[Mapping[str, object]] = []
        source_bytes: Dict[str, bytes] = {}
        for ordinal, relative in enumerate(SOURCE_PATHS):
            observation, raw = _source_command(
                role="gate-blob-%03d" % ordinal,
                argv=(git_path, "cat-file", "blob", implementation_commit + ":" + relative),
                environment=environment,
                cwd=str(repository_root),
                stdout_cap=16_777_216,
                expected_executable_sha256=git_sha256,
            )
            destination = source / relative
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            current = destination.parent
            while current != source.parent:
                directories.add(current)
                if current == source:
                    break
                current = current.parent
            _write_fsync(destination, raw)
            os.chmod(destination, 0o444)
            started = time.monotonic_ns()
            descriptor = capture_descriptor_observation(
                destination, "gate-source-pre", relative_path=relative
            )
            ended = time.monotonic_ns()
            blobs.append(observation)
            source_bytes[relative] = raw
            source_rows.append(
                {
                    "path": relative,
                    "git_object_expression": implementation_commit + ":" + relative,
                    "git_blob_oid": _git_blob_oid(raw),
                    "bytes": len(raw),
                    "sha256": sha256_bytes(raw),
                    "pre_gate_started_monotonic_ns": started,
                    "pre_gate_ended_monotonic_ns": ended,
                    "pre_gate_descriptor_observation": descriptor,
                    "post_gate_started_monotonic_ns": None,
                    "post_gate_ended_monotonic_ns": None,
                    "post_gate_descriptor_observation": None,
                }
            )
        for directory in sorted(directories, key=lambda item: len(item.parts), reverse=True):
            os.chmod(directory, 0o555)
        profile_raw = render_gate_sandbox_profile(str(source), str(scratch))
        _write_fsync(profile, profile_raw)
        os.chmod(profile, 0o400)
        inventory, observations, _ = _capture_gate_tree(source, "gate-source-pre")
        for row, observation in zip(source_rows, observations):
            if row["pre_gate_descriptor_observation"] != observation:
                raise ExecutionError("pre-gate descriptor recapture drifted")
        focused_ids = census_focused_test_ids(source_bytes)
        pre_end = time.monotonic_ns()
        materialization = GateMaterialization(
            str(parent),
            str(source),
            str(scratch),
            str(profile),
            sha256_bytes(profile_raw),
            inventory,
            observations,
        )
        return A3L6GateCapture(
            materialization,
            implementation_commit,
            implementation_tree,
            audit_commit,
            git_path,
            git_sha256,
            environment,
            str(repository_root),
            head_observation,
            tree_observation,
            status_observation,
            tuple(blobs),
            tuple(source_rows),
            focused_ids,
            pre_end,
        )
    except BaseException:
        for directory, _, _ in os.walk(parent):
            try:
                os.chmod(directory, 0o700)
            except OSError:
                pass
        shutil.rmtree(parent, ignore_errors=True)
        raise


_UNITTEST_RESULT_RE = re.compile(
    rb"\A(?P<body>.*)\n----------------------------------------------------------------------\n"
    rb"Ran (?P<count>[0-9]+) tests? in (?P<seconds>[0-9]+(?:\.[0-9]+)?)s\n\nOK\n\Z",
    re.DOTALL,
)
_UNITTEST_LINE_RE = re.compile(
    rb"\A(?P<method>test_[A-Za-z0-9_]+) \((?P<owner>[^()\r\n]+)\) \.\.\. ok\n\Z"
)


def parse_unittest_transcript(
    raw: bytes, *, expected_count: int, expected_ids: Optional[Sequence[str]]
) -> Tuple[str, ...]:
    """Reject every non-success verbose unittest transcript or id substitution."""
    if not isinstance(raw, bytes) or b"\r" in raw:
        raise ExecutionError("unittest transcript framing changed")
    match = _UNITTEST_RESULT_RE.fullmatch(raw)
    if match is None or int(match.group("count")) != expected_count:
        raise ExecutionError("unittest summary count changed")
    seconds = float(match.group("seconds").decode("ascii"))
    if not math.isfinite(seconds):
        raise ExecutionError("unittest duration is not finite")
    identifiers: List[str] = []
    body = match.group("body")
    for line in body.splitlines(keepends=True):
        line_match = _UNITTEST_LINE_RE.fullmatch(line)
        if line_match is None:
            raise ExecutionError("unittest result row changed: %r" % line)
        method = line_match.group("method").decode("ascii")
        identifier = line_match.group("owner").decode("ascii") + "." + method
        identifiers.append(identifier)
    if len(identifiers) != expected_count or len(set(identifiers)) != expected_count:
        raise ExecutionError("unittest id census changed")
    if expected_ids is not None and tuple(identifiers) != tuple(expected_ids):
        raise ExecutionError("unittest ordered ids changed")
    return tuple(identifiers)


def build_a3l6_gate_plan(
    *, capture: A3L6GateCapture, gate_source_manifest: Mapping[str, object]
) -> Dict[str, object]:
    """Finalize the plan only from the frozen roots and reconstructed command rows."""
    manifest_sha256 = domain_sha256(
        "hsai:p01b-a3l6-gate-source-manifest:v1", gate_source_manifest
    )
    materialization = capture.materialization
    commands = _gate_command_rows(
        materialization.source_root,
        materialization.scratch_root,
        materialization.profile_path,
    )
    root_identity = _identity(os.lstat(materialization.source_root))
    return {
        "schema": "hsai-p01b-a3l6-gate-plan-v1",
        "implementation_commit": capture.implementation_commit,
        "implementation_tree": capture.implementation_tree,
        "audit_commit": capture.audit_commit,
        "python_path": "/usr/bin/python3",
        "python_sha256": NATIVE_PYTHON_SHA256,
        "python_version": "3.9.6",
        "environment": dict(capture.environment),
        "gate_source_root": materialization.source_root,
        "gate_source_root_identity": root_identity,
        "gate_temp_root": materialization.scratch_root,
        "sandbox_exec_path": SANDBOX_EXEC_PATH,
        "sandbox_exec_sha256": SANDBOX_EXEC_SHA256,
        "sandbox_profile_path": materialization.profile_path,
        "sandbox_profile_sha256": materialization.profile_sha256,
        "gate_source_manifest_sha256": manifest_sha256,
        "cwd": materialization.source_root,
        "commands": commands,
        "reviewed_paths": list(REVIEWED_PATHS),
        "expected_focused_test_ids": list(capture.focused_test_ids),
        "expected_focused_test_count": 65,
        "expected_discovery_test_count": 172,
    }


def _gate_command_spec(row: Mapping[str, object], ordinal: int) -> "CommandSpec":
    expected = {
        "role",
        "argv",
        "environment",
        "cwd",
        "stdin_policy",
        "timeout_ns",
        "stdout_cap_bytes",
        "stderr_cap_bytes",
        "activation",
        "expected_exit_code",
        "expected_signal",
    }
    if set(row) != expected or row.get("stdin_policy") != "closed":
        raise ExecutionError("gate command row fields changed")
    if (
        row.get("activation") != "always"
        or row.get("expected_exit_code") != 0
        or row.get("expected_signal") is not None
    ):
        raise ExecutionError("gate command expected outcome changed")
    return CommandSpec(
        ordinal=ordinal,
        role=row["role"],  # type: ignore[arg-type]
        argv=tuple(row["argv"]),  # type: ignore[arg-type]
        environment=row["environment"],  # type: ignore[arg-type]
        cwd=row["cwd"],  # type: ignore[arg-type]
        stdin_policy="closed-null",
        stdout_cap=row["stdout_cap_bytes"],  # type: ignore[arg-type]
        stderr_cap=row["stderr_cap_bytes"],  # type: ignore[arg-type]
        timeout_ns=row["timeout_ns"],  # type: ignore[arg-type]
        activation="always",
        expected_outcomes=("exit_zero",),
    )


def _execute_gate_command(
    row: Mapping[str, object],
    ordinal: int,
    *,
    expected_root_identity: Mapping[str, object],
    expected_profile_sha256: str,
) -> Dict[str, object]:
    command = _gate_command_spec(row, ordinal)
    root_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    root_flags |= getattr(os, "O_NOFOLLOW", 0)
    root_fd = os.open(command.cwd, root_flags)
    saved_fd = os.open(".", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    process: Optional[DirectProcess] = None
    try:
        before = _identity(os.fstat(root_fd))
        if before != dict(expected_root_identity):
            raise ExecutionError("gate cwd identity drifted before spawn")
        sandbox_observation = capture_descriptor_observation(
            Path(SANDBOX_EXEC_PATH), "gate-sandbox-exec"
        )
        profile_observation = capture_descriptor_observation(
            Path(command.argv[2]), "gate-sandbox-profile"
        )
        if (
            sandbox_observation["sha256"] != SANDBOX_EXEC_SHA256
            or profile_observation["sha256"] != expected_profile_sha256
        ):
            raise ExecutionError("gate wrapper/profile identity drifted")
        os.fchdir(root_fd)
        try:
            process = DirectProcess(
                command,
                expected_executable_sha256=SANDBOX_EXEC_SHA256,
                use_inherited_cwd=True,
            )
        finally:
            os.fchdir(saved_fd)
        raw = process.complete(
            plan_sha256="0" * 64,
            completion_ordinal=ordinal,
            previous_observation_sha256=None,
        )
        after = _identity(os.fstat(root_fd))
        if after != before:
            raise ExecutionError("gate cwd identity drifted after execution")
        observation = _complete_command_observation(
            raw,
            command,
            cwd_identity_before=before,
            cwd_identity_after=after,
        )
        if raw.stdout != b"":
            raise ExecutionError("gate stdout is not empty")
        return observation
    except BaseException:
        if process is not None:
            process.abort()
        raise
    finally:
        os.close(saved_fd)
        os.close(root_fd)


def _decode_observation_stream(observation: Mapping[str, object], prefix: str) -> bytes:
    encoded = observation.get(prefix + "_base64")
    if not isinstance(encoded, str):
        raise ExecutionError("observation stream is not base64 text")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as error:
        raise ExecutionError("observation stream base64 is invalid") from error
    if (
        observation.get(prefix + "_total_bytes") != len(raw)
        or observation.get(prefix + "_retained_bytes") != len(raw)
        or observation.get(prefix + "_truncated") is not False
        or observation.get(prefix + "_sha256") != sha256_bytes(raw)
    ):
        raise ExecutionError("observation stream metadata drifted")
    return raw


def execute_a3l6_gates(capture: A3L6GateCapture) -> A3L6GateRun:
    """Execute the three frozen rows, then close their immutable post-state."""
    materialization = capture.materialization
    expected_rows = _gate_command_rows(
        materialization.source_root,
        materialization.scratch_root,
        materialization.profile_path,
    )
    sandbox_observation = capture_descriptor_observation(
        Path(SANDBOX_EXEC_PATH), "gate-sandbox-exec"
    )
    profile_observation = capture_descriptor_observation(
        Path(materialization.profile_path), "gate-sandbox-profile"
    )
    if sandbox_observation["sha256"] != SANDBOX_EXEC_SHA256:
        raise ExecutionError("sandbox-exec identity drifted")
    if profile_observation["sha256"] != materialization.profile_sha256:
        raise ExecutionError("sandbox profile identity drifted")
    python_observation, python_stdout = _source_command(
        role="gate-python-version",
        argv=("/usr/bin/python3", "--version"),
        environment=capture.environment,
        cwd=materialization.source_root,
        stdout_cap=16_384,
        expected_executable_sha256=NATIVE_PYTHON_SHA256,
    )
    if python_stdout != b"Python 3.9.6\n":
        raise ExecutionError("gate Python version transcript drifted")
    root_identity = _identity(os.lstat(materialization.source_root))
    observations: List[Mapping[str, object]] = []
    focused_paths = {
        "evidence-focused": SOURCE_PATHS[-1],
        "execution-focused": SOURCE_PATHS[-2],
    }
    for ordinal, row in enumerate(expected_rows):
        observation = _execute_gate_command(
            row,
            ordinal,
            expected_root_identity=root_identity,
            expected_profile_sha256=materialization.profile_sha256,
        )
        role = str(row["role"])
        if role in focused_paths:
            raw = _read_nofollow_regular(
                Path(materialization.source_root) / focused_paths[role],
                SNAPSHOT_FILE_LIMIT,
            )
            expected_ids: Optional[Sequence[str]] = _focused_ids_from_source(
                focused_paths[role], raw
            )
            expected_count = 32 if role == "evidence-focused" else 33
        else:
            expected_ids = None
            expected_count = 172
        try:
            parse_unittest_transcript(
                _decode_observation_stream(observation, "stderr"),
                expected_count=expected_count,
                expected_ids=expected_ids,
            )
        except ExecutionError as error:
            raise ExecutionError("%s transcript rejected: %s" % (role, error)) from error
        if observations and observations[-1]["ended_monotonic_ns"] > observation["started_monotonic_ns"]:
            raise ExecutionError("gate observations overlap")
        observations.append(observation)
    if not observations:
        raise ExecutionError("gate observations are absent")
    if capture.pre_gate_capture_ended_monotonic_ns > observations[0]["started_monotonic_ns"]:
        raise ExecutionError("gate started before pre-gate capture ended")
    post_started = time.monotonic_ns()
    if observations[-1]["ended_monotonic_ns"] > post_started:
        raise ExecutionError("post-gate capture started before final gate ended")
    inventory_after, post_observations, post_timings = _capture_gate_tree(
        Path(materialization.source_root), "gate-source-post"
    )
    if inventory_after != materialization.inventory:
        raise ExecutionError("immutable gate inventory changed")
    status_after, status_raw = _source_command(
        role="gate-status-after",
        argv=(capture.git_path, "status", "--porcelain=v2", "-z", "--untracked-files=all"),
        environment=capture.environment,
        cwd=capture.repository_cwd,
        stdout_cap=1_048_576,
        expected_executable_sha256=capture.git_sha256,
    )
    if status_after["started_monotonic_ns"] < post_started:
        raise ExecutionError("post-gate status capture started too early")
    before_status = _decode_observation_stream(capture.status_before_observation, "stdout")
    if status_raw != before_status:
        raise ExecutionError("repository status changed across gates")
    _validate_gate_status_scope(status_raw, Path(capture.repository_cwd))
    source_rows: List[Dict[str, object]] = []
    for original, post, timing in zip(
        capture.ordered_sources, post_observations, post_timings
    ):
        row = dict(original)
        row["post_gate_started_monotonic_ns"] = timing[0]
        row["post_gate_ended_monotonic_ns"] = timing[1]
        row["post_gate_descriptor_observation"] = post
        if not _descriptor_observations_match(
            row["pre_gate_descriptor_observation"], post  # type: ignore[arg-type]
        ):
            raise ExecutionError("source descriptor changed across gates")
        if row["post_gate_started_monotonic_ns"] < post_started:
            raise ExecutionError("post source capture started too early")
        source_rows.append(row)
    inventory_raw = canonical_json_bytes(list(materialization.inventory))
    profile_raw = _read_nofollow_regular(Path(materialization.profile_path), METADATA_CAP)
    source_manifest: Dict[str, object] = {
        "schema": "hsai-p01b-a3l6-gate-source-manifest-v1",
        "implementation_commit": capture.implementation_commit,
        "implementation_tree": capture.implementation_tree,
        "audit_commit": capture.audit_commit,
        "git_path": capture.git_path,
        "git_sha256": capture.git_sha256,
        "environment": dict(capture.environment),
        "repository_cwd": capture.repository_cwd,
        "materialized_root": materialization.source_root,
        "materialized_root_identity": root_identity,
        "gate_temp_root": materialization.scratch_root,
        "sandbox_exec_descriptor_observation": sandbox_observation,
        "sandbox_profile_path": materialization.profile_path,
        "sandbox_profile_descriptor_observation": profile_observation,
        "sandbox_profile_base64": base64.b64encode(profile_raw).decode("ascii"),
        "sandbox_profile_sha256": sha256_bytes(profile_raw),
        "materialized_inventory_before_sha256": sha256_bytes(inventory_raw),
        "materialized_inventory_before": list(materialization.inventory),
        "materialized_inventory_after_sha256": sha256_bytes(
            canonical_json_bytes(list(inventory_after))
        ),
        "materialized_inventory_after": list(inventory_after),
        "head_observation": dict(capture.head_observation),
        "tree_observation": dict(capture.tree_observation),
        "status_before_observation": dict(capture.status_before_observation),
        "ordered_blob_observations": [dict(item) for item in capture.ordered_blob_observations],
        "ordered_sources": source_rows,
        "pre_gate_capture_ended_monotonic_ns": capture.pre_gate_capture_ended_monotonic_ns,
        "post_gate_capture_started_monotonic_ns": post_started,
        "status_after_observation": status_after,
    }
    plan = build_a3l6_gate_plan(capture=capture, gate_source_manifest=source_manifest)
    validate_a3l6_gate_plan_execution(plan, source_manifest, observations)
    return A3L6GateRun(
        plan,
        source_manifest,
        python_observation,
        tuple(observations),
        capture.focused_test_ids,
        65,
        172,
    )


_SOURCE_MANIFEST_FIELDS = {
    "schema",
    "implementation_commit",
    "implementation_tree",
    "audit_commit",
    "git_path",
    "git_sha256",
    "environment",
    "repository_cwd",
    "materialized_root",
    "materialized_root_identity",
    "gate_temp_root",
    "sandbox_exec_descriptor_observation",
    "sandbox_profile_path",
    "sandbox_profile_descriptor_observation",
    "sandbox_profile_base64",
    "sandbox_profile_sha256",
    "materialized_inventory_before_sha256",
    "materialized_inventory_before",
    "materialized_inventory_after_sha256",
    "materialized_inventory_after",
    "head_observation",
    "tree_observation",
    "status_before_observation",
    "ordered_blob_observations",
    "ordered_sources",
    "pre_gate_capture_ended_monotonic_ns",
    "post_gate_capture_started_monotonic_ns",
    "status_after_observation",
}
_GATE_PLAN_FIELDS = {
    "schema",
    "implementation_commit",
    "implementation_tree",
    "audit_commit",
    "python_path",
    "python_sha256",
    "python_version",
    "environment",
    "gate_source_root",
    "gate_source_root_identity",
    "gate_temp_root",
    "sandbox_exec_path",
    "sandbox_exec_sha256",
    "sandbox_profile_path",
    "sandbox_profile_sha256",
    "gate_source_manifest_sha256",
    "cwd",
    "commands",
    "reviewed_paths",
    "expected_focused_test_ids",
    "expected_focused_test_count",
    "expected_discovery_test_count",
}
_COMMAND_OBSERVATION_FIELDS = {
    "role",
    "argv",
    "environment",
    "cwd",
    "stdin_policy",
    "executable_path",
    "executable_sha256",
    "timeout_ns",
    "stdout_cap_bytes",
    "stderr_cap_bytes",
    "started_monotonic_ns",
    "ended_monotonic_ns",
    "outcome",
    "exit_code",
    "signal",
    "stdout_total_bytes",
    "stdout_retained_bytes",
    "stdout_truncated",
    "stdout_base64",
    "stdout_sha256",
    "stderr_total_bytes",
    "stderr_retained_bytes",
    "stderr_truncated",
    "stderr_base64",
    "stderr_sha256",
}
_GATE_OBSERVATION_FIELDS = _COMMAND_OBSERVATION_FIELDS | {
    "cwd_identity_before",
    "cwd_identity_after",
}
_IDENTITY_FIELDS = {"device", "inode", "mode", "uid", "gid", "link_count"}
_DESCRIPTOR_IDENTITY_FIELDS = _IDENTITY_FIELDS | {
    "size",
    "mtime_ns",
    "ctime_ns",
}


def _exact_mapping(
    value: object, fields: set[str], label: str
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ExecutionError(label + " fields changed")
    return value


def _nonnegative_integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ExecutionError(label + " must be a nonnegative integer")
    return value


def _validate_identity_value(
    value: object, *, descriptor: bool, label: str
) -> Mapping[str, object]:
    fields = _DESCRIPTOR_IDENTITY_FIELDS if descriptor else _IDENTITY_FIELDS
    identity = _exact_mapping(value, fields, label)
    for field in fields:
        _nonnegative_integer(identity[field], label + " " + field)
    return identity


def _validate_descriptor_observation(
    value: object,
    *,
    role: str,
    path: str,
    relative_path: Optional[str],
    sha256: str,
    size: Optional[int] = None,
) -> Mapping[str, object]:
    observation = _exact_mapping(
        value,
        {"schema", "role", "path", "relative_path", "before", "after", "sha256"},
        "descriptor observation",
    )
    if (
        observation["schema"] != "hsai-p01b-descriptor-observation-v1"
        or observation["role"] != role
        or observation["path"] != path
        or observation["relative_path"] != relative_path
        or observation["sha256"] != sha256
    ):
        raise ExecutionError("descriptor observation binding drifted")
    _require_hex64(str(observation["sha256"]), "descriptor sha256")
    before = _validate_identity_value(
        observation["before"], descriptor=True, label="descriptor before"
    )
    after = _validate_identity_value(
        observation["after"], descriptor=True, label="descriptor after"
    )
    if before != after or before["link_count"] != 1:
        raise ExecutionError("descriptor identity is not stable single-link data")
    if size is not None and before["size"] != size:
        raise ExecutionError("descriptor byte count drifted")
    return observation


def _validate_complete_command_observation(
    value: object,
    *,
    role: str,
    argv: Sequence[str],
    environment: Mapping[str, str],
    cwd: str,
    executable_path: str,
    executable_sha256: str,
    timeout_ns: int,
    stdout_cap: int,
    stderr_cap: int,
    cwd_identity: Optional[Mapping[str, object]] = None,
) -> Tuple[Mapping[str, object], bytes, bytes]:
    expected_fields = (
        _GATE_OBSERVATION_FIELDS
        if cwd_identity is not None
        else _COMMAND_OBSERVATION_FIELDS
    )
    observation = _exact_mapping(value, expected_fields, role + " observation")
    if (
        observation["role"] != role
        or observation["argv"] != list(argv)
        or observation["environment"] != dict(environment)
        or observation["cwd"] != cwd
        or observation["stdin_policy"] != "closed"
        or observation["executable_path"] != executable_path
        or observation["executable_sha256"] != executable_sha256
        or observation["timeout_ns"] != timeout_ns
        or observation["stdout_cap_bytes"] != stdout_cap
        or observation["stderr_cap_bytes"] != stderr_cap
        or observation["outcome"] != "completed"
        or observation["exit_code"] != 0
        or observation["signal"] is not None
    ):
        raise ExecutionError(role + " observation binding/outcome drifted")
    _require_hex64(str(observation["executable_sha256"]), role + " executable")
    started = _nonnegative_integer(
        observation["started_monotonic_ns"], role + " start"
    )
    ended = _nonnegative_integer(observation["ended_monotonic_ns"], role + " end")
    if not started < ended or ended - started > timeout_ns:
        raise ExecutionError(role + " observation timing drifted")
    stdout = _decode_observation_stream(observation, "stdout")
    stderr = _decode_observation_stream(observation, "stderr")
    if len(stdout) > stdout_cap or len(stderr) > stderr_cap:
        raise ExecutionError(role + " observation exceeded its retained cap")
    if cwd_identity is not None:
        expected_identity = _validate_identity_value(
            cwd_identity, descriptor=False, label="gate cwd identity"
        )
        before = _validate_identity_value(
            observation["cwd_identity_before"],
            descriptor=False,
            label="gate cwd before",
        )
        after = _validate_identity_value(
            observation["cwd_identity_after"],
            descriptor=False,
            label="gate cwd after",
        )
        if before != expected_identity or after != expected_identity:
            raise ExecutionError(role + " cwd identity drifted")
    return observation, stdout, stderr


def _expected_gate_inventory_paths() -> Tuple[Tuple[str, ...], set[str]]:
    directories = {"."}
    for source in SOURCE_PATHS:
        parts = source.split("/")[:-1]
        for count in range(1, len(parts) + 1):
            directories.add("/".join(parts[:count]))
    paths = sorted(
        directories | set(SOURCE_PATHS),
        key=lambda item: (item != ".", item.encode("ascii")),
    )
    return tuple(paths), directories


def _validate_gate_inventory(
    value: object, root_identity: Mapping[str, object]
) -> Dict[str, Mapping[str, object]]:
    if not isinstance(value, list):
        raise ExecutionError("gate inventory is not an array")
    expected_paths, directories = _expected_gate_inventory_paths()
    if [item.get("path") if isinstance(item, Mapping) else None for item in value] != list(
        expected_paths
    ):
        raise ExecutionError("gate inventory path order/census drifted")
    by_path: Dict[str, Mapping[str, object]] = {}
    inode_pairs: List[Tuple[int, int]] = []
    fields = {
        "path",
        "type",
        "device",
        "inode",
        "mode",
        "uid",
        "gid",
        "link_count",
        "bytes",
        "sha256",
    }
    for raw in value:
        row = _exact_mapping(raw, fields, "gate inventory row")
        path = row["path"]
        if not isinstance(path, str):
            raise ExecutionError("gate inventory path is not text")
        for field in ("device", "inode", "mode", "uid", "gid", "link_count"):
            _nonnegative_integer(row[field], "gate inventory " + field)
        if path in directories:
            if (
                row["type"] != "directory"
                or row["mode"] != 0o555
                or row["bytes"] is not None
                or row["sha256"] is not None
            ):
                raise ExecutionError("gate inventory directory drifted")
        else:
            if (
                row["type"] != "regular"
                or row["mode"] != 0o444
                or row["link_count"] != 1
            ):
                raise ExecutionError("gate inventory regular file drifted")
            _nonnegative_integer(row["bytes"], "gate inventory bytes")
            _require_hex64(str(row["sha256"]), "gate inventory sha256")
            inode_pairs.append((int(row["device"]), int(row["inode"])))
        by_path[path] = row
    if len(inode_pairs) != len(set(inode_pairs)):
        raise ExecutionError("gate inventory regular inodes are not unique")
    root = by_path["."]
    if {field: root[field] for field in _IDENTITY_FIELDS} != dict(root_identity):
        raise ExecutionError("gate inventory root identity drifted")
    return by_path


def _validate_a3l6_gate_source_manifest(
    source_manifest: Mapping[str, object],
) -> Tuple[Dict[str, bytes], Dict[str, Tuple[str, ...]]]:
    manifest = _exact_mapping(
        source_manifest, _SOURCE_MANIFEST_FIELDS, "gate source manifest"
    )
    if manifest["schema"] != "hsai-p01b-a3l6-gate-source-manifest-v1":
        raise ExecutionError("gate source manifest schema drifted")
    for field in ("implementation_commit", "implementation_tree", "audit_commit"):
        _require_git(str(manifest[field]), field)
    materialized_root = manifest["materialized_root"]
    scratch = manifest["gate_temp_root"]
    profile_path = manifest["sandbox_profile_path"]
    repository_cwd = manifest["repository_cwd"]
    git_path = manifest["git_path"]
    if not all(
        isinstance(item, str)
        for item in (materialized_root, scratch, profile_path, repository_cwd, git_path)
    ):
        raise ExecutionError("gate source path binding is not text")
    for field, path in (
        ("materialized_root", materialized_root),
        ("gate_temp_root", scratch),
        ("sandbox_profile_path", profile_path),
        ("repository_cwd", repository_cwd),
        ("git_path", git_path),
    ):
        _require_absolute(path, field)
    parent = os.path.dirname(materialized_root)
    if (
        re.fullmatch(r"/private/tmp/hsai-p01b-gate-[0-9a-f]{32}", parent) is None
        or materialized_root != parent + "/source"
        or scratch != parent + "/scratch"
        or profile_path != parent + "/gate.sb"
        or git_path != "/usr/bin/git"
    ):
        raise ExecutionError("gate source frozen path grammar drifted")
    environment = manifest["environment"]
    if environment != gate_environment(scratch):
        raise ExecutionError("gate source environment drifted")
    _require_hex64(str(manifest["git_sha256"]), "gate Git sha256")
    root_identity = _validate_identity_value(
        manifest["materialized_root_identity"],
        descriptor=False,
        label="materialized root identity",
    )
    if root_identity["mode"] != 0o555:
        raise ExecutionError("materialized root is not mode 0555")
    try:
        profile_raw = base64.b64decode(
            str(manifest["sandbox_profile_base64"]).encode("ascii"), validate=True
        )
    except (UnicodeEncodeError, ValueError) as error:
        raise ExecutionError("gate sandbox profile base64 is invalid") from error
    profile_sha256 = sha256_bytes(profile_raw)
    if (
        manifest["sandbox_profile_sha256"] != profile_sha256
        or profile_raw != render_gate_sandbox_profile(materialized_root, scratch)
    ):
        raise ExecutionError("gate sandbox profile bytes drifted")
    _validate_descriptor_observation(
        manifest["sandbox_exec_descriptor_observation"],
        role="gate-sandbox-exec",
        path=SANDBOX_EXEC_PATH,
        relative_path=None,
        sha256=SANDBOX_EXEC_SHA256,
    )
    _validate_descriptor_observation(
        manifest["sandbox_profile_descriptor_observation"],
        role="gate-sandbox-profile",
        path=profile_path,
        relative_path=None,
        sha256=profile_sha256,
        size=len(profile_raw),
    )
    before = manifest["materialized_inventory_before"]
    after = manifest["materialized_inventory_after"]
    if before != after:
        raise ExecutionError("gate inventories differ across execution")
    before_raw = canonical_json_bytes(before)
    if (
        manifest["materialized_inventory_before_sha256"] != sha256_bytes(before_raw)
        or manifest["materialized_inventory_after_sha256"]
        != sha256_bytes(canonical_json_bytes(after))
    ):
        raise ExecutionError("gate inventory digest drifted")
    inventory = _validate_gate_inventory(before, root_identity)
    pre_end = _nonnegative_integer(
        manifest["pre_gate_capture_ended_monotonic_ns"], "pre-gate capture end"
    )
    post_start = _nonnegative_integer(
        manifest["post_gate_capture_started_monotonic_ns"], "post-gate capture start"
    )
    if pre_end > post_start:
        raise ExecutionError("gate source capture bracket is reversed")
    git_sha256 = str(manifest["git_sha256"])

    def source_command(
        field: str, role: str, argv: Sequence[str], stdout_cap: int
    ) -> Tuple[Mapping[str, object], bytes]:
        observation, stdout, stderr = _validate_complete_command_observation(
            manifest[field],
            role=role,
            argv=argv,
            environment=environment,  # type: ignore[arg-type]
            cwd=repository_cwd,
            executable_path=git_path,
            executable_sha256=git_sha256,
            timeout_ns=60_000_000_000,
            stdout_cap=stdout_cap,
            stderr_cap=16_384,
        )
        if stderr != b"":
            raise ExecutionError(role + " retained nonempty stderr")
        return observation, stdout

    head, head_raw = source_command(
        "head_observation", "gate-head", (git_path, "rev-parse", "HEAD"), 4_096
    )
    tree, tree_raw = source_command(
        "tree_observation",
        "gate-tree",
        (git_path, "rev-parse", str(manifest["implementation_commit"]) + "^{tree}"),
        4_096,
    )
    status_before, status_before_raw = source_command(
        "status_before_observation",
        "gate-status-before",
        (git_path, "status", "--porcelain=v2", "-z", "--untracked-files=all"),
        1_048_576,
    )
    status_after, status_after_raw = source_command(
        "status_after_observation",
        "gate-status-after",
        (git_path, "status", "--porcelain=v2", "-z", "--untracked-files=all"),
        1_048_576,
    )
    if (
        head_raw != (str(manifest["audit_commit"]) + "\n").encode("ascii")
        or tree_raw
        != (str(manifest["implementation_tree"]) + "\n").encode("ascii")
        or status_before_raw != status_after_raw
    ):
        raise ExecutionError("gate Git HEAD/tree/status binding drifted")
    for observation in (head, tree, status_before):
        if int(observation["ended_monotonic_ns"]) > pre_end:
            raise ExecutionError("pre-gate Git capture ended too late")
    if int(status_after["started_monotonic_ns"]) < post_start:
        raise ExecutionError("post-gate Git capture started too early")
    _validate_gate_status_scope(status_before_raw, Path(repository_cwd))
    blobs = manifest["ordered_blob_observations"]
    if not isinstance(blobs, list) or len(blobs) != len(SOURCE_PATHS):
        raise ExecutionError("gate Git blob observation census drifted")
    source_bytes: Dict[str, bytes] = {}
    for ordinal, (path, raw_observation) in enumerate(zip(SOURCE_PATHS, blobs)):
        observation, stdout, stderr = _validate_complete_command_observation(
            raw_observation,
            role="gate-blob-%03d" % ordinal,
            argv=(
                git_path,
                "cat-file",
                "blob",
                str(manifest["implementation_commit"]) + ":" + path,
            ),
            environment=environment,  # type: ignore[arg-type]
            cwd=repository_cwd,
            executable_path=git_path,
            executable_sha256=git_sha256,
            timeout_ns=60_000_000_000,
            stdout_cap=16_777_216,
            stderr_cap=16_384,
        )
        if stderr != b"" or int(observation["ended_monotonic_ns"]) > pre_end:
            raise ExecutionError("gate Git blob observation drifted")
        source_bytes[path] = stdout
    rows = manifest["ordered_sources"]
    if not isinstance(rows, list) or len(rows) != len(SOURCE_PATHS):
        raise ExecutionError("gate source row census drifted")
    source_fields = {
        "path",
        "git_object_expression",
        "git_blob_oid",
        "bytes",
        "sha256",
        "pre_gate_started_monotonic_ns",
        "pre_gate_ended_monotonic_ns",
        "pre_gate_descriptor_observation",
        "post_gate_started_monotonic_ns",
        "post_gate_ended_monotonic_ns",
        "post_gate_descriptor_observation",
    }
    for path, raw_row in zip(SOURCE_PATHS, rows):
        row = _exact_mapping(raw_row, source_fields, "gate source row")
        raw = source_bytes[path]
        digest = sha256_bytes(raw)
        if (
            row["path"] != path
            or row["git_object_expression"]
            != str(manifest["implementation_commit"]) + ":" + path
            or row["git_blob_oid"] != _git_blob_oid(raw)
            or row["bytes"] != len(raw)
            or row["sha256"] != digest
        ):
            raise ExecutionError("gate source row Git/byte binding drifted")
        pre_started = _nonnegative_integer(
            row["pre_gate_started_monotonic_ns"], "source pre start"
        )
        pre_ended = _nonnegative_integer(
            row["pre_gate_ended_monotonic_ns"], "source pre end"
        )
        post_started = _nonnegative_integer(
            row["post_gate_started_monotonic_ns"], "source post start"
        )
        post_ended = _nonnegative_integer(
            row["post_gate_ended_monotonic_ns"], "source post end"
        )
        if not (
            pre_started < pre_ended <= pre_end <= post_start <= post_started < post_ended
        ):
            raise ExecutionError("gate source descriptor timing drifted")
        absolute = materialized_root + "/" + path
        pre_descriptor = _validate_descriptor_observation(
            row["pre_gate_descriptor_observation"],
            role="gate-source-pre",
            path=absolute,
            relative_path=path,
            sha256=digest,
            size=len(raw),
        )
        post_descriptor = _validate_descriptor_observation(
            row["post_gate_descriptor_observation"],
            role="gate-source-post",
            path=absolute,
            relative_path=path,
            sha256=digest,
            size=len(raw),
        )
        if not _descriptor_observations_match(pre_descriptor, post_descriptor):
            raise ExecutionError("gate source descriptor facts drifted")
        inventory_row = inventory[path]
        identity = pre_descriptor["before"]
        assert isinstance(identity, Mapping)
        projection = {
            "mode": identity["mode"],
            "device": identity["device"],
            "inode": identity["inode"],
            "uid": identity["uid"],
            "gid": identity["gid"],
            "link_count": identity["link_count"],
            "bytes": identity["size"],
            "sha256": pre_descriptor["sha256"],
        }
        if any(inventory_row[field] != value for field, value in projection.items()):
            raise ExecutionError("gate inventory/descriptor projection drifted")
    focused_by_path = {
        path: tuple(_focused_ids_from_source(path, source_bytes[path]))
        for path in SOURCE_PATHS[-2:]
    }
    combined = tuple(sorted(focused_by_path[SOURCE_PATHS[-2]] + focused_by_path[SOURCE_PATHS[-1]]))
    if combined != census_focused_test_ids(source_bytes):
        raise ExecutionError("gate focused source census drifted")
    return source_bytes, focused_by_path


def _validate_a3l6_gate_plan(
    plan: Mapping[str, object],
    source_manifest: Mapping[str, object],
    focused_by_path: Mapping[str, Tuple[str, ...]],
) -> None:
    value = _exact_mapping(plan, _GATE_PLAN_FIELDS, "gate plan")
    if value["schema"] != "hsai-p01b-a3l6-gate-plan-v1":
        raise ExecutionError("gate plan schema drifted")
    root = str(source_manifest["materialized_root"])
    scratch = str(source_manifest["gate_temp_root"])
    profile = str(source_manifest["sandbox_profile_path"])
    expected_commands = _gate_command_rows(root, scratch, profile)
    focused = tuple(
        sorted(focused_by_path[SOURCE_PATHS[-2]] + focused_by_path[SOURCE_PATHS[-1]])
    )
    if (
        value["implementation_commit"] != source_manifest["implementation_commit"]
        or value["implementation_tree"] != source_manifest["implementation_tree"]
        or value["audit_commit"] != source_manifest["audit_commit"]
        or value["python_path"] != "/usr/bin/python3"
        or value["python_sha256"] != NATIVE_PYTHON_SHA256
        or value["python_version"] != "3.9.6"
        or value["environment"] != gate_environment(scratch)
        or value["gate_source_root"] != root
        or value["gate_source_root_identity"]
        != source_manifest["materialized_root_identity"]
        or value["gate_temp_root"] != scratch
        or value["sandbox_exec_path"] != SANDBOX_EXEC_PATH
        or value["sandbox_exec_sha256"] != SANDBOX_EXEC_SHA256
        or value["sandbox_profile_path"] != profile
        or value["sandbox_profile_sha256"]
        != source_manifest["sandbox_profile_sha256"]
        or value["gate_source_manifest_sha256"]
        != domain_sha256("hsai:p01b-a3l6-gate-source-manifest:v1", source_manifest)
        or value["cwd"] != root
        or value["commands"] != expected_commands
        or value["reviewed_paths"] != list(REVIEWED_PATHS)
        or value["expected_focused_test_ids"] != list(focused)
        or value["expected_focused_test_count"] != 65
        or value["expected_discovery_test_count"] != 172
    ):
        raise ExecutionError("gate plan immutable reconstruction drifted")


def _validate_a3l6_gate_observations(
    plan: Mapping[str, object],
    source_manifest: Mapping[str, object],
    observations: Sequence[Mapping[str, object]],
    focused_by_path: Mapping[str, Tuple[str, ...]],
) -> None:
    commands = plan["commands"]
    if not isinstance(commands, list) or len(observations) != 3:
        raise ExecutionError("gate observation census drifted")
    pre_end = int(source_manifest["pre_gate_capture_ended_monotonic_ns"])
    post_start = int(source_manifest["post_gate_capture_started_monotonic_ns"])
    previous_end: Optional[int] = None
    focused_paths = {
        "evidence-focused": SOURCE_PATHS[-1],
        "execution-focused": SOURCE_PATHS[-2],
    }
    for row, raw_observation in zip(commands, observations):
        if not isinstance(row, Mapping):
            raise ExecutionError("gate command row is not an object")
        observation, stdout, stderr = _validate_complete_command_observation(
            raw_observation,
            role=str(row["role"]),
            argv=row["argv"],  # type: ignore[arg-type]
            environment=row["environment"],  # type: ignore[arg-type]
            cwd=str(row["cwd"]),
            executable_path=SANDBOX_EXEC_PATH,
            executable_sha256=SANDBOX_EXEC_SHA256,
            timeout_ns=int(row["timeout_ns"]),
            stdout_cap=int(row["stdout_cap_bytes"]),
            stderr_cap=int(row["stderr_cap_bytes"]),
            cwd_identity=plan["gate_source_root_identity"],  # type: ignore[arg-type]
        )
        started = int(observation["started_monotonic_ns"])
        ended = int(observation["ended_monotonic_ns"])
        if (
            stdout != b""
            or not pre_end <= started < ended <= post_start
            or (previous_end is not None and previous_end > started)
        ):
            raise ExecutionError("gate observation bracket/order drifted")
        role = str(row["role"])
        if role in focused_paths:
            expected_ids: Optional[Sequence[str]] = focused_by_path[
                focused_paths[role]
            ]
            expected_count = 32 if role == "evidence-focused" else 33
        else:
            expected_ids = None
            expected_count = 172
        parse_unittest_transcript(
            stderr, expected_count=expected_count, expected_ids=expected_ids
        )
        previous_end = ended


def _validate_a3l6_python_observation(
    observation: Mapping[str, object], run: A3L6GateRun
) -> None:
    _, stdout, stderr = _validate_complete_command_observation(
        observation,
        role="gate-python-version",
        argv=("/usr/bin/python3", "--version"),
        environment=run.gate_plan["environment"],  # type: ignore[arg-type]
        cwd=str(run.gate_plan["cwd"]),
        executable_path="/usr/bin/python3",
        executable_sha256=NATIVE_PYTHON_SHA256,
        timeout_ns=60_000_000_000,
        stdout_cap=16_384,
        stderr_cap=16_384,
    )
    if stdout != b"Python 3.9.6\n" or stderr != b"":
        raise ExecutionError("gate Python version transcript drifted")


def validate_a3l6_gate_plan_execution(
    plan: Mapping[str, object],
    source_manifest: Mapping[str, object],
    observations: Sequence[Mapping[str, object]],
) -> None:
    source_bytes, focused_by_path = _validate_a3l6_gate_source_manifest(
        source_manifest
    )
    del source_bytes
    _validate_a3l6_gate_plan(plan, source_manifest, focused_by_path)
    _validate_a3l6_gate_observations(
        plan, source_manifest, observations, focused_by_path
    )


def _review_findings(value: object) -> List[str]:
    if not isinstance(value, list):
        raise ExecutionError("gate review findings must be an array")
    for item in value:
        if (
            not isinstance(item, str)
            or not 1 <= len(item.encode("ascii")) <= 512
            or any(ord(char) < 32 or ord(char) > 126 for char in item)
        ):
            raise ExecutionError("gate review finding is invalid")
    if value != sorted(set(value)):
        raise ExecutionError("gate review findings are not sorted unique")
    return list(value)


def _reviewed_file_projection(source_manifest: Mapping[str, object]) -> List[Dict[str, object]]:
    rows = source_manifest.get("ordered_sources")
    if not isinstance(rows, list) or len(rows) != len(SOURCE_PATHS):
        raise ExecutionError("gate source rows are absent")
    by_path = {row.get("path"): row for row in rows if isinstance(row, dict)}
    if set(by_path) != set(SOURCE_PATHS):
        raise ExecutionError("gate source rows changed")
    return [
        {"path": path, "sha256": by_path[path]["sha256"]}
        for path in REVIEWED_PATHS
    ]


def build_a3l6_code_review_record(
    run: A3L6GateRun,
    *,
    role: str,
    reviewer_id: str,
    findings: Sequence[str],
) -> Dict[str, object]:
    if role not in REVIEW_ROLE_ORDER:
        raise ExecutionError("gate review role changed")
    _require_identifier(reviewer_id, "gate reviewer id")
    checked_findings = _review_findings(list(findings))
    plan_sha256 = domain_sha256("hsai:p01b-a3l6-gate-plan:v1", run.gate_plan)
    source_sha256 = domain_sha256(
        "hsai:p01b-a3l6-gate-source-manifest:v1", run.gate_source_manifest
    )
    observation_sha256 = sha256_bytes(
        canonical_json_bytes(list(run.ordered_gate_observations))
    )
    return {
        "schema": "hsai-p01b-a3l6-code-review-v1",
        "role": role,
        "reviewer_id": reviewer_id,
        "implementation_commit": run.gate_plan["implementation_commit"],
        "implementation_tree": run.gate_plan["implementation_tree"],
        "ordered_file_sha256": _reviewed_file_projection(run.gate_source_manifest),
        "gate_plan_sha256": plan_sha256,
        "gate_source_manifest_sha256": source_sha256,
        "gate_observation_sha256": observation_sha256,
        "findings": checked_findings,
        "result": "accept" if not checked_findings else "reject",
    }


def validate_a3l6_code_review_record(
    value: Mapping[str, object], run: A3L6GateRun, expected_role: str
) -> None:
    expected_fields = {
        "schema",
        "role",
        "reviewer_id",
        "implementation_commit",
        "implementation_tree",
        "ordered_file_sha256",
        "gate_plan_sha256",
        "gate_source_manifest_sha256",
        "gate_observation_sha256",
        "findings",
        "result",
    }
    if set(value) != expected_fields or value.get("schema") != "hsai-p01b-a3l6-code-review-v1":
        raise ExecutionError("gate review fields/schema changed")
    if value.get("role") != expected_role:
        raise ExecutionError("gate review role order changed")
    _require_identifier(value.get("reviewer_id"), "gate reviewer id")  # type: ignore[arg-type]
    findings = _review_findings(value.get("findings"))
    if value.get("result") != ("accept" if not findings else "reject"):
        raise ExecutionError("gate review result changed")
    if (
        value.get("implementation_commit") != run.gate_plan["implementation_commit"]
        or value.get("implementation_tree") != run.gate_plan["implementation_tree"]
        or value.get("ordered_file_sha256") != _reviewed_file_projection(run.gate_source_manifest)
        or value.get("gate_plan_sha256")
        != domain_sha256("hsai:p01b-a3l6-gate-plan:v1", run.gate_plan)
        or value.get("gate_source_manifest_sha256")
        != domain_sha256(
            "hsai:p01b-a3l6-gate-source-manifest:v1", run.gate_source_manifest
        )
        or value.get("gate_observation_sha256")
        != sha256_bytes(canonical_json_bytes(list(run.ordered_gate_observations)))
    ):
        raise ExecutionError("gate review immutable binding drifted")


def _a3l6_gate_bundle_value(
    run: A3L6GateRun, ordered_reviews: Sequence[Mapping[str, object]]
) -> Dict[str, object]:
    result = (
        "accept"
        if all(review.get("result") == "accept" for review in ordered_reviews)
        else "reject"
    )
    return {
        "schema": "hsai-p01b-a3l6-gate-bundle-v1",
        "gate_plan": dict(run.gate_plan),
        "gate_source_manifest": dict(run.gate_source_manifest),
        "implementation_commit": run.gate_plan["implementation_commit"],
        "implementation_tree": run.gate_plan["implementation_tree"],
        "python_path": "/usr/bin/python3",
        "python_sha256": NATIVE_PYTHON_SHA256,
        "python_version": "3.9.6",
        "python_version_observation": dict(run.python_version_observation),
        "ordered_gate_observations": [
            dict(item) for item in run.ordered_gate_observations
        ],
        "focused_test_ids": list(run.focused_test_ids),
        "focused_test_count": run.focused_test_count,
        "discovery_test_count": run.discovery_test_count,
        "ordered_review_records": [dict(item) for item in ordered_reviews],
        "result": result,
    }


def _validate_a3l6_expected_bindings(
    value: Mapping[str, object], run: A3L6GateRun, bundle: Mapping[str, object]
) -> None:
    evidence = _load_evidence_module()
    try:
        bindings = evidence.validate_expected_bindings(value)
    except Exception as error:
        raise ExecutionError("A3L6 expected bindings were rejected") from error
    plan_sha256 = domain_sha256("hsai:p01b-a3l6-gate-plan:v1", run.gate_plan)
    source_sha256 = domain_sha256(
        "hsai:p01b-a3l6-gate-source-manifest:v1", run.gate_source_manifest
    )
    bundle_sha256 = domain_sha256(
        "hsai:p01b-a3l6-gate-bundle:v1", bundle
    )
    focused_sha256 = sha256_bytes(
        canonical_json_bytes(list(run.focused_test_ids))
    )
    rows_value = run.gate_source_manifest.get("ordered_sources")
    if not isinstance(rows_value, list):
        raise ExecutionError("A3L6 source rows are absent from expected binding check")
    rows = {
        row.get("path"): row for row in rows_value if isinstance(row, Mapping)
    }
    if set(rows) != set(SOURCE_PATHS):
        raise ExecutionError("A3L6 source rows drifted during expected binding check")
    expected = {
        "implementation_commit": run.gate_plan["implementation_commit"],
        "implementation_tree": run.gate_plan["implementation_tree"],
        "a3l6_audit_commit": run.gate_plan["audit_commit"],
        "a3l6_gate_plan_sha256": plan_sha256,
        "a3l6_gate_source_manifest_sha256": source_sha256,
        "a3l6_gate_bundle_sha256": bundle_sha256,
        "expected_focused_test_ids_sha256": focused_sha256,
        "expected_focused_test_count": 65,
        "discovery_expected_test_count": 172,
        "native_python_path": run.gate_plan["python_path"],
        "native_python_sha256": run.gate_plan["python_sha256"],
        "native_python_version": run.gate_plan["python_version"],
        "sandbox_exec_path": run.gate_plan["sandbox_exec_path"],
        "sandbox_exec_sha256": run.gate_plan["sandbox_exec_sha256"],
        "gate_sandbox_profile_sha256": run.gate_plan["sandbox_profile_sha256"],
        "git_path": run.gate_source_manifest["git_path"],
        "git_sha256": run.gate_source_manifest["git_sha256"],
        "validator_sha256": rows[SOURCE_PATHS[-4]]["sha256"],
        "collector_sha256": rows[SOURCE_PATHS[-3]]["sha256"],
    }
    for field, expected_value in expected.items():
        if bindings[field] != expected_value:
            raise ExecutionError("A3L6 expected binding drifted: " + field)


def assemble_a3l6_gate_bundle(
    run: A3L6GateRun,
    ordered_reviews: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    validate_a3l6_gate_plan_execution(
        run.gate_plan, run.gate_source_manifest, run.ordered_gate_observations
    )
    _validate_a3l6_python_observation(run.python_version_observation, run)
    if (
        tuple(run.focused_test_ids)
        != tuple(run.gate_plan["expected_focused_test_ids"])
        or run.focused_test_count != 65
        or run.discovery_test_count != 172
    ):
        raise ExecutionError("gate run test census drifted")
    if len(ordered_reviews) != 2:
        raise ExecutionError("gate bundle requires exactly two reviews")
    for review, role in zip(ordered_reviews, REVIEW_ROLE_ORDER):
        validate_a3l6_code_review_record(review, run, role)
    if ordered_reviews[0]["reviewer_id"] == ordered_reviews[1]["reviewer_id"]:
        raise ExecutionError("gate reviewers are not distinct")
    return _a3l6_gate_bundle_value(run, ordered_reviews)


def validate_a3l6_gate_bundle(
    value: Mapping[str, object],
    expected_bindings: Optional[Mapping[str, object]] = None,
) -> Mapping[str, object]:
    fields = {
        "schema",
        "gate_plan",
        "gate_source_manifest",
        "implementation_commit",
        "implementation_tree",
        "python_path",
        "python_sha256",
        "python_version",
        "python_version_observation",
        "ordered_gate_observations",
        "focused_test_ids",
        "focused_test_count",
        "discovery_test_count",
        "ordered_review_records",
        "result",
    }
    bundle = _exact_mapping(value, fields, "gate bundle")
    if bundle["schema"] != "hsai-p01b-a3l6-gate-bundle-v1":
        raise ExecutionError("gate bundle schema drifted")
    plan = bundle["gate_plan"]
    source = bundle["gate_source_manifest"]
    python_observation = bundle["python_version_observation"]
    observations = bundle["ordered_gate_observations"]
    focused_ids = bundle["focused_test_ids"]
    reviews = bundle["ordered_review_records"]
    if (
        not isinstance(plan, Mapping)
        or not isinstance(source, Mapping)
        or not isinstance(python_observation, Mapping)
        or not isinstance(observations, list)
        or any(not isinstance(item, Mapping) for item in observations)
        or not isinstance(focused_ids, list)
        or any(not isinstance(item, str) for item in focused_ids)
        or not isinstance(reviews, list)
        or any(not isinstance(item, Mapping) for item in reviews)
        or type(bundle["focused_test_count"]) is not int
        or type(bundle["discovery_test_count"]) is not int
    ):
        raise ExecutionError("gate bundle nested value type drifted")
    run = A3L6GateRun(
        plan,
        source,
        python_observation,
        tuple(observations),
        tuple(focused_ids),
        int(bundle["focused_test_count"]),
        int(bundle["discovery_test_count"]),
    )
    validate_a3l6_gate_plan_execution(plan, source, observations)
    _validate_a3l6_python_observation(python_observation, run)
    if (
        bundle["implementation_commit"] != plan["implementation_commit"]
        or bundle["implementation_tree"] != plan["implementation_tree"]
        or bundle["python_path"] != plan["python_path"]
        or bundle["python_sha256"] != plan["python_sha256"]
        or bundle["python_version"] != plan["python_version"]
        or tuple(focused_ids) != tuple(plan["expected_focused_test_ids"])
        or bundle["focused_test_count"] != 65
        or bundle["discovery_test_count"] != 172
        or len(reviews) != 2
    ):
        raise ExecutionError("gate bundle immutable projection drifted")
    for review, role in zip(reviews, REVIEW_ROLE_ORDER):
        validate_a3l6_code_review_record(review, run, role)
    if reviews[0]["reviewer_id"] == reviews[1]["reviewer_id"]:
        raise ExecutionError("gate bundle reviewers are not distinct")
    expected_bundle = _a3l6_gate_bundle_value(run, reviews)
    if canonical_json_bytes(bundle) != canonical_json_bytes(expected_bundle):
        raise ExecutionError("gate bundle reconstruction drifted")
    if expected_bundle["result"] != "accept":
        raise ExecutionError("gate bundle was not independently accepted")
    if expected_bindings is not None:
        _validate_a3l6_expected_bindings(expected_bindings, run, bundle)
    return bundle


CONTAINER_ENV = (
    "HOME=/nonexistent",
    "LANG=C.UTF-8",
    "LC_ALL=C.UTF-8",
    "PATH=/usr/local/bin:/usr/bin:/bin",
    "PYTHONHASHSEED=0",
    "PYTHONDONTWRITEBYTECODE=1",
    "PYTHONNOUSERSITE=1",
    "TMPDIR=/work",
    "TZ=UTC",
)


@dataclass(frozen=True)
class CommandSpec:
    ordinal: int
    role: str
    argv: Tuple[str, ...]
    environment: Mapping[str, str]
    cwd: str
    stdin_policy: str
    stdout_cap: int
    stderr_cap: int
    timeout_ns: int
    activation: str
    expected_outcomes: Tuple[str, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.ordinal, bool)
            or not isinstance(self.ordinal, int)
            or self.ordinal < 0
        ):
            raise ExecutionError("command ordinal must be a nonnegative integer")
        _require_identifier(self.role, "role")
        object.__setattr__(self, "argv", _validate_argv(self.argv))
        object.__setattr__(self, "environment", _validate_environment(self.environment))
        _require_absolute(self.cwd, "cwd")
        if self.stdin_policy != "closed-null":
            raise ExecutionError("stdin policy must be closed-null")
        for field, value in (
            ("stdout_cap", self.stdout_cap),
            ("stderr_cap", self.stderr_cap),
            ("timeout_ns", self.timeout_ns),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ExecutionError("%s must be positive" % field)
        if self.activation not in {
            "always",
            "after_index",
            "after_platform",
            "after_create",
            "after_prestart",
            "after_readiness",
            "after_export",
            "after_release",
            "on_breach",
            "after_terminal",
            "recovery_only",
            "never",
        }:
            raise ExecutionError("unknown command activation")
        if not self.expected_outcomes or any(
            not isinstance(item, str) or not item for item in self.expected_outcomes
        ):
            raise ExecutionError("expected outcomes must be nonempty strings")

    def to_dict(self) -> Dict[str, object]:
        return {
            "activation": self.activation,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "environment": dict(self.environment),
            "expected_outcomes": list(self.expected_outcomes),
            "ordinal": self.ordinal,
            "role": self.role,
            "stderr_cap": self.stderr_cap,
            "stdin_policy": self.stdin_policy,
            "stdout_cap": self.stdout_cap,
            "timeout_ns": self.timeout_ns,
        }


def _command(
    ordinal: int,
    role: str,
    argv: Sequence[str],
    environment: Mapping[str, str],
    *,
    cap: int = STREAM_CAP,
    timeout_ns: int = ATTEMPT_TIMEOUT_NS,
    activation: str = "always",
    expected: Sequence[str] = ("exit_zero",),
) -> CommandSpec:
    return CommandSpec(
        ordinal=ordinal,
        role=role,
        argv=tuple(argv),
        environment=environment,
        cwd="/",
        stdin_policy="closed-null",
        stdout_cap=cap,
        stderr_cap=cap,
        timeout_ns=timeout_ns,
        activation=activation,
        expected_outcomes=tuple(expected),
    )


def _command_before_deadline(
    command: CommandSpec, deadline_ns: int, clock: Callable[[], int],
) -> CommandSpec:
    now = clock()
    remaining = deadline_ns - now
    if remaining <= 0:
        raise ExecutionError("attempt deadline expired before command launch")
    timeout_ns = min(command.timeout_ns, remaining)
    return CommandSpec(
        ordinal=command.ordinal,
        role=command.role,
        argv=command.argv,
        environment=command.environment,
        cwd=command.cwd,
        stdin_policy=command.stdin_policy,
        stdout_cap=command.stdout_cap,
        stderr_cap=command.stderr_cap,
        timeout_ns=timeout_ns,
        activation=command.activation,
        expected_outcomes=command.expected_outcomes,
    )


def docker_prefix(config_root: str, host_uri: str) -> Tuple[str, ...]:
    _require_absolute(config_root, "config_root")
    if not isinstance(host_uri, str) or not host_uri.startswith("unix:///"):
        raise ExecutionError("Docker host must be an absolute unix URI")
    if any(char in host_uri for char in "\0\n\r"):
        raise ExecutionError("Docker host contains forbidden bytes")
    return (
        DOCKER_EXE,
        "--config",
        config_root,
        "--host",
        host_uri,
        "--log-level",
        "error",
    )


def build_readiness_plan(
    *,
    predecessor_commit: str,
    user_authorization_sha256: str,
    config_root: str,
    host_uri: str,
    temporary_root: str,
) -> Dict[str, object]:
    """Build the six-command A3L7 plan; PLATFORM remains rule-derived."""
    _require_git(predecessor_commit, "predecessor_commit")
    _require_hex64(user_authorization_sha256, "user_authorization_sha256")
    environment = closed_host_environment(config_root, temporary_root)
    prefix = docker_prefix(config_root, host_uri)
    commands = (
        _command(
            0,
            "registry-index",
            (BUILDX_EXE, "imagetools", "inspect", "--raw", INDEX_REFERENCE),
            environment,
            cap=REGISTRY_CAP,
        ),
        _command(
            1,
            "registry-platform",
            (BUILDX_EXE, "imagetools", "inspect", "--raw", PLATFORM_PLACEHOLDER),
            environment,
            cap=REGISTRY_CAP,
            activation="after_index",
        ),
        _command(
            2,
            "local-platform",
            prefix + ("image", "inspect", "--format={{json .}}", PLATFORM_PLACEHOLDER),
            environment,
            cap=METADATA_CAP,
            activation="after_platform",
        ),
        _command(
            3,
            "buildx-version",
            (BUILDX_EXE, "version"),
            environment,
            cap=METADATA_CAP,
            activation="after_platform",
        ),
        _command(
            4,
            "codesign-verify",
            (CODE_SIGN_EXE, "--verify", "--strict", "--verbose=4", DOCKER_APP_PATH),
            environment,
            cap=METADATA_CAP,
            activation="after_platform",
        ),
        _command(
            5,
            "codesign-display",
            (CODE_SIGN_EXE, "--display", "--verbose=4", DOCKER_APP_PATH),
            environment,
            cap=METADATA_CAP,
            activation="after_platform",
        ),
    )
    return {
        "buildx_path": BUILDX_EXE,
        "buildx_sha256": BUILDX_SHA256,
        "codesign_path": CODE_SIGN_EXE,
        "codesign_sha256": CODE_SIGN_SHA256,
        "commands": [command.to_dict() for command in commands],
        "docker_path": DOCKER_EXE,
        "docker_sha256": DOCKER_SHA256,
        "index_reference": INDEX_REFERENCE,
        "predecessor_commit": predecessor_commit,
        "schema": READINESS_PLAN_SCHEMA,
        "selected_reference_rule": {
            "architecture": "arm64",
            "count": 1,
            "os": "linux",
            "repository": "docker.io/library/python",
            "variant": "v8",
        },
        "user_authorization_sha256": user_authorization_sha256,
    }


def resolve_readiness_plan(
    plan: Mapping[str, object], platform_reference: str
) -> Dict[str, object]:
    """Resolve only the two rule-derived PLATFORM argv slots."""
    if OCI_REFERENCE_RE.fullmatch(platform_reference) is None:
        raise ExecutionError("platform reference is not repository-qualified")
    if not platform_reference.startswith("docker.io/library/python@sha256:"):
        raise ExecutionError("platform reference changed repository")
    resolved = json.loads(canonical_json_bytes(plan))
    commands = resolved.get("commands")
    if not isinstance(commands, list) or len(commands) != 6:
        raise ExecutionError("readiness plan command count changed")
    replacements = 0
    for command in commands:
        if not isinstance(command, dict) or not isinstance(command.get("argv"), list):
            raise ExecutionError("invalid readiness command")
        argv = command["argv"]
        if any(not isinstance(item, str) for item in argv):
            raise ExecutionError("invalid readiness argv")
        replacements += sum(item == PLATFORM_PLACEHOLDER for item in argv)
        command["argv"] = [
            platform_reference if item == PLATFORM_PLACEHOLDER else item
            for item in argv
        ]
    if replacements != 2:
        raise ExecutionError("readiness plan PLATFORM cardinality changed")
    if PLATFORM_PLACEHOLDER in canonical_json_bytes(resolved).decode("ascii"):
        raise ExecutionError("unresolved PLATFORM remained")
    return resolved


def build_native_command(
    snapshot_root: str, environment: Mapping[str, str]
) -> CommandSpec:
    """Build the exact no-network native-reference command."""
    _require_absolute(snapshot_root, "snapshot_root")
    probe = os.path.join(
        snapshot_root,
        "tools/hsai-formal-preflight/p01b_container_probe.py",
    )
    return _command(
        0,
        "native-reference",
        ("/usr/bin/python3", "-B", probe, "--mode", "native-reference"),
        environment,
        cap=RESULT_CAP,
    )


def build_metadata_commands(
    prefix: Sequence[str], environment: Mapping[str, str]
) -> Tuple[CommandSpec, ...]:
    """Build the three exact A3L8 provenance commands."""
    base = tuple(prefix)
    return (
        _command(
            1,
            "docker-version",
            base + ("version", "--format={{json .}}"),
            environment,
            cap=METADATA_CAP,
        ),
        _command(
            2,
            "docker-info",
            base + ("info", "--format={{json .}}"),
            environment,
            cap=METADATA_CAP,
        ),
        _command(
            3,
            "image-config",
            base
            + (
                "image",
                "inspect",
                "--format={{json .}}",
                IMAGE_CONFIG_DIGEST,
            ),
            environment,
            cap=METADATA_CAP,
        ),
    )


def _attempt_name(campaign_id: str, attempt_id: str) -> str:
    _require_identifier(campaign_id, "campaign_id")
    _require_identifier(attempt_id, "attempt_id")
    name = "hsai-p01b-%s-%s" % (campaign_id, attempt_id)
    if len(name) > 128:
        raise ExecutionError("container name is too long")
    return name


def _create_argv(
    prefix: Tuple[str, ...],
    *,
    name: str,
    campaign_id: str,
    attempt_id: str,
    authorization_sha256: str,
    implementation_commit: str,
    source_manifest_sha256: str,
    snapshot_root: str,
    seccomp_path: str,
    platform_reference: str,
) -> Tuple[str, ...]:
    _require_absolute(snapshot_root, "snapshot_root")
    _require_absolute(seccomp_path, "seccomp_path")
    if OCI_REFERENCE_RE.fullmatch(platform_reference) is None:
        raise ExecutionError("platform reference is invalid")
    _require_hex64(source_manifest_sha256, "source_manifest_sha256")
    mode = "normal" if attempt_id == "normal" else "oom-child"
    controls = (
        "container",
        "create",
        "--pull=never",
        "--platform=linux/arm64/v8",
        "--name=" + name,
        "--hostname=hsai-p01b",
        "--runtime=runc",
        "--network=none",
        "--ipc=private",
        "--cgroupns=private",
        "--user=65532:65532",
        "--read-only",
        "--privileged=false",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--security-opt=seccomp=" + seccomp_path,
        "--memory=536870912",
        "--memory-swap=536870912",
        "--memory-swappiness=0",
        "--oom-kill-disable=false",
        "--pids-limit=16",
        "--cpu-period=100000",
        "--cpu-quota=100000",
        "--ulimit=cpu=900:900",
        "--ulimit=fsize=67108864:67108864",
        "--ulimit=nofile=32:32",
        "--ulimit=core=0:0",
        "--tmpfs=/work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700",
        "--shm-size=1048576",
        "--log-driver=none",
        "--restart=no",
        "--no-healthcheck",
        "--label=hsai.p01b.campaign=" + campaign_id,
        "--label=hsai.p01b.attempt=" + attempt_id,
        "--label=hsai.p01b.authorization=" + authorization_sha256,
        "--label=hsai.p01b.implementation=" + implementation_commit,
        "--mount=type=bind,src=%s,dst=/input,readonly,bind-propagation=rprivate"
        % snapshot_root,
        "--workdir=/input",
        "--entrypoint=/usr/bin/env",
        platform_reference,
        "-i",
    )
    workload = CONTAINER_ENV + (
        "/usr/local/bin/python3",
        "-B",
        "tools/hsai-formal-preflight/p01b_container_probe.py",
        "--mode",
        mode,
        "--input-manifest-sha256",
        source_manifest_sha256,
        "--output",
        "/work/result.json",
    )
    return prefix + controls + workload


def build_attempt_plan(
    *,
    campaign_id: str,
    attempt_id: str,
    authorization_sha256: str,
    implementation_commit: str,
    platform_reference: str,
    source_manifest_sha256: str,
    config_root: str,
    host_uri: str,
    temporary_root: str,
    snapshot_root: str,
    seccomp_path: str,
) -> Dict[str, object]:
    """Build one exact normal or oom-child lifecycle plan."""
    if attempt_id not in {"normal", "oom"}:
        raise ExecutionError("attempt_id must be normal or oom")
    _require_hex64(authorization_sha256, "authorization_sha256")
    _require_git(implementation_commit, "implementation_commit")
    _require_hex64(source_manifest_sha256, "source_manifest_sha256")
    environment = closed_host_environment(config_root, temporary_root)
    prefix = docker_prefix(config_root, host_uri)
    name = _attempt_name(campaign_id, attempt_id)
    labels = (
        "--filter=label=hsai.p01b.campaign=" + campaign_id,
        "--filter=label=hsai.p01b.attempt=" + attempt_id,
    )
    commands = (
        _command(
            0,
            "absence-name-pre",
            prefix + ("container", "inspect", name),
            environment,
            cap=METADATA_CAP,
            expected=("exact_absent",),
        ),
        _command(
            1,
            "absence-label-pre",
            prefix
            + ("container", "ls", "--all", "--no-trunc")
            + labels
            + ("--format={{.ID}}",),
            environment,
            expected=("empty",),
        ),
        _command(
            2,
            "create",
            _create_argv(
                prefix,
                name=name,
                campaign_id=campaign_id,
                attempt_id=attempt_id,
                authorization_sha256=authorization_sha256,
                implementation_commit=implementation_commit,
                source_manifest_sha256=source_manifest_sha256,
                snapshot_root=snapshot_root,
                seccomp_path=seccomp_path,
                platform_reference=platform_reference,
            ),
            environment,
            expected=("stable_cid",),
        ),
        _command(
            3,
            "inspect-prestart",
            prefix
            + ("container", "inspect", "--format=" + INSPECT_TEMPLATE, CID_PLACEHOLDER),
            environment,
            cap=METADATA_CAP,
            activation="after_create",
        ),
        _command(
            4,
            "start-attach",
            prefix + ("container", "start", "--attach", CID_PLACEHOLDER),
            environment,
            activation="after_prestart",
        ),
        _command(
            5,
            "export-running",
            prefix + ("container", "cp", CID_PLACEHOLDER + ":/work/result.json", "-"),
            environment,
            cap=TAR_CAP,
            activation="after_readiness",
        ),
        _command(
            6,
            "release",
            prefix + ("container", "kill", "--signal=USR1", CID_PLACEHOLDER),
            environment,
            activation="after_export",
        ),
        _command(
            7,
            "emergency-kill",
            prefix + ("container", "kill", "--signal=KILL", CID_PLACEHOLDER),
            environment,
            activation="on_breach",
        ),
        _command(
            8,
            "wait",
            prefix + ("container", "wait", CID_PLACEHOLDER),
            environment,
            activation="after_release",
        ),
        _command(
            9,
            "inspect-terminal",
            prefix
            + ("container", "inspect", "--format=" + INSPECT_TEMPLATE, CID_PLACEHOLDER),
            environment,
            cap=METADATA_CAP,
            activation="after_release",
        ),
        _command(
            10,
            "remove",
            prefix + ("container", "rm", CID_PLACEHOLDER),
            environment,
            activation="after_terminal",
        ),
        _command(
            11,
            "absence-cid",
            prefix + ("container", "inspect", CID_PLACEHOLDER),
            environment,
            cap=METADATA_CAP,
            activation="after_terminal",
            expected=("exact_absent",),
        ),
        _command(
            12,
            "absence-name",
            prefix + ("container", "inspect", name),
            environment,
            cap=METADATA_CAP,
            activation="after_terminal",
            expected=("exact_absent",),
        ),
        _command(
            13,
            "absence-label",
            prefix
            + ("container", "ls", "--all", "--no-trunc")
            + labels
            + ("--format={{.ID}}",),
            environment,
            activation="after_terminal",
            expected=("empty",),
        ),
        _command(
            14,
            "daemon-recheck",
            prefix + ("version", "--format={{json .}}"),
            environment,
            cap=METADATA_CAP,
            activation="after_terminal",
        ),
    )
    return {
        "attempt_id": attempt_id,
        "attempt_kind": "normal" if attempt_id == "normal" else "oom-child",
        "authorization_sha256": authorization_sha256,
        "campaign_id": campaign_id,
        "commands": [command.to_dict() for command in commands],
        "implementation_commit": implementation_commit,
        "platform_manifest_reference": platform_reference,
        "schema": ATTEMPT_PLAN_SCHEMA,
        "source_manifest_sha256": source_manifest_sha256,
    }


def resolve_cid(plan: Mapping[str, object], container_id: str) -> Dict[str, object]:
    if (
        not isinstance(container_id, str)
        or re.fullmatch(r"[0-9a-f]{64}", container_id) is None
    ):
        raise ExecutionError("container id must be 64 lowercase hexadecimal characters")
    resolved = json.loads(canonical_json_bytes(plan))
    replacements = 0
    for command in resolved.get("commands", []):
        argv = command.get("argv") if isinstance(command, dict) else None
        if not isinstance(argv, list):
            raise ExecutionError("attempt command is invalid")
        next_argv = []
        for item in argv:
            if not isinstance(item, str):
                raise ExecutionError("attempt argv is invalid")
            count = item.count(CID_PLACEHOLDER)
            replacements += count
            next_argv.append(item.replace(CID_PLACEHOLDER, container_id))
        command["argv"] = next_argv
    if replacements != 9:
        raise ExecutionError("CID placeholder cardinality changed")
    if CID_PLACEHOLDER in canonical_json_bytes(resolved).decode("ascii"):
        raise ExecutionError("unresolved CID remained")
    return resolved


def expected_container_labels(
    campaign_id: str,
    attempt_id: str,
    authorization_sha256: str,
    implementation_commit: str,
) -> Dict[str, str]:
    _require_identifier(campaign_id, "campaign_id")
    _require_identifier(attempt_id, "attempt_id")
    _require_hex64(authorization_sha256, "authorization_sha256")
    _require_git(implementation_commit, "implementation_commit")
    return {
        "hsai.p01b.attempt": attempt_id,
        "hsai.p01b.authorization": authorization_sha256,
        "hsai.p01b.campaign": campaign_id,
        "hsai.p01b.implementation": implementation_commit,
    }


def build_container_intent(
    *,
    campaign_id: str,
    attempt_id: str,
    authorization_sha256: str,
    implementation_commit: str,
    attempt_plan_sha256: str,
    created_monotonic_ns: int,
) -> Dict[str, object]:
    """Build the durable pre-create identity that authorizes exact recovery."""
    _require_hex64(attempt_plan_sha256, "attempt_plan_sha256")
    if isinstance(created_monotonic_ns, bool) or not isinstance(created_monotonic_ns, int) or created_monotonic_ns < 0:
        raise ExecutionError("intent creation time is invalid")
    return {
        "schema": "hsai-p01b-container-intent-v1",
        "campaign_id": campaign_id,
        "attempt_id": attempt_id,
        "authorization_sha256": authorization_sha256,
        "implementation_commit": implementation_commit,
        "container_name": _attempt_name(campaign_id, attempt_id),
        "expected_labels": expected_container_labels(
            campaign_id, attempt_id, authorization_sha256, implementation_commit
        ),
        "attempt_plan_sha256": attempt_plan_sha256,
        "created_monotonic_ns": created_monotonic_ns,
    }


def build_cid_binding(
    *, intent_sha256: str, container_id: str, create_observation_sha256: str,
    bound_monotonic_ns: int
) -> Dict[str, object]:
    for field, value in (
        ("intent_sha256", intent_sha256),
        ("create_observation_sha256", create_observation_sha256),
    ):
        _require_hex64(value, field)
    if re.fullmatch(r"[0-9a-f]{64}", container_id) is None:
        raise ExecutionError("CID binding container id is invalid")
    if isinstance(bound_monotonic_ns, bool) or not isinstance(bound_monotonic_ns, int) or bound_monotonic_ns < 0:
        raise ExecutionError("CID binding time is invalid")
    return {
        "schema": "hsai-p01b-container-cid-binding-v1",
        "intent_sha256": intent_sha256,
        "container_id": container_id,
        "create_observation_sha256": create_observation_sha256,
        "bound_monotonic_ns": bound_monotonic_ns,
    }


def build_recovery_inspection_plan(
    *,
    intent_sha256: str,
    container_name: str,
    expected_labels: Mapping[str, str],
    prefix: Sequence[str],
    environment: Mapping[str, str],
) -> Dict[str, object]:
    _require_hex64(intent_sha256, "intent_sha256")
    _require_identifier(container_name, "container_name")
    if len(expected_labels) != 4:
        raise ExecutionError("recovery requires exactly four labels")
    command = _command(
        0,
        "recovery-inspect",
        tuple(prefix) + ("container", "inspect", "--format=" + INSPECT_TEMPLATE, container_name),
        environment,
        cap=METADATA_CAP,
        activation="recovery_only",
        expected=("exact_match_or_absent",),
    )
    return {
        "schema": "hsai-p01b-recovery-inspection-plan-v1",
        "intent_sha256": intent_sha256,
        "container_name": container_name,
        "expected_labels": dict(expected_labels),
        "command": command.to_dict(),
    }


def build_recovery_cleanup_plan(
    *,
    intent_sha256: str,
    cid_binding_sha256: Optional[str],
    inspection_observation_sha256: str,
    selected_branch: str,
    container_id: Optional[str],
    expected_labels: Mapping[str, str],
    container_name: str,
    prefix: Sequence[str],
    environment: Mapping[str, str],
) -> Dict[str, object]:
    """Build one branch-selected cleanup plan from a durable inspection."""
    _require_hex64(intent_sha256, "intent_sha256")
    _require_hex64(inspection_observation_sha256, "inspection_observation_sha256")
    if cid_binding_sha256 is not None:
        _require_hex64(cid_binding_sha256, "cid_binding_sha256")
    if selected_branch not in {"absent", "present-running", "present-stopped", "collision"}:
        raise ExecutionError("recovery branch is not closed")
    if container_id is not None and re.fullmatch(r"[0-9a-f]{64}", container_id) is None:
        raise ExecutionError("recovery container id is invalid")
    if selected_branch.startswith("present-") and container_id is None:
        raise ExecutionError("present recovery requires an observed CID")
    if selected_branch == "collision" and container_id is not None:
        raise ExecutionError("collision must not expose a mutable CID")
    _require_identifier(container_name, "container_name")
    if len(expected_labels) != 4:
        raise ExecutionError("recovery requires exactly four labels")
    labels = (
        "--filter=label=hsai.p01b.campaign=" + str(expected_labels["hsai.p01b.campaign"]),
        "--filter=label=hsai.p01b.attempt=" + str(expected_labels["hsai.p01b.attempt"]),
    )
    roles: List[Tuple[str, Tuple[str, ...], str, Tuple[str, ...]]] = []
    base = tuple(prefix)
    if selected_branch == "present-running":
        assert container_id is not None
        roles.extend(
            (
                ("recovery-kill", base + ("container", "kill", "--signal=KILL", container_id), "recovery_only", ("exit_zero",)),
                ("recovery-wait", base + ("container", "wait", container_id), "recovery_only", ("exit_zero",)),
                ("recovery-terminal-inspect", base + ("container", "inspect", "--format=" + INSPECT_TEMPLATE, container_id), "recovery_only", ("exit_zero",)),
            )
        )
    elif selected_branch == "present-stopped":
        assert container_id is not None
        roles.extend(
            (
                ("recovery-kill", base + ("container", "kill", "--signal=KILL", container_id), "never", ("not_run",)),
                ("recovery-wait", base + ("container", "wait", container_id), "never", ("not_run",)),
            )
        )
    if selected_branch.startswith("present-"):
        assert container_id is not None
        roles.extend(
            (
                ("recovery-remove", base + ("container", "rm", container_id), "recovery_only", ("exit_zero",)),
                ("recovery-absence-cid", base + ("container", "inspect", container_id), "recovery_only", ("exact_absent",)),
            )
        )
    elif selected_branch == "absent" and container_id is not None:
        roles.append(("recovery-absence-cid", base + ("container", "inspect", container_id), "recovery_only", ("exact_absent",)))
    if selected_branch != "collision":
        roles.extend(
            (
                ("recovery-absence-name", base + ("container", "inspect", container_name), "recovery_only", ("exact_absent",)),
                ("recovery-absence-label", base + ("container", "ls", "--all", "--no-trunc") + labels + ("--format={{.ID}}",), "recovery_only", ("empty",)),
                ("recovery-daemon-recheck", base + ("version", "--format={{json .}}"), "recovery_only", ("exit_zero",)),
            )
        )
    commands = [
        _command(index, role, argv, environment, cap=METADATA_CAP,
                 activation=activation, expected=expected).to_dict()
        for index, (role, argv, activation, expected) in enumerate(roles)
    ]
    return {
        "schema": "hsai-p01b-recovery-cleanup-plan-v1",
        "intent_sha256": intent_sha256,
        "cid_binding_sha256": cid_binding_sha256,
        "inspection_observation_sha256": inspection_observation_sha256,
        "selected_branch": selected_branch,
        "container_id": container_id,
        "expected_labels": dict(expected_labels),
        "commands": commands,
    }


def classify_recovery_inspection(
    observation: RawObservation,
    *,
    container_name: str,
    expected_labels: Mapping[str, str],
    bound_container_id: Optional[str],
    evidence_module: Optional[Any] = None,
) -> Tuple[str, Optional[str]]:
    """Select the cleanup branch solely from one complete raw inspect observation."""
    expected_absence = (
        "Error response from daemon: No such container: %s\n" % container_name
    ).encode("ascii")
    if (
        observation.value.get("outcome") == "exit"
        and observation.value.get("exit_code") == 1
        and observation.stdout == b""
        and observation.stderr == expected_absence
    ):
        return "absent", bound_container_id
    if (
        observation.value.get("outcome") != "exit"
        or observation.value.get("exit_code") != 0
        or observation.stderr != b""
    ):
        raise ExecutionError("inspection_failed")
    try:
        inspected = _strict_docker_json(
            observation.stdout, "recovery inspect", evidence_module
        )
    except Exception as error:
        raise ExecutionError("inspection_failed") from error
    if not isinstance(inspected, list) or len(inspected) != len(INSPECT_FIELDS):
        raise ExecutionError("inspection_failed")
    observed_id = inspected[INSPECT_FIELDS.index("Id")]
    observed_name = inspected[INSPECT_FIELDS.index("Name")]
    labels = inspected[INSPECT_FIELDS.index("Config.Labels")]
    running = inspected[INSPECT_FIELDS.index("State.Running")]
    valid_cid = isinstance(observed_id, str) and re.fullmatch(r"[0-9a-f]{64}", observed_id) is not None
    identity_matches = (
        valid_cid
        and observed_name in (container_name, "/" + container_name)
        and labels == dict(expected_labels)
        and type(running) is bool
        and (bound_container_id is None or observed_id == bound_container_id)
    )
    if not identity_matches:
        return "collision", None
    return ("present-running" if running else "present-stopped"), str(observed_id)


def build_recovery_inspection_failure(
    *, intent_sha256: str, inspection_plan_sha256: str,
    inspection_receipt_sha256: str
) -> Dict[str, object]:
    for field, value in (
        ("intent_sha256", intent_sha256),
        ("inspection_plan_sha256", inspection_plan_sha256),
        ("inspection_receipt_sha256", inspection_receipt_sha256),
    ):
        _require_hex64(value, field)
    return {
        "schema": "hsai-p01b-recovery-inspection-failure-v1",
        "intent_sha256": intent_sha256,
        "inspection_plan_sha256": inspection_plan_sha256,
        "inspection_receipt_sha256": inspection_receipt_sha256,
        "failure": "inspection_failed",
    }


def build_recovery_result(
    *, intent_sha256: str, inspection_plan_sha256: str,
    cleanup_plan_sha256: str, ordered_receipts: Sequence[Mapping[str, object]],
    selected_branch: str, cleanup_complete: bool, failure: str
) -> Dict[str, object]:
    for field, value in (
        ("intent_sha256", intent_sha256),
        ("inspection_plan_sha256", inspection_plan_sha256),
        ("cleanup_plan_sha256", cleanup_plan_sha256),
    ):
        _require_hex64(value, field)
    allowed = {
        "campaign_failed_container_absent",
        "campaign_failed_container_removed",
        "identity_collision",
        "recovery_incomplete",
    }
    if selected_branch not in {"absent", "present-running", "present-stopped", "collision"} or failure not in allowed:
        raise ExecutionError("recovery result vocabulary changed")
    expected = {
        "absent": (True, "campaign_failed_container_absent"),
        "present-running": (True, "campaign_failed_container_removed"),
        "present-stopped": (True, "campaign_failed_container_removed"),
        "collision": (False, "identity_collision"),
    }[selected_branch]
    if failure == "recovery_incomplete":
        if cleanup_complete:
            raise ExecutionError("incomplete recovery cannot be complete")
    elif (cleanup_complete, failure) != expected:
        raise ExecutionError("recovery result does not match branch matrix")
    return {
        "schema": "hsai-p01b-recovery-result-v1",
        "intent_sha256": intent_sha256,
        "inspection_plan_sha256": inspection_plan_sha256,
        "cleanup_plan_sha256": cleanup_plan_sha256,
        "ordered_receipt_sha256": sha256_bytes(canonical_json_bytes(list(ordered_receipts))),
        "selected_branch": selected_branch,
        "cleanup_complete": cleanup_complete,
        "failure": failure,
    }


def build_recovery_plan(
    *, prefix: Sequence[str], environment: Mapping[str, str], container_name: str,
    container_id: Optional[str], campaign_id: str, attempt_id: str,
    running: Optional[bool]
) -> Tuple[CommandSpec, ...]:
    """Compatibility projection of the corrected inspection plus cleanup plans."""
    labels = {
        "hsai.p01b.attempt": attempt_id,
        "hsai.p01b.authorization": "0" * 64,
        "hsai.p01b.campaign": campaign_id,
        "hsai.p01b.implementation": "0" * 40,
    }
    inspection = build_recovery_inspection_plan(
        intent_sha256="0" * 64, container_name=container_name,
        expected_labels=labels, prefix=prefix, environment=environment
    )
    branch = "absent" if running is None else ("present-running" if running else "present-stopped")
    cleanup = build_recovery_cleanup_plan(
        intent_sha256="0" * 64, cid_binding_sha256=("0" * 64 if container_id else None),
        inspection_observation_sha256="0" * 64, selected_branch=branch,
        container_id=container_id, expected_labels=labels, container_name=container_name,
        prefix=prefix, environment=environment
    )
    return (
        command_from_mapping(inspection["command"]),
        *(command_from_mapping(value) for value in cleanup["commands"]),
    )


def build_campaign_plan(
    *,
    campaign_id: str,
    authorization_sha256: str,
    implementation_commit: str,
    readiness_plan_sha256: str,
    native_command: CommandSpec,
    metadata_commands: Sequence[CommandSpec],
    normal_plan_sha256: str,
    oom_plan_sha256: str,
) -> Dict[str, object]:
    _require_identifier(campaign_id, "campaign_id")
    for field, value in (
        ("authorization_sha256", authorization_sha256),
        ("readiness_plan_sha256", readiness_plan_sha256),
        ("normal_plan_sha256", normal_plan_sha256),
        ("oom_plan_sha256", oom_plan_sha256),
    ):
        _require_hex64(value, field)
    _require_git(implementation_commit, "implementation_commit")
    return {
        "authorization_sha256": authorization_sha256,
        "campaign_id": campaign_id,
        "implementation_commit": implementation_commit,
        "metadata_commands": [command.to_dict() for command in metadata_commands],
        "native_command": native_command.to_dict(),
        "normal_plan_sha256": normal_plan_sha256,
        "oom_plan_sha256": oom_plan_sha256,
        "readiness_plan_sha256": readiness_plan_sha256,
        "schema": CAMPAIGN_PLAN_SCHEMA,
    }


@dataclass(frozen=True)
class RawObservation:
    value: Mapping[str, object]
    stdout: bytes
    stderr: bytes

    @property
    def digest(self) -> str:
        return domain_sha256(OBSERVATION_DOMAIN, self.value)


def _executable_sha256(path: str) -> str:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink < 1:
            raise ExecutionError("executable must be a linked regular file")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, READ_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(fd)


def _group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    group = process.pid
    try:
        os.killpg(group, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + TERMINATION_GRACE_SECONDS
    while time.monotonic() < deadline and _group_exists(group):
        process.poll()
        time.sleep(0.01)
    if _group_exists(group):
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(group, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()


def _exclusive_file(path: Path, mode: int = 0o600) -> int:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(path), flags, mode)
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        os.close(fd)
        raise ExecutionError("output is not a single-link regular file")
    os.fchmod(fd, mode)
    return fd


def _write_fsync(path: Path, data: bytes) -> None:
    fd = _exclusive_file(path)
    try:
        view = memoryview(data)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise ExecutionError("short output write")
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _replace_fsync(path: Path, data: bytes) -> None:
    """Replace one owned regular file without following links and fsync it."""
    descriptor = os.open(
        str(path),
        os.O_WRONLY
        | os.O_TRUNC
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ExecutionError("replacement target is not a single-link regular file")
        view = memoryview(data)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise ExecutionError("short replacement write")
            view = view[count:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _persist_observation(directory: Path, value: Mapping[str, object]) -> None:
    _write_fsync(directory / "observation.json", canonical_json_bytes(value))
    directory_fd = os.open(str(directory), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _persist_observation_at(
    directory_fd: int, value: Mapping[str, object]
) -> None:
    _a3l9_write_at(
        directory_fd, "observation.json", canonical_json_bytes(value)
    )
    os.fsync(directory_fd)


class DirectProcess:
    """One direct-argv process with bounded concurrent stream collection."""

    def __init__(
        self,
        command: CommandSpec,
        *,
        expected_executable_sha256: Optional[str] = None,
        raw_root: Optional[Path] = None,
        raw_root_fd: Optional[int] = None,
        storage_ordinal: Optional[int] = None,
        use_inherited_cwd: bool = False,
        pass_fds: Sequence[int] = (),
    ) -> None:
        self.command = command
        self.executable_sha256 = _executable_sha256(command.argv[0])
        if expected_executable_sha256 is None:
            expected_executable_sha256 = {
                DOCKER_EXE: DOCKER_SHA256,
                BUILDX_EXE: BUILDX_SHA256,
                "/usr/bin/python3": NATIVE_PYTHON_SHA256,
                SANDBOX_EXEC_PATH: SANDBOX_EXEC_SHA256,
            }.get(command.argv[0])
        if expected_executable_sha256 is not None:
            _require_hex64(expected_executable_sha256, "expected_executable_sha256")
            if self.executable_sha256 != expected_executable_sha256:
                raise ExecutionError("executable identity drift")
        self.raw_directory: Optional[Path] = None
        self._raw_root_fd: Optional[int] = (
            None if raw_root_fd is None else os.dup(raw_root_fd)
        )
        self._raw_directory_fd: Optional[int] = None
        self._raw_fds: Dict[str, int] = {}
        if raw_root_fd is not None and raw_root is None:
            raise ExecutionError("retained raw root requires a logical path")
        if raw_root is not None:
            ordinal = command.ordinal if storage_ordinal is None else storage_ordinal
            if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
                raise ExecutionError("storage ordinal must be a nonnegative integer")
            self.raw_directory = raw_root / ("%03d-%s" % (ordinal, command.role))
            if raw_root_fd is None:
                self.raw_directory.mkdir(mode=0o700, parents=True, exist_ok=False)
            else:
                _require_logical_directory_fd(
                    raw_root, raw_root_fd, "retained raw root"
                )
                name = self.raw_directory.name
                os.mkdir(name, 0o700, dir_fd=raw_root_fd)
                self._raw_directory_fd = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=raw_root_fd,
                )
                _a3l9_require_owned_directory(
                    os.fstat(self._raw_directory_fd),
                    os.fstat(raw_root_fd), 0o700,
                )
                os.fsync(self._raw_directory_fd)
                os.fsync(raw_root_fd)
            try:
                if self._raw_directory_fd is None:
                    self._raw_fds["stdout"] = _exclusive_file(
                        self.raw_directory / "stdout.bin"
                    )
                    self._raw_fds["stderr"] = _exclusive_file(
                        self.raw_directory / "stderr.bin"
                    )
                else:
                    self._raw_fds["stdout"] = _exclusive_file_at(
                        self._raw_directory_fd, "stdout.bin", 0o600
                    )
                    self._raw_fds["stderr"] = _exclusive_file_at(
                        self._raw_directory_fd, "stderr.bin", 0o600
                    )
            except BaseException:
                for descriptor in self._raw_fds.values():
                    os.close(descriptor)
                self._raw_fds.clear()
                if self._raw_directory_fd is not None:
                    os.close(self._raw_directory_fd)
                    self._raw_directory_fd = None
                if self._raw_root_fd is not None:
                    os.close(self._raw_root_fd)
                    self._raw_root_fd = None
                raise
        self.started_ns = time.monotonic_ns()
        self.deadline_ns = self.started_ns + command.timeout_ns
        try:
            self.process = subprocess.Popen(
                list(command.argv),
                cwd=None if use_inherited_cwd else command.cwd,
                env=dict(command.environment),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                start_new_session=True,
                pass_fds=tuple(pass_fds),
            )
        except BaseException:
            self._close_raw_streams()
            if self._raw_directory_fd is not None:
                os.close(self._raw_directory_fd)
                self._raw_directory_fd = None
            if self._raw_root_fd is not None:
                os.close(self._raw_root_fd)
                self._raw_root_fd = None
            raise
        if self.process.stdout is None or self.process.stderr is None:
            _terminate_process_group(self.process)
            self._close_raw_streams()
            raise ExecutionError("failed to allocate process pipes")
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.selector = selectors.DefaultSelector()
        self._streams: Dict[int, Tuple[str, Any]] = {}
        for name, stream in (
            ("stdout", self.process.stdout),
            ("stderr", self.process.stderr),
        ):
            os.set_blocking(stream.fileno(), False)
            self.selector.register(stream.fileno(), selectors.EVENT_READ)
            self._streams[stream.fileno()] = (name, stream)
        self.reason: Optional[str] = None
        self._closed = False

    def _write_raw(self, name: str, chunk: bytes) -> None:
        descriptor = self._raw_fds.get(name)
        if descriptor is None:
            return
        view = memoryview(chunk)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise ExecutionError("short raw stream write")
            view = view[count:]

    def _sync_raw(self, name: str) -> None:
        descriptor = self._raw_fds.get(name)
        if descriptor is not None:
            os.fsync(descriptor)

    def _close_raw_streams(self) -> None:
        first_error: Optional[OSError] = None
        for descriptor in self._raw_fds.values():
            try:
                os.fsync(descriptor)
            except OSError as error:
                if first_error is None:
                    first_error = error
            try:
                os.close(descriptor)
            except OSError as error:
                if first_error is None:
                    first_error = error
        self._raw_fds.clear()
        if first_error is not None:
            raise ExecutionError("raw stream durability failed") from first_error

    def _close_pipes(self) -> None:
        for _, stream in self._streams.values():
            try:
                stream.close()
            except OSError:
                pass
        self._streams.clear()

    def _cap(self, name: str) -> int:
        return self.command.stdout_cap if name == "stdout" else self.command.stderr_cap

    def _buffer(self, name: str) -> bytearray:
        return self.stdout if name == "stdout" else self.stderr

    def pump(self, wait_seconds: float = 0.05) -> None:
        if self._closed:
            return
        if time.monotonic_ns() >= self.deadline_ns:
            self.reason = "timeout"
            _terminate_process_group(self.process)
            return
        timeout = min(
            wait_seconds,
            max(0.0, (self.deadline_ns - time.monotonic_ns()) / 1_000_000_000),
        )
        for key, _ in self.selector.select(timeout):
            descriptor = key.fd
            name, stream = self._streams[descriptor]
            buffer = self._buffer(name)
            cap = self._cap(name)
            remaining = cap + 1 - len(buffer)
            if remaining <= 0:
                self.reason = name + "_limit"
                _terminate_process_group(self.process)
                return
            try:
                chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining))
            except BlockingIOError:
                continue
            if not chunk:
                self.selector.unregister(descriptor)
                stream.close()
                self._streams.pop(descriptor, None)
                continue
            buffer.extend(chunk)
            self._write_raw(name, chunk)
            if len(buffer) > cap:
                self.reason = name + "_limit"
                _terminate_process_group(self.process)
                return

    def wait_for_readiness(self) -> Tuple[int, int, str]:
        """Return byte offset, declared result size, and result digest."""
        checked_lines = 0
        while self.process.poll() is None:
            self.pump()
            if self.reason is not None:
                raise ExecutionError(
                    "start process failed before readiness: %s" % self.reason
                )
            data = bytes(self.stdout)
            lines = data.splitlines(keepends=True)
            for line in lines[checked_lines:]:
                if not line.endswith(b"\n"):
                    break
                offset = sum(len(item) for item in lines[:checked_lines])
                checked_lines += 1
                match = READY_RE.fullmatch(line)
                if match is not None:
                    declared_bytes = int(match.group(1))
                    if declared_bytes > RESULT_CAP:
                        raise ExecutionError("readiness result exceeds size limit")
                    self._sync_raw("stdout")
                    return offset, int(match.group(1)), match.group(2).decode("ascii")
                raise ExecutionError("unexpected stdout before readiness")
        self.pump(0.0)
        raise ExecutionError("start process exited before readiness")

    def complete(
        self,
        *,
        plan_sha256: str,
        completion_ordinal: int,
        previous_observation_sha256: Optional[str],
        container_id: Optional[str] = None,
    ) -> RawObservation:
        if self._closed:
            raise ExecutionError("process observation already completed")
        try:
            while self.process.poll() is None or self.selector.get_map():
                self.pump()
                if self.reason in {"timeout", "stdout_limit", "stderr_limit"}:
                    break
                if self.process.poll() is not None and not self.selector.get_map():
                    break
        except BaseException:
            self.abort()
            raise
        if self.process.poll() is None:
            self.process.wait()
        ended_ns = time.monotonic_ns()
        self.selector.close()
        self._close_pipes()
        self._close_raw_streams()
        self._closed = True
        returncode = self.process.returncode
        if self.reason in {"timeout", "stdout_limit", "stderr_limit"}:
            outcome = self.reason
            exit_code = None
            terminating_signal = None
        elif returncode is not None and returncode < 0:
            outcome = "signal"
            exit_code = None
            terminating_signal = -returncode
        else:
            outcome = "exit"
            exit_code = returncode
            terminating_signal = None
        observation = _observation_value(
            command=self.command,
            plan_sha256=plan_sha256,
            completion_ordinal=completion_ordinal,
            executable_sha256=self.executable_sha256,
            started_ns=self.started_ns,
            ended_ns=ended_ns,
            outcome=outcome,
            exit_code=exit_code,
            terminating_signal=terminating_signal,
            stdout=bytes(self.stdout),
            stderr=bytes(self.stderr),
            previous_observation_sha256=previous_observation_sha256,
            container_id=container_id,
            raw_directory=self.raw_directory,
        )
        result = RawObservation(observation, bytes(self.stdout), bytes(self.stderr))
        if self.raw_directory is not None:
            if self._raw_directory_fd is None:
                _persist_observation(self.raw_directory, observation)
            else:
                _require_logical_directory_fd(
                    self.raw_directory.parent,
                    self._raw_root_fd,
                    "retained raw root",
                )
                _persist_observation_at(self._raw_directory_fd, observation)
                os.close(self._raw_directory_fd)
                self._raw_directory_fd = None
                os.close(self._raw_root_fd)
                self._raw_root_fd = None
        return result

    def abort(self) -> None:
        if not self._closed:
            try:
                _terminate_process_group(self.process)
                self.selector.close()
                self._close_pipes()
                self._close_raw_streams()
            finally:
                if self._raw_directory_fd is not None:
                    os.close(self._raw_directory_fd)
                    self._raw_directory_fd = None
                if self._raw_root_fd is not None:
                    os.close(self._raw_root_fd)
                    self._raw_root_fd = None
                self._closed = True


def _observation_value(
    *,
    command: CommandSpec,
    plan_sha256: str,
    completion_ordinal: int,
    executable_sha256: str,
    started_ns: int,
    ended_ns: int,
    outcome: str,
    exit_code: Optional[int],
    terminating_signal: Optional[int],
    stdout: bytes,
    stderr: bytes,
    previous_observation_sha256: Optional[str],
    container_id: Optional[str],
    raw_directory: Optional[Path],
) -> Dict[str, object]:
    _require_hex64(plan_sha256, "plan_sha256")
    if previous_observation_sha256 is not None:
        _require_hex64(previous_observation_sha256, "previous_observation_sha256")
    stdout_retained = stdout[: command.stdout_cap]
    stderr_retained = stderr[: command.stderr_cap]
    return {
        "argv": list(command.argv),
        "completion_ordinal": completion_ordinal,
        "container_id": container_id,
        "cwd": command.cwd,
        "duration_ns": ended_ns - started_ns,
        "ended_monotonic_ns": ended_ns,
        "environment": dict(command.environment),
        "executable_path": command.argv[0],
        "executable_sha256": executable_sha256,
        "exit_code": exit_code,
        "launch_ordinal": command.ordinal,
        "outcome": outcome,
        "plan_sha256": plan_sha256,
        "previous_observation_sha256": previous_observation_sha256,
        "role": command.role,
        "schema": OBSERVATION_SCHEMA,
        "signal": terminating_signal,
        "started_monotonic_ns": started_ns,
        "stderr_cap": command.stderr_cap,
        "stderr_path": None
        if raw_directory is None
        else str(raw_directory / "stderr.bin"),
        "stderr_raw_sha256": sha256_bytes(stderr),
        "stderr_retained_bytes": len(stderr_retained),
        "stderr_retained_sha256": sha256_bytes(stderr_retained),
        "stderr_total_bytes": len(stderr),
        "stderr_truncated": len(stderr) > command.stderr_cap,
        "stdin_policy": command.stdin_policy,
        "stdout_cap": command.stdout_cap,
        "stdout_path": None
        if raw_directory is None
        else str(raw_directory / "stdout.bin"),
        "stdout_raw_sha256": sha256_bytes(stdout),
        "stdout_retained_bytes": len(stdout_retained),
        "stdout_retained_sha256": sha256_bytes(stdout_retained),
        "stdout_total_bytes": len(stdout),
        "stdout_truncated": len(stdout) > command.stdout_cap,
    }


def execute_direct(
    command: CommandSpec,
    *,
    plan_sha256: str,
    completion_ordinal: int,
    previous_observation_sha256: Optional[str] = None,
    raw_root: Optional[Path] = None,
    raw_root_fd: Optional[int] = None,
    expected_executable_sha256: Optional[str] = None,
    container_id: Optional[str] = None,
) -> RawObservation:
    process = DirectProcess(
        command,
        expected_executable_sha256=expected_executable_sha256,
        raw_root=raw_root,
        raw_root_fd=raw_root_fd,
        storage_ordinal=completion_ordinal,
    )
    return process.complete(
        plan_sha256=plan_sha256,
        completion_ordinal=completion_ordinal,
        previous_observation_sha256=previous_observation_sha256,
        container_id=container_id,
    )


def build_not_run_observation(
    command: CommandSpec,
    *,
    plan_sha256: str,
    completion_ordinal: int,
    previous_observation_sha256: Optional[str],
    raw_root: Path,
    raw_root_fd: Optional[int] = None,
    container_id: Optional[str] = None,
) -> RawObservation:
    """Receipt one planned but skipped role without launching it."""
    directory = raw_root / ("%03d-%s" % (completion_ordinal, command.role))
    directory_fd: Optional[int] = None
    if raw_root_fd is None:
        directory.mkdir(mode=0o700, parents=True, exist_ok=False)
        _write_fsync(directory / "stdout.bin", b"")
        _write_fsync(directory / "stderr.bin", b"")
    else:
        _require_logical_directory_fd(
            raw_root, raw_root_fd, "not-run raw root"
        )
        os.mkdir(directory.name, 0o700, dir_fd=raw_root_fd)
        directory_fd = _a3l9_open_relative_directory(
            raw_root_fd, (directory.name,), mode=0o700
        )
        _a3l9_write_at(directory_fd, "stdout.bin", b"")
        _a3l9_write_at(directory_fd, "stderr.bin", b"")
    value = _observation_value(
        command=command,
        plan_sha256=plan_sha256,
        completion_ordinal=completion_ordinal,
        executable_sha256=_executable_sha256(command.argv[0]),
        started_ns=0,
        ended_ns=0,
        outcome="not_run",
        exit_code=None,
        terminating_signal=None,
        stdout=b"",
        stderr=b"",
        previous_observation_sha256=previous_observation_sha256,
        container_id=container_id,
        raw_directory=directory,
    )
    if directory_fd is None:
        _persist_observation(directory, value)
    else:
        _persist_observation_at(directory_fd, value)
        os.close(directory_fd)
    return RawObservation(value, b"", b"")


def build_recovery_not_run_suffix(
    cleanup_plan: Mapping[str, object],
    *,
    failed_command_index: int,
    plan_sha256: str,
    previous_observation_sha256: str,
    raw_root: Path,
    raw_root_fd: Optional[int] = None,
) -> Tuple[RawObservation, ...]:
    """Retain every unlaunched recovery suffix role after one failed command."""
    _require_hex64(plan_sha256, "plan_sha256")
    _require_hex64(previous_observation_sha256, "previous_observation_sha256")
    commands = cleanup_plan.get("commands")
    if not isinstance(commands, list) or not (
        isinstance(failed_command_index, int)
        and not isinstance(failed_command_index, bool)
        and 0 <= failed_command_index < len(commands)
    ):
        raise ExecutionError("failed recovery command index is invalid")
    container_id = cleanup_plan.get("container_id")
    results: List[RawObservation] = []
    previous = previous_observation_sha256
    for index, value in enumerate(commands[failed_command_index + 1 :], failed_command_index + 1):
        command = command_from_mapping(value)
        if command.activation != "recovery_only":
            raise ExecutionError("failed-command suffix contains a non-recovery activation")
        observation = build_not_run_observation(
            command,
            plan_sha256=plan_sha256,
            completion_ordinal=index + 1,
            previous_observation_sha256=previous,
            raw_root=raw_root,
            raw_root_fd=raw_root_fd,
            container_id=container_id if isinstance(container_id, str) else None,
        )
        results.append(observation)
        previous = observation.digest
    return tuple(results)


def command_from_mapping(value: Mapping[str, object]) -> CommandSpec:
    """Reconstruct one validated execution command from retained plan data."""
    required = {
        "activation",
        "argv",
        "cwd",
        "environment",
        "expected_outcomes",
        "ordinal",
        "role",
        "stderr_cap",
        "stdin_policy",
        "stdout_cap",
        "timeout_ns",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise ExecutionError("retained command fields changed")
    return CommandSpec(
        ordinal=value["ordinal"],  # type: ignore[arg-type]
        role=value["role"],  # type: ignore[arg-type]
        argv=tuple(value["argv"]),  # type: ignore[arg-type]
        environment=value["environment"],  # type: ignore[arg-type]
        cwd=value["cwd"],  # type: ignore[arg-type]
        stdin_policy=value["stdin_policy"],  # type: ignore[arg-type]
        stdout_cap=value["stdout_cap"],  # type: ignore[arg-type]
        stderr_cap=value["stderr_cap"],  # type: ignore[arg-type]
        timeout_ns=value["timeout_ns"],  # type: ignore[arg-type]
        activation=value["activation"],  # type: ignore[arg-type]
        expected_outcomes=tuple(value["expected_outcomes"]),  # type: ignore[arg-type]
    )


def _read_nofollow_regular(path: Path, cap: int) -> bytes:
    descriptor = os.open(
        str(path),
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink < 1:
            raise ExecutionError("retained input is not a regular file")
        data = bytearray()
        while True:
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, cap + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > cap:
                raise ExecutionError("retained input exceeds byte cap")
        after = os.fstat(descriptor)
        if (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_size,
            metadata.st_mtime_ns,
            metadata.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ExecutionError("retained input changed during read")
        return bytes(data)
    finally:
        os.close(descriptor)


def _pinned_file_record(path: Path, expected_sha256: str) -> Mapping[str, object]:
    _require_hex64(expected_sha256, "expected_sha256")
    metadata = os.lstat(path)
    if not stat.S_ISREG(metadata.st_mode) or os.path.islink(path):
        raise ExecutionError("pinned provenance path is not regular")
    digest = _file_sha256(path)
    if digest != expected_sha256:
        raise ExecutionError("pinned provenance digest drifted")
    return {
        "bytes": metadata.st_size,
        "path": str(path),
        "sha256": digest,
    }


def _strict_object(raw: bytes, label: str) -> Mapping[str, object]:
    evidence = _load_evidence_module()
    try:
        value = evidence.strict_json_bytes(raw, max(len(raw), 1))
    except Exception as error:
        raise ExecutionError(label + " is not strict JSON") from error
    if not isinstance(value, dict):
        raise ExecutionError(label + " must be an object")
    return value


def _strict_docker_json(
    raw: bytes, label: str, evidence_module: Optional[Any] = None,
) -> object:
    """Parse Docker template output with its one mandatory trailing newline."""
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise ExecutionError(label + " must have exactly one trailing newline")
    body = raw[:-1]
    evidence = evidence_module or _load_evidence_module()
    try:
        value = evidence.strict_json_bytes(body, max(len(body), 1))
    except Exception as error:
        raise ExecutionError(label + " is not canonical Docker JSON") from error
    if canonical_json_bytes(value) != body:
        raise ExecutionError(label + " is not canonical Docker JSON")
    return value


def _select_platform_descriptor(index_raw: bytes) -> Mapping[str, object]:
    value = _strict_object(index_raw, "registry index")
    manifests = value.get("manifests")
    if not isinstance(manifests, list):
        raise ExecutionError("registry index manifests are absent")
    matches: List[Mapping[str, object]] = []
    for candidate in manifests:
        if not isinstance(candidate, dict):
            raise ExecutionError("registry descriptor is not an object")
        platform = candidate.get("platform")
        if not isinstance(platform, dict):
            continue
        if (
            platform.get("os"),
            platform.get("architecture"),
            platform.get("variant"),
        ) == ("linux", "arm64", "v8"):
            matches.append(candidate)
    if len(matches) != 1:
        raise ExecutionError("registry platform selection was not unique")
    candidate = matches[0]
    digest = candidate.get("digest")
    media_type = candidate.get("mediaType")
    size = candidate.get("size")
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
        or not isinstance(media_type, str)
        or not media_type
        or isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
    ):
        raise ExecutionError("registry descriptor fields are invalid")
    return {
        "architecture": "arm64",
        "digest": digest,
        "mediaType": media_type,
        "os": "linux",
        "size": size,
        "variant": "v8",
    }


def _validate_platform_manifest(
    raw: bytes, descriptor: Mapping[str, object]
) -> Mapping[str, object]:
    if len(raw) != descriptor["size"] or sha256_bytes(raw) != str(descriptor["digest"]).split(":", 1)[1]:
        raise ExecutionError("selected platform manifest content drifted")
    value = _strict_object(raw, "platform manifest")
    if value.get("mediaType") != descriptor.get("mediaType"):
        raise ExecutionError("platform manifest media type drifted")
    config = value.get("config")
    layers = value.get("layers")
    if not isinstance(config, dict) or config.get("digest") != IMAGE_CONFIG_DIGEST:
        raise ExecutionError("platform manifest config drifted")
    if not isinstance(layers, list) or len(layers) != len(ROOTFS_DIFF_IDS):
        raise ExecutionError("platform manifest layer count drifted")
    for layer in layers:
        if not isinstance(layer, dict) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", str(layer.get("digest", ""))
        ) is None:
            raise ExecutionError("platform manifest layer digest is invalid")
    return value


def _validate_local_image(raw: bytes, selected_reference: str) -> None:
    del selected_reference
    value = _strict_docker_json(raw, "local image inspect")
    if not isinstance(value, dict):
        raise ExecutionError("local image inspect must be an object")
    rootfs = value.get("RootFS")
    if (
        value.get("Id") != IMAGE_CONFIG_DIGEST
        or value.get("Os") != "linux"
        or value.get("Architecture") != "arm64"
        or value.get("Variant") not in (None, "", "v8")
        or not isinstance(rootfs, dict)
        or tuple(rootfs.get("Layers", ())) != ROOTFS_DIFF_IDS
    ):
        raise ExecutionError("local image resolution drifted")


_CODESIGN_COMPONENT = rb"[A-Za-z0-9](?:[A-Za-z0-9 ._+@%=-]{0,126}[A-Za-z0-9._+@%=-])?"
_CODESIGN_PATH = rb"/Applications/Docker\.app(?:/" + _CODESIGN_COMPONENT + rb"){0,15}"
_CODESIGN_NESTED_PATH = rb"/Applications/Docker\.app(?:/" + _CODESIGN_COMPONENT + rb"){1,15}"


def parse_codesign_verify(raw: bytes) -> Dict[str, object]:
    """Parse the closed codesign verification transcript grammar."""
    if len(raw) > METADATA_CAP or b"\r" in raw:
        raise ExecutionError("codesign verify transcript is invalid")
    try:
        raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ExecutionError("codesign verify transcript is not ASCII") from error
    rows = raw.splitlines(keepends=True)
    if len(rows) < 2 or rows[-2:] != [
        b"/Applications/Docker.app: valid on disk\n",
        b"/Applications/Docker.app: satisfies its Designated Requirement\n",
    ]:
        raise ExecutionError("codesign verify terminal rows changed")
    prepared: List[str] = []
    validated: List[str] = []
    prefix_rows = rows[:-2]
    if len(prefix_rows) % 2:
        raise ExecutionError("codesign prepared/validated rows are not paired")
    for index in range(0, len(prefix_rows), 2):
        prepared_match = re.fullmatch(rb"--prepared:(" + _CODESIGN_NESTED_PATH + rb")\n", prefix_rows[index])
        validated_match = re.fullmatch(rb"--validated:(" + _CODESIGN_NESTED_PATH + rb")\n", prefix_rows[index + 1])
        if prepared_match is None or validated_match is None or prepared_match.group(1) != validated_match.group(1):
            raise ExecutionError("codesign prepared/validated path mismatch")
        path = prepared_match.group(1).decode("ascii")
        if len(path.encode("ascii")) > 1024:
            raise ExecutionError("codesign path exceeds byte cap")
        prepared.append(path)
        validated.append(path)
    return {
        "prepared_paths": prepared,
        "validated_paths": validated,
        "valid_on_disk": True,
        "satisfies_designated_requirement": True,
    }


def parse_codesign_display(raw: bytes) -> Dict[str, object]:
    """Parse the frozen ordered Docker.app display rows and cross-hashes."""
    if len(raw) > METADATA_CAP or b"\r" in raw:
        raise ExecutionError("codesign display transcript is invalid")
    try:
        decoded = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise ExecutionError("codesign display transcript is not ASCII") from error
    rows = decoded.splitlines(keepends=True)
    prefixes = (
        "Executable=", "Identifier=", "Format=", "CodeDirectory v=", "Hash type=",
        "CandidateCDHash sha256=", "CandidateCDHashFull sha256=", "Hash choices=",
        "CMSDigest=", "CMSDigestType=", "Executable Segment base=",
        "Executable Segment limit=", "Executable Segment flags=", "Page size=",
        "CDHash=", "Signature size=", "Authority=", "Authority=", "Authority=",
        "Timestamp=", "Notarization Ticket=", "Info.plist entries=", "TeamIdentifier=",
        "Runtime Version=", "Sealed Resources version=", "Internal requirements count=",
    )
    if len(rows) != len(prefixes) or any(
        len(row.encode("ascii")) > 1024 or not row.startswith(prefix)
        for row, prefix in zip(rows, prefixes)
    ):
        raise ExecutionError("codesign display row order changed")
    exact = {
        0: "Executable=/Applications/Docker.app/Contents/MacOS/Docker Desktop\n",
        1: "Identifier=com.docker.docker\n",
        4: "Hash type=sha256 size=32\n",
        7: "Hash choices=sha256\n",
        9: "CMSDigestType=2\n",
        16: "Authority=Developer ID Application: Docker Inc (9BNSXJN65R)\n",
        17: "Authority=Developer ID Certification Authority\n",
        18: "Authority=Apple Root CA\n",
        20: "Notarization Ticket=stapled\n",
        22: "TeamIdentifier=9BNSXJN65R\n",
    }
    if any(rows[index] != value for index, value in exact.items()):
        raise ExecutionError("codesign display identity row changed")
    full = rows[6].removeprefix("CandidateCDHashFull sha256=").removesuffix("\n")
    candidate = rows[5].removeprefix("CandidateCDHash sha256=").removesuffix("\n")
    cms = rows[8].removeprefix("CMSDigest=").removesuffix("\n")
    cdhash = rows[14].removeprefix("CDHash=").removesuffix("\n")
    if HEX64_RE.fullmatch(full) is None or candidate != full[:40] or cms != full or cdhash != full[:40]:
        raise ExecutionError("codesign display hash correspondence failed")
    authorities = [rows[index][len("Authority=") : -1] for index in (16, 17, 18)]
    return {
        "ordered_rows": [row.removesuffix("\n") for row in rows],
        "executable": "/Applications/Docker.app/Contents/MacOS/Docker Desktop",
        "identifier": "com.docker.docker",
        "format": rows[2][len("Format=") : -1],
        "candidate_cdhash": candidate,
        "candidate_cdhash_full": full,
        "cms_digest": cms,
        "cdhash": cdhash,
        "authorities": authorities,
        "team_identifier": "9BNSXJN65R",
        "runtime_version": rows[23][len("Runtime Version=") : -1],
    }


def build_descriptor_set(kind: str, observations: Sequence[Mapping[str, object]]) -> Dict[str, object]:
    if kind not in {"host-tools", "docker-desktop"} or len(observations) != 3:
        raise ExecutionError("descriptor set kind or cardinality changed")
    ordered = sorted(observations, key=lambda item: str(item.get("path", "")).encode("ascii"))
    if list(observations) != ordered:
        raise ExecutionError("descriptor observations are not in bytewise path order")
    return {
        "schema": "hsai-p01b-descriptor-set-v1",
        "kind": kind,
        "ordered_observations": list(observations),
    }


@dataclass(frozen=True)
class A3L7SnapshotMaterial:
    root: str
    pair: Mapping[str, object]
    source_manifest: Mapping[str, object]
    copy_manifest: Mapping[str, object]
    source_descriptor_set: Mapping[str, object]
    snapshot_descriptor_set: Mapping[str, object]
    source_manifest_sha256: str
    copy_manifest_sha256: str


def create_a3l7_snapshot(
    gate_bundle: Mapping[str, object], snapshot_root: Path
) -> A3L7SnapshotMaterial:
    """Freeze the exact A3L6 source as the descriptor-bound A3L7 snapshot."""
    evidence = _load_evidence_module()
    try:
        gate = validate_a3l6_gate_bundle(gate_bundle)
    except Exception as error:
        raise ExecutionError("A3L6 gate bundle was rejected before snapshot") from error
    source_value = gate.get("gate_source_manifest")
    if not isinstance(source_value, Mapping):
        raise ExecutionError("A3L6 gate source manifest is absent")
    source_root_value = source_value.get("materialized_root")
    if not isinstance(source_root_value, str):
        raise ExecutionError("A3L6 materialized source root is absent")
    _require_absolute(source_root_value, "A3L6 materialized source root")
    source_root = Path(source_root_value)
    snapshot_path = Path(os.path.abspath(str(snapshot_root)))
    source_real = os.path.realpath(source_root)
    snapshot_real = os.path.realpath(snapshot_path)
    if snapshot_real == source_real or snapshot_real.startswith(source_real + os.sep):
        raise ExecutionError("A3L7 snapshot overlaps the immutable source")
    rows_value = source_value.get("ordered_sources")
    if not isinstance(rows_value, list) or len(rows_value) != len(SOURCE_PATHS):
        raise ExecutionError("A3L6 source row census changed")
    gate_rows = {str(row.get("path")): row for row in rows_value if isinstance(row, Mapping)}
    if tuple(gate_rows) != SOURCE_PATHS:
        raise ExecutionError("A3L6 source row order changed")
    snapshot_path.mkdir(mode=0o700, parents=False, exist_ok=False)
    created_directories = {snapshot_path}
    source_entries: List[Mapping[str, object]] = []
    copy_entries: List[Mapping[str, object]] = []
    source_observations: List[Mapping[str, object]] = []
    snapshot_observations: List[Mapping[str, object]] = []
    try:
        for relative in SOURCE_PATHS:
            row = gate_rows[relative]
            source_observation, raw = _read_observed_regular(
                source_root / relative, "source", relative, SNAPSHOT_FILE_LIMIT
            )
            if row.get("bytes") != len(raw) or row.get("sha256") != sha256_bytes(raw):
                raise ExecutionError("A3L6 source row changed before snapshot: " + relative)
            destination = snapshot_path / relative
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            current = destination.parent
            while current != snapshot_path.parent:
                created_directories.add(current)
                if current == snapshot_path:
                    break
                current = current.parent
            _write_fsync(destination, raw)
            os.chmod(destination, 0o444)
            snapshot_observation, copied = _read_observed_regular(
                destination, "snapshot", relative, SNAPSHOT_FILE_LIMIT
            )
            if copied != raw:
                raise ExecutionError("A3L7 snapshot copy changed: " + relative)
            source_entry = {
                "path": relative,
                "mode": source_observation["before"]["mode"],
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
                "descriptor_observation_sha256": evidence.descriptor_observation_digest(
                    source_observation
                ),
            }
            copy_entry = {
                "path": relative,
                "mode": 0o444,
                "bytes": len(copied),
                "sha256": sha256_bytes(copied),
                "descriptor_observation_sha256": evidence.descriptor_observation_digest(
                    snapshot_observation
                ),
            }
            source_entries.append(source_entry)
            copy_entries.append(copy_entry)
            source_observations.append(source_observation)
            snapshot_observations.append(snapshot_observation)
        for directory in sorted(
            created_directories, key=lambda value: len(value.parts), reverse=True
        ):
            os.chmod(directory, 0o555)
            _fsync_directory(directory)
        source_manifest = {
            "schema": SNAPSHOT_SOURCE_SCHEMA,
            "ordered_entries": source_entries,
        }
        copy_manifest = {
            "schema": SNAPSHOT_COPY_SCHEMA,
            "ordered_entries": copy_entries,
        }
        source_sha256 = evidence.snapshot_source_manifest_digest(source_manifest)
        copy_sha256 = evidence.snapshot_copy_manifest_digest(copy_manifest)
        source_descriptor_set = {
            "schema": SNAPSHOT_DESCRIPTOR_SCHEMA,
            "kind": "source",
            "manifest_sha256": source_sha256,
            "ordered_observations": source_observations,
        }
        snapshot_descriptor_set = {
            "schema": SNAPSHOT_DESCRIPTOR_SCHEMA,
            "kind": "snapshot",
            "manifest_sha256": copy_sha256,
            "ordered_observations": snapshot_observations,
        }
        pair = {
            "schema": SNAPSHOT_PAIR_SCHEMA,
            "implementation_commit": gate["implementation_commit"],
            "implementation_tree": gate["implementation_tree"],
            "source_manifest": source_manifest,
            "snapshot_manifest": copy_manifest,
        }
        evidence.validate_snapshot_manifest_pair(
            pair, source_descriptor_set, snapshot_descriptor_set
        )
        return A3L7SnapshotMaterial(
            str(snapshot_path),
            pair,
            source_manifest,
            copy_manifest,
            source_descriptor_set,
            snapshot_descriptor_set,
            source_sha256,
            copy_sha256,
        )
    except BaseException:
        for directory in sorted(
            created_directories, key=lambda value: len(value.parts), reverse=True
        ):
            try:
                os.chmod(directory, 0o700)
            except OSError:
                pass
        shutil.rmtree(snapshot_path, ignore_errors=True)
        raise


def _create_a3l7_snapshot_at(
    gate_bundle: Mapping[str, object], output_root: Path, output_root_fd: int,
) -> A3L7SnapshotMaterial:
    """Freeze A3L6 sources into the retained A3L7 output descriptor tree."""
    evidence = _load_evidence_module()
    gate = validate_a3l6_gate_bundle(gate_bundle)
    source_value = gate.get("gate_source_manifest")
    if not isinstance(source_value, Mapping):
        raise ExecutionError("A3L6 gate source manifest is absent")
    source_root_value = source_value.get("materialized_root")
    if not isinstance(source_root_value, str):
        raise ExecutionError("A3L6 materialized source root is absent")
    _require_absolute(source_root_value, "A3L6 materialized source root")
    source_root = Path(source_root_value)
    snapshot_relative = "snapshot/files"
    snapshot_path = output_root / snapshot_relative
    source_real = os.path.realpath(source_root)
    snapshot_real = os.path.realpath(snapshot_path)
    if snapshot_real == source_real or snapshot_real.startswith(source_real + os.sep):
        raise ExecutionError("A3L7 snapshot overlaps the immutable source")
    rows_value = source_value.get("ordered_sources")
    if not isinstance(rows_value, list) or len(rows_value) != len(SOURCE_PATHS):
        raise ExecutionError("A3L6 source row census changed")
    gate_rows = {
        str(row.get("path")): row for row in rows_value
        if isinstance(row, Mapping)
    }
    if tuple(gate_rows) != SOURCE_PATHS:
        raise ExecutionError("A3L6 source row order changed")
    _a3l7_create_directory(output_root_fd, snapshot_relative)
    created_directories = {snapshot_relative}
    source_entries: List[Mapping[str, object]] = []
    copy_entries: List[Mapping[str, object]] = []
    source_observations: List[Mapping[str, object]] = []
    snapshot_observations: List[Mapping[str, object]] = []
    for relative in SOURCE_PATHS:
        row = gate_rows[relative]
        source_observation, raw = _read_observed_regular(
            source_root / relative, "source", relative, SNAPSHOT_FILE_LIMIT
        )
        if row.get("bytes") != len(raw) or row.get("sha256") != sha256_bytes(raw):
            raise ExecutionError(
                "A3L6 source row changed before snapshot: " + relative
            )
        destination_relative = snapshot_relative + "/" + relative
        parts = _validate_relative_path(destination_relative)
        for index in range(2, len(parts)):
            created_directories.add("/".join(parts[:index]))
        _a3l7_write_at(
            output_root_fd, destination_relative, raw, file_mode=0o444
        )
        snapshot_observation, copied = _a3l7_observe_at(
            output_root_fd, output_root, destination_relative, "snapshot",
            relative,
        )
        if copied != raw:
            raise ExecutionError("A3L7 snapshot copy changed: " + relative)
        source_entry = {
            "path": relative,
            "mode": source_observation["before"]["mode"],
            "bytes": len(raw),
            "sha256": sha256_bytes(raw),
            "descriptor_observation_sha256":
                evidence.descriptor_observation_digest(source_observation),
        }
        copy_entry = {
            "path": relative,
            "mode": 0o444,
            "bytes": len(copied),
            "sha256": sha256_bytes(copied),
            "descriptor_observation_sha256":
                evidence.descriptor_observation_digest(snapshot_observation),
        }
        source_entries.append(source_entry)
        copy_entries.append(copy_entry)
        source_observations.append(source_observation)
        snapshot_observations.append(snapshot_observation)
    retained_directories: List[Tuple[str, int]] = []
    try:
        for relative in sorted(
            created_directories,
            key=lambda item: (len(item.split("/")), item.encode("ascii")),
            reverse=True,
        ):
            retained_directories.append((
                relative,
                _a3l9_open_relative_directory(
                    output_root_fd, _validate_relative_path(relative), mode=0o700
                ),
            ))
        for _, descriptor in retained_directories:
            os.fchmod(descriptor, 0o555)
            os.fsync(descriptor)
        os.fsync(output_root_fd)
    finally:
        for _, descriptor in retained_directories:
            os.close(descriptor)
    source_manifest = {
        "schema": SNAPSHOT_SOURCE_SCHEMA, "ordered_entries": source_entries,
    }
    copy_manifest = {
        "schema": SNAPSHOT_COPY_SCHEMA, "ordered_entries": copy_entries,
    }
    source_sha256 = evidence.snapshot_source_manifest_digest(source_manifest)
    copy_sha256 = evidence.snapshot_copy_manifest_digest(copy_manifest)
    source_descriptor_set = {
        "schema": SNAPSHOT_DESCRIPTOR_SCHEMA, "kind": "source",
        "manifest_sha256": source_sha256,
        "ordered_observations": source_observations,
    }
    snapshot_descriptor_set = {
        "schema": SNAPSHOT_DESCRIPTOR_SCHEMA, "kind": "snapshot",
        "manifest_sha256": copy_sha256,
        "ordered_observations": snapshot_observations,
    }
    pair = {
        "schema": SNAPSHOT_PAIR_SCHEMA,
        "implementation_commit": gate["implementation_commit"],
        "implementation_tree": gate["implementation_tree"],
        "source_manifest": source_manifest,
        "snapshot_manifest": copy_manifest,
    }
    evidence.validate_snapshot_manifest_pair(
        pair, source_descriptor_set, snapshot_descriptor_set
    )
    return A3L7SnapshotMaterial(
        str(snapshot_path), pair, source_manifest, copy_manifest,
        source_descriptor_set, snapshot_descriptor_set, source_sha256,
        copy_sha256,
    )


def _canonical_readiness_plan(
    supplied: Mapping[str, object],
    user_authorization_sha256: str,
    *,
    context_path: str,
    host_uri: str,
    output_root: Path,
) -> Tuple[Mapping[str, object], str, str, str]:
    """Rebuild every executable byte from captured/code-owned inputs."""
    _require_absolute(context_path, "Docker context path")
    _require_absolute(str(output_root), "output_root")
    if not isinstance(host_uri, str) or not host_uri.startswith("unix:///"):
        raise ExecutionError("captured Docker context host is invalid")
    context = Path(context_path)
    try:
        marker = context.parts.index(".docker")
    except ValueError as error:
        raise ExecutionError("Docker context is outside the frozen config root") from error
    config_path = Path(*context.parts[: marker + 1])
    relative = context.relative_to(config_path).parts
    if (
        len(relative) != 4
        or relative[:2] != ("contexts", "meta")
        or re.fullmatch(r"[0-9a-f]{64}", relative[2]) is None
        or relative[3] != "meta.json"
    ):
        raise ExecutionError("Docker context path grammar changed")
    config_root = str(config_path)
    temporary_root = str(output_root / READINESS_TEMP_BASENAME)
    expected = build_readiness_plan(
        predecessor_commit=READINESS_PREDECESSOR_COMMIT,
        user_authorization_sha256=user_authorization_sha256,
        config_root=config_root,
        host_uri=host_uri,
        temporary_root=temporary_root,
    )
    if canonical_json_bytes(supplied) != canonical_json_bytes(expected):
        raise ExecutionError("readiness plan is not the canonical executable plan")
    try:
        _load_evidence_module().validate_readiness_plan(expected)
    except Exception as error:
        raise ExecutionError("canonical readiness plan was rejected") from error
    return expected, config_root, host_uri, temporary_root


def _retain_readiness_observation(
    output_root: Path, output_root_fd: int, observation: RawObservation,
    completion_ordinal: int, evidence_module: Any,
) -> RawObservation:
    """Bind an observation to its candidate-relative readiness operation paths."""
    role = observation.value.get("role")
    if not isinstance(role, str):
        raise ExecutionError("readiness observation role is absent")
    basename = "%03d-%s" % (completion_ordinal, role)
    logical = "operations/readiness/" + basename
    _a3l7_create_directory(output_root_fd, logical)
    for leaf, raw in (("stdout.bin", observation.stdout), ("stderr.bin", observation.stderr)):
        _a3l7_write_at(output_root_fd, logical + "/" + leaf, raw)
    value = dict(observation.value)
    value["stdout_path"] = logical + "/stdout.bin"
    value["stderr_path"] = logical + "/stderr.bin"
    retained = RawObservation(value, observation.stdout, observation.stderr)
    try:
        evidence_module.validate_observation(
            value, observation.stdout, observation.stderr
        )
    except Exception as error:
        raise ExecutionError("readiness observation was rejected") from error
    _a3l7_write_at(
        output_root_fd, logical + "/observation.json",
        canonical_json_bytes(value),
    )
    _a3l7_fsync_directory(output_root_fd, logical)
    _a3l7_fsync_directory(output_root_fd, "operations/readiness")
    _require_logical_directory_fd(
        output_root, output_root_fd, "A3L7 output root"
    )
    return retained


def _transcript_binding(
    kind: str,
    observation: RawObservation,
    parsed: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "schema": TRANSCRIPT_BINDING_SCHEMA,
        "kind": kind,
        "observation_sha256": observation.digest,
        "stdout_path": observation.value["stdout_path"],
        "stdout_bytes": len(observation.stdout),
        "stdout_sha256": sha256_bytes(observation.stdout),
        "stderr_path": observation.value["stderr_path"],
        "stderr_bytes": len(observation.stderr),
        "stderr_sha256": sha256_bytes(observation.stderr),
        "parsed": dict(parsed),
    }


def _host_provenance(
    kind: str,
    observations: Sequence[RawObservation],
    descriptor_set: Mapping[str, object],
    facts: Mapping[str, object],
    assumptions: Sequence[str],
    evidence_module: Optional[Any] = None,
) -> Dict[str, object]:
    evidence = evidence_module or _load_evidence_module()
    return {
        "schema": HOST_PROVENANCE_SCHEMA,
        "kind": kind,
        "ordered_source_observation_sha256": [item.digest for item in observations],
        "descriptor_set_sha256": evidence.descriptor_set_digest(descriptor_set),
        "descriptor_set": dict(descriptor_set),
        "facts": dict(facts),
        "assumptions": list(assumptions),
    }


def _build_expected_bindings(
    *,
    readiness_plan: Mapping[str, object],
    user_authorization_sha256: str,
    gate_bundle: Mapping[str, object],
    snapshot: A3L7SnapshotMaterial,
    selected_descriptor: Mapping[str, object],
    platform_manifest: Mapping[str, object],
    platform_raw: bytes,
    index_raw: bytes,
    context_raw: bytes,
    info_plist_sha256: str,
    display_facts: Mapping[str, object],
) -> Dict[str, object]:
    evidence = _load_evidence_module()
    gate = evidence.validate_a3l6_gate_bundle(gate_bundle)
    gate_plan = gate["gate_plan"]
    gate_source = gate["gate_source_manifest"]
    if not isinstance(gate_plan, Mapping) or not isinstance(gate_source, Mapping):
        raise ExecutionError("A3L6 gate internals are absent")
    source_rows_value = gate_source.get("ordered_sources")
    if not isinstance(source_rows_value, list):
        raise ExecutionError("A3L6 source rows are absent")
    source_rows = {
        str(row.get("path")): row
        for row in source_rows_value
        if isinstance(row, Mapping)
    }
    copy_entries = snapshot.copy_manifest["ordered_entries"]
    if not isinstance(copy_entries, list):
        raise ExecutionError("snapshot copy entries are absent")
    copy_by_path = {
        str(row.get("path")): row for row in copy_entries if isinstance(row, Mapping)
    }
    seccomp_path = "tools/hsai-formal-preflight/p01b_container_seccomp.json"
    seccomp = copy_by_path.get(seccomp_path)
    if not isinstance(seccomp, Mapping):
        raise ExecutionError("snapshot seccomp entry is absent")
    media_type = platform_manifest.get("mediaType")
    if not isinstance(media_type, str) or not media_type:
        raise ExecutionError("platform manifest media type is absent")
    claim_boundary = canonical_claim_boundary()
    value: Dict[str, object] = {
        "schema": EXPECTED_BINDINGS_SCHEMA,
        "predecessor_commit": readiness_plan["predecessor_commit"],
        "implementation_commit": gate["implementation_commit"],
        "implementation_tree": gate["implementation_tree"],
        "user_authorization_sha256": user_authorization_sha256,
        "claim_boundary": claim_boundary,
        "claim_boundary_sha256": evidence.claim_boundary_digest(claim_boundary),
        "a3l6_audit_commit": gate_plan["audit_commit"],
        "a3l6_gate_plan_sha256": evidence.a3l6_gate_plan_digest(gate_plan),
        "a3l6_gate_source_manifest_sha256": evidence.a3l6_gate_source_digest(
            gate_source
        ),
        "a3l6_gate_bundle_sha256": evidence.a3l6_gate_bundle_digest(gate),
        "expected_focused_test_ids_sha256": sha256_bytes(
            canonical_json_bytes(gate["focused_test_ids"])
        ),
        "validator_sha256": source_rows[
            "tools/hsai-formal-preflight/p01b_container_evidence.py"
        ]["sha256"],
        "collector_sha256": source_rows[
            "tools/hsai-formal-preflight/p01b_container_execution.py"
        ]["sha256"],
        "expected_focused_test_count": 65,
        "protected_path": PROTECTED_ADMISSION_PATH,
        "protected_sha256": PROTECTED_ADMISSION_SHA256,
        "native_python_path": "/usr/bin/python3",
        "native_python_sha256": NATIVE_PYTHON_SHA256,
        "native_python_version": "3.9.6",
        "sandbox_exec_path": SANDBOX_EXEC_PATH,
        "sandbox_exec_sha256": SANDBOX_EXEC_SHA256,
        "gate_sandbox_profile_sha256": gate_plan["sandbox_profile_sha256"],
        "normal_python_path": "/usr/local/bin/python3",
        "normal_python_version": "3.11.15",
        "normal_interpreter_policy": "probe-observed-ordered-chain-under-probe-honesty",
        "git_path": gate_source["git_path"],
        "git_sha256": gate_source["git_sha256"],
        "docker_path": DOCKER_EXE,
        "docker_sha256": DOCKER_SHA256,
        "buildx_path": BUILDX_EXE,
        "buildx_sha256": BUILDX_SHA256,
        "codesign_path": CODE_SIGN_EXE,
        "codesign_sha256": CODE_SIGN_SHA256,
        "docker_desktop_info_plist_path": DOCKER_DESKTOP_INFO_PLIST,
        "docker_desktop_info_plist_sha256": info_plist_sha256,
        "docker_desktop_vm_path": DOCKER_DESKTOP_VM_PATH,
        "docker_desktop_vm_sha256": DOCKER_DESKTOP_VM_SHA256,
        "docker_desktop_kernel_path": DOCKER_DESKTOP_KERNEL_PATH,
        "docker_desktop_kernel_sha256": DOCKER_DESKTOP_KERNEL_SHA256,
        "docker_app_candidate_cdhash_full": display_facts[
            "candidate_cdhash_full"
        ],
        "docker_app_team_identifier": display_facts["team_identifier"],
        "docker_context_path": DOCKER_CONTEXT_PATH,
        "docker_context_sha256": sha256_bytes(context_raw),
        "index_reference": INDEX_REFERENCE,
        "index_manifest_sha256": sha256_bytes(index_raw),
        "selected_platform": {"os": "linux", "architecture": "arm64", "variant": "v8"},
        "selected_descriptor_digest": selected_descriptor["digest"],
        "selected_descriptor_size": selected_descriptor["size"],
        "selected_descriptor_media_type": selected_descriptor["mediaType"],
        "platform_reference": "docker.io/library/python@" + str(selected_descriptor["digest"]),
        "platform_manifest_sha256": sha256_bytes(platform_raw),
        "platform_manifest_size": len(platform_raw),
        "platform_manifest_media_type": media_type,
        "image_config_digest": IMAGE_CONFIG_DIGEST,
        "rootfs_diff_ids": list(ROOTFS_DIFF_IDS),
        "snapshot_source_manifest_sha256": snapshot.source_manifest_sha256,
        "snapshot_copy_manifest_sha256": snapshot.copy_manifest_sha256,
        "seccomp_sha256": seccomp["sha256"],
        "normal_expected_test_count": 151,
        "discovery_expected_test_count": 172,
        "candidate_payload_count": 201,
        "attempt_deadline_ns": ATTEMPT_TIMEOUT_NS,
        "class_order": list(CLASS_ORDER),
        "evidence_level": "Level1LocalReplayOrLower",
    }
    evidence.validate_expected_bindings(value)
    evidence.validate_a3l6_gate_bundle(gate, value)
    return value


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    _write_fsync(path, canonical_json_bytes(value))
    _fsync_directory(path.parent)


def _write_bytes_durable(path: Path, raw: bytes) -> None:
    """Exclusively retain bytes and durably link the file in its parent."""
    _write_fsync(path, raw)
    _fsync_directory(path.parent)


def _mkdir_durable(path: Path) -> None:
    """Create one directory and durably link it in its existing parent."""
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    _fsync_directory(path)
    _fsync_directory(path.parent)


def _a3l7_open_output_root(path: Path) -> int:
    """Exclusively create and retain one no-follow A3L7 output root."""
    value = _a3l9_canonical_absolute(str(path), "A3L7 output root")
    parts = value.split("/")[1:]
    if not parts:
        raise ExecutionError("A3L7 output root cannot be filesystem root")
    descriptor = os.open(
        "/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    created = False
    parent_fd = -1
    try:
        for index, part in enumerate(parts):
            if not part or part in (".", ".."):
                raise ExecutionError("A3L7 output path component changed")
            if index == len(parts) - 1:
                parent_fd = descriptor
                parent = os.fstat(parent_fd)
                if (
                    not stat.S_ISDIR(parent.st_mode)
                    or parent.st_uid != os.geteuid()
                    or stat.S_IMODE(parent.st_mode) != 0o700
                ):
                    raise ExecutionError(
                        "A3L7 output parent is not an owned directory"
                    )
                os.mkdir(part, 0o700, dir_fd=parent_fd)
                created = True
            next_descriptor = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptor,
            )
            if index == len(parts) - 1:
                root = os.fstat(next_descriptor)
                if (
                    not stat.S_ISDIR(root.st_mode)
                    or root.st_uid != os.geteuid()
                    or root.st_gid != parent.st_gid
                    or root.st_dev != parent.st_dev
                    or stat.S_IMODE(root.st_mode) != 0o700
                ):
                    os.close(next_descriptor)
                    raise ExecutionError("A3L7 output root identity changed")
                os.fsync(next_descriptor)
                os.fsync(parent_fd)
            os.close(descriptor)
            descriptor = next_descriptor
        result = descriptor
        descriptor = -1
        return result
    except OSError as error:
        if created and parent_fd >= 0:
            try:
                os.rmdir(parts[-1], dir_fd=parent_fd)
                os.fsync(parent_fd)
            except OSError:
                pass
        raise ExecutionError("A3L7 output traversal was rejected") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _a3l7_create_directory(root_fd: int, relative: str) -> None:
    descriptor = _a3l9_open_relative_directory(
        root_fd, _validate_relative_path(relative), mode=0o700, create=True
    )
    os.close(descriptor)


def _a3l7_fsync_directory(root_fd: int, relative: str = "") -> None:
    descriptor = (
        os.dup(root_fd)
        if not relative
        else _a3l9_open_relative_directory(
            root_fd, _validate_relative_path(relative), mode=0o700
        )
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _a3l7_write_at(
    root_fd: int, relative: str, raw: bytes, *, file_mode: int = 0o600,
) -> Dict[str, int]:
    parts = _validate_relative_path(relative)
    directory = _a3l9_open_relative_directory(
        root_fd, parts[:-1], mode=0o700, create=True
    )
    try:
        descriptor = _exclusive_file_at(directory, parts[-1], file_mode)
        try:
            view = memoryview(raw)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise ExecutionError("A3L7 output write was short")
                view = view[written:]
            os.fchmod(descriptor, file_mode)
            os.fsync(descriptor)
            identity = _identity(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        os.fsync(directory)
        return identity
    except OSError as error:
        raise ExecutionError("A3L7 exclusive output was rejected") from error
    finally:
        os.close(directory)


def _a3l7_observe_at(
    root_fd: int, output_root: Path, relative: str, role: str,
    source_relative: str,
) -> Tuple[Mapping[str, object], bytes]:
    parts = _validate_relative_path(relative)
    directory = _a3l9_open_relative_directory(
        root_fd, parts[:-1], mode=0o700
    )
    try:
        descriptor = os.open(
            parts[-1], os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0), dir_fd=directory,
        )
        try:
            observation = _capture_open_descriptor_observation(
                descriptor,
                absolute_path=str(output_root / relative),
                role=role,
                relative_path=source_relative,
            )
            os.lseek(descriptor, 0, os.SEEK_SET)
            raw = bytearray()
            while True:
                chunk = os.read(descriptor, READ_CHUNK_BYTES)
                if not chunk:
                    break
                raw.extend(chunk)
                if len(raw) > SNAPSHOT_FILE_LIMIT:
                    raise ExecutionError("A3L7 retained output exceeded cap")
            return observation, bytes(raw)
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)


def _a3l7_unlink_at(
    root_fd: int, relative: str, identity: Mapping[str, int],
) -> None:
    parts = _validate_relative_path(relative)
    directory = _a3l9_open_relative_directory(
        root_fd, parts[:-1], mode=0o700
    )
    try:
        try:
            metadata = os.stat(
                parts[-1], dir_fd=directory, follow_symlinks=False
            )
        except FileNotFoundError:
            return
        if (
            stat.S_ISREG(metadata.st_mode)
            and metadata.st_nlink == 1
            and metadata.st_dev == identity.get("device")
            and metadata.st_ino == identity.get("inode")
        ):
            os.unlink(parts[-1], dir_fd=directory)
            os.fsync(directory)
    finally:
        os.close(directory)


def _unlink_if_identity(path: Path, identity: Tuple[int, int]) -> None:
    """Remove only the exact regular file identity created by this process."""
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        return
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or (metadata.st_dev, metadata.st_ino) != identity
    ):
        return
    path.unlink()
    _fsync_directory(path.parent)


def _write_tracked_json(
    path: Path, value: Mapping[str, object]
) -> Tuple[int, int]:
    """Write one final authority file and clean it on any incomplete write."""
    descriptor = _exclusive_file(path)
    metadata = os.fstat(descriptor)
    identity = (metadata.st_dev, metadata.st_ino)
    try:
        view = memoryview(canonical_json_bytes(value))
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise ExecutionError("short final authority write")
            view = view[count:]
        os.fsync(descriptor)
    except BaseException:
        os.close(descriptor)
        _unlink_if_identity(path, identity)
        raise
    os.close(descriptor)
    _fsync_directory(path.parent)
    return identity


def _planned_not_run_observation(
    command: CommandSpec,
    *,
    plan_sha256: str,
    completion_ordinal: int,
    previous_observation_sha256: Optional[str],
) -> RawObservation:
    """Receipt one code-owned readiness role without opening or launching it."""
    expected_hashes = {
        DOCKER_EXE: DOCKER_SHA256,
        BUILDX_EXE: BUILDX_SHA256,
        CODE_SIGN_EXE: CODE_SIGN_SHA256,
    }
    executable_sha256 = expected_hashes.get(command.argv[0])
    if executable_sha256 is None:
        raise ExecutionError("readiness not-run executable is not code-owned")
    value = _observation_value(
        command=command,
        plan_sha256=plan_sha256,
        completion_ordinal=completion_ordinal,
        executable_sha256=executable_sha256,
        started_ns=0,
        ended_ns=0,
        outcome="not_run",
        exit_code=None,
        terminating_signal=None,
        stdout=b"",
        stderr=b"",
        previous_observation_sha256=previous_observation_sha256,
        container_id=None,
        raw_directory=None,
    )
    return RawObservation(value, b"", b"")


def _rejected_readiness_result(
    plan_sha256: str,
    observations: Sequence[RawObservation],
    descriptor_sets: Sequence[Mapping[str, object]],
    failure: str,
) -> Dict[str, object]:
    if len(observations) != 6 or len(descriptor_sets) != 2:
        raise ExecutionError("rejected readiness evidence census changed")
    unavailable = "0" * 64
    return {
        "schema": READINESS_RESULT_SCHEMA,
        "readiness_plan_sha256": plan_sha256,
        "ordered_observation_sha256": [item.digest for item in observations],
        "index_sha256": unavailable,
        "selected_descriptor": {
            "digest": "sha256:" + unavailable,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "size": 1,
            "os": "linux",
            "architecture": "arm64",
            "variant": "v8",
        },
        "selected_reference": "docker.io/library/python@sha256:" + unavailable,
        "platform_sha256": unavailable,
        "local_image_observation_sha256": observations[2].digest,
        "buildx_version_observation_sha256": observations[3].digest,
        "codesign_verify_observation_sha256": observations[4].digest,
        "codesign_display_observation_sha256": observations[5].digest,
        "ordered_descriptor_set_sha256": [
            _load_evidence_module().descriptor_set_digest(item)
            for item in descriptor_sets
        ],
        "context_sha256": unavailable,
        "image_config_digest": "sha256:" + unavailable,
        "rootfs_diff_ids": [],
        "accepted": False,
        "failure": failure,
    }


def _context_companion(
    observation: Mapping[str, object], raw: bytes
) -> Dict[str, object]:
    # Docker Desktop owns meta.json field order. Pin exact raw bytes via
    # validate_docker_context; do not require repository-canonical JSON.
    evidence = _load_evidence_module()
    try:
        parsed = evidence._parse_json_bytes(raw, max(len(raw), 1))
    except Exception as error:
        raise ExecutionError("Docker context is not valid JSON") from error
    if not isinstance(parsed, Mapping):
        raise ExecutionError("Docker context root is not an object")
    metadata = parsed.get("Metadata")
    endpoints = parsed.get("Endpoints")
    docker_endpoint = endpoints.get("docker") if isinstance(endpoints, Mapping) else None
    if (
        set(parsed) != {"Name", "Metadata", "Endpoints"}
        or not isinstance(metadata, Mapping)
        or set(metadata) != {"Description", "GODEBUG", "otel"}
        or not isinstance(endpoints, Mapping)
        or set(endpoints) != {"docker"}
        or not isinstance(docker_endpoint, Mapping)
        or set(docker_endpoint) != {"Host", "SkipTLSVerify"}
    ):
        raise ExecutionError("Docker context shape changed")
    value = {
        "schema": "hsai-p01b-docker-context-v1",
        "path": DOCKER_CONTEXT_PATH,
        "descriptor_observation": dict(observation),
        "descriptor_observation_sha256": evidence.descriptor_observation_digest(
            observation
        ),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "name": parsed.get("Name"),
        "host": docker_endpoint.get("Host"),
        "skip_tls_verify": docker_endpoint.get("SkipTLSVerify"),
    }
    evidence.validate_docker_context(value, raw)
    return value


@dataclass(frozen=True)
class ReadinessInputs:
    host_descriptor_set: Mapping[str, object]
    desktop_descriptor_set: Mapping[str, object]
    context: Mapping[str, object]
    context_raw: bytes
    info_raw: bytes


def _capture_readiness_inputs() -> ReadinessInputs:
    """Capture every local readiness input before the first planned command."""
    evidence = _load_evidence_module()
    host_observations = sorted(
        (
            capture_descriptor_observation(Path(DOCKER_EXE), "docker-client"),
            capture_descriptor_observation(Path(BUILDX_EXE), "buildx"),
            capture_descriptor_observation(Path(CODE_SIGN_EXE), "codesign"),
        ),
        key=lambda item: str(item["path"]).encode("ascii"),
    )
    info_observation, info_raw = _read_observed_regular(
        Path(DOCKER_DESKTOP_INFO_PLIST),
        "docker-desktop-info-plist",
        None,
        METADATA_CAP,
    )
    desktop_observations = sorted(
        (
            info_observation,
            capture_descriptor_observation(
                Path(DOCKER_DESKTOP_VM_PATH), "docker-desktop-vm"
            ),
            capture_descriptor_observation(
                Path(DOCKER_DESKTOP_KERNEL_PATH), "docker-desktop-kernel"
            ),
        ),
        key=lambda item: str(item["path"]).encode("ascii"),
    )
    context_observation, context_raw = _read_observed_regular(
        Path(DOCKER_CONTEXT_PATH), "docker-context", None, METADATA_CAP
    )
    host_set = build_descriptor_set("host-tools", host_observations)
    desktop_set = build_descriptor_set("docker-desktop", desktop_observations)
    evidence.validate_descriptor_set(host_set)
    evidence.validate_descriptor_set(desktop_set)
    context = _context_companion(context_observation, context_raw)
    return ReadinessInputs(host_set, desktop_set, context, context_raw, info_raw)


def _readiness_input_identity_failure(inputs: ReadinessInputs) -> Optional[str]:
    host_rows = {
        str(item["path"]): item
        for item in inputs.host_descriptor_set["ordered_observations"]
    }
    desktop_rows = {
        str(item["path"]): item
        for item in inputs.desktop_descriptor_set["ordered_observations"]
    }
    expected = {
        DOCKER_EXE: DOCKER_SHA256,
        BUILDX_EXE: BUILDX_SHA256,
        CODE_SIGN_EXE: CODE_SIGN_SHA256,
        DOCKER_DESKTOP_VM_PATH: DOCKER_DESKTOP_VM_SHA256,
        DOCKER_DESKTOP_KERNEL_PATH: DOCKER_DESKTOP_KERNEL_SHA256,
    }
    rows = {**host_rows, **desktop_rows}
    expected_paths = set(expected) | {DOCKER_DESKTOP_INFO_PLIST}
    if set(rows) != expected_paths:
        return "descriptor_drift"
    if any(
        rows[path].get("sha256") != digest for path, digest in expected.items()
    ):
        return "identity_drift"
    if inputs.context.get("sha256") != DOCKER_CONTEXT_SHA256:
        return "context_drift"
    return None


def _readiness_descriptor_recheck_failure(
    inputs: ReadinessInputs,
) -> Optional[str]:
    """Reopen every descriptor input and reject stable-capture drift prelaunch."""
    try:
        rechecked = _capture_readiness_inputs()
    except (ExecutionError, OSError):
        return "descriptor_drift"
    original_sets = (
        inputs.host_descriptor_set,
        inputs.desktop_descriptor_set,
    )
    rechecked_sets = (
        rechecked.host_descriptor_set,
        rechecked.desktop_descriptor_set,
    )
    if canonical_json_bytes(original_sets) != canonical_json_bytes(rechecked_sets):
        return "descriptor_drift"
    if (
        inputs.context_raw != rechecked.context_raw
        or inputs.info_raw != rechecked.info_raw
    ):
        return "descriptor_drift"
    return None


@dataclass(frozen=True)
class ReadinessMaterial:
    readiness_plan: Mapping[str, object]
    readiness_result: Mapping[str, object]
    preauthorization: Mapping[str, object]
    authorization: Optional[Mapping[str, object]]
    normal_plan: Optional[Mapping[str, object]]
    oom_plan: Optional[Mapping[str, object]]
    campaign_plan: Optional[Mapping[str, object]]
    observations: Tuple[RawObservation, ...]
    root: str


def execute_a3l7_readiness(
    *,
    readiness_plan: Mapping[str, object],
    a3l6_gate_bundle: Mapping[str, object],
    user_authorization_raw: bytes,
    campaign_id: str,
    output_root: Path,
    runner: Optional[Callable[..., RawObservation]] = None,
) -> ReadinessMaterial:
    """Retain the A3L7 output authority before observing any runtime input."""
    _require_absolute(str(output_root), "output_root")
    try:
        _load_evidence_module().validate_readiness_plan(readiness_plan)
    except Exception as error:
        raise ExecutionError(
            "readiness plan is not the canonical executable plan"
        ) from error
    output_root_fd = _a3l7_open_output_root(output_root)
    try:
        return _execute_a3l7_readiness_at(
            readiness_plan=readiness_plan,
            a3l6_gate_bundle=a3l6_gate_bundle,
            user_authorization_raw=user_authorization_raw,
            campaign_id=campaign_id,
            output_root=output_root,
            output_root_fd=output_root_fd,
            runner=runner,
        )
    finally:
        os.close(output_root_fd)


def _execute_a3l7_readiness_at(
    *,
    readiness_plan: Mapping[str, object],
    a3l6_gate_bundle: Mapping[str, object],
    user_authorization_raw: bytes,
    campaign_id: str,
    output_root: Path,
    output_root_fd: int,
    runner: Optional[Callable[..., RawObservation]] = None,
) -> ReadinessMaterial:
    """Construct authority, execute readiness, and retain the acyclic A3L7 DAG."""
    evidence = _load_evidence_module()
    if not isinstance(user_authorization_raw, bytes) or not user_authorization_raw:
        raise ExecutionError("user authorization must be exact nonempty bytes")
    try:
        user_authorization_raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ExecutionError("user authorization is not UTF-8") from error
    gate = validate_a3l6_gate_bundle(a3l6_gate_bundle)
    implementation_commit = gate.get("implementation_commit")
    implementation_tree = gate.get("implementation_tree")
    if not isinstance(implementation_commit, str) or not isinstance(
        implementation_tree, str
    ):
        raise ExecutionError("A3L6 implementation identity is absent")
    user_authorization_sha256 = sha256_bytes(user_authorization_raw)
    _require_absolute(str(output_root), "output_root")
    inputs = _capture_readiness_inputs()
    captured_host = inputs.context.get("host")
    captured_path = inputs.context.get("path")
    if not isinstance(captured_host, str) or not isinstance(captured_path, str):
        raise ExecutionError("captured Docker context identity is absent")
    plan, config_root, host_uri, temporary_root = _canonical_readiness_plan(
        readiness_plan,
        user_authorization_sha256,
        context_path=captured_path,
        host_uri=captured_host,
        output_root=output_root,
    )
    _require_identifier(campaign_id, "campaign_id")
    claim_boundary = canonical_claim_boundary()
    try:
        action_document = evidence.build_gateway_action_document(
            user_authorization_raw,
            implementation_commit,
            implementation_tree,
            gate,
            plan,
            claim_boundary,
        )
        policy_document = evidence.build_gateway_policy_document(
            implementation_commit,
            implementation_tree,
            plan,
            claim_boundary,
        )
        evidence_bundle = evidence.build_gateway_evidence_bundle_document(
            action_document, policy_document
        )
        admission_decision = evidence.build_gateway_admission_decision_document(
            action_document, policy_document, evidence_bundle
        )
        preauthorization = {
            "schema": PREAUTHORIZATION_SCHEMA,
            "user_authorization_sha256": user_authorization_sha256,
            "predecessor_commit": plan["predecessor_commit"],
            "action_sha256": evidence.gateway_action_document_digest(
                action_document
            ),
            "policy_sha256": evidence.gateway_policy_document_digest(
                policy_document
            ),
            "evidence_bundle_sha256": evidence.gateway_evidence_bundle_document_digest(
                evidence_bundle, action_document, policy_document
            ),
            "a3l6_gate_bundle_sha256": evidence.a3l6_gate_bundle_digest(gate),
            "admission_decision_sha256": evidence.gateway_admission_decision_document_digest(
                admission_decision,
                action_document,
                policy_document,
                evidence_bundle,
            ),
            "implementation_commit": implementation_commit,
            "implementation_tree": implementation_tree,
            "readiness_plan_sha256": evidence.readiness_plan_digest(plan),
        }
        evidence.validate_preauthorization_graph(
            user_authorization_raw,
            action_document,
            policy_document,
            evidence_bundle,
            admission_decision,
            gate,
            plan,
            claim_boundary,
            preauthorization,
        )
    except Exception as error:
        raise ExecutionError("A3L5H preauthorization graph was rejected") from error
    for directory in (
        "authority",
        "readiness",
        "provenance",
        "snapshot",
        READINESS_TEMP_BASENAME,
    ):
        _a3l7_create_directory(output_root_fd, directory)
    _a3l7_create_directory(output_root_fd, READINESS_TEMP_BASENAME + "/" + HOST_HOME_BASENAME)
    authority_documents = {
        "action.json": action_document,
        "policy.json": policy_document,
        "evidence-bundle.json": evidence_bundle,
        "a3l6-gate-bundle.json": gate,
        "admission-decision.json": admission_decision,
    }
    for name, value in authority_documents.items():
        _a3l7_write_at(
            output_root_fd, "authority/" + name, canonical_json_bytes(value)
        )
    _a3l7_write_at(
        output_root_fd, "authority/user-authorization.txt",
        user_authorization_raw,
    )
    _a3l7_write_at(
        output_root_fd, "readiness/preauthorization-plan.json",
        canonical_json_bytes(preauthorization),
    )
    snapshot = _create_a3l7_snapshot_at(
        gate, output_root, output_root_fd
    )
    _a3l7_write_at(
        output_root_fd, "snapshot/source-manifest.json",
        canonical_json_bytes(snapshot.pair),
    )
    _a3l7_write_at(
        output_root_fd, "snapshot/source-descriptor-observations.json",
        canonical_json_bytes(snapshot.source_descriptor_set),
    )
    _a3l7_write_at(
        output_root_fd, "snapshot/ingress-observations.json",
        canonical_json_bytes(snapshot.snapshot_descriptor_set),
    )
    _a3l7_write_at(
        output_root_fd, "provenance/docker-context.json",
        canonical_json_bytes(inputs.context),
    )
    _a3l7_write_at(
        output_root_fd, "provenance/docker-context.raw", inputs.context_raw
    )
    _a3l7_write_at(
        output_root_fd, "provenance/info-plist.raw", inputs.info_raw
    )

    plan_sha256 = evidence.readiness_plan_digest(plan)
    raw_root = output_root / "operations/readiness"
    _a3l7_create_directory(output_root_fd, "operations/readiness")
    execute = execute_direct if runner is None else runner
    commands_value = plan.get("commands")
    if not isinstance(commands_value, list) or len(commands_value) != 6:
        raise ExecutionError("readiness command set changed")
    planned_commands = [command_from_mapping(item) for item in commands_value]
    active_commands = list(planned_commands)
    observations: List[RawObservation] = []

    def retain(observation: RawObservation) -> RawObservation:
        retained = _retain_readiness_observation(
            output_root, output_root_fd, observation, len(observations),
            evidence,
        )
        observations.append(retained)
        return retained

    def append_not_run_suffix() -> None:
        while len(observations) < 6:
            index = len(observations)
            prior = observations[-1].digest if observations else None
            retain(
                _planned_not_run_observation(
                    planned_commands[index],
                    plan_sha256=plan_sha256,
                    completion_ordinal=index,
                    previous_observation_sha256=prior,
                )
            )

    def reject(failure: str) -> ReadinessMaterial:
        append_not_run_suffix()
        items = tuple((item.value, item.stdout, item.stderr) for item in observations)
        receipts = evidence.build_receipt_chain("readiness", plan, items)
        result = _rejected_readiness_result(
            plan_sha256,
            observations,
            (inputs.host_descriptor_set, inputs.desktop_descriptor_set),
            failure,
        )
        evidence.validate_readiness_graph(
            plan,
            result,
            items,
            inputs.host_descriptor_set,
            inputs.desktop_descriptor_set,
            {},
            inputs.context,
            inputs.context_raw,
            {},
            receipts,
        )
        _a3l7_write_at(
            output_root_fd, "readiness/readiness-result.json",
            canonical_json_bytes(result),
        )
        _a3l7_write_at(
            output_root_fd, "readiness/receipts.json",
            canonical_json_bytes(receipts),
        )
        os.fsync(output_root_fd)
        return ReadinessMaterial(
            plan,
            result,
            preauthorization,
            None,
            None,
            None,
            None,
            tuple(observations),
            str(output_root),
        )

    input_failure = _readiness_input_identity_failure(inputs)
    if input_failure is None:
        input_failure = _readiness_descriptor_recheck_failure(inputs)
    if input_failure is not None:
        return reject(input_failure)

    def launch(index: int) -> RawObservation:
        prior = observations[-1].digest if observations else None
        _require_logical_directory_fd(
            output_root, output_root_fd, "A3L7 output root"
        )
        try:
            raw = execute(
                active_commands[index],
                plan_sha256=plan_sha256,
                completion_ordinal=index,
                previous_observation_sha256=prior,
                raw_root=None,
            )
        except Exception as error:
            raise ExecutionError("readiness executable identity or launch failed") from error
        _require_logical_directory_fd(
            output_root, output_root_fd, "A3L7 output root"
        )
        return retain(raw)

    try:
        index_observation = launch(0)
    except ExecutionError:
        return reject("identity_drift")
    if (
        index_observation.value.get("outcome") != "exit"
        or index_observation.value.get("exit_code") != 0
        or index_observation.stderr != b""
        or sha256_bytes(index_observation.stdout)
        != INDEX_REFERENCE.rsplit(":", 1)[1]
    ):
        return reject("registry_failed")
    try:
        selected_descriptor = _select_platform_descriptor(index_observation.stdout)
    except ExecutionError:
        return reject("selection_failed")
    selected_reference = "docker.io/library/python@" + str(
        selected_descriptor["digest"]
    )
    resolved = resolve_readiness_plan(plan, selected_reference)
    resolved_rows = resolved.get("commands")
    if not isinstance(resolved_rows, list) or len(resolved_rows) != 6:
        raise ExecutionError("resolved readiness command set changed")
    active_commands = [command_from_mapping(item) for item in resolved_rows]

    try:
        platform_observation = launch(1)
    except ExecutionError:
        return reject("identity_drift")
    if (
        platform_observation.value.get("outcome") != "exit"
        or platform_observation.value.get("exit_code") != 0
        or platform_observation.stderr != b""
    ):
        return reject("platform_digest_failed")
    try:
        platform_manifest = _validate_platform_manifest(
            platform_observation.stdout, selected_descriptor
        )
    except ExecutionError:
        return reject("platform_digest_failed")

    try:
        local_observation = launch(2)
    except ExecutionError:
        return reject("identity_drift")
    if (
        local_observation.value.get("outcome") != "exit"
        or local_observation.value.get("exit_code") != 0
        or local_observation.stderr != b""
    ):
        return reject("local_resolution_failed")
    try:
        _validate_local_image(local_observation.stdout, selected_reference)
    except ExecutionError:
        return reject("local_resolution_failed")

    try:
        buildx_observation = launch(3)
    except ExecutionError:
        return reject("identity_drift")
    expected_buildx = b"github.com/docker/buildx v0.34.1-desktop.1 c79576280a671664e17eb68da98ec3136b614aed\n"
    if (
        buildx_observation.value.get("outcome") != "exit"
        or buildx_observation.value.get("exit_code") != 0
        or buildx_observation.stdout != expected_buildx
        or buildx_observation.stderr != b""
    ):
        return reject("version_transcript_drift")

    try:
        verify_observation = launch(4)
    except ExecutionError:
        return reject("identity_drift")
    if (
        verify_observation.value.get("outcome") != "exit"
        or verify_observation.value.get("exit_code") != 0
        or verify_observation.stdout != b""
    ):
        return reject("signature_drift")
    try:
        verify_facts = parse_codesign_verify(verify_observation.stderr)
    except ExecutionError:
        return reject("signature_drift")

    try:
        display_observation = launch(5)
    except ExecutionError:
        return reject("identity_drift")
    if (
        display_observation.value.get("outcome") != "exit"
        or display_observation.value.get("exit_code") != 0
        or display_observation.stdout != b""
    ):
        return reject("signature_drift")
    try:
        display_facts = parse_codesign_display(display_observation.stderr)
    except ExecutionError:
        return reject("signature_drift")

    transcript_bindings = {
        "registry-index": _transcript_binding(
            "registry-index",
            index_observation,
            _strict_object(index_observation.stdout, "registry index"),
        ),
        "registry-platform": _transcript_binding(
            "registry-platform", platform_observation, platform_manifest
        ),
        "codesign-verify": _transcript_binding(
            "codesign-verify", verify_observation, verify_facts
        ),
        "codesign-display": _transcript_binding(
            "codesign-display", display_observation, display_facts
        ),
    }
    for kind, binding in transcript_bindings.items():
        source = {
            "registry-index": index_observation,
            "registry-platform": platform_observation,
            "codesign-verify": verify_observation,
            "codesign-display": display_observation,
        }[kind]
        evidence.validate_transcript_binding(
            binding, source.value, source.stdout, source.stderr
        )
    try:
        info = plistlib.loads(inputs.info_raw)
    except (plistlib.InvalidFileException, ValueError) as error:
        raise ExecutionError("Docker Desktop Info.plist is invalid") from error
    if not isinstance(info, Mapping):
        raise ExecutionError("Docker Desktop Info.plist is not a dictionary")
    desktop_facts = {
        "info_plist_sha256": sha256_bytes(inputs.info_raw),
        "bundle_version": info.get("CFBundleVersion"),
        "short_version": info.get("CFBundleShortVersionString"),
        "vm_image_sha256": DOCKER_DESKTOP_VM_SHA256,
        "kernel_sha256": DOCKER_DESKTOP_KERNEL_SHA256,
        "codesign_verify_sha256": verify_observation.digest,
        "codesign_display_sha256": display_observation.digest,
        "candidate_cdhash_full": display_facts["candidate_cdhash_full"],
        "team_identifier": display_facts["team_identifier"],
    }
    buildx_facts = {
        "path": BUILDX_EXE,
        "sha256": BUILDX_SHA256,
        "version": "v0.34.1-desktop.1",
        "revision": "c79576280a671664e17eb68da98ec3136b614aed",
        "buildx_version_stdout_sha256": sha256_bytes(expected_buildx),
    }
    readiness_provenance = {
        "docker-desktop": _host_provenance(
            "docker-desktop",
            (verify_observation, display_observation),
            inputs.desktop_descriptor_set,
            desktop_facts,
            ("host-driver-honest", "signed-docker-app-honest"),
        ),
        "buildx": _host_provenance(
            "buildx",
            (buildx_observation,),
            inputs.host_descriptor_set,
            buildx_facts,
            ("host-driver-honest",),
        ),
    }
    evidence.validate_host_provenance(
        readiness_provenance["docker-desktop"],
        (verify_observation.value, display_observation.value),
        inputs.info_raw,
    )
    evidence.validate_host_provenance(
        readiness_provenance["buildx"], (buildx_observation.value,)
    )
    items = tuple((item.value, item.stdout, item.stderr) for item in observations)
    receipts = evidence.build_receipt_chain("readiness", plan, items)
    readiness_result: Dict[str, object] = {
        "schema": READINESS_RESULT_SCHEMA,
        "readiness_plan_sha256": plan_sha256,
        "ordered_observation_sha256": [item.digest for item in observations],
        "index_sha256": sha256_bytes(index_observation.stdout),
        "selected_descriptor": dict(selected_descriptor),
        "selected_reference": selected_reference,
        "platform_sha256": sha256_bytes(platform_observation.stdout),
        "local_image_observation_sha256": local_observation.digest,
        "buildx_version_observation_sha256": buildx_observation.digest,
        "codesign_verify_observation_sha256": verify_observation.digest,
        "codesign_display_observation_sha256": display_observation.digest,
        "ordered_descriptor_set_sha256": [
            evidence.descriptor_set_digest(inputs.host_descriptor_set),
            evidence.descriptor_set_digest(inputs.desktop_descriptor_set),
        ],
        "context_sha256": sha256_bytes(inputs.context_raw),
        "image_config_digest": IMAGE_CONFIG_DIGEST,
        "rootfs_diff_ids": list(ROOTFS_DIFF_IDS),
        "accepted": True,
        "failure": None,
    }
    evidence.validate_readiness_graph(
        plan,
        readiness_result,
        items,
        inputs.host_descriptor_set,
        inputs.desktop_descriptor_set,
        transcript_bindings,
        inputs.context,
        inputs.context_raw,
        readiness_provenance,
        receipts,
    )
    expected_bindings = _build_expected_bindings(
        readiness_plan=plan,
        user_authorization_sha256=user_authorization_sha256,
        gate_bundle=gate,
        snapshot=snapshot,
        selected_descriptor=selected_descriptor,
        platform_manifest=platform_manifest,
        platform_raw=platform_observation.stdout,
        index_raw=index_observation.stdout,
        context_raw=inputs.context_raw,
        info_plist_sha256=sha256_bytes(inputs.info_raw),
        display_facts=display_facts,
    )
    expected_bindings_sha256 = evidence.expected_bindings_digest(
        expected_bindings
    )
    readiness_sha256 = evidence.readiness_result_digest(readiness_result)
    authorization_root = {
        "schema": AUTHORIZATION_ROOT_SCHEMA,
        "user_authorization_sha256": user_authorization_sha256,
        "action_sha256": preauthorization["action_sha256"],
        "policy_sha256": preauthorization["policy_sha256"],
        "evidence_bundle_sha256": preauthorization["evidence_bundle_sha256"],
        "a3l6_gate_bundle_sha256": preauthorization["a3l6_gate_bundle_sha256"],
        "admission_decision_sha256": preauthorization[
            "admission_decision_sha256"
        ],
        "preauthorization_sha256": evidence.preauthorization_digest(
            preauthorization
        ),
        "expected_bindings_sha256": expected_bindings_sha256,
        "readiness_sha256": readiness_sha256,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "authority_granted": True,
    }
    evidence.validate_authorization_root(authorization_root)
    proposal = action_document.get("proposal")
    if not isinstance(proposal, Mapping) or not isinstance(proposal.get("id"), str):
        raise ExecutionError("A3L5H action id is absent")
    authorization = {
        "schema": AUTHORIZATION_SCHEMA,
        "authorization_id": proposal["id"],
        "authorization_root_sha256": evidence.authorization_root_digest(
            authorization_root
        ),
        "user_authorization_sha256": user_authorization_sha256,
        "action_sha256": preauthorization["action_sha256"],
        "policy_sha256": preauthorization["policy_sha256"],
        "evidence_bundle_sha256": preauthorization["evidence_bundle_sha256"],
        "a3l6_gate_bundle_sha256": preauthorization["a3l6_gate_bundle_sha256"],
        "admission_decision_sha256": preauthorization[
            "admission_decision_sha256"
        ],
        "expected_bindings_sha256": expected_bindings_sha256,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "readiness_sha256": readiness_sha256,
    }
    evidence.validate_authorization(authorization)
    authorization_sha256 = evidence.authorization_digest(authorization)
    snapshot_root = snapshot.root
    seccomp_path = str(
        Path(snapshot_root)
        / "tools/hsai-formal-preflight/p01b_container_seccomp.json"
    )
    common = {
        "campaign_id": campaign_id,
        "authorization_sha256": authorization_sha256,
        "implementation_commit": implementation_commit,
        "platform_reference": selected_reference,
        "source_manifest_sha256": snapshot.copy_manifest_sha256,
        "config_root": config_root,
        "host_uri": host_uri,
        "temporary_root": temporary_root,
        "snapshot_root": snapshot_root,
        "seccomp_path": seccomp_path,
    }
    normal_plan = build_attempt_plan(attempt_id="normal", **common)
    oom_plan = build_attempt_plan(attempt_id="oom", **common)
    evidence.validate_attempt_plan(normal_plan)
    evidence.validate_attempt_plan(oom_plan)
    environment = closed_host_environment(config_root, temporary_root)
    campaign_plan = build_campaign_plan(
        campaign_id=campaign_id,
        authorization_sha256=authorization_sha256,
        implementation_commit=implementation_commit,
        readiness_plan_sha256=plan_sha256,
        native_command=build_native_command(snapshot_root, environment),
        metadata_commands=build_metadata_commands(
            docker_prefix(config_root, host_uri), environment
        ),
        normal_plan_sha256=evidence.attempt_plan_digest(normal_plan),
        oom_plan_sha256=evidence.attempt_plan_digest(oom_plan),
    )
    evidence.validate_campaign_plan(campaign_plan)
    evidence.validate_authority_graph(
        user_authorization_raw,
        action_document,
        policy_document,
        evidence_bundle,
        admission_decision,
        gate,
        plan,
        claim_boundary,
        preauthorization,
        expected_bindings,
        readiness_result,
        authorization_root,
        authorization,
        campaign_plan,
        normal_plan,
        oom_plan,
    )
    _a3l7_create_directory(output_root_fd, "provenance/registry")
    _a3l7_create_directory(output_root_fd, "provenance/signature")
    prerequisite_documents = {
        "readiness/readiness-result.json": readiness_result,
        "readiness/receipts.json": receipts,
        "authority/expected-bindings.json": expected_bindings,
        "provenance/docker-desktop.json": readiness_provenance["docker-desktop"],
        "provenance/buildx.json": readiness_provenance["buildx"],
        "provenance/registry/index.json": transcript_bindings["registry-index"],
        "provenance/registry/platform-manifest.json": transcript_bindings[
            "registry-platform"
        ],
        "provenance/signature/verify.json": transcript_bindings[
            "codesign-verify"
        ],
        "provenance/signature/display.json": transcript_bindings[
            "codesign-display"
        ],
    }
    for relative, value in prerequisite_documents.items():
        _a3l7_write_at(
            output_root_fd, relative, canonical_json_bytes(value)
        )
    _a3l7_fsync_directory(output_root_fd, "readiness")
    _a3l7_fsync_directory(output_root_fd, "authority")
    _a3l7_fsync_directory(output_root_fd, "provenance")
    os.fsync(output_root_fd)
    _require_logical_directory_fd(
        output_root, output_root_fd, "A3L7 output root"
    )

    final_documents = (
        ("authority/authorization-root.json", authorization_root),
        ("readiness/authorization.json", authorization),
        ("readiness/campaign-plan.json", campaign_plan),
        ("readiness/normal-plan.json", normal_plan),
        ("readiness/oom-plan.json", oom_plan),
    )
    written_final: List[Tuple[str, Mapping[str, int]]] = []
    try:
        for relative, value in final_documents:
            identity = _a3l7_write_at(
                output_root_fd, relative, canonical_json_bytes(value)
            )
            written_final.append((relative, identity))
        _a3l7_fsync_directory(output_root_fd, "authority")
        _a3l7_fsync_directory(output_root_fd, "readiness")
        os.fsync(output_root_fd)
        _require_logical_directory_fd(
            output_root, output_root_fd, "A3L7 output root"
        )
    except BaseException:
        for relative, identity in reversed(written_final):
            try:
                _a3l7_unlink_at(output_root_fd, relative, identity)
            except OSError:
                pass
        os.fsync(output_root_fd)
        raise
    return ReadinessMaterial(
        plan,
        readiness_result,
        preauthorization,
        authorization,
        normal_plan,
        oom_plan,
        campaign_plan,
        tuple(observations),
        str(output_root),
    )


@dataclass(frozen=True)
class AttemptExecution:
    attempt_id: str
    container_id: str
    intent: Mapping[str, object]
    cid_binding: Mapping[str, object]
    timing: Mapping[str, object]
    result: Mapping[str, object]
    receipts: Mapping[str, object]
    readiness_event: Mapping[str, object]
    certificates: Tuple[Mapping[str, object], ...]
    observations: Tuple[RawObservation, ...]
    export_tar: bytes


READINESS_OPERATION_ROLES = (
    "registry-index", "registry-platform", "local-platform", "buildx-version",
    "codesign-verify", "codesign-display",
)
CAMPAIGN_OPERATION_ROLES = (
    "native-reference", "docker-version", "docker-info", "image-config",
)
ATTEMPT_COMPLETION_ROLES = (
    "absence-name-pre", "absence-label-pre", "create", "inspect-prestart",
    "export-running", "release", "start-attach", "emergency-kill", "wait",
    "inspect-terminal", "remove", "absence-cid", "absence-name", "absence-label",
    "daemon-recheck",
)


def candidate_payload_paths(source_paths: Sequence[str] = SOURCE_PATHS) -> Tuple[str, ...]:
    """Return the bytewise-sorted exact 201-file A3L8 payload grammar."""
    if tuple(source_paths) != SOURCE_PATHS:
        raise ExecutionError("candidate source path set changed")
    paths = {
        *("authority/%s.json" % name for name in (
            "action", "policy", "evidence-bundle", "a3l6-gate-bundle",
            "admission-decision", "authorization-root", "expected-bindings",
        )),
        "authority/user-authorization.txt",
        *("readiness/%s.json" % name for name in (
            "preauthorization-plan", "readiness-result", "authorization",
            "campaign-plan", "normal-plan", "oom-plan", "receipts",
        )),
        *("provenance/%s.json" % name for name in (
            "git", "docker-desktop", "docker-client", "buildx", "docker-daemon",
            "docker-context", "image-config", "rootfs",
        )),
        "provenance/docker-context.raw",
        "provenance/info-plist.raw",
        "provenance/registry/index.json",
        "provenance/registry/platform-manifest.json",
        "provenance/signature/verify.json",
        "provenance/signature/display.json",
        *("snapshot/%s.json" % name for name in (
            "source-manifest", "source-descriptor-observations",
            "ingress-observations", "ingress-certificates",
        )),
        *("snapshot/files/" + path for path in source_paths),
        "reference/native-result.json",
        "reference/projection.json",
        "reference/receipts.json",
        "publication/prepublication-descriptor-plan.json",
    }
    for namespace, roles in (
        ("readiness", READINESS_OPERATION_ROLES),
        ("campaign", CAMPAIGN_OPERATION_ROLES),
        ("normal", ATTEMPT_COMPLETION_ROLES),
        ("oom", ATTEMPT_COMPLETION_ROLES),
    ):
        for ordinal, role in enumerate(roles):
            base = "operations/%s/%03d-%s" % (namespace, ordinal, role)
            paths.update((base + "/observation.json", base + "/stdout.bin", base + "/stderr.bin"))
    attempt_names = (
        "intent", "cid-binding", "timing", "receipts", "result", "readiness-event",
        "inspect-prestart", "inspect-terminal", "egress-certificate", "cleanup-certificate",
    )
    for attempt in ("normal", "oom"):
        paths.update("attempts/%s/%s.json" % (attempt, name) for name in attempt_names)
        paths.add("attempts/%s/export.tar" % attempt)
    result = tuple(sorted(paths, key=lambda item: item.encode("ascii")))
    if len(result) != CANDIDATE_PAYLOAD_COUNT:
        raise ExecutionError("candidate payload census is not exactly 201")
    return result


def candidate_directory_paths(payload_paths: Sequence[str]) -> Tuple[str, ...]:
    directories = {"."}
    for relative in payload_paths:
        _validate_relative_path(relative)
        parts = relative.split("/")[:-1]
        for count in range(1, len(parts) + 1):
            directories.add("/".join(parts[:count]))
    result = tuple(sorted(directories, key=lambda item: (item != ".", item.encode("ascii"))))
    if tuple(payload_paths) == candidate_payload_paths() and len(result) != CANDIDATE_DIRECTORY_COUNT:
        raise ExecutionError("candidate directory census is not exactly 62")
    return result


def materialize_exact_candidate(
    root: Path,
    payloads: Mapping[str, bytes],
    *,
    authorization_sha256: str,
    implementation_commit: str,
) -> Dict[str, object]:
    """Exclusively write the exact 201 payloads and file-202 manifest."""
    _require_hex64(authorization_sha256, "authorization_sha256")
    _require_git(implementation_commit, "implementation_commit")
    expected = candidate_payload_paths()
    if tuple(sorted(payloads, key=lambda item: item.encode("ascii"))) != expected:
        raise ExecutionError("candidate payload mapping differs from exact grammar")
    if any(not isinstance(value, bytes) for value in payloads.values()):
        raise ExecutionError("candidate payload values must be complete bytes")
    root = Path(os.path.abspath(str(root)))
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    try:
        entries: List[Mapping[str, object]] = []
        aggregate_bytes = 0
        for relative in expected:
            raw = payloads[relative]
            aggregate_bytes += len(raw)
            if aggregate_bytes > 134_217_728:
                raise ExecutionError("candidate aggregate byte cap exceeded")
            _write_candidate_value(root, relative, raw)
            metadata = os.lstat(root / relative)
            entries.append({
                "path": relative,
                "file_type": "regular",
                "mode": stat.S_IMODE(metadata.st_mode),
                "link_count": metadata.st_nlink,
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
            })
        manifest = {
            "schema": "hsai-p01b-container-candidate-manifest-v1",
            "authorization_sha256": authorization_sha256,
            "implementation_commit": implementation_commit,
            "entries": entries,
        }
        _write_candidate_value(root, "candidate-manifest.json", manifest)
        files = [
            path.relative_to(root).as_posix()
            for path in root.rglob("*") if path.is_file()
        ]
        if len(files) != CANDIDATE_FILE_COUNT or len(candidate_directory_paths(expected)) != CANDIDATE_DIRECTORY_COUNT:
            raise ExecutionError("materialized candidate census changed")
        return manifest
    except BaseException:
        shutil.rmtree(root, ignore_errors=True)
        raise


def canonical_claim_boundary() -> Dict[str, object]:
    return {
        "schema": "hsai-p01b-local-claim-boundary-v1",
        "evidence_level": "Level1LocalReplayOrLower",
        "ordered_honesty_assumptions": list(CLAIM_ASSUMPTIONS),
        "ordered_nonclaims": list(CLAIM_NONCLAIMS),
    }


def claim_boundary_digest(value: Mapping[str, object]) -> str:
    if dict(value) != canonical_claim_boundary():
        raise ExecutionError("claim boundary fields or order changed")
    return domain_sha256("hsai:p01b-local-claim-boundary:v1", value)


def build_prepublication_descriptor_plan(
    *, candidate_root: str, parent_identity: Mapping[str, object],
    staging_identity: Mapping[str, object]
) -> Dict[str, object]:
    _require_absolute(candidate_root, "candidate_root")
    return {
        "schema": "hsai-p01b-prepublication-descriptor-plan-v1",
        "candidate_root": candidate_root,
        "parent_identity": dict(parent_identity),
        "staging_identity": dict(staging_identity),
        "expected_file_count": CANDIDATE_FILE_COUNT,
        "expected_manifest_path": candidate_root + "/candidate-manifest.json",
        "overwrite_policy": "exclusive",
    }


def build_postpublication_decision(
    *, authorization_sha256: str, implementation_commit: str,
    candidate_manifest_sha256: str, expected_bindings_sha256: str,
    claim_boundary_sha256: str, repository_state_sha256: str,
    publication_record_sha256: str, class_results: Sequence[Mapping[str, object]]
) -> Dict[str, object]:
    for field, value in (
        ("authorization_sha256", authorization_sha256),
        ("candidate_manifest_sha256", candidate_manifest_sha256),
        ("expected_bindings_sha256", expected_bindings_sha256),
        ("claim_boundary_sha256", claim_boundary_sha256),
        ("repository_state_sha256", repository_state_sha256),
        ("publication_record_sha256", publication_record_sha256),
    ):
        _require_hex64(value, field)
    _require_git(implementation_commit, "implementation_commit")
    expected_rows = [{"class_id": item, "closed": True} for item in CLASS_ORDER]
    rows = [dict(item) for item in class_results]
    if len(rows) != 8 or [item.get("class_id") for item in rows] != list(CLASS_ORDER):
        raise ExecutionError("decision class order changed")
    if any(set(item) != {"class_id", "closed"} or type(item["closed"]) is not bool for item in rows):
        raise ExecutionError("decision class row changed")
    accepted = rows == expected_rows
    return {
        "schema": "hsai-p01b-container-decision-v3",
        "authorization_sha256": authorization_sha256,
        "implementation_commit": implementation_commit,
        "candidate_manifest_sha256": candidate_manifest_sha256,
        "expected_bindings_sha256": expected_bindings_sha256,
        "claim_boundary_sha256": claim_boundary_sha256,
        "repository_state_sha256": repository_state_sha256,
        "publication_record_sha256": publication_record_sha256,
        "class_results": rows,
        "atomic_result": "accept" if accepted else "reject",
        "evidence_level": "Level1LocalReplayOrLower",
        "accepted_evidence_created": False,
        "level2_plus_created": False,
        "authority_granted": False,
    }


def build_publication_record_v2(
    *, candidate_manifest_sha256: str, repository_state_sha256: str,
    staging_path: str, final_path: str, parent_identity: Mapping[str, object],
    prepublication_inventory_sha256: str, postpublication_inventory_sha256: str,
    staging_identity: Mapping[str, object], final_identity: Mapping[str, object],
    ordered_file_reopens: Sequence[Mapping[str, object]],
    ordered_publication_events: Sequence[Mapping[str, object]],
    final_manifest_sha256: str
) -> Dict[str, object]:
    for field, value in (
        ("candidate_manifest_sha256", candidate_manifest_sha256),
        ("repository_state_sha256", repository_state_sha256),
        ("prepublication_inventory_sha256", prepublication_inventory_sha256),
        ("postpublication_inventory_sha256", postpublication_inventory_sha256),
        ("final_manifest_sha256", final_manifest_sha256),
    ):
        _require_hex64(value, field)
    _require_absolute(staging_path, "staging_path")
    _require_absolute(final_path, "final_path")
    if len(ordered_file_reopens) != CANDIDATE_FILE_COUNT:
        raise ExecutionError("publication must reopen exactly 202 files")
    if len(ordered_publication_events) != PUBLICATION_EVENT_COUNT:
        raise ExecutionError("publication must retain exactly 271 events")
    operations = [event.get("operation") for event in ordered_publication_events]
    expected_operations = (
        ["payload-file-fsync"] * CANDIDATE_PAYLOAD_COUNT
        + ["candidate-manifest-fsync"]
        + ["candidate-directory-fsync"] * CANDIDATE_DIRECTORY_COUNT
        + ["prepublication-inventory", "renameatx-np", "final-parent-fsync",
           "staging-absence", "final-root-reopen", "postpublication-inventory",
           "final-manifest-read"]
    )
    if operations != expected_operations:
        raise ExecutionError("publication event operation order changed")
    if prepublication_inventory_sha256 != postpublication_inventory_sha256:
        raise ExecutionError("publication inventories differ")
    if final_manifest_sha256 != candidate_manifest_sha256:
        raise ExecutionError("final manifest does not bind candidate manifest")
    if (staging_identity.get("device"), staging_identity.get("inode")) != (
        final_identity.get("device"), final_identity.get("inode")
    ):
        raise ExecutionError("publication root identity changed")
    return {
        "schema": PUBLICATION_SCHEMA,
        "candidate_manifest_sha256": candidate_manifest_sha256,
        "repository_state_sha256": repository_state_sha256,
        "staging_path": staging_path,
        "final_path": final_path,
        "parent_identity": dict(parent_identity),
        "prepublication_inventory_sha256": prepublication_inventory_sha256,
        "postpublication_inventory_sha256": postpublication_inventory_sha256,
        "staging_identity": dict(staging_identity),
        "final_identity": dict(final_identity),
        "ordered_file_reopens": list(ordered_file_reopens),
        "ordered_publication_events": list(ordered_publication_events),
        "final_manifest_sha256": final_manifest_sha256,
    }


def review_session_id(challenge: bytes, candidate_decision_sha256: str) -> str:
    if not isinstance(challenge, bytes) or len(challenge) != 32:
        raise ExecutionError("review challenge must be exactly 32 bytes")
    _require_hex64(candidate_decision_sha256, "candidate_decision_sha256")
    return sha256_bytes(
        b"hsai:p01b-review-session-id:v1\0"
        + challenge
        + bytes.fromhex(candidate_decision_sha256)
    )


def build_review_session(
    *, challenge: bytes, candidate_manifest_sha256: str,
    candidate_decision_sha256: str, decision_file_identity: Mapping[str, object],
    decision_file_sha256: str, created_monotonic_ns: int
) -> Dict[str, object]:
    for field, value in (
        ("candidate_manifest_sha256", candidate_manifest_sha256),
        ("candidate_decision_sha256", candidate_decision_sha256),
        ("decision_file_sha256", decision_file_sha256),
    ):
        _require_hex64(value, field)
    if isinstance(created_monotonic_ns, bool) or not isinstance(created_monotonic_ns, int) or created_monotonic_ns < 0:
        raise ExecutionError("review session time is invalid")
    return {
        "schema": "hsai-p01b-review-session-v1",
        "session_id": review_session_id(challenge, candidate_decision_sha256),
        "challenge_hex": challenge.hex(),
        "candidate_manifest_sha256": candidate_manifest_sha256,
        "candidate_decision_sha256": candidate_decision_sha256,
        "decision_file_identity": dict(decision_file_identity),
        "decision_file_sha256": decision_file_sha256,
        "created_monotonic_ns": created_monotonic_ns,
    }


def review_session_paths(root: Path, manifest_sha256: str, session_id: str) -> Dict[str, str]:
    _require_hex64(manifest_sha256, "candidate_manifest_sha256")
    _require_hex64(session_id, "session_id")
    base = Path(os.path.abspath(str(root))) / manifest_sha256 / session_id
    result = {
        "review_session": str(base / "review-session.json"),
        "review_session_durability": str(base / "review-session-durability.json"),
        "review_aggregate": str(base / "review-aggregate.json"),
        "acceptance_record": str(base / "acceptance-record.json"),
    }
    for role in REVIEW_ROLE_ORDER:
        result[role + "_receipt"] = str(base / role / "fresh-validation-receipt.json")
        result[role + "_review"] = str(base / role / "review.json")
        result[role + "_launch"] = str(base / role / "review-launch.json")
    return result


def build_review_launch(
    *, review_session_sha256: str, review_session_durability_sha256: str,
    claim_boundary_sha256: str, role: str, reviewer_id: str,
    command_observation: Mapping[str, object], receipt_path: str, receipt_raw: bytes,
    receipt_domain_sha256: str, review_path: str, review_raw: bytes,
    review_domain_sha256: str
) -> Dict[str, object]:
    for field, value in (
        ("review_session_sha256", review_session_sha256),
        ("review_session_durability_sha256", review_session_durability_sha256),
        ("claim_boundary_sha256", claim_boundary_sha256),
        ("receipt_domain_sha256", receipt_domain_sha256),
        ("review_domain_sha256", review_domain_sha256),
    ):
        _require_hex64(value, field)
    if role not in REVIEW_ROLE_ORDER:
        raise ExecutionError("review launch role changed")
    _require_identifier(reviewer_id, "reviewer_id")
    _require_absolute(receipt_path, "receipt_path")
    _require_absolute(review_path, "review_path")
    return {
        "schema": "hsai-p01b-review-launch-v1",
        "review_session_sha256": review_session_sha256,
        "review_session_durability_sha256": review_session_durability_sha256,
        "claim_boundary_sha256": claim_boundary_sha256,
        "role": role,
        "reviewer_id": reviewer_id,
        "command_observation": dict(command_observation),
        "receipt_path": receipt_path,
        "receipt_bytes": len(receipt_raw),
        "receipt_sha256": sha256_bytes(receipt_raw),
        "receipt_domain_sha256": receipt_domain_sha256,
        "review_path": review_path,
        "review_bytes": len(review_raw),
        "review_sha256": sha256_bytes(review_raw),
        "review_domain_sha256": review_domain_sha256,
    }


def build_review_aggregate_v2(
    *, common: Mapping[str, object], ordered_receipt_sha256: Sequence[str],
    ordered_review_sha256: Sequence[str], ordered_launch_sha256: Sequence[str],
    reconstructed_class_results: Sequence[Mapping[str, object]]
) -> Dict[str, object]:
    if any(len(values) != 2 for values in (
        ordered_receipt_sha256, ordered_review_sha256, ordered_launch_sha256
    )):
        raise ExecutionError("review aggregate requires exactly two fixed-role digests")
    for values in (ordered_receipt_sha256, ordered_review_sha256, ordered_launch_sha256):
        for value in values:
            _require_hex64(value, "ordered review digest")
    rows = [dict(item) for item in reconstructed_class_results]
    accepted = rows == [{"class_id": item, "closed": True} for item in CLASS_ORDER]
    return {
        "schema": "hsai-p01b-container-review-aggregate-v2",
        **dict(common),
        "ordered_fresh_validation_receipt_sha256": list(ordered_receipt_sha256),
        "ordered_review_sha256": list(ordered_review_sha256),
        "ordered_review_launch_sha256": list(ordered_launch_sha256),
        "reconstructed_class_results": rows,
        "atomic_result": "accept" if accepted else "reject",
    }


def build_acceptance_record_v2(
    *, review_session_sha256: str, review_session_durability_sha256: str,
    candidate_manifest_sha256: str, candidate_decision_sha256: str,
    review_aggregate_sha256: str, expected_bindings_sha256: str,
    claim_boundary_sha256: str, repository_state_sha256: str,
    publication_record_sha256: str, ordered_review_launch_sha256: Sequence[str],
    reconstructed_class_results: Sequence[Mapping[str, object]]
) -> Dict[str, object]:
    digest_values = (
        review_session_sha256, review_session_durability_sha256,
        candidate_manifest_sha256, candidate_decision_sha256, review_aggregate_sha256,
        expected_bindings_sha256, claim_boundary_sha256, repository_state_sha256,
        publication_record_sha256, *ordered_review_launch_sha256,
    )
    for value in digest_values:
        _require_hex64(value, "acceptance digest")
    if len(ordered_review_launch_sha256) != 2:
        raise ExecutionError("acceptance requires two review launches")
    rows = [dict(item) for item in reconstructed_class_results]
    if rows != [{"class_id": item, "closed": True} for item in CLASS_ORDER]:
        raise ExecutionError("acceptance requires all eight independently closed classes")
    return {
        "schema": "hsai-p01b-container-acceptance-v2",
        "review_session_sha256": review_session_sha256,
        "review_session_durability_sha256": review_session_durability_sha256,
        "candidate_manifest_sha256": candidate_manifest_sha256,
        "candidate_decision_sha256": candidate_decision_sha256,
        "review_aggregate_sha256": review_aggregate_sha256,
        "expected_bindings_sha256": expected_bindings_sha256,
        "claim_boundary_sha256": claim_boundary_sha256,
        "repository_state_sha256": repository_state_sha256,
        "publication_record_sha256": publication_record_sha256,
        "ordered_review_launch_sha256": list(ordered_review_launch_sha256),
        "closed_classes": list(CLASS_ORDER),
        "correspondence_score": "10/10",
        "evidence_level": "Level1LocalReplayOrLower",
        "accepted_evidence_created": False,
        "level2_plus_created": False,
        "authority_granted": False,
    }


def _validate_exact_absence(observation: RawObservation, subject: str) -> None:
    expected = ("Error response from daemon: No such container: %s\n" % subject).encode("ascii")
    if (
        observation.value.get("outcome") != "exit"
        or observation.value.get("exit_code") != 1
        or observation.stdout != b""
        or observation.stderr != expected
    ):
        raise ExecutionError("exact container absence was not established")


def _logical_operation_observation(
    observation: RawObservation,
    namespace: str,
    completion_ordinal: int,
    previous_observation_sha256: Optional[str],
    evidence_module: Optional[Any] = None,
) -> RawObservation:
    """Rebind one freshly retained operation to the exact candidate path graph."""
    role = observation.value.get("role")
    if not isinstance(role, str):
        raise ExecutionError("operation role is absent")
    base = "operations/%s/%03d-%s" % (namespace, completion_ordinal, role)
    value = dict(observation.value)
    value["completion_ordinal"] = completion_ordinal
    value["previous_observation_sha256"] = previous_observation_sha256
    value["stdout_path"] = base + "/stdout.bin"
    value["stderr_path"] = base + "/stderr.bin"
    try:
        (evidence_module or _load_evidence_module()).validate_observation(
            value, observation.stdout, observation.stderr
        )
    except Exception as error:
        raise ExecutionError("operation observation was rejected") from error
    return RawObservation(value, observation.stdout, observation.stderr)


def _clock_interval(clock: Callable[[], int]) -> Tuple[int, int]:
    started = clock()
    ended = clock()
    while ended <= started:
        ended = clock()
    return started, ended


def _execute_attempt(
    *,
    plan: Mapping[str, object],
    authorization_sha256: str,
    implementation_commit: str,
    snapshot: SnapshotResult,
    snapshot_pair: Mapping[str, object],
    raw_root: Path,
    attempt_root: Path,
    raw_root_fd: Optional[int] = None,
    attempt_root_fd: Optional[int] = None,
    runner: Callable[..., RawObservation],
    spanning_executor: Callable[..., RunningExportResult],
    clock: Callable[[], int] = time.monotonic_ns,
    container_id_sink: Optional[Callable[[str], None]] = None,
    evidence_module: Optional[Any] = None,
    post_binding_durability_hook: Optional[Callable[[], None]] = None,
) -> AttemptExecution:
    evidence = evidence_module or _load_evidence_module()
    if raw_root_fd is not None:
        _require_logical_directory_fd(
            raw_root, raw_root_fd, "attempt operation root"
        )
    if attempt_root_fd is not None:
        _require_logical_directory_fd(
            attempt_root, attempt_root_fd, "attempt audit root"
        )
    evidence.validate_attempt_plan(plan)
    plan_sha256 = evidence.attempt_plan_digest(plan)
    commands_value = plan["commands"]
    if not isinstance(commands_value, list) or len(commands_value) != 15:
        raise ExecutionError("attempt lifecycle command count changed")
    observations: List[RawObservation] = []
    container_id: Optional[str] = None
    attempt_id = str(plan["attempt_id"])
    start_ns = clock()
    deadline_ns = start_ns + ATTEMPT_TIMEOUT_NS
    intent = build_container_intent(
        campaign_id=str(plan["campaign_id"]),
        attempt_id=attempt_id,
        authorization_sha256=authorization_sha256,
        implementation_commit=implementation_commit,
        attempt_plan_sha256=plan_sha256,
        created_monotonic_ns=start_ns,
    )
    if attempt_root_fd is None:
        _mkdir_durable(attempt_root)
    durability_events: List[Mapping[str, object]] = []

    def durability_event(
        operation: str,
        target: str,
        started: int,
        ended: int,
        digest: Optional[str],
        error_number: Optional[int] = 0,
    ) -> None:
        if ended <= started:
            raise ExecutionError("attempt durability event clock did not advance")
        durability_events.append(
            {
                "ordinal": len(durability_events),
                "operation": operation,
                "target": target,
                "started_monotonic_ns": started,
                "ended_monotonic_ns": ended,
                "result": 0,
                "errno": error_number,
                "sha256": digest,
            }
        )

    event_start = clock()
    if attempt_root_fd is None:
        _write_fsync(attempt_root / "intent.json", canonical_json_bytes(intent))
    else:
        _a3l9_write_at(
            attempt_root_fd, "intent.json", canonical_json_bytes(intent)
        )
    event_end = clock()
    while event_end <= event_start:
        event_end = clock()
    durability_event(
        "intent-file-fsync",
        "intent.json",
        event_start,
        event_end,
        evidence._digest("intent", intent),
    )
    event_start = clock()
    if attempt_root_fd is None:
        _fsync_directory(attempt_root)
    else:
        os.fsync(attempt_root_fd)
    event_end = clock()
    while event_end <= event_start:
        event_end = clock()
    durability_event(
        "intent-directory-fsync", ".", event_start, event_end, None
    )

    def execute_command(command_value: Mapping[str, object]) -> RawObservation:
        if raw_root_fd is not None:
            _require_logical_directory_fd(
                raw_root, raw_root_fd, "attempt operation root"
            )
        if attempt_root_fd is not None:
            _require_logical_directory_fd(
                attempt_root, attempt_root_fd, "attempt audit root"
            )
        previous = observations[-1].digest if observations else None
        command = _command_before_deadline(
            command_from_mapping(command_value), deadline_ns, clock
        )
        raw_observation = runner(
            command,
            plan_sha256=plan_sha256,
            completion_ordinal=len(observations),
            previous_observation_sha256=previous,
            raw_root=raw_root,
            raw_root_fd=raw_root_fd,
            container_id=container_id,
        )
        observation = _logical_operation_observation(
            raw_observation, attempt_id, len(observations), previous, evidence
        )
        if observation.value["ended_monotonic_ns"] > deadline_ns:
            raise ExecutionError("attempt deadline exceeded")
        observations.append(observation)
        return observation

    name = _attempt_name(str(plan["campaign_id"]), str(plan["attempt_id"]))
    pre_name = execute_command(commands_value[0])
    _validate_exact_absence(pre_name, name)
    pre_labels = execute_command(commands_value[1])
    _require_success(pre_labels, "pre-create label absence")
    if pre_labels.stdout != b"":
        raise ExecutionError("pre-create label collision")
    created = execute_command(commands_value[2])
    _require_success(created, "container create")
    match = re.fullmatch(rb"([0-9a-f]{64})\n", created.stdout)
    if match is None or created.stderr != b"":
        raise ExecutionError("container create did not return one stable CID")
    container_id = match.group(1).decode("ascii")
    durability_event(
        "container-create",
        str(intent["container_name"]),
        int(created.value["started_monotonic_ns"]),
        int(created.value["ended_monotonic_ns"]),
        created.digest,
        None,
    )
    binding_start = clock()
    cid_binding = build_cid_binding(
        intent_sha256=evidence._digest("intent", intent),
        container_id=container_id,
        create_observation_sha256=created.digest,
        bound_monotonic_ns=binding_start,
    )
    if attempt_root_fd is None:
        _write_fsync(
            attempt_root / "cid-binding.json", canonical_json_bytes(cid_binding)
        )
    else:
        _a3l9_write_at(
            attempt_root_fd, "cid-binding.json",
            canonical_json_bytes(cid_binding),
        )
    binding_end = clock()
    while binding_end <= binding_start:
        binding_end = clock()
    durability_event(
        "cid-binding-file-fsync",
        "cid-binding.json",
        binding_start,
        binding_end,
        evidence._digest("cid_binding", cid_binding),
    )
    binding_dir_start = clock()
    if attempt_root_fd is None:
        _fsync_directory(attempt_root)
    else:
        os.fsync(attempt_root_fd)
    binding_dir_end = clock()
    while binding_dir_end <= binding_dir_start:
        binding_dir_end = clock()
    durability_event(
        "cid-binding-directory-fsync",
        ".",
        binding_dir_start,
        binding_dir_end,
        None,
    )
    if post_binding_durability_hook is not None:
        post_binding_durability_hook()
    if container_id_sink is not None:
        container_id_sink(container_id)
    resolved = resolve_cid(plan, container_id)
    resolved_commands = resolved["commands"]
    prestart = execute_command(resolved_commands[3])
    _require_success(prestart, "prestart inspect")
    try:
        inspect_value = _strict_docker_json(
            prestart.stdout, "prestart inspect", evidence
        )
    except Exception as error:
        raise ExecutionError("prestart inspect was not strict JSON") from error
    if not isinstance(inspect_value, list) or len(inspect_value) != len(INSPECT_FIELDS):
        raise ExecutionError("prestart inspect field count changed")
    def emergency_kill() -> None:
        command = _command_before_deadline(
            command_from_mapping(resolved_commands[7]), deadline_ns, clock
        )
        emergency_root_fd: Optional[int] = None
        if raw_root_fd is not None:
            emergency_root_fd = _a3l9_open_relative_directory(
                raw_root_fd, ("emergency",), mode=0o700, create=True
            )
        try:
            emergency = runner(
                command,
                plan_sha256=plan_sha256,
                completion_ordinal=0,
                previous_observation_sha256=None,
                raw_root=raw_root / "emergency",
                raw_root_fd=emergency_root_fd,
                container_id=container_id,
            )
        finally:
            if emergency_root_fd is not None:
                os.close(emergency_root_fd)
        _require_success(emergency, "emergency kill")

    spanning = spanning_executor(
        attempt_id=str(plan["attempt_id"]),
        plan_sha256=plan_sha256,
        container_id=container_id,
        start_command=command_from_mapping(resolved_commands[4]),
        export_command=command_from_mapping(resolved_commands[5]),
        release_command=command_from_mapping(resolved_commands[6]),
        raw_root=raw_root,
        raw_root_fd=raw_root_fd,
        readiness_event_path=raw_root / "readiness-event.json",
        first_completion_ordinal=4,
        previous_observation_sha256=observations[-1].digest,
        tar_parser=evidence.parse_docker_copy_tar,
        runner=runner,
        emergency_kill=emergency_kill,
        deadline_ns=deadline_ns,
        clock=clock,
    )
    export_observation = _logical_operation_observation(
        spanning.export_observation,
        attempt_id,
        4,
        observations[-1].digest, evidence,
    )
    release_observation = _logical_operation_observation(
        spanning.release_observation,
        attempt_id,
        5,
        export_observation.digest, evidence,
    )
    start_observation = _logical_operation_observation(
        spanning.start_observation,
        attempt_id,
        6,
        release_observation.digest, evidence,
    )
    if max(
        int(item.value["ended_monotonic_ns"])
        for item in (export_observation, release_observation, start_observation)
    ) > deadline_ns:
        raise ExecutionError("attempt deadline exceeded")
    observations.extend((export_observation, release_observation, start_observation))
    emergency_raw = build_not_run_observation(
        command_from_mapping(resolved_commands[7]),
        plan_sha256=plan_sha256,
        completion_ordinal=7,
        previous_observation_sha256=observations[-1].digest,
        raw_root=raw_root,
        raw_root_fd=raw_root_fd,
        container_id=container_id,
    )
    emergency = _logical_operation_observation(
        emergency_raw, attempt_id, 7, observations[-1].digest, evidence
    )
    observations.append(emergency)
    for launch in range(8, 15):
        observation = execute_command(resolved_commands[launch])
        if launch in (11, 12):
            _validate_exact_absence(
                observation, container_id if launch == 11 else name
            )
        else:
            _require_success(observation, str(observation.value["role"]))
        if launch == 13 and observation.stdout != b"":
            raise ExecutionError("post-remove label listing was not empty")
    if observations[8].stdout != b"0\n":
        raise ExecutionError("container wait status was not zero")
    try:
        terminal = _strict_docker_json(
            observations[9].stdout, "terminal inspect", evidence
        )
    except Exception as error:
        raise ExecutionError("terminal inspect was not strict JSON") from error
    if not isinstance(terminal, list) or len(terminal) != len(INSPECT_FIELDS):
        raise ExecutionError("terminal inspect field count changed")
    result = evidence.parse_probe_result(
        spanning.payload,
        "normal" if plan["attempt_id"] == "normal" else "oom-child",
    )
    if result.get("input_manifest_sha256") != snapshot.manifest_sha256:
        raise ExecutionError("probe result does not bind A3L7 snapshot copy manifest")
    items = [(item.value, item.stdout, item.stderr) for item in observations]
    receipts = evidence.build_receipt_chain(attempt_id, plan, items)
    readiness_event = dict(spanning.readiness_event)
    readiness_event["stdout_path"] = start_observation.value["stdout_path"]
    event_sha256 = evidence.readiness_event_digest(readiness_event)
    evidence.validate_readiness_event(
        readiness_event,
        start_observation.value,
        start_observation.stdout,
        export_observation.value,
        release_observation.value,
    )
    source_manifest_sha256 = evidence.snapshot_source_manifest_digest(
        snapshot_pair["source_manifest"]
    )
    source_descriptor_sha256 = evidence.descriptor_set_digest(
        snapshot_pair["source_descriptor_set"]
    )
    snapshot_descriptor_sha256 = evidence.descriptor_set_digest(
        snapshot_pair["copy_descriptor_set"]
    )
    ingress = evidence.build_certificate(
        "ingress",
        authorization_sha256,
        implementation_commit,
        str(plan["attempt_id"]),
        snapshot.manifest_sha256,
        prestart.digest,
        {
            "container_mount_read_only": True,
            "snapshot_descriptor_observation_sha256": snapshot_descriptor_sha256,
            "snapshot_manifest_sha256": snapshot.manifest_sha256,
            "source_count": SNAPSHOT_FILE_COUNT,
            "source_descriptor_observation_sha256": source_descriptor_sha256,
            "source_manifest_sha256": source_manifest_sha256,
        },
    )
    egress = evidence.build_certificate(
        "egress",
        authorization_sha256,
        implementation_commit,
        str(plan["attempt_id"]),
        snapshot.manifest_sha256,
        start_observation.digest,
        {
            "export_observation_sha256": export_observation.digest,
            "ordering_valid": True,
            "raw_tar_sha256": sha256_bytes(export_observation.stdout),
            "readiness_event_sha256": event_sha256,
            "release_observation_sha256": release_observation.digest,
            "result_bytes": len(spanning.payload),
            "result_sha256": sha256_bytes(spanning.payload),
            "start_observation_sha256": start_observation.digest,
        },
    )
    cleanup = evidence.build_certificate(
        "cleanup",
        authorization_sha256,
        implementation_commit,
        str(plan["attempt_id"]),
        snapshot.manifest_sha256,
        observations[14].digest,
        {
            "absent": True,
            "cid_absence_observation_sha256": observations[11].digest,
            "container_id": container_id,
            "container_name": name,
            "daemon_recheck_observation_sha256": observations[14].digest,
            "label_absence_observation_sha256": observations[13].digest,
            "labels_sha256": sha256_bytes(
                canonical_json_bytes(intent["expected_labels"])
            ),
            "name_absence_observation_sha256": observations[12].digest,
            "remove_observation_sha256": observations[10].digest,
        },
    )
    end_ns = clock()
    latest_observation_end = max(
        int(item.value["ended_monotonic_ns"])
        for item in observations
        if item.value["outcome"] != "not_run"
    )
    while end_ns < latest_observation_end:
        end_ns = clock()
    if end_ns > deadline_ns:
        raise ExecutionError("attempt deadline exceeded")
    timing = {
        "schema": "hsai-p01b-attempt-timing-v1",
        "campaign_id": plan["campaign_id"],
        "attempt_id": attempt_id,
        "start_monotonic_ns": start_ns,
        "deadline_monotonic_ns": deadline_ns,
        "end_monotonic_ns": end_ns,
        "ordered_durability_events": durability_events,
        "deadline_met": True,
    }
    if attempt_root_fd is None:
        _write_json(attempt_root / "timing.json", timing)
    else:
        _a3l9_write_at(
            attempt_root_fd, "timing.json", canonical_json_bytes(timing)
        )
        os.fsync(attempt_root_fd)
    return AttemptExecution(
        attempt_id,
        container_id,
        intent,
        cid_binding,
        timing,
        result,
        receipts,
        readiness_event,
        (ingress, egress, cleanup),
        tuple(observations),
        export_observation.stdout,
    )


def _write_candidate_value(root: Path, relative: str, value: object) -> None:
    _validate_relative_path(relative)
    data = value if isinstance(value, bytes) else canonical_json_bytes(value)
    if not isinstance(data, bytes):
        raise ExecutionError("candidate value is not bytes")
    _write_fsync(root / relative, data)


@dataclass(frozen=True)
class CampaignExecution:
    manifest: Mapping[str, object]
    publication: Mapping[str, object]
    repository_state: Mapping[str, object]
    attempts: Tuple[AttemptExecution, ...]
    final_path: str


_A3L7_AUTHORITY_FILES = (
    "a3l6-gate-bundle.json",
    "action.json",
    "admission-decision.json",
    "authorization-root.json",
    "evidence-bundle.json",
    "expected-bindings.json",
    "policy.json",
    "user-authorization.txt",
)
_A3L7_READINESS_FILES = (
    "authorization.json",
    "campaign-plan.json",
    "normal-plan.json",
    "oom-plan.json",
    "preauthorization-plan.json",
    "readiness-result.json",
    "receipts.json",
)


@dataclass(frozen=True)
class A3L7CampaignMaterial:
    root: Path
    readiness_result: Mapping[str, object]
    authorization: Mapping[str, object]
    campaign_plan: Mapping[str, object]
    normal_plan: Mapping[str, object]
    oom_plan: Mapping[str, object]
    expected_bindings: Mapping[str, object]
    snapshot: SnapshotResult
    snapshot_graph: Mapping[str, object]
    retained_payloads: Mapping[str, bytes]


def _exact_regular_inventory(root: Path, expected: Sequence[str], label: str) -> None:
    try:
        entries = sorted(item.name for item in root.iterdir())
    except OSError as error:
        raise ExecutionError(label + " root is unreadable") from error
    if entries != sorted(expected):
        raise ExecutionError(label + " root inventory changed")
    for name in expected:
        metadata = os.lstat(root / name)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ExecutionError(label + " input is not a single-link regular file")


def _retained_operation(
    root: Path, namespace: str, basename: str,
    evidence_module: Optional[Any] = None,
    retained_payloads: Optional[Mapping[str, bytes]] = None,
) -> RawObservation:
    directory = root / "operations" / namespace / basename
    logical = "operations/%s/%s" % (namespace, basename)
    if retained_payloads is None:
        value = _load_json_file(directory / "observation.json")
        stdout = _read_nofollow_regular(directory / "stdout.bin", TAR_CAP)
        stderr = _read_nofollow_regular(directory / "stderr.bin", METADATA_CAP)
    else:
        value = _strict_json_object_bytes(
            retained_payloads[logical + "/observation.json"],
            "retained operation " + basename,
        )
        stdout = retained_payloads[logical + "/stdout.bin"]
        stderr = retained_payloads[logical + "/stderr.bin"]
    try:
        (evidence_module or _load_evidence_module()).validate_observation(
            value, stdout, stderr
        )
    except Exception as error:
        raise ExecutionError("retained operation was rejected: " + basename) from error
    if (
        value.get("stdout_path") != logical + "/stdout.bin"
        or value.get("stderr_path") != logical + "/stderr.bin"
    ):
        raise ExecutionError("retained operation path drifted: " + basename)
    return RawObservation(value, stdout, stderr)


def _load_a3l7_campaign_material(
    *,
    a3l7_root: Path,
    evidence_module: Optional[Any] = None,
) -> A3L7CampaignMaterial:
    """Reconstruct the complete accepted A3L7 graph and immutable snapshot."""
    evidence = evidence_module or _load_evidence_module()
    root = Path(_a3l9_canonical_absolute(
        os.path.abspath(str(a3l7_root)), "A3L7 root"
    ))
    retained_payloads = _a3l7_candidate_payloads(root)

    def retained_object(
        relative: str, cap: int = RESULT_CAP,
    ) -> Mapping[str, object]:
        return _strict_json_object_bytes(
            retained_payloads[relative], "retained A3L7 " + relative, cap
        )

    authority = root / "authority"
    readiness = root / "readiness"
    retained_bindings = retained_object("authority/expected-bindings.json")
    retained_result = retained_object("readiness/readiness-result.json")
    retained_authorization = retained_object("readiness/authorization.json")
    retained_campaign = retained_object("readiness/campaign-plan.json")
    retained_normal = retained_object("readiness/normal-plan.json")
    retained_oom = retained_object("readiness/oom-plan.json")

    context = retained_object("provenance/docker-context.json")
    context_raw = retained_payloads["provenance/docker-context.raw"]
    first = _retained_operation(
        root, "readiness", "000-registry-index", evidence,
        retained_payloads,
    )
    environment = first.value.get("environment")
    if not isinstance(environment, Mapping):
        raise ExecutionError("retained readiness environment is absent")
    config_root = environment.get("DOCKER_CONFIG")
    temporary_root = environment.get("TMPDIR")
    host_uri = context.get("host")
    if not all(isinstance(item, str) for item in (config_root, temporary_root, host_uri)):
        raise ExecutionError("retained readiness dynamic binding is absent")
    readiness_plan = build_readiness_plan(
        predecessor_commit=str(retained_bindings["predecessor_commit"]),
        user_authorization_sha256=str(retained_bindings["user_authorization_sha256"]),
        config_root=str(config_root),
        host_uri=str(host_uri),
        temporary_root=str(temporary_root),
    )
    readiness_items = tuple(
        _retained_operation(
            root, "readiness", "%03d-%s" % (index, role), evidence,
            retained_payloads,
        )
        for index, role in enumerate(READINESS_OPERATION_ROLES)
    )
    desktop_provenance = retained_object("provenance/docker-desktop.json")
    buildx_provenance = retained_object("provenance/buildx.json")
    transcript_bindings = {
        "registry-index": retained_object("provenance/registry/index.json"),
        "registry-platform": retained_object(
            "provenance/registry/platform-manifest.json"
        ),
        "codesign-verify": retained_object("provenance/signature/verify.json"),
        "codesign-display": retained_object("provenance/signature/display.json"),
    }
    readiness_provenance = {
        "docker-desktop": desktop_provenance,
        "buildx": buildx_provenance,
    }
    try:
        evidence.validate_readiness_graph(
            readiness_plan,
            retained_result,
            tuple((item.value, item.stdout, item.stderr) for item in readiness_items),
            buildx_provenance["descriptor_set"],
            desktop_provenance["descriptor_set"],
            transcript_bindings,
            context,
            context_raw,
            readiness_provenance,
            retained_object("readiness/receipts.json"),
        )
    except Exception as error:
        raise ExecutionError("retained A3L7 readiness graph was rejected") from error

    pair = retained_object("snapshot/source-manifest.json")
    source_descriptors = retained_object(
        "snapshot/source-descriptor-observations.json"
    )
    copy_descriptors = retained_object("snapshot/ingress-observations.json")
    try:
        evidence.validate_snapshot_manifest_pair(
            pair, source_descriptors, copy_descriptors
        )
    except Exception as error:
        raise ExecutionError("retained A3L7 snapshot graph was rejected") from error
    source_manifest = pair["source_manifest"]
    copy_manifest = pair["snapshot_manifest"]
    source_sha256 = evidence.snapshot_source_manifest_digest(source_manifest)
    copy_sha256 = evidence.snapshot_copy_manifest_digest(copy_manifest)
    if (
        source_sha256 != retained_bindings["snapshot_source_manifest_sha256"]
        or copy_sha256 != retained_bindings["snapshot_copy_manifest_sha256"]
        or retained_normal["source_manifest_sha256"] != copy_sha256
        or retained_oom["source_manifest_sha256"] != copy_sha256
    ):
        raise ExecutionError("A3L5G source/copy/plan binding drifted")
    source_by_path = {item["path"]: item for item in source_manifest["ordered_entries"]}
    snapshot_files = root / "snapshot/files"
    entries: List[SnapshotEntry] = []
    for copied in copy_manifest["ordered_entries"]:
        relative = str(copied["path"])
        raw = retained_payloads["snapshot/files/" + relative]
        if (
            len(raw) != copied["bytes"]
            or sha256_bytes(raw) != copied["sha256"]
        ):
            raise ExecutionError("immutable A3L7 snapshot file drifted: " + relative)
        source = source_by_path[relative]
        entries.append(
            SnapshotEntry(
                relative,
                len(raw),
                sha256_bytes(raw),
                int(source["mode"]),
                int(copied["mode"]),
            )
        )
    snapshot = SnapshotResult(str(snapshot_files), tuple(entries), copy_sha256)

    try:
        evidence.validate_authority_graph(
            retained_payloads["authority/user-authorization.txt"],
            retained_object("authority/action.json"),
            retained_object("authority/policy.json"),
            retained_object("authority/evidence-bundle.json"),
            retained_object("authority/admission-decision.json"),
            retained_object("authority/a3l6-gate-bundle.json", GATE_JSON_CAP),
            readiness_plan,
            retained_bindings["claim_boundary"],
            retained_object("readiness/preauthorization-plan.json"),
            retained_bindings,
            retained_result,
            retained_object("authority/authorization-root.json"),
            retained_authorization,
            retained_campaign,
            retained_normal,
            retained_oom,
            str(snapshot_files),
        )
    except Exception as error:
        raise ExecutionError("retained A3L7 authority graph was rejected") from error
    snapshot_graph = dict(pair)
    snapshot_graph["source_descriptor_set"] = source_descriptors
    snapshot_graph["copy_descriptor_set"] = copy_descriptors
    return A3L7CampaignMaterial(
        root,
        retained_result,
        retained_authorization,
        retained_campaign,
        retained_normal,
        retained_oom,
        retained_bindings,
        snapshot,
        snapshot_graph,
        retained_payloads,
    )


def _repository_command_capture(
    *,
    role: str,
    argv: Sequence[str],
    plan: Mapping[str, object],
    clock: Callable[[], int],
    runner: Optional[Callable[[Sequence[str], Path], bytes]],
) -> Mapping[str, object]:
    started = clock()
    if runner is None:
        command = CommandSpec(
            ordinal=0,
            role=role,
            argv=tuple(argv),
            environment=plan["environment"],  # type: ignore[arg-type]
            cwd=str(plan["cwd"]),
            stdin_policy="closed-null",
            stdout_cap=METADATA_CAP,
            stderr_cap=STREAM_CAP,
            timeout_ns=60_000_000_000,
            activation="always",
            expected_outcomes=("exit_zero",),
        )
        process = DirectProcess(
            command,
            expected_executable_sha256=str(plan["git_sha256"]),
        )
        captured = process.complete(
            plan_sha256=domain_sha256(
                "hsai:p01b-repository-state-plan:v1", plan
            ),
            completion_ordinal=0,
            previous_observation_sha256=None,
        )
        stdout, stderr = captured.stdout, captured.stderr
        exit_code = captured.value["exit_code"]
        if captured.value["outcome"] != "exit":
            raise ExecutionError(
                "repository-state command failed: "
                + str(captured.value["outcome"])
            )
    else:
        stdout = runner(argv, Path(str(plan["cwd"])))
        stderr, exit_code = b"", 0
    ended = clock()
    while ended <= started:
        ended = clock()
    if (
        not isinstance(stdout, bytes)
        or not isinstance(stderr, bytes)
        or len(stdout) > METADATA_CAP
        or len(stderr) > STREAM_CAP
        or stderr != b""
        or exit_code != 0
    ):
        raise ExecutionError("repository-state command failed")
    return {
        "role": role,
        "argv": list(argv),
        "environment": dict(plan["environment"]),
        "cwd": plan["cwd"],
        "stdin_policy": plan["stdin_policy"],
        "executable_path": plan["git_path"],
        "executable_sha256": plan["git_sha256"],
        "timeout_ns": 60_000_000_000,
        "stdout_cap_bytes": METADATA_CAP,
        "stderr_cap_bytes": STREAM_CAP,
        "started_monotonic_ns": started,
        "ended_monotonic_ns": ended,
        "outcome": "completed",
        "exit_code": 0,
        "signal": None,
        "stdout_total_bytes": len(stdout),
        "stdout_retained_bytes": len(stdout),
        "stdout_truncated": False,
        "stdout_base64": base64.b64encode(stdout).decode("ascii"),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_total_bytes": len(stderr),
        "stderr_retained_bytes": len(stderr),
        "stderr_truncated": False,
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
        "stderr_sha256": sha256_bytes(stderr),
    }


def _repository_capture_v1(
    plan: Mapping[str, object],
    *,
    clock: Callable[[], int],
    runner: Optional[Callable[[Sequence[str], Path], bytes]],
) -> Mapping[str, object]:
    roles = ("head", "tree", "status")
    commands = tuple(item["argv"] for item in plan["commands"])
    rows = [
        _repository_command_capture(
            role=role, argv=argv, plan=plan, clock=clock, runner=runner
        )
        for role, argv in zip(roles, commands)
    ]
    return {
        "schema": "hsai-p01b-repository-state-capture-v1",
        "ordered_commands": rows,
        "protected_observation": capture_descriptor_observation(
            Path(str(plan["protected_path"])), "protected"
        ),
    }


def _repository_state_plan(
    *, repo_root: Path, protected_file: Path, bindings: Mapping[str, object]
) -> Mapping[str, object]:
    root = os.path.abspath(str(repo_root))
    protected = os.path.abspath(str(protected_file))
    git_path = str(bindings["git_path"])
    environment = {
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TZ": "UTC",
    }
    argv = (
        [git_path, "rev-parse", "HEAD"],
        [git_path, "rev-parse", "HEAD^{tree}"],
        [git_path, "status", "--porcelain=v2", "-z", "--untracked-files=all"],
    )
    return {
        "schema": "hsai-p01b-repository-state-plan-v1",
        "git_path": git_path,
        "git_sha256": bindings["git_sha256"],
        "protected_path": protected,
        "environment": environment,
        "cwd": root,
        "stdin_policy": "closed",
        "commands": [{"argv": item} for item in argv],
    }


def _build_repository_state_v1(
    *,
    plan: Mapping[str, object],
    before: Mapping[str, object],
    after: Mapping[str, object],
    bindings: Mapping[str, object],
    evidence_module: Optional[Any] = None,
) -> Mapping[str, object]:
    state = {
        "schema": "hsai-p01b-repository-state-v1",
        "plan": dict(plan),
        "implementation_commit": bindings["implementation_commit"],
        "implementation_tree": bindings["implementation_tree"],
        "before": dict(before),
        "after": dict(after),
        "unchanged": True,
    }
    try:
        (evidence_module or _load_evidence_module()).validate_repository_state(
            state
        )
    except Exception as error:
        raise ExecutionError("repository state changed during A3L8") from error
    return state


def _operation_payloads(
    namespace: str, observations: Sequence[RawObservation]
) -> Dict[str, bytes]:
    payloads: Dict[str, bytes] = {}
    for ordinal, item in enumerate(observations):
        role = str(item.value["role"])
        base = "operations/%s/%03d-%s/" % (namespace, ordinal, role)
        if (
            item.value["stdout_path"] != base + "stdout.bin"
            or item.value["stderr_path"] != base + "stderr.bin"
        ):
            raise ExecutionError("operation payload path drifted")
        payloads[base + "observation.json"] = canonical_json_bytes(item.value)
        payloads[base + "stdout.bin"] = item.stdout
        payloads[base + "stderr.bin"] = item.stderr
    return payloads


def _a3l7_candidate_paths() -> Tuple[str, ...]:
    paths = set()
    paths.update("authority/" + name for name in _A3L7_AUTHORITY_FILES)
    paths.update("readiness/" + name for name in _A3L7_READINESS_FILES)
    paths.update(
        (
            "provenance/docker-desktop.json",
            "provenance/buildx.json",
            "provenance/docker-context.json",
            "provenance/docker-context.raw",
            "provenance/info-plist.raw",
            "provenance/registry/index.json",
            "provenance/registry/platform-manifest.json",
            "provenance/signature/verify.json",
            "provenance/signature/display.json",
            "snapshot/source-manifest.json",
            "snapshot/source-descriptor-observations.json",
            "snapshot/ingress-observations.json",
        )
    )
    paths.update("snapshot/files/" + path for path in SOURCE_PATHS)
    for index, role in enumerate(READINESS_OPERATION_ROLES):
        base = "operations/readiness/%03d-%s/" % (index, role)
        paths.update(base + leaf for leaf in ("observation.json", "stdout.bin", "stderr.bin"))
    return tuple(sorted(paths, key=lambda item: item.encode("ascii")))


def _a3l7_candidate_payloads(root: Path) -> Dict[str, bytes]:
    """Capture the exact A3L7 tree once through retained no-follow descriptors."""
    root_value = _a3l9_canonical_absolute(
        os.path.abspath(str(root)), "A3L7 root"
    )
    root_fd = _a3l9_open_absolute_directory(root_value)
    directory_fds: Dict[str, int] = {"": os.dup(root_fd)}
    try:
        root_metadata = os.fstat(root_fd)
        if (
            stat.S_IMODE(root_metadata.st_mode) != 0o700
            or root_metadata.st_uid != os.geteuid()
        ):
            raise ExecutionError("A3L7 root is not an owned retained directory")
        paths = _a3l7_candidate_paths()
        directories = {
            "/".join(path.split("/")[:index])
            for path in paths
            for index in range(1, len(path.split("/")))
        }
        directories.add(READINESS_TEMP_BASENAME)
        directories.add(READINESS_TEMP_BASENAME + "/" + HOST_HOME_BASENAME)
        expected_children: Dict[str, set[str]] = {
            directory: set() for directory in directories | {""}
        }
        for directory in directories:
            parent, _, name = directory.rpartition("/")
            expected_children[parent].add(name)
        for path in paths:
            parent, _, name = path.rpartition("/")
            expected_children[parent].add(name)
        directory_identities: Dict[str, Tuple[int, int, int, int, int]] = {}
        for directory in sorted(
            directories, key=lambda item: (len(item.split("/")), item)
        ):
            parent, _, name = directory.rpartition("/")
            descriptor = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fds[parent],
            )
            metadata = os.fstat(descriptor)
            expected_mode = (
                0o555
                if directory == "snapshot/files"
                or directory.startswith("snapshot/files/")
                else 0o700
            )
            if (
                not stat.S_ISDIR(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != expected_mode
                or metadata.st_dev != root_metadata.st_dev
                or metadata.st_uid != root_metadata.st_uid
                or metadata.st_gid != root_metadata.st_gid
            ):
                os.close(descriptor)
                raise ExecutionError("A3L7 retained directory identity changed")
            directory_fds[directory] = descriptor
            directory_identities[directory] = (
                metadata.st_dev, metadata.st_ino, metadata.st_mode,
                metadata.st_uid, metadata.st_gid,
            )
        for directory, expected in expected_children.items():
            if set(os.listdir(directory_fds[directory])) != expected:
                raise ExecutionError("A3L7 retained tree inventory changed")
        result: Dict[str, bytes] = {}
        for relative in paths:
            parent, _, name = relative.rpartition("/")
            descriptor = os.open(
                name,
                os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fds[parent],
            )
            try:
                before = os.fstat(descriptor)
                expected_mode = (
                    0o444 if relative.startswith("snapshot/files/") else 0o600
                )
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_nlink != 1
                    or stat.S_IMODE(before.st_mode) != expected_mode
                    or before.st_dev != root_metadata.st_dev
                    or before.st_uid != root_metadata.st_uid
                    or before.st_gid != root_metadata.st_gid
                ):
                    raise ExecutionError("A3L7 retained file identity changed")
                raw = bytearray()
                while True:
                    chunk = os.read(
                        descriptor,
                        min(READ_CHUNK_BYTES, TAR_CAP + 1 - len(raw)),
                    )
                    if not chunk:
                        break
                    raw.extend(chunk)
                    if len(raw) > TAR_CAP:
                        raise ExecutionError("A3L7 retained file exceeded cap")
                after = os.fstat(descriptor)
                if (
                    before.st_dev, before.st_ino, before.st_mode,
                    before.st_nlink, before.st_uid, before.st_gid,
                    before.st_size, before.st_mtime_ns, before.st_ctime_ns,
                ) != (
                    after.st_dev, after.st_ino, after.st_mode,
                    after.st_nlink, after.st_uid, after.st_gid,
                    after.st_size, after.st_mtime_ns, after.st_ctime_ns,
                ):
                    raise ExecutionError("A3L7 retained file changed during read")
                result[relative] = bytes(raw)
            finally:
                os.close(descriptor)
        for directory, identity in directory_identities.items():
            metadata = os.fstat(directory_fds[directory])
            if (
                metadata.st_dev, metadata.st_ino, metadata.st_mode,
                metadata.st_uid, metadata.st_gid,
            ) != identity:
                raise ExecutionError("A3L7 retained directory changed during read")
        return result
    except OSError as error:
        raise ExecutionError("A3L7 descriptor capture was rejected") from error
    finally:
        for descriptor in directory_fds.values():
            os.close(descriptor)
        os.close(root_fd)


def _campaign_provenance(
    *,
    retained_payloads: Mapping[str, bytes],
    observations: Sequence[RawObservation],
    bindings: Mapping[str, object],
    evidence_module: Optional[Any] = None,
) -> Mapping[str, Mapping[str, object]]:
    evidence = evidence_module or _load_evidence_module()
    version = _strict_docker_json(
        observations[1].stdout, "Docker version", evidence
    )
    info = _strict_docker_json(
        observations[2].stdout, "Docker info", evidence
    )
    image = _strict_docker_json(
        observations[3].stdout, "image config", evidence
    )
    if not all(isinstance(item, Mapping) for item in (version, info, image)):
        raise ExecutionError("campaign provenance JSON root changed")
    client = version.get("Client")
    server = version.get("Server")
    rootfs = image.get("RootFS")
    if not all(isinstance(item, Mapping) for item in (client, server, rootfs)):
        raise ExecutionError("campaign provenance fields are absent")

    def commit_value(name: str) -> Tuple[str, str]:
        value = info.get(name)
        if not isinstance(value, Mapping):
            raise ExecutionError(name + " is absent from Docker info")
        version_value = value.get("Version") or value.get("ID")
        commit = value.get("Commit") or value.get("Expected") or value.get("ID")
        if not isinstance(version_value, str) or not isinstance(commit, str):
            raise ExecutionError(name + " identity is incomplete")
        return version_value, commit

    containerd_version, containerd_commit = commit_value("ContainerdCommit")
    runc_version, runc_commit = commit_value("RuncCommit")
    host_set = _strict_json_object_bytes(
        retained_payloads["provenance/buildx.json"], "retained buildx provenance"
    )["descriptor_set"]
    context = _strict_json_object_bytes(
        retained_payloads["provenance/docker-context.json"],
        "retained Docker context",
    )
    def common(kind, rows, facts, descriptor=None):
        assumptions = (
            ("host-driver-honest",)
            if kind == "docker-client"
            else ("docker-daemon-honest", "host-driver-honest")
        )
        if descriptor is not None:
            return _host_provenance(
                kind, rows, descriptor, facts, assumptions, evidence
            )
        return {
            "schema": HOST_PROVENANCE_SCHEMA,
            "kind": kind,
            "ordered_source_observation_sha256": [item.digest for item in rows],
            "descriptor_set_sha256": None,
            "descriptor_set": None,
            "facts": dict(facts),
            "assumptions": list(assumptions),
        }
    values = {
        "docker-client": common(
            "docker-client",
            (observations[1],),
            {
                "path": bindings["docker_path"],
                "sha256": bindings["docker_sha256"],
                "client_version": client.get("Version"),
                "api_version": client.get("ApiVersion"),
                "go_version": client.get("GoVersion"),
                "os": client.get("Os"),
                "arch": client.get("Arch"),
            },
            host_set,
        ),
        "docker-daemon": common(
            "docker-daemon",
            (observations[1], observations[2]),
            {
                "host": context["host"],
                "context_name": context["name"],
                "server_version": server.get("Version"),
                "api_version": server.get("ApiVersion"),
                "os": server.get("Os"),
                "arch": info.get("Architecture"),
                "kernel_version": info.get("KernelVersion"),
                "operating_system": info.get("OperatingSystem"),
                "docker_root_dir": info.get("DockerRootDir"),
                "containerd_version": containerd_version,
                "containerd_commit": containerd_commit,
                "runc_version": runc_version,
                "runc_commit": runc_commit,
                "version_observation_sha256": observations[1].digest,
                "info_observation_sha256": observations[2].digest,
            },
        ),
        "image-config": common(
            "image-config",
            (observations[3],),
            {
                "platform_reference": bindings["platform_reference"],
                "image_id": image.get("Id"),
                "config_descriptor_digest": bindings["image_config_digest"],
                "architecture": image.get("Architecture"),
                "os": image.get("Os"),
                "variant": image.get("Variant"),
                "config_sha256": str(bindings["image_config_digest"]).split(":", 1)[1],
            },
        ),
        "rootfs": common(
            "rootfs",
            (observations[3],),
            {
                "image_id": image.get("Id"),
                "rootfs_type": rootfs.get("Type"),
                "ordered_diff_ids": rootfs.get("Layers"),
            },
        ),
    }
    for kind, value in values.items():
        try:
            evidence.validate_host_provenance(
                value,
                tuple(item.value for item in (
                    (observations[1], observations[2])
                    if kind == "docker-daemon"
                    else (observations[1],)
                    if kind == "docker-client"
                    else (observations[3],)
                )),
            )
        except Exception as error:
            raise ExecutionError("campaign provenance was rejected: " + kind) from error
    return values


def _publication_identity(path: Path) -> Mapping[str, object]:
    metadata = os.lstat(path)
    return _identity(metadata)


def _publication_file_reopen(root: Path, relative: str) -> Mapping[str, object]:
    raw = _read_nofollow_regular(root / relative, TAR_CAP)
    metadata = os.lstat(root / relative)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ExecutionError("publication reopen identity drifted: " + relative)
    return {
        "identity": dict(_identity(metadata)),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
    }


def _publication_event(
    events: List[Mapping[str, object]],
    *,
    clock: Callable[[], int],
    operation: str,
    target: object,
    flags: Sequence[str] = (),
    result: int = 0,
    error_number: int = 0,
    identity: Optional[Mapping[str, object]] = None,
    digest: Optional[str] = None,
    action: Optional[Callable[[], None]] = None,
) -> None:
    started = clock()
    if action is not None:
        action()
    ended = clock()
    while ended <= started:
        ended = clock()
    events.append(
        {
            "ordinal": len(events),
            "operation": operation,
            "target": target,
            "flags": list(flags),
            "started_monotonic_ns": started,
            "ended_monotonic_ns": ended,
            "result": result,
            "errno": error_number,
            "identity": None if identity is None else dict(identity),
            "sha256": digest,
        }
    )


def _renameatx_np_exclusive(
    parent_fd: object,
    staging_name: str,
    final_name: str,
    rename_callable: Optional[Callable[..., Tuple[int, int]]],
) -> Tuple[int, int]:
    owned_fd = not isinstance(parent_fd, int) or isinstance(parent_fd, bool)
    directory_fd = (
        os.open(os.fspath(parent_fd), os.O_RDONLY | os.O_DIRECTORY)
        if owned_fd else parent_fd
    )
    try:
        if rename_callable is not None:
            result, error_number = rename_callable(
                directory_fd,
                os.fsencode(staging_name),
                directory_fd,
                os.fsencode(final_name),
                0x00000004,
            )
        else:
            if sys.platform != "darwin":
                raise ExecutionError("renameatx_np publication is Darwin-only")
            libc = ctypes.CDLL(None, use_errno=True)
            function = getattr(libc, "renameatx_np", None)
            if function is None:
                raise ExecutionError("renameatx_np is unavailable")
            function.argtypes = (
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            )
            function.restype = ctypes.c_int
            ctypes.set_errno(0)
            result = function(
                directory_fd,
                os.fsencode(staging_name),
                directory_fd,
                os.fsencode(final_name),
                0x00000004,
            )
            error_number = ctypes.get_errno()
    finally:
        if owned_fd:
            os.close(directory_fd)
    if result != 0 or error_number != 0:
        raise ExecutionError("renameatx_np failed with errno %d" % error_number)
    return result, error_number


def _materialize_and_publish_candidate_v2_at(
    *,
    output_parent: Path,
    output_parent_fd: int,
    staging_fd: int,
    campaign_id: str,
    payloads: Mapping[str, bytes],
    authorization_sha256: str,
    implementation_commit: str,
    repository_plan: Mapping[str, object],
    repository_before: Mapping[str, object],
    repository_runner: Optional[Callable[[Sequence[str], Path], bytes]],
    bindings: Mapping[str, object],
    clock: Callable[[], int],
    rename_callable: Optional[Callable[..., Tuple[int, int]]],
    evidence_module: Optional[Any] = None,
) -> Tuple[Mapping[str, object], Mapping[str, object], Mapping[str, object], str]:
    evidence = evidence_module or _load_evidence_module()
    staging = output_parent / (".p01b-staging-" + campaign_id)
    final = output_parent / ("p01b-candidate-" + campaign_id)
    expected_paths = candidate_payload_paths()
    for relative in sorted(
        (item for item in candidate_directory_paths(expected_paths) if item != "."),
        key=lambda item: (len(item.split("/")), item.encode("ascii")),
    ):
        descriptor = _a3l9_open_relative_directory(
            staging_fd, _validate_relative_path(relative), mode=0o700,
            create=True,
        )
        os.close(descriptor)
    _a3l9_write_at(staging_fd, "candidate-manifest.json", b"")
    os.fsync(staging_fd)
    parent_identity = dict(_identity(os.fstat(output_parent_fd)))
    staging_identity = dict(_identity(os.fstat(staging_fd)))
    complete_payloads = dict(payloads)
    complete_payloads["publication/prepublication-descriptor-plan.json"] = canonical_json_bytes(
        build_prepublication_descriptor_plan(
            candidate_root=str(final),
            parent_identity=parent_identity,
            staging_identity=staging_identity,
        )
    )
    if tuple(sorted(complete_payloads, key=lambda item: item.encode("ascii"))) != expected_paths:
        raise ExecutionError("A3L8 payload map differs from exact 201-file grammar")
    for relative in expected_paths:
        if relative.endswith(".json"):
            try:
                evidence.strict_json_bytes(
                    complete_payloads[relative],
                    GATE_JSON_CAP
                    if relative == "authority/a3l6-gate-bundle.json"
                    else RESULT_CAP,
                )
            except Exception as error:
                raise ExecutionError(
                    "candidate JSON is malformed: " + relative
                ) from error
    events: List[Mapping[str, object]] = []
    entries: List[Mapping[str, object]] = []
    for relative in expected_paths:
        raw = complete_payloads[relative]
        write_started = clock()
        identity = _a3l9_write_at(staging_fd, relative, raw)
        write_ended = clock()
        while write_ended <= write_started:
            write_ended = clock()
        events.append(
            {
                "ordinal": len(events),
                "operation": "payload-file-fsync",
                "target": relative,
                "flags": [],
                "started_monotonic_ns": write_started,
                "ended_monotonic_ns": write_ended,
                "result": 0,
                "errno": 0,
                "identity": identity,
                "sha256": sha256_bytes(raw),
            }
        )
        entries.append(
            {
                "path": relative,
                "file_type": "regular",
                "mode": identity["mode"],
                "link_count": identity["link_count"],
                "bytes": len(raw),
                "sha256": sha256_bytes(raw),
            }
        )
    manifest = evidence.build_candidate_manifest(
        authorization_sha256, implementation_commit, entries
    )
    manifest_raw = canonical_json_bytes(manifest)
    manifest_started = clock()
    manifest_identity = _replace_fsync_at(
        staging_fd, "candidate-manifest.json", manifest_raw
    )
    manifest_ended = clock()
    while manifest_ended <= manifest_started:
        manifest_ended = clock()
    events.append(
        {
            "ordinal": len(events),
            "operation": "candidate-manifest-fsync",
            "target": "candidate-manifest.json",
            "flags": [],
            "started_monotonic_ns": manifest_started,
            "ended_monotonic_ns": manifest_ended,
            "result": 0,
            "errno": 0,
            "identity": manifest_identity,
            "sha256": sha256_bytes(manifest_raw),
        }
    )
    directories = sorted(
        candidate_directory_paths(expected_paths),
        key=lambda item: (
            item == ".",
            -(0 if item == "." else item.count("/") + 1),
            item.encode("ascii"),
        ),
    )
    for relative in directories:
        directory_fd = (
            os.dup(staging_fd)
            if relative == "."
            else _a3l9_open_relative_directory(
                staging_fd, _validate_relative_path(relative), mode=0o700
            )
        )
        identity = dict(_identity(os.fstat(directory_fd)))
        _publication_event(
            events,
            clock=clock,
            operation="candidate-directory-fsync",
            target=relative,
            identity=identity,
            action=lambda directory_fd=directory_fd: os.fsync(directory_fd),
        )
        os.close(directory_fd)
    all_paths = sorted((*expected_paths, "candidate-manifest.json"))
    pre = {
        relative: _publication_file_reopen_at(staging_fd, relative)
        for relative in all_paths
    }
    pre_inventory = [
        {"path": path, **pre[path]} for path in all_paths
    ]
    inventory_sha256 = evidence.domain_sha256(
        evidence.DOMAINS["publication_inventory"], pre_inventory
    )
    _publication_event(
        events,
        clock=clock,
        operation="prepublication-inventory",
        target=".",
        identity=staging_identity,
        digest=inventory_sha256,
    )
    evidence.validate_prepublication_candidate(
        complete_payloads, manifest, bindings
    )
    rename_started = clock()
    rename_result, rename_errno = _renameatx_np_exclusive(
        output_parent_fd, staging.name, final.name, rename_callable
    )
    rename_ended = clock()
    while rename_ended <= rename_started:
        rename_ended = clock()
    events.append(
        {
            "ordinal": len(events),
            "operation": "renameatx-np",
            "target": {"source": staging.name, "destination": final.name},
            "flags": ["RENAME_EXCL"],
            "started_monotonic_ns": rename_started,
            "ended_monotonic_ns": rename_ended,
            "result": rename_result,
            "errno": rename_errno,
            "identity": None,
            "sha256": None,
        }
    )
    _publication_event(
        events,
        clock=clock,
        operation="final-parent-fsync",
        target=str(output_parent),
        identity=parent_identity,
        action=lambda: os.fsync(output_parent_fd),
    )
    try:
        os.stat(staging.name, dir_fd=output_parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise ExecutionError("publication staging path remained")
    _publication_event(
        events,
        clock=clock,
        operation="staging-absence",
        target=staging.name,
        result=-1,
        error_number=2,
    )
    final_fd = os.open(
        final.name,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=output_parent_fd,
    )
    final_identity = dict(_identity(os.fstat(final_fd)))
    if staging_identity != final_identity:
        raise ExecutionError(
            "publication root identity changed: %s != %s"
            % (staging_identity, final_identity)
        )
    _publication_event(
        events,
        clock=clock,
        operation="final-root-reopen",
        target=final.name,
        identity=final_identity,
    )
    post = {
        relative: _publication_file_reopen_at(final_fd, relative)
        for relative in all_paths
    }
    post_inventory = [{"path": path, **post[path]} for path in all_paths]
    post_inventory_sha256 = evidence.domain_sha256(
        evidence.DOMAINS["publication_inventory"], post_inventory
    )
    _publication_event(
        events,
        clock=clock,
        operation="postpublication-inventory",
        target=".",
        identity=final_identity,
        digest=post_inventory_sha256,
    )
    manifest_sha256 = evidence.manifest_digest(manifest)
    _publication_event(
        events,
        clock=clock,
        operation="final-manifest-read",
        target="candidate-manifest.json",
        identity=post["candidate-manifest.json"]["identity"],
        digest=manifest_sha256,
    )
    repository_after = _repository_capture_v1(
        repository_plan, clock=clock, runner=repository_runner
    )
    repository_state = _build_repository_state_v1(
        plan=repository_plan,
        before=repository_before,
        after=repository_after,
        bindings=bindings,
        evidence_module=evidence,
    )
    reopen_rows = [
        {"path": path, "prepublication": pre[path], "postpublication": post[path]}
        for path in all_paths
    ]
    publication = build_publication_record_v2(
        candidate_manifest_sha256=manifest_sha256,
        repository_state_sha256=evidence.repository_state_digest(repository_state),
        staging_path=str(staging),
        final_path=str(final),
        parent_identity=parent_identity,
        prepublication_inventory_sha256=inventory_sha256,
        postpublication_inventory_sha256=post_inventory_sha256,
        staging_identity=staging_identity,
        final_identity=final_identity,
        ordered_file_reopens=reopen_rows,
        ordered_publication_events=events,
        final_manifest_sha256=manifest_sha256,
    )
    evidence.validate_publication_record(publication)
    external_relative = "artifacts/publication/" + manifest_sha256
    _a3l9_write_at(
        output_parent_fd, external_relative + "/repository-state.json",
        canonical_json_bytes(repository_state),
    )
    _a3l9_write_at(
        output_parent_fd, external_relative + "/publication-record.json",
        canonical_json_bytes(publication),
    )
    external_fd = _a3l9_open_relative_directory(
        output_parent_fd, _validate_relative_path(external_relative),
        mode=0o700,
    )
    try:
        os.fsync(external_fd)
    finally:
        os.close(external_fd)
    if _identity(os.fstat(output_parent_fd)) != parent_identity:
        raise ExecutionError("A3L8 output parent descriptor changed")
    os.close(final_fd)
    return manifest, publication, repository_state, str(final)


def _materialize_and_publish_candidate_v2(
    *,
    output_parent: Path,
    campaign_id: str,
    payloads: Mapping[str, bytes],
    authorization_sha256: str,
    implementation_commit: str,
    repository_plan: Mapping[str, object],
    repository_before: Mapping[str, object],
    repository_runner: Optional[Callable[[Sequence[str], Path], bytes]],
    bindings: Mapping[str, object],
    clock: Callable[[], int],
    rename_callable: Optional[Callable[..., Tuple[int, int]]],
    output_parent_fd: Optional[int] = None,
    evidence_module: Optional[Any] = None,
) -> Tuple[Mapping[str, object], Mapping[str, object], Mapping[str, object], str]:
    parent_fd = (
        _a3l9_open_absolute_directory(str(output_parent))
        if output_parent_fd is None else os.dup(output_parent_fd)
    )
    parent_before = os.fstat(parent_fd)
    staging_name = ".p01b-staging-" + campaign_id
    final_name = "p01b-candidate-" + campaign_id
    try:
        for name in (staging_name, final_name):
            try:
                os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise ExecutionError("campaign publication path already exists")
        os.mkdir(staging_name, 0o700, dir_fd=parent_fd)
        staging_fd = os.open(
            staging_name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        try:
            os.fsync(staging_fd)
            os.fsync(parent_fd)
            result = _materialize_and_publish_candidate_v2_at(
                output_parent=output_parent,
                output_parent_fd=parent_fd,
                staging_fd=staging_fd,
                campaign_id=campaign_id,
                payloads=payloads,
                authorization_sha256=authorization_sha256,
                implementation_commit=implementation_commit,
                repository_plan=repository_plan,
                repository_before=repository_before,
                repository_runner=repository_runner,
                bindings=bindings,
                clock=clock,
                rename_callable=rename_callable,
                evidence_module=evidence_module,
            )
        finally:
            os.close(staging_fd)
        parent_after = os.fstat(parent_fd)
        if (
            parent_after.st_dev, parent_after.st_ino, parent_after.st_mode,
            parent_after.st_uid, parent_after.st_gid,
        ) != (
            parent_before.st_dev, parent_before.st_ino, parent_before.st_mode,
            parent_before.st_uid, parent_before.st_gid,
        ):
            raise ExecutionError("A3L8 output parent identity changed")
        return result
    finally:
        os.close(parent_fd)


def _attempt_candidate_payloads(
    attempt: AttemptExecution, evidence_module: Optional[Any] = None,
) -> Dict[str, bytes]:
    base = "attempts/" + attempt.attempt_id + "/"
    prestart_projection = _strict_docker_json(
        attempt.observations[3].stdout,
        attempt.attempt_id + " prestart inspect", evidence_module,
    )
    terminal_projection = _strict_docker_json(
        attempt.observations[9].stdout,
        attempt.attempt_id + " terminal inspect", evidence_module,
    )

    def inspect_document(value: object, label: str) -> List[Mapping[str, object]]:
        if not isinstance(value, list) or len(value) != len(INSPECT_FIELDS):
            raise ExecutionError(label + " field count changed")
        root: Dict[str, object] = {}
        for dotted, field_value in zip(INSPECT_FIELDS, value):
            target = root
            parts = dotted.split(".")
            for part in parts[:-1]:
                nested = target.setdefault(part, {})
                if not isinstance(nested, dict):
                    raise ExecutionError(label + " nesting changed")
                target = nested
            target[parts[-1]] = field_value
        return [root]

    prestart = inspect_document(
        prestart_projection, attempt.attempt_id + " prestart inspect"
    )
    terminal = inspect_document(
        terminal_projection, attempt.attempt_id + " terminal inspect"
    )
    return {
        base + "intent.json": canonical_json_bytes(attempt.intent),
        base + "cid-binding.json": canonical_json_bytes(attempt.cid_binding),
        base + "timing.json": canonical_json_bytes(attempt.timing),
        base + "receipts.json": canonical_json_bytes(attempt.receipts),
        base + "result.json": canonical_json_bytes(attempt.result),
        base + "readiness-event.json": canonical_json_bytes(attempt.readiness_event),
        base + "inspect-prestart.json": canonical_json_bytes(prestart),
        base + "inspect-terminal.json": canonical_json_bytes(terminal),
        base + "egress-certificate.json": canonical_json_bytes(attempt.certificates[1]),
        base + "cleanup-certificate.json": canonical_json_bytes(attempt.certificates[2]),
        base + "export.tar": attempt.export_tar,
    }


def _campaign_candidate_payloads(
    *,
    material: A3L7CampaignMaterial,
    repository_before: Mapping[str, object],
    campaign_observations: Sequence[RawObservation],
    campaign_receipts: Mapping[str, object],
    native_result: Mapping[str, object],
    attempts: Sequence[AttemptExecution],
    evidence_module: Optional[Any] = None,
) -> Dict[str, bytes]:
    if tuple(item.attempt_id for item in attempts) != ("normal", "oom"):
        raise ExecutionError("attempt execution order changed")
    payloads = dict(material.retained_payloads)
    payloads.update(_operation_payloads("campaign", campaign_observations))
    for attempt in attempts:
        payloads.update(_operation_payloads(attempt.attempt_id, attempt.observations))
        payloads.update(_attempt_candidate_payloads(attempt, evidence_module))
    provenance = _campaign_provenance(
        retained_payloads=material.retained_payloads,
        observations=campaign_observations,
        bindings=material.expected_bindings,
        evidence_module=evidence_module,
    )
    payloads["provenance/git.json"] = canonical_json_bytes(repository_before)
    for kind, value in provenance.items():
        payloads["provenance/" + kind + ".json"] = canonical_json_bytes(value)
    payloads["reference/native-result.json"] = canonical_json_bytes(native_result)
    payloads["reference/projection.json"] = canonical_json_bytes(
        {
            "schema": "hsai-p01b-reference-projection-v1",
            "probe_sha256": native_result["probe_sha256"],
            "projection_sha256": native_result["projection_sha256"],
        }
    )
    payloads["reference/receipts.json"] = canonical_json_bytes(campaign_receipts)
    payloads["snapshot/ingress-certificates.json"] = canonical_json_bytes(
        [attempt.certificates[0] for attempt in attempts]
    )
    return payloads


def _verify_bound_file(path: str, expected_sha256: str) -> None:
    if _executable_sha256(path) != expected_sha256:
        raise ExecutionError("bound executable identity drifted: " + path)


def _paths_overlap(left: Path, right: Path) -> bool:
    left_value = os.path.realpath(left)
    right_value = os.path.realpath(right)
    return (
        left_value == right_value
        or left_value.startswith(right_value + os.sep)
        or right_value.startswith(left_value + os.sep)
    )


def _verify_a3l8_running_sources(a3l7_root: Path) -> Any:
    root = _a3l9_canonical_absolute(str(a3l7_root), "A3L7 root")
    root_fd = _a3l9_open_absolute_directory(root)
    try:
        root_metadata = os.fstat(root_fd)
        if stat.S_IMODE(root_metadata.st_mode) != 0o700:
            raise ExecutionError("A3L8 A3L7 root mode changed")
        bindings_raw, _ = _a3l9_read_at(
            root_fd, "authority/expected-bindings.json", RESULT_CAP,
            directory_mode=0o700, file_mode=0o600,
        )
    finally:
        os.close(root_fd)
    bindings = _a3l9_bootstrap_object(
        bindings_raw, "A3L8 expected bindings"
    )
    collector = root + "/snapshot/files/" + _A3L9_COLLECTOR_RELATIVE
    _, _, snapshot_files = _a3l9_verified_snapshot_bytes(collector)
    current_collector = _read_nofollow_regular(
        Path(__file__), SNAPSHOT_FILE_LIMIT
    )
    current_validator = _read_nofollow_regular(
        Path(__file__).with_name("p01b_container_evidence.py"),
        SNAPSHOT_FILE_LIMIT,
    )
    if (
        current_collector != snapshot_files[_A3L9_COLLECTOR_RELATIVE]
        or current_validator != snapshot_files[_A3L9_VALIDATOR_RELATIVE]
        or bindings.get("collector_sha256") != sha256_bytes(current_collector)
        or bindings.get("validator_sha256") != sha256_bytes(current_validator)
    ):
        raise ExecutionError("A3L8 running source/snapshot binding changed")
    return _a3l9_evaluate_verified_evidence(
        root + "/snapshot/files",
        snapshot_files[_A3L9_VALIDATOR_RELATIVE],
    )


def _verify_a3l8_repository_boundary(
    material: A3L7CampaignMaterial, repo_root: Path, protected_file: Path,
) -> None:
    gate = _a3l9_bootstrap_object(
        material.retained_payloads["authority/a3l6-gate-bundle.json"],
        "A3L8 gate bundle", GATE_JSON_CAP,
    )
    source = gate.get("gate_source_manifest")
    if not isinstance(source, Mapping):
        raise ExecutionError("A3L8 gate repository binding is absent")
    expected_repo = source.get("repository_cwd")
    repo = _a3l9_canonical_absolute(str(repo_root), "repository root")
    if expected_repo != repo:
        raise ExecutionError("A3L8 alternate repository/worktree rejected")
    repo_fd = _a3l9_open_absolute_directory(repo)
    try:
        before = os.fstat(repo_fd)
        protected = _a3l9_canonical_absolute(
            str(protected_file), "protected repository file"
        )
        prefix = repo + "/"
        if (
            not protected.startswith(prefix)
            or protected != material.expected_bindings["protected_path"]
        ):
            raise ExecutionError("A3L8 protected file is not the exact repo child")
        relative = protected[len(prefix):]
        raw, identity = _a3l9_read_at(
            repo_fd, relative, SNAPSHOT_FILE_LIMIT,
            directory_mode=stat.S_IMODE(before.st_mode),
            file_mode=stat.S_IMODE(os.lstat(protected).st_mode),
        )
        after = os.fstat(repo_fd)
        if (
            _identity(before) != _identity(after)
            or sha256_bytes(raw) != material.expected_bindings["protected_sha256"]
            or identity["link_count"] != 1
        ):
            raise ExecutionError("A3L8 repository/protected descriptor changed")
    finally:
        os.close(repo_fd)


def _verify_a3l7_material_still_bound(
    material: A3L7CampaignMaterial,
) -> None:
    if _a3l7_candidate_payloads(material.root) != material.retained_payloads:
        raise ExecutionError("retained A3L7 tree changed after capture")


def _a3l8_open_output_parent(path: Path) -> int:
    value = _a3l9_canonical_absolute(str(path), "A3L8 output parent")
    parts = value.split("/")[1:]
    descriptor = os.open(
        "/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        for index, part in enumerate(parts):
            if not part or part in (".", ".."):
                raise ExecutionError("A3L8 output path component changed")
            try:
                next_descriptor = os.open(
                    part,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                if index != len(parts) - 1:
                    raise ExecutionError(
                        "A3L8 output ancestor does not exist"
                    )
                os.mkdir(part, 0o700, dir_fd=descriptor)
                next_descriptor = os.open(
                    part,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=descriptor,
                )
                os.fsync(next_descriptor)
                os.fsync(descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        result = descriptor
        descriptor = -1
        return result
    except OSError as error:
        raise ExecutionError(
            "A3L8 output parent traversal was rejected"
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _require_logical_directory_fd(
    path: Path, descriptor: int, label: str,
) -> None:
    reopened = _a3l9_open_absolute_directory(
        _a3l9_canonical_absolute(str(path), label)
    )
    try:
        expected = os.fstat(descriptor)
        actual = os.fstat(reopened)
        if (
            expected.st_dev, expected.st_ino, expected.st_mode,
            expected.st_uid, expected.st_gid,
        ) != (
            actual.st_dev, actual.st_ino, actual.st_mode,
            actual.st_uid, actual.st_gid,
        ):
            raise ExecutionError(label + " logical path changed")
    finally:
        os.close(reopened)


def _recover_failed_attempt(
    *,
    plan: Mapping[str, object],
    container_id: Optional[str],
    authorization_sha256: str,
    implementation_commit: str,
    raw_root: Path,
    runner: Callable[..., RawObservation],
    attempt_root_fd: Optional[int] = None,
    evidence_module: Optional[Any] = None,
) -> None:
    commands = plan.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ExecutionError("recovery cannot derive the retained attempt command")
    first = command_from_mapping(commands[0])
    prefix = first.argv[:-3]
    if tuple(first.argv[-3:-1]) != ("container", "inspect"):
        raise ExecutionError("recovery Docker prefix changed")
    attempt_root = raw_root.parent
    if attempt_root_fd is None:
        intent = _load_json_file(attempt_root / "intent.json")
    else:
        intent = _strict_json_object_bytes(
            _a3l9_read_at(
                attempt_root_fd, "intent.json", RESULT_CAP,
                directory_mode=0o700, file_mode=0o600,
            )[0], "durable recovery intent",
        )
    cid_binding: Optional[Mapping[str, object]] = None
    if attempt_root_fd is None:
        binding_path = attempt_root / "cid-binding.json"
        if binding_path.is_file():
            cid_binding = _load_json_file(binding_path)
    else:
        try:
            binding_raw = _a3l9_read_at(
                attempt_root_fd, "cid-binding.json", RESULT_CAP,
                directory_mode=0o700, file_mode=0o600,
            )[0]
        except ExecutionError as error:
            try:
                os.stat(
                    "cid-binding.json", dir_fd=attempt_root_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                binding_raw = None
            else:
                raise ExecutionError(
                    "durable CID binding storage is ambiguous"
                ) from error
        if binding_raw is not None:
            cid_binding = _strict_json_object_bytes(
                binding_raw, "durable CID binding"
            )
    recovery_fd: Optional[int] = None
    if attempt_root_fd is not None:
        try:
            os.mkdir("recovery", 0o700, dir_fd=attempt_root_fd)
        except FileExistsError as error:
            raise ExecutionError("recovery audit root already exists") from error
        recovery_fd = _a3l9_open_relative_directory(
            attempt_root_fd, ("recovery",), mode=0o700
        )
        os.fsync(recovery_fd)
        os.fsync(attempt_root_fd)
    try:
        execute_closed_recovery(
        prefix=prefix,
        environment=first.environment,
        container_name=_attempt_name(str(plan["campaign_id"]), str(plan["attempt_id"])),
        container_id=container_id,
        campaign_id=str(plan["campaign_id"]),
        attempt_id=str(plan["attempt_id"]),
        authorization_sha256=authorization_sha256,
        implementation_commit=implementation_commit,
        raw_root=raw_root,
        runner=runner,
        intent=intent,
        cid_binding=cid_binding,
        raw_root_fd=recovery_fd,
        evidence_module=evidence_module,
        )
    finally:
        if recovery_fd is not None:
            os.close(recovery_fd)


def _execute_a3l8_campaign_with_seams(
    *,
    a3l7_root: Path,
    repo_root: Path,
    protected_file: Path,
    output_parent: Path,
    runner: Callable[..., RawObservation],
    spanning_executor: Callable[..., RunningExportResult],
    repository_runner: Optional[Callable[[Sequence[str], Path], bytes]],
    rename_callable: Optional[Callable[..., Tuple[int, int]]],
    clock: Callable[[], int],
    identity_verifier: Callable[[str, str], None],
    source_binding_verifier: Optional[Callable[[Path], Any]] = None,
    repository_boundary_verifier: Optional[
        Callable[[A3L7CampaignMaterial, Path, Path], None]
    ] = None,
    post_binding_durability_hook: Optional[Callable[[], None]] = None,
) -> CampaignExecution:
    """Private hermetic seams for the one production A3L8 execution graph."""
    evidence = (
        source_binding_verifier(a3l7_root)
        if source_binding_verifier is not None else _load_evidence_module()
    )
    if evidence is None:
        raise ExecutionError("A3L8 verified evidence module is absent")
    material = _load_a3l7_campaign_material(
        a3l7_root=a3l7_root, evidence_module=evidence
    )
    if repository_boundary_verifier is not None:
        repository_boundary_verifier(material, repo_root, protected_file)
    _verify_a3l7_material_still_bound(material)
    bindings = material.expected_bindings
    campaign_plan = material.campaign_plan
    campaign_id = str(campaign_plan["campaign_id"])
    authorization_sha256 = evidence.authorization_digest(material.authorization)
    implementation_commit = str(material.authorization["implementation_commit"])
    if (
        campaign_plan["normal_plan_sha256"]
        != evidence.attempt_plan_digest(material.normal_plan)
        or campaign_plan["oom_plan_sha256"]
        != evidence.attempt_plan_digest(material.oom_plan)
    ):
        raise ExecutionError("campaign attempt-plan binding drifted")
    for field, path, digest in (
        ("Git", bindings["git_path"], bindings["git_sha256"]),
        (
            "native Python",
            bindings["native_python_path"],
            bindings["native_python_sha256"],
        ),
        ("Docker", bindings["docker_path"], bindings["docker_sha256"]),
    ):
        try:
            identity_verifier(str(path), str(digest))
        except Exception as error:
            raise ExecutionError(field + " executable identity drifted") from error
    if (
        os.path.abspath(str(protected_file)) != bindings["protected_path"]
        or _file_sha256(protected_file) != bindings["protected_sha256"]
    ):
        raise ExecutionError("protected repository file binding drifted")
    if not all(path.is_absolute() for path in (a3l7_root, repo_root, protected_file, output_parent)):
        raise ExecutionError("A3L8 paths must be absolute")
    if _paths_overlap(output_parent, repo_root) or _paths_overlap(output_parent, a3l7_root):
        raise ExecutionError("A3L8 output overlaps a retained input")
    output_parent_fd = _a3l8_open_output_parent(output_parent)
    output_metadata = os.fstat(output_parent_fd)
    if (
        not stat.S_ISDIR(output_metadata.st_mode)
        or stat.S_IMODE(output_metadata.st_mode) != 0o700
        or output_metadata.st_uid != os.geteuid()
    ):
        os.close(output_parent_fd)
        raise ExecutionError(
            "A3L8 output parent is not an owned directory: mode=%o uid=%d gid=%d device=%d"
            % (
                stat.S_IMODE(output_metadata.st_mode), output_metadata.st_uid,
                output_metadata.st_gid, output_metadata.st_dev,
            )
        )
    runtime_root = output_parent / "artifacts/runtime" / campaign_id
    attempts_parent = runtime_root / "attempts"
    operations_parent = runtime_root / "operations"
    try:
        for relative in (
            "artifacts",
            "artifacts/runtime",
            "artifacts/runtime/" + campaign_id,
            "artifacts/runtime/" + campaign_id + "/attempts",
            "artifacts/runtime/" + campaign_id + "/operations",
            "artifacts/runtime/" + campaign_id + "/operations/campaign",
        ):
            directory_fd = _a3l9_open_relative_directory(
                output_parent_fd, relative.split("/"), mode=0o700,
                create=True,
            )
            os.close(directory_fd)
        retained_runtime_fds = {
            "runtime": _a3l9_open_relative_directory(
                output_parent_fd,
                ("artifacts", "runtime", campaign_id), mode=0o700,
            ),
            "attempts": _a3l9_open_relative_directory(
                output_parent_fd,
                ("artifacts", "runtime", campaign_id, "attempts"),
                mode=0o700,
            ),
            "operations": _a3l9_open_relative_directory(
                output_parent_fd,
                ("artifacts", "runtime", campaign_id, "operations"),
                mode=0o700,
            ),
            "campaign": _a3l9_open_relative_directory(
                output_parent_fd,
                (
                    "artifacts", "runtime", campaign_id, "operations",
                    "campaign",
                ), mode=0o700,
            ),
        }
        output_after = os.fstat(output_parent_fd)
        if (
            output_after.st_dev, output_after.st_ino, output_after.st_mode,
            output_after.st_uid, output_after.st_gid,
        ) != (
            output_metadata.st_dev, output_metadata.st_ino,
            output_metadata.st_mode, output_metadata.st_uid,
            output_metadata.st_gid,
        ):
            raise ExecutionError("A3L8 output parent descriptor changed")
        repository_plan = _repository_state_plan(
            repo_root=repo_root, protected_file=protected_file, bindings=bindings
        )
        repository_before = _repository_capture_v1(
            repository_plan, clock=clock, runner=repository_runner
        )
    except BaseException:
        for descriptor in locals().get("retained_runtime_fds", {}).values():
            os.close(descriptor)
        os.close(output_parent_fd)
        raise
    campaign_sha256 = evidence.campaign_plan_digest(campaign_plan)
    campaign_observations: List[RawObservation] = []
    attempts: List[AttemptExecution] = []
    staging = output_parent / (".p01b-staging-" + campaign_id)
    final = output_parent / ("p01b-candidate-" + campaign_id)
    try:
        campaign_commands = [
            campaign_plan["native_command"],
            *campaign_plan["metadata_commands"],
        ]
        for completion, command_value in enumerate(campaign_commands):
            _require_logical_directory_fd(
                operations_parent / "campaign",
                retained_runtime_fds["campaign"],
                "campaign operation root",
            )
            previous = (
                campaign_observations[-1].digest
                if campaign_observations else None
            )
            raw = runner(
                command_from_mapping(command_value),
                plan_sha256=campaign_sha256,
                completion_ordinal=completion,
                previous_observation_sha256=previous,
                raw_root=operations_parent / "campaign",
                raw_root_fd=retained_runtime_fds["campaign"],
            )
            observation = _logical_operation_observation(
                raw, "campaign", completion, previous, evidence
            )
            _require_success(observation, str(observation.value["role"]))
            campaign_observations.append(observation)
        native_result = evidence.parse_probe_result(
            campaign_observations[0].stdout, "native-reference"
        )
        campaign_receipts = evidence.build_receipt_chain(
            "campaign",
            campaign_plan,
            [(item.value, item.stdout, item.stderr) for item in campaign_observations],
        )

        def run_attempt(plan: Mapping[str, object]) -> AttemptExecution:
            attempt_id = str(plan["attempt_id"])
            attempt_state: Dict[str, str] = {}
            attempt_root = attempts_parent / attempt_id
            os.mkdir(attempt_id, 0o700, dir_fd=retained_runtime_fds["attempts"])
            attempt_root_fd = _a3l9_open_relative_directory(
                retained_runtime_fds["attempts"], (attempt_id,), mode=0o700
            )
            os.mkdir(attempt_id, 0o700, dir_fd=retained_runtime_fds["operations"])
            raw_root_fd = _a3l9_open_relative_directory(
                retained_runtime_fds["operations"], (attempt_id,), mode=0o700
            )
            os.fsync(retained_runtime_fds["attempts"])
            os.fsync(retained_runtime_fds["operations"])
            try:
                return _execute_attempt(
                    plan=plan,
                    authorization_sha256=authorization_sha256,
                    implementation_commit=implementation_commit,
                    snapshot=material.snapshot,
                    snapshot_pair=material.snapshot_graph,
                    raw_root=operations_parent / attempt_id,
                    attempt_root=attempt_root,
                    raw_root_fd=raw_root_fd,
                    attempt_root_fd=attempt_root_fd,
                    runner=runner,
                    spanning_executor=spanning_executor,
                    clock=clock,
                    container_id_sink=lambda value: attempt_state.__setitem__(
                        "container_id", value
                    ),
                    evidence_module=evidence,
                    post_binding_durability_hook=
                        post_binding_durability_hook,
                )
            except BaseException as attempt_error:
                container_id = attempt_state.get("container_id")
                recovery_error: Optional[BaseException] = None
                try:
                    os.stat(
                        "intent.json", dir_fd=attempt_root_fd,
                        follow_symlinks=False,
                    )
                    has_intent = True
                except FileNotFoundError:
                    has_intent = False
                if has_intent:
                    try:
                        _recover_failed_attempt(
                            plan=plan,
                            container_id=container_id,
                            authorization_sha256=authorization_sha256,
                            implementation_commit=implementation_commit,
                            raw_root=attempt_root / "recovery",
                            attempt_root_fd=attempt_root_fd,
                            runner=runner,
                            evidence_module=evidence,
                        )
                    except BaseException as error:
                        recovery_error = error
                try:
                    os.stat(
                        "failure.json", dir_fd=attempt_root_fd,
                        follow_symlinks=False,
                    )
                    has_failure = True
                except FileNotFoundError:
                    has_failure = False
                if not has_failure:
                    _a3l9_write_at(
                        attempt_root_fd, "failure.json",
                        canonical_json_bytes(
                        {
                            "schema": "hsai-p01b-container-attempt-failure-v1",
                            "attempt_id": attempt_id,
                            "container_id": container_id,
                            "error": str(attempt_error),
                            "recovery_complete": recovery_error is None,
                            "recovery_error": (
                                None if recovery_error is None else str(recovery_error)
                            ),
                        }
                        ),
                    )
                if recovery_error is not None:
                    raise ExecutionError(
                        "attempt failed and exact recovery did not close"
                    ) from recovery_error
                raise
            finally:
                os.close(raw_root_fd)
                os.close(attempt_root_fd)

        attempts.append(run_attempt(material.normal_plan))
        attempts.append(run_attempt(material.oom_plan))
        payloads = _campaign_candidate_payloads(
            material=material,
            repository_before=repository_before,
            campaign_observations=campaign_observations,
            campaign_receipts=campaign_receipts,
            native_result=native_result,
            attempts=attempts,
            evidence_module=evidence,
        )
        _verify_a3l7_material_still_bound(material)
        manifest, publication, repository_state, final_path = (
            _materialize_and_publish_candidate_v2(
                output_parent=output_parent,
                campaign_id=campaign_id,
                payloads=payloads,
                authorization_sha256=authorization_sha256,
                implementation_commit=implementation_commit,
                repository_plan=repository_plan,
                repository_before=repository_before,
                repository_runner=repository_runner,
                bindings=bindings,
                clock=clock,
                rename_callable=rename_callable,
                output_parent_fd=output_parent_fd,
                evidence_module=evidence,
            )
        )
        result = CampaignExecution(
            manifest,
            publication,
            repository_state,
            tuple(attempts),
            final_path,
        )
        for descriptor in retained_runtime_fds.values():
            os.close(descriptor)
        os.close(output_parent_fd)
        return result
    except BaseException as error:
        if os.path.lexists(staging) and not os.path.lexists(final):
            shutil.rmtree(staging, ignore_errors=True)
            _fsync_directory(output_parent)
        try:
            failure_parent_fd = _a3l9_open_relative_directory(
                output_parent_fd, ("artifacts", "failures"), mode=0o700,
                create=True,
            )
            try:
                os.mkdir(campaign_id, 0o700, dir_fd=failure_parent_fd)
                failure_root_fd = _a3l9_open_relative_directory(
                    failure_parent_fd, (campaign_id,), mode=0o700
                )
                try:
                    _a3l9_write_at(
                        failure_root_fd, "failure.json",
                        canonical_json_bytes(
                            {
                                "schema":
                                    "hsai-p01b-container-campaign-failure-v1",
                                "campaign_id": campaign_id,
                                "error": str(error),
                                "final_path_exists": os.path.lexists(final),
                            }
                        ),
                    )
                    os.fsync(failure_root_fd)
                    os.fsync(failure_parent_fd)
                finally:
                    os.close(failure_root_fd)
            finally:
                os.close(failure_parent_fd)
        except BaseException:
            pass
        for descriptor in retained_runtime_fds.values():
            os.close(descriptor)
        os.close(output_parent_fd)
        raise


def execute_a3l8_campaign(
    *,
    a3l7_root: Path,
    repo_root: Path,
    protected_file: Path,
    output_parent: Path,
) -> CampaignExecution:
    """Execute normal then OOM from one immutable accepted A3L7 root."""
    return _execute_a3l8_campaign_with_seams(
        a3l7_root=a3l7_root,
        repo_root=repo_root,
        protected_file=protected_file,
        output_parent=output_parent,
        runner=execute_direct,
        spanning_executor=orchestrate_running_export,
        repository_runner=None,
        rename_callable=None,
        clock=time.monotonic_ns,
        identity_verifier=_verify_bound_file,
        source_binding_verifier=_verify_a3l8_running_sources,
        repository_boundary_verifier=_verify_a3l8_repository_boundary,
    )


def build_readiness_event(
    *,
    plan_sha256: str,
    attempt_id: str,
    start_command: CommandSpec,
    stdout_path: str,
    stdout_prefix: bytes,
    line_offset: int,
    line: bytes,
    observed_monotonic_ns: int,
) -> Dict[str, object]:
    _require_hex64(plan_sha256, "plan_sha256")
    _require_identifier(attempt_id, "attempt_id")
    _require_absolute(stdout_path, "stdout_path")
    if READY_RE.fullmatch(line) is None:
        raise ExecutionError("readiness line is invalid")
    if line_offset < 0 or stdout_prefix[line_offset : line_offset + len(line)] != line:
        raise ExecutionError("readiness line does not match prefix")
    return {
        "attempt_id": attempt_id,
        "line_bytes": len(line),
        "line_offset": line_offset,
        "line_sha256": sha256_bytes(line),
        "observed_monotonic_ns": observed_monotonic_ns,
        "plan_sha256": plan_sha256,
        "prefix_bytes": len(stdout_prefix),
        "prefix_sha256": sha256_bytes(stdout_prefix),
        "schema": READINESS_EVENT_SCHEMA,
        "start_launch_ordinal": start_command.ordinal,
        "stdout_path": stdout_path,
    }


@dataclass(frozen=True)
class RunningExportResult:
    readiness_event: Mapping[str, object]
    export_observation: RawObservation
    release_observation: RawObservation
    start_observation: RawObservation
    payload: bytes


def _require_success(observation: RawObservation, role: str) -> None:
    if (
        observation.value.get("outcome") != "exit"
        or observation.value.get("exit_code") != 0
        or observation.value.get("stdout_truncated") is not False
        or observation.value.get("stderr_truncated") is not False
    ):
        raise ExecutionError("%s did not complete successfully" % role)


def orchestrate_running_export(
    *,
    attempt_id: str,
    plan_sha256: str,
    container_id: str,
    start_command: CommandSpec,
    export_command: CommandSpec,
    release_command: CommandSpec,
    raw_root: Path,
    raw_root_fd: Optional[int] = None,
    readiness_event_path: Path,
    first_completion_ordinal: int,
    previous_observation_sha256: Optional[str],
    tar_parser: Callable[[bytes], bytes],
    runner: Callable[..., RawObservation] = execute_direct,
    expected_start_executable_sha256: Optional[str] = None,
    emergency_kill: Optional[Callable[[], None]] = None,
    deadline_ns: Optional[int] = None,
    clock: Callable[[], int] = time.monotonic_ns,
) -> RunningExportResult:
    """Run the only spanning lifecycle: start, export while live, then release."""
    if re.fullmatch(r"[0-9a-f]{64}", container_id) is None:
        raise ExecutionError("container id is invalid")
    _require_absolute(str(raw_root), "raw_root")
    _require_absolute(str(readiness_event_path), "readiness_event_path")
    if (
        start_command.role != "start-attach"
        or export_command.role != "export-running"
        or release_command.role != "release"
    ):
        raise ExecutionError("running export roles changed")
    if deadline_ns is not None:
        start_command = _command_before_deadline(
            start_command, deadline_ns, clock
        )
    start_completion_ordinal = first_completion_ordinal + 2
    start = DirectProcess(
        start_command,
        expected_executable_sha256=expected_start_executable_sha256,
        raw_root=raw_root,
        raw_root_fd=raw_root_fd,
        storage_ordinal=start_completion_ordinal,
    )
    try:
        line_offset, declared_bytes, declared_sha256 = start.wait_for_readiness()
        observed_ns = clock()
        stdout_prefix = bytes(start.stdout)
        newline = stdout_prefix.find(b"\n", line_offset)
        if newline < 0:
            raise ExecutionError("readiness line is incomplete")
        line = stdout_prefix[line_offset : newline + 1]
        if newline + 1 != len(stdout_prefix):
            raise ExecutionError("unexpected stdout followed readiness")
        if start.raw_directory is None:
            raise ExecutionError("running export requires retained raw streams")
        event = build_readiness_event(
            plan_sha256=plan_sha256,
            attempt_id=attempt_id,
            start_command=start_command,
            stdout_path=str(start.raw_directory / "stdout.bin"),
            stdout_prefix=stdout_prefix,
            line_offset=line_offset,
            line=line,
            observed_monotonic_ns=observed_ns,
        )
        if raw_root_fd is None:
            _write_fsync(readiness_event_path, canonical_json_bytes(event))
            _fsync_directory(readiness_event_path.parent)
        else:
            _a3l9_write_at(
                raw_root_fd, readiness_event_path.name,
                canonical_json_bytes(event),
            )
            os.fsync(raw_root_fd)

        effective_export = (
            export_command if deadline_ns is None else _command_before_deadline(
                export_command, deadline_ns, clock
            )
        )
        export = runner(
            effective_export,
            plan_sha256=plan_sha256,
            completion_ordinal=first_completion_ordinal,
            previous_observation_sha256=previous_observation_sha256,
            raw_root=raw_root,
            raw_root_fd=raw_root_fd,
            container_id=container_id,
        )
        _require_success(export, "running export")
        payload = tar_parser(export.stdout)
        if not isinstance(payload, bytes):
            raise ExecutionError("TAR parser did not return payload bytes")
        if len(payload) != declared_bytes or sha256_bytes(payload) != declared_sha256:
            raise ExecutionError("running export does not match readiness")

        effective_release = (
            release_command if deadline_ns is None else _command_before_deadline(
                release_command, deadline_ns, clock
            )
        )
        release = runner(
            effective_release,
            plan_sha256=plan_sha256,
            completion_ordinal=first_completion_ordinal + 1,
            previous_observation_sha256=export.digest,
            raw_root=raw_root,
            raw_root_fd=raw_root_fd,
            container_id=container_id,
        )
        _require_success(release, "release")
        start_observation = start.complete(
            plan_sha256=plan_sha256,
            completion_ordinal=start_completion_ordinal,
            previous_observation_sha256=release.digest,
            container_id=container_id,
        )
        _require_success(start_observation, "start attach")
        if READY_RE.fullmatch(start_observation.stdout) is None:
            raise ExecutionError("start stdout was not exactly one readiness line")
        export_begin = export.value.get("started_monotonic_ns")
        export_end = export.value.get("ended_monotonic_ns")
        release_begin = release.value.get("started_monotonic_ns")
        start_begin = start_observation.value.get("started_monotonic_ns")
        start_end = start_observation.value.get("ended_monotonic_ns")
        if not all(
            isinstance(item, int) and not isinstance(item, bool)
            for item in (
                start_begin,
                export_begin,
                export_end,
                release_begin,
                start_end,
            )
        ):
            raise ExecutionError("lifecycle timing values are invalid")
        if not (
            start_begin
            <= observed_ns
            <= export_begin
            < export_end
            <= release_begin
            < start_end
        ):
            raise ExecutionError("running export ordering was not retained")
        return RunningExportResult(event, export, release, start_observation, payload)
    except BaseException:
        start.abort()
        if emergency_kill is not None:
            try:
                emergency_kill()
            except BaseException as emergency_error:
                raise ExecutionError(
                    "running export and emergency kill failed"
                ) from emergency_error
        raise


@dataclass(frozen=True)
class SnapshotEntry:
    path: str
    bytes: int
    sha256: str
    source_mode: int
    snapshot_mode: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "bytes": self.bytes,
            "path": self.path,
            "sha256": self.sha256,
            "snapshot_mode": self.snapshot_mode,
            "source_mode": self.source_mode,
        }


@dataclass(frozen=True)
class SnapshotResult:
    root: str
    entries: Tuple[SnapshotEntry, ...]
    manifest_sha256: str


def _validate_relative_path(path: str) -> Tuple[str, ...]:
    if not isinstance(path, str) or not path or path.startswith("/"):
        raise ExecutionError("snapshot path must be relative")
    if os.path.normpath(path) != path or path in {".", ".."}:
        raise ExecutionError("snapshot path is not canonical")
    parts = tuple(path.split("/"))
    if any(
        part in {"", ".", ".."} or any(char in part for char in "\0\n\r")
        for part in parts
    ):
        raise ExecutionError("snapshot path contains a forbidden component")
    return parts


def _open_source_file(root_fd: int, parts: Sequence[str]) -> int:
    directory_fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_fd
        return os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
    finally:
        os.close(directory_fd)


def _open_snapshot_directory(
    root_fd: int, parts: Sequence[str], *, create: bool
) -> int:
    directory_fd = os.dup(root_fd)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, 0o700, dir_fd=directory_fd)
                except FileExistsError:
                    pass
            next_fd = os.open(
                part,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            metadata = os.fstat(next_fd)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(next_fd)
                raise ExecutionError(
                    "snapshot destination component is not a directory"
                )
            os.close(directory_fd)
            directory_fd = next_fd
        result = directory_fd
        directory_fd = -1
        return result
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)


def _exclusive_file_at(directory_fd: int, name: str, mode: int) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, mode, dir_fd=directory_fd)
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        os.close(descriptor)
        raise ExecutionError("snapshot output is not a single-link regular file")
    os.fchmod(descriptor, mode)
    return descriptor


def create_frozen_snapshot(
    source_root: Path,
    snapshot_root: Path,
    relative_paths: Sequence[str],
) -> SnapshotResult:
    """Copy the exact snapshot file set through no-follow descriptors."""
    if (
        len(relative_paths) != SNAPSHOT_FILE_COUNT
        or len(set(relative_paths)) != SNAPSHOT_FILE_COUNT
    ):
        raise ExecutionError(
            "snapshot must contain exactly %d unique paths" % SNAPSHOT_FILE_COUNT
        )
    ordered = sorted(relative_paths)
    if list(relative_paths) != ordered:
        raise ExecutionError("snapshot paths must be lexicographically ordered")
    source_path = os.path.abspath(str(source_root))
    snapshot_path = os.path.abspath(str(snapshot_root))
    if snapshot_path == source_path or snapshot_path.startswith(source_path + os.sep):
        raise ExecutionError("snapshot must not overlap source root")
    source_fd = os.open(
        source_path,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    created = False
    snapshot_fd: Optional[int] = None
    try:
        os.mkdir(snapshot_path, 0o700)
        created = True
        snapshot_fd = os.open(
            snapshot_path,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        entries: List[SnapshotEntry] = []
        directories = {()}
        for relative in ordered:
            parts = _validate_relative_path(relative)
            input_fd = _open_source_file(source_fd, parts)
            try:
                before = os.fstat(input_fd)
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise ExecutionError(
                        "snapshot source is not a single-link regular file"
                    )
                if (
                    stat.S_IMODE(before.st_mode) != 0o644
                    or before.st_size > SNAPSHOT_FILE_LIMIT
                ):
                    raise ExecutionError("snapshot source mode or size is invalid")
                data = bytearray()
                digest = hashlib.sha256()
                while True:
                    chunk = os.read(
                        input_fd,
                        min(READ_CHUNK_BYTES, SNAPSHOT_FILE_LIMIT + 1 - len(data)),
                    )
                    if not chunk:
                        break
                    data.extend(chunk)
                    digest.update(chunk)
                    if len(data) > SNAPSHOT_FILE_LIMIT:
                        raise ExecutionError("snapshot source exceeds size limit")
                after = os.fstat(input_fd)
                if (
                    before.st_dev,
                    before.st_ino,
                    before.st_size,
                    before.st_mtime_ns,
                    before.st_ctime_ns,
                ) != (
                    after.st_dev,
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                ):
                    raise ExecutionError("snapshot source changed during read")
            finally:
                os.close(input_fd)
            for count in range(1, len(parts)):
                directories.add(tuple(parts[:count]))
            destination_directory_fd = _open_snapshot_directory(
                snapshot_fd, parts[:-1], create=True
            )
            try:
                output_fd = _exclusive_file_at(
                    destination_directory_fd, parts[-1], 0o600
                )
                try:
                    view = memoryview(data)
                    while view:
                        written = os.write(output_fd, view)
                        if written <= 0:
                            raise ExecutionError("short snapshot write")
                        view = view[written:]
                    os.fsync(output_fd)
                    os.fchmod(output_fd, 0o444)
                    final = os.fstat(output_fd)
                    if not stat.S_ISREG(final.st_mode) or final.st_nlink != 1:
                        raise ExecutionError("snapshot output identity changed")
                finally:
                    os.close(output_fd)
                verify_fd = os.open(
                    parts[-1],
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=destination_directory_fd,
                )
                try:
                    verified = os.fstat(verify_fd)
                    if (
                        not stat.S_ISREG(verified.st_mode)
                        or verified.st_nlink != 1
                        or stat.S_IMODE(verified.st_mode) != 0o444
                    ):
                        raise ExecutionError("snapshot output mode or identity changed")
                    verify_digest = hashlib.sha256()
                    while True:
                        chunk = os.read(verify_fd, READ_CHUNK_BYTES)
                        if not chunk:
                            break
                        verify_digest.update(chunk)
                    if verify_digest.hexdigest() != digest.hexdigest():
                        raise ExecutionError("snapshot output digest changed")
                finally:
                    os.close(verify_fd)
            finally:
                os.close(destination_directory_fd)
            entries.append(
                SnapshotEntry(relative, len(data), digest.hexdigest(), 0o644, 0o444)
            )
        for directory in sorted(directories, key=len, reverse=True):
            directory_fd = _open_snapshot_directory(
                snapshot_fd, directory, create=False
            )
            try:
                os.fchmod(directory_fd, 0o555)
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        manifest = [entry.to_dict() for entry in entries]
        return SnapshotResult(
            snapshot_path, tuple(entries), sha256_bytes(canonical_json_bytes(manifest))
        )
    except BaseException:
        if created:
            for directory, _, _ in os.walk(snapshot_path):
                try:
                    os.chmod(directory, 0o700)
                except FileNotFoundError:
                    pass
            shutil.rmtree(snapshot_path, ignore_errors=True)
        raise
    finally:
        if snapshot_fd is not None:
            os.close(snapshot_fd)
        os.close(source_fd)


def _file_sha256(path: Path) -> str:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(str(path), flags)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ExecutionError("path is not a single-link regular file")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, READ_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(fd)


def verify_preserved_file(path: Path, expected_sha256: str) -> None:
    _require_hex64(expected_sha256, "expected_sha256")
    if _file_sha256(path) != expected_sha256:
        raise ExecutionError("preserved file changed")


def write_failure_audit(root: Path, record: Mapping[str, object]) -> Path:
    """Durably retain one canonical failure record under a new mode-0700 root."""
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    path = root / "failure.json"
    _write_fsync(path, canonical_json_bytes(record))
    directory_fd = os.open(str(root), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return path


def _load_evidence_module() -> Any:
    try:
        import p01b_container_evidence as evidence  # type: ignore[import-not-found]
    except ImportError as error:
        raise ExecutionError("p01b_container_evidence is unavailable") from error
    return evidence


def execute_closed_recovery(
    *,
    prefix: Sequence[str],
    environment: Mapping[str, str],
    container_name: str,
    container_id: Optional[str],
    campaign_id: str,
    attempt_id: str,
    authorization_sha256: str,
    implementation_commit: str,
    raw_root: Path,
    runner: Optional[Callable[..., RawObservation]] = None,
    intent: Optional[Mapping[str, object]] = None,
    cid_binding: Optional[Mapping[str, object]] = None,
    raw_root_fd: Optional[int] = None,
    evidence_module: Optional[Any] = None,
) -> Tuple[RawObservation, ...]:
    """Durably inspect by name, then execute only the selected cleanup plan."""
    _require_hex64(authorization_sha256, "authorization_sha256")
    _require_git(implementation_commit, "implementation_commit")
    execute = execute_direct if runner is None else runner
    if raw_root_fd is not None:
        _require_logical_directory_fd(
            raw_root, raw_root_fd, "recovery audit root"
        )
    if intent is None:
        raise ExecutionError("durable recovery intent is required")
    expected_intent_fields = {
        "schema", "campaign_id", "attempt_id", "authorization_sha256",
        "implementation_commit", "container_name", "expected_labels",
        "attempt_plan_sha256", "created_monotonic_ns",
    }
    if (
        set(intent) != expected_intent_fields
        or intent.get("schema") != "hsai-p01b-container-intent-v1"
        or intent.get("campaign_id") != campaign_id
        or intent.get("attempt_id") != attempt_id
        or intent.get("authorization_sha256") != authorization_sha256
        or intent.get("implementation_commit") != implementation_commit
        or intent.get("container_name") != container_name
        or intent.get("expected_labels")
        != expected_container_labels(
            campaign_id, attempt_id, authorization_sha256,
            implementation_commit,
        )
    ):
        raise ExecutionError("durable recovery intent changed")
    intent_sha256 = domain_sha256("hsai:p01b-container-intent:v1", intent)
    cid_binding_sha256: Optional[str] = None
    bound_container_id: Optional[str] = None
    if cid_binding is not None:
        if (
            set(cid_binding) != {
                "schema", "intent_sha256", "container_id",
                "create_observation_sha256", "bound_monotonic_ns",
            }
            or cid_binding.get("schema")
            != "hsai-p01b-container-cid-binding-v1"
            or cid_binding.get("intent_sha256") != intent_sha256
        ):
            raise ExecutionError("durable CID binding changed")
        bound_value = cid_binding.get("container_id")
        if not isinstance(bound_value, str) or re.fullmatch(
            r"[0-9a-f]{64}", bound_value
        ) is None:
            raise ExecutionError("durable CID binding is invalid")
        if container_id is not None and container_id != bound_value:
            raise ExecutionError("supplied recovery CID changed")
        bound_container_id = bound_value
        cid_binding_sha256 = domain_sha256(
            "hsai:p01b-container-cid-binding:v1", cid_binding
        )
    elif container_id is not None:
        raise ExecutionError("recovery CID lacks a durable binding")
    if raw_root_fd is None:
        if raw_root.exists():
            raise ExecutionError("recovery audit root already exists")
        raw_root.mkdir(mode=0o700, parents=False, exist_ok=False)
        _fsync_directory(raw_root)
        _fsync_directory(raw_root.parent)
    elif os.listdir(raw_root_fd):
        raise ExecutionError("recovery audit root already exists")

    def persist(relative: str, raw: bytes) -> None:
        if raw_root_fd is None:
            _write_fsync(raw_root / relative, raw)
            _fsync_directory(raw_root)
        else:
            _a3l9_write_at(raw_root_fd, relative, raw)
            os.fsync(raw_root_fd)

    def sync_root() -> None:
        if raw_root_fd is None:
            _fsync_directory(raw_root)
        else:
            os.fsync(raw_root_fd)

    inspection_plan = build_recovery_inspection_plan(
        intent_sha256=intent_sha256,
        container_name=container_name,
        expected_labels=intent["expected_labels"],  # type: ignore[arg-type]
        prefix=prefix,
        environment=environment,
    )
    inspection_plan_sha256 = domain_sha256(
        "hsai:p01b-recovery-inspection-plan:v1", inspection_plan
    )
    persist("inspection-plan.json", canonical_json_bytes(inspection_plan))
    inspection_command = command_from_mapping(inspection_plan["command"])
    first = execute(
        inspection_command,
        plan_sha256=inspection_plan_sha256,
        completion_ordinal=0,
        previous_observation_sha256=None,
        raw_root=raw_root,
        raw_root_fd=raw_root_fd,
        container_id=bound_container_id,
    )
    sync_root()
    persist("inspection-receipt.json", canonical_json_bytes(first.value))
    observations = [first]
    try:
        selected_branch, observed_container_id = classify_recovery_inspection(
            first,
            container_name=container_name,
            expected_labels=intent["expected_labels"],  # type: ignore[arg-type]
            bound_container_id=bound_container_id,
            evidence_module=evidence_module,
        )
    except ExecutionError as error:
        failure = build_recovery_inspection_failure(
            intent_sha256=intent_sha256,
            inspection_plan_sha256=inspection_plan_sha256,
            inspection_receipt_sha256=first.digest,
        )
        persist("inspection-failure.json", canonical_json_bytes(failure))
        raise ExecutionError("recovery inspection failed") from error
    cleanup_plan = build_recovery_cleanup_plan(
        intent_sha256=intent_sha256,
        cid_binding_sha256=cid_binding_sha256,
        inspection_observation_sha256=first.digest,
        selected_branch=selected_branch,
        container_id=observed_container_id,
        expected_labels=intent["expected_labels"],  # type: ignore[arg-type]
        container_name=container_name,
        prefix=prefix,
        environment=environment,
    )
    cleanup_plan_sha256 = domain_sha256(
        "hsai:p01b-recovery-cleanup-plan:v1", cleanup_plan
    )
    persist("cleanup-plan.json", canonical_json_bytes(cleanup_plan))

    def persist_result(cleanup_complete: bool, failure: str) -> None:
        receipts = [item.value for item in observations]
        persist("ordered-receipts.json", canonical_json_bytes(receipts))
        result = build_recovery_result(
            intent_sha256=intent_sha256,
            inspection_plan_sha256=inspection_plan_sha256,
            cleanup_plan_sha256=cleanup_plan_sha256,
            ordered_receipts=receipts,
            selected_branch=selected_branch,
            cleanup_complete=cleanup_complete,
            failure=failure,
        )
        persist("recovery-result.json", canonical_json_bytes(result))

    if selected_branch == "collision":
        persist_result(False, "identity_collision")
        raise ExecutionError("recovery identity collision")

    cleanup_commands = cleanup_plan["commands"]
    if not isinstance(cleanup_commands, list):
        raise ExecutionError("recovery cleanup command array changed")
    terminal_status: Optional[int] = None
    for index, command_value in enumerate(cleanup_commands):
        command = command_from_mapping(command_value)
        if command.activation == "never":
            observation = build_not_run_observation(
                command,
                plan_sha256=cleanup_plan_sha256,
                completion_ordinal=index + 1,
                previous_observation_sha256=observations[-1].digest,
                raw_root=raw_root,
                raw_root_fd=raw_root_fd,
                container_id=observed_container_id,
            )
        else:
            observation = execute(
                command,
                plan_sha256=cleanup_plan_sha256,
                completion_ordinal=index + 1,
                previous_observation_sha256=observations[-1].digest,
                raw_root=raw_root,
                raw_root_fd=raw_root_fd,
                container_id=observed_container_id,
            )
        observations.append(observation)
        try:
            if command.activation == "never":
                if observation.value.get("outcome") != "not_run":
                    raise ExecutionError("recovery never command was launched")
                continue
            if command.role in {"recovery-kill", "recovery-remove"}:
                _require_success(observation, command.role)
                if observation.stdout != (str(observed_container_id) + "\n").encode("ascii") or observation.stderr != b"":
                    raise ExecutionError(command.role + " transcript changed")
            elif command.role == "recovery-wait":
                _require_success(observation, command.role)
                if re.fullmatch(rb"([0-9]+)\n", observation.stdout) is None or observation.stderr != b"":
                    raise ExecutionError("recovery wait transcript changed")
                terminal_status = int(observation.stdout[:-1])
            elif command.role == "recovery-terminal-inspect":
                _require_success(observation, command.role)
                terminal = _strict_docker_json(
                    observation.stdout, "recovery terminal inspect",
                    evidence_module,
                )
                if not isinstance(terminal, list) or len(terminal) != len(INSPECT_FIELDS) or terminal[INSPECT_FIELDS.index("Id")] != observed_container_id or terminal[INSPECT_FIELDS.index("State.Running")] is not False or terminal_status is None or terminal[INSPECT_FIELDS.index("State.ExitCode")] != terminal_status:
                    raise ExecutionError("recovery terminal inspect changed")
            elif command.role == "recovery-absence-cid":
                _validate_exact_absence(observation, str(observed_container_id))
            elif command.role == "recovery-absence-name":
                _validate_exact_absence(observation, container_name)
            elif command.role == "recovery-absence-label":
                _require_success(observation, command.role)
                if observation.stdout != b"" or observation.stderr != b"":
                    raise ExecutionError("recovery label absence was not empty")
            elif command.role == "recovery-daemon-recheck":
                _require_success(observation, command.role)
                if observation.stderr != b"":
                    raise ExecutionError("recovery daemon recheck stderr changed")
                _strict_docker_json(
                    observation.stdout, "recovery daemon recheck",
                    evidence_module,
                )
            else:
                raise ExecutionError("unknown recovery cleanup role")
        except BaseException as error:
            suffix = build_recovery_not_run_suffix(
                cleanup_plan,
                failed_command_index=index,
                plan_sha256=cleanup_plan_sha256,
                previous_observation_sha256=observation.digest,
                raw_root=raw_root,
                raw_root_fd=raw_root_fd,
            )
            observations.extend(suffix)
            persist_result(False, "recovery_incomplete")
            raise ExecutionError("recovery cleanup remained incomplete") from error
    expected_failure = (
        "campaign_failed_container_absent"
        if selected_branch == "absent"
        else "campaign_failed_container_removed"
    )
    persist_result(True, expected_failure)
    return tuple(observations)


def _strict_json_object_bytes(
    raw: bytes, label: str, cap: int = RESULT_CAP,
) -> Mapping[str, object]:
    if len(raw) > cap:
        raise ExecutionError(label + " exceeds size limit")
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ExecutionError(label + " is not strict JSON") from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ExecutionError(label + " is not canonical")
    return value


def _load_json_file(path: Path, cap: int = RESULT_CAP) -> Mapping[str, object]:
    return _strict_json_object_bytes(path.read_bytes(), "runtime material", cap)


def dispatch_runtime(
    arguments: argparse.Namespace,
    *,
    readiness_executor: Callable[..., ReadinessMaterial] = execute_a3l7_readiness,
    campaign_executor: Callable[..., CampaignExecution] = execute_a3l8_campaign,
    recovery_executor: Callable[..., Tuple[RawObservation, ...]] = execute_closed_recovery,
) -> int:
    """Validate CLI authority and dispatch only to the sole host boundary."""
    if arguments.command == "readiness-v1":
        if arguments.operator_acknowledgement != READINESS_ACKNOWLEDGEMENT:
            raise ExecutionError("readiness operator acknowledgement is absent")
        material = readiness_executor(
            readiness_plan=_load_json_file(Path(arguments.readiness_plan)),
            a3l6_gate_bundle=_load_json_file(Path(arguments.a3l6_gate_bundle)),
            user_authorization_raw=_read_nofollow_regular(
                Path(arguments.user_authorization), RESULT_CAP
            ),
            campaign_id=arguments.campaign_id,
            output_root=Path(arguments.output_root),
        )
        status = "ready" if material.readiness_result["accepted"] else "rejected"
        print(canonical_json_bytes({"root": material.root, "status": status}).decode("ascii"))
        return 0 if status == "ready" else 2
    if arguments.command == "run-v1":
        if arguments.operator_acknowledgement != RUN_ACKNOWLEDGEMENT:
            raise ExecutionError("runtime operator acknowledgement is absent")
        result = campaign_executor(
            a3l7_root=Path(arguments.a3l7_root),
            repo_root=Path(arguments.repo_root),
            protected_file=Path(arguments.protected_file),
            output_parent=Path(arguments.output_root),
        )
        print(canonical_json_bytes({"path": result.final_path, "status": "published"}).decode("ascii"))
        return 0
    if arguments.operator_acknowledgement != RECOVERY_ACKNOWLEDGEMENT:
        raise ExecutionError("recovery operator acknowledgement is absent")
    config = _load_json_file(Path(arguments.recovery_config))
    required = {
        "attempt_id",
        "authorization_sha256",
        "campaign_id",
        "container_id",
        "container_name",
        "environment",
        "implementation_commit",
        "prefix",
    }
    if set(config) != required:
        raise ExecutionError("recovery configuration fields changed")
    observations = recovery_executor(
        prefix=config["prefix"],
        environment=config["environment"],
        container_name=config["container_name"],
        container_id=config["container_id"],
        campaign_id=config["campaign_id"],
        attempt_id=config["attempt_id"],
        authorization_sha256=config["authorization_sha256"],
        implementation_commit=config["implementation_commit"],
        raw_root=Path(arguments.output_root),
    )
    print(canonical_json_bytes({"observations": len(observations), "status": "recovered"}).decode("ascii"))
    return 0


@dataclass(frozen=True)
class A3L9CommonGraph:
    evidence: Any
    snapshot_root: str
    collector_path: str
    validator_path: str
    artifact_root: str
    candidate_root: str
    candidate_files: Mapping[str, bytes]
    candidate_manifest: Mapping[str, object]
    authorization: Mapping[str, object]
    a3l6_gate_bundle: Mapping[str, object]
    snapshot_copy_manifest: Mapping[str, object]
    expected_bindings: Mapping[str, object]
    repository_state: Mapping[str, object]
    publication_record: Mapping[str, object]
    reconstructed_class_results: Tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class A3L9AcceptanceExecution:
    candidate_decision_path: str
    review_session_path: str
    review_session_durability_path: str
    review_aggregate_path: str
    acceptance_path: str
    acceptance: Mapping[str, object]


@dataclass(frozen=True)
class A3L9Bootstrap:
    snapshot_root: str
    collector_path: str
    collector_raw: bytes
    validator_raw: bytes
    candidate_root: str
    candidate_files: Mapping[str, bytes]
    candidate_manifest: Mapping[str, object]
    candidate_manifest_sha256: str
    expected_bindings: Mapping[str, object]
    snapshot_copy_manifest: Mapping[str, object]


_A3L9_COLLECTOR_RELATIVE = "tools/hsai-formal-preflight/p01b_container_execution.py"
_A3L9_VALIDATOR_RELATIVE = "tools/hsai-formal-preflight/p01b_container_evidence.py"
_A3L9_PUBLICATION_RE = re.compile(
    r"\A(.+)/artifacts/publication/([0-9a-f]{64})/publication-record\.json\Z"
)
_A3L9_DESCRIPTOR_BOOTSTRAP = "exec(" + repr("""import hashlib,os,stat,sys
fd_text,expected_sha,logical,*child_args=sys.argv[1:]
if not fd_text.isdecimal() or len(expected_sha)!=64 or any(c not in '0123456789abcdef' for c in expected_sha) or not logical.startswith('/') or os.path.abspath(logical)!=logical:
    raise SystemExit(121)
fd=int(fd_text)
before=os.fstat(fd)
if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_size>16777216:
    raise SystemExit(122)
chunks=[]
offset=0
while offset<before.st_size:
    chunk=os.pread(fd,min(65536,before.st_size-offset),offset)
    if not chunk:
        raise SystemExit(123)
    chunks.append(chunk)
    offset+=len(chunk)
raw=b''.join(chunks)
after=os.fstat(fd)
identity=lambda value:(value.st_dev,value.st_ino,value.st_mode,value.st_nlink,value.st_uid,value.st_size)
actual_sha=hashlib.sha256(raw).hexdigest()
if identity(before)!=identity(after) or len(raw)!=before.st_size or actual_sha!=expected_sha:
    raise SystemExit(124)
scope={'__name__':'__main__','__file__':logical,'__a3l9_execution_binding__':(fd,expected_sha,logical,identity(before),actual_sha,len(raw))}
sys.argv=[logical,*child_args]
exec(compile(raw,logical,'exec',dont_inherit=True),scope,scope)
""") + ")"
_A3L9_OPTIONS = {
    "decide-v3": (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "expected-bindings", "implementation-commit", "decision-output",
    ),
    "review-v2": (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "candidate-decision", "expected-bindings", "review-session",
        "review-session-durability", "role", "reviewer-id",
        "implementation-commit", "receipt-output", "review-output",
    ),
    "aggregate-v2": (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "candidate-decision", "expected-bindings", "review-session",
        "review-session-durability", "security-capability-receipt",
        "security-capability-review", "security-capability-launch",
        "correspondence-reproducibility-receipt",
        "correspondence-reproducibility-review",
        "correspondence-reproducibility-launch", "implementation-commit",
        "aggregate-output",
    ),
    "accept-v2": (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "candidate-decision", "expected-bindings", "review-session",
        "review-session-durability", "security-capability-receipt",
        "security-capability-review", "security-capability-launch",
        "correspondence-reproducibility-receipt",
        "correspondence-reproducibility-review",
        "correspondence-reproducibility-launch", "implementation-commit",
        "review-aggregate", "acceptance-output",
    ),
}


def _validate_a3l9_raw_argv(raw: Sequence[str]) -> None:
    if not raw or raw[0] not in _A3L9_OPTIONS:
        return
    options = _A3L9_OPTIONS[raw[0]]
    if len(raw) != 1 + 2 * len(options):
        raise ExecutionError("A3L9 argv arity changed")
    for index, name in enumerate(options):
        flag = raw[1 + 2 * index]
        value = raw[2 + 2 * index]
        if flag != "--" + name or not value or value.startswith("--"):
            raise ExecutionError("A3L9 argv order changed")


def _a3l9_canonical_absolute(path: str, label: str) -> str:
    _require_absolute(path, label)
    if os.path.abspath(path) != path:
        raise ExecutionError(label + " is not lexical-canonical")
    return path


def _a3l9_read_absolute_file(
    path: str, cap: int, *, directory_mode: int, file_mode: int,
) -> bytes:
    value = _a3l9_canonical_absolute(path, "A3L9 absolute file")
    parent, name = value.rsplit("/", 1)
    parent_fd = _a3l9_open_absolute_directory(parent or "/")
    try:
        return _a3l9_read_at(
            parent_fd, name, cap, directory_mode=directory_mode,
            file_mode=file_mode,
        )[0]
    finally:
        os.close(parent_fd)


def _a3l9_open_absolute_directory(path: str) -> int:
    path = _a3l9_canonical_absolute(path, "A3L9 directory")
    descriptor = os.open(
        "/", os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        for part in path.split("/")[1:]:
            if not part:
                continue
            next_descriptor = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
        result = descriptor
        descriptor = -1
        return result
    except OSError as error:
        raise ExecutionError("A3L9 directory traversal was rejected") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _a3l9_require_owned_directory(
    metadata: os.stat_result, root: os.stat_result, mode: int
) -> None:
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != mode
        or metadata.st_dev != root.st_dev
        or metadata.st_uid != root.st_uid
        or metadata.st_gid != root.st_gid
    ):
        raise ExecutionError("A3L9 directory identity changed")


def _a3l9_open_relative_directory(
    root_fd: int, parts: Sequence[str], *, mode: int, create: bool = False
) -> int:
    root = os.fstat(root_fd)
    descriptor = os.dup(root_fd)
    try:
        for part in parts:
            if not part or part in (".", "..") or "/" in part:
                raise ExecutionError("A3L9 directory component changed")
            created = False
            if create:
                try:
                    os.mkdir(part, mode, dir_fd=descriptor)
                    created = True
                except FileExistsError:
                    pass
            next_descriptor = os.open(
                part,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=descriptor,
            )
            _a3l9_require_owned_directory(os.fstat(next_descriptor), root, mode)
            if created:
                os.fsync(next_descriptor)
                os.fsync(descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        result = descriptor
        descriptor = -1
        return result
    except OSError as error:
        raise ExecutionError("A3L9 relative directory traversal was rejected") from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _a3l9_read_at(
    root_fd: int, relative: str, cap: int, *, directory_mode: int,
    file_mode: int,
) -> Tuple[bytes, Dict[str, int]]:
    parts = _validate_relative_path(relative)
    directory = _a3l9_open_relative_directory(
        root_fd, parts[:-1], mode=directory_mode
    )
    try:
        descriptor = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory,
        )
        try:
            root = os.fstat(root_fd)
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or stat.S_IMODE(before.st_mode) != file_mode
                or before.st_dev != root.st_dev
                or before.st_uid != root.st_uid
                or before.st_gid != root.st_gid
            ):
                raise ExecutionError("A3L9 file identity changed")
            raw = bytearray()
            while True:
                chunk = os.read(descriptor, min(READ_CHUNK_BYTES, cap + 1 - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
                if len(raw) > cap:
                    raise ExecutionError("A3L9 file exceeded its byte cap")
            after = os.fstat(descriptor)
            stable = (
                before.st_dev, before.st_ino, before.st_mode, before.st_nlink,
                before.st_uid, before.st_gid, before.st_size,
                before.st_mtime_ns, before.st_ctime_ns,
            ) == (
                after.st_dev, after.st_ino, after.st_mode, after.st_nlink,
                after.st_uid, after.st_gid, after.st_size,
                after.st_mtime_ns, after.st_ctime_ns,
            )
            if not stable or before.st_size != len(raw):
                raise ExecutionError("A3L9 file changed during descriptor read")
            return bytes(raw), _identity(after)
        finally:
            os.close(descriptor)
    except OSError as error:
        raise ExecutionError("A3L9 file read was rejected") from error
    finally:
        os.close(directory)


def _a3l9_write_at(root_fd: int, relative: str, raw: bytes) -> Dict[str, int]:
    parts = _validate_relative_path(relative)
    directory = _a3l9_open_relative_directory(
        root_fd, parts[:-1], mode=0o700, create=True
    )
    try:
        descriptor = _exclusive_file_at(directory, parts[-1], 0o600)
        try:
            view = memoryview(raw)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise ExecutionError("A3L9 output write was short")
                view = view[written:]
            os.fsync(descriptor)
            metadata = os.fstat(descriptor)
            identity = _identity(metadata)
        finally:
            os.close(descriptor)
        os.fsync(directory)
        return identity
    except OSError as error:
        raise ExecutionError("A3L9 exclusive output was rejected") from error
    finally:
        os.close(directory)


def _replace_fsync_at(root_fd: int, relative: str, raw: bytes) -> Dict[str, int]:
    parts = _validate_relative_path(relative)
    directory = _a3l9_open_relative_directory(
        root_fd, parts[:-1], mode=0o700
    )
    try:
        descriptor = os.open(
            parts[-1],
            os.O_WRONLY | os.O_TRUNC | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory,
        )
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ExecutionError("descriptor replacement target changed")
            view = memoryview(raw)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise ExecutionError("descriptor replacement write was short")
                view = view[written:]
            os.fsync(descriptor)
            identity = _identity(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        os.fsync(directory)
        return identity
    finally:
        os.close(directory)


def _publication_file_reopen_at(root_fd: int, relative: str) -> Dict[str, object]:
    raw, identity = _a3l9_read_at(
        root_fd, relative, TAR_CAP, directory_mode=0o700, file_mode=0o600
    )
    return {
        "identity": identity,
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
    }


def _a3l9_tree_paths(root_fd: int, *, directory_mode: int) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    root = os.fstat(root_fd)
    files: List[str] = []
    directories: List[str] = []

    def visit(directory_fd: int, prefix: str) -> None:
        try:
            names = sorted(os.listdir(directory_fd), key=lambda item: item.encode("ascii"))
        except (OSError, UnicodeEncodeError) as error:
            raise ExecutionError("A3L9 inventory was rejected") from error
        for name in names:
            relative = name if not prefix else prefix + "/" + name
            try:
                metadata = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as error:
                raise ExecutionError("A3L9 inventory entry changed") from error
            if stat.S_ISDIR(metadata.st_mode):
                _a3l9_require_owned_directory(metadata, root, directory_mode)
                directories.append(relative)
                child = os.open(
                    name,
                    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
                try:
                    visit(child, relative)
                finally:
                    os.close(child)
            elif stat.S_ISREG(metadata.st_mode):
                files.append(relative)
            else:
                raise ExecutionError("A3L9 inventory contains a special file")
            if len(files) + len(directories) > 10_000:
                raise ExecutionError("A3L9 inventory exceeded its census cap")

    visit(root_fd, "")
    return tuple(files), tuple(directories)


def _a3l9_bootstrap_object(
    raw: bytes, label: str, cap: int = RESULT_CAP,
) -> Mapping[str, object]:
    if not isinstance(raw, bytes) or len(raw) > cap:
        raise ExecutionError(label + " exceeded its bootstrap byte cap")

    def reject_duplicates(pairs: Sequence[Tuple[str, object]]) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ExecutionError(label + " contains a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda item: (_ for _ in ()).throw(
                ExecutionError(label + " contains non-finite JSON: " + item)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ExecutionError(label + " is malformed bootstrap JSON") from error
    nodes = 0

    def walk(item: object, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > 100_000 or depth > 32:
            raise ExecutionError(label + " exceeded bootstrap structure limits")
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise ExecutionError(label + " contains a non-string key")
                walk(child, depth + 1)
        elif isinstance(item, list):
            for child in item:
                walk(child, depth + 1)
        elif not isinstance(item, (str, int, float, bool, type(None))):
            raise ExecutionError(label + " contains an unsupported value")

    walk(value, 0)
    if not isinstance(value, Mapping) or canonical_json_bytes(value) != raw:
        raise ExecutionError(label + " is not canonical bootstrap JSON")
    return value


def _a3l9_verified_snapshot_bytes(
    collector_path: str,
) -> Tuple[str, str, Mapping[str, bytes]]:
    collector = _a3l9_canonical_absolute(collector_path, "A3L9 collector")
    suffix = "/" + _A3L9_COLLECTOR_RELATIVE
    if not collector.endswith(suffix):
        raise ExecutionError("A3L9 collector is outside the immutable snapshot")
    snapshot_root = collector[:-len(suffix)]
    root_fd = _a3l9_open_absolute_directory(snapshot_root)
    try:
        root_metadata = os.fstat(root_fd)
        if stat.S_IMODE(root_metadata.st_mode) != 0o555:
            raise ExecutionError("A3L9 snapshot root is not immutable")
        snapshot_files = {
            relative: _a3l9_read_at(
                root_fd, relative, SNAPSHOT_FILE_LIMIT,
                directory_mode=0o555, file_mode=0o444,
            )[0]
            for relative in SOURCE_PATHS
        }
    finally:
        os.close(root_fd)
    return snapshot_root, collector, snapshot_files


def _a3l9_evaluate_verified_evidence(
    snapshot_root: str, validator_raw: bytes,
) -> Any:
    module = types.ModuleType("_p01b_a3l9_immutable_evidence")
    module.__file__ = snapshot_root + "/" + _A3L9_VALIDATOR_RELATIVE
    try:
        code = compile(validator_raw, module.__file__, "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception as error:
        raise ExecutionError("immutable evidence module could not be evaluated") from error
    return module


def _a3l9_strict_object(
    evidence: Any, raw: bytes, label: str, cap: int = RESULT_CAP
) -> Mapping[str, object]:
    try:
        value = evidence.strict_json_bytes(raw, cap)
    except Exception as error:
        raise ExecutionError(label + " is not strict canonical JSON") from error
    if not isinstance(value, Mapping):
        raise ExecutionError(label + " is not an object")
    return value


def _a3l9_artifact_layout(publication_path: str) -> Tuple[str, str]:
    publication_path = _a3l9_canonical_absolute(publication_path, "publication record")
    match = _A3L9_PUBLICATION_RE.fullmatch(publication_path)
    if match is None:
        raise ExecutionError("A3L9 publication path changed")
    return match.group(1), match.group(2)


def _a3l9_candidate_byte_map(
    candidate_root: str,
) -> Tuple[Mapping[str, bytes], Mapping[str, object]]:
    candidate_root = _a3l9_canonical_absolute(candidate_root, "candidate root")
    root_fd = _a3l9_open_absolute_directory(candidate_root)
    try:
        root_metadata = os.fstat(root_fd)
        if stat.S_IMODE(root_metadata.st_mode) != 0o700:
            raise ExecutionError("candidate root mode changed")
        payload_paths = candidate_payload_paths()
        expected_files = payload_paths + ("candidate-manifest.json",)
        expected_directories = sorted(
            {
                parent
                for path in expected_files
                for parent in (
                    "/".join(path.split("/")[:index])
                    for index in range(1, len(path.split("/")))
                )
            },
            key=lambda item: item.encode("ascii"),
        )
        files, directories = _a3l9_tree_paths(root_fd, directory_mode=0o700)
        if tuple(sorted(files, key=lambda item: item.encode("ascii"))) != tuple(
            sorted(expected_files, key=lambda item: item.encode("ascii"))
        ) or tuple(sorted(directories, key=lambda item: item.encode("ascii"))) != tuple(expected_directories):
            raise ExecutionError("candidate retained inventory changed")
        raw_by_path: Dict[str, bytes] = {}
        for path in expected_files:
            cap = GATE_JSON_CAP if path == "authority/a3l6-gate-bundle.json" else TAR_CAP
            raw_by_path[path] = _a3l9_read_at(
                root_fd, path, cap, directory_mode=0o700, file_mode=0o600
            )[0]
    finally:
        os.close(root_fd)
    manifest = _a3l9_bootstrap_object(
        raw_by_path["candidate-manifest.json"], "candidate manifest"
    )
    if set(manifest) != {
        "schema", "authorization_sha256", "implementation_commit", "entries",
    } or manifest.get("schema") != "hsai-p01b-container-manifest-v2":
        raise ExecutionError("candidate manifest bootstrap shape changed")
    _require_hex64(str(manifest.get("authorization_sha256")), "manifest authorization")
    _require_git(str(manifest.get("implementation_commit")), "manifest commit")
    expected_entries = [
        {
            "path": path,
            "file_type": "regular",
            "mode": 0o600,
            "link_count": 1,
            "bytes": len(raw_by_path[path]),
            "sha256": sha256_bytes(raw_by_path[path]),
        }
        for path in payload_paths
    ]
    if manifest.get("entries") != expected_entries:
        raise ExecutionError("candidate manifest bootstrap entries changed")
    if sum(len(raw_by_path[path]) for path in payload_paths) > 134_217_728:
        raise ExecutionError("candidate bootstrap aggregate byte cap exceeded")
    candidate_files = {path: raw_by_path[path] for path in payload_paths}
    return candidate_files, manifest


def _a3l9_bootstrap(
    *, candidate_root: str, expected_bindings_path: str, collector_path: str,
    publication_record: Optional[str] = None,
    repository_state: Optional[str] = None,
) -> A3L9Bootstrap:
    candidate_root = _a3l9_canonical_absolute(candidate_root, "candidate root")
    expected_bindings_path = _a3l9_canonical_absolute(
        expected_bindings_path, "expected bindings"
    )
    if expected_bindings_path != candidate_root + "/authority/expected-bindings.json":
        raise ExecutionError("A3L9 bootstrap expected-bindings path changed")
    candidate_files, manifest = _a3l9_candidate_byte_map(candidate_root)
    manifest_sha256 = domain_sha256(
        "hsai:p01b-container-manifest:v2", manifest
    )
    if publication_record is not None:
        artifact_root, path_manifest_sha256 = _a3l9_artifact_layout(
            publication_record
        )
        if path_manifest_sha256 != manifest_sha256:
            raise ExecutionError("A3L9 bootstrap publication binding changed")
        if repository_state != (
            artifact_root + "/artifacts/publication/" + manifest_sha256
            + "/repository-state.json"
        ):
            raise ExecutionError("A3L9 bootstrap repository path changed")
    bindings = _a3l9_bootstrap_object(
        candidate_files["authority/expected-bindings.json"],
        "expected bindings",
    )
    for field in (
        "validator_sha256", "collector_sha256",
        "snapshot_copy_manifest_sha256",
    ):
        value = bindings.get(field)
        if not isinstance(value, str):
            raise ExecutionError("A3L9 bootstrap binding is absent: " + field)
        _require_hex64(value, "bootstrap " + field)
    if bindings.get("implementation_commit") != manifest.get(
        "implementation_commit"
    ):
        raise ExecutionError("A3L9 bootstrap implementation/source binding changed")
    pair = _a3l9_bootstrap_object(
        candidate_files["snapshot/source-manifest.json"],
        "snapshot manifest pair",
    )
    if set(pair) != {
        "schema", "implementation_commit", "implementation_tree",
        "source_manifest", "snapshot_manifest",
    } or pair.get("schema") != "hsai-p01b-snapshot-manifest-pair-v1":
        raise ExecutionError("A3L9 bootstrap snapshot pair changed")
    copy_manifest = pair.get("snapshot_manifest")
    if not isinstance(copy_manifest, Mapping) or set(copy_manifest) != {
        "schema", "ordered_entries",
    } or copy_manifest.get("schema") != "hsai-p01b-snapshot-copy-manifest-v1":
        raise ExecutionError("A3L9 bootstrap copy manifest changed")
    snapshot_root, collector, snapshot_files = _a3l9_verified_snapshot_bytes(
        collector_path
    )
    copy_entries = copy_manifest.get("ordered_entries")
    if not isinstance(copy_entries, list) or len(copy_entries) != len(SOURCE_PATHS):
        raise ExecutionError("A3L9 bootstrap copy census changed")
    for entry, relative in zip(copy_entries, SOURCE_PATHS):
        raw = snapshot_files[relative]
        if not isinstance(entry, Mapping) or set(entry) != {
            "path", "mode", "bytes", "sha256", "descriptor_observation_sha256",
        } or entry.get("path") != relative or entry.get("mode") != 0o444:
            raise ExecutionError("A3L9 bootstrap copy entry changed: " + relative)
        descriptor_sha = entry.get("descriptor_observation_sha256")
        if not isinstance(descriptor_sha, str):
            raise ExecutionError("A3L9 bootstrap descriptor digest is absent")
        _require_hex64(descriptor_sha, "bootstrap descriptor digest")
        if (
            entry.get("bytes") != len(raw)
            or entry.get("sha256") != sha256_bytes(raw)
            or candidate_files["snapshot/files/" + relative] != raw
        ):
            raise ExecutionError("A3L9 bootstrap snapshot bytes changed: " + relative)
    copy_sha256 = domain_sha256(
        "hsai:p01b-snapshot-copy-manifest:v1", copy_manifest
    )
    collector_raw = snapshot_files[_A3L9_COLLECTOR_RELATIVE]
    validator_raw = snapshot_files[_A3L9_VALIDATOR_RELATIVE]
    if (
        bindings["snapshot_copy_manifest_sha256"] != copy_sha256
        or bindings["collector_sha256"] != sha256_bytes(collector_raw)
        or bindings["validator_sha256"] != sha256_bytes(validator_raw)
    ):
        raise ExecutionError("A3L9 bootstrap immutable hash binding changed")
    return A3L9Bootstrap(
        snapshot_root, collector, collector_raw, validator_raw, candidate_root,
        candidate_files, manifest, manifest_sha256, bindings, copy_manifest,
    )


def _a3l9_external_read(
    artifact_root: str, relative: str, cap: int = RESULT_CAP
) -> Tuple[bytes, Dict[str, int]]:
    root_fd = _a3l9_open_absolute_directory(artifact_root)
    try:
        root = os.fstat(root_fd)
        if stat.S_IMODE(root.st_mode) != 0o700:
            raise ExecutionError("A3L9 artifact root mode changed")
        return _a3l9_read_at(
            root_fd, relative, cap, directory_mode=0o700, file_mode=0o600
        )
    finally:
        os.close(root_fd)


def _a3l9_external_write(artifact_root: str, relative: str, raw: bytes) -> Dict[str, int]:
    root_fd = _a3l9_open_absolute_directory(artifact_root)
    try:
        root = os.fstat(root_fd)
        if stat.S_IMODE(root.st_mode) != 0o700:
            raise ExecutionError("A3L9 artifact root mode changed")
        return _a3l9_write_at(root_fd, relative, raw)
    finally:
        os.close(root_fd)


def _load_a3l9_common_graph(
    *, candidate_root: str, publication_record: str, repository_state: str,
    expected_bindings: str, implementation_commit: str,
    collector_path: Optional[str] = None,
) -> A3L9CommonGraph:
    if collector_path is None:
        collector_path = os.path.abspath(__file__)
    bootstrap = _a3l9_bootstrap(
        candidate_root=candidate_root,
        expected_bindings_path=expected_bindings,
        collector_path=collector_path,
        publication_record=publication_record,
        repository_state=repository_state,
    )
    evidence = _a3l9_evaluate_verified_evidence(
        bootstrap.snapshot_root, bootstrap.validator_raw
    )
    snapshot_root = bootstrap.snapshot_root
    collector = bootstrap.collector_path
    collector_raw = bootstrap.collector_raw
    validator_raw = bootstrap.validator_raw
    artifact_root, manifest_sha256 = _a3l9_artifact_layout(publication_record)
    candidate_root = bootstrap.candidate_root
    candidate_files = bootstrap.candidate_files
    manifest = bootstrap.candidate_manifest
    try:
        checked_manifest = evidence.validate_candidate_manifest(manifest)
        actual_manifest_sha256 = evidence.manifest_digest(checked_manifest)
    except Exception as error:
        raise ExecutionError("candidate manifest was rejected") from error
    if actual_manifest_sha256 != manifest_sha256:
        raise ExecutionError("candidate manifest/publication path binding drifted")
    expected_publication = (
        artifact_root + "/artifacts/publication/" + manifest_sha256
        + "/publication-record.json"
    )
    expected_repository = (
        artifact_root + "/artifacts/publication/" + manifest_sha256
        + "/repository-state.json"
    )
    expected_bindings_path = candidate_root + "/authority/expected-bindings.json"
    if (
        publication_record != expected_publication
        or repository_state != expected_repository
        or expected_bindings != expected_bindings_path
    ):
        raise ExecutionError("A3L9 common path graph changed")
    publication_raw, _ = _a3l9_external_read(
        artifact_root,
        "artifacts/publication/%s/publication-record.json" % manifest_sha256,
    )
    repository_raw, _ = _a3l9_external_read(
        artifact_root,
        "artifacts/publication/%s/repository-state.json" % manifest_sha256,
    )
    publication = _a3l9_strict_object(evidence, publication_raw, "publication record")
    repository = _a3l9_strict_object(evidence, repository_raw, "repository state")
    bindings = _a3l9_strict_object(
        evidence, candidate_files["authority/expected-bindings.json"],
        "expected bindings",
    )
    authorization = _a3l9_strict_object(
        evidence, candidate_files["readiness/authorization.json"], "authorization"
    )
    gate = _a3l9_strict_object(
        evidence, candidate_files["authority/a3l6-gate-bundle.json"], "A3L6 gate",
        int(evidence.MAX_A3L6_GATE_JSON_BYTES),
    )
    pair = _a3l9_strict_object(
        evidence, candidate_files["snapshot/source-manifest.json"],
        "snapshot manifest pair",
    )
    for field, expected in (
        ("docker_path", evidence.DOCKER_PATH),
        ("docker_sha256", evidence.DOCKER_SHA256),
        ("buildx_path", evidence.BUILDX_PATH),
        ("buildx_sha256", evidence.BUILDX_SHA256),
        ("codesign_path", evidence.CODESIGN_PATH),
        ("codesign_sha256", evidence.CODESIGN_SHA256),
        ("sandbox_exec_path", "/usr/bin/sandbox-exec"),
        ("sandbox_exec_sha256", evidence.SANDBOX_EXEC_SHA256),
    ):
        if bindings.get(field) != expected:
            raise ExecutionError("A3L9 expected tool binding drifted: " + field)
    try:
        checked_publication = evidence.validate_publication_record(publication)
        checked_repository = evidence.validate_repository_state(repository)
        checked_bindings = evidence.validate_expected_bindings(bindings)
        checked_authorization = evidence.validate_authorization(authorization)
        checked_gate = evidence.validate_a3l6_gate_bundle(gate, checked_bindings)
        evidence.validate_snapshot_manifest_pair(pair)
        copy_manifest = evidence.validate_snapshot_copy_manifest(
            pair["snapshot_manifest"]
        )
        rows = evidence.reconstruct_published_candidate(
            candidate_files, checked_manifest, checked_publication,
            checked_repository, checked_bindings,
        )
    except Exception as error:
        raise ExecutionError(
            "A3L9 retained common graph was rejected: " + str(error)
        ) from error
    if (
        checked_publication["final_path"] != candidate_root
        or checked_publication["candidate_manifest_sha256"] != manifest_sha256
        or checked_manifest["implementation_commit"] != implementation_commit
        or checked_bindings["implementation_commit"] != implementation_commit
        or checked_authorization["implementation_commit"] != implementation_commit
        or tuple(rows) != tuple(
            {"class_id": class_id, "closed": True} for class_id in CLASS_ORDER
        )
    ):
        raise ExecutionError("A3L9 common immutable binding drifted")
    copy_entries = {item["path"]: item for item in copy_manifest["ordered_entries"]}
    for relative, raw, binding_name in (
        (_A3L9_VALIDATOR_RELATIVE, validator_raw, "validator_sha256"),
        (_A3L9_COLLECTOR_RELATIVE, collector_raw, "collector_sha256"),
    ):
        candidate_relative = "snapshot/files/" + relative
        copy_entry = copy_entries.get(relative)
        if (
            candidate_files.get(candidate_relative) != raw
            or not isinstance(copy_entry, Mapping)
            or copy_entry.get("bytes") != len(raw)
            or copy_entry.get("sha256") != sha256_bytes(raw)
            or checked_bindings[binding_name] != sha256_bytes(raw)
        ):
            raise ExecutionError("A3L9 immutable validator/collector binding drifted")
    return A3L9CommonGraph(
        evidence, snapshot_root, collector,
        snapshot_root + "/" + _A3L9_VALIDATOR_RELATIVE,
        artifact_root, candidate_root, candidate_files, checked_manifest,
        checked_authorization, checked_gate, copy_manifest, checked_bindings,
        checked_repository, checked_publication, tuple(rows),
    )


def _a3l9_manifest_sha256(common: A3L9CommonGraph) -> str:
    return str(common.evidence.manifest_digest(common.candidate_manifest))


def _a3l9_external_relative(common: A3L9CommonGraph, path: str) -> str:
    path = _a3l9_canonical_absolute(path, "A3L9 external path")
    prefix = common.artifact_root + "/"
    if not path.startswith(prefix):
        raise ExecutionError("A3L9 output escaped the artifact root")
    relative = path[len(prefix):]
    _validate_relative_path(relative)
    return relative


def _a3l9_read_object_path(
    common: A3L9CommonGraph, path: str, label: str
) -> Tuple[Mapping[str, object], bytes, Dict[str, int]]:
    relative = _a3l9_external_relative(common, path)
    raw, identity = _a3l9_external_read(common.artifact_root, relative)
    return _a3l9_strict_object(common.evidence, raw, label), raw, identity


def _a3l9_decision_path(common: A3L9CommonGraph) -> str:
    return (
        common.artifact_root + "/artifacts/decision/"
        + _a3l9_manifest_sha256(common) + "/candidate-decision.json"
    )


def _a3l9_review_root(common: A3L9CommonGraph) -> str:
    return (
        common.artifact_root + "/artifacts/reviews/"
        + _a3l9_manifest_sha256(common)
    )


def _a3l9_load_session_graph(
    common: A3L9CommonGraph,
    *, candidate_decision_path: str, review_session_path: str,
    review_session_durability_path: str,
) -> Tuple[
    Mapping[str, object], bytes, Dict[str, int], Mapping[str, object], bytes,
    Mapping[str, object], bytes,
]:
    evidence = common.evidence
    if candidate_decision_path != _a3l9_decision_path(common):
        raise ExecutionError("A3L9 decision path changed")
    decision, decision_raw, decision_identity = _a3l9_read_object_path(
        common, candidate_decision_path, "candidate decision"
    )
    session, session_raw, _ = _a3l9_read_object_path(
        common, review_session_path, "review session"
    )
    durability, durability_raw, _ = _a3l9_read_object_path(
        common, review_session_durability_path, "review session durability"
    )
    expected_root = _a3l9_review_root(common)
    expected_session = expected_root + "/" + str(session.get("session_id"))
    if (
        review_session_path != expected_session + "/review-session.json"
        or review_session_durability_path
        != expected_session + "/review-session-durability.json"
    ):
        raise ExecutionError("A3L9 session path graph changed")
    try:
        evidence.validate_review_session_graph(
            session, session_raw, durability, durability_raw,
            decision, decision_raw, decision_identity,
            _a3l9_manifest_sha256(common), candidate_decision_path,
            expected_root, review_session_path, review_session_durability_path,
        )
    except Exception as error:
        raise ExecutionError("A3L9 review session graph was rejected") from error
    return (
        decision, decision_raw, decision_identity, session, session_raw,
        durability, durability_raw,
    )


def _a3l9_common_digests(
    common: A3L9CommonGraph, decision: Mapping[str, object],
    session: Mapping[str, object], durability: Mapping[str, object],
) -> Dict[str, str]:
    evidence = common.evidence
    return {
        "review_session_sha256": evidence.review_session_digest(session),
        "review_session_durability_sha256":
            evidence.review_session_durability_digest(durability),
        "authorization_sha256": evidence.authorization_digest(common.authorization),
        "candidate_manifest_sha256": evidence.manifest_digest(common.candidate_manifest),
        "candidate_decision_sha256": evidence.decision_digest(decision),
        "expected_bindings_sha256":
            evidence.expected_bindings_digest(common.expected_bindings),
        "claim_boundary_sha256": evidence.claim_boundary_digest(
            common.expected_bindings["claim_boundary"]
        ),
        "repository_state_sha256":
            evidence.repository_state_digest(common.repository_state),
        "publication_record_sha256":
            evidence.publication_record_digest(common.publication_record),
        "a3l6_gate_bundle_sha256": evidence.a3l6_gate_bundle_digest(
            common.a3l6_gate_bundle, common.expected_bindings
        ),
        "validator_sha256": str(common.expected_bindings["validator_sha256"]),
        "collector_sha256": str(common.expected_bindings["collector_sha256"]),
    }


def _a3l9_exact_child_argv(arguments: argparse.Namespace) -> List[str]:
    raw = getattr(arguments, "_raw_argv", None)
    if not isinstance(raw, list):
        raise ExecutionError("A3L9 raw argv was not retained")
    _validate_a3l9_raw_argv(raw)
    binding = globals().get("__a3l9_execution_binding__")
    if (
        not isinstance(binding, tuple) or len(binding) != 6
        or not isinstance(binding[0], int)
        or not isinstance(binding[1], str)
        or not isinstance(binding[2], str)
    ):
        raise ExecutionError("A3L9 descriptor execution binding is absent")
    return [
        "/usr/bin/python3", "-I", "-B", "-c",
        _A3L9_DESCRIPTOR_BOOTSTRAP, str(binding[0]), binding[1], binding[2],
        *raw,
    ]


def _a3l9_now() -> int:
    """Use one host-global clock across the pinned macOS Python 3.9 processes."""
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)


def _a3l9_verify_actual_child_context(arguments: argparse.Namespace) -> None:
    raw = getattr(arguments, "_raw_argv", None)
    if not isinstance(raw, list):
        raise ExecutionError("A3L9 child raw argv is absent")
    binding = globals().get("__a3l9_execution_binding__")
    if (
        not isinstance(binding, tuple) or len(binding) != 6
        or not isinstance(binding[0], int)
        or not isinstance(binding[1], str)
        or not isinstance(binding[2], str)
        or not isinstance(binding[3], tuple)
        or not isinstance(binding[4], str)
        or not isinstance(binding[5], int)
    ):
        raise ExecutionError("A3L9 child descriptor binding is absent")
    expected_argv = [binding[2], *raw]
    if sys.argv != expected_argv:
        raise ExecutionError("A3L9 child actual argv changed")
    if os.path.abspath(__file__) != binding[2]:
        raise ExecutionError("A3L9 child logical collector path changed")
    collector_fd = binding[0]
    collector_metadata = os.fstat(collector_fd)
    if not stat.S_ISREG(collector_metadata.st_mode):
        raise ExecutionError("A3L9 executed collector descriptor changed")
    executed_raw = bytearray()
    offset = 0
    while True:
        chunk = os.pread(collector_fd, READ_CHUNK_BYTES, offset)
        if not chunk:
            break
        executed_raw.extend(chunk)
        offset += len(chunk)
        if len(executed_raw) > SNAPSHOT_FILE_LIMIT:
            raise ExecutionError("A3L9 executed collector exceeded cap")
    logical_collector = _a3l9_canonical_absolute(
        arguments.collector_logical_path, "A3L9 logical collector"
    )
    logical_raw = _a3l9_read_absolute_file(
        logical_collector, SNAPSHOT_FILE_LIMIT,
        directory_mode=0o555, file_mode=0o444,
    )
    bindings_raw = _a3l9_read_absolute_file(
        arguments.expected_bindings, RESULT_CAP,
        directory_mode=0o700, file_mode=0o600,
    )
    bindings = _a3l9_bootstrap_object(
        bindings_raw, "A3L9 child expected bindings"
    )
    current_identity = (
        collector_metadata.st_dev, collector_metadata.st_ino,
        collector_metadata.st_mode, collector_metadata.st_nlink,
        collector_metadata.st_uid, collector_metadata.st_size,
    )
    if (
        bytes(executed_raw) != logical_raw
        or sha256_bytes(bytes(executed_raw)) != bindings.get("collector_sha256")
        or binding[1] != bindings.get("collector_sha256")
        or binding[2] != logical_collector
        or binding[3] != current_identity
        or binding[4] != sha256_bytes(bytes(executed_raw))
        or binding[5] != len(executed_raw)
    ):
        raise ExecutionError("A3L9 executed collector byte binding changed")
    expected_executable = "/Library/Developer/CommandLineTools/usr/bin/python3"
    if (
        sys.executable != expected_executable
        or sys.version_info[:3] != (3, 9, 6)
        or sys.flags.isolated != 1
        or sys.flags.ignore_environment != 1
        or sys.flags.no_user_site != 1
        or sys.flags.dont_write_bytecode != 1
    ):
        raise ExecutionError("A3L9 child actual interpreter context changed")
    expected_environment = {
        **A3L9_ENVIRONMENT,
        "CPATH": "/usr/local/include",
        "LIBRARY_PATH": "/usr/local/lib",
        "MANPATH": (
            "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/share/man:"
            "/Library/Developer/CommandLineTools/usr/share/man:"
            "/Library/Developer/CommandLineTools/Toolchains/"
            "XcodeDefault.xctoolchain/usr/share/man:"
        ),
        "SDKROOT": "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk",
        "__CF_USER_TEXT_ENCODING": "0x%X:0x0:0x0" % os.geteuid(),
    }
    if dict(os.environ) != expected_environment or os.getcwd() != "/":
        raise ExecutionError("A3L9 child actual environment/cwd changed")
    stdin_metadata = os.fstat(0)
    null_metadata = os.stat("/dev/null", follow_symlinks=False)
    if (
        not stat.S_ISCHR(stdin_metadata.st_mode)
        or stdin_metadata.st_rdev != null_metadata.st_rdev
    ):
        raise ExecutionError("A3L9 child stdin is not closed /dev/null")


def _a3l9_decide(arguments: argparse.Namespace) -> int:
    _a3l9_verify_actual_child_context(arguments)
    common = _load_a3l9_common_graph(
        candidate_root=arguments.candidate_root,
        publication_record=arguments.publication_record,
        repository_state=arguments.repository_state,
        expected_bindings=arguments.expected_bindings,
        implementation_commit=arguments.implementation_commit,
        collector_path=arguments.collector_logical_path,
    )
    output = _a3l9_decision_path(common)
    if arguments.decision_output != output:
        raise ExecutionError("A3L9 decision output path changed")
    decision = _a3l9_reconstruct_decision(
        common, arguments.implementation_commit
    )
    _a3l9_external_write(
        common.artifact_root, _a3l9_external_relative(common, output),
        canonical_json_bytes(decision),
    )
    reopened, reopened_raw, _ = _a3l9_read_object_path(
        common, output, "candidate decision"
    )
    if reopened != decision or reopened_raw != canonical_json_bytes(decision):
        raise ExecutionError("A3L9 decision reopen changed")
    return 0


def _a3l9_reconstruct_decision(
    common: A3L9CommonGraph, implementation_commit: str,
) -> Mapping[str, object]:
    evidence = common.evidence
    classes = {
        str(item["class_id"]): bool(item["closed"])
        for item in common.reconstructed_class_results
    }
    try:
        decision = evidence.build_atomic_decision(
            evidence.authorization_digest(common.authorization),
            implementation_commit,
            _a3l9_manifest_sha256(common), classes,
            evidence.expected_bindings_digest(common.expected_bindings),
            evidence.claim_boundary_digest(common.expected_bindings["claim_boundary"]),
            evidence.repository_state_digest(common.repository_state),
            evidence.publication_record_digest(common.publication_record),
        )
        evidence.validate_decision(decision)
    except Exception as error:
        raise ExecutionError("A3L9 atomic decision was rejected") from error
    return decision


def _a3l9_external_path_exists(
    common: A3L9CommonGraph, absolute_path: str,
) -> bool:
    relative = _a3l9_external_relative(common, absolute_path)
    parts = _validate_relative_path(relative)
    root_fd = _a3l9_open_absolute_directory(common.artifact_root)
    try:
        try:
            parent_fd = _a3l9_open_relative_directory(
                root_fd, parts[:-1], mode=0o700
            )
        except ExecutionError:
            return False
        try:
            try:
                metadata = os.stat(
                    parts[-1], dir_fd=parent_fd, follow_symlinks=False
                )
            except FileNotFoundError:
                return False
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ExecutionError("A3L9 retained external path changed")
            return True
        finally:
            os.close(parent_fd)
    finally:
        os.close(root_fd)


def _a3l9_ensure_retry_decision(
    common: A3L9CommonGraph,
    decision_path: str,
    implementation_commit: str,
    create: Callable[[], None],
) -> None:
    if not _a3l9_external_path_exists(common, decision_path):
        create()
        return
    retained_decision, retained_raw, _ = _a3l9_read_object_path(
        common, decision_path, "retained candidate decision"
    )
    expected_decision = _a3l9_reconstruct_decision(
        common, implementation_commit
    )
    if (
        retained_decision != expected_decision
        or retained_raw != canonical_json_bytes(expected_decision)
        or common.evidence.decision_digest(retained_decision)
        != common.evidence.decision_digest(expected_decision)
    ):
        raise ExecutionError("A3L9 retained decision does not match retry")


def _a3l9_review(arguments: argparse.Namespace) -> int:
    _a3l9_verify_actual_child_context(arguments)
    started = _a3l9_now()
    common = _load_a3l9_common_graph(
        candidate_root=arguments.candidate_root,
        publication_record=arguments.publication_record,
        repository_state=arguments.repository_state,
        expected_bindings=arguments.expected_bindings,
        implementation_commit=arguments.implementation_commit,
        collector_path=arguments.collector_logical_path,
    )
    if (
        arguments.role not in REVIEW_ROLE_ORDER
        or arguments.reviewer_id != A3L9_REVIEWER_IDS[arguments.role]
    ):
        raise ExecutionError("A3L9 reviewer identity changed")
    (
        decision, _decision_raw, _decision_identity, session, _session_raw,
        durability, _durability_raw,
    ) = _a3l9_load_session_graph(
        common,
        candidate_decision_path=arguments.candidate_decision,
        review_session_path=arguments.review_session,
        review_session_durability_path=arguments.review_session_durability,
    )
    session_directory = arguments.review_session.rsplit("/", 1)[0]
    expected_receipt = (
        session_directory + "/" + arguments.role
        + "/fresh-validation-receipt.json"
    )
    expected_review = session_directory + "/" + arguments.role + "/review.json"
    if (
        arguments.receipt_output != expected_receipt
        or arguments.review_output != expected_review
    ):
        raise ExecutionError("A3L9 review output path changed")
    input_digests = _a3l9_common_digests(common, decision, session, durability)
    python_observation = capture_descriptor_observation(
        Path("/usr/bin/python3"), "review-python"
    )
    ended = _a3l9_now()
    while ended <= started:
        ended = _a3l9_now()
    receipt = {
        "schema": common.evidence.SCHEMAS["fresh_validation"],
        "role": arguments.role,
        "reviewer_id": arguments.reviewer_id,
        "review_session_sha256": input_digests["review_session_sha256"],
        "review_session_durability_sha256":
            input_digests["review_session_durability_sha256"],
        "process_id": os.getpid(),
        "python_path": "/usr/bin/python3",
        "python_sha256": NATIVE_PYTHON_SHA256,
        "python_version": "3.9.6",
        "argv": _a3l9_exact_child_argv(arguments),
        "environment": dict(A3L9_ENVIRONMENT),
        "cwd": "/",
        "stdin_policy": "closed",
        "python_descriptor_observation": python_observation,
        "snapshot_copy_manifest_sha256":
            common.evidence.snapshot_copy_manifest_digest(
                common.snapshot_copy_manifest
            ),
        "validator_path": common.validator_path,
        "validator_sha256": input_digests["validator_sha256"],
        "collector_path": common.collector_path,
        "collector_sha256": input_digests["collector_sha256"],
        "started_monotonic_ns": started,
        "ended_monotonic_ns": ended,
        "input_digests": input_digests,
        "reconstructed_class_results": [
            dict(item) for item in common.reconstructed_class_results
        ],
        "result": "accept",
    }
    try:
        common.evidence.validate_fresh_validation_receipt(receipt)
        receipt_digest = common.evidence.fresh_validation_receipt_digest(receipt)
    except Exception as error:
        raise ExecutionError("A3L9 fresh receipt was rejected") from error
    review = {
        "schema": common.evidence.SCHEMAS["review"],
        "role": arguments.role,
        "reviewer_id": arguments.reviewer_id,
        "review_session_sha256": input_digests["review_session_sha256"],
        "review_session_durability_sha256":
            input_digests["review_session_durability_sha256"],
        "candidate_manifest_sha256": input_digests["candidate_manifest_sha256"],
        "candidate_decision_sha256": input_digests["candidate_decision_sha256"],
        "implementation_commit": arguments.implementation_commit,
        "expected_bindings_sha256": input_digests["expected_bindings_sha256"],
        "claim_boundary_sha256": input_digests["claim_boundary_sha256"],
        "repository_state_sha256": input_digests["repository_state_sha256"],
        "publication_record_sha256": input_digests["publication_record_sha256"],
        "validator_sha256": input_digests["validator_sha256"],
        "collector_sha256": input_digests["collector_sha256"],
        "fresh_validation_receipt_sha256": receipt_digest,
        "reconstructed_class_results": [
            dict(item) for item in common.reconstructed_class_results
        ],
        "findings": [],
        "result": "accept",
    }
    try:
        common.evidence.validate_review_record(review)
    except Exception as error:
        raise ExecutionError("A3L9 review record was rejected") from error
    _a3l9_external_write(
        common.artifact_root, _a3l9_external_relative(common, expected_receipt),
        canonical_json_bytes(receipt),
    )
    _a3l9_external_write(
        common.artifact_root, _a3l9_external_relative(common, expected_review),
        canonical_json_bytes(review),
    )
    return 0


def _a3l9_review_expected_paths(
    common: A3L9CommonGraph, arguments: argparse.Namespace, role: str,
) -> Dict[str, str]:
    prefix = role.replace("-", "_")
    return {
        "snapshot_root": common.snapshot_root,
        "candidate_root": common.candidate_root,
        "publication_record": arguments.publication_record,
        "repository_state": arguments.repository_state,
        "candidate_decision": arguments.candidate_decision,
        "expected_bindings": arguments.expected_bindings,
        "review_session": arguments.review_session,
        "review_session_durability": arguments.review_session_durability,
        "receipt_output": getattr(arguments, prefix + "_receipt"),
        "review_output": getattr(arguments, prefix + "_review"),
    }


def _a3l9_load_review_pairs(
    common: A3L9CommonGraph, arguments: argparse.Namespace,
    session: Mapping[str, object], durability: Mapping[str, object],
    decision: Mapping[str, object],
) -> Tuple[List[Mapping[str, object]], List[Mapping[str, object]], List[Mapping[str, object]], List[Mapping[str, object]]]:
    receipts: List[Mapping[str, object]] = []
    reviews: List[Mapping[str, object]] = []
    launches: List[Mapping[str, object]] = []
    contexts: List[Mapping[str, object]] = []
    for role in REVIEW_ROLE_ORDER:
        prefix = role.replace("-", "_")
        receipt_path = getattr(arguments, prefix + "_receipt")
        review_path = getattr(arguments, prefix + "_review")
        launch_path = getattr(arguments, prefix + "_launch")
        receipt, receipt_raw, _ = _a3l9_read_object_path(
            common, receipt_path, role + " receipt"
        )
        review, review_raw, _ = _a3l9_read_object_path(
            common, review_path, role + " review"
        )
        launch, _launch_raw, _ = _a3l9_read_object_path(
            common, launch_path, role + " launch"
        )
        expected_paths = _a3l9_review_expected_paths(common, arguments, role)
        expected_argv = receipt.get("argv")
        if not isinstance(expected_argv, list):
            raise ExecutionError("A3L9 receipt argv is absent")
        try:
            common.evidence.validate_fresh_review_graph(
                receipt, receipt_raw, review, review_raw, launch,
                review_session=session,
                review_session_durability=durability,
                authorization=common.authorization,
                candidate_manifest=common.candidate_manifest,
                candidate_decision=decision,
                expected_bindings=common.expected_bindings,
                repository_state=common.repository_state,
                publication_record=common.publication_record,
                a3l6_gate_bundle=common.a3l6_gate_bundle,
                snapshot_copy_manifest=common.snapshot_copy_manifest,
                candidate_files=common.candidate_files,
                reconstructed_class_results=[
                    dict(item) for item in common.reconstructed_class_results
                ],
                expected_argv=expected_argv,
                expected_paths=expected_paths,
            )
        except Exception as error:
            timing = ""
            if "timing" in str(error):
                observation = launch.get("command_observation")
                if isinstance(observation, Mapping):
                    timing = " durable=%r launch=(%r,%r) receipt=(%r,%r)" % (
                        durability.get("durable_monotonic_ns"),
                        observation.get("started_monotonic_ns"),
                        observation.get("ended_monotonic_ns"),
                        receipt.get("started_monotonic_ns"),
                        receipt.get("ended_monotonic_ns"),
                    )
            raise ExecutionError(
                "A3L9 fresh review graph was rejected: " + str(error) + timing
            ) from error
        receipts.append(receipt)
        reviews.append(review)
        launches.append(launch)
        contexts.append({
            "receipt": receipt,
            "receipt_raw": receipt_raw,
            "review": review,
            "review_raw": review_raw,
            "launch": launch,
            "expected_argv": expected_argv,
            "expected_paths": expected_paths,
        })
    return receipts, reviews, launches, contexts


def _a3l9_aggregate(arguments: argparse.Namespace) -> int:
    _a3l9_verify_actual_child_context(arguments)
    common = _load_a3l9_common_graph(
        candidate_root=arguments.candidate_root,
        publication_record=arguments.publication_record,
        repository_state=arguments.repository_state,
        expected_bindings=arguments.expected_bindings,
        implementation_commit=arguments.implementation_commit,
        collector_path=arguments.collector_logical_path,
    )
    (
        decision, _decision_raw, _decision_identity, session, _session_raw,
        durability, _durability_raw,
    ) = _a3l9_load_session_graph(
        common,
        candidate_decision_path=arguments.candidate_decision,
        review_session_path=arguments.review_session,
        review_session_durability_path=arguments.review_session_durability,
    )
    receipts, reviews, launches, _ = _a3l9_load_review_pairs(
        common, arguments, session, durability, decision
    )
    session_directory = arguments.review_session.rsplit("/", 1)[0]
    _a3l9_require_review_session_grammar(common, session_directory, "reviewed")
    try:
        aggregate = common.evidence.reconstruct_review_aggregate(
            reviews, receipts, launches
        )
        common.evidence.validate_review_aggregate(aggregate)
    except Exception as error:
        raise ExecutionError("A3L9 review aggregate was rejected") from error
    expected_output = session_directory + "/review-aggregate.json"
    if arguments.aggregate_output != expected_output:
        raise ExecutionError("A3L9 aggregate output path changed")
    _a3l9_external_write(
        common.artifact_root, _a3l9_external_relative(common, expected_output),
        canonical_json_bytes(aggregate),
    )
    return 0


def _a3l9_accept(arguments: argparse.Namespace) -> int:
    _a3l9_verify_actual_child_context(arguments)
    common = _load_a3l9_common_graph(
        candidate_root=arguments.candidate_root,
        publication_record=arguments.publication_record,
        repository_state=arguments.repository_state,
        expected_bindings=arguments.expected_bindings,
        implementation_commit=arguments.implementation_commit,
        collector_path=arguments.collector_logical_path,
    )
    (
        decision, decision_raw, decision_identity, session, session_raw,
        durability, durability_raw,
    ) = _a3l9_load_session_graph(
        common,
        candidate_decision_path=arguments.candidate_decision,
        review_session_path=arguments.review_session,
        review_session_durability_path=arguments.review_session_durability,
    )
    _receipts, _reviews, _launches, contexts = _a3l9_load_review_pairs(
        common, arguments, session, durability, decision
    )
    session_directory = arguments.review_session.rsplit("/", 1)[0]
    _a3l9_require_review_session_grammar(
        common, session_directory, "aggregated"
    )
    aggregate, aggregate_raw, _ = _a3l9_read_object_path(
        common, arguments.review_aggregate, "review aggregate"
    )
    try:
        acceptance = common.evidence.build_acceptance_record(
            aggregate, common.evidence.decision_digest(decision)
        )
        acceptance_raw = canonical_json_bytes(acceptance)
        common.evidence.validate_acceptance_graph(
            acceptance, acceptance_raw, aggregate, aggregate_raw, contexts,
            review_session=session,
            review_session_raw=session_raw,
            review_session_durability=durability,
            review_session_durability_raw=durability_raw,
            candidate_decision=decision,
            candidate_decision_raw=decision_raw,
            decision_file_identity=decision_identity,
            authorization=common.authorization,
            candidate_manifest=common.candidate_manifest,
            expected_bindings=common.expected_bindings,
            repository_state=common.repository_state,
            publication_record=common.publication_record,
            a3l6_gate_bundle=common.a3l6_gate_bundle,
            snapshot_copy_manifest=common.snapshot_copy_manifest,
            candidate_files=common.candidate_files,
            reconstructed_class_results=[
                dict(item) for item in common.reconstructed_class_results
            ],
            session_paths={
                "decision": arguments.candidate_decision,
                "review_root": _a3l9_review_root(common),
                "review_session": arguments.review_session,
                "review_session_durability": arguments.review_session_durability,
            },
        )
    except Exception as error:
        raise ExecutionError("A3L9 acceptance graph was rejected") from error
    expected_output = session_directory + "/acceptance-record.json"
    if (
        arguments.review_aggregate != session_directory + "/review-aggregate.json"
        or arguments.acceptance_output != expected_output
    ):
        raise ExecutionError("A3L9 acceptance output path changed")
    _a3l9_external_write(
        common.artifact_root, _a3l9_external_relative(common, expected_output),
        acceptance_raw,
    )
    return 0


def _a3l9_validate_review_tree(
    files: Sequence[str], directories: Sequence[str],
) -> None:
    sessions: set[str] = set()
    for directory in directories:
        parts = directory.split("/")
        _require_hex64(parts[0], "retained review session id")
        if len(parts) == 2 and parts[1] not in REVIEW_ROLE_ORDER:
            raise ExecutionError("A3L9 prior review directory changed")
        if len(parts) > 2:
            raise ExecutionError("A3L9 prior review directory depth changed")
        sessions.add(parts[0])
    for path in files:
        parts = path.split("/")
        _require_hex64(parts[0], "retained review session id")
        if len(parts) == 2:
            if parts[1] not in {
                "review-session.json", "review-session-durability.json",
                "review-aggregate.json", "acceptance-record.json",
            }:
                raise ExecutionError("A3L9 prior review file changed")
        elif len(parts) == 3:
            if parts[1] not in REVIEW_ROLE_ORDER or parts[2] not in {
                "fresh-validation-receipt.json", "review.json",
                "review-launch.json",
            }:
                raise ExecutionError("A3L9 prior role file changed")
        else:
            raise ExecutionError("A3L9 prior review file depth changed")
        sessions.add(parts[0])
    directory_set, file_set = set(directories), set(files)
    for session in sessions:
        if session not in directory_set:
            raise ExecutionError("A3L9 prior session parent is absent")
        own = {path for path in file_set if path.startswith(session + "/")}
        session_file = session + "/review-session.json"
        durability_file = session + "/review-session-durability.json"
        other = own - {session_file, durability_file}
        if durability_file in own and session_file not in own:
            raise ExecutionError("A3L9 prior durability dependency changed")
        if other and not {session_file, durability_file}.issubset(own):
            raise ExecutionError("A3L9 prior review dependency changed")
        complete_launches = True
        for role in REVIEW_ROLE_ORDER:
            role_directory = session + "/" + role
            ordered = [
                role_directory + "/fresh-validation-receipt.json",
                role_directory + "/review.json",
                role_directory + "/review-launch.json",
            ]
            present = [path in own for path in ordered]
            if present not in (
                [False, False, False], [True, False, False],
                [True, True, False], [True, True, True],
            ):
                raise ExecutionError("A3L9 prior role dependency changed")
            if any(present) and role_directory not in directory_set:
                raise ExecutionError("A3L9 prior role directory is absent")
            complete_launches = complete_launches and present[-1]
        aggregate = session + "/review-aggregate.json"
        acceptance = session + "/acceptance-record.json"
        if aggregate in own and not complete_launches:
            raise ExecutionError("A3L9 prior aggregate dependency changed")
        if acceptance in own and aggregate not in own:
            raise ExecutionError("A3L9 prior acceptance dependency changed")


def _a3l9_review_inventory(review_root: str) -> Tuple[Dict[str, int], List[Dict[str, object]]]:
    root_fd = _a3l9_open_absolute_directory(review_root)
    try:
        root_metadata = os.fstat(root_fd)
        if stat.S_IMODE(root_metadata.st_mode) != 0o700:
            raise ExecutionError("A3L9 review root mode changed")
        root_identity = _identity(root_metadata)
        files, directories = _a3l9_tree_paths(root_fd, directory_mode=0o700)
        _a3l9_validate_review_tree(files, directories)
        rows: List[Dict[str, object]] = [
            {"path": ".", "type": "directory", **root_identity}
        ]
        for relative in sorted((*files, *directories), key=lambda item: item.encode("ascii")):
            parts = _validate_relative_path(relative)
            parent_fd = _a3l9_open_relative_directory(
                root_fd, parts[:-1], mode=0o700
            )
            try:
                metadata = os.stat(
                    parts[-1], dir_fd=parent_fd, follow_symlinks=False
                )
            finally:
                os.close(parent_fd)
            kind = "directory" if stat.S_ISDIR(metadata.st_mode) else "regular"
            if (
                (kind == "directory" and stat.S_IMODE(metadata.st_mode) != 0o700)
                or (kind == "regular" and (
                    stat.S_IMODE(metadata.st_mode) != 0o600
                    or metadata.st_nlink != 1
                ))
            ):
                raise ExecutionError("A3L9 review inventory identity changed")
            rows.append({"path": relative, "type": kind, **_identity(metadata)})
        return root_identity, rows
    finally:
        os.close(root_fd)


def _a3l9_require_review_session_grammar(
    common: A3L9CommonGraph, session_directory: str, phase: str,
) -> None:
    if phase not in {"reviewed", "aggregated", "accepted"}:
        raise ExecutionError("A3L9 review grammar phase changed")
    session_directory = _a3l9_canonical_absolute(
        session_directory, "review session directory"
    )
    review_root = _a3l9_review_root(common)
    prefix = review_root + "/"
    if not session_directory.startswith(prefix):
        raise ExecutionError("A3L9 review session escaped its root")
    session_id = session_directory[len(prefix):]
    _require_hex64(session_id, "review session id")
    review_root_fd = _a3l9_open_absolute_directory(review_root)
    try:
        root_files, root_directories = _a3l9_tree_paths(
            review_root_fd, directory_mode=0o700
        )
    finally:
        os.close(review_root_fd)
    _a3l9_validate_review_tree(root_files, root_directories)
    current_files = {
        path for path in root_files if path.startswith(session_id + "/")
    }
    current_directories = {
        path for path in root_directories
        if path == session_id or path.startswith(session_id + "/")
    }
    expected_root_directories = {
        session_id,
        *(session_id + "/" + role for role in REVIEW_ROLE_ORDER),
    }
    expected_files = {
        session_id + "/review-session.json",
        session_id + "/review-session-durability.json",
        *(
            session_id + "/" + role + "/" + filename
            for role in REVIEW_ROLE_ORDER
            for filename in (
                "fresh-validation-receipt.json", "review.json",
                "review-launch.json",
            )
        ),
    }
    if phase in {"aggregated", "accepted"}:
        expected_files.add(session_id + "/review-aggregate.json")
    if phase == "accepted":
        expected_files.add(session_id + "/acceptance-record.json")
    if current_files != expected_files or current_directories != expected_root_directories:
        raise ExecutionError("A3L9 review session grammar changed")


def _a3l9_create_review_session(
    common: A3L9CommonGraph,
) -> Tuple[Mapping[str, object], Mapping[str, object], str, str]:
    evidence = common.evidence
    review_root = _a3l9_review_root(common)
    review_root_relative = _a3l9_external_relative(common, review_root)
    artifact_fd = _a3l9_open_absolute_directory(common.artifact_root)
    try:
        review_root_fd = _a3l9_open_relative_directory(
            artifact_fd, _validate_relative_path(review_root_relative),
            mode=0o700, create=True,
        )
        os.fsync(review_root_fd)
        os.close(review_root_fd)
    finally:
        os.close(artifact_fd)
    inventory_started = _a3l9_now()
    root_identity, inventory = _a3l9_review_inventory(review_root)
    inventory_ended = _a3l9_now()
    while inventory_ended <= inventory_started:
        inventory_ended = _a3l9_now()
    decision_path = _a3l9_decision_path(common)
    decision_started = _a3l9_now()
    decision, decision_raw, decision_identity = _a3l9_read_object_path(
        common, decision_path, "candidate decision"
    )
    decision_ended = _a3l9_now()
    while decision_ended <= decision_started:
        decision_ended = _a3l9_now()
    try:
        decision_domain = evidence.decision_digest(decision)
    except Exception as error:
        raise ExecutionError("A3L9 decision domain was rejected") from error
    random_fd = os.open(
        "/dev/urandom", os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        challenge = os.read(random_fd, 32)
    finally:
        os.close(random_fd)
    if len(challenge) != 32:
        raise ExecutionError("A3L9 review challenge read was not exact")
    session_id = review_session_id(challenge, decision_domain)
    session_directory = review_root + "/" + session_id
    absence_started = _a3l9_now()
    review_root_fd = _a3l9_open_absolute_directory(review_root)
    try:
        try:
            os.stat(session_id, dir_fd=review_root_fd, follow_symlinks=False)
        except FileNotFoundError:
            absence_result, absence_errno = -1, 2
        else:
            raise ExecutionError("A3L9 review session already exists")
    finally:
        os.close(review_root_fd)
    absence_ended = _a3l9_now()
    while absence_ended <= absence_started:
        absence_ended = _a3l9_now()
    created = _a3l9_now()
    while created <= absence_ended:
        created = _a3l9_now()
    session = build_review_session(
        challenge=challenge,
        candidate_manifest_sha256=_a3l9_manifest_sha256(common),
        candidate_decision_sha256=decision_domain,
        decision_file_identity=decision_identity,
        decision_file_sha256=sha256_bytes(decision_raw),
        created_monotonic_ns=created,
    )
    session_path = session_directory + "/review-session.json"
    durability_path = session_directory + "/review-session-durability.json"
    session_raw = canonical_json_bytes(session)
    session_write_started = _a3l9_now()
    session_identity = _a3l9_external_write(
        common.artifact_root, _a3l9_external_relative(common, session_path),
        session_raw,
    )
    session_write_ended = _a3l9_now()
    while session_write_ended <= session_write_started:
        session_write_ended = _a3l9_now()
    parent_fsync_started = _a3l9_now()
    session_fd = _a3l9_open_absolute_directory(session_directory)
    try:
        os.fsync(session_fd)
        session_directory_identity = _identity(os.fstat(session_fd))
    finally:
        os.close(session_fd)
    parent_fsync_ended = _a3l9_now()
    while parent_fsync_ended <= parent_fsync_started:
        parent_fsync_ended = _a3l9_now()
    absence = {
        "path": session_directory,
        "parent_identity": root_identity,
        "started_monotonic_ns": absence_started,
        "ended_monotonic_ns": absence_ended,
        "result": absence_result,
        "errno": absence_errno,
    }
    events = [
        {
            "ordinal": 0, "operation": "decision-reopen",
            "target": decision_path,
            "started_monotonic_ns": decision_started,
            "ended_monotonic_ns": decision_ended,
            "result": 0, "errno": 0, "identity": decision_identity,
            "sha256": sha256_bytes(decision_raw),
        },
        {
            "ordinal": 1, "operation": "review-session-path-absence",
            "target": session_directory,
            "started_monotonic_ns": absence_started,
            "ended_monotonic_ns": absence_ended,
            "result": -1, "errno": 2, "identity": None, "sha256": None,
        },
        {
            "ordinal": 2, "operation": "review-session-file-fsync",
            "target": session_path,
            "started_monotonic_ns": session_write_started,
            "ended_monotonic_ns": session_write_ended,
            "result": 0, "errno": 0, "identity": session_identity,
            "sha256": sha256_bytes(session_raw),
        },
        {
            "ordinal": 3, "operation": "review-session-parent-fsync",
            "target": session_directory,
            "started_monotonic_ns": parent_fsync_started,
            "ended_monotonic_ns": parent_fsync_ended,
            "result": 0, "errno": 0, "identity": session_directory_identity,
            "sha256": None,
        },
    ]
    durability = {
        "schema": evidence.SCHEMAS["review_session_durability"],
        "review_session_sha256": evidence.review_session_digest(session),
        "decision_file_identity": decision_identity,
        "review_root_path": review_root,
        "review_root_identity": root_identity,
        "review_root_inventory_started_monotonic_ns": inventory_started,
        "review_root_inventory_ended_monotonic_ns": inventory_ended,
        "review_root_inventory_before": inventory,
        "review_root_inventory_before_sha256": sha256_bytes(
            canonical_json_bytes(inventory)
        ),
        "session_path_absence_observation": absence,
        "session_file_identity": session_identity,
        "ordered_events": events,
        "durable_monotonic_ns": parent_fsync_ended,
    }
    try:
        evidence.validate_review_session_durability(durability)
    except Exception as error:
        raise ExecutionError("A3L9 review session durability was rejected") from error
    durability_raw = canonical_json_bytes(durability)
    _a3l9_external_write(
        common.artifact_root,
        _a3l9_external_relative(common, durability_path), durability_raw,
    )
    reopened = _a3l9_load_session_graph(
        common, candidate_decision_path=decision_path,
        review_session_path=session_path,
        review_session_durability_path=durability_path,
    )
    if reopened[3] != session or reopened[5] != durability:
        raise ExecutionError("A3L9 retained review session changed")
    return session, durability, session_path, durability_path


def _a3l9_retain_collector(bootstrap: A3L9Bootstrap) -> int:
    """Retain the immutable collector parent directory as launch authority."""
    root_fd = _a3l9_open_absolute_directory(bootstrap.snapshot_root)
    parent_fd = _a3l9_open_relative_directory(
        root_fd,
        _validate_relative_path(_A3L9_COLLECTOR_RELATIVE)[:-1],
        mode=0o555,
    )
    retained = False
    try:
        descriptor = os.open(
            _A3L9_COLLECTOR_RELATIVE.rsplit("/", 1)[1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o444
            or metadata.st_dev != os.fstat(root_fd).st_dev
        ):
            os.close(descriptor)
            raise ExecutionError("A3L9 retained collector identity changed")
        raw = bytearray()
        offset = 0
        while True:
            chunk = os.pread(descriptor, READ_CHUNK_BYTES, offset)
            if not chunk:
                break
            raw.extend(chunk)
            offset += len(chunk)
            if len(raw) > SNAPSHOT_FILE_LIMIT:
                os.close(descriptor)
                raise ExecutionError("A3L9 retained collector exceeded cap")
        if bytes(raw) != bootstrap.collector_raw:
            os.close(descriptor)
            raise ExecutionError("A3L9 retained collector bytes changed")
        os.close(descriptor)
        retained = True
        return parent_fd
    finally:
        if not retained:
            os.close(parent_fd)
        os.close(root_fd)


def _a3l9_open_execution_collector(
    collector_parent_fd: int, expected_raw: bytes,
) -> int:
    """Open one independent exact collector description for one child."""
    descriptor = os.open(
        _A3L9_COLLECTOR_RELATIVE.rsplit("/", 1)[1],
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=collector_parent_fd,
    )
    try:
        metadata = os.fstat(descriptor)
        parent_metadata = os.fstat(collector_parent_fd)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o444
            or metadata.st_dev != parent_metadata.st_dev
        ):
            raise ExecutionError("A3L9 execution collector identity changed")
        raw = bytearray()
        offset = 0
        while True:
            chunk = os.pread(descriptor, READ_CHUNK_BYTES, offset)
            if not chunk:
                break
            raw.extend(chunk)
            offset += len(chunk)
            if len(raw) > SNAPSHOT_FILE_LIMIT:
                raise ExecutionError("A3L9 execution collector exceeded cap")
        if bytes(raw) != expected_raw:
            raise ExecutionError("A3L9 execution collector bytes changed")
        if os.lseek(descriptor, 0, os.SEEK_SET) != 0:
            raise ExecutionError("A3L9 execution collector offset changed")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _a3l9_child_command(
    collector_path: str, raw: Sequence[str], collector_fd: int,
    collector_sha256: str,
) -> List[str]:
    _validate_a3l9_raw_argv(raw)
    _a3l9_canonical_absolute(collector_path, "A3L9 logical collector")
    _require_hex64(collector_sha256, "A3L9 collector SHA-256")
    return [
        "/usr/bin/python3", "-I", "-B", "-c", _A3L9_DESCRIPTOR_BOOTSTRAP,
        str(collector_fd), collector_sha256, collector_path, *raw,
    ]


def _a3l9_command_spec(argv: Sequence[str], ordinal: int) -> CommandSpec:
    values = list(argv)
    if (
        len(values) < 9
        or values[:5] != [
            "/usr/bin/python3", "-I", "-B", "-c",
            _A3L9_DESCRIPTOR_BOOTSTRAP,
        ]
        or re.fullmatch(r"[0-9]+", values[5]) is None
    ):
        raise ExecutionError("A3L9 child interpreter argv changed")
    collector_fd = int(values[5])
    collector_sha256 = values[6]
    _require_hex64(collector_sha256, "A3L9 collector SHA-256")
    collector = _a3l9_canonical_absolute(
        values[7], "A3L9 logical collector"
    )
    raw = values[8:]
    _validate_a3l9_raw_argv(raw)
    if values != _a3l9_child_command(
        collector, raw, collector_fd, collector_sha256
    ):
        raise ExecutionError("A3L9 child argv changed")
    return CommandSpec(
        ordinal=ordinal,
        role=raw[0],
        argv=tuple(values),
        environment=A3L9_ENVIRONMENT,
        cwd="/",
        stdin_policy="closed-null",
        stdout_cap=A3L9_STREAM_CAP,
        stderr_cap=A3L9_STREAM_CAP,
        timeout_ns=A3L9_TIMEOUT_NS,
        activation="always",
        expected_outcomes=("exit_zero",),
    )


def _a3l9_start_child(
    argv: Sequence[str], ordinal: int, collector_fd: Optional[int] = None,
) -> Tuple[CommandSpec, DirectProcess, int]:
    command = _a3l9_command_spec(argv, ordinal)
    started = _a3l9_now()
    process = DirectProcess(
        command, expected_executable_sha256=NATIVE_PYTHON_SHA256,
        pass_fds=(() if collector_fd is None else (collector_fd,)),
    )
    return command, process, started


def _a3l9_complete_child(
    command: CommandSpec, process: DirectProcess, started: int,
) -> Tuple[RawObservation, int]:
    observation = process.complete(
        plan_sha256=sha256_bytes(canonical_json_bytes(command.to_dict())),
        completion_ordinal=command.ordinal,
        previous_observation_sha256=None,
    )
    ended = _a3l9_now()
    while ended <= started:
        ended = _a3l9_now()
    return observation, ended


def _a3l9_require_child_success(
    observation: RawObservation, context: str,
) -> None:
    value = observation.value
    if (
        value["outcome"] != "exit"
        or value["exit_code"] != 0
        or value["signal"] is not None
        or observation.stdout != b""
        or observation.stderr != b""
    ):
        detail = str(value["outcome"])
        stderr = observation.stderr[:A3L9_STREAM_CAP].decode("ascii", "replace")
        if stderr:
            detail += ": " + stderr
        raise ExecutionError(
            "A3L9 " + context + " child failed: " + detail
        )


def _a3l9_run_child(
    argv: Sequence[str], ordinal: int = 0,
    collector_fd: Optional[int] = None,
) -> None:
    command, process, started = _a3l9_start_child(
        argv, ordinal, collector_fd
    )
    try:
        observation, _ = _a3l9_complete_child(command, process, started)
    except BaseException:
        process.abort()
        raise
    _a3l9_require_child_success(observation, command.role)


def _a3l9_run_retained_child(
    collector_path: str, raw: Sequence[str], ordinal: int,
    collector_parent_fd: int, expected_raw: bytes,
) -> None:
    descriptor = _a3l9_open_execution_collector(
        collector_parent_fd, expected_raw
    )
    try:
        _a3l9_run_child(
            _a3l9_child_command(
                collector_path, raw, descriptor, sha256_bytes(expected_raw)
            ),
            ordinal, descriptor,
        )
    finally:
        os.close(descriptor)


def _a3l9_launch_observation(
    command: CommandSpec, observation: RawObservation, started: int, ended: int,
) -> Dict[str, object]:
    value = observation.value
    outcome = (
        "completed"
        if value["outcome"] == "exit" and value["exit_code"] == 0
        else value["outcome"]
    )
    return {
        "role": command.role,
        "argv": list(command.argv),
        "environment": dict(command.environment),
        "cwd": command.cwd,
        "stdin_policy": "closed",
        "executable_path": command.argv[0],
        "executable_sha256": value["executable_sha256"],
        "timeout_ns": command.timeout_ns,
        "stdout_cap_bytes": command.stdout_cap,
        "stderr_cap_bytes": command.stderr_cap,
        "started_monotonic_ns": started,
        "ended_monotonic_ns": ended,
        "outcome": outcome,
        "exit_code": value["exit_code"],
        "signal": value["signal"],
        "stdout_total_bytes": len(observation.stdout),
        "stdout_retained_bytes": min(len(observation.stdout), command.stdout_cap),
        "stdout_truncated": bool(value["stdout_truncated"]),
        "stdout_base64": base64.b64encode(observation.stdout).decode("ascii"),
        "stdout_sha256": sha256_bytes(observation.stdout),
        "stderr_total_bytes": len(observation.stderr),
        "stderr_retained_bytes": min(len(observation.stderr), command.stderr_cap),
        "stderr_truncated": bool(value["stderr_truncated"]),
        "stderr_base64": base64.b64encode(observation.stderr).decode("ascii"),
        "stderr_sha256": sha256_bytes(observation.stderr),
    }


def execute_a3l9_acceptance(
    *, a3l7_root: Path, campaign: CampaignExecution, output_parent: Path,
    after_collector_retain: Optional[Callable[[], None]] = None,
) -> A3L9AcceptanceExecution:
    """Retain exact collector bytes, then run the isolated acceptance graph."""
    a3l7_value = _a3l9_canonical_absolute(str(a3l7_root), "A3L7 root")
    collector = a3l7_value + "/snapshot/files/" + _A3L9_COLLECTOR_RELATIVE
    candidate_root = _a3l9_canonical_absolute(campaign.final_path, "candidate root")
    bootstrap = _a3l9_bootstrap(
        candidate_root=candidate_root,
        expected_bindings_path=
            candidate_root + "/authority/expected-bindings.json",
        collector_path=collector,
    )
    collector_fd = _a3l9_retain_collector(bootstrap)
    try:
        if after_collector_retain is not None:
            after_collector_retain()
        return _execute_a3l9_acceptance_retained(
            a3l7_root=a3l7_root, campaign=campaign,
            output_parent=output_parent, collector_fd=collector_fd,
        )
    finally:
        os.close(collector_fd)


def _execute_a3l9_acceptance_retained(
    *, a3l7_root: Path, campaign: CampaignExecution, output_parent: Path,
    collector_fd: int,
) -> A3L9AcceptanceExecution:
    """Run the exact isolated decision/two-review/aggregate/acceptance graph."""
    a3l7_root_value = _a3l9_canonical_absolute(str(a3l7_root), "A3L7 root")
    output_value = _a3l9_canonical_absolute(str(output_parent), "A3L9 output parent")
    collector = a3l7_root_value + "/snapshot/files/" + _A3L9_COLLECTOR_RELATIVE
    candidate_root = _a3l9_canonical_absolute(campaign.final_path, "candidate root")
    bindings_path = candidate_root + "/authority/expected-bindings.json"
    bootstrap = _a3l9_bootstrap(
        candidate_root=candidate_root,
        expected_bindings_path=bindings_path,
        collector_path=collector,
    )
    if canonical_json_bytes(campaign.manifest) != canonical_json_bytes(
        bootstrap.candidate_manifest
    ):
        raise ExecutionError("A3L9 campaign manifest changed before bootstrap")
    manifest_sha256 = bootstrap.candidate_manifest_sha256
    publication_path = (
        output_value + "/artifacts/publication/" + manifest_sha256
        + "/publication-record.json"
    )
    repository_path = (
        output_value + "/artifacts/publication/" + manifest_sha256
        + "/repository-state.json"
    )
    implementation_commit = str(campaign.manifest["implementation_commit"])
    decision_path = (
        output_value + "/artifacts/decision/" + manifest_sha256
        + "/candidate-decision.json"
    )
    decide_raw = [
        "decide-v3", "--candidate-root", candidate_root,
        "--collector-logical-path", collector,
        "--publication-record", publication_path,
        "--repository-state", repository_path,
        "--expected-bindings", bindings_path,
        "--implementation-commit", implementation_commit,
        "--decision-output", decision_path,
    ]
    common = _load_a3l9_common_graph(
        candidate_root=candidate_root, publication_record=publication_path,
        repository_state=repository_path, expected_bindings=bindings_path,
        implementation_commit=implementation_commit, collector_path=collector,
    )
    _a3l9_ensure_retry_decision(
        common, decision_path, implementation_commit,
        lambda: _a3l9_run_retained_child(
            collector, decide_raw, 0, collector_fd, bootstrap.collector_raw,
        ),
    )
    session, durability, session_path, durability_path = (
        _a3l9_create_review_session(common)
    )
    session_directory = session_path.rsplit("/", 1)[0]
    review_raw_by_role: Dict[str, List[str]] = {}
    review_argv_by_role: Dict[str, List[str]] = {}
    review_paths: Dict[str, Dict[str, str]] = {}
    for role in REVIEW_ROLE_ORDER:
        receipt = session_directory + "/" + role + "/fresh-validation-receipt.json"
        review = session_directory + "/" + role + "/review.json"
        launch = session_directory + "/" + role + "/review-launch.json"
        review_paths[role] = {"receipt": receipt, "review": review, "launch": launch}
        raw = [
            "review-v2", "--candidate-root", candidate_root,
            "--collector-logical-path", collector,
            "--publication-record", publication_path,
            "--repository-state", repository_path,
            "--candidate-decision", decision_path,
            "--expected-bindings", bindings_path,
            "--review-session", session_path,
            "--review-session-durability", durability_path,
            "--role", role,
            "--reviewer-id", A3L9_REVIEWER_IDS[role],
            "--implementation-commit", implementation_commit,
            "--receipt-output", receipt,
            "--review-output", review,
        ]
        review_raw_by_role[role] = raw
    running: Dict[str, Tuple[CommandSpec, DirectProcess, int, int]] = {}
    observations: Dict[str, Mapping[str, object]] = {}
    try:
        for ordinal, role in enumerate(REVIEW_ROLE_ORDER, start=1):
            execution_fd = _a3l9_open_execution_collector(
                collector_fd, bootstrap.collector_raw
            )
            try:
                review_argv_by_role[role] = _a3l9_child_command(
                    collector, review_raw_by_role[role], execution_fd,
                    sha256_bytes(bootstrap.collector_raw),
                )
                command, process, started = _a3l9_start_child(
                    review_argv_by_role[role], ordinal, execution_fd
                )
                running[role] = (command, process, started, execution_fd)
            except BaseException:
                os.close(execution_fd)
                raise
        pending = list(REVIEW_ROLE_ORDER)
        completed: Dict[str, Tuple[RawObservation, int]] = {}
        while pending:
            for role in tuple(pending):
                command, process, started, _ = running[role]
                process.pump(0.01)
                if (
                    process.reason in {
                        "timeout", "stdout_limit", "stderr_limit",
                    }
                    or (
                        process.process.poll() is not None
                        and not process.selector.get_map()
                    )
                ):
                    completed[role] = _a3l9_complete_child(
                        command, process, started
                    )
                    pending.remove(role)
        for role in REVIEW_ROLE_ORDER:
            command, _, started, execution_fd = running[role]
            observation, ended = completed[role]
            _a3l9_require_child_success(
                observation, "independent review (" + role + ")"
            )
            observations[role] = _a3l9_launch_observation(
                command, observation, started, ended
            )
            os.close(execution_fd)
    except BaseException:
        for _, process, _, execution_fd in running.values():
            process.abort()
            try:
                os.close(execution_fd)
            except OSError:
                pass
        raise
    for role in REVIEW_ROLE_ORDER:
        receipt, receipt_raw, _ = _a3l9_read_object_path(
            common, review_paths[role]["receipt"], role + " receipt"
        )
        review, review_raw, _ = _a3l9_read_object_path(
            common, review_paths[role]["review"], role + " review"
        )
        launch = build_review_launch(
            review_session_sha256=common.evidence.review_session_digest(session),
            review_session_durability_sha256=
                common.evidence.review_session_durability_digest(durability),
            claim_boundary_sha256=common.evidence.claim_boundary_digest(
                common.expected_bindings["claim_boundary"]
            ),
            role=role, reviewer_id=A3L9_REVIEWER_IDS[role],
            command_observation=observations[role],
            receipt_path=review_paths[role]["receipt"], receipt_raw=receipt_raw,
            receipt_domain_sha256=
                common.evidence.fresh_validation_receipt_digest(receipt),
            review_path=review_paths[role]["review"], review_raw=review_raw,
            review_domain_sha256=common.evidence.review_record_digest(review),
        )
        _a3l9_external_write(
            common.artifact_root,
            _a3l9_external_relative(common, review_paths[role]["launch"]),
            canonical_json_bytes(launch),
        )
    pair_flags: List[str] = []
    for role in REVIEW_ROLE_ORDER:
        prefix = "--" + role
        pair_flags.extend((
            prefix + "-receipt", review_paths[role]["receipt"],
            prefix + "-review", review_paths[role]["review"],
            prefix + "-launch", review_paths[role]["launch"],
        ))
    common_raw = [
        "--candidate-root", candidate_root,
        "--collector-logical-path", collector,
        "--publication-record", publication_path,
        "--repository-state", repository_path,
        "--candidate-decision", decision_path,
        "--expected-bindings", bindings_path,
        "--review-session", session_path,
        "--review-session-durability", durability_path,
        *pair_flags,
        "--implementation-commit", implementation_commit,
    ]
    aggregate_path = session_directory + "/review-aggregate.json"
    aggregate_raw = ["aggregate-v2", *common_raw, "--aggregate-output", aggregate_path]
    _a3l9_run_retained_child(
        collector, aggregate_raw, 3, collector_fd, bootstrap.collector_raw,
    )
    acceptance_path = session_directory + "/acceptance-record.json"
    accept_raw = [
        "accept-v2", *common_raw, "--review-aggregate", aggregate_path,
        "--acceptance-output", acceptance_path,
    ]
    _a3l9_run_retained_child(
        collector, accept_raw, 4, collector_fd, bootstrap.collector_raw,
    )
    _a3l9_require_review_session_grammar(common, session_directory, "accepted")
    acceptance, acceptance_raw, _ = _a3l9_read_object_path(
        common, acceptance_path, "acceptance record"
    )
    aggregate, aggregate_bytes, _ = _a3l9_read_object_path(
        common, aggregate_path, "review aggregate"
    )
    decision, decision_raw, decision_identity, reopened_session, session_raw, reopened_durability, durability_raw = _a3l9_load_session_graph(
        common, candidate_decision_path=decision_path,
        review_session_path=session_path,
        review_session_durability_path=durability_path,
    )
    namespace_values: Dict[str, object] = {
        "publication_record": publication_path,
        "repository_state": repository_path,
        "candidate_decision": decision_path,
        "expected_bindings": bindings_path,
        "review_session": session_path,
        "review_session_durability": durability_path,
    }
    for role in REVIEW_ROLE_ORDER:
        prefix = role.replace("-", "_")
        for kind in ("receipt", "review", "launch"):
            namespace_values[prefix + "_" + kind] = review_paths[role][kind]
    contexts = _a3l9_load_review_pairs(
        common, argparse.Namespace(**namespace_values), reopened_session,
        reopened_durability, decision,
    )[3]
    try:
        common.evidence.validate_acceptance_graph(
            acceptance, acceptance_raw, aggregate, aggregate_bytes, contexts,
            review_session=reopened_session,
            review_session_raw=session_raw,
            review_session_durability=reopened_durability,
            review_session_durability_raw=durability_raw,
            candidate_decision=decision,
            candidate_decision_raw=decision_raw,
            decision_file_identity=decision_identity,
            authorization=common.authorization,
            candidate_manifest=common.candidate_manifest,
            expected_bindings=common.expected_bindings,
            repository_state=common.repository_state,
            publication_record=common.publication_record,
            a3l6_gate_bundle=common.a3l6_gate_bundle,
            snapshot_copy_manifest=common.snapshot_copy_manifest,
            candidate_files=common.candidate_files,
            reconstructed_class_results=[
                dict(item) for item in common.reconstructed_class_results
            ],
            session_paths={
                "decision": decision_path, "review_root": _a3l9_review_root(common),
                "review_session": session_path,
                "review_session_durability": durability_path,
            },
        )
    except Exception as error:
        raise ExecutionError("parent A3L9 acceptance reopen was rejected") from error
    return A3L9AcceptanceExecution(
        decision_path, session_path, durability_path, aggregate_path,
        acceptance_path, acceptance,
    )


def dispatch_a3l9(arguments: argparse.Namespace) -> int:
    """Dispatch one exact isolated postpublication child operation."""
    handlers = {
        "decide-v3": _a3l9_decide,
        "review-v2": _a3l9_review,
        "aggregate-v2": _a3l9_aggregate,
        "accept-v2": _a3l9_accept,
    }
    handler = handlers.get(arguments.command)
    if handler is None:
        raise ExecutionError("A3L9 command changed")
    return handler(arguments)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    readiness = subparsers.add_parser("readiness-v1")
    readiness.add_argument("--readiness-plan", required=True)
    readiness.add_argument("--a3l6-gate-bundle", required=True)
    readiness.add_argument("--user-authorization", required=True)
    readiness.add_argument("--campaign-id", required=True)
    readiness.add_argument("--output-root", required=True)
    readiness.add_argument("--operator-acknowledgement", required=True)
    readiness.set_defaults(handler=dispatch_runtime)
    run = subparsers.add_parser("run-v1")
    for name in (
        "a3l7-root", "repo-root", "protected-file", "output-root",
        "operator-acknowledgement",
    ):
        # Keep these optional at parse time so a bare run-v1 reaches the
        # explicit A3L7 authority guard instead of argparse usage text.
        run.add_argument("--" + name)
    run.set_defaults(handler=dispatch_runtime)
    recovery = subparsers.add_parser("recover-v1")
    recovery.add_argument("--recovery-config", required=True)
    recovery.add_argument("--output-root", required=True)
    recovery.add_argument("--operator-acknowledgement", required=True)
    recovery.set_defaults(handler=dispatch_runtime)
    decide = subparsers.add_parser("decide-v3", allow_abbrev=False)
    for name in (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "expected-bindings", "implementation-commit", "decision-output",
    ):
        decide.add_argument("--" + name, required=True)
    decide.set_defaults(handler=dispatch_a3l9)
    review = subparsers.add_parser("review-v2", allow_abbrev=False)
    for name in (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "candidate-decision", "expected-bindings", "review-session",
        "review-session-durability", "role", "reviewer-id",
        "implementation-commit", "receipt-output", "review-output",
    ):
        review.add_argument("--" + name, required=True)
    review.set_defaults(handler=dispatch_a3l9)
    common_review_inputs = (
        "candidate-root", "collector-logical-path", "publication-record", "repository-state",
        "candidate-decision", "expected-bindings", "review-session",
        "review-session-durability", "security-capability-receipt",
        "security-capability-review", "security-capability-launch",
        "correspondence-reproducibility-receipt",
        "correspondence-reproducibility-review",
        "correspondence-reproducibility-launch", "implementation-commit",
    )
    aggregate = subparsers.add_parser("aggregate-v2", allow_abbrev=False)
    for name in (*common_review_inputs, "aggregate-output"):
        aggregate.add_argument("--" + name, required=True)
    aggregate.set_defaults(handler=dispatch_a3l9)
    accept = subparsers.add_parser("accept-v2", allow_abbrev=False)
    for name in (*common_review_inputs, "review-aggregate", "acceptance-output"):
        accept.add_argument("--" + name, required=True)
    accept.set_defaults(handler=dispatch_a3l9)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        raw = list(sys.argv[1:] if argv is None else argv)
        _validate_a3l9_raw_argv(raw)
        if raw[:1] == ["run-v1"]:
            required = (
                "--a3l7-root", "--repo-root", "--protected-file",
                "--output-root", "--operator-acknowledgement",
            )
            if any(flag not in raw for flag in required):
                raise ExecutionError(
                    "A3L7 accepted readiness, final authorization, and bound runtime inputs are required"
                )
        arguments = build_parser().parse_args(raw)
        setattr(arguments, "_raw_argv", raw)
        return arguments.handler(arguments)
    except ExecutionError as error:
        print(str(error), file=sys.stderr)
        return 2
    except SystemExit as error:
        return int(error.code)


if __name__ == "__main__":
    raise SystemExit(main())
