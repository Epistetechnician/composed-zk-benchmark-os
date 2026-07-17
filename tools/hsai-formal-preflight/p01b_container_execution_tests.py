#!/usr/bin/env python3
"""Hermetic tests for the P01B retained container execution authority."""

from __future__ import annotations

import contextlib
import base64
import hashlib
import importlib.util
import inspect
import io
import json
import os
import plistlib
import shutil
import stat
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock

import p01b_container_evidence as evidence
import p01b_container_execution as execution


HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
GIT_A = "a" * 40
GIT_B = "b" * 40
PLATFORM = "docker.io/library/python@sha256:" + HEX_C


def _gate_sandbox_active() -> bool:
    """True when running under the A3L6 execution-focused Seatbelt gate."""
    return os.environ.get("P01B_GATE_SANDBOX_ACTIVE") == "1"


def command(
    role: str,
    code: str,
    *,
    ordinal: int = 0,
    cap: int = 16_384,
    timeout_ns: int = 2_000_000_000,
) -> execution.CommandSpec:
    return execution.CommandSpec(
        ordinal=ordinal,
        role=role,
        argv=("/usr/bin/python3", "-c", code),
        environment={
            "HOME": "/nonexistent",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "TZ": "UTC",
        },
        cwd="/",
        stdin_policy="closed-null",
        stdout_cap=cap,
        stderr_cap=cap,
        timeout_ns=timeout_ns,
        activation="always",
        expected_outcomes=("exit_zero",),
    )


def make_source(root: Path) -> list[str]:
    paths = [
        "files/%02d.txt" % index for index in range(execution.SNAPSHOT_FILE_COUNT)
    ]
    (root / "files").mkdir()
    for index, relative in enumerate(paths):
        path = root / relative
        path.write_bytes(("payload-%02d" % index).encode("ascii"))
        path.chmod(0o644)
    return paths


def command_from_value(value: object) -> execution.CommandSpec:
    item = dict(value)
    return execution.CommandSpec(
        ordinal=item["ordinal"],
        role=item["role"],
        argv=tuple(item["argv"]),
        environment=item["environment"],
        cwd=item["cwd"],
        stdin_policy=item["stdin_policy"],
        stdout_cap=item["stdout_cap"],
        stderr_cap=item["stderr_cap"],
        timeout_ns=item["timeout_ns"],
        activation=item["activation"],
        expected_outcomes=tuple(item["expected_outcomes"]),
    )


def thaw(root: Path) -> None:
    if not root.exists():
        return
    for directory, directories, files in os.walk(root):
        os.chmod(directory, 0o700)
        for name in directories:
            os.chmod(os.path.join(directory, name), 0o700)
        for name in files:
            os.chmod(os.path.join(directory, name), 0o600)


def recovery_observation(
    *, stdout: bytes, stderr: bytes = b"", exit_code: int = 0
) -> execution.RawObservation:
    return execution.RawObservation(
        {"outcome": "exit", "exit_code": exit_code}, stdout, stderr
    )


def inspect_array(
    *, container_id: str, name: str, labels: dict[str, str], running: bool
) -> bytes:
    values: list[object] = [None] * len(execution.INSPECT_FIELDS)
    values[execution.INSPECT_FIELDS.index("Id")] = container_id
    values[execution.INSPECT_FIELDS.index("Name")] = name
    values[execution.INSPECT_FIELDS.index("Config.Labels")] = labels
    values[execution.INSPECT_FIELDS.index("State.Running")] = running
    return execution.canonical_json_bytes(values) + b"\n"


def focused_test_source(class_name: str, count: int = 32) -> bytes:
    lines = ["import unittest", "", "class %s(unittest.TestCase):" % class_name]
    for index in range(count):
        lines.extend(
            (
                "    def test_%03d(self):" % index,
                "        self.assertTrue(True)",
                "",
            )
        )
    lines.extend(('if __name__ == "__main__":', "    unittest.main()", ""))
    return ("\n".join(lines) + "\n").encode("ascii")


def fake_snapshot_evidence_overrides(parent: Path) -> dict[str, object]:
    host = parent / "fake-host"
    context_raw = execution.canonical_json_bytes({
        "Name": "desktop-linux",
        "Metadata": {
            "Description": "Docker Desktop",
            "GODEBUG": "x509negativeserial=1",
            "otel": {
                "OTEL_EXPORTER_OTLP_ENDPOINT":
                    "unix:///fake/otel.sock" + "x" * 60,
            },
        },
        "Endpoints": {"docker": {
            "Host": "unix:///fake/docker.sock", "SkipTLSVerify": False,
        }},
    })
    image_config = "sha256:" + "2" * 64
    rootfs = tuple("sha256:" + str(index + 3) * 64 for index in range(4))
    platform = execution.canonical_json_bytes({
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "digest": image_config,
            "mediaType": "application/vnd.oci.image.config.v1+json", "size": 1,
        },
        "layers": [{
            "digest": "sha256:" + "789a"[index] * 64,
            "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
            "size": 1,
        } for index in range(4)],
    })
    index_raw = execution.canonical_json_bytes({
        "schemaVersion": 2,
        "manifests": [{
            "digest": "sha256:" + hashlib.sha256(platform).hexdigest(),
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "platform": {"architecture": "arm64", "os": "linux", "variant": "v8"},
            "size": len(platform),
        }],
    })
    raws = {
        "docker": b"fake docker client\n",
        "buildx": b"fake buildx client\n",
        "codesign": b"fake codesign client\n",
        "vm": b"fake desktop image\n",
        "kernel": b"fake desktop kernel\n",
    }
    return {
        "DOCKER_PATH": str(host / "docker"),
        "DOCKER_SHA256": hashlib.sha256(raws["docker"]).hexdigest(),
        "BUILDX_PATH": str(host / "docker-buildx"),
        "BUILDX_SHA256": hashlib.sha256(raws["buildx"]).hexdigest(),
        "CODESIGN_PATH": str(host / "codesign"),
        "CODESIGN_SHA256": hashlib.sha256(raws["codesign"]).hexdigest(),
        "DOCKER_DESKTOP_INFO_PLIST_PATH": str(host / "Info.plist"),
        "DOCKER_DESKTOP_VM_PATH": str(host / "desktop.img"),
        "DOCKER_DESKTOP_VM_SHA256": hashlib.sha256(raws["vm"]).hexdigest(),
        "DOCKER_DESKTOP_KERNEL_PATH": str(host / "kernel"),
        "DOCKER_DESKTOP_KERNEL_SHA256": hashlib.sha256(raws["kernel"]).hexdigest(),
        "DOCKER_CONTEXT_SHA256": hashlib.sha256(context_raw).hexdigest(),
        "INDEX_REFERENCE": "docker.io/library/python@sha256:"
            + hashlib.sha256(index_raw).hexdigest(),
        "IMAGE_CONFIG_DIGEST": image_config,
        "ROOTFS_DIFF_IDS": rootfs,
    }


def fixture_git(root: Path, *arguments: str) -> bytes:
    environment = {
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOME": str(root),
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "TMPDIR": str(root),
        "TZ": "UTC",
    }
    result = subprocess.run(
        ["/usr/bin/git", *arguments],
        cwd=str(root),
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "fixture Git failed: %s" % result.stderr.decode("utf-8", "replace")
        )
    return result.stdout


def make_gate_repository(
    root: Path, fixture_parent: Optional[Path] = None
) -> tuple[str, str]:
    fixture_git(root, "init", "-q")
    discovery_counts = (12, 53, 13, 68, 21, 5)
    discovery_paths = execution.SOURCE_PATHS[6:12]
    for index, relative in enumerate(execution.SOURCE_PATHS):
        path = root / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if relative in execution.REVIEWED_PATHS[:3]:
            raw = (Path(__file__).parent / Path(relative).name).read_bytes()
            if relative.endswith("p01b_container_evidence.py"):
                overrides = fake_snapshot_evidence_overrides(
                    root.parent if fixture_parent is None else fixture_parent
                )
                raw += b"\n" + b"\n".join(
                    (name + " = " + repr(value)).encode("ascii")
                    for name, value in overrides.items()
                ) + b"\n"
        elif relative == execution.SOURCE_PATHS[-2]:
            raw = focused_test_source("ExecutionGateFixture")
        elif relative == execution.SOURCE_PATHS[-1]:
            raw = focused_test_source("EvidenceGateFixture")
        elif relative in discovery_paths:
            discovery_index = discovery_paths.index(relative)
            raw = focused_test_source(
                "DiscoveryGateFixture%02d" % discovery_index,
                discovery_counts[discovery_index],
            )
        elif relative.endswith("p01b_container_seccomp.json"):
            raw = execution.canonical_json_bytes(
                {"defaultAction": "SCMP_ACT_ERRNO", "syscalls": []}
            )
        elif relative.endswith(".json"):
            raw = execution.canonical_json_bytes(
                {"path": relative, "synthetic": True}
            )
        else:
            raw = ("# immutable fixture %02d: %s\n" % (index, relative)).encode(
                "ascii"
            )
        path.write_bytes(raw)
        path.chmod(0o644)
    fixture_git(root, "add", "--all")
    fixture_git(
        root,
        "-c",
        "user.name=A3L6 Fixture",
        "-c",
        "user.email=a3l6@example.invalid",
        "commit",
        "-q",
        "-m",
        "immutable gate fixture",
    )
    commit = fixture_git(root, "rev-parse", "HEAD").decode("ascii").strip()
    tree = fixture_git(root, "rev-parse", "HEAD^{tree}").decode("ascii").strip()
    return commit, tree


def unittest_transcript(identifiers: list[str]) -> bytes:
    rows = []
    for identifier in identifiers:
        owner, method = identifier.rsplit(".", 1)
        rows.append("%s (%s) ... ok\n" % (method, owner))
    return (
        "".join(rows)
        + "\n"
        + "-" * 70
        + "\nRan %d tests in 0.001s\n\nOK\n" % len(identifiers)
    ).encode("ascii")


def synthetic_gate_observation(
    row: dict[str, object],
    root_identity: dict[str, int],
    stderr: bytes,
    started_ns: int,
    ended_ns: int,
) -> dict[str, object]:
    return {
        "role": row["role"],
        "argv": row["argv"],
        "environment": row["environment"],
        "cwd": row["cwd"],
        "stdin_policy": row["stdin_policy"],
        "executable_path": execution.SANDBOX_EXEC_PATH,
        "executable_sha256": execution.SANDBOX_EXEC_SHA256,
        "cwd_identity_before": root_identity,
        "cwd_identity_after": root_identity,
        "timeout_ns": row["timeout_ns"],
        "stdout_cap_bytes": row["stdout_cap_bytes"],
        "stderr_cap_bytes": row["stderr_cap_bytes"],
        "started_monotonic_ns": started_ns,
        "ended_monotonic_ns": ended_ns,
        "outcome": "completed",
        "exit_code": 0,
        "signal": None,
        "stdout_total_bytes": 0,
        "stdout_retained_bytes": 0,
        "stdout_truncated": False,
        "stdout_base64": "",
        "stdout_sha256": hashlib.sha256(b"").hexdigest(),
        "stderr_total_bytes": len(stderr),
        "stderr_retained_bytes": len(stderr),
        "stderr_truncated": False,
        "stderr_base64": base64.b64encode(stderr).decode("ascii"),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }


def gate_bundle_candidate(
    run: execution.A3L6GateRun, reviews: tuple[dict[str, object], dict[str, object]]
) -> dict[str, object]:
    return {
        "schema": "hsai-p01b-a3l6-gate-bundle-v1",
        "gate_plan": dict(run.gate_plan),
        "gate_source_manifest": dict(run.gate_source_manifest),
        "implementation_commit": run.gate_plan["implementation_commit"],
        "implementation_tree": run.gate_plan["implementation_tree"],
        "python_path": "/usr/bin/python3",
        "python_sha256": execution.NATIVE_PYTHON_SHA256,
        "python_version": "3.9.6",
        "python_version_observation": dict(run.python_version_observation),
        "ordered_gate_observations": [
            dict(item) for item in run.ordered_gate_observations
        ],
        "focused_test_ids": list(run.focused_test_ids),
        "focused_test_count": run.focused_test_count,
        "discovery_test_count": run.discovery_test_count,
        "ordered_review_records": [dict(item) for item in reviews],
        "result": "accept",
    }


def gate_expected_bindings(
    run: execution.A3L6GateRun, reviews: tuple[dict[str, object], dict[str, object]]
) -> dict[str, object]:
    value = {name: "x" for name in evidence.EXPECTED_BINDING_FIELDS}
    value.update(
        {
            "schema": evidence.SCHEMAS["expected_bindings"],
            "predecessor_commit": GIT_A,
            "implementation_commit": run.gate_plan["implementation_commit"],
            "implementation_tree": run.gate_plan["implementation_tree"],
            "a3l6_audit_commit": run.gate_plan["audit_commit"],
            "claim_boundary": execution.canonical_claim_boundary(),
            "expected_focused_test_count": 64,
            "normal_expected_test_count": 151,
            "discovery_expected_test_count": 172,
            "candidate_payload_count": 201,
            "attempt_deadline_ns": 1_800_000_000_000,
            "class_order": list(execution.CLASS_ORDER),
            "evidence_level": "Level1LocalReplayOrLower",
            "native_python_path": "/usr/bin/python3",
            "native_python_sha256": execution.NATIVE_PYTHON_SHA256,
            "native_python_version": "3.9.6",
            "normal_python_path": "/usr/local/bin/python3",
            "normal_python_version": "3.11.15",
            "normal_interpreter_policy": "probe-observed-ordered-chain-under-probe-honesty",
            "selected_platform": {
                "os": "linux",
                "architecture": "arm64",
                "variant": "v8",
            },
            "rootfs_diff_ids": list(evidence.ROOTFS_DIFF_IDS),
            "selected_descriptor_size": 1,
            "platform_manifest_size": 1,
            "image_config_digest": evidence.IMAGE_CONFIG_DIGEST,
            "index_reference": evidence.INDEX_REFERENCE,
            "protected_path": execution.PROTECTED_ADMISSION_PATH,
            "protected_sha256": execution.PROTECTED_ADMISSION_SHA256,
            "docker_path": execution.DOCKER_EXE,
            "docker_sha256": execution.DOCKER_SHA256,
            "buildx_path": execution.BUILDX_EXE,
            "buildx_sha256": execution.BUILDX_SHA256,
            "codesign_path": execution.CODE_SIGN_EXE,
            "codesign_sha256": execution.CODE_SIGN_SHA256,
            "docker_desktop_info_plist_path": execution.DOCKER_DESKTOP_INFO_PLIST,
            "docker_desktop_vm_path": execution.DOCKER_DESKTOP_VM_PATH,
            "docker_desktop_vm_sha256": execution.DOCKER_DESKTOP_VM_SHA256,
            "docker_desktop_kernel_path": execution.DOCKER_DESKTOP_KERNEL_PATH,
            "docker_desktop_kernel_sha256": execution.DOCKER_DESKTOP_KERNEL_SHA256,
            "docker_context_path": execution.DOCKER_CONTEXT_PATH,
            "docker_context_sha256": execution.DOCKER_CONTEXT_SHA256,
            "index_manifest_sha256": evidence.INDEX_REFERENCE.rsplit(":", 1)[1],
            "selected_descriptor_digest": "sha256:" + HEX_B,
            "selected_descriptor_media_type": "application/vnd.oci.image.manifest.v1+json",
            "platform_reference": "docker.io/library/python@sha256:" + HEX_B,
            "platform_manifest_sha256": HEX_B,
            "platform_manifest_media_type": "application/vnd.oci.image.manifest.v1+json",
            "snapshot_source_manifest_sha256": HEX_A,
            "snapshot_copy_manifest_sha256": HEX_B,
        }
    )
    for name in evidence.EXPECTED_BINDING_FIELDS:
        if name.endswith("_sha256") and value[name] == "x":
            value[name] = HEX_A
    value["claim_boundary_sha256"] = execution.claim_boundary_digest(
        value["claim_boundary"]  # type: ignore[arg-type]
    )
    value["native_python_sha256"] = execution.NATIVE_PYTHON_SHA256
    value["a3l6_gate_plan_sha256"] = execution.domain_sha256(
        "hsai:p01b-a3l6-gate-plan:v1", run.gate_plan
    )
    value["a3l6_gate_source_manifest_sha256"] = execution.domain_sha256(
        "hsai:p01b-a3l6-gate-source-manifest:v1", run.gate_source_manifest
    )
    value["expected_focused_test_ids_sha256"] = execution.sha256_bytes(
        execution.canonical_json_bytes(list(run.focused_test_ids))
    )
    rows = {
        row["path"]: row for row in run.gate_source_manifest["ordered_sources"]
    }
    value["validator_sha256"] = rows[execution.SOURCE_PATHS[-4]]["sha256"]
    value["collector_sha256"] = rows[execution.SOURCE_PATHS[-3]]["sha256"]
    value["sandbox_exec_path"] = execution.SANDBOX_EXEC_PATH
    value["sandbox_exec_sha256"] = execution.SANDBOX_EXEC_SHA256
    value["gate_sandbox_profile_sha256"] = run.gate_plan[
        "sandbox_profile_sha256"
    ]
    value["git_path"] = run.gate_source_manifest["git_path"]
    value["git_sha256"] = run.gate_source_manifest["git_sha256"]
    value["a3l6_gate_bundle_sha256"] = execution.domain_sha256(
        "hsai:p01b-a3l6-gate-bundle:v1", gate_bundle_candidate(run, reviews)
    )
    return value


