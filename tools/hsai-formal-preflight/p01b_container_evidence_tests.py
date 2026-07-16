"""Exactly 32 hermetic A3L5C evidence-contract tests.

State slice: phase-796a3l6-hsai-p01b-execution-evidence-implementation.
No test invokes a runtime, filesystem mutation, subprocess, socket, or network.
"""

import base64
import copy
import hashlib
import json
import plistlib
import unittest

import p01b_container_evidence as evidence
import p01b_container_execution as execution


SHA = "11" * 32
SHA_B = "22" * 32
SHA_C = "33" * 32
COMMIT = "a" * 40
TREE = "b" * 40
PINNED_DOCKER_CONTEXT_HOST = "unix:///Users/shaanp/.docker/run/docker.sock"
PINNED_DOCKER_CONTEXT_RAW = (
    b'{"Name":"desktop-linux","Metadata":{"Description":"Docker Desktop",'
    b'"GODEBUG":"x509negativeserial=1","otel":{"OTEL_EXPORTER_OTLP_ENDPOINT":'
    b'"unix:///Users/shaanp/.docker/run/user-analytics.otlp.grpc.sock"}},'
    b'"Endpoints":{"docker":{"Host":"unix:///Users/shaanp/.docker/run/docker.sock",'
    b'"SkipTLSVerify":false}}}'
)


def sized_canonical_json(schema: str, total_bytes: int) -> tuple:
    value = {"padding": "", "schema": schema}
    empty = json.dumps(
        value, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"), sort_keys=True,
    ).encode("ascii")
    value["padding"] = "x" * (total_bytes - len(empty))
    raw = json.dumps(
        value, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"), sort_keys=True,
    ).encode("ascii")
    if len(raw) != total_bytes:
        raise AssertionError("sized canonical JSON construction drift")
    return value, raw


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def identity(size: int = 1) -> dict:
    return {
        "device": 1,
        "inode": 2,
        "mode": 0o600,
        "uid": 501,
        "gid": 20,
        "link_count": 1,
        "size": size,
        "mtime_ns": 3,
        "ctime_ns": 4,
    }


def publication_identity(inode: int = 2, mode: int = 0o700) -> dict:
    return {
        "device": 1,
        "inode": inode,
        "mode": mode,
        "uid": 501,
        "gid": 20,
        "link_count": 1,
    }


def descriptor(role: str = "host-tool", path: str = "/usr/bin/tool", relative=None) -> dict:
    return {
        "schema": evidence.SCHEMAS["descriptor_observation"],
        "role": role,
        "path": path,
        "relative_path": relative,
        "before": identity(),
        "after": identity(),
        "sha256": SHA,
    }


def claim_boundary() -> dict:
    return {
        "schema": evidence.SCHEMAS["claim_boundary"],
        "evidence_level": evidence.EVIDENCE_LEVEL,
        "ordered_honesty_assumptions": list(evidence.HONESTY_ASSUMPTIONS),
        "ordered_nonclaims": list(evidence.NONCLAIMS),
    }


def expected_bindings() -> dict:
    value = {name: "x" for name in evidence.EXPECTED_BINDING_FIELDS}
    value.update(
        {
            "schema": evidence.SCHEMAS["expected_bindings"],
            "predecessor_commit": COMMIT,
            "implementation_commit": COMMIT,
            "implementation_tree": TREE,
            "a3l6_audit_commit": COMMIT,
            "claim_boundary": claim_boundary(),
            "expected_focused_test_count": 64,
            "normal_expected_test_count": 151,
            "discovery_expected_test_count": 172,
            "candidate_payload_count": 200,
            "attempt_deadline_ns": 1_800_000_000_000,
            "class_order": list(evidence.CLASS_ORDER),
            "evidence_level": evidence.EVIDENCE_LEVEL,
            "native_python_path": "/usr/bin/python3",
            "native_python_sha256": evidence.NATIVE_PYTHON_SHA256,
            "native_python_version": "3.9.6",
            "normal_python_path": "/usr/local/bin/python3",
            "normal_python_version": "3.11.15",
            "normal_interpreter_policy": "probe-observed-ordered-chain-under-probe-honesty",
            "selected_platform": {"os": "linux", "architecture": "arm64", "variant": "v8"},
            "rootfs_diff_ids": list(evidence.ROOTFS_DIFF_IDS),
            "selected_descriptor_size": 1,
            "platform_manifest_size": 1,
            "image_config_digest": evidence.IMAGE_CONFIG_DIGEST,
            "index_reference": evidence.INDEX_REFERENCE,
            "protected_path": "/private/tmp/p01b-protected",
            "sandbox_exec_path": "/usr/bin/sandbox-exec",
            "docker_path": evidence.DOCKER_PATH,
            "buildx_path": evidence.BUILDX_PATH,
            "codesign_path": evidence.CODESIGN_PATH,
            "docker_desktop_info_plist_path": evidence.DOCKER_DESKTOP_INFO_PLIST_PATH,
            "docker_desktop_vm_path": evidence.DOCKER_DESKTOP_VM_PATH,
            "docker_desktop_kernel_path": evidence.DOCKER_DESKTOP_KERNEL_PATH,
            "docker_context_path": "/Users/test/.docker/contexts/meta.json",
            "selected_descriptor_digest": "sha256:" + SHA,
            "selected_descriptor_media_type": "application/vnd.oci.image.manifest.v1+json",
            "platform_reference": "docker.io/library/python@sha256:" + SHA,
            "platform_manifest_media_type": "application/vnd.oci.image.manifest.v1+json",
        }
    )
    for name in evidence.EXPECTED_BINDING_FIELDS:
        if name.endswith("_sha256"):
            value[name] = SHA
    value["claim_boundary_sha256"] = evidence.claim_boundary_digest(value["claim_boundary"])
    value["native_python_sha256"] = evidence.NATIVE_PYTHON_SHA256
    value["sandbox_exec_sha256"] = evidence.SANDBOX_EXEC_SHA256
    value["docker_sha256"] = evidence.DOCKER_SHA256
    value["buildx_sha256"] = evidence.BUILDX_SHA256
    value["codesign_sha256"] = evidence.CODESIGN_SHA256
    value["docker_desktop_vm_sha256"] = evidence.DOCKER_DESKTOP_VM_SHA256
    value["docker_desktop_kernel_sha256"] = evidence.DOCKER_DESKTOP_KERNEL_SHA256
    value["docker_context_sha256"] = evidence.DOCKER_CONTEXT_SHA256
    value["index_manifest_sha256"] = evidence.INDEX_REFERENCE.rsplit(":", 1)[1]
    value["platform_manifest_sha256"] = SHA
    value["snapshot_source_manifest_sha256"] = SHA
    value["snapshot_copy_manifest_sha256"] = SHA_B
    return value


def candidate() -> tuple:
    bindings = expected_bindings()
    files = {}
    for path in evidence.CANDIDATE_PAYLOAD_PATHS:
        files[path] = b"{}" if path.endswith(".json") else b"x"
    files["authority/expected-bindings.json"] = evidence.canonical_json_bytes(bindings)
    entries = [
        {
            "path": path,
            "file_type": "regular",
            "mode": 0o600,
            "link_count": 1,
            "bytes": len(files[path]),
            "sha256": evidence.sha256_hex(files[path]),
        }
        for path in evidence.CANDIDATE_PAYLOAD_PATHS
    ]
    manifest = {
        "schema": evidence.SCHEMAS["manifest"],
        "authorization_sha256": SHA,
        "implementation_commit": COMMIT,
        "entries": entries,
    }
    return files, manifest, bindings


def publication(manifest: dict, repository_digest: str) -> dict:
    manifest_raw = evidence.canonical_json_bytes(manifest)
    rows = []
    all_files = list(zip(evidence.CANDIDATE_PAYLOAD_PATHS, manifest["entries"]))
    all_files.append(
        (
            "candidate-manifest.json",
            {"bytes": len(manifest_raw), "sha256": evidence.sha256_hex(manifest_raw)},
        )
    )
    for ordinal, (path, entry) in enumerate(sorted(all_files)):
        observed = {
            "identity": publication_identity(1000 + ordinal, 0o600),
            "bytes": entry["bytes"],
            "sha256": entry["sha256"],
        }
        rows.append({"path": path, "prepublication": observed, "postpublication": copy.deepcopy(observed)})
    inventory = [
        {"path": row["path"], **row["prepublication"]}
        for row in rows
    ]
    inventory_digest = evidence.domain_sha256(evidence.DOMAINS["publication_inventory"], inventory)
    operations = ["payload-file-fsync"] * 200
    operations += ["candidate-manifest-fsync"] + ["candidate-directory-fsync"] * 62
    operations += [
        "prepublication-inventory",
        "renameatx-np",
        "final-parent-fsync",
        "staging-absence",
        "final-root-reopen",
        "postpublication-inventory",
        "final-manifest-read",
    ]
    events = []
    for ordinal, operation in enumerate(operations):
        events.append(
            {
                "ordinal": ordinal,
                "operation": operation,
                "target": ".",
                "flags": [],
                "started_monotonic_ns": ordinal * 2 + 1,
                "ended_monotonic_ns": ordinal * 2 + 2,
                "result": 0,
                "errno": 0,
                "identity": None,
                "sha256": None,
            }
        )
    events[264]["target"] = {"source": ".p01b-staging-campaign", "destination": "p01b-candidate-campaign"}
    events[264]["flags"] = ["RENAME_EXCL"]
    events[265]["target"] = "/private/tmp/p01b"
    events[265]["identity"] = publication_identity(7)
    events[266]["target"] = ".p01b-staging-campaign"
    events[266]["result"] = -1
    events[266]["errno"] = 2
    by_path = {row["path"]: row for row in rows}
    for event, entry in zip(events[:200], manifest["entries"]):
        event["target"] = entry["path"]
        event["identity"] = by_path[entry["path"]]["prepublication"]["identity"]
        event["sha256"] = entry["sha256"]
    events[200]["target"] = "candidate-manifest.json"
    events[200]["identity"] = by_path["candidate-manifest.json"]["prepublication"]["identity"]
    events[200]["sha256"] = evidence.sha256_hex(manifest_raw)
    for event, target in zip(events[201:263], evidence._candidate_directory_order()):
        event["target"] = target
        event["identity"] = publication_identity(3000 + event["ordinal"])
    events[262]["identity"] = publication_identity(8)
    events[263]["identity"] = publication_identity(8)
    events[263]["sha256"] = inventory_digest
    events[267]["target"] = "p01b-candidate-campaign"
    events[267]["identity"] = publication_identity(8)
    events[268]["identity"] = publication_identity(8)
    events[268]["sha256"] = inventory_digest
    events[269]["target"] = "candidate-manifest.json"
    events[269]["identity"] = by_path["candidate-manifest.json"]["postpublication"]["identity"]
    events[269]["sha256"] = evidence.manifest_digest(manifest)
    return {
        "schema": evidence.SCHEMAS["publication"],
        "candidate_manifest_sha256": evidence.manifest_digest(manifest),
        "repository_state_sha256": repository_digest,
        "staging_path": "/private/tmp/p01b/.p01b-staging-campaign",
        "final_path": "/private/tmp/p01b/p01b-candidate-campaign",
        "parent_identity": publication_identity(7),
        "prepublication_inventory_sha256": inventory_digest,
        "postpublication_inventory_sha256": inventory_digest,
        "staging_identity": publication_identity(8),
        "final_identity": publication_identity(8),
        "ordered_file_reopens": rows,
        "ordered_publication_events": events,
        "final_manifest_sha256": evidence.manifest_digest(manifest),
    }


def repository_command(role: str, argv: list, stdout: bytes, start: int) -> dict:
    return {
        "role": role,
        "argv": argv,
        "environment": {"PATH": "/usr/bin:/bin"},
        "cwd": "/repo",
        "stdin_policy": "closed",
        "executable_path": "/usr/bin/git",
        "executable_sha256": SHA,
        "timeout_ns": 60_000_000_000,
        "stdout_cap_bytes": 1_048_576,
        "stderr_cap_bytes": 16_384,
        "started_monotonic_ns": start,
        "ended_monotonic_ns": start + 1,
        "outcome": "completed",
        "exit_code": 0,
        "signal": None,
        "stdout_total_bytes": len(stdout),
        "stdout_retained_bytes": len(stdout),
        "stdout_truncated": False,
        "stdout_base64": b64(stdout),
        "stdout_sha256": evidence.sha256_hex(stdout),
        "stderr_total_bytes": 0,
        "stderr_retained_bytes": 0,
        "stderr_truncated": False,
        "stderr_base64": b64(b""),
        "stderr_sha256": evidence.EMPTY_SHA256,
    }


def repository_state() -> dict:
    argvs = [
        ["/usr/bin/git", "rev-parse", "HEAD"],
        ["/usr/bin/git", "rev-parse", "HEAD^{tree}"],
        ["/usr/bin/git", "status", "--porcelain=v2", "-z", "--untracked-files=all"],
    ]
    outputs = ((COMMIT + "\n").encode(), (TREE + "\n").encode(), b"1 .M N... dirty\0")
    before = {
        "schema": evidence.SCHEMAS["repository_capture"],
        "ordered_commands": [
            repository_command(role, argv, stdout, 1 + index * 2)
            for index, (role, argv, stdout) in enumerate(
                zip(("head", "tree", "status"), argvs, outputs)
            )
        ],
        "protected_observation": descriptor("protected", "/repo/AGENTS.md"),
    }
    after = copy.deepcopy(before)
    for index, command in enumerate(after["ordered_commands"]):
        command["started_monotonic_ns"] = 10 + index * 2
        command["ended_monotonic_ns"] = 11 + index * 2
    return {
        "schema": evidence.SCHEMAS["repository_state"],
        "plan": {
            "schema": evidence.SCHEMAS["repository_state_plan"],
            "git_path": "/usr/bin/git",
            "git_sha256": SHA,
            "protected_path": "/repo/AGENTS.md",
            "environment": {"PATH": "/usr/bin:/bin"},
            "cwd": "/repo",
            "stdin_policy": "closed",
            "commands": [{"argv": argv} for argv in argvs],
        },
        "implementation_commit": COMMIT,
        "implementation_tree": TREE,
        "before": before,
        "after": after,
        "unchanged": True,
    }


def readiness_command(ordinal: int, role: str, argv: list, activation: str) -> dict:
    return {
        "ordinal": ordinal,
        "role": role,
        "argv": argv,
        "environment": {"HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "TMPDIR": "/private/tmp/p01b-readiness", "TZ": "UTC", "DOCKER_CONFIG": "/private/tmp/p01b-docker-config"},
        "cwd": "/",
        "stdin_policy": "closed-null",
        "stdout_cap": 262_144,
        "stderr_cap": 262_144,
        "timeout_ns": 1_800_000_000_000,
        "activation": activation,
        "expected_outcomes": ["exit_zero"],
    }


def readiness_plan(user_authorization_sha256: str = SHA) -> dict:
    prefix = [evidence.DOCKER_PATH, "--config", "/private/tmp/p01b-docker-config", "--host", "unix:///var/run/docker.sock", "--log-level", "error"]
    commands = (
        ("registry-index", [evidence.BUILDX_PATH, "imagetools", "inspect", "--raw", evidence.INDEX_REFERENCE], "always"),
        ("registry-platform", [evidence.BUILDX_PATH, "imagetools", "inspect", "--raw", evidence.PLATFORM_PLACEHOLDER], "after_index"),
        ("local-platform", prefix + ["image", "inspect", "--format={{json .}}", evidence.PLATFORM_PLACEHOLDER], "after_platform"),
        ("buildx-version", [evidence.BUILDX_PATH, "version"], "after_platform"),
        ("codesign-verify", [evidence.CODESIGN_PATH, "--verify", "--strict", "--verbose=4", "/Applications/Docker.app"], "after_platform"),
        ("codesign-display", [evidence.CODESIGN_PATH, "--display", "--verbose=4", "/Applications/Docker.app"], "after_platform"),
    )
    return {
        "schema": evidence.SCHEMAS["readiness_plan"],
        "predecessor_commit": COMMIT,
        "user_authorization_sha256": user_authorization_sha256,
        "index_reference": evidence.INDEX_REFERENCE,
        "docker_path": evidence.DOCKER_PATH,
        "docker_sha256": evidence.DOCKER_SHA256,
        "buildx_path": evidence.BUILDX_PATH,
        "buildx_sha256": evidence.BUILDX_SHA256,
        "codesign_path": evidence.CODESIGN_PATH,
        "codesign_sha256": evidence.CODESIGN_SHA256,
        "commands": [readiness_command(i, role, argv, activation) for i, (role, argv, activation) in enumerate(commands)],
        "selected_reference_rule": {"repository": "docker.io/library/python", "os": "linux", "architecture": "arm64", "variant": "v8", "count": 1},
    }


def readiness_result(accepted: bool = False) -> dict:
    unavailable = evidence.UNAVAILABLE_SHA256
    digest = SHA if accepted else unavailable
    descriptor_value = {"digest": "sha256:" + digest, "mediaType": "application/vnd.oci.image.manifest.v1+json", "size": 1, "os": "linux", "architecture": "arm64", "variant": "v8"}
    return {
        "schema": evidence.SCHEMAS["readiness_result"],
        "readiness_plan_sha256": SHA,
        "ordered_observation_sha256": [SHA] * 6,
        "index_sha256": evidence.INDEX_REFERENCE.rsplit(":", 1)[1] if accepted else unavailable,
        "selected_descriptor": descriptor_value,
        "selected_reference": "docker.io/library/python@" + descriptor_value["digest"],
        "platform_sha256": SHA if accepted else unavailable,
        "local_image_observation_sha256": SHA,
        "buildx_version_observation_sha256": SHA,
        "codesign_verify_observation_sha256": SHA,
        "codesign_display_observation_sha256": SHA,
        "ordered_descriptor_set_sha256": [SHA, SHA_B],
        "context_sha256": SHA if accepted else unavailable,
        "image_config_digest": evidence.IMAGE_CONFIG_DIGEST if accepted else "sha256:" + unavailable,
        "rootfs_diff_ids": list(evidence.ROOTFS_DIFF_IDS) if accepted else [],
        "accepted": accepted,
        "failure": None if accepted else "registry_failed",
    }


def inspect_pair(state: str) -> tuple:
    expected = {name: None for name in evidence.INSPECT_FIELDS}
    endpoint = {
        "IPAMConfig": None, "Links": None, "Aliases": None, "MacAddress": "",
        "DriverOpts": None, "GwPriority": 0, "NetworkID": "" if state == "prestart" else SHA,
        "EndpointID": "", "Gateway": "", "IPAddress": "", "IPPrefixLen": 0,
        "IPv6Gateway": "", "GlobalIPv6Address": "", "GlobalIPv6PrefixLen": 0,
        "DNSNames": None,
    }
    expected["NetworkSettings.Networks"] = {"none": endpoint}
    if state == "prestart":
        values = ("created", False, 0, False, "", 0, "0001-01-01T00:00:00Z", "0001-01-01T00:00:00Z")
    else:
        values = ("exited", False, 0, False, "", 0, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z")
    for name, item in zip(("State.Status", "State.Running", "State.ExitCode", "State.OOMKilled", "State.Error", "State.Pid", "State.StartedAt", "State.FinishedAt"), values):
        expected[name] = item
    nested = {}
    for dotted, item in expected.items():
        current = nested
        parts = dotted.split(".")
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = item
    return nested, expected


def cgroup_snapshot(phase: str, pids: list, oom: int = 0, oom_kill: int = 0, observed: int = 10) -> dict:
    rows = {
        "cgroup.procs": "".join(str(pid) + "\n" for pid in pids).encode(),
        "cgroup.events": b"populated 1\nfrozen 0\n",
        "memory.current": b"1048576\n", "memory.max": b"536870912\n",
        "memory.swap.current": b"0\n", "memory.peak": b"2097152\n",
        "memory.min": b"0\n", "memory.low": b"0\n", "memory.high": b"max\n",
        "memory.swap.max": b"0\n", "memory.swap.events": b"high 0\nmax 0\nfail 0\n",
        "memory.oom.group": b"0\n",
        "memory.events": "low 0\nhigh 0\nmax 0\noom {}\noom_kill {}\noom_group_kill 0\n".format(oom, oom_kill).encode(),
        "memory.events.local": "low 0\nhigh 0\nmax 0\noom {}\noom_kill {}\noom_group_kill 0\n".format(oom, oom_kill).encode(),
        "pids.current": (str(len(pids)) + "\n").encode(), "pids.max": b"16\n", "pids.events": b"max 0\n",
        "cpu.max": b"100000 100000\n",
        "cpu.stat": b"usage_usec 10\nuser_usec 5\nsystem_usec 5\nnr_periods 1\nnr_throttled 0\nthrottled_usec 0\n",
    }
    normalized = {}
    for name, raw in rows.items():
        if name == "cgroup.procs": normalized[name] = pids
        elif name == "cpu.max": normalized[name] = [100000, 100000]
        elif name in evidence._KV_CGROUP: normalized[name] = evidence._parse_kv(raw)
        else: normalized[name] = evidence._parse_scalar(raw, allow_max=name in evidence._MAX_CGROUP)
    return {"phase": phase, "path": "/docker/test", "observed_monotonic_ns": observed, "files": normalized, "raw_files_base64": {name: b64(raw) for name, raw in rows.items()}}


def security(pid: int) -> dict:
    status = b"Uid:\t65532\t65532\t65532\t65532\nGid:\t65532\t65532\t65532\t65532\nNoNewPrivs:\t1\nSeccomp:\t2\nSeccomp_filters:\t1\nCapInh:\t0000000000000000\nCapPrm:\t0000000000000000\nCapEff:\t0000000000000000\nCapBnd:\t0000000000000000\nCapAmb:\t0000000000000000\n"
    namespaces = {name: "{}:[{}]".format(name, 100 + index) for index, name in enumerate(("pid", "uts", "mnt", "net", "ipc", "cgroup", "user"))}
    return {"pid": pid, "uid": 65532, "gid": 65532, "uid_map_base64": b64(b"         0          0 4294967295\n"), "gid_map_base64": b64(b"         0          0 4294967295\n"), "status_base64": b64(status), "attr_current_base64": b64(b"docker-default (enforce)\n"), "namespaces": namespaces, "oom_score_adj": 0, "cgroup_base64": b64(b"0::/docker/test\n"), "oom_score_adj_base64": b64(b"0\n")}


def semantic_inspect(state: str, seccomp_raw: bytes, cid: str, name: str, labels: dict) -> dict:
    _, expected = inspect_pair(state)
    expected.update({
        "Id": cid, "Name": "/" + name, "Path": "/usr/local/bin/python3", "Args": ["/input/probe.py"],
        "Platform": "linux", "AppArmorProfile": "docker-default", "Config.Image": "python@sha256:" + SHA,
        "Config.User": "65532:65532", "Config.Entrypoint": None, "Config.Cmd": ["/input/probe.py"],
        "Config.Env": ["LANG=C"], "Config.WorkingDir": "/work", "Config.Hostname": "p01b",
        "Config.Healthcheck": {"Test": ["NONE"]}, "Config.OpenStdin": False, "Config.Tty": False, "Config.Labels": labels,
        "HostConfig.Runtime": "runc", "HostConfig.NetworkMode": "none", "HostConfig.IpcMode": "private",
        "HostConfig.PidMode": "", "HostConfig.UTSMode": "", "HostConfig.CgroupnsMode": "private",
        "HostConfig.CgroupParent": "", "HostConfig.UsernsMode": "", "HostConfig.ReadonlyRootfs": True,
        "HostConfig.Privileged": False, "HostConfig.CapAdd": None, "HostConfig.CapDrop": ["ALL"],
        "HostConfig.SecurityOpt": ["no-new-privileges:true", "seccomp=" + seccomp_raw.decode("ascii")],
        "HostConfig.Memory": 536870912, "HostConfig.MemorySwap": 536870912, "HostConfig.MemorySwappiness": 0,
        "HostConfig.OomKillDisable": False, "HostConfig.PidsLimit": 16, "HostConfig.CpuPeriod": 100000,
        "HostConfig.CpuQuota": 100000, "HostConfig.Ulimits": [], "HostConfig.Tmpfs": {"/work": "rw,nosuid,nodev,noexec,size=16777216,mode=0700,uid=65532,gid=65532"},
        "HostConfig.ShmSize": 1048576, "HostConfig.LogConfig": {"Type": "none", "Config": {}},
        "HostConfig.RestartPolicy": {"Name": "no", "MaximumRetryCount": 0}, "HostConfig.AutoRemove": False,
        "HostConfig.Devices": [], "HostConfig.DeviceRequests": None, "HostConfig.GroupAdd": None,
        "Mounts": [{"Type": "bind", "Source": "/snapshot", "Destination": "/input", "Mode": "ro", "RW": False, "Propagation": "rprivate"}],
    })
    nested = {}
    for dotted, value in expected.items():
        current = nested
        parts = dotted.split(".")
        for part in parts[:-1]: current = current.setdefault(part, {})
        current[parts[-1]] = value
    return nested


def semantic_c04_c05_fixture() -> tuple:
    seccomp_raw = evidence.canonical_json_bytes({"defaultAction": "SCMP_ACT_ERRNO", "syscalls": []})
    labels = {"hsai.p01b.attempt": "normal", "hsai.p01b.authorization": SHA, "hsai.p01b.campaign": "campaign", "hsai.p01b.commit": COMMIT}
    normal_security = security(100)
    oom_security = security(200)
    process_common = {"cgroup_path": "/docker/test", "ready": True, "namespaces": oom_security["namespaces"], "cgroup_base64": b64(b"0::/docker/test\n")}
    normal = {"schema": evidence.SCHEMAS["probe_result"], "security": normal_security, "cgroup_pre": cgroup_snapshot("pre", [100], observed=10), "cgroup_terminal": cgroup_snapshot("terminal", [100], observed=20)}
    oom = {"schema": evidence.SCHEMAS["probe_result"], "security": oom_security, "cgroup_pre": cgroup_snapshot("pre", [200, 201], observed=30), "cgroup_terminal": cgroup_snapshot("terminal", [200], oom=1, oom_kill=1, observed=40), "parent": {"pid": 200, "oom_score_adj": 0, "wait_signal": None, "survived": True, "oom_score_adj_base64": b64(b"0\n"), **process_common}, "child": {"pid": 201, "oom_score_adj": 1000, "wait_signal": 9, "survived": False, "oom_score_adj_base64": b64(b"1000\n"), **process_common}, "workload": {"local_event_deltas": {"oom": 1, "oom_kill": 1, "oom_group_kill": 0}}}
    files = {"attempts/normal/result.json": evidence.canonical_json_bytes(normal), "attempts/oom/result.json": evidence.canonical_json_bytes(oom), "snapshot/files/tools/hsai-formal-preflight/p01b_container_seccomp.json": seccomp_raw}
    for attempt in ("normal", "oom"):
        attempt_labels = dict(labels); attempt_labels["hsai.p01b.attempt"] = attempt
        files["attempts/{}/inspect-prestart.json".format(attempt)] = evidence.canonical_json_bytes([semantic_inspect("prestart", seccomp_raw, SHA, "campaign-" + attempt, attempt_labels)])
        files["attempts/{}/inspect-terminal.json".format(attempt)] = evidence.canonical_json_bytes([semantic_inspect("terminal", seccomp_raw, SHA, "campaign-" + attempt, attempt_labels)])
    bindings = expected_bindings(); bindings["seccomp_sha256"] = evidence.sha256_hex(seccomp_raw)
    return files, bindings


def semantic_observation(namespace: str, basename: str, ordinal: int, stdout: bytes, stderr: bytes = b"") -> dict:
    base = "operations/{}/{}/".format(namespace, basename)
    return {
        "schema": evidence.SCHEMAS["observation"], "plan_sha256": SHA, "launch_ordinal": ordinal,
        "completion_ordinal": ordinal, "role": basename.split("-", 1)[1], "argv": ["/usr/bin/tool", basename],
        "environment": {"PATH": "/usr/bin:/bin"}, "cwd": "/", "stdin_policy": "closed-null",
        "executable_path": "/usr/bin/tool", "executable_sha256": SHA, "started_monotonic_ns": ordinal * 10 + 1,
        "ended_monotonic_ns": ordinal * 10 + 2, "duration_ns": 1, "outcome": "exit", "exit_code": 0,
        "signal": None, "stdout_path": base + "stdout.bin", "stdout_total_bytes": len(stdout),
        "stdout_retained_bytes": len(stdout), "stdout_raw_sha256": evidence.sha256_hex(stdout),
        "stdout_retained_sha256": evidence.sha256_hex(stdout), "stdout_cap": 262144, "stdout_truncated": False,
        "stderr_path": base + "stderr.bin", "stderr_total_bytes": len(stderr), "stderr_retained_bytes": len(stderr),
        "stderr_raw_sha256": evidence.sha256_hex(stderr), "stderr_retained_sha256": evidence.sha256_hex(stderr),
        "stderr_cap": 262144, "stderr_truncated": False, "container_id": None, "previous_observation_sha256": None,
    }


def descriptor_set(kind: str) -> dict:
    paths = [evidence.DOCKER_DESKTOP_INFO_PLIST_PATH, evidence.DOCKER_DESKTOP_VM_PATH, evidence.DOCKER_DESKTOP_KERNEL_PATH] if kind == "docker-desktop" else [evidence.CODESIGN_PATH, evidence.DOCKER_PATH, evidence.BUILDX_PATH]
    paths.sort()
    observations = [descriptor(kind, path) for path in paths]
    hashes = {
        evidence.CODESIGN_PATH: evidence.CODESIGN_SHA256,
        evidence.DOCKER_PATH: evidence.DOCKER_SHA256,
        evidence.BUILDX_PATH: evidence.BUILDX_SHA256,
        evidence.DOCKER_DESKTOP_INFO_PLIST_PATH: SHA,
        evidence.DOCKER_DESKTOP_VM_PATH: evidence.DOCKER_DESKTOP_VM_SHA256,
        evidence.DOCKER_DESKTOP_KERNEL_PATH: evidence.DOCKER_DESKTOP_KERNEL_SHA256,
    }
    for observation in observations:
        observation["sha256"] = hashes[observation["path"]]
    return {"schema": evidence.SCHEMAS["descriptor_set"], "kind": kind, "ordered_observations": observations}


def transcript_wrapper(kind: str, observation: dict, stdout: bytes, stderr: bytes, parsed: dict) -> dict:
    return {"schema": "hsai-p01b-transcript-binding-v1", "kind": kind, "observation_sha256": evidence.observation_digest(observation), "stdout_path": observation["stdout_path"], "stdout_bytes": len(stdout), "stdout_sha256": evidence.sha256_hex(stdout), "stderr_path": observation["stderr_path"], "stderr_bytes": len(stderr), "stderr_sha256": evidence.sha256_hex(stderr), "parsed": parsed}


def host_provenance(kind: str, observations: list, facts: dict, descriptors=None) -> dict:
    return {"schema": "hsai-p01b-host-provenance-v1", "kind": kind, "ordered_source_observation_sha256": [evidence.observation_digest(item) for item in observations], "descriptor_set_sha256": evidence.descriptor_set_digest(descriptors) if descriptors is not None else None, "descriptor_set": descriptors, "facts": facts, "assumptions": evidence._PROVENANCE_ASSUMPTIONS[kind]}


def semantic_c07_fixture(user_authorization_sha256: str = SHA) -> tuple:
    files = {}; bindings = expected_bindings()
    config_digest = evidence.IMAGE_CONFIG_DIGEST
    platform = {"schemaVersion": 2, "mediaType": "application/vnd.oci.image.manifest.v1+json", "config": {"mediaType": "application/vnd.oci.image.config.v1+json", "digest": config_digest, "size": 1}, "layers": [{"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip", "digest": "sha256:" + SHA_B, "size": 1}]}
    platform_raw = evidence.canonical_json_bytes(platform)
    platform_digest = evidence.sha256_hex(platform_raw)
    selected = {"digest": "sha256:" + platform_digest, "mediaType": platform["mediaType"], "size": len(platform_raw), "os": "linux", "architecture": "arm64", "variant": "v8"}
    index_descriptor = {"digest": selected["digest"], "mediaType": selected["mediaType"], "size": selected["size"], "platform": bindings["selected_platform"]}
    index = {"schemaVersion": 2, "manifests": [index_descriptor]}
    index_raw = evidence.canonical_json_bytes(index)
    retained_readiness_plan = readiness_plan(user_authorization_sha256)
    readiness_plan_sha = evidence.readiness_plan_digest(retained_readiness_plan)
    selected_reference = "docker.io/library/python@sha256:" + platform_digest
    local = {"Id": config_digest, "RepoDigests": ["docker.io/library/python@sha256:" + platform_digest], "Architecture": "arm64", "Os": "linux", "Variant": "v8", "RootFS": {"Type": "layers", "Layers": list(evidence.ROOTFS_DIFF_IDS)}}
    full = "44" * 32; short = full[:40]
    display_rows = [
        "Executable=/Applications/Docker.app/Contents/MacOS/Docker Desktop", "Identifier=com.docker.docker", "Format=Mach-O 64-bit executable arm64", "CodeDirectory v=20500 size=1 flags=0x0 hashes=1+0 location=embedded", "Hash type=sha256 size=32", "CandidateCDHash sha256=" + short, "CandidateCDHashFull sha256=" + full, "Hash choices=sha256", "CMSDigest=" + full, "CMSDigestType=2", "Executable Segment base=0", "Executable Segment limit=1", "Executable Segment flags=0x1", "Page size=4096", "CDHash=" + short, "Signature size=1", "Authority=Developer ID Application: Docker Inc (9BNSXJN65R)", "Authority=Developer ID Certification Authority", "Authority=Apple Root CA", "Timestamp=Jul 15, 2026 at 1:00:00 PM", "Notarization Ticket=stapled", "Info.plist entries=1", "TeamIdentifier=9BNSXJN65R", "Runtime Version=15.0.0", "Sealed Resources version=2 rules=1 files=1", "Internal requirements count=1 size=1",
    ]
    verify_path = "/Applications/Docker.app"
    display_path = "/Applications/Docker.app/Contents/MacOS/Docker Desktop"
    verify_stderr = (verify_path + ": valid on disk\n" + verify_path + ": satisfies its Designated Requirement\n").encode()
    display_stderr = ("\n".join(display_rows) + "\n").encode()
    streams = {
        ("readiness", "000-registry-index"): (index_raw, b""),
        ("readiness", "001-registry-platform"): (platform_raw, b""),
        ("readiness", "002-local-platform"): (evidence.canonical_json_bytes(local) + b"\n", b""),
        ("readiness", "003-buildx-version"): (b"github.com/docker/buildx v0.34.1-desktop.1 c79576280a671664e17eb68da98ec3136b614aed\n", b""),
        ("readiness", "004-codesign-verify"): (b"", verify_stderr),
        ("readiness", "005-codesign-display"): (b"", display_stderr),
        ("campaign", "000-native-reference"): (b"{}\n", b""),
        ("campaign", "001-docker-version"): (b'{"Client":{"ApiVersion":"1.52","Arch":"arm64","GoVersion":"go1.24","Os":"darwin","Version":"29.5.3"},"Server":{"ApiVersion":"1.52","Arch":"arm64","Os":"linux","Version":"29.5.3"}}\n', b""),
        ("campaign", "002-docker-info"): (b'{"Architecture":"aarch64","DockerRootDir":"/var/lib/docker","KernelVersion":"6.10","Name":"docker-desktop","OperatingSystem":"Docker Desktop","OSType":"linux"}\n', b""),
        ("campaign", "003-image-config"): (evidence.canonical_json_bytes(local) + b"\n", b""),
    }
    observations = {}
    for namespace in ("readiness", "campaign"):
        previous = None
        for ordinal, basename in enumerate(evidence._OPERATION_BASENAMES[namespace]):
            stdout, stderr = streams[(namespace, basename)]
            observation = semantic_observation(namespace, basename, ordinal, stdout, stderr)
            if namespace == "readiness":
                command = retained_readiness_plan["commands"][ordinal]
                observation["plan_sha256"] = readiness_plan_sha
                observation["argv"] = [
                    selected_reference if item == evidence.PLATFORM_PLACEHOLDER else item
                    for item in command["argv"]
                ]
                observation["environment"] = command["environment"]
                observation["cwd"] = command["cwd"]
                observation["stdin_policy"] = command["stdin_policy"]
                observation["stdout_cap"] = command["stdout_cap"]
                observation["stderr_cap"] = command["stderr_cap"]
                observation["executable_path"] = observation["argv"][0]
                observation["executable_sha256"] = {
                    evidence.BUILDX_PATH: evidence.BUILDX_SHA256,
                    evidence.DOCKER_PATH: evidence.DOCKER_SHA256,
                    evidence.CODESIGN_PATH: evidence.CODESIGN_SHA256,
                }[observation["executable_path"]]
                observation["previous_observation_sha256"] = previous
            observations[(namespace, basename)] = observation
            base = "operations/{}/{}/".format(namespace, basename)
            files[base + "observation.json"] = evidence.canonical_json_bytes(observation); files[base + "stdout.bin"] = stdout; files[base + "stderr.bin"] = stderr
            previous = evidence.observation_digest(observation)
    verify_parsed = {"prepared_paths": [], "validated_paths": [], "valid_on_disk": True, "satisfies_designated_requirement": True}
    display_parsed = {"ordered_rows": display_rows, "executable": display_path, "identifier": "com.docker.docker", "format": display_rows[2].split("=", 1)[1], "candidate_cdhash": short, "candidate_cdhash_full": full, "cms_digest": full, "cdhash": short, "authorities": [display_rows[index].split("=", 1)[1] for index in (16,17,18)], "team_identifier": "9BNSXJN65R", "runtime_version": "15.0.0"}
    for path, kind, key, parsed in (("provenance/registry/index.json", "registry-index", ("readiness", "000-registry-index"), index), ("provenance/registry/platform-manifest.json", "registry-platform", ("readiness", "001-registry-platform"), platform), ("provenance/signature/verify.json", "codesign-verify", ("readiness", "004-codesign-verify"), verify_parsed), ("provenance/signature/display.json", "codesign-display", ("readiness", "005-codesign-display"), display_parsed)):
        stdout, stderr = streams[key]; files[path] = evidence.canonical_json_bytes(transcript_wrapper(kind, observations[key], stdout, stderr, parsed))
    info_plist_raw = plistlib.dumps({"CFBundleIdentifier": "com.docker.docker", "CFBundleVersion": "1", "CFBundleShortVersionString": "1.0"}, fmt=plistlib.FMT_BINARY, sort_keys=True)
    host_set = descriptor_set("host-tools"); desktop_set = descriptor_set("docker-desktop")
    info_descriptor = next(item for item in desktop_set["ordered_observations"] if item["path"] == evidence.DOCKER_DESKTOP_INFO_PLIST_PATH)
    info_descriptor["before"]["size"] = info_descriptor["after"]["size"] = len(info_plist_raw)
    info_descriptor["sha256"] = evidence.sha256_hex(info_plist_raw)
    ro = lambda name: observations[("readiness", name)]; co = lambda name: observations[("campaign", name)]
    provenance = {
        "docker-desktop": host_provenance("docker-desktop", [ro("004-codesign-verify"), ro("005-codesign-display")], {"info_plist_sha256": evidence.sha256_hex(info_plist_raw), "bundle_version": "1", "short_version": "1.0", "vm_image_sha256": evidence.DOCKER_DESKTOP_VM_SHA256, "kernel_sha256": evidence.DOCKER_DESKTOP_KERNEL_SHA256, "codesign_verify_sha256": evidence.observation_digest(ro("004-codesign-verify")), "codesign_display_sha256": evidence.observation_digest(ro("005-codesign-display")), "candidate_cdhash_full": full, "team_identifier": "9BNSXJN65R"}, desktop_set),
        "docker-client": host_provenance("docker-client", [co("001-docker-version")], {"path": evidence.DOCKER_PATH, "sha256": evidence.DOCKER_SHA256, "client_version": "29.5.3", "api_version": "1.52", "go_version": "go1.24", "os": "darwin", "arch": "arm64"}, host_set),
        "buildx": host_provenance("buildx", [ro("003-buildx-version")], {"path": evidence.BUILDX_PATH, "sha256": evidence.BUILDX_SHA256, "version": "v0.34.1-desktop.1", "revision": "c79576280a671664e17eb68da98ec3136b614aed", "buildx_version_stdout_sha256": evidence.sha256_hex(streams[("readiness", "003-buildx-version")][0])}, host_set),
        "docker-daemon": host_provenance("docker-daemon", [co("001-docker-version"), co("002-docker-info")], {"host": PINNED_DOCKER_CONTEXT_HOST, "context_name": "desktop-linux", "server_version": "29.5.3", "api_version": "1.52", "os": "linux", "arch": "aarch64", "kernel_version": "6.10", "operating_system": "Docker Desktop", "docker_root_dir": "/var/lib/docker", "containerd_version": "1", "containerd_commit": "x", "runc_version": "1", "runc_commit": "x", "version_observation_sha256": evidence.observation_digest(co("001-docker-version")), "info_observation_sha256": evidence.observation_digest(co("002-docker-info"))}),
        "image-config": host_provenance("image-config", [co("003-image-config")], {"platform_reference": "docker.io/library/python@sha256:" + platform_digest, "image_id": config_digest, "config_descriptor_digest": config_digest, "architecture": "arm64", "os": "linux", "variant": "v8", "config_sha256": config_digest.split(":", 1)[1]}),
        "rootfs": host_provenance("rootfs", [co("003-image-config")], {"image_id": config_digest, "rootfs_type": "layers", "ordered_diff_ids": list(evidence.ROOTFS_DIFF_IDS)}),
    }
    for kind, value in provenance.items(): files["provenance/" + kind + ".json"] = evidence.canonical_json_bytes(value)
    files["provenance/info-plist.raw"] = info_plist_raw
    context_raw = PINNED_DOCKER_CONTEXT_RAW
    context_descriptor = descriptor("docker-context", "/Users/test/.docker/contexts/meta.json"); context_descriptor["before"]["size"] = context_descriptor["after"]["size"] = len(context_raw); context_descriptor["sha256"] = evidence.sha256_hex(context_raw)
    files["provenance/docker-context.raw"] = context_raw
    files["provenance/docker-context.json"] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["docker_context"], "path": context_descriptor["path"], "descriptor_observation": context_descriptor, "descriptor_observation_sha256": evidence.descriptor_observation_digest(context_descriptor), "bytes": len(context_raw), "sha256": evidence.sha256_hex(context_raw), "name": "desktop-linux", "host": PINNED_DOCKER_CONTEXT_HOST, "skip_tls_verify": False})
    runtime = {"python_version": "3.11.15", "executable": "/usr/local/bin/python3", "interpreter_sha256": SHA, "executable_chain": [{"kind": "regular", "path": "/usr/local/bin/python3", "mode": 0o755, "target_base64": None, "bytes": 1, "sha256": SHA}], "linker_version_argv": ["/usr/bin/ldd", "--version"], "linker_version_stdout_base64": b64(b"ldd 2.40\n"), "os_release_base64": b64(b"ID=debian\n")}
    files["attempts/normal/result.json"] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["probe_result"], "runtime": runtime})
    readiness_items = [
        (ro(name), *streams[("readiness", name)])
        for name in evidence._OPERATION_BASENAMES["readiness"]
    ]
    files["readiness/receipts.json"] = evidence.canonical_json_bytes(
        evidence.build_receipt_chain("readiness", retained_readiness_plan, readiness_items)
    )
    result = readiness_result(True); result.update({"readiness_plan_sha256": readiness_plan_sha, "ordered_observation_sha256": [evidence.observation_digest(ro(name)) for name in evidence._OPERATION_BASENAMES["readiness"]], "index_sha256": evidence.sha256_hex(index_raw), "selected_descriptor": selected, "selected_reference": selected_reference, "platform_sha256": platform_digest, "local_image_observation_sha256": evidence.observation_digest(ro("002-local-platform")), "buildx_version_observation_sha256": evidence.observation_digest(ro("003-buildx-version")), "codesign_verify_observation_sha256": evidence.observation_digest(ro("004-codesign-verify")), "codesign_display_observation_sha256": evidence.observation_digest(ro("005-codesign-display")), "context_sha256": evidence.sha256_hex(context_raw), "image_config_digest": config_digest})
    files["readiness/readiness-result.json"] = evidence.canonical_json_bytes(result)
    bindings.update({"user_authorization_sha256": user_authorization_sha256, "index_manifest_sha256": evidence.sha256_hex(index_raw), "selected_descriptor_digest": "sha256:" + platform_digest, "selected_descriptor_size": len(platform_raw), "selected_descriptor_media_type": platform["mediaType"], "platform_reference": selected_reference, "platform_manifest_sha256": platform_digest, "platform_manifest_size": len(platform_raw), "platform_manifest_media_type": platform["mediaType"], "docker_context_sha256": evidence.sha256_hex(context_raw), "docker_app_candidate_cdhash_full": full, "docker_app_team_identifier": "9BNSXJN65R", "docker_desktop_info_plist_sha256": evidence.sha256_hex(info_plist_raw)})
    return files, bindings