def codesign_display_fixture() -> bytes:
    full = "1" * 64
    short = full[:40]
    rows = (
        "Executable=/Applications/Docker.app/Contents/MacOS/Docker Desktop",
        "Identifier=com.docker.docker",
        "Format=Mach-O universal",
        "CodeDirectory v=20500 size=1 flags=0x10000(runtime) hashes=1+1 location=embedded",
        "Hash type=sha256 size=32",
        "CandidateCDHash sha256=" + short,
        "CandidateCDHashFull sha256=" + full,
        "Hash choices=sha256",
        "CMSDigest=" + full,
        "CMSDigestType=2",
        "Executable Segment base=0",
        "Executable Segment limit=1",
        "Executable Segment flags=0x1",
        "Page size=4096",
        "CDHash=" + short,
        "Signature size=1",
        "Authority=Developer ID Application: Docker Inc (9BNSXJN65R)",
        "Authority=Developer ID Certification Authority",
        "Authority=Apple Root CA",
        "Timestamp=Jul 15, 2026 at 1:02:03 PM",
        "Notarization Ticket=stapled",
        "Info.plist entries=1",
        "TeamIdentifier=9BNSXJN65R",
        "Runtime Version=1.0.0",
        "Sealed Resources version=2 rules=1 files=1",
        "Internal requirements count=1 size=1",
    )
    return ("\n".join(rows) + "\n").encode("ascii")


def execute_fake_a3l7(
    gate_bundle: dict[str, object],
    parent: Path,
    *,
    stream_drift_role=None,
    preflight_failure=None,
    plan_overrides=None,
    runner_calls=None,
    output_root=None,
    runner_hook=None,
) -> execution.ReadinessMaterial:
    host = parent / "fake-host"
    host.mkdir(mode=0o700)
    paths = {
        "docker": host / "docker",
        "buildx": host / "docker-buildx",
        "codesign": host / "codesign",
        "info": host / "Info.plist",
        "vm": host / "desktop.img",
        "kernel": host / "kernel",
        "context": host / ".docker/contexts/meta" / ("f" * 64) / "meta.json",
    }
    raw_files = {
        "docker": b"fake docker client\n",
        "buildx": b"fake buildx client\n",
        "codesign": b"fake codesign client\n",
        "info": plistlib.dumps(
            {
                "CFBundleIdentifier": "com.docker.docker",
                "CFBundleShortVersionString": "4.50.0",
                "CFBundleVersion": "209931",
            }
        ),
        "vm": b"fake desktop image\n",
        "kernel": b"fake desktop kernel\n",
        "context": execution.canonical_json_bytes(
            {
                "Name": "desktop-linux",
                "Metadata": {
                    "Description": "Docker Desktop",
                    "GODEBUG": "x509negativeserial=1",
                    "otel": {
                        "OTEL_EXPORTER_OTLP_ENDPOINT":
                            "unix:///fake/otel.sock" + "x" * 60,
                    },
                },
                "Endpoints": {"docker": {
                    "Host": "unix:///fake/docker.sock",
                    "SkipTLSVerify": False,
                }},
            }
        ),
    }
    for name, path in paths.items():
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        path.write_bytes(raw_files[name])
        path.chmod(0o700 if name in {"docker", "buildx", "codesign"} else 0o600)
    file_hashes = {
        name: hashlib.sha256(raw).hexdigest() for name, raw in raw_files.items()
    }
    image_config = "sha256:" + "2" * 64
    rootfs = tuple("sha256:" + str(index + 3) * 64 for index in range(4))
    platform_value = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {
            "digest": image_config,
            "mediaType": "application/vnd.oci.image.config.v1+json",
            "size": 1,
        },
        "layers": [
            {
                "digest": "sha256:" + "789a"[index] * 64,
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "size": 1,
            }
            for index in range(4)
        ],
    }
    platform_raw = execution.canonical_json_bytes(platform_value)
    platform_digest = hashlib.sha256(platform_raw).hexdigest()
    index_value = {
        "schemaVersion": 2,
        "manifests": [
            {
                "digest": "sha256:" + platform_digest,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "platform": {
                    "architecture": "arm64",
                    "os": "linux",
                    "variant": "v8",
                },
                "size": len(platform_raw),
            }
        ],
    }
    index_raw = execution.canonical_json_bytes(index_value)
    index_reference = "docker.io/library/python@sha256:" + hashlib.sha256(
        index_raw
    ).hexdigest()
    local_raw = execution.canonical_json_bytes(
        {
            "Architecture": "arm64",
            "Id": image_config,
            "Os": "linux",
            "RootFS": {"Layers": list(rootfs), "Type": "layers"},
            "Variant": "v8",
        }
    ) + b"\n"
    streams = {
        "registry-index": (index_raw, b""),
        "registry-platform": (platform_raw, b""),
        "local-platform": (local_raw, b""),
        "buildx-version": (
            b"github.com/docker/buildx v0.34.1-desktop.1 c79576280a671664e17eb68da98ec3136b614aed\n",
            b"",
        ),
        "codesign-verify": (
            b"",
            b"/Applications/Docker.app: valid on disk\n"
            b"/Applications/Docker.app: satisfies its Designated Requirement\n",
        ),
        "codesign-display": (b"", codesign_display_fixture()),
    }
    patches = {
        "DOCKER_EXE": str(paths["docker"]),
        "DOCKER_SHA256": file_hashes["docker"],
        "BUILDX_EXE": str(paths["buildx"]),
        "BUILDX_SHA256": file_hashes["buildx"],
        "CODE_SIGN_EXE": str(paths["codesign"]),
        "CODE_SIGN_SHA256": file_hashes["codesign"],
        "DOCKER_DESKTOP_INFO_PLIST": str(paths["info"]),
        "DOCKER_DESKTOP_VM_PATH": str(paths["vm"]),
        "DOCKER_DESKTOP_VM_SHA256": file_hashes["vm"],
        "DOCKER_DESKTOP_KERNEL_PATH": str(paths["kernel"]),
        "DOCKER_DESKTOP_KERNEL_SHA256": file_hashes["kernel"],
        "DOCKER_CONTEXT_PATH": str(paths["context"]),
        "DOCKER_CONTEXT_SHA256": file_hashes["context"],
        "INDEX_REFERENCE": index_reference,
        "IMAGE_CONFIG_DIGEST": image_config,
        "ROOTFS_DIFF_IDS": rootfs,
    }
    if preflight_failure == "identity_drift":
        patches["DOCKER_SHA256"] = HEX_A
    elif preflight_failure == "context_drift":
        patches["DOCKER_CONTEXT_SHA256"] = HEX_A
    elif preflight_failure is not None:
        raise AssertionError("unknown fake A3L7 preflight failure")
    evidence_names = {
        "DOCKER_PATH": patches["DOCKER_EXE"],
        "DOCKER_SHA256": patches["DOCKER_SHA256"],
        "BUILDX_PATH": patches["BUILDX_EXE"],
        "BUILDX_SHA256": patches["BUILDX_SHA256"],
        "CODESIGN_PATH": patches["CODE_SIGN_EXE"],
        "CODESIGN_SHA256": patches["CODE_SIGN_SHA256"],
        "DOCKER_DESKTOP_INFO_PLIST_PATH": patches["DOCKER_DESKTOP_INFO_PLIST"],
        "DOCKER_DESKTOP_VM_PATH": patches["DOCKER_DESKTOP_VM_PATH"],
        "DOCKER_DESKTOP_VM_SHA256": patches["DOCKER_DESKTOP_VM_SHA256"],
        "DOCKER_DESKTOP_KERNEL_PATH": patches["DOCKER_DESKTOP_KERNEL_PATH"],
        "DOCKER_DESKTOP_KERNEL_SHA256": patches["DOCKER_DESKTOP_KERNEL_SHA256"],
        "DOCKER_CONTEXT_SHA256": file_hashes["context"],
        "INDEX_REFERENCE": index_reference,
        "IMAGE_CONFIG_DIGEST": image_config,
        "ROOTFS_DIFF_IDS": rootfs,
    }

    def runner(
        command_value: execution.CommandSpec,
        *,
        plan_sha256: str,
        completion_ordinal: int,
        previous_observation_sha256,
        raw_root,
    ) -> execution.RawObservation:
        if runner_calls is not None:
            runner_calls.append(command_value.role)
        if runner_hook is not None:
            runner_hook(command_value.role)
        self_path = command_value.argv[0]
        if self_path not in {
            str(paths["docker"]), str(paths["buildx"]), str(paths["codesign"])
        }:
            raise AssertionError("fake runner received non-fixture executable")
        if raw_root is not None:
            raise AssertionError("fake runner must not retain outside executor")
        stdout, stderr = streams[command_value.role]
        if command_value.role == stream_drift_role:
            stdout = b"semantic-drift\n"
        started = 100 + completion_ordinal * 10
        value = execution._observation_value(
            command=command_value,
            plan_sha256=plan_sha256,
            completion_ordinal=completion_ordinal,
            executable_sha256=file_hashes[
                "docker" if self_path == str(paths["docker"]) else
                "buildx" if self_path == str(paths["buildx"]) else "codesign"
            ],
            started_ns=started,
            ended_ns=started + 1,
            outcome="exit",
            exit_code=0,
            terminating_signal=None,
            stdout=stdout,
            stderr=stderr,
            previous_observation_sha256=previous_observation_sha256,
            container_id=None,
            raw_directory=None,
        )
        return execution.RawObservation(value, stdout, stderr)

    with contextlib.ExitStack() as stack:
        for name, value in patches.items():
            stack.enter_context(mock.patch.object(execution, name, value))
        for name, value in evidence_names.items():
            stack.enter_context(mock.patch.object(evidence, name, value))
        user_raw = b"retain one bounded normal/OOM local campaign; no stronger claims"
        selected_output_root = (
            parent / "a3l7-output" if output_root is None else output_root
        )
        plan_inputs = {
            "predecessor_commit": execution.READINESS_PREDECESSOR_COMMIT,
            "user_authorization_sha256": hashlib.sha256(user_raw).hexdigest(),
            "config_root": str(host / ".docker"),
            "host_uri": "unix:///fake/docker.sock",
            "temporary_root": str(selected_output_root / "runtime-tmp"),
        }
        if plan_overrides is not None:
            plan_inputs.update(plan_overrides)
        plan = execution.build_readiness_plan(**plan_inputs)
        return execution.execute_a3l7_readiness(
            readiness_plan=plan,
            a3l6_gate_bundle=gate_bundle,
            user_authorization_raw=user_raw,
            campaign_id="campaign",
            output_root=selected_output_root,
            runner=runner,
        )


class StepClock:
    def __init__(self) -> None:
        self.value = 1_000_000

    def __call__(self) -> int:
        self.value += 10
        return self.value


def bound_a3l7_constants(bindings: dict[str, object]) -> contextlib.ExitStack:
    stack = contextlib.ExitStack()
    execution_values = {
        "DOCKER_EXE": bindings["docker_path"],
        "DOCKER_SHA256": bindings["docker_sha256"],
        "BUILDX_EXE": bindings["buildx_path"],
        "BUILDX_SHA256": bindings["buildx_sha256"],
        "CODE_SIGN_EXE": bindings["codesign_path"],
        "CODE_SIGN_SHA256": bindings["codesign_sha256"],
        "DOCKER_DESKTOP_INFO_PLIST": bindings["docker_desktop_info_plist_path"],
        "DOCKER_DESKTOP_VM_PATH": bindings["docker_desktop_vm_path"],
        "DOCKER_DESKTOP_VM_SHA256": bindings["docker_desktop_vm_sha256"],
        "DOCKER_DESKTOP_KERNEL_PATH": bindings["docker_desktop_kernel_path"],
        "DOCKER_DESKTOP_KERNEL_SHA256": bindings["docker_desktop_kernel_sha256"],
        "DOCKER_CONTEXT_PATH": bindings["docker_context_path"],
        "DOCKER_CONTEXT_SHA256": bindings["docker_context_sha256"],
        "INDEX_REFERENCE": bindings["index_reference"],
        "IMAGE_CONFIG_DIGEST": bindings["image_config_digest"],
        "ROOTFS_DIFF_IDS": tuple(bindings["rootfs_diff_ids"]),
        "PROTECTED_ADMISSION_PATH": bindings["protected_path"],
        "PROTECTED_ADMISSION_SHA256": bindings["protected_sha256"],
    }
    evidence_values = {
        "DOCKER_PATH": bindings["docker_path"],
        "DOCKER_SHA256": bindings["docker_sha256"],
        "BUILDX_PATH": bindings["buildx_path"],
        "BUILDX_SHA256": bindings["buildx_sha256"],
        "CODESIGN_PATH": bindings["codesign_path"],
        "CODESIGN_SHA256": bindings["codesign_sha256"],
        "DOCKER_DESKTOP_INFO_PLIST_PATH": bindings["docker_desktop_info_plist_path"],
        "DOCKER_DESKTOP_VM_PATH": bindings["docker_desktop_vm_path"],
        "DOCKER_DESKTOP_VM_SHA256": bindings["docker_desktop_vm_sha256"],
        "DOCKER_DESKTOP_KERNEL_PATH": bindings["docker_desktop_kernel_path"],
        "DOCKER_DESKTOP_KERNEL_SHA256": bindings["docker_desktop_kernel_sha256"],
        "DOCKER_CONTEXT_SHA256": bindings["docker_context_sha256"],
        "INDEX_REFERENCE": bindings["index_reference"],
        "IMAGE_CONFIG_DIGEST": bindings["image_config_digest"],
        "ROOTFS_DIFF_IDS": tuple(bindings["rootfs_diff_ids"]),
    }
    for name, value in execution_values.items():
        stack.enter_context(mock.patch.object(execution, name, value))
    for name, value in evidence_values.items():
        stack.enter_context(mock.patch.object(evidence, name, value))
    return stack