def attempt_command(ordinal: int, basename: str) -> dict:
    return {"ordinal": ordinal, "role": basename.split("-", 1)[1], "argv": ["/usr/bin/tool", basename], "environment": {"PATH": "/usr/bin:/bin"}, "cwd": "/", "stdin_policy": "closed-null", "stdout_cap": 262144, "stderr_cap": 262144, "timeout_ns": 60000000000, "activation": "always", "expected_outcomes": ["exit", "not_run"]}


def make_attempt_plan(
    attempt: str, authorization_sha256: str,
    platform_reference: str = "docker.io/library/python@sha256:" + SHA,
    source_manifest_sha256: str = SHA,
) -> dict:
    return execution.build_attempt_plan(
        campaign_id="campaign", attempt_id=attempt,
        authorization_sha256=authorization_sha256,
        implementation_commit=COMMIT,
        platform_reference=platform_reference,
        source_manifest_sha256=source_manifest_sha256,
        config_root="/private/tmp/p01b-docker-config",
        host_uri="unix:///var/run/docker.sock",
        temporary_root="/private/tmp/p01b-readiness",
        snapshot_root="/snapshot",
        seccomp_path="/snapshot/tools/hsai-formal-preflight/p01b_container_seccomp.json",
    )


def reseal_receipts(files: dict, attempt: str, plan: dict) -> list:
    items = []; previous = None
    for basename in evidence._OPERATION_BASENAMES[attempt]:
        base = "operations/{}/{}/".format(attempt, basename)
        observation = evidence.strict_json_bytes(files[base + "observation.json"])
        stdout = files[base + "stdout.bin"]; stderr = files[base + "stderr.bin"]
        for prefix, raw in (("stdout", stdout), ("stderr", stderr)):
            observation[prefix + "_total_bytes"] = observation[prefix + "_retained_bytes"] = len(raw)
            observation[prefix + "_raw_sha256"] = observation[prefix + "_retained_sha256"] = evidence.sha256_hex(raw)
            observation[prefix + "_truncated"] = False
        observation["previous_observation_sha256"] = previous
        files[base + "observation.json"] = evidence.canonical_json_bytes(observation)
        items.append((observation, stdout, stderr)); previous = evidence.observation_digest(observation)
    receipts = evidence.reconstruct_receipt_chain(plan, items)
    wrapper = {"schema": evidence.SCHEMAS["receipt_chain"], "kind": attempt, "plan_sha256": evidence.attempt_plan_digest(plan), "ordered_receipts": receipts, "chain_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(receipts))}
    files["attempts/{}/receipts.json".format(attempt)] = evidence.canonical_json_bytes(wrapper)
    return [item[0] for item in items]


def semantic_c10_fixture() -> tuple:
    files = {}; bindings = expected_bindings()
    readiness = readiness_result(True)
    files["readiness/readiness-result.json"] = evidence.canonical_json_bytes(readiness)
    common_digests = {name: SHA for name in ("user_authorization_sha256", "action_sha256", "policy_sha256", "evidence_bundle_sha256", "a3l6_gate_bundle_sha256", "admission_decision_sha256")}
    for path in ("action", "policy", "evidence-bundle", "admission-decision"):
        files["authority/" + path + ".json"] = evidence.canonical_json_bytes({"schema": "hsai-test-" + path + "-v1", "implementation_commit": COMMIT, "network_allowed": False})
    preauth = {"schema": evidence.SCHEMAS["preauthorization"], **common_digests, "predecessor_commit": COMMIT, "implementation_commit": COMMIT, "implementation_tree": TREE, "readiness_plan_sha256": SHA}
    files["readiness/preauthorization-plan.json"] = evidence.canonical_json_bytes(preauth)
    root = {"schema": evidence.SCHEMAS["authorization_root"], **common_digests, "preauthorization_sha256": evidence._digest("preauthorization", preauth), "expected_bindings_sha256": evidence.expected_bindings_digest(bindings), "readiness_sha256": evidence.readiness_result_digest(readiness), "implementation_commit": COMMIT, "implementation_tree": TREE, "authority_granted": True}
    files["authority/authorization-root.json"] = evidence.canonical_json_bytes(root)
    authorization = {"schema": evidence.SCHEMAS["authorization"], "authorization_id": "authorization", "authorization_root_sha256": evidence._digest("authorization_root", root), **common_digests, "expected_bindings_sha256": evidence.expected_bindings_digest(bindings), "implementation_commit": COMMIT, "implementation_tree": TREE, "readiness_sha256": evidence.readiness_result_digest(readiness)}
    files["readiness/authorization.json"] = evidence.canonical_json_bytes(authorization)
    authorization_sha256 = evidence._digest("authorization", authorization)
    plans = {attempt: make_attempt_plan(attempt, authorization_sha256) for attempt in ("normal", "oom")}
    campaign_commands = [attempt_command(index, "{:03d}-{}".format(index, role)) for index, role in enumerate(("native-reference", "docker-version", "docker-info", "image-config"))]
    campaign = {"schema": evidence.SCHEMAS["campaign_plan"], "campaign_id": "campaign", "authorization_sha256": authorization_sha256, "implementation_commit": COMMIT, "readiness_plan_sha256": SHA, "native_command": campaign_commands[0], "metadata_commands": campaign_commands[1:], "normal_plan_sha256": evidence.attempt_plan_digest(plans["normal"]), "oom_plan_sha256": evidence.attempt_plan_digest(plans["oom"])}
    files["readiness/campaign-plan.json"] = evidence.canonical_json_bytes(campaign)
    files["readiness/normal-plan.json"] = evidence.canonical_json_bytes(plans["normal"]); files["readiness/oom-plan.json"] = evidence.canonical_json_bytes(plans["oom"])
    seccomp_raw = evidence.canonical_json_bytes({"defaultAction": "SCMP_ACT_ERRNO"})
    for attempt in ("normal", "oom"):
        cid = ("55" if attempt == "normal" else "66") * 32; name = "campaign-" + attempt
        labels = {"hsai.p01b.attempt": attempt, "hsai.p01b.authorization": authorization_sha256, "hsai.p01b.campaign": "campaign", "hsai.p01b.commit": COMMIT}
        intent = {"schema": evidence.SCHEMAS["intent"], "campaign_id": "campaign", "attempt_id": attempt, "authorization_sha256": authorization_sha256, "implementation_commit": COMMIT, "container_name": name, "expected_labels": labels, "attempt_plan_sha256": evidence.attempt_plan_digest(plans[attempt]), "created_monotonic_ns": 1}
        files["attempts/{}/intent.json".format(attempt)] = evidence.canonical_json_bytes(intent)
        plan_sha = evidence.attempt_plan_digest(plans[attempt]); previous = None; observations = []
        commands_by_role = {item["role"]: item for item in plans[attempt]["commands"]}
        ready_line = ("P01B_RESULT_READY 1 " + SHA + "\n").encode()
        for index, basename in enumerate(evidence._OPERATION_BASENAMES[attempt]):
            command = commands_by_role[basename.split("-", 1)[1]]
            stdout = b""; stderr = b""; outcome = "exit"; exit_code = 0
            if index == 2: stdout = (cid + "\n").encode()
            elif index == 4: stdout = b"tar"
            elif index == 5: stdout = (cid + "\n").encode()
            elif index == 6: stdout = ready_line
            elif index == 7: outcome = "not_run"; exit_code = None
            elif index == 8: stdout = b"0\n"
            elif index == 10: stdout = (cid + "\n").encode()
            elif index == 11: exit_code = 1; stderr = ("Error: No such container: " + cid + "\n").encode()
            elif index == 12: exit_code = 1; stderr = ("Error: No such container: " + name + "\n").encode()
            elif index == 14: stdout = b'{"ServerVersion":"29.5.3"}\n'
            observation = semantic_observation(attempt, basename, index, stdout, stderr)
            observation["plan_sha256"] = plan_sha
            observation["launch_ordinal"] = command["ordinal"]
            observation["argv"] = [item.replace(evidence.CID_PLACEHOLDER, cid) for item in command["argv"]]
            observation["environment"] = command["environment"]
            observation["cwd"] = command["cwd"]
            observation["stdin_policy"] = command["stdin_policy"]
            observation["stdout_cap"] = command["stdout_cap"]
            observation["stderr_cap"] = command["stderr_cap"]
            observation["executable_path"] = observation["argv"][0]
            observation["executable_sha256"] = evidence.DOCKER_SHA256
            observation["container_id"] = cid if index >= 2 else None; observation["exit_code"] = exit_code; observation["outcome"] = outcome
            if index == 6: observation["started_monotonic_ns"] = 50; observation["ended_monotonic_ns"] = 200; observation["duration_ns"] = 150
            elif index == 4: observation["started_monotonic_ns"] = 100; observation["ended_monotonic_ns"] = 110; observation["duration_ns"] = 10
            elif index == 5: observation["started_monotonic_ns"] = 120; observation["ended_monotonic_ns"] = 130; observation["duration_ns"] = 10
            elif index == 7:
                observation["started_monotonic_ns"] = observation["ended_monotonic_ns"] = observation["duration_ns"] = 0
            elif index >= 8:
                observation["started_monotonic_ns"] = 210 + index * 10; observation["ended_monotonic_ns"] = 211 + index * 10; observation["duration_ns"] = 1
            observation["previous_observation_sha256"] = previous
            base = "operations/{}/{}/".format(attempt, basename)
            files[base + "observation.json"] = evidence.canonical_json_bytes(observation); files[base + "stdout.bin"] = stdout; files[base + "stderr.bin"] = stderr
            previous = evidence.observation_digest(observation); observations.append(observation)
        binding = {"schema": evidence.SCHEMAS["cid_binding"], "intent_sha256": evidence._digest("intent", intent), "container_id": cid, "create_observation_sha256": evidence.observation_digest(observations[2]), "bound_monotonic_ns": 45}
        files["attempts/{}/cid-binding.json".format(attempt)] = evidence.canonical_json_bytes(binding)
        durability = [("intent-file-fsync", "intent.json", evidence._digest("intent", intent)), ("intent-directory-fsync", ".", None), ("container-create", name, evidence.observation_digest(observations[2])), ("cid-binding-file-fsync", "cid-binding.json", evidence._digest("cid_binding", binding)), ("cid-binding-directory-fsync", ".", None)]
        events = [{"ordinal": index, "operation": op, "target": target, "started_monotonic_ns": [2,4,22,42,44][index], "ended_monotonic_ns": [3,5,41,43,45][index], "result": 0, "errno": None if index == 2 else 0, "sha256": digest} for index, (op, target, digest) in enumerate(durability)]
        timing = {"schema": "hsai-p01b-attempt-timing-v1", "campaign_id": "campaign", "attempt_id": attempt, "start_monotonic_ns": 1, "deadline_monotonic_ns": 1 + bindings["attempt_deadline_ns"], "end_monotonic_ns": 400, "ordered_durability_events": events, "deadline_met": True}
        files["attempts/{}/timing.json".format(attempt)] = evidence.canonical_json_bytes(timing)
        receipts = reseal_receipts(files, attempt, plans[attempt]); observations = [evidence.strict_json_bytes(files["operations/{}/{}/observation.json".format(attempt, basename)]) for basename in evidence._OPERATION_BASENAMES[attempt]]
        event = {"schema": evidence.SCHEMAS["readiness_event"], "plan_sha256": plan_sha, "attempt_id": attempt, "start_launch_ordinal": observations[6]["launch_ordinal"], "stdout_path": observations[6]["stdout_path"], "prefix_bytes": len(ready_line), "prefix_sha256": evidence.sha256_hex(ready_line), "line_offset": 0, "line_bytes": len(ready_line), "line_sha256": evidence.sha256_hex(ready_line), "observed_monotonic_ns": 90}
        files["attempts/{}/readiness-event.json".format(attempt)] = evidence.canonical_json_bytes(event)
        files["attempts/{}/inspect-prestart.json".format(attempt)] = evidence.canonical_json_bytes([semantic_inspect("prestart", seccomp_raw, cid, name, labels)])
        files["attempts/{}/inspect-terminal.json".format(attempt)] = evidence.canonical_json_bytes([semantic_inspect("terminal", seccomp_raw, cid, name, labels)])
        predicates = {"container_id": cid, "container_name": name, "labels_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(labels)), "remove_observation_sha256": evidence.observation_digest(observations[10]), "cid_absence_observation_sha256": evidence.observation_digest(observations[11]), "name_absence_observation_sha256": evidence.observation_digest(observations[12]), "label_absence_observation_sha256": evidence.observation_digest(observations[13]), "daemon_recheck_observation_sha256": evidence.observation_digest(observations[14]), "absent": True}
        cleanup = {"schema": evidence.SCHEMAS["certificate"], "kind": "cleanup", "predicate_schema": "cleanup-v1", "authorization_sha256": authorization_sha256, "implementation_commit": COMMIT, "attempt_id": attempt, "subject_manifest_sha256": SHA, "observation_sha256": evidence.observation_digest(observations[14]), "predicates": predicates, "accepted_evidence_created": False, "level2_plus_created": False, "authority_granted": False}
        files["attempts/{}/cleanup-certificate.json".format(attempt)] = evidence.canonical_json_bytes(cleanup)
    return files, bindings, plans


def retained_descriptor(role: str, path: str, relative: str, raw: bytes, inode: int, mode: int = 0o444) -> dict:
    value = identity(len(raw))
    value.update({"inode": inode, "mode": mode})
    return {
        "schema": evidence.SCHEMAS["descriptor_observation"], "role": role,
        "path": path, "relative_path": relative, "before": value,
        "after": copy.deepcopy(value), "sha256": evidence.sha256_hex(raw),
    }


def synthetic_snapshot(files: dict, bindings: dict) -> dict:
    seccomp = evidence.canonical_json_bytes({"defaultAction": "SCMP_ACT_ERRNO", "syscalls": []})
    source_bytes = {}
    for index, path in enumerate(evidence.SNAPSHOT_PATHS):
        if path.endswith("p01b_container_seccomp.json"):
            raw = seccomp
        elif path.endswith(".json"):
            raw = evidence.canonical_json_bytes({"path": path, "synthetic": True})
        else:
            raw = ("synthetic source " + path + "\n").encode("ascii")
        source_bytes[path] = raw
        files["snapshot/files/" + path] = raw
    source_observations = []
    copy_observations = []
    for index, path in enumerate(evidence.SNAPSHOT_PATHS):
        raw = source_bytes[path]
        source_observations.append(retained_descriptor("source", "/repo/" + path, path, raw, 100 + index, 0o444))
        copy_observations.append(retained_descriptor("snapshot", "/snapshot/" + path, path, raw, 200 + index, 0o444))
    source_manifest = {"schema": evidence.SCHEMAS["snapshot_source"], "ordered_entries": []}
    copy_manifest = {"schema": evidence.SCHEMAS["snapshot_copy"], "ordered_entries": []}
    for path, source_observation, copy_observation in zip(evidence.SNAPSHOT_PATHS, source_observations, copy_observations):
        raw = source_bytes[path]
        common = {"path": path, "mode": 0o444, "bytes": len(raw), "sha256": evidence.sha256_hex(raw)}
        source_manifest["ordered_entries"].append({**common, "descriptor_observation_sha256": evidence.descriptor_observation_digest(source_observation)})
        copy_manifest["ordered_entries"].append({**common, "descriptor_observation_sha256": evidence.descriptor_observation_digest(copy_observation)})
    source_sha = evidence._digest("snapshot_source", source_manifest)
    copy_sha = evidence._digest("snapshot_copy", copy_manifest)
    files["snapshot/source-manifest.json"] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["snapshot_pair"], "implementation_commit": COMMIT, "implementation_tree": TREE, "source_manifest": source_manifest, "snapshot_manifest": copy_manifest})
    files["snapshot/source-descriptor-observations.json"] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["snapshot_descriptor"], "kind": "source", "manifest_sha256": source_sha, "ordered_observations": source_observations})
    files["snapshot/ingress-observations.json"] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["snapshot_descriptor"], "kind": "snapshot", "manifest_sha256": copy_sha, "ordered_observations": copy_observations})
    bindings.update({"snapshot_source_manifest_sha256": source_sha, "snapshot_copy_manifest_sha256": copy_sha, "seccomp_sha256": evidence.sha256_hex(seccomp)})
    return source_bytes


def gate_capture(role: str, argv: list, environment: dict, cwd: str, executable: str, executable_sha: str, stdout: bytes, started: int, stdout_cap: int) -> dict:
    return {
        "role": role, "argv": argv, "environment": environment, "cwd": cwd,
        "stdin_policy": "closed", "executable_path": executable,
        "executable_sha256": executable_sha, "timeout_ns": 60_000_000_000,
        "stdout_cap_bytes": stdout_cap, "stderr_cap_bytes": 16_384,
        "started_monotonic_ns": started, "ended_monotonic_ns": started + 1,
        "outcome": "completed", "exit_code": 0, "signal": None,
        "stdout_total_bytes": len(stdout), "stdout_retained_bytes": len(stdout),
        "stdout_truncated": False, "stdout_base64": b64(stdout),
        "stdout_sha256": evidence.sha256_hex(stdout), "stderr_total_bytes": 0,
        "stderr_retained_bytes": 0, "stderr_truncated": False,
        "stderr_base64": b64(b""), "stderr_sha256": evidence.EMPTY_SHA256,
    }


def unittest_transcript(ids: list) -> bytes:
    rows = ["{} ({}) ... ok".format(item.rsplit(".", 1)[1], item.rsplit(".", 1)[0]) for item in ids]
    rows += ["", "-" * 70, "Ran {} tests in 0.001s".format(len(ids)), "", "OK"]
    return ("\n".join(rows) + "\n").encode("ascii")