def execute_fake_a3l8(
    *,
    a3l7_root: Path,
    repo_root: Path,
    output_parent: Path,
    post_binding_durability_hook=None,
) -> execution.CampaignExecution:
    bindings = json.loads((a3l7_root / "authority/expected-bindings.json").read_bytes())
    fixture_path = Path(__file__).with_name("p01b_container_evidence_tests.py")
    spec = importlib.util.spec_from_file_location("p01b_a3l8_fixtures", fixture_path)
    if spec is None or spec.loader is None:
        raise AssertionError("evidence fixture module is unavailable")
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    seed = {
        "snapshot/files/tools/hsai-formal-preflight/p01b_container_probe.py":
            (a3l7_root / "snapshot/files/tools/hsai-formal-preflight/p01b_container_probe.py").read_bytes()
    }
    fixtures.synthetic_probe_results(seed, bindings)
    result_raw = {
        "native-reference": seed["reference/native-result.json"],
        "normal": seed["attempts/normal/result.json"],
        "oom": seed["attempts/oom/result.json"],
    }
    seccomp_raw = (
        a3l7_root
        / "snapshot/files/tools/hsai-formal-preflight/p01b_container_seccomp.json"
    ).read_bytes()
    clock = StepClock()
    cids = {"normal": "55" * 32, "oom": "66" * 32}

    version_raw = execution.canonical_json_bytes(
        {
            "Client": {
                "ApiVersion": "1.52", "Arch": "arm64", "GoVersion": "go1.24",
                "Os": "darwin", "Version": "29.5.3",
            },
            "Server": {
                "ApiVersion": "1.52", "Arch": "arm64", "Os": "linux",
                "Version": "29.5.3",
            },
        }
    ) + b"\n"
    info_raw = execution.canonical_json_bytes(
        {
            "Architecture": "aarch64",
            "ContainerdCommit": {"Commit": "containerd-commit", "Version": "2.1.0"},
            "DockerRootDir": "/var/lib/docker",
            "KernelVersion": "6.10",
            "OperatingSystem": "Docker Desktop",
            "OSType": "linux",
            "RuncCommit": {"Commit": "runc-commit", "Version": "1.3.0"},
        }
    ) + b"\n"
    image_raw = execution.canonical_json_bytes(
        {
            "Architecture": "arm64",
            "Id": bindings["image_config_digest"],
            "Os": "linux",
            "RepoDigests": [bindings["platform_reference"]],
            "RootFS": {"Layers": bindings["rootfs_diff_ids"], "Type": "layers"},
            "Variant": "v8",
        }
    ) + b"\n"

    def inspect_raw(attempt: str, state: str) -> bytes:
        cid = cids[attempt]
        name = "hsai-p01b-campaign-" + attempt
        labels = execution.expected_container_labels(
            "campaign", attempt,
            str(json.loads((a3l7_root / "readiness/campaign-plan.json").read_bytes())["authorization_sha256"]),
            str(bindings["implementation_commit"]),
        )
        value = fixtures.semantic_inspect(state, seccomp_raw, cid, name, labels)
        value["Mounts"][0]["Source"] = str(a3l7_root / "snapshot/files")
        value["Config"]["Image"] = bindings["platform_reference"]
        projection = []
        for dotted in execution.INSPECT_FIELDS:
            selected = value
            for part in dotted.split("."):
                selected = selected[part]
            projection.append(selected)
        return execution.canonical_json_bytes(projection) + b"\n"

    def streams(command_value: execution.CommandSpec, namespace: str) -> tuple[bytes, bytes, int]:
        role = command_value.role
        if namespace == "campaign":
            values = {
                "native-reference": result_raw["native-reference"],
                "docker-version": version_raw,
                "docker-info": info_raw,
                "image-config": image_raw,
            }
            return values[role], b"", 0
        cid = cids[namespace]
        name = "hsai-p01b-campaign-" + namespace
        if role == "absence-name-pre" or role == "absence-name":
            return b"", ("Error response from daemon: No such container: " + name + "\n").encode("ascii"), 1
        if role == "absence-cid":
            return b"", ("Error response from daemon: No such container: " + cid + "\n").encode("ascii"), 1
        if role == "recovery-inspect":
            running = json.loads(inspect_raw(namespace, "prestart"))
            running[execution.INSPECT_FIELDS.index("State.Running")] = True
            return execution.canonical_json_bytes(running) + b"\n", b"", 0
        if role in {"recovery-kill", "recovery-remove"}:
            return (cid + "\n").encode("ascii"), b"", 0
        if role == "recovery-wait":
            return b"0\n", b"", 0
        if role == "recovery-terminal-inspect":
            return inspect_raw(namespace, "terminal"), b"", 0
        if role in {"recovery-absence-cid", "recovery-absence-name"}:
            target = command_value.argv[-1]
            return b"", (
                "Error response from daemon: No such container: "
                + target + "\n"
            ).encode("ascii"), 1
        if role == "recovery-absence-label":
            return b"", b"", 0
        if role == "recovery-daemon-recheck":
            return b"{}\n", b"", 0
        values = {
            "absence-label-pre": b"",
            "create": (cid + "\n").encode("ascii"),
            "inspect-prestart": inspect_raw(namespace, "prestart"),
            "export-running": fixtures.strict_ustar(result_raw[namespace]),
            "release": b"",
            "start-attach": (
                "P01B_RESULT_READY {} {}\n".format(
                    len(result_raw[namespace]), hashlib.sha256(result_raw[namespace]).hexdigest()
                )
            ).encode("ascii"),
            "wait": b"0\n",
            "inspect-terminal": inspect_raw(namespace, "terminal"),
            "remove": (cid + "\n").encode("ascii"),
            "absence-label": b"",
            "daemon-recheck": b'{"daemon":"unchanged"}\n',
            "emergency-kill": b"",
        }
        return values[role], b"", 0

    def runner(
        command_value: execution.CommandSpec,
        *,
        plan_sha256: str,
        completion_ordinal: int,
        previous_observation_sha256=None,
        raw_root=None,
        raw_root_fd=None,
        container_id=None,
    ) -> execution.RawObservation:
        del raw_root_fd
        namespace = "campaign" if command_value.role in execution.CAMPAIGN_OPERATION_ROLES else Path(raw_root).name
        if namespace == "recovery":
            namespace = Path(raw_root).parent.name
        stdout, stderr, exit_code = streams(command_value, namespace)
        started = clock(); ended = clock()
        executable_sha256 = (
            str(bindings["native_python_sha256"])
            if command_value.argv[0] == bindings["native_python_path"]
            else str(bindings["docker_sha256"])
        )
        value = execution._observation_value(
            command=command_value,
            plan_sha256=plan_sha256,
            completion_ordinal=completion_ordinal,
            executable_sha256=executable_sha256,
            started_ns=started,
            ended_ns=ended,
            outcome="exit",
            exit_code=exit_code,
            terminating_signal=None,
            stdout=stdout,
            stderr=stderr,
            previous_observation_sha256=previous_observation_sha256,
            container_id=container_id,
            raw_directory=None,
        )
        return execution.RawObservation(value, stdout, stderr)

    def spanning_executor(**values) -> execution.RunningExportResult:
        start_command = values["start_command"]
        start_begin = clock()
        observed = clock()
        export = runner(
            values["export_command"],
            plan_sha256=values["plan_sha256"],
            completion_ordinal=values["first_completion_ordinal"],
            previous_observation_sha256=values["previous_observation_sha256"],
            raw_root=values["raw_root"],
            container_id=values["container_id"],
        )
        release = runner(
            values["release_command"],
            plan_sha256=values["plan_sha256"],
            completion_ordinal=values["first_completion_ordinal"] + 1,
            previous_observation_sha256=export.digest,
            raw_root=values["raw_root"],
            container_id=values["container_id"],
        )
        stdout, _, _ = streams(start_command, values["attempt_id"])
        start_end = clock()
        start_value = execution._observation_value(
            command=start_command,
            plan_sha256=values["plan_sha256"],
            completion_ordinal=values["first_completion_ordinal"] + 2,
            executable_sha256=str(bindings["docker_sha256"]),
            started_ns=start_begin,
            ended_ns=start_end,
            outcome="exit",
            exit_code=0,
            terminating_signal=None,
            stdout=stdout,
            stderr=b"",
            previous_observation_sha256=release.digest,
            container_id=values["container_id"],
            raw_directory=None,
        )
        start = execution.RawObservation(start_value, stdout, b"")
        event = execution.build_readiness_event(
            plan_sha256=values["plan_sha256"],
            attempt_id=values["attempt_id"],
            start_command=start_command,
            stdout_path=str(values["raw_root"] / "006-start-attach/stdout.bin"),
            stdout_prefix=stdout,
            line_offset=0,
            line=stdout,
            observed_monotonic_ns=observed,
        )
        return execution.RunningExportResult(
            event, export, release, start, values["tar_parser"](export.stdout)
        )

    def repository_runner(argv, _cwd) -> bytes:
        if argv[-2:] == ("rev-parse", "HEAD") or list(argv[-2:]) == ["rev-parse", "HEAD"]:
            return (str(bindings["implementation_commit"]) + "\n").encode("ascii")
        if argv[-2:] == ("rev-parse", "HEAD^{tree}") or list(argv[-2:]) == ["rev-parse", "HEAD^{tree}"]:
            return (str(bindings["implementation_tree"]) + "\n").encode("ascii")
        return b""

    def rename(source_fd, source, destination_fd, destination, flags):
        if flags != 0x00000004:
            raise AssertionError("exclusive rename flag changed")
        os.rename(
            os.fsdecode(source), os.fsdecode(destination),
            src_dir_fd=source_fd, dst_dir_fd=destination_fd,
        )
        return 0, 0

    with bound_a3l7_constants(bindings):
        return execution._execute_a3l8_campaign_with_seams(
            a3l7_root=a3l7_root,
            repo_root=repo_root,
            protected_file=Path(str(bindings["protected_path"])),
            output_parent=output_parent,
            runner=runner,
            spanning_executor=spanning_executor,
            repository_runner=repository_runner,
            rename_callable=rename,
            clock=clock,
            identity_verifier=lambda _path, _digest: None,
            source_binding_verifier=lambda _root: evidence,
            post_binding_durability_hook=post_binding_durability_hook,
        )