def synthetic_gate(source_bytes: dict, bindings: dict) -> dict:
    parent = "/private/tmp/hsai-p01b-gate-" + "1" * 32
    root = parent + "/source"; scratch = parent + "/scratch"; profile_path = parent + "/gate.sb"
    environment = evidence._gate_environment(scratch)
    root_identity = {"device": 7, "inode": 70, "mode": 0o555, "uid": 501, "gid": 20, "link_count": 1}
    git = "/usr/bin/git"; git_sha = SHA
    captures = []
    head = gate_capture("gate-head", [git, "rev-parse", "HEAD"], environment, "/repo", git, git_sha, (COMMIT + "\n").encode(), 10, 4096)
    tree = gate_capture("gate-tree", [git, "rev-parse", COMMIT + "^{tree}"], environment, "/repo", git, git_sha, (TREE + "\n").encode(), 20, 4096)
    status_argv = [git, "status", "--porcelain=v2", "-z", "--untracked-files=all"]
    status_before = gate_capture("gate-status-before", status_argv, environment, "/repo", git, git_sha, b"", 30, 1_048_576)
    source_rows = []
    for index, path in enumerate(evidence.SNAPSHOT_PATHS):
        raw = source_bytes[path]; expression = COMMIT + ":" + path
        captures.append(gate_capture("gate-blob-%03d" % index, [git, "cat-file", "blob", expression], environment, "/repo", git, git_sha, raw, 40 + index * 2, 16_777_216))
        pre = retained_descriptor("gate-source-pre", root + "/" + path, path, raw, 1000 + index)
        post = retained_descriptor("gate-source-post", root + "/" + path, path, raw, 1000 + index)
        source_rows.append({"path": path, "git_object_expression": expression, "git_blob_oid": evidence._git_blob_oid(raw), "bytes": len(raw), "sha256": evidence.sha256_hex(raw), "pre_gate_started_monotonic_ns": 90, "pre_gate_ended_monotonic_ns": 91, "pre_gate_descriptor_observation": pre, "post_gate_started_monotonic_ns": 2001, "post_gate_ended_monotonic_ns": 2002, "post_gate_descriptor_observation": post})
    inventory = []
    directory_paths = set(evidence._gate_inventory_paths()) - set(evidence.SNAPSHOT_PATHS)
    for ordinal, path in enumerate(evidence._gate_inventory_paths()):
        if path in directory_paths:
            inode = root_identity["inode"] if path == "." else 5000 + ordinal
            inventory.append({"path": path, "type": "directory", "mode": 0o555, "device": 7, "inode": inode, "uid": 501, "gid": 20, "link_count": 1, "bytes": None, "sha256": None})
        else:
            source = source_rows[list(evidence.SNAPSHOT_PATHS).index(path)]
            inventory.append({"path": path, "type": "regular", "mode": 0o444, "device": 1, "inode": source["pre_gate_descriptor_observation"]["before"]["inode"], "uid": 501, "gid": 20, "link_count": 1, "bytes": source["bytes"], "sha256": source["sha256"]})
    inventory_sha = evidence.sha256_hex(evidence.canonical_json_bytes(inventory))
    profile = evidence._gate_profile(root, scratch)
    sandbox_descriptor = retained_descriptor("sandbox-exec", "/usr/bin/sandbox-exec", None, b"x", 8000, 0o755)
    sandbox_descriptor["sha256"] = evidence.SANDBOX_EXEC_SHA256
    profile_descriptor = retained_descriptor("sandbox-profile", profile_path, None, profile, 8001, 0o400)
    status_after = gate_capture("gate-status-after", status_argv, environment, "/repo", git, git_sha, b"", 2100, 1_048_576)
    source = {"schema": evidence.SCHEMAS["a3l6_gate_source"], "implementation_commit": COMMIT, "implementation_tree": TREE, "audit_commit": COMMIT, "git_path": git, "git_sha256": git_sha, "environment": environment, "repository_cwd": "/repo", "materialized_root": root, "materialized_root_identity": root_identity, "gate_temp_root": scratch, "sandbox_exec_descriptor_observation": sandbox_descriptor, "sandbox_profile_path": profile_path, "sandbox_profile_descriptor_observation": profile_descriptor, "sandbox_profile_base64": b64(profile), "sandbox_profile_sha256": evidence.sha256_hex(profile), "materialized_inventory_before_sha256": inventory_sha, "materialized_inventory_before": inventory, "materialized_inventory_after_sha256": inventory_sha, "materialized_inventory_after": copy.deepcopy(inventory), "head_observation": head, "tree_observation": tree, "status_before_observation": status_before, "ordered_blob_observations": captures, "ordered_sources": source_rows, "pre_gate_capture_ended_monotonic_ns": 1000, "post_gate_capture_started_monotonic_ns": 2000, "status_after_observation": status_after}
    source_sha = evidence.a3l6_gate_source_digest(source)
    evidence_ids = ["__main__.EvidenceSynthetic.test_{:02d}".format(index) for index in range(32)]
    execution_ids = ["__main__.ExecutionSynthetic.test_{:02d}".format(index) for index in range(32)]
    ids = evidence_ids + execution_ids
    ids.sort()
    command_argv = (
        ["/usr/bin/sandbox-exec", "-f", profile_path, "/usr/bin/python3", "-E", "-s", "-S", "-B", "tools/hsai-formal-preflight/p01b_container_evidence_tests.py", "-v"],
        ["/usr/bin/sandbox-exec", "-f", profile_path, "/usr/bin/python3", "-E", "-s", "-S", "-B", "tools/hsai-formal-preflight/p01b_container_execution_tests.py", "-v"],
        ["/usr/bin/sandbox-exec", "-f", profile_path, "/usr/bin/python3", "-E", "-s", "-S", "-B", "-m", "unittest", "discover", "-s", "tools/hsai-formal-preflight/tests", "-p", "test_*.py", "-v"],
    )
    roles = ("evidence-focused", "execution-focused", "formal-discovery")
    commands = [{"role": role, "argv": argv, "environment": environment, "cwd": root, "stdin_policy": "closed", "timeout_ns": 600_000_000_000, "stdout_cap_bytes": 262_144, "stderr_cap_bytes": 262_144, "activation": "always", "expected_exit_code": 0, "expected_signal": None} for role, argv in zip(roles, command_argv)]
    plan = {"schema": evidence.SCHEMAS["a3l6_gate_plan"], "implementation_commit": COMMIT, "implementation_tree": TREE, "audit_commit": COMMIT, "python_path": "/usr/bin/python3", "python_sha256": evidence.NATIVE_PYTHON_SHA256, "python_version": "3.9.6", "environment": environment, "gate_source_root": root, "gate_source_root_identity": root_identity, "gate_temp_root": scratch, "sandbox_exec_path": "/usr/bin/sandbox-exec", "sandbox_exec_sha256": evidence.SANDBOX_EXEC_SHA256, "sandbox_profile_path": profile_path, "sandbox_profile_sha256": evidence.sha256_hex(profile), "gate_source_manifest_sha256": source_sha, "cwd": root, "commands": commands, "reviewed_paths": list(evidence.REVIEWED_PATHS), "expected_focused_test_ids": ids, "expected_focused_test_count": 64, "expected_discovery_test_count": 172}
    gate_observations = []
    gate_id_sets = (evidence_ids, execution_ids, ["formal_tests.Synthetic.test_{:03d}".format(index) for index in range(172)])
    for index, (command, test_ids) in enumerate(zip(commands, gate_id_sets)):
        stderr = unittest_transcript(test_ids)
        observation = {**command, "executable_path": "/usr/bin/sandbox-exec", "executable_sha256": evidence.SANDBOX_EXEC_SHA256, "cwd_identity_before": root_identity, "cwd_identity_after": root_identity, "started_monotonic_ns": 1100 + index * 100, "ended_monotonic_ns": 1150 + index * 100, "outcome": "completed", "exit_code": 0, "signal": None, "stdout_total_bytes": 0, "stdout_retained_bytes": 0, "stdout_truncated": False, "stdout_base64": b64(b""), "stdout_sha256": evidence.EMPTY_SHA256, "stderr_total_bytes": len(stderr), "stderr_retained_bytes": len(stderr), "stderr_truncated": False, "stderr_base64": b64(stderr), "stderr_sha256": evidence.sha256_hex(stderr)}
        for name in ("activation", "expected_exit_code", "expected_signal"):
            observation.pop(name)
        gate_observations.append(observation)
    version = gate_capture("gate-python-version", ["/usr/bin/python3", "--version"], environment, root, "/usr/bin/python3", evidence.NATIVE_PYTHON_SHA256, b"Python 3.9.6\n", 1001, 16_384)
    observation_sha = evidence.sha256_hex(evidence.canonical_json_bytes(gate_observations))
    source_sha_by_path = {item["path"]: item["sha256"] for item in source_rows}
    reviewed = [{"path": path, "sha256": source_sha_by_path[path]} for path in evidence.REVIEWED_PATHS]
    plan_sha = evidence.a3l6_gate_plan_digest(plan)
    reviews = [{"schema": evidence.SCHEMAS["a3l6_code_review"], "role": role, "reviewer_id": "gate-reviewer-" + str(index), "implementation_commit": COMMIT, "implementation_tree": TREE, "ordered_file_sha256": reviewed, "gate_plan_sha256": plan_sha, "gate_source_manifest_sha256": source_sha, "gate_observation_sha256": observation_sha, "findings": [], "result": "accept"} for index, role in enumerate(evidence.REVIEW_ROLE_ORDER)]
    bundle = {"schema": evidence.SCHEMAS["a3l6_gate_bundle"], "gate_plan": plan, "gate_source_manifest": source, "implementation_commit": COMMIT, "implementation_tree": TREE, "python_path": "/usr/bin/python3", "python_sha256": evidence.NATIVE_PYTHON_SHA256, "python_version": "3.9.6", "python_version_observation": version, "ordered_gate_observations": gate_observations, "focused_test_ids": ids, "focused_test_count": 64, "discovery_test_count": 172, "ordered_review_records": reviews, "result": "accept"}
    bindings.update({"a3l6_audit_commit": COMMIT, "a3l6_gate_plan_sha256": plan_sha, "a3l6_gate_source_manifest_sha256": source_sha, "a3l6_gate_bundle_sha256": evidence._digest("a3l6_gate_bundle", bundle), "expected_focused_test_ids_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(ids)), "validator_sha256": source_sha_by_path[evidence.REVIEWED_PATHS[1]], "collector_sha256": source_sha_by_path[evidence.REVIEWED_PATHS[2]], "sandbox_exec_path": "/usr/bin/sandbox-exec", "sandbox_exec_sha256": evidence.SANDBOX_EXEC_SHA256, "gate_sandbox_profile_sha256": evidence.sha256_hex(profile), "git_path": git, "git_sha256": git_sha})
    return bundle


def synthetic_runtime(mode: str, interpreter_sha: str) -> dict:
    executable = "/usr/bin/python3" if mode == "native-reference" else "/usr/local/bin/python3"
    version = "3.9.6" if mode == "native-reference" else "3.11.15"
    inventory = [{"path": executable, "mode": 0o755, "bytes": 1, "sha256": interpreter_sha}]
    chain = [{**inventory[0], "kind": "regular", "target_base64": None}]
    return {
        "python_version": version, "implementation": "CPython", "executable": executable,
        "executable_chain": chain, "interpreter_sha256": interpreter_sha,
        "stdlib_root": "/usr/lib/python", "stdlib_entries": [{"path": "/usr/lib/python/os.py", "mode": 0o444, "bytes": 1, "sha256": SHA}],
        "stdlib_sha256": SHA, "ldd_argv": ["/usr/bin/ldd", executable],
        "ldd_stdout_base64": b64(b"libc.so\n"), "dependencies": [{"path": "/usr/lib/libc.so", "mode": 0o555, "bytes": 1, "sha256": SHA}],
        "dependencies_sha256": SHA, "zlib_compile": "1.2", "zlib_runtime": "1.2",
        "libc": "glibc", "os_release_base64": b64(b"ID=debian\n"), "packages": ["python"],
        "packages_sha256": SHA, "sys_version": version, "sysconfig_paths": {"stdlib": "/usr/lib/python"},
        "linker_version_argv": ["/usr/bin/ldd", "--version"], "linker_version_stdout_base64": b64(b"ldd 2.40\n"),
    }


def synthetic_mounts_and_limits() -> tuple:
    mountinfo = b"1 0 0:1 / /work rw - tmpfs tmpfs rw\n2 0 0:2 / /dev/shm rw - tmpfs tmpfs rw\n"
    mounts = {
        "mountinfo_sha256": evidence.sha256_hex(mountinfo), "mountinfo_base64": b64(mountinfo),
        "work": {"target": "/work", "fs_type": "tmpfs", "options": ["rw", "nosuid", "nodev", "noexec"], "size_bytes": 16_777_216, "mode": 0o700, "uid": 65532, "gid": 65532},
        "shm": {"target": "/dev/shm", "fs_type": "tmpfs", "options": ["rw", "nosuid", "nodev", "noexec"], "size_bytes": 1_048_576, "mode": 0o1777, "uid": 65532, "gid": 65532},
    }
    proc_limits = b"Max cpu time 900 900 seconds\nMax file size 67108864 67108864 bytes\nMax open files 32 32 files\nMax core file size 0 0 bytes\n"
    limits = {"cpu": [900, 900], "fsize": [67_108_864, 67_108_864], "nofile": [32, 32], "core": [0, 0], "proc_limits_base64": b64(proc_limits)}
    return mounts, limits


def synthetic_probe_results(files: dict, bindings: dict) -> None:
    probe_sha = evidence.sha256_hex(files["snapshot/files/tools/hsai-formal-preflight/p01b_container_probe.py"])
    fixture = b"fixture"; header = b"header"; inventory = b"inventory"
    manifest_projection = {"entries": 1}; status_projection = {"status": "ok"}
    projection = {"header_ledger_sha256": evidence.sha256_hex(header), "inventory_ledger_sha256": evidence.sha256_hex(inventory), "normalized_manifest_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(manifest_projection)), "normalized_status_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(status_projection))}
    projection_sha = evidence.domain_sha256(evidence.DOMAINS["projection"], projection)
    common = {"schema": evidence.SCHEMAS["probe_result"], "probe_sha256": probe_sha, "fixture_base64": b64(fixture), "header_ledger_base64": b64(header), "inventory_ledger_base64": b64(inventory), "manifest_projection": manifest_projection, "status_projection": status_projection, "excluded_telemetry": {"manifest": list(evidence._MANIFEST_EXCLUDED_FIELDS), "status": list(evidence._STATUS_EXCLUDED_FIELDS)}, "projection_sha256": projection_sha}
    native = {**common, "mode": "native-reference", "runtime": synthetic_runtime("native-reference", evidence.NATIVE_PYTHON_SHA256)}
    mounts, limits = synthetic_mounts_and_limits()
    normal = {**copy.deepcopy(common), "mode": "normal", "runtime": synthetic_runtime("normal", SHA), "input_manifest_sha256": bindings["snapshot_copy_manifest_sha256"], "corpus_validation": {"focused_test_count": 68, "full_test_count": 151, "source_file_count": 11, "test_id_digest": SHA}, "workload": {"argv": ["/usr/bin/python3", "-m", "unittest"], "returncode": 0, "signal": None, "stdout_base64": b64(b""), "stderr_base64": b64(b""), "discovered_count": 151, "expected_count": 151}, "security": security(100), "cgroup_pre": cgroup_snapshot("pre", [100], observed=10), "cgroup_terminal": cgroup_snapshot("terminal", [100], observed=20), "mounts": mounts, "rlimits": limits}
    oom_security = security(200)
    process_common = {"cgroup_path": "/docker/test", "ready": True, "namespaces": oom_security["namespaces"], "cgroup_base64": b64(b"0::/docker/test\n")}
    transcript = b"P01B_OOM_CHILD_READY\nP01B_OOM_CHILD_RELEASE\n"
    oom = {"schema": evidence.SCHEMAS["probe_result"], "mode": "oom-child", "probe_sha256": probe_sha, "input_manifest_sha256": bindings["snapshot_copy_manifest_sha256"], "security": oom_security, "cgroup_pre": cgroup_snapshot("pre", [200, 201], observed=30), "cgroup_terminal": cgroup_snapshot("terminal", [200], oom=1, oom_kill=1, observed=40), "mounts": copy.deepcopy(mounts), "rlimits": copy.deepcopy(limits), "parent": {"pid": 200, "oom_score_adj": 0, "wait_signal": None, "survived": True, "oom_score_adj_base64": b64(b"0\n"), **process_common}, "child": {"pid": 201, "oom_score_adj": 1000, "wait_signal": 9, "survived": False, "oom_score_adj_base64": b64(b"1000\n"), **process_common}, "workload": {"barrier_sha256": evidence.sha256_hex(transcript), "allocation_bytes": 640 * 1024 * 1024, "child_wait_signal": 9, "parent_survived": True, "local_event_deltas": {"oom": 1, "oom_kill": 1, "oom_group_kill": 0}, "terminal_processes": [200], "barrier_transcript_base64": b64(transcript), "child_cgroup_read_monotonic_ns": 1, "score_write_monotonic_ns": 2, "score_readback_monotonic_ns": 3, "child_ready_monotonic_ns": 3, "release_monotonic_ns": 4, "allocation_started_monotonic_ns": 5, "child_wait_monotonic_ns": 6, "raw_wait_status": 9}}
    files["reference/native-result.json"] = evidence.canonical_json_bytes(native)
    files["reference/projection.json"] = evidence.canonical_json_bytes({"schema": "hsai-p01b-reference-projection-v1", "probe_sha256": probe_sha, "projection_sha256": projection_sha})
    files["attempts/normal/result.json"] = evidence.canonical_json_bytes(normal)
    files["attempts/oom/result.json"] = evidence.canonical_json_bytes(oom)


def strict_ustar(payload: bytes) -> bytes:
    header = bytearray(512)
    header[0:100] = b"result.json" + b"\0" * 89
    header[100:108] = b"0000600\0"; header[108:116] = b"0177774\0"; header[116:124] = b"0177774\0"
    header[124:136] = ("{:011o}\0".format(len(payload))).encode("ascii")
    header[136:148] = b"00000000000\0"; header[148:156] = b"        "; header[156:157] = b"0"
    header[257:263] = b"ustar\0"; header[263:265] = b"00"
    header[329:337] = b"0000000\0"; header[337:345] = b"0000000\0"
    checksum = sum(header)
    header[148:156] = ("{:06o}\0 ".format(checksum)).encode("ascii")
    padding = b"\0" * ((512 - len(payload) % 512) % 512)
    return bytes(header) + payload + padding + b"\0" * 1024


def reseal_campaign(files: dict, plan: dict) -> None:
    previous = None; items = []
    commands = [plan["native_command"], *plan["metadata_commands"]]
    for basename, command in zip(evidence._OPERATION_BASENAMES["campaign"], commands):
        base = "operations/campaign/{}/".format(basename)
        observation = evidence.strict_json_bytes(files[base + "observation.json"])
        observation["plan_sha256"] = evidence.campaign_plan_digest(plan)
        observation["argv"] = command["argv"]
        observation["environment"] = command["environment"]
        observation["cwd"] = command["cwd"]
        observation["stdin_policy"] = command["stdin_policy"]
        observation["stdout_cap"] = command["stdout_cap"]
        observation["stderr_cap"] = command["stderr_cap"]
        observation["executable_path"] = observation["argv"][0]
        observation["executable_sha256"] = (
            evidence.NATIVE_PYTHON_SHA256
            if observation["executable_path"] == "/usr/bin/python3"
            else evidence.DOCKER_SHA256
        )
        observation["previous_observation_sha256"] = previous
        files[base + "observation.json"] = evidence.canonical_json_bytes(observation)
        previous = evidence.observation_digest(observation)
        items.append((observation, files[base + "stdout.bin"], files[base + "stderr.bin"]))
    receipts = evidence.reconstruct_receipt_chain(plan, items)
    files["reference/receipts.json"] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["receipt_chain"], "kind": "campaign", "plan_sha256": evidence.campaign_plan_digest(plan), "ordered_receipts": receipts, "chain_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(receipts))})
    for kind in ("docker-client", "docker-daemon", "image-config", "rootfs"):
        path = "provenance/" + kind + ".json"; value = evidence.strict_json_bytes(files[path])
        names = {"docker-client": ("001-docker-version",), "docker-daemon": ("001-docker-version", "002-docker-info"), "image-config": ("003-image-config",), "rootfs": ("003-image-config",)}[kind]
        value["ordered_source_observation_sha256"] = [evidence.observation_digest(evidence.strict_json_bytes(files["operations/campaign/{}/observation.json".format(name)])) for name in names]
        if kind == "docker-daemon":
            value["facts"]["version_observation_sha256"], value["facts"]["info_observation_sha256"] = value["ordered_source_observation_sha256"]
        files[path] = evidence.canonical_json_bytes(value)


def rebind_attempt(files: dict, attempt: str, plan: dict, authorization_sha: str, bindings: dict) -> dict:
    cid = ("55" if attempt == "normal" else "66") * 32
    name = "hsai-p01b-campaign-" + attempt
    labels = {"hsai.p01b.attempt": attempt, "hsai.p01b.authorization": authorization_sha, "hsai.p01b.campaign": "campaign", "hsai.p01b.implementation": COMMIT}
    plan_sha = evidence.attempt_plan_digest(plan)
    intent = {"schema": evidence.SCHEMAS["intent"], "campaign_id": "campaign", "attempt_id": attempt, "authorization_sha256": authorization_sha, "implementation_commit": COMMIT, "container_name": name, "expected_labels": labels, "attempt_plan_sha256": plan_sha, "created_monotonic_ns": 1}
    files["attempts/{}/intent.json".format(attempt)] = evidence.canonical_json_bytes(intent)
    export_tar = strict_ustar(files["attempts/{}/result.json".format(attempt)])
    files["attempts/{}/export.tar".format(attempt)] = export_tar
    files["operations/{}/004-export-running/stdout.bin".format(attempt)] = export_tar
    files["operations/{}/011-absence-cid/stderr.bin".format(attempt)] = (
        "Error: No such container: " + cid + "\n"
    ).encode("ascii")
    files["operations/{}/012-absence-name/stderr.bin".format(attempt)] = (
        "Error: No such container: " + name + "\n"
    ).encode("ascii")
    previous = None; observations = []
    commands_by_role = {item["role"]: item for item in plan["commands"]}
    for index, basename in enumerate(evidence._OPERATION_BASENAMES[attempt]):
        command = commands_by_role[basename.split("-", 1)[1]]
        base = "operations/{}/{}/".format(attempt, basename)
        observation = evidence.strict_json_bytes(files[base + "observation.json"])
        observation["plan_sha256"] = plan_sha
        observation["launch_ordinal"] = command["ordinal"]
        observation["argv"] = [
            item.replace(evidence.CID_PLACEHOLDER, cid) for item in command["argv"]
        ]
        observation["environment"] = command["environment"]
        observation["cwd"] = command["cwd"]
        observation["stdin_policy"] = command["stdin_policy"]
        observation["stdout_cap"] = command["stdout_cap"]
        observation["stderr_cap"] = command["stderr_cap"]
        observation["executable_path"] = observation["argv"][0]
        observation["executable_sha256"] = evidence.DOCKER_SHA256
        stdout = files[base + "stdout.bin"]
        stderr = files[base + "stderr.bin"]
        for prefix, raw in (("stdout", stdout), ("stderr", stderr)):
            observation[prefix + "_total_bytes"] = len(raw)
            observation[prefix + "_retained_bytes"] = len(raw)
            observation[prefix + "_raw_sha256"] = evidence.sha256_hex(raw)
            observation[prefix + "_retained_sha256"] = evidence.sha256_hex(raw)
        observation["previous_observation_sha256"] = previous
        files[base + "observation.json"] = evidence.canonical_json_bytes(observation)
        previous = evidence.observation_digest(observation); observations.append(observation)
    binding = {"schema": evidence.SCHEMAS["cid_binding"], "intent_sha256": evidence._digest("intent", intent), "container_id": cid, "create_observation_sha256": evidence.observation_digest(observations[2]), "bound_monotonic_ns": 45}
    files["attempts/{}/cid-binding.json".format(attempt)] = evidence.canonical_json_bytes(binding)
    expected_events = (("intent-file-fsync", "intent.json", evidence._digest("intent", intent)), ("intent-directory-fsync", ".", None), ("container-create", name, evidence.observation_digest(observations[2])), ("cid-binding-file-fsync", "cid-binding.json", evidence._digest("cid_binding", binding)), ("cid-binding-directory-fsync", ".", None))
    starts = (2, 4, 22, 42, 44); ends = (3, 5, 41, 43, 45)
    events = [{"ordinal": index, "operation": operation, "target": target, "started_monotonic_ns": starts[index], "ended_monotonic_ns": ends[index], "result": 0, "errno": None if index == 2 else 0, "sha256": digest} for index, (operation, target, digest) in enumerate(expected_events)]
    files["attempts/{}/timing.json".format(attempt)] = evidence.canonical_json_bytes({"schema": "hsai-p01b-attempt-timing-v1", "campaign_id": "campaign", "attempt_id": attempt, "start_monotonic_ns": 1, "deadline_monotonic_ns": 1 + bindings["attempt_deadline_ns"], "end_monotonic_ns": 400, "ordered_durability_events": events, "deadline_met": True})
    ready_line = ("P01B_RESULT_READY 1 " + SHA + "\n").encode()
    files["attempts/{}/readiness-event.json".format(attempt)] = evidence.canonical_json_bytes({"schema": evidence.SCHEMAS["readiness_event"], "plan_sha256": plan_sha, "attempt_id": attempt, "start_launch_ordinal": observations[6]["launch_ordinal"], "stdout_path": observations[6]["stdout_path"], "prefix_bytes": len(ready_line), "prefix_sha256": evidence.sha256_hex(ready_line), "line_offset": 0, "line_bytes": len(ready_line), "line_sha256": evidence.sha256_hex(ready_line), "observed_monotonic_ns": 90})
    seccomp = files["snapshot/files/tools/hsai-formal-preflight/p01b_container_seccomp.json"]
    files["attempts/{}/inspect-prestart.json".format(attempt)] = evidence.canonical_json_bytes([semantic_inspect("prestart", seccomp, cid, name, labels)])
    files["attempts/{}/inspect-terminal.json".format(attempt)] = evidence.canonical_json_bytes([semantic_inspect("terminal", seccomp, cid, name, labels)])
    reseal_receipts(files, attempt, plan)
    observations = [
        evidence.strict_json_bytes(
            files["operations/{}/{}/observation.json".format(attempt, basename)]
        )
        for basename in evidence._OPERATION_BASENAMES[attempt]
    ]
    predicates = {"container_id": cid, "container_name": name, "labels_sha256": evidence.sha256_hex(evidence.canonical_json_bytes(labels)), "remove_observation_sha256": evidence.observation_digest(observations[10]), "cid_absence_observation_sha256": evidence.observation_digest(observations[11]), "name_absence_observation_sha256": evidence.observation_digest(observations[12]), "label_absence_observation_sha256": evidence.observation_digest(observations[13]), "daemon_recheck_observation_sha256": evidence.observation_digest(observations[14]), "absent": True}
    cleanup = {"schema": evidence.SCHEMAS["certificate"], "kind": "cleanup", "predicate_schema": "cleanup-v1", "authorization_sha256": authorization_sha, "implementation_commit": COMMIT, "attempt_id": attempt, "subject_manifest_sha256": bindings["snapshot_copy_manifest_sha256"], "observation_sha256": evidence.observation_digest(observations[14]), "predicates": predicates, "accepted_evidence_created": False, "level2_plus_created": False, "authority_granted": False}
    files["attempts/{}/cleanup-certificate.json".format(attempt)] = evidence.canonical_json_bytes(cleanup)
    snapshot_pair = evidence.strict_json_bytes(files["snapshot/source-manifest.json"])
    source_descriptors = evidence.strict_json_bytes(files["snapshot/source-descriptor-observations.json"])
    copy_descriptors = evidence.strict_json_bytes(files["snapshot/ingress-observations.json"])
    ingress = evidence.build_certificate(
        "ingress", authorization_sha, COMMIT, attempt,
        bindings["snapshot_copy_manifest_sha256"],
        evidence.observation_digest(observations[3]),
        {
            "source_count": len(evidence.SNAPSHOT_PATHS),
            "source_manifest_sha256": evidence.snapshot_source_manifest_digest(snapshot_pair["source_manifest"]),
            "snapshot_manifest_sha256": evidence.snapshot_copy_manifest_digest(snapshot_pair["snapshot_manifest"]),
            "source_descriptor_observation_sha256": evidence.descriptor_set_digest(source_descriptors),
            "snapshot_descriptor_observation_sha256": evidence.descriptor_set_digest(copy_descriptors),
            "container_mount_read_only": True,
        },
    )
    readiness_event = evidence.strict_json_bytes(files["attempts/{}/readiness-event.json".format(attempt)])
    result_raw = files["attempts/{}/result.json".format(attempt)]
    egress = evidence.build_certificate(
        "egress", authorization_sha, COMMIT, attempt,
        bindings["snapshot_copy_manifest_sha256"],
        evidence.observation_digest(observations[6]),
        {
            "readiness_event_sha256": evidence.readiness_event_digest(readiness_event),
            "start_observation_sha256": evidence.observation_digest(observations[6]),
            "export_observation_sha256": evidence.observation_digest(observations[4]),
            "raw_tar_sha256": evidence.sha256_hex(export_tar),
            "result_sha256": evidence.sha256_hex(result_raw),
            "result_bytes": len(result_raw),
            "release_observation_sha256": evidence.observation_digest(observations[5]),
            "ordering_valid": True,
        },
    )
    files["attempts/{}/egress-certificate.json".format(attempt)] = evidence.canonical_json_bytes(egress)
    return ingress


def reseal_candidate(files: dict, authorization_sha: str, state: dict) -> tuple:
    entries = [{"path": path, "file_type": "regular", "mode": 0o600, "link_count": 1, "bytes": len(files[path]), "sha256": evidence.sha256_hex(files[path])} for path in evidence.CANDIDATE_PAYLOAD_PATHS]
    manifest = {"schema": evidence.SCHEMAS["manifest"], "authorization_sha256": authorization_sha, "implementation_commit": COMMIT, "entries": entries}
    return manifest, publication(manifest, evidence.repository_state_digest(state))


def complete_candidate() -> tuple:
    files = {path: (evidence.canonical_json_bytes({"schema": "hsai-p01b-synthetic-unused-v1"}) if path.endswith(".json") else b"synthetic") for path in evidence.CANDIDATE_PAYLOAD_PATHS}
    user_authorization = b"synthetic authorization for hermetic regression only"
    user_sha = evidence.sha256_hex(user_authorization)
    c10_files, _, _ = semantic_c10_fixture(); files.update(c10_files)
    c07_files, bindings = semantic_c07_fixture(user_sha); files.update(c07_files)
    source_bytes = synthetic_snapshot(files, bindings)
    gate = synthetic_gate(source_bytes, bindings)
    files["authority/a3l6-gate-bundle.json"] = evidence.canonical_json_bytes(
        gate, evidence.MAX_A3L6_GATE_JSON_BYTES
    )
    files["authority/user-authorization.txt"] = user_authorization
    retained_readiness_plan = readiness_plan(user_sha)
    boundary = claim_boundary()
    action = evidence.build_gateway_action_document(
        user_authorization, COMMIT, TREE, gate, retained_readiness_plan, boundary
    )
    policy = evidence.build_gateway_policy_document(
        COMMIT, TREE, retained_readiness_plan, boundary
    )
    evidence_bundle = evidence.build_gateway_evidence_bundle_document(action, policy)
    admission_decision = evidence.build_gateway_admission_decision_document(
        action, policy, evidence_bundle
    )
    authority_objects = {
        "action": action, "policy": policy, "evidence-bundle": evidence_bundle,
        "admission-decision": admission_decision,
    }
    for name, value in authority_objects.items(): files["authority/" + name + ".json"] = evidence.canonical_json_bytes(value)
    common = {
        "user_authorization_sha256": user_sha,
        "action_sha256": evidence.gateway_action_document_digest(action),
        "policy_sha256": evidence.gateway_policy_document_digest(policy),
        "evidence_bundle_sha256": evidence.gateway_evidence_bundle_document_digest(evidence_bundle, action, policy),
        "a3l6_gate_bundle_sha256": evidence.a3l6_gate_bundle_digest(gate),
        "admission_decision_sha256": evidence.gateway_admission_decision_document_digest(admission_decision, action, policy, evidence_bundle),
    }
    readiness = evidence.strict_json_bytes(files["readiness/readiness-result.json"])
    bindings["index_reference"] = "docker.io/library/python@sha256:" + bindings["index_manifest_sha256"]
    files["authority/expected-bindings.json"] = evidence.canonical_json_bytes(bindings)
    bindings_sha = evidence.expected_bindings_digest(bindings)
    preauth = {"schema": evidence.SCHEMAS["preauthorization"], **common, "predecessor_commit": COMMIT, "implementation_commit": COMMIT, "implementation_tree": TREE, "readiness_plan_sha256": evidence.readiness_plan_digest(retained_readiness_plan)}
    readiness_sha = evidence._digest("readiness_result", readiness)
    root = {"schema": evidence.SCHEMAS["authorization_root"], **common, "preauthorization_sha256": evidence.preauthorization_digest(preauth), "expected_bindings_sha256": bindings_sha, "readiness_sha256": readiness_sha, "implementation_commit": COMMIT, "implementation_tree": TREE, "authority_granted": True}
    authorization = {"schema": evidence.SCHEMAS["authorization"], "authorization_id": action["proposal"]["id"], "authorization_root_sha256": evidence.authorization_root_digest(root), **common, "expected_bindings_sha256": bindings_sha, "implementation_commit": COMMIT, "implementation_tree": TREE, "readiness_sha256": readiness_sha}
    files["readiness/preauthorization-plan.json"] = evidence.canonical_json_bytes(preauth); files["authority/authorization-root.json"] = evidence.canonical_json_bytes(root); files["readiness/authorization.json"] = evidence.canonical_json_bytes(authorization)
    authorization_sha = evidence.authorization_digest(authorization)
    plans = {
        attempt: make_attempt_plan(
            attempt, authorization_sha, bindings["platform_reference"],
            bindings["snapshot_copy_manifest_sha256"],
        )
        for attempt in ("normal", "oom")
    }
    environment = retained_readiness_plan["commands"][0]["environment"]
    prefix = execution.docker_prefix(
        environment["DOCKER_CONFIG"], "unix:///var/run/docker.sock"
    )
    campaign = execution.build_campaign_plan(
        campaign_id="campaign", authorization_sha256=authorization_sha,
        implementation_commit=COMMIT,
        readiness_plan_sha256=evidence.readiness_plan_digest(retained_readiness_plan),
        native_command=execution.build_native_command("/snapshot", environment),
        metadata_commands=execution.build_metadata_commands(prefix, environment),
        normal_plan_sha256=evidence.attempt_plan_digest(plans["normal"]),
        oom_plan_sha256=evidence.attempt_plan_digest(plans["oom"]),
    )
    files["readiness/campaign-plan.json"] = evidence.canonical_json_bytes(campaign); files["readiness/normal-plan.json"] = evidence.canonical_json_bytes(plans["normal"]); files["readiness/oom-plan.json"] = evidence.canonical_json_bytes(plans["oom"])
    reseal_campaign(files, campaign)
    synthetic_probe_results(files, bindings)
    ingress_certificates = []
    for attempt in ("normal", "oom"):
        ingress_certificates.append(
            rebind_attempt(files, attempt, plans[attempt], authorization_sha, bindings)
        )
    files["snapshot/ingress-certificates.json"] = evidence.canonical_json_bytes(ingress_certificates)
    state = repository_state()
    files["provenance/git.json"] = evidence.canonical_json_bytes(state["before"])
    plan = {"schema": evidence.SCHEMAS["prepublication_plan"], "candidate_root": "/private/tmp/p01b/p01b-candidate-campaign", "parent_identity": publication_identity(7), "staging_identity": publication_identity(8), "expected_file_count": 201, "expected_manifest_path": "/private/tmp/p01b/p01b-candidate-campaign/candidate-manifest.json", "overwrite_policy": "exclusive"}
    files["publication/prepublication-descriptor-plan.json"] = evidence.canonical_json_bytes(plan)
    files["authority/expected-bindings.json"] = evidence.canonical_json_bytes(bindings)
    manifest, publication_record = reseal_candidate(files, authorization_sha, state)
    return files, manifest, publication_record, state, bindings


def classes(closed: bool = True) -> list:
    return [{"class_id": item, "closed": closed} for item in evidence.CLASS_ORDER]


def independent_acceptance_fixture() -> dict:
    files, manifest, publication_record, state, bindings = complete_candidate()
    rows = evidence.reconstruct_published_candidate(
        files, manifest, publication_record, state, bindings
    )
    decision = evidence.build_atomic_decision(
        manifest["authorization_sha256"], COMMIT, evidence.manifest_digest(manifest),
        {item["class_id"]: item["closed"] for item in rows},
        evidence.expected_bindings_digest(bindings),
        evidence.claim_boundary_digest(bindings["claim_boundary"]),
        evidence.repository_state_digest(state),
        evidence.publication_record_digest(publication_record),
    )
    decision_raw = evidence.canonical_json_bytes(decision)
    decision_identity = publication_identity(50, 0o600)
    artifact_root = "/private/tmp/p01b-artifacts"
    manifest_sha = evidence.manifest_digest(manifest)
    decision_path = artifact_root + "/decision/" + manifest_sha + "/candidate-decision.json"
    review_root = artifact_root + "/reviews/" + manifest_sha
    challenge = bytes.fromhex("44" * 32)
    session = {
        "schema": evidence.SCHEMAS["review_session"],
        "session_id": hashlib.sha256(
            b"hsai:p01b-review-session-id:v1\0" + challenge
            + bytes.fromhex(evidence.decision_digest(decision))
        ).hexdigest(),
        "challenge_hex": challenge.hex(),
        "candidate_manifest_sha256": manifest_sha,
        "candidate_decision_sha256": evidence.decision_digest(decision),
        "decision_file_identity": decision_identity,
        "decision_file_sha256": evidence.sha256_hex(decision_raw),
        "created_monotonic_ns": 7,
    }
    session_raw = evidence.canonical_json_bytes(session)
    session_directory = review_root + "/" + session["session_id"]
    session_path = session_directory + "/review-session.json"
    durability_path = session_directory + "/review-session-durability.json"
    root_identity = publication_identity(60, 0o700)
    session_file_identity = publication_identity(62, 0o600)
    session_directory_identity = publication_identity(61, 0o700)
    inventory = [{"path": ".", "type": "directory", **root_identity}]
    absence = {
        "path": session_directory, "parent_identity": root_identity,
        "started_monotonic_ns": 5, "ended_monotonic_ns": 6,
        "result": -1, "errno": 2,
    }
    events = [
        {"ordinal": 0, "operation": "decision-reopen", "target": decision_path,
         "started_monotonic_ns": 3, "ended_monotonic_ns": 4, "result": 0,
         "errno": 0, "identity": decision_identity,
         "sha256": evidence.sha256_hex(decision_raw)},
        {"ordinal": 1, "operation": "review-session-path-absence",
         "target": session_directory, "started_monotonic_ns": 5,
         "ended_monotonic_ns": 6, "result": -1, "errno": 2,
         "identity": None, "sha256": None},
        {"ordinal": 2, "operation": "review-session-file-fsync",
         "target": session_path, "started_monotonic_ns": 8,
         "ended_monotonic_ns": 9, "result": 0, "errno": 0,
         "identity": session_file_identity,
         "sha256": evidence.sha256_hex(session_raw)},
        {"ordinal": 3, "operation": "review-session-parent-fsync",
         "target": session_directory, "started_monotonic_ns": 10,
         "ended_monotonic_ns": 11, "result": 0, "errno": 0,
         "identity": session_directory_identity, "sha256": None},
    ]
    durability_value = {
        "schema": evidence.SCHEMAS["review_session_durability"],
        "review_session_sha256": evidence.review_session_digest(session),
        "decision_file_identity": decision_identity,
        "review_root_path": review_root,
        "review_root_identity": root_identity,
        "review_root_inventory_started_monotonic_ns": 1,
        "review_root_inventory_ended_monotonic_ns": 2,
        "review_root_inventory_before": inventory,
        "review_root_inventory_before_sha256": evidence.sha256_hex(
            evidence.canonical_json_bytes(inventory)
        ),
        "session_path_absence_observation": absence,
        "session_file_identity": session_file_identity,
        "ordered_events": events,
        "durable_monotonic_ns": 11,
    }
    durability_raw = evidence.canonical_json_bytes(durability_value)
    authorization = evidence.strict_json_bytes(files["readiness/authorization.json"])
    gate = evidence.strict_json_bytes(files["authority/a3l6-gate-bundle.json"])
    pair = evidence.strict_json_bytes(files["snapshot/source-manifest.json"])
    input_digests = {
        "review_session_sha256": evidence.review_session_digest(session),
        "review_session_durability_sha256": evidence.review_session_durability_digest(durability_value),
        "authorization_sha256": evidence.authorization_digest(authorization),
        "candidate_manifest_sha256": manifest_sha,
        "candidate_decision_sha256": evidence.decision_digest(decision),
        "expected_bindings_sha256": evidence.expected_bindings_digest(bindings),
        "claim_boundary_sha256": evidence.claim_boundary_digest(bindings["claim_boundary"]),
        "repository_state_sha256": evidence.repository_state_digest(state),
        "publication_record_sha256": evidence.publication_record_digest(publication_record),
        "a3l6_gate_bundle_sha256": evidence.a3l6_gate_bundle_digest(gate),
        "validator_sha256": bindings["validator_sha256"],
        "collector_sha256": bindings["collector_sha256"],
    }
    pair_contexts = []
    for index, (role, reviewer) in enumerate(zip(evidence.REVIEW_ROLE_ORDER, ("reviewer-a", "reviewer-b"))):
        receipt_path = session_directory + "/" + role + "/fresh-validation-receipt.json"
        review_path = session_directory + "/" + role + "/review.json"
        paths = {
            "snapshot_root": "/snapshot", "candidate_root": publication_record["final_path"],
            "publication_record": artifact_root + "/publication/" + manifest_sha + "/publication-record.json",
            "repository_state": artifact_root + "/publication/" + manifest_sha + "/repository-state.json",
            "candidate_decision": decision_path,
            "expected_bindings": publication_record["final_path"] + "/authority/expected-bindings.json",
            "review_session": session_path,
            "review_session_durability": durability_path,
            "receipt_output": receipt_path, "review_output": review_path,
        }
        receipt = {
            "schema": evidence.SCHEMAS["fresh_validation"], "role": role,
            "reviewer_id": reviewer,
            "review_session_sha256": input_digests["review_session_sha256"],
            "review_session_durability_sha256": input_digests["review_session_durability_sha256"],
            "process_id": 100 + index,
            "python_path": "/usr/bin/python3", "python_sha256": evidence.NATIVE_PYTHON_SHA256,
            "python_version": "3.9.6", "argv": [],
            "environment": copy.deepcopy(evidence.REVIEW_ENVIRONMENT), "cwd": "/", "stdin_policy": "closed",
            "python_descriptor_observation": descriptor("review-python", "/usr/bin/python3") | {"sha256": evidence.NATIVE_PYTHON_SHA256},
            "snapshot_copy_manifest_sha256": bindings["snapshot_copy_manifest_sha256"],
            "validator_path": "/snapshot/tools/hsai-formal-preflight/p01b_container_evidence.py",
            "validator_sha256": bindings["validator_sha256"],
            "collector_path": "/snapshot/tools/hsai-formal-preflight/p01b_container_execution.py",
            "collector_sha256": bindings["collector_sha256"],
            "started_monotonic_ns": 21 + index * 10,
            "ended_monotonic_ns": 22 + index * 10,
            "input_digests": copy.deepcopy(input_digests),
            "reconstructed_class_results": copy.deepcopy(rows), "result": "accept",
        }
        receipt["argv"] = evidence._expected_review_argv(receipt, paths, COMMIT)
        receipt_raw = evidence.canonical_json_bytes(receipt)
        review = {
            "schema": evidence.SCHEMAS["review"], "role": role,
            "reviewer_id": reviewer,
            "review_session_sha256": input_digests["review_session_sha256"],
            "review_session_durability_sha256": input_digests["review_session_durability_sha256"],
            "candidate_manifest_sha256": manifest_sha,
            "candidate_decision_sha256": input_digests["candidate_decision_sha256"],
            "implementation_commit": COMMIT,
            "expected_bindings_sha256": input_digests["expected_bindings_sha256"],
            "claim_boundary_sha256": input_digests["claim_boundary_sha256"],
            "repository_state_sha256": input_digests["repository_state_sha256"],
            "publication_record_sha256": input_digests["publication_record_sha256"],
            "validator_sha256": bindings["validator_sha256"],
            "collector_sha256": bindings["collector_sha256"],
            "fresh_validation_receipt_sha256": evidence.fresh_validation_receipt_digest(receipt),
            "reconstructed_class_results": copy.deepcopy(rows),
            "findings": [], "result": "accept",
        }
        review_raw = evidence.canonical_json_bytes(review)
        empty = b""
        observation = {
            "role": "review-v2", "argv": copy.deepcopy(receipt["argv"]),
            "environment": copy.deepcopy(evidence.REVIEW_ENVIRONMENT), "cwd": "/",
            "stdin_policy": "closed", "executable_path": "/usr/bin/python3",
            "executable_sha256": evidence.NATIVE_PYTHON_SHA256,
            "timeout_ns": 60_000_000_000, "stdout_cap_bytes": 16_384,
            "stderr_cap_bytes": 16_384,
            "started_monotonic_ns": 20 + index * 10,
            "ended_monotonic_ns": 23 + index * 10,
            "outcome": "completed", "exit_code": 0, "signal": None,
            "stdout_total_bytes": 0, "stdout_retained_bytes": 0,
            "stdout_truncated": False, "stdout_base64": b64(empty),
            "stdout_sha256": evidence.sha256_hex(empty),
            "stderr_total_bytes": 0, "stderr_retained_bytes": 0,
            "stderr_truncated": False, "stderr_base64": b64(empty),
            "stderr_sha256": evidence.sha256_hex(empty),
        }
        launch_value = {
            "schema": evidence.SCHEMAS["review_launch"],
            "review_session_sha256": input_digests["review_session_sha256"],
            "review_session_durability_sha256": input_digests["review_session_durability_sha256"],
            "claim_boundary_sha256": input_digests["claim_boundary_sha256"],
            "role": role, "reviewer_id": reviewer,
            "command_observation": observation,
            "receipt_path": receipt_path, "receipt_bytes": len(receipt_raw),
            "receipt_sha256": evidence.sha256_hex(receipt_raw),
            "receipt_domain_sha256": evidence.fresh_validation_receipt_digest(receipt),
            "review_path": review_path, "review_bytes": len(review_raw),
            "review_sha256": evidence.sha256_hex(review_raw),
            "review_domain_sha256": evidence.review_record_digest(review),
        }
        pair_contexts.append({
            "receipt": receipt, "receipt_raw": receipt_raw,
            "review": review, "review_raw": review_raw, "launch": launch_value,
            "expected_argv": copy.deepcopy(receipt["argv"]), "expected_paths": paths,
        })
    aggregate = evidence.reconstruct_review_aggregate(
        [item["review"] for item in pair_contexts],
        [item["receipt"] for item in pair_contexts],
        [item["launch"] for item in pair_contexts],
    )
    acceptance = evidence.build_acceptance_record(
        aggregate, evidence.decision_digest(decision)
    )
    return {
        "files": files, "manifest": manifest, "publication": publication_record,
        "repository": state, "bindings": bindings, "authorization": authorization,
        "gate": gate, "snapshot_copy_manifest": pair["snapshot_manifest"],
        "decision": decision, "decision_raw": decision_raw,
        "decision_identity": decision_identity, "session": session,
        "session_raw": session_raw, "durability": durability_value,
        "durability_raw": durability_raw, "rows": rows,
        "pair_contexts": pair_contexts, "aggregate": aggregate,
        "aggregate_raw": evidence.canonical_json_bytes(aggregate),
        "acceptance": acceptance,
        "acceptance_raw": evidence.canonical_json_bytes(acceptance),
        "session_paths": {"decision": decision_path, "review_root": review_root,
                          "review_session": session_path,
                          "review_session_durability": durability_path},
    }


def validate_independent_acceptance_fixture(value: dict) -> dict:
    return evidence.validate_acceptance_graph(
        value["acceptance"], value["acceptance_raw"],
        value["aggregate"], value["aggregate_raw"], value["pair_contexts"],
        review_session=value["session"], review_session_raw=value["session_raw"],
        review_session_durability=value["durability"],
        review_session_durability_raw=value["durability_raw"],
        candidate_decision=value["decision"], candidate_decision_raw=value["decision_raw"],
        decision_file_identity=value["decision_identity"],
        authorization=value["authorization"], candidate_manifest=value["manifest"],
        expected_bindings=value["bindings"], repository_state=value["repository"],
        publication_record=value["publication"], a3l6_gate_bundle=value["gate"],
        snapshot_copy_manifest=value["snapshot_copy_manifest"],
        candidate_files=value["files"],
        reconstructed_class_results=value["rows"], session_paths=value["session_paths"],
    )


class CanonicalAndBoundaryTests(unittest.TestCase):
    def test_01_all_corrected_domain_vectors(self) -> None:
        evidence.verify_domain_vectors()
        self.assertEqual(len(evidence.DOMAIN_VECTORS), 56)

    def test_02_canonical_ascii_sorted_compact(self) -> None:
        self.assertEqual(evidence.canonical_json_bytes({"z": 1, "a": "é"}), b'{"a":"\\u00e9","z":1}')

    def test_03_duplicate_newline_and_noncanonical_json_reject(self) -> None:
        for raw in (b'{"a":1,"a":2}', b'{"a":1}\n', b'{"z":1,"a":2}'):
            with self.subTest(raw=raw), self.assertRaises(evidence.EvidenceError):
                evidence.strict_json_bytes(raw)
        ordinary, ordinary_raw = sized_canonical_json(
            "hsai-p01b-ordinary-protocol-v1", evidence.MAX_JSON_BYTES + 1
        )
        with self.assertRaises(evidence.EvidenceError):
            evidence.canonical_json_bytes(ordinary)
        with self.assertRaises(evidence.EvidenceError):
            evidence.strict_json_bytes(ordinary_raw)
        with self.assertRaises(evidence.EvidenceError):
            evidence.domain_sha256("hsai:test:ordinary:v1", ordinary)
        for kind in ("a3l6_gate_source", "a3l6_gate_bundle"):
            value, raw = sized_canonical_json(
                evidence.SCHEMAS[kind], evidence.MAX_A3L6_GATE_JSON_BYTES
            )
            self.assertEqual(
                evidence.canonical_json_bytes(
                    value, evidence.MAX_A3L6_GATE_JSON_BYTES
                ),
                raw,
            )
            self.assertEqual(
                evidence.strict_json_bytes(
                    raw, evidence.MAX_A3L6_GATE_JSON_BYTES
                ),
                value,
            )
            self.assertEqual(
                evidence._digest(kind, value),
                evidence.domain_sha256(
                    evidence.DOMAINS[kind], value,
                    evidence.MAX_A3L6_GATE_JSON_BYTES,
                ),
            )
            over, over_raw = sized_canonical_json(
                evidence.SCHEMAS[kind],
                evidence.MAX_A3L6_GATE_JSON_BYTES + 1,
            )
            with self.assertRaises(evidence.EvidenceError):
                evidence.canonical_json_bytes(
                    over, evidence.MAX_A3L6_GATE_JSON_BYTES
                )
            with self.assertRaises(evidence.EvidenceError):
                evidence.strict_json_bytes(
                    over_raw, evidence.MAX_A3L6_GATE_JSON_BYTES
                )
            with self.assertRaises(evidence.EvidenceError):
                evidence._digest(kind, over)
        source_bytes = {path: b"x\n" for path in evidence.SNAPSHOT_PATHS}
        source_bytes[evidence.SNAPSHOT_PATHS[0]] = b"x" * 780_000
        bindings = expected_bindings()
        bundle = synthetic_gate(source_bytes, bindings)
        source = bundle["gate_source_manifest"]
        source_raw = evidence.canonical_json_bytes(
            source, evidence.MAX_A3L6_GATE_JSON_BYTES
        )
        bundle_raw = evidence.canonical_json_bytes(
            bundle, evidence.MAX_A3L6_GATE_JSON_BYTES
        )
        for value, raw in ((source, source_raw), (bundle, bundle_raw)):
            self.assertGreater(len(raw), evidence.MAX_JSON_BYTES)
            self.assertLessEqual(len(raw), evidence.MAX_A3L6_GATE_JSON_BYTES)
            self.assertEqual(
                evidence.strict_json_bytes(
                    raw, evidence.MAX_A3L6_GATE_JSON_BYTES
                ),
                value,
            )
        evidence.validate_a3l6_gate_source(source)
        evidence.validate_a3l6_gate_bundle(bundle, bindings)

    def test_04_exact_claim_boundary_accepts(self) -> None:
        evidence.validate_claim_boundary(claim_boundary())

    def test_05_reordered_honesty_assumptions_reject(self) -> None:
        value = claim_boundary(); value["ordered_honesty_assumptions"].reverse()
        with self.assertRaises(evidence.EvidenceError): evidence.validate_claim_boundary(value)

    def test_06_missing_nonclaim_rejects(self) -> None:
        value = claim_boundary(); value["ordered_nonclaims"].pop()
        with self.assertRaises(evidence.EvidenceError): evidence.validate_claim_boundary(value)


class DescriptorReadinessProbeTests(unittest.TestCase):
    def test_07_descriptor_identity_accepts(self) -> None:
        evidence.validate_descriptor_observation(descriptor())
        review_python = descriptor("review-python", "/usr/bin/python3")
        review_python["before"]["link_count"] = 78
        review_python["after"]["link_count"] = 78
        evidence.validate_descriptor_observation(review_python)

    def test_08_descriptor_drift_and_hardlink_reject(self) -> None:
        value = descriptor(); value["after"]["inode"] = 9
        with self.assertRaises(evidence.EvidenceError): evidence.validate_descriptor_observation(value)
        value = descriptor(); value["before"]["link_count"] = value["after"]["link_count"] = 2
        with self.assertRaises(evidence.EvidenceError): evidence.validate_descriptor_observation(value)
        value = descriptor("review-python", "/usr/bin/python3")
        value["before"]["link_count"] = value["after"]["link_count"] = 0
        with self.assertRaises(evidence.EvidenceError): evidence.validate_descriptor_observation(value)
        value = descriptor("review-python", "/usr/bin/python3")
        value["before"]["link_count"] = 78
        value["after"]["link_count"] = 77
        with self.assertRaises(evidence.EvidenceError): evidence.validate_descriptor_observation(value)
        value = descriptor("host-tool", "/usr/bin/python3")
        value["before"]["link_count"] = value["after"]["link_count"] = 78
        with self.assertRaises(evidence.EvidenceError): evidence.validate_descriptor_observation(value)

    def test_09_descriptor_sets_enforce_kind_specific_census_and_order(self) -> None:
        rows = [descriptor(path=path) for path in ("/a", "/b", "/c")]
        evidence.validate_descriptor_set({"schema": evidence.SCHEMAS["descriptor_set"], "kind": "host-tools", "ordered_observations": rows})
        rows.reverse()
        with self.assertRaises(evidence.EvidenceError): evidence.validate_descriptor_set({"schema": evidence.SCHEMAS["descriptor_set"], "kind": "host-tools", "ordered_observations": rows})

        snapshot_rows = [
            descriptor("snapshot", "/snapshot/" + path, path)
            for path in evidence.SNAPSHOT_PATHS
        ]
        evidence.validate_descriptor_set(
            {
                "schema": evidence.SCHEMAS["snapshot_descriptor"],
                "kind": "snapshot",
                "manifest_sha256": SHA,
                "ordered_observations": snapshot_rows,
            }
        )
        with self.assertRaises(evidence.EvidenceError):
            evidence.validate_descriptor_set(
                {
                    "schema": evidence.SCHEMAS["snapshot_descriptor"],
                    "kind": "snapshot",
                    "manifest_sha256": SHA,
                    "ordered_observations": snapshot_rows[:-1],
                }
            )

    def test_10_readiness_v2_requires_six_fixed_roles(self) -> None:
        evidence.validate_readiness_plan(readiness_plan())
        value = readiness_plan(); value["commands"].pop()
        with self.assertRaises(evidence.EvidenceError): evidence.validate_readiness_plan(value)

    def test_11_readiness_result_failure_vocabulary_is_closed(self) -> None:
        evidence.validate_readiness_result(readiness_result())
        value = readiness_result(); value["failure"] = "network_failed"
        with self.assertRaises(evidence.EvidenceError): evidence.validate_readiness_result(value)

    def test_12_probe_v2_rejects_schema_or_missing_raw_inputs(self) -> None:
        for value in ({"schema": "hsai-p01b-probe-result-v1"}, {"schema": evidence.SCHEMAS["probe_result"], "mode": "normal"}):
            with self.assertRaises(evidence.EvidenceError): evidence.validate_probe_result(value, "normal")


class InspectTests(unittest.TestCase):
    def test_13_prestart_evaluates_complete_frozen_56_field_list(self) -> None:
        raw, expected = inspect_pair("prestart")
        self.assertEqual(tuple(expected), evidence.INSPECT_FIELDS)
        self.assertEqual(len(evidence.validate_inspect_evaluation(raw, expected, "prestart")), 56)

    def test_14_networks_requires_only_explicit_none_endpoint(self) -> None:
        raw, expected = inspect_pair("prestart")
        expected["NetworkSettings.Networks"]["bridge"] = copy.deepcopy(expected["NetworkSettings.Networks"]["none"])
        raw["NetworkSettings"]["Networks"] = expected["NetworkSettings.Networks"]
        with self.assertRaises(evidence.EvidenceError): evidence.validate_inspect_evaluation(raw, expected, "prestart")

    def test_15_terminal_network_transition_and_state(self) -> None:
        raw, expected = inspect_pair("terminal")
        evidence.validate_inspect_evaluation(raw, expected, "terminal")
        expected["NetworkSettings.Networks"]["none"]["EndpointID"] = SHA
        raw["NetworkSettings"]["Networks"] = expected["NetworkSettings.Networks"]
        with self.assertRaises(evidence.EvidenceError): evidence.validate_inspect_evaluation(raw, expected, "terminal")


class CandidateTests(unittest.TestCase):
    def test_16_exact_candidate_grammar_has_200_payloads(self) -> None:
        self.assertEqual((len(evidence.CANDIDATE_PAYLOAD_PATHS), len(set(evidence.CANDIDATE_PAYLOAD_PATHS))), (200, 200))
        self.assertNotIn("candidate-manifest.json", evidence.CANDIDATE_PAYLOAD_PATHS)

    def test_17_expected_bindings_exact_fields_and_constants(self) -> None:
        evidence.validate_expected_bindings(expected_bindings())
        value = expected_bindings(); value["candidate_payload_count"] = 199
        with self.assertRaises(evidence.EvidenceError): evidence.validate_expected_bindings(value)

    def test_18_manifest_exact_200_sorted_paths(self) -> None:
        _, manifest, _ = candidate(); evidence.validate_candidate_manifest(manifest)
        manifest["entries"].reverse()
        with self.assertRaises(evidence.EvidenceError): evidence.validate_candidate_manifest(manifest)

    def test_19_prepublication_validates_bytes_without_classes(self) -> None:
        files, manifest, bindings = candidate()
        result = evidence.validate_prepublication_candidate(files, manifest, bindings)
        self.assertEqual(result["payload_count"], 200)
        self.assertNotIn("class_results", result)
        retained_path = "snapshot/files/tools/hsai-formal-preflight/p01b_container_seccomp.json"
        retained_raw = b'{\n  "defaultAction": "SCMP_ACT_ERRNO"\n}\n'
        files[retained_path] = retained_raw
        retained_entry = next(
            item for item in manifest["entries"] if item["path"] == retained_path
        )
        retained_entry["bytes"] = len(retained_raw)
        retained_entry["sha256"] = evidence.sha256_hex(retained_raw)
        evidence.validate_prepublication_candidate(files, manifest, bindings)

        large_bundle, large_bundle_raw = sized_canonical_json(
            evidence.SCHEMAS["a3l6_gate_bundle"],
            evidence.MAX_JSON_BYTES + 1,
        )
        files, manifest, bindings = candidate()
        files[evidence.A3L6_GATE_BUNDLE_PATH] = large_bundle_raw
        bundle_entry = next(
            item for item in manifest["entries"]
            if item["path"] == evidence.A3L6_GATE_BUNDLE_PATH
        )
        bundle_entry["bytes"] = len(large_bundle_raw)
        bundle_entry["sha256"] = evidence.sha256_hex(large_bundle_raw)
        evidence.validate_prepublication_candidate(files, manifest, bindings)
        self.assertEqual(
            evidence._semantic_json(
                {evidence.A3L6_GATE_BUNDLE_PATH: large_bundle_raw},
                evidence.A3L6_GATE_BUNDLE_PATH,
            ),
            large_bundle,
        )

        files, manifest, bindings = candidate()
        ordinary_path = "authority/action.json"
        files[ordinary_path] = large_bundle_raw
        ordinary_entry = next(
            item for item in manifest["entries"]
            if item["path"] == ordinary_path
        )
        ordinary_entry["bytes"] = len(large_bundle_raw)
        ordinary_entry["sha256"] = evidence.sha256_hex(large_bundle_raw)
        with self.assertRaises(evidence.EvidenceError):
            evidence.validate_prepublication_candidate(files, manifest, bindings)
        with self.assertRaises(evidence.EvidenceError):
            evidence._semantic_json(
                {ordinary_path: large_bundle_raw}, ordinary_path
            )

        _, over_bundle_raw = sized_canonical_json(
            evidence.SCHEMAS["a3l6_gate_bundle"],
            evidence.MAX_A3L6_GATE_JSON_BYTES + 1,
        )
        files, manifest, bindings = candidate()
        files[evidence.A3L6_GATE_BUNDLE_PATH] = over_bundle_raw
        bundle_entry = next(
            item for item in manifest["entries"]
            if item["path"] == evidence.A3L6_GATE_BUNDLE_PATH
        )
        bundle_entry["bytes"] = len(over_bundle_raw)
        bundle_entry["sha256"] = evidence.sha256_hex(over_bundle_raw)
        with self.assertRaises(evidence.EvidenceError):
            evidence.validate_prepublication_candidate(files, manifest, bindings)

    def test_20_candidate_extra_or_missing_path_rejects(self) -> None:
        files, manifest, bindings = candidate(); files["extra"] = b"x"
        with self.assertRaises(evidence.EvidenceError): evidence.validate_prepublication_candidate(files, manifest, bindings)

    def test_21_payload_hash_or_expected_binding_bytes_reject(self) -> None:
        files, manifest, bindings = candidate(); files["authority/action.json"] = b'{"changed":true}'
        with self.assertRaises(evidence.EvidenceError): evidence.validate_prepublication_candidate(files, manifest, bindings)
        files, manifest, bindings = candidate(); files["authority/expected-bindings.json"] = b"{}"
        with self.assertRaises(evidence.EvidenceError): evidence.validate_prepublication_candidate(files, manifest, bindings)
        files, manifest, bindings = candidate()
        protocol_path = "authority/action.json"
        files[protocol_path] = b"{\n}\n"
        protocol_entry = next(
            item for item in manifest["entries"] if item["path"] == protocol_path
        )
        protocol_entry["bytes"] = len(files[protocol_path])
        protocol_entry["sha256"] = evidence.sha256_hex(files[protocol_path])
        with self.assertRaises(evidence.EvidenceError):
            evidence.validate_prepublication_candidate(files, manifest, bindings)


class PublicationRepositoryDecisionTests(unittest.TestCase):
    def test_22_repository_state_reconstructs_unchanged_transcripts(self) -> None:
        value = repository_state()
        self.assertNotEqual(
            value["before"]["ordered_commands"][0]["started_monotonic_ns"],
            value["after"]["ordered_commands"][0]["started_monotonic_ns"],
        )
        evidence.validate_repository_state(value)

    def test_23_repository_after_capture_drift_rejects(self) -> None:
        value = repository_state(); value["after"]["ordered_commands"][2]["stdout_base64"] = b64(b"")
        with self.assertRaises(evidence.EvidenceError): evidence.validate_repository_state(value)

    def test_24_publication_requires_201_reopens_and_270_events(self) -> None:
        _, manifest, _ = candidate(); state = repository_state()
        evidence.validate_publication_record(publication(manifest, evidence.repository_state_digest(state)))
        directories = evidence._candidate_directory_order()
        self.assertEqual(directories[-1], ".")
        self.assertEqual(
            [len(path.split("/")) if path != "." else 0 for path in directories],
            sorted(
                [len(path.split("/")) if path != "." else 0 for path in directories],
                reverse=True,
            ),
        )

    def test_25_resealed_publication_event_matrix_closes_c09_false(self) -> None:
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        _, synthetic_bindings = semantic_c07_fixture()
        evidence.INDEX_REFERENCE = (
            "docker.io/library/python@sha256:"
            + synthetic_bindings["index_manifest_sha256"]
        )
        evidence.DOCKER_CONTEXT_SHA256 = synthetic_bindings["docker_context_sha256"]
        try:
            files, manifest, published, state, bindings = complete_candidate()
            alternate_file_identity = publication_identity(9001, 0o600)
            alternate_directory_identity = publication_identity(9002, 0o700)
            mutations = (
                ("ordinal", 0, "ordinal", 1),
                ("payload-operation", 0, "operation", "alternate-operation"),
                ("rename-operation", 264, "operation", "rename"),
                ("payload-target", 0, "target", evidence.CANDIDATE_PAYLOAD_PATHS[1]),
                ("manifest-target", 200, "target", "authority/action.json"),
                ("directory-target", 201, "target", evidence._candidate_directory_order()[1]),
                ("preinventory-target", 263, "target", "authority"),
                ("rename-target", 264, "target", {"source": "other", "destination": "other-final"}),
                ("parent-target", 265, "target", "/private/tmp/other"),
                ("staging-target", 266, "target", "other-staging"),
                ("final-root-target", 267, "target", "other-final"),
                ("postinventory-target", 268, "target", "authority"),
                ("final-manifest-target", 269, "target", "authority/action.json"),
                ("payload-flags", 0, "flags", ["OTHER"]),
                ("directory-flags", 201, "flags", ["OTHER"]),
                ("rename-flags", 264, "flags", []),
                ("terminal-flags", 263, "flags", ["OTHER"]),
                ("negative-start", 0, "started_monotonic_ns", -1),
                ("empty-duration", 0, "ended_monotonic_ns", 1),
                ("event-overlap", 1, "started_monotonic_ns", 1),
                ("success-result", 0, "result", 1),
                ("success-errno", 0, "errno", 1),
                ("rename-result", 264, "result", 1),
                ("rename-errno", 264, "errno", 1),
                ("absence-result", 266, "result", 0),
                ("absence-errno", 266, "errno", 0),
                ("payload-identity", 0, "identity", alternate_file_identity),
                ("manifest-identity", 200, "identity", alternate_file_identity),
                ("directory-identity-kind", 201, "identity", alternate_file_identity),
                ("root-fsync-identity", 262, "identity", alternate_directory_identity),
                ("preinventory-identity", 263, "identity", alternate_directory_identity),
                ("rename-identity-nullability", 264, "identity", alternate_directory_identity),
                ("parent-identity", 265, "identity", alternate_directory_identity),
                ("absence-identity-nullability", 266, "identity", alternate_directory_identity),
                ("final-root-identity", 267, "identity", alternate_directory_identity),
                ("postinventory-identity", 268, "identity", alternate_directory_identity),
                ("final-manifest-identity", 269, "identity", alternate_file_identity),
                ("payload-sha", 0, "sha256", SHA_B),
                ("manifest-raw-sha", 200, "sha256", SHA_B),
                ("directory-sha-nullability", 201, "sha256", SHA_B),
                ("preinventory-sha", 263, "sha256", SHA_B),
                ("rename-sha-nullability", 264, "sha256", SHA_B),
                ("parent-sha-nullability", 265, "sha256", SHA_B),
                ("absence-sha-nullability", 266, "sha256", SHA_B),
                ("final-root-sha-nullability", 267, "sha256", SHA_B),
                ("postinventory-sha", 268, "sha256", SHA_B),
                ("final-manifest-domain-sha", 269, "sha256", SHA_B),
            )
            for name, ordinal, field, changed in mutations:
                with self.subTest(name=name):
                    tampered = copy.deepcopy(published)
                    tampered["ordered_publication_events"][ordinal][field] = copy.deepcopy(changed)
                    with self.assertRaises(evidence.EvidenceError):
                        evidence.validate_publication_record(tampered)
                    rows = evidence.reconstruct_published_candidate(
                        files, manifest, tampered, state, bindings
                    )
                    class_results = {
                        item["class_id"]: item["closed"] for item in rows
                    }
                    self.assertFalse(class_results["C09"])
                    self.assertTrue(
                        all(
                            class_results[class_id]
                            for class_id in evidence.CLASS_ORDER
                            if class_id != "C09"
                        )
                    )
                    decision = evidence.build_atomic_decision(
                        manifest["authorization_sha256"],
                        COMMIT,
                        evidence.manifest_digest(manifest),
                        class_results,
                        evidence.expected_bindings_digest(bindings),
                        evidence.claim_boundary_digest(bindings["claim_boundary"]),
                        evidence.repository_state_digest(state),
                        evidence.domain_sha256(
                            evidence.DOMAINS["publication"], tampered
                        ),
                    )
                    self.assertEqual(decision["atomic_result"], "reject")
                    self.assertFalse(decision["authority_granted"])
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context

    def test_26_v3_decision_is_all_or_nothing_and_false_authority(self) -> None:
        results = {name: True for name in evidence.CLASS_ORDER}
        value = evidence.build_atomic_decision(SHA, COMMIT, SHA_B, results, SHA, SHA, SHA, SHA)
        self.assertEqual(value["atomic_result"], "accept")
        results["C07"] = False
        value = evidence.build_atomic_decision(SHA, COMMIT, SHA_B, results, SHA, SHA, SHA, SHA)
        self.assertEqual(value["atomic_result"], "reject")
        self.assertFalse(value["authority_granted"])

    def test_27_public_dispatch_closes_non_authority_classes_and_resealed_tamper_rejects_atomically(self) -> None:
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        _, synthetic_bindings = semantic_c07_fixture()
        evidence.INDEX_REFERENCE = "docker.io/library/python@sha256:" + synthetic_bindings["index_manifest_sha256"]
        evidence.DOCKER_CONTEXT_SHA256 = synthetic_bindings["docker_context_sha256"]
        try:
            files, manifest, published, state, bindings = complete_candidate()
            rows = evidence.reconstruct_published_candidate(files, manifest, published, state, bindings)
            self.assertEqual(rows, [{"class_id": name, "closed": True} for name in evidence.CLASS_ORDER])

            def mutate(target: str, candidate_files: dict) -> None:
                if target == "C02":
                    value = evidence.strict_json_bytes(candidate_files["reference/native-result.json"]); value["mode"] = "normal"
                    candidate_files["reference/native-result.json"] = evidence.canonical_json_bytes(value)
                elif target == "C03":
                    value = evidence.strict_json_bytes(candidate_files["attempts/oom/result.json"]); value["workload"]["barrier_transcript_base64"] = b64(b"wrong\n")
                    candidate_files["attempts/oom/result.json"] = evidence.canonical_json_bytes(value)
                elif target == "C04":
                    value = evidence.strict_json_bytes(candidate_files["attempts/normal/result.json"])
                    value["security"]["status_base64"] = b64(base64.b64decode(value["security"]["status_base64"]).replace(b"Seccomp:\t2", b"Seccomp:\t0"))
                    candidate_files["attempts/normal/result.json"] = evidence.canonical_json_bytes(value)
                elif target == "C05":
                    value = evidence.strict_json_bytes(candidate_files["attempts/normal/result.json"])
                    value["cgroup_terminal"]["raw_files_base64"]["pids.events"] = b64(b"max 1\n")
                    value["cgroup_terminal"]["files"]["pids.events"]["max"] = 1
                    candidate_files["attempts/normal/result.json"] = evidence.canonical_json_bytes(value)
                elif target == "C06":
                    value = evidence.strict_json_bytes(candidate_files["authority/a3l6-gate-bundle.json"]); value["result"] = "reject"
                    candidate_files["authority/a3l6-gate-bundle.json"] = evidence.canonical_json_bytes(value)
                elif target == "C07":
                    value = evidence.strict_json_bytes(candidate_files["provenance/rootfs.json"]); value["facts"]["ordered_diff_ids"].reverse()
                    candidate_files["provenance/rootfs.json"] = evidence.canonical_json_bytes(value)
                elif target == "C09":
                    raw = bytearray(candidate_files["attempts/normal/export.tar"]); raw[257] ^= 1
                    candidate_files["attempts/normal/export.tar"] = bytes(raw)
                else:
                    value = evidence.strict_json_bytes(candidate_files["authority/authorization-root.json"]); value["authority_granted"] = False
                    candidate_files["authority/authorization-root.json"] = evidence.canonical_json_bytes(value)

            for target in evidence.CLASS_ORDER:
                with self.subTest(target=target):
                    tampered = copy.deepcopy(files); mutate(target, tampered)
                    tampered_manifest, tampered_publication = reseal_candidate(tampered, manifest["authorization_sha256"], state)
                    tampered_rows = evidence.reconstruct_published_candidate(tampered, tampered_manifest, tampered_publication, state, bindings)
                    self.assertFalse(dict((item["class_id"], item["closed"]) for item in tampered_rows)[target])
                    decision = evidence.build_atomic_decision(manifest["authorization_sha256"], COMMIT, evidence.manifest_digest(tampered_manifest), dict((item["class_id"], item["closed"]) for item in tampered_rows), evidence.expected_bindings_digest(bindings), evidence.claim_boundary_digest(bindings["claim_boundary"]), evidence.repository_state_digest(state), evidence.publication_record_digest(tampered_publication))
                    self.assertEqual(decision["atomic_result"], "reject")
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context


class IndependentAcceptanceTests(unittest.TestCase):
    def test_28_review_session_id_reconstructs_challenge_and_decision(self) -> None:
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        _, synthetic_bindings = semantic_c07_fixture()
        evidence.INDEX_REFERENCE = "docker.io/library/python@sha256:" + synthetic_bindings["index_manifest_sha256"]
        evidence.DOCKER_CONTEXT_SHA256 = synthetic_bindings["docker_context_sha256"]
        try:
            value = independent_acceptance_fixture()
            graph = evidence.validate_review_session_graph(
                value["session"], value["session_raw"], value["durability"],
                value["durability_raw"], value["decision"], value["decision_raw"],
                value["decision_identity"], evidence.manifest_digest(value["manifest"]),
                value["session_paths"]["decision"], value["session_paths"]["review_root"],
                value["session_paths"]["review_session"],
                value["session_paths"]["review_session_durability"],
            )
            self.assertNotEqual(
                graph["decision_file_sha256"], graph["candidate_decision_sha256"]
            )
            cases = []
            changed = copy.deepcopy(value); changed["session"]["session_id"] = SHA
            changed["session_raw"] = evidence.canonical_json_bytes(changed["session"])
            cases.append(("session-id", changed))
            changed = copy.deepcopy(value); changed["decision_raw"] += b"\n"
            cases.append(("raw-decision", changed))
            changed = copy.deepcopy(value); changed["session_paths"]["decision"] = "/private/tmp/alternate.json"
            cases.append(("decision-path", changed))
            for label, changed in cases:
                with self.subTest(group=label), self.assertRaises(evidence.EvidenceError):
                    evidence.validate_review_session_graph(
                        changed["session"], changed["session_raw"], changed["durability"],
                        changed["durability_raw"], changed["decision"], changed["decision_raw"],
                        changed["decision_identity"], evidence.manifest_digest(changed["manifest"]),
                        changed["session_paths"]["decision"], changed["session_paths"]["review_root"],
                        changed["session_paths"]["review_session"],
                        changed["session_paths"]["review_session_durability"],
                    )
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context

    def test_29_session_durability_requires_inventory_and_four_events(self) -> None:
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        _, synthetic_bindings = semantic_c07_fixture()
        evidence.INDEX_REFERENCE = "docker.io/library/python@sha256:" + synthetic_bindings["index_manifest_sha256"]
        evidence.DOCKER_CONTEXT_SHA256 = synthetic_bindings["docker_context_sha256"]
        try:
            fixture = independent_acceptance_fixture()
            evidence.validate_review_session_durability(fixture["durability"])
            cases = []
            value = copy.deepcopy(fixture["durability"]); value["ordered_events"].pop()
            cases.append(("event-census", value))
            value = copy.deepcopy(fixture["durability"]); value["ordered_events"][0]["sha256"] = None
            cases.append(("decision-sha-null", value))
            value = copy.deepcopy(fixture["durability"]); value["ordered_events"][1]["target"] = "/private/tmp/alternate"
            cases.append(("absence-target", value))
            value = copy.deepcopy(fixture["durability"])
            value["review_root_inventory_before"].append({"path": "a", "type": "symlink", **publication_identity(99, 0o777)})
            value["review_root_inventory_before_sha256"] = evidence.sha256_hex(evidence.canonical_json_bytes(value["review_root_inventory_before"]))
            cases.append(("inventory-special", value))
            for label, value in cases:
                with self.subTest(group=label), self.assertRaises(evidence.EvidenceError):
                    evidence.validate_review_session_durability(value)
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context

    def test_30_fresh_receipt_review_and_parent_launch_cross_bind(self) -> None:
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        _, synthetic_bindings = semantic_c07_fixture()
        evidence.INDEX_REFERENCE = "docker.io/library/python@sha256:" + synthetic_bindings["index_manifest_sha256"]
        evidence.DOCKER_CONTEXT_SHA256 = synthetic_bindings["docker_context_sha256"]
        try:
            fixture = independent_acceptance_fixture()
            review_python_receipt = copy.deepcopy(
                fixture["pair_contexts"][0]["receipt"]
            )
            python_descriptor = review_python_receipt[
                "python_descriptor_observation"
            ]
            python_descriptor["before"]["link_count"] = 78
            python_descriptor["after"]["link_count"] = 78
            evidence.validate_fresh_validation_receipt(review_python_receipt)
            receipt_cases = []
            value = copy.deepcopy(review_python_receipt)
            value["python_descriptor_observation"]["sha256"] = SHA
            receipt_cases.append(("review-python-hash", value))
            value = copy.deepcopy(review_python_receipt)
            value["python_descriptor_observation"]["path"] = "/usr/bin/false"
            receipt_cases.append(("review-python-path", value))
            value = copy.deepcopy(review_python_receipt)
            value["python_version"] = "3.9.7"
            receipt_cases.append(("review-python-version", value))
            for label, value in receipt_cases:
                with self.subTest(group=label), self.assertRaises(
                    evidence.EvidenceError
                ):
                    evidence.validate_fresh_validation_receipt(value)
            result = validate_independent_acceptance_fixture(fixture)
            self.assertEqual((result["closed_classes"], result["correspondence_score"]), (list(evidence.CLASS_ORDER), "10/10"))
            self.assertFalse(result["accepted_evidence_created"])
            cases = []
            value = copy.deepcopy(fixture)
            value["pair_contexts"][0]["receipt"]["argv"].append("--extra")
            value["pair_contexts"][0]["receipt_raw"] = evidence.canonical_json_bytes(value["pair_contexts"][0]["receipt"])
            cases.append(("receipt-argv", value))
            value = copy.deepcopy(fixture)
            value["pair_contexts"][0]["receipt"]["environment"]["EXTRA"] = "1"
            value["pair_contexts"][0]["receipt_raw"] = evidence.canonical_json_bytes(value["pair_contexts"][0]["receipt"])
            cases.append(("receipt-environment", value))
            value = copy.deepcopy(fixture)
            value["pair_contexts"][0]["receipt"]["validator_sha256"] = SHA
            value["pair_contexts"][0]["receipt_raw"] = evidence.canonical_json_bytes(value["pair_contexts"][0]["receipt"])
            cases.append(("validator-binding", value))
            value = copy.deepcopy(fixture)
            value["pair_contexts"][0]["review_raw"] += b"\n"
            cases.append(("review-raw", value))
            value = copy.deepcopy(fixture)
            value["aggregate"]["ordered_review_launch_sha256"].reverse()
            value["aggregate_raw"] = evidence.canonical_json_bytes(value["aggregate"])
            cases.append(("aggregate-launch-order", value))
            value = copy.deepcopy(fixture)
            value["acceptance"]["authority_granted"] = True
            value["acceptance_raw"] = evidence.canonical_json_bytes(value["acceptance"])
            cases.append(("acceptance-authority", value))
            value = copy.deepcopy(fixture)
            first_pid = value["pair_contexts"][0]["receipt"]["process_id"]
            second = value["pair_contexts"][1]
            second["receipt"]["process_id"] = first_pid
            second["receipt_raw"] = evidence.canonical_json_bytes(second["receipt"])
            second["review"]["fresh_validation_receipt_sha256"] = evidence.fresh_validation_receipt_digest(second["receipt"])
            second["review_raw"] = evidence.canonical_json_bytes(second["review"])
            second["launch"]["receipt_bytes"] = len(second["receipt_raw"])
            second["launch"]["receipt_sha256"] = evidence.sha256_hex(second["receipt_raw"])
            second["launch"]["receipt_domain_sha256"] = evidence.fresh_validation_receipt_digest(second["receipt"])
            second["launch"]["review_bytes"] = len(second["review_raw"])
            second["launch"]["review_sha256"] = evidence.sha256_hex(second["review_raw"])
            second["launch"]["review_domain_sha256"] = evidence.review_record_digest(second["review"])
            cases.append(("process-independence", value))
            value = copy.deepcopy(fixture)
            second = value["pair_contexts"][1]
            second["receipt"]["reviewer_id"] = "reviewer-a"
            second["receipt"]["argv"] = evidence._expected_review_argv(
                second["receipt"], second["expected_paths"], COMMIT
            )
            second["expected_argv"] = copy.deepcopy(second["receipt"]["argv"])
            second["receipt_raw"] = evidence.canonical_json_bytes(second["receipt"])
            second["review"]["reviewer_id"] = "reviewer-a"
            second["review"]["fresh_validation_receipt_sha256"] = evidence.fresh_validation_receipt_digest(second["receipt"])
            second["review_raw"] = evidence.canonical_json_bytes(second["review"])
            second["launch"]["reviewer_id"] = "reviewer-a"
            second["launch"]["command_observation"]["argv"] = copy.deepcopy(second["receipt"]["argv"])
            second["launch"]["receipt_bytes"] = len(second["receipt_raw"])
            second["launch"]["receipt_sha256"] = evidence.sha256_hex(second["receipt_raw"])
            second["launch"]["receipt_domain_sha256"] = evidence.fresh_validation_receipt_digest(second["receipt"])
            second["launch"]["review_bytes"] = len(second["review_raw"])
            second["launch"]["review_sha256"] = evidence.sha256_hex(second["review_raw"])
            second["launch"]["review_domain_sha256"] = evidence.review_record_digest(second["review"])
            cases.append(("reviewer-independence", value))
            for label, value in cases:
                with self.subTest(group=label), self.assertRaises(evidence.EvidenceError):
                    validate_independent_acceptance_fixture(value)
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context

    def test_31_c07_reconstructs_raw_provenance_and_rejects_resealed_rootfs_tamper(self) -> None:
        files, bindings = semantic_c07_fixture()
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        evidence.INDEX_REFERENCE = "docker.io/library/python@sha256:" + bindings["index_manifest_sha256"]
        try:
            self.assertEqual(len(PINNED_DOCKER_CONTEXT_RAW), 306)
            self.assertEqual(
                evidence.sha256_hex(PINNED_DOCKER_CONTEXT_RAW),
                original_context,
            )
            context_record = evidence.strict_json_bytes(
                files["provenance/docker-context.json"]
            )
            evidence.validate_docker_context(
                context_record, PINNED_DOCKER_CONTEXT_RAW
            )
            self.assertTrue(evidence._reconstruct_c07(files, bindings))
            tampered = copy.deepcopy(files)
            rootfs = evidence.strict_json_bytes(tampered["provenance/rootfs.json"])
            rootfs["facts"]["ordered_diff_ids"] = list(reversed(rootfs["facts"]["ordered_diff_ids"]))
            tampered["provenance/rootfs.json"] = evidence.canonical_json_bytes(rootfs)
            with self.assertRaises(evidence.EvidenceError): evidence._reconstruct_c07(tampered, bindings)

            def record(raw: bytes, host=PINNED_DOCKER_CONTEXT_HOST, skip=False) -> dict:
                observed = descriptor(
                    "docker-context", "/Users/test/.docker/contexts/meta.json"
                )
                observed["before"]["size"] = observed["after"]["size"] = len(raw)
                observed["sha256"] = evidence.sha256_hex(raw)
                return {
                    "schema": evidence.SCHEMAS["docker_context"],
                    "path": observed["path"],
                    "descriptor_observation": observed,
                    "descriptor_observation_sha256": evidence.descriptor_observation_digest(observed),
                    "bytes": len(raw), "sha256": evidence.sha256_hex(raw),
                    "name": "desktop-linux", "host": host,
                    "skip_tls_verify": skip,
                }

            def resize_description(value: dict) -> bytes:
                raw = evidence.canonical_json_bytes(value)
                delta = 306 - len(raw)
                description = value["Metadata"].get("Description", "")
                if delta >= 0:
                    value["Metadata"]["Description"] = description + "x" * delta
                else:
                    self.assertGreaterEqual(len(description), -delta)
                    value["Metadata"]["Description"] = description[:len(description) + delta]
                raw = evidence.canonical_json_bytes(value)
                self.assertEqual(len(raw), 306)
                return raw

            parsed = json.loads(PINNED_DOCKER_CONTEXT_RAW.decode("ascii"))
            semantic_cases = []
            old = {
                "Name": "desktop-linux",
                "Metadata": {
                    "Description": "Docker Desktop",
                    "GODEBUG": "x509negativeserial=1",
                    "otel": parsed["Metadata"]["otel"],
                    "Host": PINNED_DOCKER_CONTEXT_HOST,
                    "SkipTLSVerify": False,
                },
            }
            semantic_cases.append(("old-endpoint-location", resize_description(old), PINNED_DOCKER_CONTEXT_HOST, False))
            missing_top = copy.deepcopy(parsed); missing_top.pop("Endpoints")
            semantic_cases.append(("missing-top-level", resize_description(missing_top), PINNED_DOCKER_CONTEXT_HOST, False))
            extra_top = copy.deepcopy(parsed); extra_top["Extra"] = False
            semantic_cases.append(("extra-top-level", resize_description(extra_top), PINNED_DOCKER_CONTEXT_HOST, False))
            missing_endpoint = copy.deepcopy(parsed); missing_endpoint["Endpoints"]["docker"].pop("Host")
            semantic_cases.append(("missing-endpoint-field", resize_description(missing_endpoint), PINNED_DOCKER_CONTEXT_HOST, False))
            extra_endpoint = copy.deepcopy(parsed); extra_endpoint["Endpoints"]["docker"]["Extra"] = False
            semantic_cases.append(("extra-endpoint-field", resize_description(extra_endpoint), PINNED_DOCKER_CONTEXT_HOST, False))
            wrong_scheme = copy.deepcopy(parsed)
            wrong_host = PINNED_DOCKER_CONTEXT_HOST.replace("unix:///", "tcpx:///")
            wrong_scheme["Endpoints"]["docker"]["Host"] = wrong_host
            semantic_cases.append(("wrong-host-scheme", evidence.canonical_json_bytes(wrong_scheme), wrong_host, False))
            nonfalse = copy.deepcopy(parsed); nonfalse["Endpoints"]["docker"]["SkipTLSVerify"] = "yes"
            semantic_cases.append(("nonfalse-skip-tls", evidence.canonical_json_bytes(nonfalse), PINNED_DOCKER_CONTEXT_HOST, "yes"))
            for label, raw, host, skip in semantic_cases:
                self.assertEqual(len(raw), 306)
                evidence.DOCKER_CONTEXT_SHA256 = evidence.sha256_hex(raw)
                with self.subTest(group=label), self.assertRaises(evidence.EvidenceError):
                    evidence.validate_docker_context(record(raw, host, skip), raw)
            evidence.DOCKER_CONTEXT_SHA256 = original_context
            mutated_endpoint = PINNED_DOCKER_CONTEXT_RAW.replace(
                b"docker.sock", b"dockez.sock", 1
            )
            with self.subTest(group="mutated-pinned-endpoint"), self.assertRaises(evidence.EvidenceError):
                evidence.validate_docker_context(
                    record(mutated_endpoint, PINNED_DOCKER_CONTEXT_HOST.replace("docker.sock", "dockez.sock")),
                    mutated_endpoint,
                )
            with self.subTest(group="wrong-raw-bytes"), self.assertRaises(evidence.EvidenceError):
                evidence.validate_docker_context(
                    record(PINNED_DOCKER_CONTEXT_RAW + b"\n"),
                    PINNED_DOCKER_CONTEXT_RAW + b"\n",
                )
            wrong_sha = record(PINNED_DOCKER_CONTEXT_RAW)
            wrong_sha["sha256"] = SHA
            wrong_sha["descriptor_observation"]["sha256"] = SHA
            wrong_sha["descriptor_observation_sha256"] = evidence.descriptor_observation_digest(
                wrong_sha["descriptor_observation"]
            )
            with self.subTest(group="wrong-raw-sha"), self.assertRaises(evidence.EvidenceError):
                evidence.validate_docker_context(wrong_sha, PINNED_DOCKER_CONTEXT_RAW)
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context

    def test_32_a3l5h_exact_authority_reconstruction_and_grouped_negatives(self) -> None:
        original_reference = evidence.INDEX_REFERENCE
        original_context = evidence.DOCKER_CONTEXT_SHA256
        _, synthetic_bindings = semantic_c07_fixture()
        evidence.INDEX_REFERENCE = "docker.io/library/python@sha256:" + synthetic_bindings["index_manifest_sha256"]
        evidence.DOCKER_CONTEXT_SHA256 = synthetic_bindings["docker_context_sha256"]
        try:
            files, _, _, _, bindings = complete_candidate()
            snapshot = evidence._snapshot_semantics(files, bindings)
            self.assertTrue(evidence._reconstruct_c10(files, bindings, snapshot))
            authority = evidence._authorization_semantics(files, bindings, snapshot)
            handoff = authority["ephemeral_accepted_handoff"]
            self.assertEqual(
                (handoff["action_kind"], handoff["target"], handoff["value_units"]),
                ("ToolCall", evidence.P01B_PROGRAM_ID, 0),
            )
            self.assertNotIn("authority/accepted-handoff.json", evidence.CANDIDATE_PAYLOAD_PATHS)

            def reject_json(path: str, label: str, mutate) -> None:
                tampered = dict(files)
                value = evidence.strict_json_bytes(tampered[path])
                mutate(value)
                tampered[path] = evidence.canonical_json_bytes(value)
                with self.subTest(group=label), self.assertRaises(evidence.EvidenceError):
                    evidence._reconstruct_c10(tampered, bindings, snapshot)

            action_path = "authority/action.json"
            policy_path = "authority/policy.json"
            bundle_path = "authority/evidence-bundle.json"
            decision_path = "authority/admission-decision.json"

            wrapper_cases = (
                (action_path, "missing-wrapper-field", lambda value: value.pop("schema")),
                (action_path, "extra-wrapper-field", lambda value: value.update({"extra": False})),
                (action_path, "program-drift", lambda value: value.update({"program_id": "other"})),
                (action_path, "network-scope-drift", lambda value: value.update({"network_scope": "a3l9-no-network"})),
                (action_path, "enum-drift", lambda value: value["proposal"].update({"action_kind": "tool_call"})),
                (action_path, "newtype-drift", lambda value: value["proposal"].update({"id": 7})),
                (action_path, "hash-wire-drift", lambda value: value["proposal"]["source_artifact_digests"][0].update({"sha256": SHA})),
                (action_path, "source-artifact-order", lambda value: value["proposal"]["source_artifact_digests"].reverse()),
                (action_path, "nonclaim-set-order", lambda value: value["proposal"]["nonclaims"].reverse()),
                (action_path, "model-lane-zero-domain", lambda value: value["proposal"]["model_lane"].update({"input_corpus_digest": [0] * 32})),
                (action_path, "threat-drift", lambda value: value["proposal"].update({"threat_labels": ["Hostile"]})),
                (action_path, "direct-authority", lambda value: value["proposal"].update({"direct_authority_requested": True})),
                (action_path, "rust-declaration-order-digest", lambda value: value.update({"proposal_sha256": evidence.gateway_action_proposal_digest(value["proposal"])})),
                (policy_path, "policy-above-local", lambda value: value["gateway_policy"]["admission_policy"].update({"max_claim_boundary": "External"})),
                (policy_path, "policy-extra-target", lambda value: value["gateway_policy"]["allowed_targets"].append("other")),
                (policy_path, "policy-nonzero-value", lambda value: value["gateway_policy"].update({"max_value_units": 1})),
                (policy_path, "policy-source-disabled", lambda value: value["gateway_policy"]["admission_policy"].update({"require_source_artifacts": False})),
                (policy_path, "policy-provider-authority", lambda value: value["gateway_policy"]["admission_policy"].update({"allow_provider_direct_authority": True})),
                (policy_path, "policy-secret-lane", lambda value: value["gateway_policy"].update({"require_non_secret_model_lane": False})),
                (bundle_path, "candidate-policy-violations-retained", lambda value: value["candidate"].update({"gateway_policy_violations": []})),
                (bundle_path, "candidate-promotion-flag", lambda value: value["candidate"].update({"accepted_ledger_mutation_requested": True})),
                (bundle_path, "candidate-boundary-drift", lambda value: value["candidate"].update({"requested_claim_boundary": "External"})),
                (bundle_path, "p01b-for-rust-tag-substitution", lambda value: value.update({"candidate_sha256": evidence._digest("gateway_evidence_bundle", value["candidate"])})),
                (decision_path, "decision-nonaccepted", lambda value: value["decision"].update({"verdict": "Rejected"})),
                (decision_path, "decision-reasons", lambda value: value["decision"]["reasons"].append("changed")),
                (decision_path, "decision-envelope", lambda value: value["decision"].update({"accepted_envelope": {}})),
                (decision_path, "decision-candidate-hash", lambda value: value["decision"].update({"candidate_digest": [1] * 32})),
                (decision_path, "decision-policy", lambda value: value["decision"].update({"policy_id": "other"})),
            )
            for path, label, mutate in wrapper_cases:
                reject_json(path, label, mutate)

            duplicate = dict(files)
            action_raw = duplicate[action_path]
            duplicate[action_path] = b'{"schema":"duplicate",' + action_raw[1:]
            with self.subTest(group="duplicate-wrapper-field"), self.assertRaises(evidence.EvidenceError):
                evidence._reconstruct_c10(duplicate, bindings, snapshot)
            invalid_utf8 = dict(files); invalid_utf8["authority/user-authorization.txt"] = b"\xff"
            with self.subTest(group="user-authorization-utf8"), self.assertRaises(evidence.EvidenceError):
                evidence._reconstruct_c10(invalid_utf8, bindings, snapshot)

            cross_cases = (
                ("readiness/preauthorization-plan.json", "raw-file-for-domain-substitution", lambda value: value.update({"action_sha256": evidence.sha256_hex(files[action_path])})),
                ("readiness/preauthorization-plan.json", "rust-tag-for-wrapper-domain-substitution", lambda value: value.update({"action_sha256": evidence.strict_json_bytes(files[action_path])["proposal_sha256"]})),
                ("readiness/preauthorization-plan.json", "gate-cross-binding", lambda value: value.update({"a3l6_gate_bundle_sha256": SHA})),
                ("authority/authorization-root.json", "authorization-root-cross-binding", lambda value: value.update({"expected_bindings_sha256": SHA})),
                ("readiness/authorization.json", "authorization-cycle-field", lambda value: value.update({"normal_plan_sha256": SHA})),
                ("operations/readiness/000-registry-index/observation.json", "readiness-plan-cross-binding", lambda value: value.update({"plan_sha256": SHA})),
            )
            for path, label, mutate in cross_cases:
                reject_json(path, label, mutate)

            certificate_cases = (
                ("snapshot/ingress-certificates.json", "ingress-descriptor-binding", lambda value: value[0]["predicates"].update({"snapshot_descriptor_observation_sha256": SHA})),
                ("attempts/normal/inspect-prestart.json", "ingress-producer-boolean-bypass", lambda value: value[0]["Mounts"][0].update({"Source": "/alternate"})),
                ("attempts/normal/egress-certificate.json", "egress-tar-binding", lambda value: value["predicates"].update({"raw_tar_sha256": SHA})),
                ("attempts/normal/egress-certificate.json", "egress-ordering-digest", lambda value: value["predicates"].update({"export_observation_sha256": SHA})),
            )
            for path, label, mutate in certificate_cases:
                reject_json(path, label, mutate)
            tampered_tar = dict(files)
            raw_tar = bytearray(tampered_tar["attempts/normal/export.tar"])
            raw_tar[257] ^= 1
            tampered_tar["attempts/normal/export.tar"] = bytes(raw_tar)
            with self.subTest(group="egress-reopened-tar"), self.assertRaises(evidence.EvidenceError):
                evidence._reconstruct_c10(tampered_tar, bindings, snapshot)

            drifted_bindings = copy.deepcopy(bindings)
            drifted_bindings["implementation_tree"] = "c" * 40
            with self.subTest(group="expected-binding-implementation"), self.assertRaises(evidence.EvidenceError):
                evidence._reconstruct_c10(files, drifted_bindings, snapshot)
            drifted_bindings = copy.deepcopy(bindings)
            drifted_bindings["claim_boundary"]["ordered_nonclaims"].reverse()
            with self.subTest(group="claim-boundary-cross-binding"), self.assertRaises(evidence.EvidenceError):
                evidence._reconstruct_c10(files, drifted_bindings, snapshot)

            plan_cases = (
                ("extra-tag-resolution", lambda plan: plan["commands"][2]["argv"].insert(-18, "python:latest")),
                ("non-create-operation-substitution", lambda plan: plan["commands"][10]["argv"].__setitem__(7, "kill")),
                ("missing-network-none", lambda plan: plan["commands"][2]["argv"].remove("--network=none")),
                ("changed-network", lambda plan: plan["commands"][2]["argv"].__setitem__(plan["commands"][2]["argv"].index("--network=none"), "--network=bridge")),
                ("pull-authority", lambda plan: plan["commands"][2]["argv"].__setitem__(plan["commands"][2]["argv"].index("--pull=never"), "--pull=always")),
                ("build-authority", lambda plan: plan["commands"][14]["argv"].__setitem__(7, "build")),
                ("login-authority", lambda plan: plan["commands"][14]["argv"].__setitem__(7, "login")),
                ("shell-authority", lambda plan: plan["commands"][14]["argv"].append("/bin/sh")),
                ("remote-endpoint", lambda plan: plan["commands"][0]["argv"].__setitem__(4, "tcp://127.0.0.1:2375")),
                ("caller-environment", lambda plan: plan["commands"][0]["environment"].update({"EXTRA": "1"})),
                ("caller-argv", lambda plan: plan["commands"][0]["argv"].append("--extra")),
            )
            for label, mutate in plan_cases:
                reject_json("readiness/normal-plan.json", label, mutate)
            reject_json(
                "readiness/campaign-plan.json", "alternate-native-snapshot-root",
                lambda plan: plan["native_command"]["argv"].__setitem__(
                    2, "/alternate/tools/hsai-formal-preflight/p01b_container_probe.py"
                ),
            )
            def alternate_attempt_root(plan: dict) -> None:
                argv = plan["commands"][2]["argv"]
                for index, item in enumerate(argv):
                    if item.startswith("--mount=type=bind,src="):
                        argv[index] = "--mount=type=bind,src=/alternate,dst=/input,readonly,bind-propagation=rprivate"
                    elif item.startswith("--security-opt=seccomp="):
                        argv[index] = "--security-opt=seccomp=/alternate/tools/hsai-formal-preflight/p01b_container_seccomp.json"
            reject_json("readiness/normal-plan.json", "alternate-attempt-snapshot-root", alternate_attempt_root)
        finally:
            evidence.INDEX_REFERENCE = original_reference
            evidence.DOCKER_CONTEXT_SHA256 = original_context


if __name__ == "__main__":
    unittest.main()