class PlanBuilderTests(unittest.TestCase):
    def test_readiness_commands_execute_only_test_owned_fake_clients(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = "#!/usr/bin/python3\nimport json,sys\nsys.stdout.write(json.dumps(sys.argv[1:],separators=(',',':')))\n"
            docker = root / "docker"
            buildx = root / "docker-buildx"
            codesign = root / "codesign"
            docker.write_text(script, encoding="ascii")
            buildx.write_text(script, encoding="ascii")
            codesign.write_text(script, encoding="ascii")
            docker.chmod(0o700)
            buildx.chmod(0o700)
            codesign.chmod(0o700)
            original = (
                execution.DOCKER_EXE,
                execution.BUILDX_EXE,
                execution.CODE_SIGN_EXE,
                execution.DOCKER_SHA256,
                execution.BUILDX_SHA256,
                execution.CODE_SIGN_SHA256,
            )
            evidence_original = (
                evidence.DOCKER_PATH,
                evidence.BUILDX_PATH,
                evidence.CODESIGN_PATH,
                evidence.DOCKER_SHA256,
                evidence.BUILDX_SHA256,
                evidence.CODESIGN_SHA256,
            )
            execution.DOCKER_EXE = str(docker)
            execution.BUILDX_EXE = str(buildx)
            execution.CODE_SIGN_EXE = str(codesign)
            execution.DOCKER_SHA256 = hashlib.sha256(docker.read_bytes()).hexdigest()
            execution.BUILDX_SHA256 = hashlib.sha256(buildx.read_bytes()).hexdigest()
            execution.CODE_SIGN_SHA256 = hashlib.sha256(codesign.read_bytes()).hexdigest()
            evidence.DOCKER_PATH = execution.DOCKER_EXE
            evidence.BUILDX_PATH = execution.BUILDX_EXE
            evidence.CODESIGN_PATH = execution.CODE_SIGN_EXE
            evidence.DOCKER_SHA256 = execution.DOCKER_SHA256
            evidence.BUILDX_SHA256 = execution.BUILDX_SHA256
            evidence.CODESIGN_SHA256 = execution.CODE_SIGN_SHA256
            try:
                context_path = str(
                    root
                    / ".docker/contexts/meta"
                    / ("f" * 64)
                    / "meta.json"
                )
                output_root = root / "a3l7-output"
                plan = execution.resolve_readiness_plan(
                    execution.build_readiness_plan(
                        predecessor_commit=execution.READINESS_PREDECESSOR_COMMIT,
                        user_authorization_sha256=HEX_A,
                        config_root=str(root / ".docker"),
                        host_uri="unix:///test-owned/docker.sock",
                        temporary_root=str(output_root / "runtime-tmp"),
                    ),
                    PLATFORM,
                )
                unresolved = execution.build_readiness_plan(
                    predecessor_commit=execution.READINESS_PREDECESSOR_COMMIT,
                    user_authorization_sha256=HEX_A,
                    config_root=str(root / ".docker"),
                    host_uri="unix:///test-owned/docker.sock",
                    temporary_root=str(output_root / "runtime-tmp"),
                )
                canonical, _, _, _ = execution._canonical_readiness_plan(
                    unresolved,
                    HEX_A,
                    context_path=context_path,
                    host_uri="unix:///test-owned/docker.sock",
                    output_root=output_root,
                )
                self.assertEqual(canonical, unresolved)
                tampered = json.loads(execution.canonical_json_bytes(unresolved))
                tampered["commands"][0]["argv"].extend(["pull", "python:latest"])
                with self.assertRaises(execution.ExecutionError):
                    execution._canonical_readiness_plan(
                        tampered,
                        HEX_A,
                        context_path=context_path,
                        host_uri="unix:///test-owned/docker.sock",
                        output_root=output_root,
                    )
                self.assertFalse((root / "raw").exists())
                for index, value in enumerate(plan["commands"]):
                    result = execution.execute_direct(
                        command_from_value(value),
                        plan_sha256=HEX_A,
                        completion_ordinal=index,
                        raw_root=root / "raw",
                    )
                    self.assertEqual(result.value["exit_code"], 0)
                    self.assertTrue(result.stdout)
            finally:
                (
                    execution.DOCKER_EXE,
                    execution.BUILDX_EXE,
                    execution.CODE_SIGN_EXE,
                    execution.DOCKER_SHA256,
                    execution.BUILDX_SHA256,
                    execution.CODE_SIGN_SHA256,
                ) = original
                (
                    evidence.DOCKER_PATH,
                    evidence.BUILDX_PATH,
                    evidence.CODESIGN_PATH,
                    evidence.DOCKER_SHA256,
                    evidence.BUILDX_SHA256,
                    evidence.CODESIGN_SHA256,
                ) = evidence_original

    def test_readiness_plan_has_exact_direct_network_surface(self) -> None:
        plan = execution.build_readiness_plan(
            predecessor_commit=GIT_A,
            user_authorization_sha256=HEX_B,
            config_root="/cfg",
            host_uri="unix:///socket",
            temporary_root="/private/tmp/p01b",
        )
        commands = plan["commands"]
        self.assertEqual(len(commands), 6)
        self.assertEqual(
            commands[0]["argv"],
            [
                execution.BUILDX_EXE,
                "imagetools",
                "inspect",
                "--raw",
                execution.INDEX_REFERENCE,
            ],
        )
        self.assertEqual(commands[1]["argv"][-1], execution.PLATFORM_PLACEHOLDER)
        self.assertEqual(commands[2]["argv"][-1], execution.PLATFORM_PLACEHOLDER)
        self.assertEqual(commands[3]["argv"], [execution.BUILDX_EXE, "version"])
        self.assertEqual(
            commands[4]["argv"],
            [execution.CODE_SIGN_EXE, "--verify", "--strict", "--verbose=4", execution.DOCKER_APP_PATH],
        )
        self.assertEqual(commands[5]["argv"][1], "--display")
        self.assertNotIn("pull", execution.canonical_json_bytes(plan).decode("ascii"))

    def test_readiness_resolution_replaces_exactly_two_slots(self) -> None:
        plan = execution.build_readiness_plan(
            predecessor_commit=GIT_A,
            user_authorization_sha256=HEX_B,
            config_root="/cfg",
            host_uri="unix:///socket",
            temporary_root="/private/tmp/p01b",
        )
        resolved = execution.resolve_readiness_plan(plan, PLATFORM)
        self.assertNotIn(
            execution.PLATFORM_PLACEHOLDER,
            execution.canonical_json_bytes(resolved).decode("ascii"),
        )
        tampered = json.loads(execution.canonical_json_bytes(plan))
        tampered["commands"][0]["argv"].append(execution.PLATFORM_PLACEHOLDER)
        with self.assertRaises(execution.ExecutionError):
            execution.resolve_readiness_plan(tampered, PLATFORM)

    def test_native_and_metadata_argv_are_exact(self) -> None:
        environment = execution.closed_host_environment("/cfg", "/tmp/p01b")
        native = execution.build_native_command("/snapshot", environment)
        self.assertEqual(
            native.argv,
            (
                "/usr/bin/python3",
                "-B",
                "/snapshot/tools/hsai-formal-preflight/p01b_container_probe.py",
                "--mode",
                "native-reference",
            ),
        )
        prefix = execution.docker_prefix("/cfg", "unix:///socket")
        metadata = execution.build_metadata_commands(prefix, environment)
        self.assertEqual(
            [item.role for item in metadata],
            ["docker-version", "docker-info", "image-config"],
        )
        self.assertEqual(metadata[2].argv[-1], execution.IMAGE_CONFIG_DIGEST)
        for attempt_id, mode in (("normal", "normal"), ("oom", "oom-child")):
            plan = execution.build_attempt_plan(
                campaign_id="campaign",
                attempt_id=attempt_id,
                authorization_sha256=HEX_A,
                implementation_commit=GIT_B,
                platform_reference=PLATFORM,
                source_manifest_sha256=HEX_B,
                config_root="/cfg",
                host_uri="unix:///socket",
                temporary_root="/tmp/p01b",
                snapshot_root="/snapshot",
                seccomp_path="/snapshot/seccomp.json",
            )
            create = plan["commands"][2]["argv"]
            self.assertEqual(
                create[-6:],
                [
                    "--mode",
                    mode,
                    "--input-manifest-sha256",
                    HEX_B,
                    "--output",
                    "/work/result.json",
                ],
            )
        probe_path = Path(execution.__file__).with_name("p01b_container_probe.py")
        spec = importlib.util.spec_from_file_location("a3l5f_probe_fixture", probe_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec is not None else None)
        probe = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(probe)  # type: ignore[union-attr]
        with self.assertRaises(probe.ProbeError):
            probe._parse_cli(
                [
                    "probe",
                    "--mode",
                    "native-reference",
                    "--input-manifest-sha256",
                    HEX_B,
                ]
            )
        for mode in ("normal", "oom-child"):
            with self.assertRaises(probe.ProbeError):
                probe._parse_cli(
                    ["probe", "--mode", mode, "--output", "/work/result.json"]
                )
            with self.assertRaises(probe.ProbeError):
                probe._parse_cli(
                    [
                        "probe",
                        "--mode",
                        mode,
                        "--input-manifest-sha256",
                        "B" * 64,
                        "--output",
                        "/work/result.json",
                    ]
                )
            self.assertEqual(
                probe._parse_cli(
                    [
                        "probe",
                        "--mode",
                        mode,
                        "--input-manifest-sha256",
                        HEX_B,
                        "--output",
                        "/work/result.json",
                    ]
                ),
                (mode, HEX_B, "/work/result.json"),
            )

    def test_attempt_plan_removes_invalid_pid_uts_modes_and_binds_cid_slots(self) -> None:
        plan = execution.build_attempt_plan(
            campaign_id="campaign",
            attempt_id="normal",
            authorization_sha256=HEX_A,
            implementation_commit=GIT_B,
            platform_reference=PLATFORM,
            source_manifest_sha256=HEX_B,
            config_root="/cfg",
            host_uri="unix:///socket",
            temporary_root="/tmp/p01b",
            snapshot_root="/snapshot",
            seccomp_path="/snapshot/seccomp.json",
        )
        create = plan["commands"][2]["argv"]
        self.assertIn("--ipc=private", create)
        self.assertNotIn("--pid=private", create)
        self.assertNotIn("--uts=private", create)
        self.assertIn("--network=none", create)
        self.assertIn("--pull=never", create)
        resolved = execution.resolve_cid(plan, "d" * 64)
        self.assertNotIn(
            execution.CID_PLACEHOLDER,
            execution.canonical_json_bytes(resolved).decode("ascii"),
        )

    def test_recovery_absence_never_mutates_and_presence_uses_cid(self) -> None:
        environment = execution.closed_host_environment("/cfg", "/tmp/p01b")
        prefix = execution.docker_prefix("/cfg", "unix:///socket")
        absent = execution.build_recovery_plan(
            prefix=prefix,
            environment=environment,
            container_name="hsai-p01b-cc-normal",
            container_id=None,
            campaign_id="cc",
            attempt_id="normal",
            running=None,
        )
        self.assertNotIn("recovery-remove", [item.role for item in absent])
        present = execution.build_recovery_plan(
            prefix=prefix,
            environment=environment,
            container_name="hsai-p01b-cc-normal",
            container_id="d" * 64,
            campaign_id="cc",
            attempt_id="normal",
            running=True,
        )
        self.assertEqual(
            [item.role for item in present][1:5],
            ["recovery-kill", "recovery-wait", "recovery-terminal-inspect", "recovery-remove"],
        )
        self.assertEqual(present[4].argv[-1], "d" * 64)
        with self.assertRaises(execution.ExecutionError):
            execution.build_recovery_plan(
                prefix=prefix,
                environment=environment,
                container_name="hsai-p01b-cc-normal",
                container_id=None,
                campaign_id="cc",
                attempt_id="normal",
                running=False,
            )

    def test_gate_profile_is_byte_exact_and_keeps_network_denied(self) -> None:
        # Under the A3L6 gate Seatbelt, host /private/tmp gate parents and nested
        # denial-check launches are unavailable. Keep byte-exact profile checks
        # under TMPDIR=scratch so the gate transcript stays parseable (... ok).
        if _gate_sandbox_active():
            with tempfile.TemporaryDirectory() as temporary:
                parent = Path(temporary)
                source = parent / "source"
                scratch = parent / "scratch"
                source.mkdir(mode=0o555)
                scratch.mkdir(mode=0o700)
                raw = execution.render_gate_sandbox_profile(
                    str(source), str(scratch)
                )
                expected = (
                    "(version 1)\n"
                    "(deny default)\n"
                    "(allow process*)\n"
                    "(allow signal)\n"
                    "(allow sysctl-read)\n"
                    "(allow file-read-metadata)\n"
                    '(allow file-read-data (literal "/"))\n'
                    '(allow file-read* (subpath "%s") (subpath "%s") '
                    '(subpath "/System/Library") (subpath "/usr/lib") '
                    '(subpath "/usr/bin") (subpath "/bin") '
                    '(subpath "/Library/Developer/CommandLineTools") '
                    '(subpath "/private/etc") (literal "/dev/null") '
                    '(literal "/dev/urandom"))\n'
                    '(allow file-write* (subpath "%s") (literal "/dev/null"))\n'
                    "(deny network*)\n"
                ) % (source, scratch, scratch)
                self.assertEqual(raw, expected.encode("ascii"))
                self.assertTrue(raw.endswith(b"(deny network*)\n"))
                self.assertEqual(raw.count(b"(allow file-write*"), 1)
                self.assertNotIn(b"network-outbound", raw)
                with self.assertRaises(execution.ExecutionError):
                    execution.render_gate_sandbox_profile(
                        '/private/tmp/bad"root', "/private/tmp/scratch"
                    )
            return

        parent = Path("/private/tmp/hsai-p01b-gate-" + os.urandom(16).hex())
        source = parent / "source"
        scratch = parent / "scratch"
        profile = parent / "gate.sb"
        try:
            parent.mkdir(mode=0o700)
            source.mkdir(mode=0o555)
            scratch.mkdir(mode=0o700)
            raw = execution.render_gate_sandbox_profile(str(source), str(scratch))
            expected = (
                "(version 1)\n"
                "(deny default)\n"
                "(allow process*)\n"
                "(allow signal)\n"
                "(allow sysctl-read)\n"
                "(allow file-read-metadata)\n"
                '(allow file-read-data (literal "/"))\n'
                '(allow file-read* (subpath "%s") (subpath "%s") '
                '(subpath "/System/Library") (subpath "/usr/lib") '
                '(subpath "/usr/bin") (subpath "/bin") '
                '(subpath "/Library/Developer/CommandLineTools") '
                '(subpath "/private/etc") (literal "/dev/null") '
                '(literal "/dev/urandom"))\n'
                '(allow file-write* (subpath "%s") (literal "/dev/null"))\n'
                "(deny network*)\n"
            ) % (source, scratch, scratch)
            self.assertEqual(raw, expected.encode("ascii"))
            self.assertNotIn(
                b"hsai-p01b-denied.invalid",
                Path(execution.__file__).read_bytes(),
            )
            profile.write_bytes(raw)
            profile.chmod(0o400)
            self.assertTrue(raw.endswith(b"(deny network*)\n"))
            self.assertEqual(raw.count(b"(allow file-write*"), 1)
            self.assertNotIn(b"<materialized_root>", raw)
            self.assertNotIn(b"network-outbound", raw)
            checks = execution.run_gate_sandbox_denial_checks(
                materialized_root=source,
                gate_temp_root=scratch,
                profile_path=profile,
            )
            self.assertEqual(
                [item.value["role"] for item in checks],
                [
                    "gate-denial-positive",
                    "gate-denial-ipv4",
                    "gate-denial-ipv6",
                    "gate-denial-dns",
                    "gate-denial-mach",
                ],
            )
            with self.assertRaises(execution.ExecutionError):
                execution.render_gate_sandbox_profile(
                    '/private/tmp/bad"root', "/private/tmp/scratch"
                )
        finally:
            thaw(source)
            shutil.rmtree(parent, ignore_errors=True)

    def test_gate_materialization_freezes_exact_sources_and_builds_three_wrapped_gates(
        self,
    ) -> None:
        self.assertNotIn("os.walk", inspect.getsource(execution._capture_gate_tree))
        self.assertFalse(hasattr(execution, "capture_gate_inventory"))
        # Host-only: capture_a3l6_gate_sources requires a real
        # /private/tmp/hsai-p01b-gate-<32hex> parent outside the gate scratch.
        if _gate_sandbox_active():
            self.assertEqual(os.environ.get("P01B_GATE_SANDBOX_ACTIVE"), "1")
            return
        parent = Path("/private/tmp/hsai-p01b-gate-" + os.urandom(16).hex())
        try:
            with tempfile.TemporaryDirectory() as temporary:
                repository = Path(temporary)
                commit, tree = make_gate_repository(repository, parent)
                capture = execution.capture_a3l6_gate_sources(
                    repository_root=repository,
                    parent=parent,
                    implementation_commit=commit,
                    implementation_tree=tree,
                    audit_commit=commit,
                )
                materialized = capture.materialization
                self.assertEqual(
                    len(capture.ordered_blob_observations),
                    len(execution.SOURCE_PATHS),
                )
                self.assertEqual(
                    len(materialized.source_observations),
                    len(execution.SOURCE_PATHS),
                )
                self.assertEqual(len(capture.focused_test_ids), 64)
                self.assertEqual(
                    stat.S_IMODE(Path(materialized.source_root).stat().st_mode),
                    0o555,
                )
                self.assertTrue(
                    all(
                        stat.S_IMODE(
                            (Path(materialized.source_root) / path).stat().st_mode
                        )
                        == 0o444
                        for path in execution.SOURCE_PATHS
                    )
                )
                live_run = execution.execute_a3l6_gates(capture)
                self.assertEqual(live_run.focused_test_count, 64)
                self.assertEqual(live_run.discovery_test_count, 172)
                self.assertEqual(len(live_run.ordered_gate_observations), 3)
                self.assertEqual(
                    [item["role"] for item in live_run.ordered_gate_observations],
                    ["evidence-focused", "execution-focused", "formal-discovery"],
                )
                live_reviews = (
                    execution.build_a3l6_code_review_record(
                        live_run,
                        role="security-capability",
                        reviewer_id="security-reviewer",
                        findings=(),
                    ),
                    execution.build_a3l6_code_review_record(
                        live_run,
                        role="correspondence-reproducibility",
                        reviewer_id="correspondence-reviewer",
                        findings=(),
                    ),
                )
                bindings = gate_expected_bindings(live_run, live_reviews)
                live_bundle = execution.assemble_a3l6_gate_bundle(
                    live_run, live_reviews
                )
                execution.validate_a3l6_gate_bundle(live_bundle, bindings)
                self.assertEqual(live_bundle["result"], "accept")
                snapshot = execution.create_a3l7_snapshot(
                    live_bundle, parent / "a3l7-snapshot"
                )
                self.assertEqual(
                    len(snapshot.source_manifest["ordered_entries"]),
                    len(execution.SOURCE_PATHS),
                )
                self.assertEqual(
                    len(snapshot.copy_manifest["ordered_entries"]),
                    len(execution.SOURCE_PATHS),
                )
                self.assertNotEqual(
                    snapshot.source_manifest_sha256,
                    snapshot.copy_manifest_sha256,
                )
                evidence.validate_snapshot_manifest_pair(
                    snapshot.pair,
                    snapshot.source_descriptor_set,
                    snapshot.snapshot_descriptor_set,
                )
                plan_mutations = (
                    ("predecessor", {"predecessor_commit": GIT_A}),
                    ("config", {"config_root": "/private/tmp/caller-config"}),
                    ("host", {"host_uri": "unix:///private/tmp/caller.sock"}),
                    ("temporary", {"temporary_root": "/private/tmp/caller-temp"}),
                )
                for label, overrides in plan_mutations:
                    mutation_parent = parent / ("a3l7-plan-" + label)
                    mutation_parent.mkdir(mode=0o700)
                    runner_calls = []
                    with self.assertRaisesRegex(
                        execution.ExecutionError,
                        "readiness plan is not the canonical executable plan",
                    ):
                        execute_fake_a3l7(
                            live_bundle,
                            mutation_parent,
                            plan_overrides=overrides,
                            runner_calls=runner_calls,
                        )
                    self.assertEqual(runner_calls, [])
                    retained_empty_root = mutation_parent / "a3l7-output"
                    self.assertTrue(retained_empty_root.is_dir())
                    self.assertEqual(list(retained_empty_root.iterdir()), [])
                symlink_fixture = parent / "a3l7-symlink-fixture"
                symlink_fixture.mkdir(mode=0o700)
                symlink_target = parent / "a3l7-symlink-target"
                symlink_target.mkdir(mode=0o700)
                symlink_ancestor = parent / "a3l7-symlink-ancestor"
                symlink_ancestor.symlink_to(symlink_target, target_is_directory=True)
                symlink_runner_calls = []
                with mock.patch.object(
                    execution, "_capture_readiness_inputs",
                    side_effect=AssertionError(
                        "readiness capture ran before output authority"
                    ),
                ), self.assertRaisesRegex(
                    execution.ExecutionError, "output traversal"
                ):
                    execute_fake_a3l7(
                        live_bundle,
                        symlink_fixture,
                        output_root=symlink_ancestor / "a3l7-output",
                        runner_calls=symlink_runner_calls,
                    )
                self.assertEqual(symlink_runner_calls, [])
                self.assertEqual(list(symlink_target.iterdir()), [])

                swap_fixture = parent / "a3l7-output-swap-fixture"
                swap_fixture.mkdir(mode=0o700)
                swap_output = swap_fixture / "a3l7-output"
                displaced_output = swap_fixture / "a3l7-output-displaced"
                swap_state = {"done": False}

                def swap_a3l7_output(_role):
                    if swap_state["done"]:
                        return
                    swap_state["done"] = True
                    swap_output.rename(displaced_output)
                    swap_output.mkdir(mode=0o700)

                with self.assertRaisesRegex(
                    execution.ExecutionError, "logical path changed"
                ):
                    execute_fake_a3l7(
                        live_bundle, swap_fixture,
                        output_root=swap_output,
                        runner_hook=swap_a3l7_output,
                    )
                self.assertTrue(swap_state["done"])
                self.assertEqual(list(swap_output.iterdir()), [])
                self.assertFalse(
                    (swap_output / "readiness/authorization.json").exists()
                )
                self.assertFalse(
                    (displaced_output / "readiness/authorization.json").exists()
                )
                readiness = execute_fake_a3l7(live_bundle, parent)
                self.assertTrue(readiness.readiness_result["accepted"])
                self.assertIsNotNone(readiness.authorization)
                self.assertEqual(
                    readiness.authorization["authorization_id"],
                    json.loads(
                        (parent / "a3l7-output/authority/action.json").read_bytes()
                    )["proposal"]["id"],
                )
                self.assertEqual(len(readiness.observations), 6)
                self.assertEqual(
                    len(
                        list(
                            (parent / "a3l7-output/operations/readiness").glob(
                                "[0-9][0-9][0-9]-*"
                            )
                        )
                    ),
                    6,
                )
                normal_plan = readiness.normal_plan
                self.assertIsNotNone(normal_plan)
                normal_raw = execution.canonical_json_bytes(normal_plan)
                self.assertIn(b"--network=none", normal_raw)
                self.assertIn(b"--pull=never", normal_raw)
                self.assertNotIn(b'"pull"', normal_raw)
                self.assertNotIn(b'"build"', normal_raw)
                self.assertNotIn(b'"login"', normal_raw)
                retained_bindings = json.loads(
                    (parent / "a3l7-output/authority/expected-bindings.json")
                    .read_bytes()
                )
                with bound_a3l7_constants(retained_bindings):
                    retained_material = execution._load_a3l7_campaign_material(
                        a3l7_root=parent / "a3l7-output"
                    )
                authority_path = parent / "a3l7-output/authority"
                displaced_authority = parent / "a3l7-output/authority-old"
                authority_path.rename(displaced_authority)
                authority_path.mkdir(mode=0o700)
                try:
                    with self.assertRaises(execution.ExecutionError):
                        execution._verify_a3l7_material_still_bound(
                            retained_material
                        )
                finally:
                    authority_path.rmdir()
                    displaced_authority.rename(authority_path)
                del retained_material
                with mock.patch.object(
                    execution, "_load_evidence_module",
                    side_effect=AssertionError(
                        "ambient evidence loaded after source verification"
                    ),
                ):
                    campaign_execution = execute_fake_a3l8(
                        a3l7_root=parent / "a3l7-output",
                        repo_root=repository,
                        output_parent=parent / "a3l8-output",
                    )
                candidate_root = Path(campaign_execution.final_path)
                self.assertTrue(candidate_root.is_dir())
                self.assertEqual(
                    [item.attempt_id for item in campaign_execution.attempts],
                    ["normal", "oom"],
                )
                self.assertEqual(
                    len(campaign_execution.publication["ordered_publication_events"]),
                    271,
                )
                self.assertFalse((candidate_root / "candidate-decision.json").exists())
                self.assertFalse((candidate_root / "reviews").exists())
                candidate_files = {
                    entry["path"]: (candidate_root / entry["path"]).read_bytes()
                    for entry in campaign_execution.manifest["entries"]
                }
                with bound_a3l7_constants(retained_bindings):
                    reconstructed = evidence.reconstruct_published_candidate(
                        candidate_files,
                        campaign_execution.manifest,
                        campaign_execution.publication,
                        campaign_execution.repository_state,
                        retained_bindings,
                    )
                    if not all(item["closed"] for item in reconstructed):
                        evidence._reconstruct_c10(
                            candidate_files,
                            retained_bindings,
                            evidence._snapshot_semantics(
                                candidate_files, retained_bindings
                            ),
                        )
                self.assertEqual(
                    reconstructed,
                    [
                        {"class_id": class_id, "closed": True}
                        for class_id in evidence.CLASS_ORDER
                    ],
                )
                for relative in (
                    "tools/hsai-formal-preflight/p01b_container_evidence.py",
                    "tools/hsai-formal-preflight/p01b_container_execution.py",
                ):
                    snapshot_file = parent / "a3l7-output/snapshot/files" / relative
                    original = snapshot_file.read_bytes()
                    snapshot_file.chmod(0o600)
                    snapshot_file.write_bytes(original + b"\n")
                    snapshot_file.chmod(0o444)
                    try:
                        with mock.patch.object(
                            execution, "_a3l9_start_child",
                            side_effect=AssertionError("child launched before bootstrap"),
                        ), self.assertRaisesRegex(
                            execution.ExecutionError, "bootstrap snapshot bytes"
                        ):
                            execution.execute_a3l9_acceptance(
                                a3l7_root=parent / "a3l7-output",
                                campaign=campaign_execution,
                                output_parent=parent / "a3l8-output",
                            )
                    finally:
                        snapshot_file.chmod(0o600)
                        snapshot_file.write_bytes(original)
                        snapshot_file.chmod(0o444)
                    self.assertFalse(
                        (parent / "a3l8-output/artifacts/decision").exists()
                    )
                collector_path = (
                    parent / "a3l7-output/snapshot/files/tools/hsai-formal-preflight/"
                    "p01b_container_execution.py"
                )
                collector_parent = collector_path.parent
                displaced_collector = collector_parent / ".collector-retained-old"
                marker_path = parent / "replaced-collector-executed"

                original_start_child = execution._a3l9_start_child
                collector_swap_state = {"done": False}

                def replace_collector_before_exec(argv, ordinal, collector_fd=None):
                    if collector_swap_state["done"]:
                        return original_start_child(argv, ordinal, collector_fd)
                    collector_swap_state["done"] = True
                    collector_parent.chmod(0o700)
                    collector_path.rename(displaced_collector)
                    collector_path.write_bytes(
                        (
                            "from pathlib import Path\n"
                            "Path(%r).write_text('executed')\n" % str(marker_path)
                        ).encode("ascii")
                    )
                    collector_path.chmod(0o444)
                    collector_parent.chmod(0o555)
                    return original_start_child(argv, ordinal, collector_fd)

                try:
                    with mock.patch.object(
                        execution, "_a3l9_start_child",
                        side_effect=replace_collector_before_exec,
                    ), self.assertRaises(execution.ExecutionError):
                        execution.execute_a3l9_acceptance(
                            a3l7_root=parent / "a3l7-output",
                            campaign=campaign_execution,
                            output_parent=parent / "a3l8-output",
                        )
                finally:
                    collector_parent.chmod(0o700)
                    if collector_path.exists():
                        collector_path.chmod(0o600)
                        collector_path.unlink()
                    displaced_collector.rename(collector_path)
                    collector_parent.chmod(0o555)
                self.assertTrue(collector_swap_state["done"])
                self.assertFalse(marker_path.exists())
                self.assertFalse(
                    (parent / "a3l8-output/artifacts/decision").exists()
                )
                acceptance_execution = execution.execute_a3l9_acceptance(
                    a3l7_root=parent / "a3l7-output",
                    campaign=campaign_execution,
                    output_parent=parent / "a3l8-output",
                )
                self.assertEqual(
                    acceptance_execution.acceptance["correspondence_score"],
                    "10/10",
                )
                self.assertEqual(
                    acceptance_execution.acceptance["closed_classes"],
                    list(evidence.CLASS_ORDER),
                )
                self.assertEqual(
                    stat.S_IMODE(
                        os.lstat(acceptance_execution.acceptance_path).st_mode
                    ),
                    0o600,
                )
                launch_fds = []
                for role in execution.REVIEW_ROLE_ORDER:
                    launch = json.loads(
                        (
                            Path(acceptance_execution.review_session_path).parent
                            / role / "review-launch.json"
                        ).read_bytes()
                    )
                    argv = launch["command_observation"]["argv"]
                    self.assertEqual(
                        argv[:5],
                        [
                            "/usr/bin/python3", "-I", "-B", "-c",
                            execution._A3L9_DESCRIPTOR_BOOTSTRAP,
                        ],
                    )
                    launch_fds.append(argv[5])
                self.assertEqual(len(set(launch_fds)), 2)
                wrong_output = parent / "a3l8-wrong-mode"
                wrong_output.mkdir(mode=0o755)
                wrong_output.chmod(0o755)
                with self.assertRaisesRegex(
                    execution.ExecutionError, "owned directory"
                ):
                    execute_fake_a3l8(
                        a3l7_root=parent / "a3l7-output",
                        repo_root=repository,
                        output_parent=wrong_output,
                    )
                network_tamper = json.loads(normal_raw)
                create_argv = network_tamper["commands"][2]["argv"]
                create_argv[create_argv.index("--network=none")] = "--network=bridge"
                output = parent / "a3l7-output"
                load = lambda relative: json.loads((output / relative).read_bytes())
                with self.assertRaises(evidence.EvidenceError):
                    evidence.validate_authority_graph(
                        b"retain one bounded normal/OOM local campaign; no stronger claims",
                        load("authority/action.json"),
                        load("authority/policy.json"),
                        load("authority/evidence-bundle.json"),
                        load("authority/admission-decision.json"),
                        live_bundle,
                        readiness.readiness_plan,
                        execution.canonical_claim_boundary(),
                        readiness.preauthorization,
                        load("authority/expected-bindings.json"),
                        readiness.readiness_result,
                        load("authority/authorization-root.json"),
                        readiness.authorization,
                        readiness.campaign_plan,
                        network_tamper,
                        readiness.oom_plan,
                    )
                cycle_tamper = dict(readiness.authorization)
                cycle_tamper["normal_plan_sha256"] = HEX_A
                with self.assertRaises(evidence.EvidenceError):
                    evidence.validate_authorization(cycle_tamper)
                failure_parent = parent / "a3l7-negative"
                failure_parent.mkdir(mode=0o700)
                rejected = execute_fake_a3l7(
                    live_bundle,
                    failure_parent,
                    stream_drift_role="buildx-version",
                )
                self.assertFalse(rejected.readiness_result["accepted"])
                self.assertEqual(
                    rejected.readiness_result["failure"],
                    "version_transcript_drift",
                )
                self.assertIsNone(rejected.authorization)
                self.assertIsNone(rejected.normal_plan)
                self.assertFalse(
                    (
                        failure_parent
                        / "a3l7-output/authority/authorization-root.json"
                    ).exists()
                )
                self.assertFalse(
                    (
                        failure_parent / "a3l7-output/readiness/normal-plan.json"
                    ).exists()
                )
                self.assertEqual(
                    [item.value["outcome"] for item in rejected.observations],
                    ["exit", "exit", "exit", "exit", "not_run", "not_run"],
                )
                for failure in ("identity_drift", "context_drift"):
                    failure_parent = parent / ("a3l7-" + failure)
                    failure_parent.mkdir(mode=0o700)
                    preflight_rejected = execute_fake_a3l7(
                        live_bundle,
                        failure_parent,
                        preflight_failure=failure,
                    )
                    self.assertEqual(
                        preflight_rejected.readiness_result["failure"], failure
                    )
                    self.assertEqual(
                        [
                            item.value["outcome"]
                            for item in preflight_rejected.observations
                        ],
                        ["not_run"] * 6,
                    )
                    self.assertIsNone(preflight_rejected.authorization)
                descriptor_parent = parent / "a3l7-descriptor-drift"
                descriptor_parent.mkdir(mode=0o700)
                with mock.patch.object(
                    execution,
                    "_readiness_descriptor_recheck_failure",
                    return_value="descriptor_drift",
                ):
                    descriptor_rejected = execute_fake_a3l7(
                        live_bundle, descriptor_parent
                    )
                self.assertEqual(
                    descriptor_rejected.readiness_result["failure"],
                    "descriptor_drift",
                )
                self.assertEqual(
                    [item.value["outcome"] for item in descriptor_rejected.observations],
                    ["not_run"] * 6,
                )
                persistence_parent = parent / "a3l7-persistence-failure"
                persistence_parent.mkdir(mode=0o700)
                tracked_writer = execution._a3l7_write_at

                def fail_campaign_plan(
                    root_fd, relative, raw, *, file_mode=0o600
                ):
                    if relative == "readiness/campaign-plan.json":
                        raise OSError("injected finalization failure")
                    return tracked_writer(
                        root_fd, relative, raw, file_mode=file_mode
                    )

                with mock.patch.object(
                    execution, "_a3l7_write_at", fail_campaign_plan
                ):
                    with self.assertRaisesRegex(
                        OSError, "injected finalization failure"
                    ):
                        execute_fake_a3l7(live_bundle, persistence_parent)
                persistence_output = persistence_parent / "a3l7-output"
                for relative in (
                    "authority/authorization-root.json",
                    "readiness/authorization.json",
                    "readiness/campaign-plan.json",
                    "readiness/normal-plan.json",
                    "readiness/oom-plan.json",
                ):
                    self.assertFalse((persistence_output / relative).exists())
                tampered_run = execution.A3L6GateRun(
                    live_run.gate_plan,
                    live_run.gate_source_manifest,
                    live_run.python_version_observation,
                    live_run.ordered_gate_observations,
                    live_run.focused_test_ids,
                    63,
                    172,
                )
                with self.assertRaises(execution.ExecutionError):
                    execution.assemble_a3l6_gate_bundle(
                        tampered_run, live_reviews
                    )
                tampered_bundle = json.loads(
                    execution.canonical_json_bytes(live_bundle)
                )
                tampered_bundle["ordered_gate_observations"][0][
                    "stderr_sha256"
                ] = HEX_A
                with self.assertRaises(execution.ExecutionError):
                    execution.validate_a3l6_gate_bundle(tampered_bundle)
                tampered_bindings = dict(bindings)
                tampered_bindings["a3l6_gate_bundle_sha256"] = HEX_A
                with self.assertRaises(execution.ExecutionError):
                    execution.validate_a3l6_gate_bundle(
                        live_bundle, tampered_bindings
                    )

                sandbox_observation = execution.capture_descriptor_observation(
                    Path(execution.SANDBOX_EXEC_PATH), "gate-sandbox-exec"
                )
                profile_observation = execution.capture_descriptor_observation(
                    Path(materialized.profile_path), "gate-sandbox-profile"
                )
                python_observation, python_raw = execution._source_command(
                    role="gate-python-version",
                    argv=("/usr/bin/python3", "--version"),
                    environment=capture.environment,
                    cwd=materialized.source_root,
                    stdout_cap=16_384,
                    expected_executable_sha256=execution.NATIVE_PYTHON_SHA256,
                )
                self.assertEqual(python_raw, b"Python 3.9.6\n")
                post_started = time.monotonic_ns()
                inventory_after, post_observations, post_timings = (
                    execution._capture_gate_tree(
                        Path(materialized.source_root), "gate-source-post"
                    )
                )
                status_after, status_raw = execution._source_command(
                    role="gate-status-after",
                    argv=(
                        capture.git_path,
                        "status",
                        "--porcelain=v2",
                        "-z",
                        "--untracked-files=all",
                    ),
                    environment=capture.environment,
                    cwd=capture.repository_cwd,
                    stdout_cap=1_048_576,
                    expected_executable_sha256=capture.git_sha256,
                )
                self.assertEqual(
                    status_raw,
                    execution._decode_observation_stream(
                        capture.status_before_observation, "stdout"
                    ),
                )
                source_rows = []
                for original, post, timing in zip(
                    capture.ordered_sources, post_observations, post_timings
                ):
                    row = dict(original)
                    row["post_gate_started_monotonic_ns"] = timing[0]
                    row["post_gate_ended_monotonic_ns"] = timing[1]
                    row["post_gate_descriptor_observation"] = post
                    source_rows.append(row)
                inventory_before_raw = execution.canonical_json_bytes(
                    list(materialized.inventory)
                )
                inventory_after_raw = execution.canonical_json_bytes(
                    list(inventory_after)
                )
                profile_raw = Path(materialized.profile_path).read_bytes()
                root_identity = execution._identity(
                    os.lstat(materialized.source_root)
                )
                manifest = {
                    "schema": "hsai-p01b-a3l6-gate-source-manifest-v1",
                    "implementation_commit": capture.implementation_commit,
                    "implementation_tree": capture.implementation_tree,
                    "audit_commit": capture.audit_commit,
                    "git_path": capture.git_path,
                    "git_sha256": capture.git_sha256,
                    "environment": dict(capture.environment),
                    "repository_cwd": capture.repository_cwd,
                    "materialized_root": materialized.source_root,
                    "materialized_root_identity": root_identity,
                    "gate_temp_root": materialized.scratch_root,
                    "sandbox_exec_descriptor_observation": sandbox_observation,
                    "sandbox_profile_path": materialized.profile_path,
                    "sandbox_profile_descriptor_observation": profile_observation,
                    "sandbox_profile_base64": base64.b64encode(profile_raw).decode(
                        "ascii"
                    ),
                    "sandbox_profile_sha256": hashlib.sha256(profile_raw).hexdigest(),
                    "materialized_inventory_before_sha256": hashlib.sha256(
                        inventory_before_raw
                    ).hexdigest(),
                    "materialized_inventory_before": list(materialized.inventory),
                    "materialized_inventory_after_sha256": hashlib.sha256(
                        inventory_after_raw
                    ).hexdigest(),
                    "materialized_inventory_after": list(inventory_after),
                    "head_observation": dict(capture.head_observation),
                    "tree_observation": dict(capture.tree_observation),
                    "status_before_observation": dict(
                        capture.status_before_observation
                    ),
                    "ordered_blob_observations": [
                        dict(item) for item in capture.ordered_blob_observations
                    ],
                    "ordered_sources": source_rows,
                    "pre_gate_capture_ended_monotonic_ns": capture.pre_gate_capture_ended_monotonic_ns,
                    "post_gate_capture_started_monotonic_ns": post_started,
                    "status_after_observation": status_after,
                }
                plan = execution.build_a3l6_gate_plan(
                    capture=capture, gate_source_manifest=manifest
                )
                self.assertEqual(len(plan["commands"]), 3)
                self.assertTrue(
                    all(
                        command_row["argv"][:4]
                        == [
                            execution.SANDBOX_EXEC_PATH,
                            "-f",
                            materialized.profile_path,
                            "/usr/bin/python3",
                        ]
                        for command_row in plan["commands"]
                    )
                )
                evidence_ids = execution._focused_ids_from_source(
                    execution.SOURCE_PATHS[-1],
                    (Path(materialized.source_root) / execution.SOURCE_PATHS[-1]).read_bytes(),
                )
                execution_ids = execution._focused_ids_from_source(
                    execution.SOURCE_PATHS[-2],
                    (Path(materialized.source_root) / execution.SOURCE_PATHS[-2]).read_bytes(),
                )
                discovery_ids = [
                    "fixture.DiscoveryGateFixture.test_%03d" % index
                    for index in range(172)
                ]
                span = post_started - capture.pre_gate_capture_ended_monotonic_ns
                self.assertGreaterEqual(span, 7)
                step = span // 7
                transcripts = (
                    unittest_transcript(evidence_ids),
                    unittest_transcript(execution_ids),
                    unittest_transcript(discovery_ids),
                )
                observations = tuple(
                    synthetic_gate_observation(
                        command_row,
                        root_identity,
                        transcripts[index],
                        capture.pre_gate_capture_ended_monotonic_ns
                        + step * (index * 2 + 1),
                        capture.pre_gate_capture_ended_monotonic_ns
                        + step * (index * 2 + 2),
                    )
                    for index, command_row in enumerate(plan["commands"])
                )
                self.assertEqual(
                    execution.parse_unittest_transcript(
                        transcripts[0], expected_count=32, expected_ids=evidence_ids
                    ),
                    tuple(evidence_ids),
                )
                execution.validate_a3l6_gate_plan_execution(
                    plan, manifest, observations
                )
                run = execution.A3L6GateRun(
                    plan,
                    manifest,
                    python_observation,
                    observations,
                    capture.focused_test_ids,
                    64,
                    172,
                )
                reviews = (
                    execution.build_a3l6_code_review_record(
                        run,
                        role="security-capability",
                        reviewer_id="security-reviewer",
                        findings=(),
                    ),
                    execution.build_a3l6_code_review_record(
                        run,
                        role="correspondence-reproducibility",
                        reviewer_id="correspondence-reviewer",
                        findings=(),
                    ),
                )
                bundle = execution.assemble_a3l6_gate_bundle(run, reviews)
                self.assertEqual(bundle["result"], "accept")
                tampered = json.loads(execution.canonical_json_bytes(plan))
                tampered["commands"][0]["timeout_ns"] += 1
                with self.assertRaises(execution.ExecutionError):
                    execution.validate_a3l6_gate_plan_execution(
                        tampered, manifest, observations
                    )
                duplicate_review = dict(reviews[1])
                duplicate_review["reviewer_id"] = reviews[0]["reviewer_id"]
                with self.assertRaises(execution.ExecutionError):
                    execution.assemble_a3l6_gate_bundle(
                        run, (reviews[0], duplicate_review)
                    )
                rejected_review = execution.build_a3l6_code_review_record(
                    run,
                    role="correspondence-reproducibility",
                    reviewer_id="rejecting-correspondence-reviewer",
                    findings=("retained finding",),
                )
                rejected_bundle = execution.assemble_a3l6_gate_bundle(
                    run, (reviews[0], rejected_review)
                )
                self.assertEqual(rejected_bundle["result"], "reject")
                with self.assertRaisesRegex(
                    execution.ExecutionError, "not independently accepted"
                ):
                    execution.validate_a3l6_gate_bundle(rejected_bundle)
        finally:
            thaw(parent / "source")
            shutil.rmtree(parent, ignore_errors=True)

    def test_codesign_verify_parser_requires_paired_canonical_paths(self) -> None:
        raw = (
            b"--prepared:/Applications/Docker.app/Contents/MacOS/Docker Desktop\n"
            b"--validated:/Applications/Docker.app/Contents/MacOS/Docker Desktop\n"
            b"/Applications/Docker.app: valid on disk\n"
            b"/Applications/Docker.app: satisfies its Designated Requirement\n"
        )
        parsed = execution.parse_codesign_verify(raw)
        self.assertEqual(parsed["prepared_paths"], parsed["validated_paths"])
        with self.assertRaises(execution.ExecutionError):
            execution.parse_codesign_verify(raw.replace(b"/MacOS/", b"/Resources/", 1))

    def test_recovery_inspection_recomputes_absent_present_and_collision_branches(
        self,
    ) -> None:
        labels = execution.expected_container_labels("cc", "normal", HEX_A, GIT_A)
        name = "hsai-p01b-cc-normal"
        absent_error = ("Error response from daemon: No such container: %s\n" % name).encode("ascii")
        self.assertEqual(
            execution.classify_recovery_inspection(
                recovery_observation(stdout=b"", stderr=absent_error, exit_code=1),
                container_name=name,
                expected_labels=labels,
                bound_container_id=None,
            ),
            ("absent", None),
        )
        cid = "d" * 64
        for running, expected in ((True, "present-running"), (False, "present-stopped")):
            branch = execution.classify_recovery_inspection(
                recovery_observation(stdout=inspect_array(
                    container_id=cid, name="/" + name, labels=labels, running=running
                )),
                container_name=name,
                expected_labels=labels,
                bound_container_id=cid,
            )
            self.assertEqual(branch, (expected, cid))
        collision = execution.classify_recovery_inspection(
            recovery_observation(stdout=inspect_array(
                container_id="e" * 64, name=name, labels=labels, running=True
            )),
            container_name=name,
            expected_labels=labels,
            bound_container_id=cid,
        )
        self.assertEqual(collision, ("collision", None))
        with self.assertRaisesRegex(execution.ExecutionError, "inspection_failed"):
            execution.classify_recovery_inspection(
                recovery_observation(stdout=b"not-json\n"),
                container_name=name,
                expected_labels=labels,
                bound_container_id=None,
            )
        # Host-only: second half opens resolved /private/tmp trees via A3L9.
        if _gate_sandbox_active():
            self.assertEqual(os.environ.get("P01B_GATE_SANDBOX_ACTIVE"), "1")
            return
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            prefix = ("/usr/bin/python3",)
            environment = {"PATH": "/usr/bin:/bin"}
            intent = execution.build_container_intent(
                campaign_id="cc", attempt_id="normal",
                authorization_sha256=HEX_A, implementation_commit=GIT_A,
                attempt_plan_sha256=HEX_B, created_monotonic_ns=1,
            )

            def terminal_bytes(container: str) -> bytes:
                value = json.loads(inspect_array(
                    container_id=container, name="/" + name,
                    labels=labels, running=False,
                ))
                value[execution.INSPECT_FIELDS.index("State.ExitCode")] = 0
                return execution.canonical_json_bytes(value) + b"\n"

            def run_case(
                case: str, root: Path, *, cleanup_failure: bool = False
            ) -> tuple[execution.RawObservation, ...]:
                def runner(command_value, **values):
                    role = command_value.role
                    target = command_value.argv[-1]
                    stdout, stderr, status = b"", b"", 0
                    if role == "recovery-inspect":
                        if case == "absent":
                            stderr = (
                                "Error response from daemon: No such container: "
                                + name + "\n"
                            ).encode("ascii")
                            status = 1
                        elif case == "collision":
                            stdout = inspect_array(
                                container_id="e" * 64, name=name,
                                labels={**labels, "unexpected": "collision"},
                                running=True,
                            )
                        else:
                            stdout = inspect_array(
                                container_id=cid, name="/" + name,
                                labels=labels, running=case == "running",
                            )
                    elif role in {"recovery-kill", "recovery-remove"}:
                        stdout = (cid + "\n").encode("ascii")
                        if cleanup_failure and role == "recovery-remove":
                            stdout = b"wrong\n"
                    elif role == "recovery-wait":
                        stdout = b"0\n"
                    elif role == "recovery-terminal-inspect":
                        stdout = terminal_bytes(cid)
                    elif role in {"recovery-absence-cid", "recovery-absence-name"}:
                        stderr = (
                            "Error response from daemon: No such container: "
                            + target + "\n"
                        ).encode("ascii")
                        status = 1
                    elif role == "recovery-daemon-recheck":
                        stdout = b"{}\n"
                    value = execution._observation_value(
                        command=command_value,
                        plan_sha256=values["plan_sha256"],
                        completion_ordinal=values["completion_ordinal"],
                        executable_sha256=execution.NATIVE_PYTHON_SHA256,
                        started_ns=10 + values["completion_ordinal"] * 2,
                        ended_ns=11 + values["completion_ordinal"] * 2,
                        outcome="exit", exit_code=status,
                        terminating_signal=None, stdout=stdout, stderr=stderr,
                        previous_observation_sha256=values.get(
                            "previous_observation_sha256"
                        ),
                        container_id=values.get("container_id"),
                        raw_directory=None,
                    )
                    return execution.RawObservation(value, stdout, stderr)

                return execution.execute_closed_recovery(
                    prefix=prefix, environment=environment,
                    container_name=name, container_id=None,
                    campaign_id="cc", attempt_id="normal",
                    authorization_sha256=HEX_A,
                    implementation_commit=GIT_A, raw_root=root,
                    runner=runner, intent=intent,
                )

            for case, expected_failure in (
                ("absent", "campaign_failed_container_absent"),
                ("running", "campaign_failed_container_removed"),
                ("stopped", "campaign_failed_container_removed"),
            ):
                root = parent / case
                observations = run_case(case, root)
                result = json.loads((root / "recovery-result.json").read_bytes())
                self.assertTrue(result["cleanup_complete"])
                self.assertEqual(result["failure"], expected_failure)
                self.assertEqual(
                    len(observations),
                    4 if case == "absent" else (9 if case == "running" else 8),
                )
                if case == "stopped":
                    self.assertEqual(
                        [item.value["outcome"] for item in observations[1:3]],
                        ["not_run", "not_run"],
                    )
            collision_root = parent / "collision"
            with self.assertRaisesRegex(
                execution.ExecutionError, "identity collision"
            ):
                run_case("collision", collision_root)
            collision = json.loads(
                (collision_root / "recovery-result.json").read_bytes()
            )
            self.assertEqual(collision["failure"], "identity_collision")
            self.assertEqual(
                json.loads((collision_root / "cleanup-plan.json").read_bytes())[
                    "commands"
                ],
                [],
            )
            incomplete_root = parent / "incomplete"
            with self.assertRaisesRegex(
                execution.ExecutionError, "cleanup remained incomplete"
            ):
                run_case("running", incomplete_root, cleanup_failure=True)
            incomplete = json.loads(
                (incomplete_root / "recovery-result.json").read_bytes()
            )
            receipts = json.loads(
                (incomplete_root / "ordered-receipts.json").read_bytes()
            )
            self.assertEqual(incomplete["failure"], "recovery_incomplete")
            self.assertEqual(len(receipts), 9)
            self.assertTrue(
                all(item["outcome"] == "not_run" for item in receipts[5:])
            )
            self.assertFalse(any(parent.glob("p01b-candidate-*")))

            interrupted = parent.resolve() / "post-binding-interruption"
            attempt_root = interrupted / "attempt"
            raw_root = interrupted / "operations"
            attempt_root.mkdir(mode=0o700, parents=True)
            raw_root.mkdir(mode=0o700)
            attempt_fd = os.open(
                str(attempt_root), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            raw_fd = os.open(
                str(raw_root), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            attempt_plan = execution.build_attempt_plan(
                campaign_id="campaign", attempt_id="normal",
                authorization_sha256=HEX_A,
                implementation_commit=GIT_A,
                platform_reference=PLATFORM,
                source_manifest_sha256=HEX_B,
                config_root="/cfg", host_uri="unix:///socket",
                temporary_root="/tmp/p01b", snapshot_root="/snapshot",
                seccomp_path="/snapshot/seccomp.json",
            )
            stable_cid = "d" * 64
            expected_name = "hsai-p01b-campaign-normal"
            expected_labels = execution.expected_container_labels(
                "campaign", "normal", HEX_A, GIT_A
            )
            sink_values: list[str] = []
            mutation_roles: list[tuple[str, str]] = []
            clock = StepClock()

            def interruption_runner(command_value, **values):
                role = command_value.role
                stdout, stderr, status = b"", b"", 0
                if role == "absence-name-pre":
                    stderr = (
                        "Error response from daemon: No such container: "
                        + expected_name + "\n"
                    ).encode("ascii")
                    status = 1
                elif role == "create":
                    stdout = (stable_cid + "\n").encode("ascii")
                elif role == "recovery-inspect":
                    stdout = inspect_array(
                        container_id=stable_cid, name="/" + expected_name,
                        labels=expected_labels, running=True,
                    )
                elif role in {"recovery-kill", "recovery-remove"}:
                    mutation_roles.append((role, command_value.argv[-1]))
                    stdout = (stable_cid + "\n").encode("ascii")
                elif role == "recovery-wait":
                    stdout = b"0\n"
                elif role == "recovery-terminal-inspect":
                    terminal = json.loads(inspect_array(
                        container_id=stable_cid, name="/" + expected_name,
                        labels=expected_labels, running=False,
                    ))
                    terminal[
                        execution.INSPECT_FIELDS.index("State.ExitCode")
                    ] = 0
                    stdout = execution.canonical_json_bytes(terminal) + b"\n"
                elif role in {
                    "recovery-absence-cid", "recovery-absence-name",
                }:
                    stderr = (
                        "Error response from daemon: No such container: "
                        + command_value.argv[-1] + "\n"
                    ).encode("ascii")
                    status = 1
                elif role == "recovery-daemon-recheck":
                    stdout = b"{}\n"
                started = clock(); ended = clock()
                value = execution._observation_value(
                    command=command_value,
                    plan_sha256=values["plan_sha256"],
                    completion_ordinal=values["completion_ordinal"],
                    executable_sha256=execution.DOCKER_SHA256,
                    started_ns=started, ended_ns=ended,
                    outcome="exit", exit_code=status,
                    terminating_signal=None, stdout=stdout, stderr=stderr,
                    previous_observation_sha256=values.get(
                        "previous_observation_sha256"
                    ),
                    container_id=values.get("container_id"),
                    raw_directory=None,
                )
                return execution.RawObservation(value, stdout, stderr)

            def interrupt_after_binding() -> None:
                raise RuntimeError("injected after CID directory fsync")

            try:
                with self.assertRaisesRegex(
                    RuntimeError, "injected after CID directory fsync"
                ):
                    execution._execute_attempt(
                        plan=attempt_plan,
                        authorization_sha256=HEX_A,
                        implementation_commit=GIT_A,
                        snapshot=execution.SnapshotResult(
                            "/snapshot", tuple(), HEX_B
                        ),
                        snapshot_pair={}, raw_root=raw_root,
                        attempt_root=attempt_root, raw_root_fd=raw_fd,
                        attempt_root_fd=attempt_fd,
                        runner=interruption_runner,
                        spanning_executor=lambda **_values: None,
                        clock=clock,
                        container_id_sink=sink_values.append,
                        evidence_module=evidence,
                        post_binding_durability_hook=
                            interrupt_after_binding,
                    )
                self.assertEqual(sink_values, [])
                self.assertTrue((attempt_root / "cid-binding.json").is_file())
                execution._recover_failed_attempt(
                    plan=attempt_plan, container_id=None,
                    authorization_sha256=HEX_A,
                    implementation_commit=GIT_A,
                    raw_root=attempt_root / "recovery",
                    runner=interruption_runner,
                    attempt_root_fd=attempt_fd,
                )
            finally:
                os.close(raw_fd)
                os.close(attempt_fd)
            recovery_result = json.loads(
                (attempt_root / "recovery/recovery-result.json").read_bytes()
            )
            self.assertTrue(recovery_result["cleanup_complete"])
            self.assertEqual(
                mutation_roles,
                [
                    ("recovery-kill", stable_cid),
                    ("recovery-remove", stable_cid),
                ],
            )
            self.assertFalse(any(interrupted.glob("p01b-candidate-*")))

    def test_recovery_failure_artifact_and_suffix_are_total_and_not_run(self) -> None:
        labels = execution.expected_container_labels("cc", "normal", HEX_A, GIT_A)
        plan = execution.build_recovery_cleanup_plan(
            intent_sha256=HEX_A,
            cid_binding_sha256=HEX_B,
            inspection_observation_sha256=HEX_C,
            selected_branch="present-running",
            container_id="d" * 64,
            expected_labels=labels,
            container_name="hsai-p01b-cc-normal",
            prefix=("/usr/bin/python3",),
            environment={"PATH": "/usr/bin:/bin"},
        )
        self.assertEqual(len(plan["commands"]), 8)
        failure = execution.build_recovery_inspection_failure(
            intent_sha256=HEX_A,
            inspection_plan_sha256=HEX_B,
            inspection_receipt_sha256=HEX_C,
        )
        self.assertEqual(failure["failure"], "inspection_failed")
        with tempfile.TemporaryDirectory() as temporary:
            suffix = execution.build_recovery_not_run_suffix(
                plan,
                failed_command_index=0,
                plan_sha256=HEX_A,
                previous_observation_sha256=HEX_B,
                raw_root=Path(temporary) / "recovery",
            )
            self.assertEqual(len(suffix), 7)
            self.assertTrue(all(item.value["outcome"] == "not_run" for item in suffix))
            self.assertEqual(
                [item.value["role"] for item in suffix],
                [item["role"] for item in plan["commands"][1:]],
            )
        result = execution.build_recovery_result(
            intent_sha256=HEX_A,
            inspection_plan_sha256=HEX_B,
            cleanup_plan_sha256=HEX_C,
            ordered_receipts=[{"receipt": "inspection"}],
            selected_branch="present-running",
            cleanup_complete=False,
            failure="recovery_incomplete",
        )
        self.assertFalse(result["cleanup_complete"])


class ExecutorTests(unittest.TestCase):
    def test_direct_executor_closes_stdin_and_retains_raw_streams(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "raw"
            result = execution.execute_direct(
                command(
                    "native-reference",
                    "import sys; data=sys.stdin.buffer.read(); print('closed' if data == b'' else 'open')",
                ),
                plan_sha256=HEX_A,
                completion_ordinal=4,
                raw_root=raw,
            )
            self.assertEqual(result.stdout, b"closed\n")
            self.assertEqual(result.value["exit_code"], 0)
            directory = raw / "004-native-reference"
            self.assertEqual((directory / "stdout.bin").read_bytes(), b"closed\n")
            self.assertEqual(
                stat.S_IMODE((directory / "stdout.bin").stat().st_mode), 0o600
            )
            self.assertEqual(
                (directory / "observation.json").read_bytes(),
                execution.canonical_json_bytes(result.value),
            )
            evidence.validate_observation(result.value, result.stdout, result.stderr)

    def test_stdout_limit_kills_real_process_group_and_a3l9_rejects_overflow(
        self,
    ) -> None:
        # Host-only: Seatbelt alters DirectProcess stream-cap / kill outcomes.
        if _gate_sandbox_active():
            self.assertEqual(os.environ.get("P01B_GATE_SANDBOX_ACTIVE"), "1")
            return
        code = "import os,signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); os.fork(); os.write(1,b'x'*4096); time.sleep(10)"
        with tempfile.TemporaryDirectory() as temporary:
            process = execution.DirectProcess(
                command("overflow", code, cap=64),
                raw_root=Path(temporary) / "raw",
                storage_ordinal=0,
            )
            group = process.process.pid
            result = process.complete(
                plan_sha256=HEX_A,
                completion_ordinal=0,
                previous_observation_sha256=None,
            )
            self.assertEqual(result.value["outcome"], "stdout_limit")
            self.assertEqual(len(result.stdout), 65)
            self.assertFalse(execution._group_exists(group))
            evidence.validate_observation(result.value, result.stdout, result.stderr)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            aggregate = root / "review-aggregate.json"
            acceptance = root / "acceptance-record.json"
            raw = [
                "decide-v3", "--candidate-root", str(root / "candidate"),
                "--collector-logical-path", str(root / "collector.py"),
                "--publication-record", str(root / "publication.json"),
                "--repository-state", str(root / "repository.json"),
                "--expected-bindings", str(root / "bindings.json"),
                "--implementation-commit", GIT_A,
                "--decision-output", str(root / "candidate-decision.json"),
            ]
            for stream in ("stdout", "stderr"):
                collector = root / ("overflow-" + stream + ".py")
                descriptor = "1" if stream == "stdout" else "2"
                collector.write_text(
                    "import os,time\n"
                    "os.write(" + descriptor + ", b'x' * 16385)\n"
                    "time.sleep(10)\n",
                    encoding="ascii",
                )
                raw[4] = str(collector)
                collector_fd = os.open(collector, os.O_RDONLY)
                try:
                    with self.subTest(stream=stream), mock.patch.object(
                        execution, "A3L9_TIMEOUT_NS", 2_000_000_000
                    ):
                        with self.assertRaisesRegex(
                            execution.ExecutionError, stream + "_limit"
                        ):
                            execution._a3l9_run_child(
                                execution._a3l9_child_command(
                                    str(collector), raw, collector_fd,
                                    hashlib.sha256(collector.read_bytes()).hexdigest(),
                                ),
                                collector_fd=collector_fd,
                            )
                        self.assertFalse(aggregate.exists())
                        self.assertFalse(acceptance.exists())
                finally:
                    os.close(collector_fd)

    def test_timeout_kills_term_ignoring_child_and_grandchild(self) -> None:
        # Host-only: Seatbelt alters DirectProcess / probe stream-cap outcomes.
        if _gate_sandbox_active():
            self.assertEqual(os.environ.get("P01B_GATE_SANDBOX_ACTIVE"), "1")
            return
        code = "import os,signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); p=os.fork(); (os.fork() if p == 0 else None); time.sleep(10)"
        with tempfile.TemporaryDirectory() as temporary:
            process = execution.DirectProcess(
                command("timeout", code, timeout_ns=100_000_000),
                raw_root=Path(temporary) / "raw",
                storage_ordinal=0,
            )
            group = process.process.pid
            result = process.complete(
                plan_sha256=HEX_A,
                completion_ordinal=0,
                previous_observation_sha256=None,
            )
            self.assertEqual(result.value["outcome"], "timeout")
            self.assertFalse(execution._group_exists(group))
            evidence.validate_observation(result.value, result.stdout, result.stderr)
        probe_path = Path(execution.__file__).with_name("p01b_container_probe.py")
        spec = importlib.util.spec_from_file_location(
            "p01b_probe_bounded_fixture", probe_path
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec is not None else None)
        probe = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(probe)  # type: ignore[union-attr]
        environment = {"PATH": "/usr/bin:/bin"}
        returncode, stdout, stderr = probe._run_bounded_command(
            (
                "/usr/bin/python3", "-c",
                "import os; os.write(1,b'o'*40000); os.write(2,b'e'*40000)",
            ),
            cwd="/", env=environment, timeout_seconds=5,
            stdout_cap=40_000, stderr_cap=40_000,
        )
        self.assertEqual((returncode, len(stdout), len(stderr)), (0, 40_000, 40_000))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for case, code, expected in (
                (
                    "cap",
                    "import os,sys,time; open(sys.argv[1],'w').write(str(os.getpid())); os.fork(); os.write(1,b'x'*65); time.sleep(10)",
                    "stdout cap exceeded",
                ),
                (
                    "timeout",
                    "import os,sys,time; open(sys.argv[1],'w').write(str(os.getpid())); os.fork(); time.sleep(10)",
                    "timed out",
                ),
            ):
                pid_file = root / (case + ".pid")
                with self.subTest(case=case), self.assertRaisesRegex(
                    probe._BoundedProcessError, expected
                ):
                    probe._run_bounded_command(
                        ("/usr/bin/python3", "-c", code, str(pid_file)),
                        cwd="/", env=environment, timeout_seconds=1,
                        stdout_cap=64, stderr_cap=64,
                    )
                group = int(pid_file.read_text(encoding="ascii"))
                self.assertFalse(execution._group_exists(group))

    def test_executable_identity_drift_is_rejected_before_launch(self) -> None:
        with self.assertRaises(execution.ExecutionError):
            execution.DirectProcess(
                command("identity", "pass"), expected_executable_sha256=HEX_A
            )

    def test_skipped_role_is_retained_without_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            raw = Path(temporary) / "raw"
            result = execution.build_not_run_observation(
                command("emergency-kill", "raise SystemExit(99)", ordinal=7),
                plan_sha256=HEX_A,
                completion_ordinal=8,
                previous_observation_sha256=None,
                raw_root=raw,
                container_id="d" * 64,
            )
            self.assertEqual(result.value["outcome"], "not_run")
            self.assertEqual(result.value["duration_ns"], 0)
            self.assertEqual((raw / "008-emergency-kill/stdout.bin").read_bytes(), b"")
            # Host-only: path-change check opens resolved /private/tmp via A3L9.
            if _gate_sandbox_active():
                self.assertEqual(os.environ.get("P01B_GATE_SANDBOX_ACTIVE"), "1")
                return
            base = Path(temporary).resolve()
            logical = base / "retained-raw"
            logical.mkdir(mode=0o700)
            descriptor = os.open(
                str(logical), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            displaced = base / "displaced-raw"
            logical.rename(displaced)
            logical.mkdir(mode=0o700)
            try:
                with self.assertRaisesRegex(
                    execution.ExecutionError, "logical path changed"
                ):
                    execution.build_not_run_observation(
                        command("emergency-kill", "pass", ordinal=7),
                        plan_sha256=HEX_A,
                        completion_ordinal=9,
                        previous_observation_sha256=None,
                        raw_root=logical,
                        raw_root_fd=descriptor,
                    )
            finally:
                os.close(descriptor)
            self.assertEqual(list(logical.iterdir()), [])
            self.assertEqual(list(displaced.iterdir()), [])

    def test_running_export_is_retained_before_release_and_start_completion(
        self,
    ) -> None:
        payload = b'{"value":1}'
        ready = b"P01B_RESULT_READY %d %s\n" % (
            len(payload),
            hashlib.sha256(payload).hexdigest().encode("ascii"),
        )
        start_code = "import os,time; os.write(1,%r); time.sleep(0.35)" % ready
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = execution.orchestrate_running_export(
                attempt_id="normal",
                plan_sha256=HEX_A,
                container_id="d" * 64,
                start_command=command("start-attach", start_code, ordinal=4),
                export_command=command(
                    "export-running",
                    "import os,time; time.sleep(.02); os.write(1,b'tar')",
                    ordinal=5,
                    cap=execution.TAR_CAP,
                ),
                release_command=command(
                    "release", "import time; time.sleep(.02)", ordinal=6
                ),
                raw_root=root / "operations",
                readiness_event_path=root / "readiness-event.json",
                first_completion_ordinal=10,
                previous_observation_sha256=None,
                tar_parser=lambda raw: payload if raw == b"tar" else b"",
            )
            self.assertEqual(result.payload, payload)
            self.assertEqual(result.export_observation.value["completion_ordinal"], 10)
            self.assertEqual(result.release_observation.value["completion_ordinal"], 11)
            self.assertEqual(result.start_observation.value["completion_ordinal"], 12)
            self.assertEqual(
                (root / "readiness-event.json").read_bytes(),
                execution.canonical_json_bytes(result.readiness_event),
            )
            self.assertTrue(
                (root / "operations/012-start-attach/stdout.bin").is_file()
            )

    def test_running_export_digest_mismatch_aborts(self) -> None:
        payload = b"{}"
        ready = b"P01B_RESULT_READY %d %s\n" % (
            len(payload),
            hashlib.sha256(payload).hexdigest().encode("ascii"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(execution.ExecutionError):
                execution.orchestrate_running_export(
                    attempt_id="normal",
                    plan_sha256=HEX_A,
                    container_id="d" * 64,
                    start_command=command(
                        "start-attach",
                        "import os,time; os.write(1,%r); time.sleep(10)" % ready,
                        ordinal=4,
                    ),
                    export_command=command(
                        "export-running", "print('tar',end='')", ordinal=5
                    ),
                    release_command=command("release", "pass", ordinal=6),
                    raw_root=root / "operations",
                    readiness_event_path=root / "readiness-event.json",
                    first_completion_ordinal=10,
                    previous_observation_sha256=None,
                    tar_parser=lambda raw: b"wrong",
                )


class SnapshotAndPublicationTests(unittest.TestCase):
    def test_exact_snapshot_is_reopened_rehashed_and_frozen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            source = parent / "source"
            source.mkdir()
            paths = make_source(source)
            snapshot = parent / "snapshot"
            try:
                result = execution.create_frozen_snapshot(source, snapshot, paths)
                self.assertEqual(len(result.entries), execution.SNAPSHOT_FILE_COUNT)
                self.assertEqual(stat.S_IMODE(snapshot.stat().st_mode), 0o555)
                self.assertEqual(
                    stat.S_IMODE((snapshot / paths[0]).stat().st_mode), 0o444
                )
                expected = hashlib.sha256(
                    execution.canonical_json_bytes(
                        [item.to_dict() for item in result.entries]
                    )
                ).hexdigest()
                self.assertEqual(result.manifest_sha256, expected)
            finally:
                thaw(snapshot)

    def test_snapshot_rejects_symlink_and_wrong_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            source = parent / "source"
            source.mkdir()
            paths = make_source(source)
            (source / paths[0]).unlink()
            (source / paths[0]).symlink_to(source / paths[1])
            with self.assertRaises((execution.ExecutionError, OSError)):
                execution.create_frozen_snapshot(source, parent / "snapshot-a", paths)
            (source / paths[0]).unlink()
            (source / paths[0]).write_bytes(b"replacement")
            (source / paths[0]).chmod(0o600)
            with self.assertRaises(execution.ExecutionError):
                execution.create_frozen_snapshot(source, parent / "snapshot-b", paths)

    def test_snapshot_requires_exact_order_and_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            paths = make_source(source)
            with self.assertRaises(execution.ExecutionError):
                execution.create_frozen_snapshot(
                    source, Path(temporary) / "a", paths[:-1]
                )
            with self.assertRaises(execution.ExecutionError):
                execution.create_frozen_snapshot(
                    source, Path(temporary) / "b", list(reversed(paths))
                )

    def test_failure_audit_is_exclusive_and_fsynced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "failure"
            record = {"failure": "bounded"}
            path = execution.write_failure_audit(root, record)
            self.assertEqual(path.read_bytes(), execution.canonical_json_bytes(record))
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                execution.write_failure_audit(root, record)

    def test_darwin_publication_abstraction_is_exclusive_and_identity_bound(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            staging = parent / "staging"
            final = parent / "final"
            staging.mkdir()
            before = os.lstat(staging)

            def rename(
                source_fd: int, source: bytes,
                destination_fd: int, destination: bytes, flags: int,
            ) -> tuple[int, int]:
                self.assertEqual(flags, 0x00000004)
                os.rename(
                    os.fsdecode(source), os.fsdecode(destination),
                    src_dir_fd=source_fd, dst_dir_fd=destination_fd,
                )
                return 0, 0

            result = execution._renameatx_np_exclusive(
                parent, staging.name, final.name, rename
            )
            self.assertEqual(result, (0, 0))
            self.assertTrue(final.is_dir())
            after = os.lstat(final)
            self.assertEqual((before.st_dev, before.st_ino), (after.st_dev, after.st_ino))

    def test_candidate_grammar_has_exact_201_payloads_and_62_directories(self) -> None:
        paths = execution.candidate_payload_paths()
        self.assertEqual(len(paths), 201)
        self.assertEqual(len(execution.candidate_directory_paths(paths)), 62)
        self.assertIn("operations/readiness/005-codesign-display/stderr.bin", paths)
        self.assertIn("operations/normal/006-start-attach/observation.json", paths)
        self.assertNotIn("candidate-manifest.json", paths)

    def test_exact_candidate_materializer_writes_201_payloads_plus_manifest(self) -> None:
        paths = execution.candidate_payload_paths()
        payloads = {path: (path + "\n").encode("ascii") for path in paths}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "candidate"
            manifest = execution.materialize_exact_candidate(
                root,
                payloads,
                authorization_sha256=HEX_A,
                implementation_commit=GIT_A,
            )
            self.assertEqual(len(manifest["entries"]), 201)
            files = [path for path in root.rglob("*") if path.is_file()]
            self.assertEqual(len(files), 202)
            self.assertEqual(
                (root / "candidate-manifest.json").read_bytes(),
                execution.canonical_json_bytes(manifest),
            )

    def test_publication_v2_and_decision_bind_exact_events_and_claim_ceiling(self) -> None:
        operations = (
            ["payload-file-fsync"] * 201
            + ["candidate-manifest-fsync"]
            + ["candidate-directory-fsync"] * 62
            + ["prepublication-inventory", "renameatx-np", "final-parent-fsync",
               "staging-absence", "final-root-reopen", "postpublication-inventory",
               "final-manifest-read"]
        )
        events = [{"operation": value} for value in operations]
        identity = {"device": 1, "inode": 2}
        publication = execution.build_publication_record_v2(
            candidate_manifest_sha256=HEX_A,
            repository_state_sha256=HEX_B,
            staging_path="/outside/.p01b-staging-campaign",
            final_path="/outside/p01b-candidate-campaign",
            parent_identity={"device": 1, "inode": 1},
            prepublication_inventory_sha256=HEX_C,
            postpublication_inventory_sha256=HEX_C,
            staging_identity=identity,
            final_identity=identity,
            ordered_file_reopens=[{} for _ in range(202)],
            ordered_publication_events=events,
            final_manifest_sha256=HEX_A,
        )
        self.assertEqual(publication["schema"], execution.PUBLICATION_SCHEMA)
        boundary = execution.canonical_claim_boundary()
        boundary_sha = execution.claim_boundary_digest(boundary)
        rows = [{"class_id": name, "closed": True} for name in execution.CLASS_ORDER]
        decision = execution.build_postpublication_decision(
            authorization_sha256=HEX_A,
            implementation_commit=GIT_A,
            candidate_manifest_sha256=HEX_B,
            expected_bindings_sha256=HEX_C,
            claim_boundary_sha256=boundary_sha,
            repository_state_sha256=HEX_A,
            publication_record_sha256=HEX_B,
            class_results=rows,
        )
        self.assertEqual(decision["atomic_result"], "accept")
        self.assertFalse(decision["accepted_evidence_created"])
        self.assertEqual(len(boundary["ordered_honesty_assumptions"]), 8)
        self.assertEqual(len(boundary["ordered_nonclaims"]), 11)


class BoundaryGuardTests(unittest.TestCase):
    def test_all_execution_plan_builders_validate_in_evidence_layer(self) -> None:
        readiness = execution.build_readiness_plan(
            predecessor_commit=GIT_A,
            user_authorization_sha256=HEX_A,
            config_root="/cfg",
            host_uri="unix:///socket",
            temporary_root="/tmp/p01b",
        )
        evidence.validate_readiness_plan(readiness)
        attempt = execution.build_attempt_plan(
            campaign_id="campaign",
            attempt_id="normal",
            authorization_sha256=HEX_A,
            implementation_commit=GIT_B,
            platform_reference=PLATFORM,
            source_manifest_sha256=HEX_B,
            config_root="/cfg",
            host_uri="unix:///socket",
            temporary_root="/tmp/p01b",
            snapshot_root="/snapshot",
            seccomp_path="/snapshot/seccomp.json",
        )
        evidence.validate_attempt_plan(attempt)
        environment = execution.closed_host_environment("/cfg", "/tmp/p01b")
        campaign = execution.build_campaign_plan(
            campaign_id="campaign",
            authorization_sha256=HEX_A,
            implementation_commit=GIT_B,
            readiness_plan_sha256=HEX_B,
            native_command=execution.build_native_command("/snapshot", environment),
            metadata_commands=execution.build_metadata_commands(
                execution.docker_prefix("/cfg", "unix:///socket"), environment
            ),
            normal_plan_sha256=HEX_B,
            oom_plan_sha256=HEX_C,
        )
        evidence.validate_campaign_plan(campaign)

    def test_preserved_file_detects_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "protected"
            path.write_bytes(b"initial")
            digest = hashlib.sha256(b"initial").hexdigest()
            execution.verify_preserved_file(path, digest)
            path.write_bytes(b"changed")
            with self.assertRaises(execution.ExecutionError):
                execution.verify_preserved_file(path, digest)

    def test_repository_state_recheck_is_exact(self) -> None:
        outputs = {
            "HEAD": ("1" * 40 + "\n").encode("ascii"),
            "HEAD^{tree}": ("2" * 40 + "\n").encode("ascii"),
            "status": b" M protected\0",
        }

        def runner(argv: object, root: Path) -> bytes:
            del root
            values = list(argv)
            if "status" in values:
                return outputs["status"]
            return outputs[values[-1]]

        with tempfile.TemporaryDirectory() as temporary:
            protected = Path(temporary) / "protected"
            protected.write_bytes(b"bytes")
            bindings = {
                "git_path": "/usr/bin/git",
                "git_sha256": HEX_A,
                "implementation_commit": "1" * 40,
                "implementation_tree": "2" * 40,
            }
            plan = execution._repository_state_plan(
                repo_root=Path(temporary),
                protected_file=protected,
                bindings=bindings,
            )
            clock = StepClock()
            before = execution._repository_capture_v1(
                plan, clock=clock, runner=runner
            )
            after = execution._repository_capture_v1(
                plan, clock=clock, runner=runner
            )
            state = execution._build_repository_state_v1(
                plan=plan, before=before, after=after, bindings=bindings
            )
            self.assertTrue(state["unchanged"])

            def changed_runner(argv: object, root: Path) -> bytes:
                values = list(argv)
                if "status" in values:
                    return b"changed\0"
                return runner(argv, root)

            changed = execution._repository_capture_v1(
                plan, clock=clock, runner=changed_runner
            )
            with self.assertRaises(execution.ExecutionError):
                execution._build_repository_state_v1(
                    plan=plan, before=before, after=changed, bindings=bindings
                )

        # Host-only: second half opens resolved /private/tmp trees via A3L9.
        if _gate_sandbox_active():
            self.assertEqual(os.environ.get("P01B_GATE_SANDBOX_ACTIVE"), "1")
            return

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source_root = root / "source-a3l7"
            source_root.mkdir(mode=0o700)
            authority = source_root / "authority"
            authority.mkdir(mode=0o700)
            snapshot_files = source_root / "snapshot/files"
            snapshot_files.mkdir(mode=0o700, parents=True)
            current_sources = {
                execution._A3L9_COLLECTOR_RELATIVE:
                    Path(execution.__file__).read_bytes(),
                execution._A3L9_VALIDATOR_RELATIVE:
                    Path(evidence.__file__).read_bytes(),
            }
            for relative in execution.SOURCE_PATHS:
                path = snapshot_files / relative
                path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                path.write_bytes(current_sources.get(relative, b"# fixture\n"))
                path.chmod(0o444)
            for directory in sorted(
                (item for item in snapshot_files.rglob("*") if item.is_dir()),
                key=lambda item: len(item.parts), reverse=True,
            ):
                directory.chmod(0o555)
            snapshot_files.chmod(0o555)
            expected = {
                "collector_sha256": hashlib.sha256(
                    current_sources[execution._A3L9_COLLECTOR_RELATIVE]
                ).hexdigest(),
                "validator_sha256": hashlib.sha256(
                    current_sources[execution._A3L9_VALIDATOR_RELATIVE]
                ).hexdigest(),
            }
            expected_path = authority / "expected-bindings.json"
            expected_path.write_bytes(execution.canonical_json_bytes(expected))
            expected_path.chmod(0o600)
            execution._verify_a3l8_running_sources(source_root)
            collector_copy = (
                snapshot_files / execution._A3L9_COLLECTOR_RELATIVE
            )
            collector_copy.chmod(0o600)
            collector_copy.write_bytes(
                current_sources[execution._A3L9_COLLECTOR_RELATIVE] + b"\n"
            )
            collector_copy.chmod(0o444)
            try:
                with self.assertRaisesRegex(
                    execution.ExecutionError,
                    "running source/snapshot binding",
                ):
                    execution._verify_a3l8_running_sources(source_root)
            finally:
                collector_copy.chmod(0o600)
                collector_copy.write_bytes(
                    current_sources[execution._A3L9_COLLECTOR_RELATIVE]
                )
                collector_copy.chmod(0o444)
            thaw(source_root)

            repository = root / "repository"
            repository.mkdir(mode=0o700)
            protected = repository / "protected"
            protected.write_bytes(b"protected")
            protected.chmod(0o600)
            material = mock.Mock()
            material.retained_payloads = {
                "authority/a3l6-gate-bundle.json":
                    execution.canonical_json_bytes({
                        "gate_source_manifest": {
                            "repository_cwd": str(repository),
                        },
                    }),
            }
            material.expected_bindings = {
                "protected_path": str(protected),
                "protected_sha256": hashlib.sha256(b"protected").hexdigest(),
            }
            execution._verify_a3l8_repository_boundary(
                material, repository, protected
            )
            alternate = root / "alternate"
            alternate.mkdir(mode=0o700)
            with self.assertRaisesRegex(
                execution.ExecutionError, "alternate repository/worktree"
            ):
                execution._verify_a3l8_repository_boundary(
                    material, alternate, protected
                )

            a3l7_root = root / "a3l7"
            a3l7_root.mkdir(mode=0o700)
            target = root / "target"
            target.mkdir(mode=0o700)
            linked_ancestor = root / "linked-output"
            linked_ancestor.symlink_to(target, target_is_directory=True)
            output_parent = linked_ancestor / "candidate-parent"
            bindings = {
                "git_path": "/git", "git_sha256": HEX_A,
                "native_python_path": "/python",
                "native_python_sha256": HEX_B,
                "docker_path": "/docker", "docker_sha256": HEX_C,
                "protected_path": str(protected),
                "protected_sha256": hashlib.sha256(b"protected").hexdigest(),
            }
            campaign_material = mock.Mock()
            campaign_material.expected_bindings = bindings
            campaign_material.campaign_plan = {
                "campaign_id": "campaign",
                "normal_plan_sha256": HEX_A,
                "oom_plan_sha256": HEX_A,
            }
            campaign_material.normal_plan = {}
            campaign_material.oom_plan = {}
            campaign_material.authorization = {
                "implementation_commit": GIT_A,
            }
            fake_evidence = mock.Mock()
            fake_evidence.authorization_digest.return_value = HEX_A
            fake_evidence.attempt_plan_digest.return_value = HEX_A
            runner_calls: list[str] = []
            repository_calls: list[str] = []

            def forbidden_runner(*_args, **_values):
                runner_calls.append("runner")
                raise AssertionError("runner must not launch")

            def forbidden_repository(*_args, **_values):
                repository_calls.append("repository")
                raise AssertionError("repository runner must not launch")

            with mock.patch.object(
                execution, "_load_evidence_module",
                side_effect=AssertionError("ambient evidence must not load"),
            ), mock.patch.object(
                execution, "_load_a3l7_campaign_material",
                return_value=campaign_material,
            ), mock.patch.object(
                execution, "_verify_a3l7_material_still_bound",
            ), self.assertRaisesRegex(
                execution.ExecutionError, "output parent traversal"
            ):
                execution._execute_a3l8_campaign_with_seams(
                    a3l7_root=a3l7_root,
                    repo_root=repository,
                    protected_file=protected,
                    output_parent=output_parent,
                    runner=forbidden_runner,
                    spanning_executor=forbidden_runner,
                    repository_runner=forbidden_repository,
                    rename_callable=None,
                    clock=StepClock(),
                    identity_verifier=lambda _path, _digest: None,
                    source_binding_verifier=lambda _root: fake_evidence,
                    repository_boundary_verifier=lambda *_values: None,
                )
            self.assertEqual(runner_calls, [])
            self.assertEqual(repository_calls, [])
            self.assertFalse((target / "candidate-parent").exists())

    def test_cli_refuses_runtime_without_a3l7_material(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            status = execution.main(["run-v1"])
        self.assertEqual(status, 2)
        self.assertIn("A3L7", stderr.getvalue())

    def test_module_import_performs_no_docker_or_network_action(self) -> None:
        source = Path(execution.__file__).read_text(encoding="utf-8")
        self.assertNotIn("shell=True", source)
        self.assertNotIn("import socket", source)
        self.assertNotIn("docker.from_env", source)

    def test_a3l9_session_launch_acceptance_and_cli_surfaces_are_session_scoped(
        self,
    ) -> None:
        challenge = bytes(range(32))
        session = execution.build_review_session(
            challenge=challenge,
            candidate_manifest_sha256=HEX_A,
            candidate_decision_sha256=HEX_B,
            decision_file_identity={
                "device": 1, "inode": 2, "mode": 0o600,
                "uid": 3, "gid": 4, "link_count": 1,
            },
            decision_file_sha256=HEX_C,
            created_monotonic_ns=10,
        )
        self.assertEqual(session["candidate_decision_sha256"], HEX_B)
        self.assertEqual(session["decision_file_sha256"], HEX_C)
        paths = execution.review_session_paths(
            Path("/artifacts/reviews"), HEX_A, session["session_id"]
        )
        self.assertIn("/%s/%s/" % (HEX_A, session["session_id"]), paths["review_aggregate"])
        launch = execution.build_review_launch(
            review_session_sha256=HEX_A,
            review_session_durability_sha256=HEX_B,
            claim_boundary_sha256=HEX_C,
            role="security-capability",
            reviewer_id="reviewer-one",
            command_observation={"outcome": "completed"},
            receipt_path=paths["security-capability_receipt"],
            receipt_raw=b"{}",
            receipt_domain_sha256=HEX_A,
            review_path=paths["security-capability_review"],
            review_raw=b"{}",
            review_domain_sha256=HEX_B,
        )
        self.assertEqual(launch["role"], "security-capability")
        rows = [{"class_id": name, "closed": True} for name in execution.CLASS_ORDER]
        acceptance = execution.build_acceptance_record_v2(
            review_session_sha256=HEX_A,
            review_session_durability_sha256=HEX_B,
            candidate_manifest_sha256=HEX_C,
            candidate_decision_sha256=HEX_A,
            review_aggregate_sha256=HEX_B,
            expected_bindings_sha256=HEX_C,
            claim_boundary_sha256=HEX_A,
            repository_state_sha256=HEX_B,
            publication_record_sha256=HEX_C,
            ordered_review_launch_sha256=(HEX_A, HEX_B),
            reconstructed_class_results=rows,
        )
        self.assertEqual(acceptance["correspondence_score"], "10/10")
        self.assertEqual(acceptance["closed_classes"], list(execution.CLASS_ORDER))
        self.assertEqual(
            execution.REVIEWED_PATHS,
            (
                "tools/hsai-formal-preflight/p01b_container_probe.py",
                "tools/hsai-formal-preflight/p01b_container_evidence.py",
                "tools/hsai-formal-preflight/p01b_container_execution.py",
                "tools/hsai-formal-preflight/p01b_container_evidence_tests.py",
                "tools/hsai-formal-preflight/p01b_container_execution_tests.py",
            ),
        )
        self.assertEqual(
            execution.A3L9_ENVIRONMENT,
            {
                "HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C",
                "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
            },
        )
        session_id = HEX_A
        execution._a3l9_validate_review_tree((), (session_id,))
        execution._a3l9_validate_review_tree(
            (session_id + "/review-session.json",), (session_id,)
        )
        role = execution.REVIEW_ROLE_ORDER[0]
        execution._a3l9_validate_review_tree(
            (
                session_id + "/review-session.json",
                session_id + "/review-session-durability.json",
                session_id + "/" + role
                + "/fresh-validation-receipt.json",
            ),
            (session_id, session_id + "/" + role),
        )
        with self.assertRaises(execution.ExecutionError):
            execution._a3l9_validate_review_tree(
                (session_id + "/junk.json",), (session_id,)
            )
        with self.assertRaisesRegex(
            execution.ExecutionError, "role dependency"
        ):
            execution._a3l9_validate_review_tree(
                (
                    session_id + "/review-session.json",
                    session_id + "/review-session-durability.json",
                    session_id + "/" + role + "/review.json",
                ),
                (session_id, session_id + "/" + role),
            )
        complete_files = [
            session_id + "/review-session.json",
            session_id + "/review-session-durability.json",
        ]
        complete_directories = [session_id]
        for complete_role in execution.REVIEW_ROLE_ORDER:
            base = session_id + "/" + complete_role
            complete_directories.append(base)
            complete_files.extend((
                base + "/fresh-validation-receipt.json",
                base + "/review.json",
                base + "/review-launch.json",
            ))
        complete_files.extend((
            session_id + "/review-aggregate.json",
            session_id + "/acceptance-record.json",
        ))
        execution._a3l9_validate_review_tree(
            complete_files, complete_directories
        )
        decision = {"decision": "accept"}
        common = mock.Mock()
        common.evidence.decision_digest.side_effect = lambda value: hashlib.sha256(
            execution.canonical_json_bytes(value)
        ).hexdigest()
        creates: list[str] = []
        with mock.patch.object(
            execution, "_a3l9_external_path_exists", return_value=True
        ), mock.patch.object(
            execution, "_a3l9_read_object_path",
            return_value=(decision, execution.canonical_json_bytes(decision), {}),
        ), mock.patch.object(
            execution, "_a3l9_reconstruct_decision", return_value=decision
        ):
            execution._a3l9_ensure_retry_decision(
                common, "/decision", GIT_A,
                lambda: creates.append("created"),
            )
        self.assertEqual(creates, [])
        with mock.patch.object(
            execution, "_a3l9_external_path_exists", return_value=True
        ), mock.patch.object(
            execution, "_a3l9_read_object_path",
            return_value=(decision, execution.canonical_json_bytes(decision), {}),
        ), mock.patch.object(
            execution, "_a3l9_reconstruct_decision",
            return_value={"decision": "reject"},
        ), self.assertRaisesRegex(
            execution.ExecutionError, "retained decision"
        ):
            execution._a3l9_ensure_retry_decision(
                common, "/decision", GIT_A,
                lambda: creates.append("created"),
            )
        invalid = [
            "decide-v3", "--publication-record", "/publication",
            "--candidate-root", "/candidate",
            "--collector-logical-path", "/collector",
            "--repository-state", "/repository",
            "--expected-bindings", "/bindings",
            "--implementation-commit", GIT_A,
            "--decision-output", "/decision",
        ]
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            status = execution.main(invalid)
        self.assertEqual(status, 2)
        self.assertIn("argv order", stderr.getvalue())
        parser = execution.build_parser()
        self.assertTrue(
            {"decide-v3", "review-v2", "aggregate-v2", "accept-v2"}.issubset(
                parser._subparsers._group_actions[0].choices
            )
        )

    def test_docker_context_companion_accepts_pinned_noncanonical_raw(
        self,
    ) -> None:
        fixture_path = Path(__file__).with_name("p01b_container_evidence_tests.py")
        spec = importlib.util.spec_from_file_location(
            "p01b_docker_context_fixtures", fixture_path
        )
        if spec is None or spec.loader is None:
            raise AssertionError("evidence fixture module is unavailable")
        fixtures = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixtures)
        pinned_raw = fixtures.PINNED_DOCKER_CONTEXT_RAW
        pinned_digest = evidence.sha256_hex(pinned_raw)

        def docker_context_descriptor(raw: bytes) -> dict:
            size = len(raw)
            digest = evidence.sha256_hex(raw)
            return {
                "schema": evidence.SCHEMAS["descriptor_observation"],
                "role": "docker-context",
                "path": execution.DOCKER_CONTEXT_PATH,
                "relative_path": None,
                "before": {
                    "device": 1,
                    "inode": 2,
                    "mode": 0o600,
                    "uid": 501,
                    "gid": 20,
                    "link_count": 1,
                    "size": size,
                    "mtime_ns": 3,
                    "ctime_ns": 4,
                },
                "after": {
                    "device": 1,
                    "inode": 2,
                    "mode": 0o600,
                    "uid": 501,
                    "gid": 20,
                    "link_count": 1,
                    "size": size,
                    "mtime_ns": 3,
                    "ctime_ns": 4,
                },
                "sha256": digest,
            }

        companion = execution._context_companion(
            docker_context_descriptor(pinned_raw),
            pinned_raw,
        )
        self.assertEqual(companion["schema"], "hsai-p01b-docker-context-v1")
        self.assertEqual(companion["name"], "desktop-linux")
        self.assertEqual(companion["host"], fixtures.PINNED_DOCKER_CONTEXT_HOST)
        self.assertEqual(companion["sha256"], pinned_digest)
        self.assertEqual(companion["bytes"], len(pinned_raw))
        # Docker Desktop owns meta.json field order; companion must accept the
        # pinned raw bytes even though they are not repository-canonical JSON.
        self.assertNotEqual(
            pinned_raw,
            execution.canonical_json_bytes(json.loads(pinned_raw.decode("utf-8"))),
        )
        old_context = execution.canonical_json_bytes({
            "Name": "desktop-linux",
            "Metadata": {"Host": "unix:///old", "SkipTLSVerify": False},
        })
        with self.assertRaisesRegex(execution.ExecutionError, "shape changed"):
            execution._context_companion(
                docker_context_descriptor(old_context),
                old_context,
            )


if __name__ == "__main__":
    unittest.main()
