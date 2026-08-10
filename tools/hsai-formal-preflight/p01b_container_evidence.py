"""Pure-data P01B retained container evidence contracts.

State slice:
phase-796a3l6-hsai-p01b-execution-evidence-implementation.

This module validates caller-supplied bytes and dictionaries. It has no process,
environment, filesystem-write, Docker, socket, or network capability.
"""

import base64
import binascii
import copy
import hashlib
import json
import plistlib
import re
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class EvidenceError(ValueError):
    """Retained evidence violates the frozen A3L5 contract."""


SCHEMAS = {
    "authorization": "hsai-p01b-container-authorization-v2",
    "attempt_plan": "hsai-p01b-container-plan-v2",
    "readiness_plan": "hsai-p01b-container-readiness-plan-v1",
    "readiness_result": "hsai-p01b-container-readiness-result-v1",
    "campaign_plan": "hsai-p01b-container-campaign-plan-v1",
    "observation": "hsai-p01b-container-observation-v2",
    "receipt": "hsai-p01b-container-receipt-v2",
    "certificate": "hsai-p01b-container-certificate-v2",
    "readiness_event": "hsai-p01b-container-readiness-event-v1",
    "publication": "hsai-p01b-container-publication-v1",
    "manifest": "hsai-p01b-container-manifest-v2",
    "decision": "hsai-p01b-container-decision-v2",
    "review": "hsai-p01b-container-review-v1",
    "review_aggregate": "hsai-p01b-container-review-aggregate-v1",
    "acceptance": "hsai-p01b-container-acceptance-v1",
}

DOMAINS = {
    "authorization": "hsai:p01b-container-authorization:v2",
    "attempt_plan": "hsai:p01b-container-plan:v2",
    "readiness_plan": "hsai:p01b-container-readiness-plan:v1",
    "readiness_result": "hsai:p01b-container-readiness-result:v1",
    "campaign_plan": "hsai:p01b-container-campaign-plan:v1",
    "observation": "hsai:p01b-container-observation:v2",
    "receipt": "hsai:p01b-container-receipt:v2",
    "certificate": "hsai:p01b-container-certificate:v2",
    "readiness_event": "hsai:p01b-container-readiness-event:v1",
    "publication": "hsai:p01b-container-publication:v1",
    "manifest": "hsai:p01b-container-manifest:v2",
    "decision": "hsai:p01b-container-decision:v2",
    "review": "hsai:p01b-container-review:v1",
    "review_aggregate": "hsai:p01b-container-review-aggregate:v1",
    "acceptance": "hsai:p01b-container-acceptance:v1",
    "projection": "hsai:p01b-container-projection:v1",
}

DOMAIN_VECTORS = {
    "authorization": "3fdc727376e6f4186a68dc130bc9810f517b7d326e324c6d0d5c3990f8c97ed2",
    "attempt_plan": "9a1f5502ab0e31898e9f2ab4269cd42f7ac878ea8c592d75c7f66c616bf41ce5",
    "observation": "348241ba8d3b6681deec49968324f42f7d7bda851d269bd5b01c2b67c0dadb0d",
    "receipt": "6f5e6021e7d8f26ed1e28d64b619a1dfc5a69f68e8a3ea1ba689e5edbf37761e",
    "certificate": "bac9dc7e6718dc89f7a7f653017872ad3cc39d3668b6cea3c75f7ed6bd41070b",
    "manifest": "893389c936a8b6afe02318e0deee1eac6c773619776004d0bec77457f4049a22",
    "decision": "d0e1a37812c689da0ff590c1acec3cc4a8ffc12439091f440d1cbcf2a05fa99e",
    "readiness_plan": "ecd3ac14421ba4b078c42f91fdadf5717f6892eca79e93d04912c09d42855b93",
    "readiness_result": "f51af3cbf9a99aab8399fb2e43a1898be64fb26bc6d990cb2b0b3e9b05b8e7fa",
    "campaign_plan": "b294a225bf33946eb9e8aaaa38c66992a81718eaf6582b7c040887680a34dee1",
    "readiness_event": "9fa034a4f85ce636d1564d3114a191c6c3c01457dc086f34ff3ea31630070bde",
    "publication": "bf65ed0e093ace596935be674be2e00a350d7bc0d7880d053d16958d8fe2ec5d",
    "review": "56d67ce2eb94fb4e427f29a7546fd2d4978b187b018a4360eea2a3bd95bf5de8",
    "review_aggregate": "3e567f1b5c7f1138aa6dbdb35f34d37080f8c97f164457f8e8619241cabf8823",
    "acceptance": "9b5ecc2778fd26744ac4e985f51d7ec94b56b4bdfb21ee855d8aadcd0d86aa0d",
}

CLASS_ORDER = ("C02", "C03", "C04", "C05", "C06", "C07", "C09", "C10")
REVIEW_ROLE_ORDER = ("security-capability", "correspondence-reproducibility")
EVIDENCE_LEVEL = "Level1LocalReplayOrLower"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
MAX_JSON_BYTES = 1_048_576
MAX_A3L6_GATE_JSON_BYTES = 4_194_304
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 65_536
MAX_TAR_BYTES = 16_777_216
MAX_RESULT_BYTES = 1_048_576
A3L6_GATE_BUNDLE_PATH = "authority/a3l6-gate-bundle.json"
PLATFORM_PLACEHOLDER = "${PLATFORM}"
CID_PLACEHOLDER = "${CID}"
PLATFORM_REFERENCE_RE = re.compile(r"^docker\.io/library/python@sha256:[0-9a-f]{64}$")
INDEX_REFERENCE = "docker.io/library/python@sha256:8dca233de9f3d9bb410665f00a4da6dd06f331083137e0e98ccf227236fcc438"
BUILDX_SHA256 = "9d594c8c396e02385b8de8d7594ede893a64ceebbaefb37f7fa99fcd991cf94e"
DOCKER_SHA256 = "73206884cd100a165e20fbab2b1f9e09e0ae8fc959ec9b02fed46152a99c5e79"
IMAGE_CONFIG_DIGEST = (
    "sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4"
)
ROOTFS_DIFF_IDS = (
    "sha256:3bfd0b5a99a1f25a488230217defd5c2781ad861f692f5df22d9734bbddfc53d",
    "sha256:e3866ac24baf965b1d6445dab2a6697dc8c5e633e961cdeb8664e947af0afcd8",
    "sha256:58c826d6f8b6c49949dcff1a49bcc504e95bdd68a1e7822c397599576ca5842e",
    "sha256:4a0f4c378bc5afc903ba2f580dd5e0a2e45fb6599e4635133e6662c7acad0e7a",
)
NATIVE_PYTHON_SHA256 = (
    "7f30f076d0e9c38f772a76449fca9da8cf97f6a3d43b94c90a00e4f9ce7ad39e"
)
SANDBOX_EXEC_SHA256 = (
    "556b22a255f0c6d5f3811194a2622c165cfcfabbfbe50f95d92190ff81e99470"
)
CODESIGN_SHA256 = (
    "c91d293ec824037dc4fcb204c5aae32545f73a79a4d6b5f0d113cc856465f209"
)
DOCKER_PATH = "/Applications/Docker.app/Contents/Resources/bin/docker"
BUILDX_PATH = "/Applications/Docker.app/Contents/Resources/cli-plugins/docker-buildx"
CODESIGN_PATH = "/usr/bin/codesign"
DOCKER_DESKTOP_INFO_PLIST_PATH = "/Applications/Docker.app/Contents/Info.plist"
DOCKER_DESKTOP_VM_PATH = "/Applications/Docker.app/Contents/Resources/linuxkit/desktop.img"
DOCKER_DESKTOP_KERNEL_PATH = "/Applications/Docker.app/Contents/Resources/linuxkit/kernel"
DOCKER_CONTEXT_SHA256 = (
    "c36db611bb2256cd052f36471538d4c8d1ff3dc36a978d325391c3813072cb2c"
)
DOCKER_DESKTOP_VM_SHA256 = (
    "be2274863e3e008de42f38c6d746a6090b31619715a3c02b4134e1889cdbc9d9"
)
DOCKER_DESKTOP_KERNEL_SHA256 = (
    "420cd7ac96572498e74d8593f9bb3e2ed0dbf06d61dc5214be3e5c5f08763d0b"
)
EXPECTED_BINDING_FIELDS = (
    "predecessor_commit",
    "user_authorization_sha256",
    "implementation_commit",
    "implementation_tree",
    "protected_file_sha256",
    "source_paths",
    "seccomp_sha256",
    "seccomp_license_sha256",
    "seccomp_provenance_sha256",
    "docker_context_sha256",
    "docker_desktop_vm_sha256",
    "docker_desktop_kernel_sha256",
)

INSPECT_FIELDS = (
    "Id", "Name", "Path", "Args", "Platform", "AppArmorProfile",
    "Config.Image", "Config.User", "Config.Entrypoint", "Config.Cmd",
    "Config.Env", "Config.WorkingDir", "Config.Hostname", "Config.Healthcheck",
    "Config.OpenStdin", "Config.Tty", "Config.Labels", "HostConfig.Runtime",
    "HostConfig.NetworkMode", "HostConfig.IpcMode", "HostConfig.PidMode",
    "HostConfig.UTSMode", "HostConfig.CgroupnsMode", "HostConfig.CgroupParent",
    "HostConfig.UsernsMode", "HostConfig.ReadonlyRootfs",
    "HostConfig.Privileged", "HostConfig.CapAdd", "HostConfig.CapDrop",
    "HostConfig.SecurityOpt", "HostConfig.Memory", "HostConfig.MemorySwap",
    "HostConfig.MemorySwappiness", "HostConfig.OomKillDisable",
    "HostConfig.PidsLimit", "HostConfig.CpuPeriod", "HostConfig.CpuQuota",
    "HostConfig.Ulimits", "HostConfig.Tmpfs", "HostConfig.ShmSize",
    "HostConfig.LogConfig", "HostConfig.RestartPolicy", "HostConfig.AutoRemove",
    "HostConfig.Devices", "HostConfig.DeviceRequests", "HostConfig.GroupAdd",
    "Mounts", "NetworkSettings.Networks", "State.Status", "State.Running",
    "State.ExitCode", "State.OOMKilled", "State.Error", "State.Pid",
    "State.StartedAt", "State.FinishedAt",
)

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

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_PREFIXED_SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_RE = re.compile(r"^[0-9a-f]{40}$")
_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,126}[a-z0-9]$")
_CID_RE = re.compile(r"^[0-9a-f]{64}$")
_NS_RE = re.compile(r"^(pid|uts|mnt|net|ipc|cgroup|user):\[[0-9]+\]$")
_READY_RE = re.compile(rb"^P01B_RESULT_READY ([1-9][0-9]*) ([0-9a-f]{64})\n$")
_FAILURES = {
    "registry_failed",
    "selection_failed",
    "platform_digest_failed",
    "local_resolution_failed",
    "context_drift",
    "identity_drift",
}
_OUTCOMES = {
    "exit",
    "signal",
    "timeout",
    "stdout_limit",
    "stderr_limit",
    "not_run",
    "protocol_error",
}
_CONTAINER_ROLES = {
    "absence-name-pre",
    "absence-label-pre",
    "pre-create-inspect",
    "pre-create-label-list",
    "create",
    "inspect-prestart",
    "start-attach",
    "export-running",
    "release",
    "emergency-kill",
    "wait",
    "inspect-terminal",
    "remove",
    "absence-cid",
    "absence-name",
    "absence-label",
    "absence-label-list",
    "daemon-recheck",
    "recovery-inspect",
    "recovery-kill",
    "recovery-wait",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _reject_duplicates(pairs: Iterable[Tuple[str, object]]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate JSON key: {}".format(key))
        result[key] = value
    return result


def _walk_limits(value: object) -> None:
    stack = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        _require(nodes <= MAX_JSON_NODES, "JSON node limit exceeded")
        _require(depth <= MAX_JSON_DEPTH, "JSON depth limit exceeded")
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


def _json_size_limit(max_bytes: int) -> int:
    _require(
        isinstance(max_bytes, int)
        and not isinstance(max_bytes, bool)
        and 0 < max_bytes <= MAX_A3L6_GATE_JSON_BYTES,
        "invalid JSON size limit",
    )
    return max_bytes


def canonical_json_bytes(
    value: object, max_bytes: int = MAX_JSON_BYTES
) -> bytes:
    """Return canonical compact sorted-key ASCII JSON."""
    limit = _json_size_limit(max_bytes)
    try:
        raw = json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise EvidenceError("value is not canonical JSON") from error
    _require(len(raw) <= limit, "canonical JSON exceeds size limit")
    _walk_limits(value)
    return raw


def _parse_json_bytes(raw: bytes, max_bytes: int = MAX_JSON_BYTES) -> object:
    """Parse ASCII JSON with duplicate, depth, and node rejection."""
    limit = _json_size_limit(max_bytes)
    _require(isinstance(raw, bytes), "JSON input must be bytes")
    _require(len(raw) <= limit, "JSON input exceeds size limit")
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_reject_duplicates,
            parse_constant=lambda item: (_ for _ in ()).throw(
                EvidenceError("non-finite JSON: " + item)
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise EvidenceError("malformed JSON") from error
    _walk_limits(value)
    return value


def strict_json_bytes(raw: bytes, max_bytes: int = MAX_JSON_BYTES) -> object:
    """Parse canonical ASCII JSON with duplicate, depth, and node rejection."""
    value = _parse_json_bytes(raw, max_bytes)
    _require(
        raw == canonical_json_bytes(value, max_bytes),
        "JSON is not canonical",
    )
    return value


def sha256_hex(raw: bytes) -> str:
    _require(isinstance(raw, bytes), "SHA-256 input must be bytes")
    return hashlib.sha256(raw).hexdigest()


def domain_sha256(
    domain: str, value: object, max_bytes: int = MAX_JSON_BYTES
) -> str:
    _require(
        isinstance(domain, str) and domain and "\x00" not in domain,
        "invalid digest domain",
    )
    try:
        encoded = domain.encode("ascii")
    except UnicodeEncodeError as error:
        raise EvidenceError("digest domain must be ASCII") from error
    return hashlib.sha256(
        encoded + b"\0" + canonical_json_bytes(value, max_bytes)
    ).hexdigest()


def _digest(kind: str, value: Mapping[str, object]) -> str:
    limit = (
        MAX_A3L6_GATE_JSON_BYTES
        if kind in ("a3l6_gate_source", "a3l6_gate_bundle")
        else MAX_JSON_BYTES
    )
    return domain_sha256(DOMAINS[kind], value, limit)


def _fields(value: object, expected: Sequence[str], label: str) -> Mapping[str, object]:
    _require(isinstance(value, dict), label + " must be an object")
    _require(set(value) == set(expected), label + " fields drift")
    return value


def _ascii(value: object, label: str, allow_empty: bool = False) -> str:
    _require(isinstance(value, str), label + " must be a string")
    _require(allow_empty or bool(value), label + " is empty")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as error:
        raise EvidenceError(label + " must be ASCII") from error
    _require("\x00" not in value, label + " contains NUL")
    return value


def _sha(value: object, label: str, prefixed: bool = False) -> str:
    pattern = _PREFIXED_SHA_RE if prefixed else _SHA_RE
    _require(
        isinstance(value, str) and pattern.fullmatch(value) is not None,
        "invalid " + label,
    )
    return value


def _git(value: object, label: str) -> str:
    _require(
        isinstance(value, str) and _GIT_RE.fullmatch(value) is not None,
        "invalid " + label,
    )
    return value


def _identifier(value: object, label: str) -> str:
    _require(
        isinstance(value, str) and _ID_RE.fullmatch(value) is not None,
        "invalid " + label,
    )
    return value


def _path(value: object, label: str, absolute: Optional[bool] = None) -> str:
    path = _ascii(value, label)
    _require("//" not in path, label + " is noncanonical")
    if absolute is True:
        _require(path.startswith("/"), label + " must be absolute")
    if absolute is False:
        _require(not path.startswith("/"), label + " must be relative")
    if path == "/":
        return path
    parts = path.split("/")
    if path.startswith("/"):
        parts = parts[1:]
    _require(
        all(part not in ("", ".", "..") for part in parts), label + " is noncanonical"
    )
    return path


def _false_authority(value: Mapping[str, object]) -> None:
    for name in (
        "accepted_evidence_created",
        "level2_plus_created",
        "authority_granted",
    ):
        _require(value[name] is False, name + " must be false")


COMMAND_FIELDS = (
    "ordinal",
    "role",
    "argv",
    "environment",
    "cwd",
    "stdin_policy",
    "stdout_cap",
    "stderr_cap",
    "timeout_ns",
    "activation",
    "expected_outcomes",
)


def validate_command(value: object) -> Mapping[str, object]:
    command = _fields(value, COMMAND_FIELDS, "command")
    _require(
        _is_int(command["ordinal"]) and command["ordinal"] >= 0,
        "invalid command ordinal",
    )
    _ascii(command["role"], "command role")
    _require(
        isinstance(command["argv"], list) and command["argv"], "invalid command argv"
    )
    for item in command["argv"]:
        _ascii(item, "argv item")
    _require(isinstance(command["environment"], dict), "environment must be an object")
    for key, item in command["environment"].items():
        _ascii(key, "environment key")
        _ascii(item, "environment value", allow_empty=True)
    _path(command["cwd"], "command cwd", absolute=True)
    _require(command["stdin_policy"] == "closed-null", "stdin policy drift")
    for name in ("stdout_cap", "stderr_cap", "timeout_ns"):
        _require(_is_int(command[name]) and command[name] > 0, "invalid " + name)
    _ascii(command["activation"], "command activation")
    outcomes = command["expected_outcomes"]
    _require(
        isinstance(outcomes, list) and outcomes, "expected outcomes must be nonempty"
    )
    _require(len(outcomes) == len(set(outcomes)), "duplicate expected outcome")
    for item in outcomes:
        _ascii(item, "expected outcome")
    return command


def _validate_commands(commands: object) -> List[Mapping[str, object]]:
    _require(
        isinstance(commands, list) and commands, "commands must be a nonempty array"
    )
    checked = [validate_command(item) for item in commands]
    _require(
        [item["ordinal"] for item in checked] == list(range(len(checked))),
        "command ordinals drift",
    )
    _require(
        len({item["role"] for item in checked}) == len(checked),
        "duplicate command role",
    )
    return checked


READINESS_PLAN_FIELDS = (
    "schema",
    "predecessor_commit",
    "user_authorization_sha256",
    "index_reference",
    "buildx_sha256",
    "docker_sha256",
    "commands",
    "selected_reference_rule",
)


READINESS_RESULT_FIELDS = (
    "schema",
    "readiness_plan_sha256",
    "index_observation_sha256",
    "index_sha256",
    "selected_descriptor",
    "selected_reference",
    "platform_observation_sha256",
    "platform_sha256",
    "local_image_observation_sha256",
    "context_path",
    "context_bytes",
    "context_sha256",
    "image_config_digest",
    "rootfs_diff_ids",
    "accepted",
    "failure",
)


PREAUTHORIZATION_FIELDS = (
    "schema", "user_authorization_sha256", "predecessor_commit", "action_sha256",
    "policy_sha256", "evidence_bundle_sha256", "a3l6_gate_bundle_sha256",
    "admission_decision_sha256", "implementation_commit", "implementation_tree",
    "readiness_plan_sha256",
)
AUTHORIZATION_ROOT_FIELDS = (
    "schema", "user_authorization_sha256", "action_sha256", "policy_sha256",
    "evidence_bundle_sha256", "a3l6_gate_bundle_sha256", "admission_decision_sha256",
    "preauthorization_sha256", "expected_bindings_sha256", "readiness_sha256",
    "implementation_commit", "implementation_tree", "authority_granted",
)
AUTHORIZATION_FIELDS = (
    "schema", "authorization_id", "authorization_root_sha256",
    "user_authorization_sha256", "action_sha256", "policy_sha256",
    "evidence_bundle_sha256", "a3l6_gate_bundle_sha256", "admission_decision_sha256",
    "expected_bindings_sha256", "implementation_commit", "implementation_tree",
    "readiness_sha256",
)


def validate_preauthorization(value: object) -> Mapping[str, object]:
    plan = _fields(value, PREAUTHORIZATION_FIELDS, "preauthorization plan")
    _require(plan["schema"] == SCHEMAS["preauthorization"], "preauthorization schema drift")
    for name in PREAUTHORIZATION_FIELDS:
        if name.endswith("_sha256"):
            _sha(plan[name], name.replace("_", " "))
    for name in ("predecessor_commit", "implementation_commit", "implementation_tree"):
        _git(plan[name], name.replace("_", " "))
    return plan


def preauthorization_digest(value: Mapping[str, object]) -> str:
    validate_preauthorization(value)
    return _digest("preauthorization", value)


def validate_authorization_root(value: object) -> Mapping[str, object]:
    root = _fields(value, AUTHORIZATION_ROOT_FIELDS, "authorization root")
    _require(root["schema"] == SCHEMAS["authorization_root"], "authorization root schema drift")
    for name in AUTHORIZATION_ROOT_FIELDS:
        if name.endswith("_sha256"):
            _sha(root[name], name.replace("_", " "))
    _git(root["implementation_commit"], "authorization root implementation commit")
    _git(root["implementation_tree"], "authorization root implementation tree")
    _require(root["authority_granted"] is True, "bounded local authority not granted")
    return root


def authorization_root_digest(value: Mapping[str, object]) -> str:
    validate_authorization_root(value)
    return _digest("authorization_root", value)


def validate_authorization(value: object) -> Mapping[str, object]:
    authorization = _fields(value, AUTHORIZATION_FIELDS, "authorization")
    _require(
        authorization["schema"] == SCHEMAS["authorization"],
        "authorization schema drift",
    )
    _identifier(authorization["authorization_id"], "authorization id")
    for name in AUTHORIZATION_FIELDS:
        if name.endswith("_sha256"):
            _sha(authorization[name], name.replace("_", " "))
    _git(authorization["implementation_commit"], "implementation commit")
    _git(authorization["implementation_tree"], "implementation tree")
    return authorization


def authorization_digest(value: Mapping[str, object]) -> str:
    validate_authorization(value)
    return _digest("authorization", value)


ATTEMPT_PLAN_FIELDS = (
    "schema",
    "campaign_id",
    "attempt_id",
    "attempt_kind",
    "authorization_sha256",
    "implementation_commit",
    "platform_manifest_reference",
    "source_manifest_sha256",
    "commands",
)


def _attempt_command_value(
    ordinal: int, role: str, argv: Sequence[str], environment: Mapping[str, str],
    *, cap: int = 16_384, activation: str = "always",
    expected: Sequence[str] = ("exit_zero",),
) -> Dict[str, object]:
    return {
        "ordinal": ordinal, "role": role, "argv": list(argv),
        "environment": dict(environment), "cwd": "/",
        "stdin_policy": "closed-null", "stdout_cap": cap, "stderr_cap": cap,
        "timeout_ns": 1_800_000_000_000, "activation": activation,
        "expected_outcomes": list(expected),
    }


def _expected_attempt_commands(plan: Mapping[str, object]) -> List[Dict[str, object]]:
    commands = plan["commands"]
    _require(isinstance(commands, list) and commands, "attempt commands missing")
    environment = commands[0]["environment"]
    prefix = commands[0]["argv"][:7]
    _require(
        prefix[0] == DOCKER_PATH and prefix[1] == "--config"
        and prefix[2] == environment.get("DOCKER_CONFIG")
        and prefix[3] == "--host" and isinstance(prefix[4], str)
        and prefix[4].startswith("unix:///")
        and prefix[5:] == ["--log-level", "error"],
        "attempt local Docker prefix drift",
    )
    campaign_id = plan["campaign_id"]; attempt_id = plan["attempt_id"]
    name = "hsai-p01b-{}-{}".format(campaign_id, attempt_id)
    labels = [
        "--filter=label=hsai.p01b.campaign=" + campaign_id,
        "--filter=label=hsai.p01b.attempt=" + attempt_id,
    ]
    inspect_template = "[" + ",".join(
        "{{json .%s}}" % field for field in INSPECT_FIELDS
    ) + "]"
    actual_create = commands[2]["argv"]
    seccomp_values = [
        item for item in actual_create if item.startswith("--security-opt=seccomp=")
    ]
    mount_values = [
        item for item in actual_create if item.startswith("--mount=type=bind,src=")
    ]
    _require(
        len(seccomp_values) == len(mount_values) == 1,
        "attempt local input path declaration drift",
    )
    seccomp_path = seccomp_values[0].split("=seccomp=", 1)[1]
    mount_value = mount_values[0]
    mount_match = re.fullmatch(
        r"--mount=type=bind,src=(/[^,\x00\r\n]+),dst=/input,readonly,bind-propagation=rprivate",
        mount_value,
    )
    _require(
        mount_match is not None and seccomp_path.startswith(mount_match.group(1) + "/"),
        "attempt snapshot/seccomp path relationship drift",
    )
    create = prefix + [
        "container", "create", "--pull=never", "--platform=linux/arm64/v8",
        "--name=" + name, "--hostname=hsai-p01b", "--runtime=runc",
        "--network=none", "--ipc=private", "--cgroupns=private",
        "--user=65532:65532", "--read-only", "--privileged=false",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true", seccomp_values[0],
        "--memory=536870912", "--memory-swap=536870912",
        "--memory-swappiness=0", "--oom-kill-disable=false", "--pids-limit=16",
        "--cpu-period=100000", "--cpu-quota=100000", "--ulimit=cpu=900:900",
        "--ulimit=fsize=67108864:67108864", "--ulimit=nofile=32:32",
        "--ulimit=core=0:0",
        "--tmpfs=/work:rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700",
        "--shm-size=1048576", "--log-driver=none", "--restart=no",
        "--no-healthcheck", "--label=hsai.p01b.campaign=" + campaign_id,
        "--label=hsai.p01b.attempt=" + attempt_id,
        "--label=hsai.p01b.authorization=" + plan["authorization_sha256"],
        "--label=hsai.p01b.implementation=" + plan["implementation_commit"],
        mount_value,
        "--workdir=/input", "--entrypoint=/usr/bin/env",
        plan["platform_manifest_reference"], "-i", "HOME=/nonexistent",
        "LANG=C.UTF-8", "LC_ALL=C.UTF-8",
        "PATH=/usr/local/bin:/usr/bin:/bin", "PYTHONHASHSEED=0",
        "PYTHONDONTWRITEBYTECODE=1", "PYTHONNOUSERSITE=1", "TMPDIR=/work",
        "TZ=UTC", "/usr/local/bin/python3", "-B",
        "tools/hsai-formal-preflight/p01b_container_probe.py", "--mode",
        plan["attempt_kind"], "--input-manifest-sha256",
        plan["source_manifest_sha256"], "--output", "/work/result.json",
    ]
    return [
        _attempt_command_value(0, "absence-name-pre", prefix + ["container", "inspect", name], environment, cap=262_144, expected=("exact_absent",)),
        _attempt_command_value(1, "absence-label-pre", prefix + ["container", "ls", "--all", "--no-trunc", *labels, "--format={{.ID}}"], environment, expected=("empty",)),
        _attempt_command_value(2, "create", create, environment, expected=("stable_cid",)),
        _attempt_command_value(3, "inspect-prestart", prefix + ["container", "inspect", "--format=" + inspect_template, CID_PLACEHOLDER], environment, cap=262_144, activation="after_create"),
        _attempt_command_value(4, "start-attach", prefix + ["container", "start", "--attach", CID_PLACEHOLDER], environment, activation="after_prestart"),
        _attempt_command_value(5, "export-running", prefix + ["container", "cp", CID_PLACEHOLDER + ":/work/result.json", "-"], environment, cap=16_777_216, activation="after_readiness"),
        _attempt_command_value(6, "release", prefix + ["container", "kill", "--signal=USR1", CID_PLACEHOLDER], environment, activation="after_export"),
        _attempt_command_value(7, "emergency-kill", prefix + ["container", "kill", "--signal=KILL", CID_PLACEHOLDER], environment, activation="on_breach"),
        _attempt_command_value(8, "wait", prefix + ["container", "wait", CID_PLACEHOLDER], environment, activation="after_release"),
        _attempt_command_value(9, "inspect-terminal", prefix + ["container", "inspect", "--format=" + inspect_template, CID_PLACEHOLDER], environment, cap=262_144, activation="after_release"),
        _attempt_command_value(10, "remove", prefix + ["container", "rm", CID_PLACEHOLDER], environment, activation="after_terminal"),
        _attempt_command_value(11, "absence-cid", prefix + ["container", "inspect", CID_PLACEHOLDER], environment, cap=262_144, activation="after_terminal", expected=("exact_absent",)),
        _attempt_command_value(12, "absence-name", prefix + ["container", "inspect", name], environment, cap=262_144, activation="after_terminal", expected=("exact_absent",)),
        _attempt_command_value(13, "absence-label", prefix + ["container", "ls", "--all", "--no-trunc", *labels, "--format={{.ID}}"], environment, activation="after_terminal", expected=("empty",)),
        _attempt_command_value(14, "daemon-recheck", prefix + ["version", "--format={{json .}}"], environment, cap=262_144, activation="after_terminal"),
    ]


def validate_attempt_plan(value: object) -> Mapping[str, object]:
    plan = _fields(value, ATTEMPT_PLAN_FIELDS, "attempt plan")
    _require(plan["schema"] == SCHEMAS["attempt_plan"], "attempt plan schema drift")
    _identifier(plan["campaign_id"], "campaign id")
    _identifier(plan["attempt_id"], "attempt id")
    _require(plan["attempt_kind"] in ("normal", "oom-child"), "unknown attempt kind")
    _sha(plan["authorization_sha256"], "authorization digest")
    _git(plan["implementation_commit"], "implementation commit")
    reference = _ascii(
        plan["platform_manifest_reference"], "platform manifest reference"
    )
    _require("@sha256:" in reference, "platform reference is not digest-addressed")
    _sha(reference.rsplit("@sha256:", 1)[1], "platform reference digest")
    _sha(plan["source_manifest_sha256"], "source manifest digest")
    commands = _validate_commands(plan["commands"])
    _require(commands == _expected_attempt_commands(plan), "attempt exact command grammar drift")
    return plan


def attempt_plan_digest(value: Mapping[str, object]) -> str:
    validate_attempt_plan(value)
    return _digest("attempt_plan", value)


CAMPAIGN_PLAN_FIELDS = (
    "schema",
    "campaign_id",
    "authorization_sha256",
    "implementation_commit",
    "readiness_plan_sha256",
    "native_command",
    "metadata_commands",
    "normal_plan_sha256",
    "oom_plan_sha256",
)


def validate_campaign_plan(value: object) -> Mapping[str, object]:
    plan = _fields(value, CAMPAIGN_PLAN_FIELDS, "campaign plan")
    _require(plan["schema"] == SCHEMAS["campaign_plan"], "campaign plan schema drift")
    _identifier(plan["campaign_id"], "campaign id")
    for name in (
        "authorization_sha256",
        "readiness_plan_sha256",
        "normal_plan_sha256",
        "oom_plan_sha256",
    ):
        _sha(plan[name], name.replace("_", " "))
    _git(plan["implementation_commit"], "implementation commit")
    _require(
        isinstance(plan["metadata_commands"], list) and plan["metadata_commands"],
        "metadata commands missing",
    )
    commands = _validate_commands([plan["native_command"], *plan["metadata_commands"]])
    environment = commands[0]["environment"]
    native_argv = commands[0]["argv"]
    _require(
        len(native_argv) == 5 and native_argv[:2] == ["/usr/bin/python3", "-B"]
        and native_argv[2].endswith("/tools/hsai-formal-preflight/p01b_container_probe.py")
        and native_argv[3:] == ["--mode", "native-reference"],
        "campaign native command grammar drift",
    )
    metadata_prefix = commands[1]["argv"][:7]
    _require(
        metadata_prefix[0] == DOCKER_PATH
        and metadata_prefix[1:3] == ["--config", environment.get("DOCKER_CONFIG")]
        and metadata_prefix[3] == "--host"
        and isinstance(metadata_prefix[4], str)
        and metadata_prefix[4].startswith("unix:///")
        and metadata_prefix[5:] == ["--log-level", "error"],
        "campaign local Docker prefix drift",
    )
    expected = [
        _attempt_command_value(0, "native-reference", native_argv, environment, cap=1_048_576),
        _attempt_command_value(1, "docker-version", metadata_prefix + ["version", "--format={{json .}}"], environment, cap=262_144),
        _attempt_command_value(2, "docker-info", metadata_prefix + ["info", "--format={{json .}}"], environment, cap=262_144),
        _attempt_command_value(3, "image-config", metadata_prefix + ["image", "inspect", "--format={{json .}}", IMAGE_CONFIG_DIGEST], environment, cap=262_144),
    ]
    _require(commands == expected, "campaign exact command grammar drift")
    return plan


def campaign_plan_digest(value: Mapping[str, object]) -> str:
    validate_campaign_plan(value)
    return _digest("campaign_plan", value)


OBSERVATION_FIELDS = (
    "schema",
    "plan_sha256",
    "launch_ordinal",
    "completion_ordinal",
    "role",
    "argv",
    "environment",
    "cwd",
    "stdin_policy",
    "executable_path",
    "executable_sha256",
    "started_monotonic_ns",
    "ended_monotonic_ns",
    "duration_ns",
    "outcome",
    "exit_code",
    "signal",
    "stdout_path",
    "stdout_total_bytes",
    "stdout_retained_bytes",
    "stdout_raw_sha256",
    "stdout_retained_sha256",
    "stdout_cap",
    "stdout_truncated",
    "stderr_path",
    "stderr_total_bytes",
    "stderr_retained_bytes",
    "stderr_raw_sha256",
    "stderr_retained_sha256",
    "stderr_cap",
    "stderr_truncated",
    "container_id",
    "previous_observation_sha256",
)


def _validate_stream(
    value: Mapping[str, object], prefix: str, raw: Optional[bytes]
) -> None:
    path = value[prefix + "_path"]
    _path(path, prefix + " path")
    total = value[prefix + "_total_bytes"]
    retained = value[prefix + "_retained_bytes"]
    cap = value[prefix + "_cap"]
    truncated = value[prefix + "_truncated"]
    _require(_is_int(total) and total >= 0, "invalid " + prefix + " total bytes")
    _require(
        _is_int(retained) and retained >= 0, "invalid " + prefix + " retained bytes"
    )
    _require(_is_int(cap) and cap > 0, "invalid " + prefix + " cap")
    _require(isinstance(truncated, bool), "invalid " + prefix + " truncation flag")
    _sha(value[prefix + "_raw_sha256"], prefix + " raw digest")
    _sha(value[prefix + "_retained_sha256"], prefix + " retained digest")
    _require(total <= cap + 1, prefix + " raw observation exceeds cap+1")
    _require(retained == min(total, cap), prefix + " retained length drift")
    _require(truncated == (total > cap), prefix + " truncation arithmetic drift")
    if raw is not None:
        _require(isinstance(raw, bytes), prefix + " raw stream must be bytes")
        _require(len(raw) == total, prefix + " raw length drift")
        _require(
            sha256_hex(raw) == value[prefix + "_raw_sha256"],
            prefix + " raw digest drift",
        )
        _require(
            sha256_hex(raw[:retained]) == value[prefix + "_retained_sha256"],
            prefix + " retained digest drift",
        )


def validate_observation(
    value: object,
    stdout_raw: Optional[bytes] = None,
    stderr_raw: Optional[bytes] = None,
) -> Mapping[str, object]:
    observation = _fields(value, OBSERVATION_FIELDS, "observation")
    _require(
        observation["schema"] == SCHEMAS["observation"], "observation schema drift"
    )
    _sha(observation["plan_sha256"], "plan digest")
    for name in (
        "launch_ordinal",
        "completion_ordinal",
        "started_monotonic_ns",
        "ended_monotonic_ns",
        "duration_ns",
    ):
        _require(
            _is_int(observation[name]) and observation[name] >= 0, "invalid " + name
        )
    _ascii(observation["role"], "observation role")
    _require(
        isinstance(observation["argv"], list) and observation["argv"],
        "invalid observation argv",
    )
    for item in observation["argv"]:
        _ascii(item, "observation argv item")
    _require(
        isinstance(observation["environment"], dict),
        "observation environment must be an object",
    )
    for key, item in observation["environment"].items():
        _ascii(key, "observation environment key")
        _ascii(item, "observation environment value", allow_empty=True)
    _path(observation["cwd"], "observation cwd", absolute=True)
    _require(observation["stdin_policy"] == "closed-null", "observation stdin drift")
    _path(observation["executable_path"], "executable path", absolute=True)
    _sha(observation["executable_sha256"], "executable digest")
    outcome = observation["outcome"]
    _require(outcome in _OUTCOMES, "unknown observation outcome")
    if outcome == "exit":
        _require(
            _is_int(observation["exit_code"])
            and observation["exit_code"] >= 0
            and observation["signal"] is None,
            "invalid exit outcome",
        )
    elif outcome == "signal":
        _require(
            observation["exit_code"] is None
            and _is_int(observation["signal"])
            and observation["signal"] > 0,
            "invalid signal outcome",
        )
    else:
        _require(
            observation["exit_code"] is None and observation["signal"] is None,
            "bounded outcome carries exit status",
        )
    _validate_stream(observation, "stdout", stdout_raw)
    _validate_stream(observation, "stderr", stderr_raw)
    if observation["container_id"] is not None:
        _require(
            isinstance(observation["container_id"], str)
            and _CID_RE.fullmatch(observation["container_id"]) is not None,
            "invalid container id",
        )
    if observation["previous_observation_sha256"] is not None:
        _sha(observation["previous_observation_sha256"], "previous observation digest")
    if outcome == "not_run":
        _require(
            observation["started_monotonic_ns"]
            == observation["ended_monotonic_ns"]
            == observation["duration_ns"]
            == 0,
            "not-run observation carries time",
        )
        _require(
            observation["stdout_total_bytes"] == observation["stderr_total_bytes"] == 0,
            "not-run observation carries stream bytes",
        )
    else:
        _require(
            observation["ended_monotonic_ns"] >= observation["started_monotonic_ns"],
            "observation time reversal",
        )
        _require(
            observation["duration_ns"]
            == observation["ended_monotonic_ns"] - observation["started_monotonic_ns"],
            "observation duration drift",
        )
    return observation


def observation_digest(value: Mapping[str, object]) -> str:
    validate_observation(value)
    return _digest("observation", value)


RECEIPT_FIELDS = (
    "schema",
    "plan_sha256",
    "launch_ordinal",
    "completion_ordinal",
    "role",
    "argv",
    "environment",
    "cwd",
    "stdin_policy",
    "executable_path",
    "executable_sha256",
    "started_monotonic_ns",
    "ended_monotonic_ns",
    "duration_ns",
    "outcome",
    "exit_code",
    "signal",
    "stdout_total_bytes",
    "stdout_retained_bytes",
    "stdout_raw_sha256",
    "stdout_retained_sha256",
    "stdout_cap",
    "stdout_truncated",
    "stderr_total_bytes",
    "stderr_retained_bytes",
    "stderr_raw_sha256",
    "stderr_retained_sha256",
    "stderr_cap",
    "stderr_truncated",
    "container_id",
    "observation_sha256",
    "previous_receipt_sha256",
    "observation_class",
    "container_action_observed",
    "accepted_evidence_created",
    "level2_plus_created",
    "authority_granted",
)


def _commands_for_plan(plan: Mapping[str, object]) -> List[Mapping[str, object]]:
    if plan.get("schema") == SCHEMAS["campaign_plan"]:
        commands = [plan["native_command"], *plan["metadata_commands"]]
    else:
        commands = plan["commands"]
    _require(isinstance(commands, list), "plan commands missing")
    return commands


def _command_for_launch(
    plan: Mapping[str, object], ordinal: int
) -> Mapping[str, object]:
    commands = _commands_for_plan(plan)
    for command in commands:
        if command["ordinal"] == ordinal:
            return command
    raise EvidenceError("observation launch ordinal is absent from plan")


def _validate_resolved_argv(
    command: Mapping[str, object], observation: Mapping[str, object]
) -> None:
    expected = command["argv"]
    actual = observation["argv"]
    _require(len(expected) == len(actual), "observation command drift: argv")
    for planned, observed in zip(expected, actual):
        resolved = planned
        if CID_PLACEHOLDER in resolved:
            container_id = observation["container_id"]
            _require(
                isinstance(container_id, str),
                "CID-resolved observation lacks container id",
            )
            resolved = resolved.replace(CID_PLACEHOLDER, container_id)
        if PLATFORM_PLACEHOLDER in resolved:
            _require(resolved == PLATFORM_PLACEHOLDER, "invalid PLATFORM substitution")
            if observation["outcome"] == "not_run":
                _require(observed == PLATFORM_PLACEHOLDER, "not-run PLATFORM argv drift")
            else:
                _require(PLATFORM_REFERENCE_RE.fullmatch(observed) is not None, "invalid PLATFORM substitution")
                resolved = observed
        _require(resolved == observed, "observation command drift: argv")


def reconstruct_receipt(
    plan: Mapping[str, object],
    observation: Mapping[str, object],
    stdout_raw: bytes,
    stderr_raw: bytes,
    previous_receipt_sha256: Optional[str] = None,
) -> Dict[str, object]:
    """Reconstruct one receipt solely from a plan, raw observation, and raw streams."""
    if plan.get("schema") == SCHEMAS["attempt_plan"]:
        validate_attempt_plan(plan)
        plan_digest = attempt_plan_digest(plan)
    elif plan.get("schema") == SCHEMAS["readiness_plan"]:
        validate_readiness_plan(plan)
        plan_digest = readiness_plan_digest(plan)
    elif plan.get("schema") == SCHEMAS["campaign_plan"]:
        validate_campaign_plan(plan)
        plan_digest = campaign_plan_digest(plan)
    else:
        raise EvidenceError("unsupported receipt plan schema")
    validate_observation(observation, stdout_raw, stderr_raw)
    _require(
        observation["plan_sha256"] == plan_digest, "observation plan binding drift"
    )
    command = _command_for_launch(plan, observation["launch_ordinal"])
    for name in (
        "role",
        "environment",
        "cwd",
        "stdin_policy",
        "stdout_cap",
        "stderr_cap",
    ):
        _require(
            observation[name] == command[name], "observation command drift: " + name
        )
    _validate_resolved_argv(command, observation)
    if observation["outcome"] == "timeout":
        _require(
            observation["duration_ns"] >= command["timeout_ns"],
            "timeout below plan bound",
        )
    if previous_receipt_sha256 is not None:
        _sha(previous_receipt_sha256, "previous receipt digest")
    receipt: Dict[str, object] = {"schema": SCHEMAS["receipt"]}
    copied = (
        "plan_sha256",
        "launch_ordinal",
        "completion_ordinal",
        "role",
        "argv",
        "environment",
        "cwd",
        "stdin_policy",
        "executable_path",
        "executable_sha256",
        "started_monotonic_ns",
        "ended_monotonic_ns",
        "duration_ns",
        "outcome",
        "exit_code",
        "signal",
        "stdout_total_bytes",
        "stdout_retained_bytes",
        "stdout_raw_sha256",
        "stdout_retained_sha256",
        "stdout_cap",
        "stdout_truncated",
        "stderr_total_bytes",
        "stderr_retained_bytes",
        "stderr_raw_sha256",
        "stderr_retained_sha256",
        "stderr_cap",
        "stderr_truncated",
        "container_id",
    )
    receipt.update((name, observation[name]) for name in copied)
    receipt.update(
        {
            "observation_sha256": observation_digest(observation),
            "previous_receipt_sha256": previous_receipt_sha256,
            "observation_class": "untrusted_external_candidate",
            "container_action_observed": observation["role"] in _CONTAINER_ROLES
            and observation["outcome"] != "not_run",
            "accepted_evidence_created": False,
            "level2_plus_created": False,
            "authority_granted": False,
        }
    )
    validate_receipt(receipt)
    return receipt


def validate_receipt(value: object) -> Mapping[str, object]:
    receipt = _fields(value, RECEIPT_FIELDS, "receipt")
    _require(receipt["schema"] == SCHEMAS["receipt"], "receipt schema drift")
    _sha(receipt["plan_sha256"], "receipt plan digest")
    _sha(receipt["observation_sha256"], "receipt observation digest")
    if receipt["previous_receipt_sha256"] is not None:
        _sha(receipt["previous_receipt_sha256"], "previous receipt digest")
    _require(
        receipt["observation_class"] == "untrusted_external_candidate",
        "receipt observation class drift",
    )
    _require(
        isinstance(receipt["container_action_observed"], bool),
        "invalid container action marker",
    )
    _false_authority(receipt)
    return receipt


def receipt_digest(value: Mapping[str, object]) -> str:
    validate_receipt(value)
    return _digest("receipt", value)


def reconstruct_receipt_chain(
    plan: Mapping[str, object],
    items: Sequence[Tuple[Mapping[str, object], bytes, bytes]],
) -> List[Dict[str, object]]:
    """Reconstruct a complete chain ordered by command completion."""
    _require(isinstance(items, (list, tuple)) and items, "receipt chain is empty")
    receipts: List[Dict[str, object]] = []
    previous_observation: Optional[str] = None
    previous_receipt: Optional[str] = None
    launches: List[int] = []
    previous_end = -1
    for completion, (observation, stdout_raw, stderr_raw) in enumerate(items):
        validate_observation(observation, stdout_raw, stderr_raw)
        _require(
            observation["completion_ordinal"] == completion, "completion order drift"
        )
        _require(
            observation["previous_observation_sha256"] == previous_observation,
            "observation chain drift",
        )
        _require(
            observation["ended_monotonic_ns"] >= previous_end
            or observation["outcome"] == "not_run",
            "completion time drift",
        )
        receipt = reconstruct_receipt(
            plan, observation, stdout_raw, stderr_raw, previous_receipt
        )
        receipts.append(receipt)
        previous_observation = observation_digest(observation)
        previous_receipt = receipt_digest(receipt)
        launches.append(observation["launch_ordinal"])
        if observation["outcome"] != "not_run":
            previous_end = observation["ended_monotonic_ns"]
    commands = _commands_for_plan(plan)
    _require(
        sorted(launches) == [command["ordinal"] for command in commands],
        "receipt chain launch coverage drift",
    )
    _require(len(launches) == len(set(launches)), "duplicate launch receipt")
    return receipts


def _receipt_chain_plan(kind: str, plan: Mapping[str, object]) -> Tuple[Mapping[str, object], str]:
    _require(kind in ("readiness", "campaign", "normal", "oom"), "receipt-chain kind drift")
    if kind == "readiness":
        checked = validate_readiness_plan(plan); digest = readiness_plan_digest(checked)
    elif kind == "campaign":
        checked = validate_campaign_plan(plan); digest = campaign_plan_digest(checked)
    else:
        checked = validate_attempt_plan(plan); digest = attempt_plan_digest(checked)
        expected_kind = "normal" if kind == "normal" else "oom-child"
        _require(checked["attempt_id"] == kind and checked["attempt_kind"] == expected_kind, "receipt-chain attempt identity drift")
    return checked, digest


def build_receipt_chain(
    kind: str, plan: Mapping[str, object],
    items: Sequence[Tuple[Mapping[str, object], bytes, bytes]],
) -> Dict[str, object]:
    checked_plan, plan_sha = _receipt_chain_plan(kind, plan)
    receipts = reconstruct_receipt_chain(checked_plan, items)
    value = {
        "schema": SCHEMAS["receipt_chain"], "kind": kind,
        "plan_sha256": plan_sha, "ordered_receipts": receipts,
        "chain_sha256": sha256_hex(canonical_json_bytes(receipts)),
    }
    validate_receipt_chain(value, checked_plan, items)
    return value


def validate_receipt_chain(
    value: object, plan: Mapping[str, object],
    items: Sequence[Tuple[Mapping[str, object], bytes, bytes]],
) -> Mapping[str, object]:
    wrapper = _fields(value, ("schema", "kind", "plan_sha256", "ordered_receipts", "chain_sha256"), "receipt chain")
    _require(wrapper["schema"] == SCHEMAS["receipt_chain"], "receipt-chain schema drift")
    checked_plan, plan_sha = _receipt_chain_plan(wrapper["kind"], plan)
    reconstructed = reconstruct_receipt_chain(checked_plan, items)
    _require(
        wrapper["plan_sha256"] == plan_sha
        and wrapper["ordered_receipts"] == reconstructed
        and wrapper["chain_sha256"] == sha256_hex(canonical_json_bytes(reconstructed)),
        "receipt-chain reconstruction drift",
    )
    return wrapper


def receipt_chain_digest(
    value: Mapping[str, object], plan: Optional[Mapping[str, object]] = None,
    items: Optional[Sequence[Tuple[Mapping[str, object], bytes, bytes]]] = None,
) -> str:
    _fields(value, ("schema", "kind", "plan_sha256", "ordered_receipts", "chain_sha256"), "receipt chain")
    if plan is not None or items is not None:
        _require(plan is not None and items is not None, "receipt-chain digest inputs incomplete")
        validate_receipt_chain(value, plan, items)
    return _digest("receipt_chain", value)


READINESS_EVENT_FIELDS = (
    "schema",
    "plan_sha256",
    "attempt_id",
    "start_launch_ordinal",
    "stdout_path",
    "prefix_bytes",
    "prefix_sha256",
    "line_offset",
    "line_bytes",
    "line_sha256",
    "observed_monotonic_ns",
)


def validate_readiness_event(
    value: object,
    start_observation: Optional[Mapping[str, object]] = None,
    start_stdout_raw: Optional[bytes] = None,
    export_observation: Optional[Mapping[str, object]] = None,
    release_observation: Optional[Mapping[str, object]] = None,
) -> Mapping[str, object]:
    event = _fields(value, READINESS_EVENT_FIELDS, "readiness event")
    _require(
        event["schema"] == SCHEMAS["readiness_event"], "readiness event schema drift"
    )
    _sha(event["plan_sha256"], "readiness plan digest")
    _identifier(event["attempt_id"], "readiness attempt id")
    _require(
        _is_int(event["start_launch_ordinal"]) and event["start_launch_ordinal"] >= 0,
        "invalid start launch ordinal",
    )
    _path(event["stdout_path"], "readiness stdout path")
    for name in ("prefix_bytes", "line_offset", "line_bytes", "observed_monotonic_ns"):
        _require(_is_int(event[name]) and event[name] >= 0, "invalid " + name)
    _sha(event["prefix_sha256"], "readiness prefix digest")
    _sha(event["line_sha256"], "readiness line digest")
    _require(
        event["line_bytes"] > 0
        and event["line_offset"] + event["line_bytes"] == event["prefix_bytes"],
        "readiness prefix geometry drift",
    )
    if start_observation is not None or start_stdout_raw is not None:
        _require(
            start_observation is not None and start_stdout_raw is not None,
            "incomplete readiness context",
        )
        validate_observation(start_observation, start_stdout_raw, None)
        _require(
            event["plan_sha256"] == start_observation["plan_sha256"],
            "readiness plan drift",
        )
        _require(
            event["start_launch_ordinal"] == start_observation["launch_ordinal"],
            "readiness launch drift",
        )
        _require(
            event["stdout_path"] == start_observation["stdout_path"],
            "readiness stdout path drift",
        )
        _require(
            event["prefix_bytes"] <= len(start_stdout_raw),
            "readiness prefix exceeds stream",
        )
        prefix = start_stdout_raw[: event["prefix_bytes"]]
        line = prefix[event["line_offset"] :]
        _require(
            sha256_hex(prefix) == event["prefix_sha256"],
            "readiness prefix digest drift",
        )
        _require(
            sha256_hex(line) == event["line_sha256"], "readiness line digest drift"
        )
        _require(_READY_RE.fullmatch(line) is not None, "readiness line grammar drift")
        _require(
            start_stdout_raw.count(b"P01B_RESULT_READY ") == 1,
            "readiness line cardinality drift",
        )
        _require(
            start_observation["started_monotonic_ns"]
            <= event["observed_monotonic_ns"]
            <= start_observation["ended_monotonic_ns"],
            "readiness time outside spanning start",
        )
        if export_observation is not None and release_observation is not None:
            validate_observation(export_observation)
            validate_observation(release_observation)
            _require(
                event["observed_monotonic_ns"]
                <= export_observation["started_monotonic_ns"]
                < export_observation["ended_monotonic_ns"]
                <= release_observation["started_monotonic_ns"]
                < start_observation["ended_monotonic_ns"],
                "readiness/export/release order drift",
            )
    return event


def readiness_event_digest(value: Mapping[str, object]) -> str:
    validate_readiness_event(value)
    return _digest("readiness_event", value)


def _decode_b64(value: object, label: str) -> bytes:
    text = _ascii(value, label, allow_empty=True)
    try:
        raw = base64.b64decode(text.encode("ascii"), validate=True)
    except (binascii.Error, ValueError) as error:
        raise EvidenceError(label + " is not canonical base64") from error
    _require(
        base64.b64encode(raw).decode("ascii") == text, label + " base64 is noncanonical"
    )
    return raw


_RUNTIME_FIELDS = (
    "python_version",
    "implementation",
    "executable",
    "executable_chain",
    "interpreter_sha256",
    "stdlib_root",
    "stdlib_entries",
    "stdlib_sha256",
    "ldd_argv",
    "ldd_stdout_base64",
    "dependencies",
    "dependencies_sha256",
    "zlib_compile",
    "zlib_runtime",
    "libc",
    "os_release_base64",
    "packages",
    "packages_sha256",
)
_SECURITY_FIELDS = (
    "pid",
    "uid",
    "gid",
    "uid_map_base64",
    "gid_map_base64",
    "status_base64",
    "attr_current_base64",
    "namespaces",
    "oom_score_adj",
)
_MOUNTS_FIELDS = ("mountinfo_sha256", "work", "shm")
_RLIMIT_FIELDS = ("cpu", "fsize", "nofile", "core")
_CORPUS_FIELDS = (
    "focused_test_count",
    "full_test_count",
    "source_file_count",
    "test_id_digest",
)
_NORMAL_WORKLOAD_FIELDS = (
    "argv",
    "returncode",
    "signal",
    "stdout_base64",
    "stderr_base64",
    "discovered_count",
    "expected_count",
)
_PROCESS_FIELDS = (
    "pid",
    "cgroup_path",
    "oom_score_adj",
    "ready",
    "wait_signal",
    "survived",
)
_OOM_WORKLOAD_FIELDS = (
    "barrier_sha256",
    "allocation_bytes",
    "child_wait_signal",
    "parent_survived",
    "local_event_deltas",
    "terminal_processes",
)
_INVENTORY_FIELDS = ("path", "mode", "bytes", "sha256")


def _validate_inventory(value: object, label: str) -> None:
    _require(isinstance(value, list), label + " must be an array")
    paths: List[str] = []
    for item in value:
        row = _fields(item, _INVENTORY_FIELDS, label + " row")
        path = _path(row["path"], label + " path", absolute=True)
        paths.append(path)
        _require(
            _is_int(row["mode"]) and 0 <= row["mode"] <= 0o7777,
            "invalid inventory mode",
        )
        _require(_is_int(row["bytes"]) and row["bytes"] >= 0, "invalid inventory bytes")
        _sha(row["sha256"], label + " digest")
    _require(
        paths == sorted(paths) and len(paths) == len(set(paths)),
        label + " order/cardinality drift",
    )


def _validate_runtime(value: object, mode: str) -> None:
    runtime = _fields(value, _RUNTIME_FIELDS, "runtime")
    for name in (
        "python_version",
        "implementation",
        "executable",
        "stdlib_root",
        "zlib_compile",
        "zlib_runtime",
        "libc",
    ):
        _ascii(runtime[name], "runtime " + name)
    _path(runtime["executable"], "runtime executable", absolute=True)
    _path(runtime["stdlib_root"], "stdlib root", absolute=True)
    for name in ("executable_chain", "stdlib_entries", "dependencies"):
        _validate_inventory(runtime[name], name)
    for name in (
        "interpreter_sha256",
        "stdlib_sha256",
        "dependencies_sha256",
        "packages_sha256",
    ):
        _sha(runtime[name], name.replace("_", " "))
    _require(
        isinstance(runtime["ldd_argv"], list) and runtime["ldd_argv"],
        "ldd argv missing",
    )
    for item in runtime["ldd_argv"]:
        _ascii(item, "ldd argv item")
    _decode_b64(runtime["ldd_stdout_base64"], "ldd stdout")
    _decode_b64(runtime["os_release_base64"], "os-release")
    packages = runtime["packages"]
    _require(
        isinstance(packages, list)
        and all(isinstance(item, str) and item for item in packages),
        "invalid package rows",
    )
    _require(
        packages == sorted(packages) and len(packages) == len(set(packages)),
        "package row order drift",
    )
    expected_python = "3.9.6" if mode == "native-reference" else "3.11.15"
    expected_executable = (
        "/usr/bin/python3" if mode == "native-reference" else "/usr/local/bin/python3"
    )
    _require(
        runtime["python_version"] == expected_python, "runtime Python version drift"
    )
    _require(
        runtime["executable"] == expected_executable, "runtime Python executable drift"
    )


def _status_rows(raw: bytes) -> Dict[str, bytes]:
    _require(raw.endswith(b"\n"), "status framing drift")
    rows: Dict[str, bytes] = {}
    for line in raw[:-1].split(b"\n"):
        _require(b":" in line, "status row grammar drift")
        key_raw, value = line.split(b":", 1)
        try:
            key = key_raw.decode("ascii")
        except UnicodeDecodeError as error:
            raise EvidenceError("status key is not ASCII") from error
        _require(key and key not in rows, "duplicate status key")
        rows[key] = value.strip()
    return rows


def _validate_security(value: object) -> Mapping[str, object]:
    security = _fields(value, _SECURITY_FIELDS, "security")
    for name in ("pid", "uid", "gid", "oom_score_adj"):
        _require(_is_int(security[name]), "invalid security " + name)
    _require(security["pid"] > 0, "invalid security pid")
    _require(security["uid"] == security["gid"] == 65532, "container uid/gid drift")
    proc_map = b"         0          0 4294967295\n"
    _require(
        _decode_b64(security["uid_map_base64"], "uid map") == proc_map, "uid map drift"
    )
    _require(
        _decode_b64(security["gid_map_base64"], "gid map") == proc_map, "gid map drift"
    )
    status = _status_rows(_decode_b64(security["status_base64"], "status"))
    _require(status.get("NoNewPrivs") == b"1", "NoNewPrivs drift")
    _require(status.get("Seccomp") == b"2", "Seccomp mode drift")
    filters = status.get("Seccomp_filters")
    _require(
        filters is not None and re.fullmatch(rb"[1-9][0-9]*", filters) is not None,
        "Seccomp filter count drift",
    )
    for name in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"):
        _require(status.get(name) == b"0000000000000000", name + " drift")
    attr_current = _decode_b64(security["attr_current_base64"], "attr/current")
    _require(
        attr_current in (b"docker-default (enforce)\n", b"unconfined\n"),
        "LSM identity drift",
    )
    namespaces = security["namespaces"]
    _require(
        isinstance(namespaces, dict)
        and set(namespaces) == {"pid", "uts", "mnt", "net", "ipc", "cgroup", "user"},
        "namespace census drift",
    )
    for kind, item in namespaces.items():
        _require(
            isinstance(item, str)
            and _NS_RE.fullmatch(item) is not None
            and item.startswith(kind + ":["),
            "invalid namespace link",
        )
    _require(security["oom_score_adj"] == 0, "collector oom_score_adj drift")
    return security


_SCALAR_CGROUP = {
    "memory.current",
    "memory.swap.current",
    "memory.peak",
    "memory.min",
    "memory.low",
    "memory.oom.group",
    "pids.current",
}
_MAX_CGROUP = {"memory.max", "memory.high", "memory.swap.max", "pids.max"}
_KV_CGROUP = {
    "cgroup.events",
    "memory.swap.events",
    "memory.events",
    "memory.events.local",
    "pids.events",
    "cpu.stat",
}


def _parse_scalar(raw: bytes, allow_max: bool = False) -> object:
    if allow_max and raw == b"max\n":
        return "max"
    _require(
        re.fullmatch(rb"(?:0|[1-9][0-9]*)\n", raw) is not None,
        "invalid scalar cgroup grammar",
    )
    return int(raw[:-1])


def _parse_kv(raw: bytes) -> Dict[str, int]:
    _require(raw.endswith(b"\n") and raw, "invalid key/value cgroup grammar")
    result: Dict[str, int] = {}
    for line in raw[:-1].split(b"\n"):
        match = re.fullmatch(rb"([a-z_]+) (0|[1-9][0-9]*)", line)
        _require(match is not None, "invalid key/value cgroup row")
        key = match.group(1).decode("ascii")
        _require(key not in result, "duplicate cgroup key")
        result[key] = int(match.group(2))
    return result


def _validate_cgroup(value: object) -> Dict[str, object]:
    snapshot = _fields(value, ("phase", "path", "files"), "cgroup snapshot")
    _require(snapshot["phase"] in ("pre", "terminal"), "invalid cgroup phase")
    _path(snapshot["path"], "cgroup path", absolute=True)
    files = snapshot["files"]
    _require(
        isinstance(files, dict) and tuple(sorted(files)) == tuple(sorted(CGROUP_FILES)),
        "cgroup file census drift",
    )
    parsed: Dict[str, object] = {}
    for name, encoded in files.items():
        raw = _decode_b64(encoded, "cgroup " + name)
        if name == "cgroup.procs":
            _require(
                raw.endswith(b"\n")
                and all(
                    re.fullmatch(rb"[1-9][0-9]*", line)
                    for line in raw[:-1].split(b"\n")
                ),
                "invalid cgroup.procs",
            )
            parsed[name] = [int(line) for line in raw[:-1].split(b"\n")]
        elif name in _SCALAR_CGROUP:
            parsed[name] = _parse_scalar(raw)
        elif name in _MAX_CGROUP:
            parsed[name] = _parse_scalar(raw, allow_max=True)
        elif name in _KV_CGROUP:
            parsed[name] = _parse_kv(raw)
        elif name == "cpu.max":
            _require(
                re.fullmatch(rb"(max|[1-9][0-9]*) [1-9][0-9]*\n", raw) is not None,
                "invalid cpu.max",
            )
            quota, period = raw[:-1].split(b" ")
            parsed[name] = ("max" if quota == b"max" else int(quota), int(period))
    _require(parsed["memory.max"] == 536_870_912, "memory.max drift")
    _require(parsed["memory.swap.max"] == 0, "memory.swap.max drift")
    _require(
        parsed["memory.min"] == parsed["memory.low"] == 0, "memory protection drift"
    )
    _require(parsed["memory.high"] == "max", "memory.high drift")
    _require(parsed["memory.oom.group"] == 0, "memory.oom.group drift")
    _require(parsed["pids.max"] == 16, "pids.max drift")
    _require(parsed["cpu.max"] == (100_000, 100_000), "cpu.max drift")
    _require(
        parsed["memory.peak"] >= parsed["memory.current"], "memory peak/current drift"
    )
    return parsed


def _validate_mounts(value: object) -> None:
    mounts = _fields(value, _MOUNTS_FIELDS, "mounts")
    _sha(mounts["mountinfo_sha256"], "mountinfo digest")
    for name in ("work", "shm"):
        row = _fields(
            mounts[name],
            ("target", "fs_type", "options", "size_bytes", "mode", "uid", "gid"),
            name + " mount",
        )
        _path(row["target"], name + " target", absolute=True)
        _ascii(row["fs_type"], name + " fs type")
        _require(
            isinstance(row["options"], list)
            and all(isinstance(item, str) for item in row["options"]),
            "invalid mount options",
        )
        for field in ("size_bytes", "mode", "uid", "gid"):
            _require(_is_int(row[field]) and row[field] >= 0, "invalid mount " + field)
        _require(
            row["fs_type"] == "tmpfs"
            and {"rw", "nosuid", "nodev", "noexec"}.issubset(row["options"]),
            name + " tmpfs drift",
        )
        expected = (
            ("/work", 16_777_216, 0o700)
            if name == "work"
            else ("/dev/shm", 1_048_576, 0o1777)
        )
        _require(
            (row["target"], row["size_bytes"], row["mode"]) == expected,
            name + " mount identity drift",
        )
        _require(row["uid"] == row["gid"] == 65532, name + " mount ownership drift")


def _validate_rlimits(value: object) -> None:
    limits = _fields(value, _RLIMIT_FIELDS, "rlimits")
    for name in _RLIMIT_FIELDS:
        pair = limits[name]
        _require(
            isinstance(pair, list)
            and len(pair) == 2
            and all(_is_int(item) and item >= 0 for item in pair),
            "invalid rlimit " + name,
        )
    _require(
        limits
        == {
            "cpu": [900, 900],
            "fsize": [67_108_864, 67_108_864],
            "nofile": [32, 32],
            "core": [0, 0],
        },
        "rlimit identity drift",
    )


def _validate_projection(value: Mapping[str, object]) -> str:
    header = _decode_b64(value["header_ledger_base64"], "header ledger")
    inventory = _decode_b64(value["inventory_ledger_base64"], "inventory ledger")
    projection = {
        "header_ledger_sha256": sha256_hex(header),
        "inventory_ledger_sha256": sha256_hex(inventory),
        "normalized_manifest_sha256": sha256_hex(
            canonical_json_bytes(value["manifest_projection"])
        ),
        "normalized_status_sha256": sha256_hex(
            canonical_json_bytes(value["status_projection"])
        ),
    }
    projection["projection_sha256"] = domain_sha256(DOMAINS["projection"], projection)
    _require(
        value["projection_sha256"] == projection["projection_sha256"],
        "projection digest drift",
    )
    return projection["projection_sha256"]


_NATIVE_FIELDS = {
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
_NORMAL_EXTRA = {
    "input_manifest_sha256",
    "corpus_validation",
    "workload",
    "security",
    "cgroup_pre",
    "cgroup_terminal",
    "mounts",
    "rlimits",
}
_OOM_FIELDS = {
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


def _validate_probe_result_a3l5(value: object, expected_mode: str) -> Mapping[str, object]:
    _require(
        expected_mode in ("native-reference", "normal", "oom-child"),
        "unknown probe mode",
    )
    expected_fields = (
        _OOM_FIELDS
        if expected_mode == "oom-child"
        else _NATIVE_FIELDS | (_NORMAL_EXTRA if expected_mode == "normal" else set())
    )
    result = _fields(value, tuple(expected_fields), "probe result")
    _ascii(result["schema"], "probe result schema")
    _require(result["mode"] == expected_mode, "probe mode drift")
    _sha(result["probe_sha256"], "probe digest")
    if expected_mode != "oom-child":
        _decode_b64(result["fixture_base64"], "fixture")
        _decode_b64(result["header_ledger_base64"], "header ledger")
        _decode_b64(result["inventory_ledger_base64"], "inventory ledger")
        _require(
            isinstance(result["manifest_projection"], dict)
            and isinstance(result["status_projection"], dict),
            "projection must be objects",
        )
        _require(
            isinstance(result["excluded_telemetry"], dict),
            "excluded telemetry must be an object",
        )
        _sha(result["projection_sha256"], "projection digest")
        _validate_projection(result)
        _validate_runtime(result["runtime"], expected_mode)
    if expected_mode in ("normal", "oom-child"):
        _sha(result["input_manifest_sha256"], "input manifest digest")
        security = _validate_security(result["security"])
        cgroup_pre = _validate_cgroup(result["cgroup_pre"])
        cgroup_terminal = _validate_cgroup(result["cgroup_terminal"])
        _require(
            result["cgroup_pre"]["phase"] == "pre"
            and result["cgroup_terminal"]["phase"] == "terminal",
            "cgroup phase order drift",
        )
        _require(
            result["cgroup_pre"]["path"] == result["cgroup_terminal"]["path"],
            "cgroup path drift",
        )
        _validate_mounts(result["mounts"])
        _validate_rlimits(result["rlimits"])
        for census in (
            "memory.events",
            "memory.events.local",
            "memory.swap.events",
            "pids.events",
            "cpu.stat",
        ):
            before = cgroup_pre[census]
            after = cgroup_terminal[census]
            _require(set(before) == set(after), census + " key census drift")
            _require(
                all(after[key] >= before[key] for key in before),
                census + " counter decreased",
            )
    if expected_mode == "normal":
        corpus = _fields(
            result["corpus_validation"], _CORPUS_FIELDS, "corpus validation"
        )
        _require(
            (
                corpus["focused_test_count"],
                corpus["full_test_count"],
                corpus["source_file_count"],
            )
            == (68, 151, 11),
            "corpus census drift",
        )
        _sha(corpus["test_id_digest"], "test id digest")
        workload = _fields(
            result["workload"], _NORMAL_WORKLOAD_FIELDS, "normal workload"
        )
        _require(
            isinstance(workload["argv"], list) and workload["argv"],
            "normal argv missing",
        )
        _require(
            workload["returncode"] == 0 and workload["signal"] is None,
            "normal workload failed",
        )
        _decode_b64(workload["stdout_base64"], "normal stdout")
        _decode_b64(workload["stderr_base64"], "normal stderr")
        _require(
            workload["discovered_count"] == workload["expected_count"] == 151,
            "normal test count drift",
        )
        _require(
            cgroup_terminal["cgroup.procs"] == [security["pid"]],
            "normal terminal process census drift",
        )
        for census in (
            "memory.events",
            "memory.events.local",
            "memory.swap.events",
            "pids.events",
        ):
            _require(
                cgroup_pre[census] == cgroup_terminal[census],
                "normal event delta drift",
            )
    elif expected_mode == "oom-child":
        for name in ("parent", "child"):
            process = _fields(result[name], _PROCESS_FIELDS, name)
            _require(
                _is_int(process["pid"]) and process["pid"] > 0, "invalid process pid"
            )
            _path(process["cgroup_path"], name + " cgroup path", absolute=True)
            _require(_is_int(process["oom_score_adj"]), "invalid oom_score_adj")
            _require(
                isinstance(process["ready"], bool)
                and isinstance(process["survived"], bool),
                "invalid process state",
            )
            _require(
                process["wait_signal"] is None
                or (_is_int(process["wait_signal"]) and process["wait_signal"] > 0),
                "invalid wait signal",
            )
        workload = _fields(result["workload"], _OOM_WORKLOAD_FIELDS, "OOM workload")
        _sha(workload["barrier_sha256"], "OOM barrier digest")
        _require(
            workload["allocation_bytes"] == 640 * 1024 * 1024, "OOM allocation drift"
        )
        _require(
            workload["child_wait_signal"] == 9 and workload["parent_survived"] is True,
            "OOM outcome drift",
        )
        deltas = _fields(
            workload["local_event_deltas"],
            ("oom", "oom_kill", "oom_group_kill"),
            "OOM deltas",
        )
        _require(
            _is_int(deltas["oom"])
            and deltas["oom"] >= 1
            and deltas["oom_kill"] == 1
            and deltas["oom_group_kill"] == 0,
            "OOM deltas drift",
        )
        _require(
            isinstance(workload["terminal_processes"], list)
            and workload["terminal_processes"] == [result["parent"]["pid"]],
            "terminal cgroup process drift",
        )
        _require(
            security["pid"] == result["parent"]["pid"], "OOM collector identity drift"
        )
        _require(
            result["parent"]["cgroup_path"]
            == result["child"]["cgroup_path"]
            == result["cgroup_pre"]["path"],
            "OOM cgroup identity drift",
        )
        _require(
            result["parent"]["oom_score_adj"] == 0
            and result["child"]["oom_score_adj"] == 1000,
            "OOM score adjustment drift",
        )
        _require(
            result["parent"]["ready"] is True
            and result["parent"]["survived"] is True
            and result["parent"]["wait_signal"] is None,
            "OOM collector state drift",
        )
        _require(
            result["child"]["ready"] is True
            and result["child"]["survived"] is False
            and result["child"]["wait_signal"] == 9,
            "OOM child state drift",
        )
        _require(
            sorted(cgroup_pre["cgroup.procs"])
            == sorted([result["parent"]["pid"], result["child"]["pid"]]),
            "OOM pre process census drift",
        )
        _require(
            cgroup_terminal["cgroup.procs"] == [result["parent"]["pid"]],
            "OOM terminal process census drift",
        )
        local_before = cgroup_pre["memory.events.local"]
        local_after = cgroup_terminal["memory.events.local"]
        for key in ("oom", "oom_kill", "oom_group_kill"):
            _require(
                local_after.get(key, 0) - local_before.get(key, 0) == deltas[key],
                "OOM local event correspondence drift",
            )
    return result


def _parse_octal(field: bytes, digits: int, label: str) -> int:
    _require(
        len(field) == digits + 1 and field[-1:] == b"\0", label + " terminator drift"
    )
    body = field[:-1]
    _require(
        re.fullmatch(rb"[0-7]{" + str(digits).encode("ascii") + rb"}", body)
        is not None,
        label + " is not canonical octal",
    )
    return int(body, 8)


def parse_docker_copy_tar(raw: bytes) -> bytes:
    """Parse the frozen one-member USTAR language without extraction."""
    _require(isinstance(raw, bytes), "TAR input must be bytes")
    _require(512 + 1 + 1024 <= len(raw) <= MAX_TAR_BYTES, "TAR size out of range")
    _require(len(raw) % 512 == 0, "TAR length is not block aligned")
    header = raw[:512]
    _require(header[0:100] == b"result.json" + b"\0" * 89, "TAR name drift")
    _require(_parse_octal(header[100:108], 7, "mode") == 0o600, "TAR mode drift")
    _require(_parse_octal(header[108:116], 7, "uid") == 65532, "TAR uid drift")
    _require(_parse_octal(header[116:124], 7, "gid") == 65532, "TAR gid drift")
    size = _parse_octal(header[124:136], 11, "size")
    _require(1 <= size <= MAX_RESULT_BYTES, "TAR payload size out of range")
    _require(_parse_octal(header[136:148], 11, "mtime") == 0, "TAR mtime drift")
    checksum_field = header[148:156]
    _require(
        re.fullmatch(rb"[0-7]{6}\0 ", checksum_field) is not None,
        "TAR checksum encoding drift",
    )
    expected_checksum = int(checksum_field[:6], 8)
    checksum_header = header[:148] + b" " * 8 + header[156:]
    _require(sum(checksum_header) == expected_checksum, "TAR checksum drift")
    _require(header[156:157] == b"0", "TAR typeflag drift")
    _require(header[157:257] == b"\0" * 100, "TAR linkname drift")
    _require(
        header[257:263] == b"ustar\0" and header[263:265] == b"00",
        "USTAR identity drift",
    )
    _require(header[265:329] == b"\0" * 64, "USTAR owner names drift")
    _require(_parse_octal(header[329:337], 7, "devmajor") == 0, "TAR devmajor drift")
    _require(_parse_octal(header[337:345], 7, "devminor") == 0, "TAR devminor drift")
    _require(header[345:512] == b"\0" * 167, "USTAR prefix/unused bytes drift")
    payload_end = 512 + size
    padded_end = 512 + ((size + 511) // 512) * 512
    _require(padded_end + 1024 <= len(raw), "TAR terminal blocks missing")
    _require(
        raw[payload_end:padded_end] == b"\0" * (padded_end - payload_end),
        "TAR payload padding drift",
    )
    _require(
        raw[padded_end:] == b"\0" * (len(raw) - padded_end), "TAR trailing data drift"
    )
    _require(len(raw) - padded_end >= 1024, "TAR needs two zero blocks")
    payload = raw[512:payload_end]
    strict_json_bytes(payload, MAX_RESULT_BYTES)
    return payload


CERTIFICATE_FIELDS = (
    "schema",
    "kind",
    "predicate_schema",
    "authorization_sha256",
    "implementation_commit",
    "attempt_id",
    "subject_manifest_sha256",
    "observation_sha256",
    "predicates",
    "accepted_evidence_created",
    "level2_plus_created",
    "authority_granted",
)
_PREDICATE_FIELDS = {
    "ingress-v1": (
        "source_count",
        "source_manifest_sha256",
        "snapshot_manifest_sha256",
        "source_descriptor_observation_sha256",
        "snapshot_descriptor_observation_sha256",
        "container_mount_read_only",
    ),
    "egress-v1": (
        "readiness_event_sha256",
        "start_observation_sha256",
        "export_observation_sha256",
        "raw_tar_sha256",
        "result_sha256",
        "result_bytes",
        "release_observation_sha256",
        "ordering_valid",
    ),
    "cleanup-v1": (
        "container_id",
        "container_name",
        "labels_sha256",
        "remove_observation_sha256",
        "cid_absence_observation_sha256",
        "name_absence_observation_sha256",
        "label_absence_observation_sha256",
        "daemon_recheck_observation_sha256",
        "absent",
    ),
}


def validate_certificate(value: object) -> Mapping[str, object]:
    certificate = _fields(value, CERTIFICATE_FIELDS, "certificate")
    _require(
        certificate["schema"] == SCHEMAS["certificate"], "certificate schema drift"
    )
    _require(
        certificate["kind"] in ("ingress", "egress", "cleanup"),
        "unknown certificate kind",
    )
    predicate_schema = certificate["predicate_schema"]
    _require(
        predicate_schema == certificate["kind"] + "-v1",
        "certificate predicate schema drift",
    )
    predicates = _fields(
        certificate["predicates"],
        _PREDICATE_FIELDS[predicate_schema],
        "certificate predicates",
    )
    _sha(certificate["authorization_sha256"], "certificate authorization digest")
    _git(certificate["implementation_commit"], "certificate implementation commit")
    _identifier(certificate["attempt_id"], "certificate attempt id")
    _sha(certificate["subject_manifest_sha256"], "certificate subject digest")
    _sha(certificate["observation_sha256"], "certificate observation digest")
    for name, item in predicates.items():
        if name.endswith("_sha256"):
            _sha(item, "predicate " + name)
    if predicate_schema == "ingress-v1":
        _require(
            predicates["source_count"] == len(SNAPSHOT_PATHS)
            and predicates["container_mount_read_only"] is True,
            "ingress predicate drift",
        )
    elif predicate_schema == "egress-v1":
        _require(
            _is_int(predicates["result_bytes"])
            and 1 <= predicates["result_bytes"] <= MAX_RESULT_BYTES
            and predicates["ordering_valid"] is True,
            "egress predicate drift",
        )
    else:
        _require(
            isinstance(predicates["container_id"], str)
            and _CID_RE.fullmatch(predicates["container_id"]) is not None,
            "cleanup CID drift",
        )
        _ascii(predicates["container_name"], "cleanup container name")
        _require(predicates["absent"] is True, "cleanup absence not established")
    _false_authority(certificate)
    return certificate


def build_certificate(
    kind: str,
    authorization_sha256: str,
    implementation_commit: str,
    attempt_id: str,
    subject_manifest_sha256: str,
    observation_sha256: str,
    predicates: Mapping[str, object],
) -> Dict[str, object]:
    value = {
        "schema": SCHEMAS["certificate"],
        "kind": kind,
        "predicate_schema": kind + "-v1",
        "authorization_sha256": authorization_sha256,
        "implementation_commit": implementation_commit,
        "attempt_id": attempt_id,
        "subject_manifest_sha256": subject_manifest_sha256,
        "observation_sha256": observation_sha256,
        "predicates": dict(predicates),
        "accepted_evidence_created": False,
        "level2_plus_created": False,
        "authority_granted": False,
    }
    validate_certificate(value)
    return value


def certificate_digest(value: Mapping[str, object]) -> str:
    validate_certificate(value)
    return _digest("certificate", value)


def _class_results(value: object, label: str) -> List[Mapping[str, object]]:
    _require(isinstance(value, list), label + " must be an array")
    rows = [_fields(item, ("class_id", "closed"), label + " row") for item in value]
    _require(
        tuple(row["class_id"] for row in rows) == CLASS_ORDER,
        label + " class order drift",
    )
    _require(
        all(isinstance(row["closed"], bool) for row in rows),
        label + " contains nonboolean result",
    )
    return rows


# Phase 796-A3L6 semantic reconstruction.  The public dispatcher below is the
# only class-closing entry point and never derives truth from path presence.

_SEMANTIC_PLACEHOLDER_SCHEMAS = {
    "hsai-p01b-test-placeholder-v1",
    "hsai-p01b-retained-placeholder-v1",
}
_MANIFEST_EXCLUDED_FIELDS = (
    "python_version", "zlib_version", "archive_device", "archive_inode",
    "archive_mode", "archive_owner_uid", "archive_link_count",
    "archive_modified_seconds", "archive_modified_nanoseconds",
    "archive_changed_seconds", "archive_changed_nanoseconds",
)
_STATUS_EXCLUDED_FIELDS = ("manifest_bytes", "manifest_sha256")


def _semantic_json(files: Mapping[str, bytes], path: str) -> Mapping[str, object]:
    raw = files.get(path)
    _require(isinstance(raw, bytes) and raw not in (b"", b"{}", b"x"),
             "semantic JSON is absent or placeholder: " + path)
    limit = (
        MAX_A3L6_GATE_JSON_BYTES
        if path == A3L6_GATE_BUNDLE_PATH
        else MAX_RESULT_BYTES
    )
    value = strict_json_bytes(raw, limit)
    _require(isinstance(value, dict) and value.get("schema") not in _SEMANTIC_PLACEHOLDER_SCHEMAS,
             "semantic JSON is not a retained object: " + path)
    return value


def _semantic_json_value(files: Mapping[str, bytes], path: str) -> object:
    raw = files.get(path)
    _require(isinstance(raw, bytes) and raw not in (b"", b"{}", b"x"),
             "semantic JSON value is absent or placeholder: " + path)
    return strict_json_bytes(raw, MAX_RESULT_BYTES)


def _snapshot_semantics(files: Mapping[str, bytes], bindings: Mapping[str, object]) -> Mapping[str, object]:
    pair = _fields(
        _semantic_json(files, "snapshot/source-manifest.json"),
        ("schema", "implementation_commit", "implementation_tree", "source_manifest", "snapshot_manifest"),
        "snapshot manifest pair",
    )
    _require(pair["schema"] == SCHEMAS["snapshot_pair"], "snapshot pair schema drift")
    _require(pair["implementation_commit"] == bindings["implementation_commit"] and
             pair["implementation_tree"] == bindings["implementation_tree"],
             "snapshot implementation binding drift")
    manifests = []
    for key, schema_name, domain_name, expected_digest, expected_mode in (
        ("source_manifest", "snapshot_source", "snapshot_source", bindings["snapshot_source_manifest_sha256"], None),
        ("snapshot_manifest", "snapshot_copy", "snapshot_copy", bindings["snapshot_copy_manifest_sha256"], 0o444),
    ):
        manifest_value = _fields(pair[key], ("schema", "ordered_entries"), key.replace("_", " "))
        _require(manifest_value["schema"] == SCHEMAS[schema_name], key + " schema drift")
        entries = manifest_value["ordered_entries"]
        _require(isinstance(entries, list) and len(entries) == len(SNAPSHOT_PATHS), key + " census drift")
        checked = []
        for entry, path in zip(entries, SNAPSHOT_PATHS):
            row = _fields(entry, ("path", "mode", "bytes", "sha256", "descriptor_observation_sha256"), key + " entry")
            _require(row["path"] == path and _is_int(row["mode"]), key + " path/mode drift")
            if expected_mode is not None:
                _require(row["mode"] == expected_mode, "snapshot copy mode drift")
            _nonnegative(row["bytes"], key + " bytes"); _sha(row["sha256"], key + " digest")
            _sha(row["descriptor_observation_sha256"], key + " descriptor digest")
            raw = files["snapshot/files/" + path]
            _require(len(raw) == row["bytes"] and sha256_hex(raw) == row["sha256"],
                     "snapshot retained bytes drift: " + path)
            checked.append(row)
        digest = _digest(domain_name, manifest_value)
        _require(digest == expected_digest, key + " expected digest drift")
        manifests.append((manifest_value, checked, digest))
    source_entries = manifests[0][1]
    copy_entries = manifests[1][1]
    for source, copied in zip(source_entries, copy_entries):
        _require(source["path"] == copied["path"] and source["bytes"] == copied["bytes"] and
                 source["sha256"] == copied["sha256"], "snapshot source/copy correspondence drift")
    copy_root = None
    descriptor_sets = {}
    for path, kind, manifest_digest_value, entries in (
        ("snapshot/source-descriptor-observations.json", "source", manifests[0][2], source_entries),
        ("snapshot/ingress-observations.json", "snapshot", manifests[1][2], copy_entries),
    ):
        descriptor_set = validate_descriptor_set(_semantic_json(files, path))
        descriptor_sets[kind] = descriptor_set
        _require(descriptor_set["kind"] == kind and descriptor_set["manifest_sha256"] == manifest_digest_value,
                 kind + " descriptor manifest drift")
        for observation, entry in zip(descriptor_set["ordered_observations"], entries):
            _require(descriptor_observation_digest(observation) == entry["descriptor_observation_sha256"] and
                     observation["sha256"] == entry["sha256"] and
                     observation["before"]["size"] == entry["bytes"],
                     kind + " descriptor byte binding drift")
            if kind == "snapshot":
                suffix = "/" + entry["path"]
                _require(observation["path"].endswith(suffix), "snapshot descriptor root drift")
                observed_root = observation["path"][:-len(suffix)]
                _path(observed_root, "snapshot copy root", absolute=True)
                if copy_root is None:
                    copy_root = observed_root
                _require(observed_root == copy_root, "snapshot copy root changed")
    _require(isinstance(copy_root, str), "snapshot copy root missing")
    return {"pair": pair, "source_entries": source_entries, "copy_entries": copy_entries,
            "source_sha256": manifests[0][2], "copy_sha256": manifests[1][2],
            "copy_root": copy_root, "source_descriptor_set": descriptor_sets["source"],
            "copy_descriptor_set": descriptor_sets["snapshot"]}


def _projection_semantics(result: Mapping[str, object], label: str) -> None:
    excluded = _fields(result.get("excluded_telemetry"), ("manifest", "status"), label + " excluded telemetry")
    _require(tuple(excluded["manifest"]) == _MANIFEST_EXCLUDED_FIELDS and
             tuple(excluded["status"]) == _STATUS_EXCLUDED_FIELDS,
             label + " excluded telemetry census drift")
    _validate_projection(result)


def _runtime_core(result: Mapping[str, object], label: str) -> Mapping[str, object]:
    runtime = result.get("runtime")
    _require(isinstance(runtime, dict), label + " runtime missing")
    for field in ("python_version", "executable", "interpreter_sha256", "executable_chain"):
        _require(field in runtime, label + " runtime field missing: " + field)
    _path(runtime["executable"], label + " executable", absolute=True)
    _sha(runtime["interpreter_sha256"], label + " interpreter digest")
    chain = runtime["executable_chain"]
    _require(isinstance(chain, list) and chain, label + " executable chain missing")
    terminal = chain[-1]
    terminal = _fields(terminal, ("kind", "path", "mode", "target_base64", "bytes", "sha256"), label + " terminal executable")
    _require(terminal["kind"] == "regular" and terminal["target_base64"] is None and
             terminal["sha256"] == runtime["interpreter_sha256"], label + " terminal interpreter drift")
    return runtime


def _reconstruct_c02(files: Mapping[str, bytes], bindings: Mapping[str, object], snapshot: Mapping[str, object]) -> bool:
    native = _semantic_json(files, "reference/native-result.json")
    normal = _semantic_json(files, "attempts/normal/result.json")
    _require(native.get("schema") == normal.get("schema") == SCHEMAS["probe_result"] and
             native.get("mode") == "native-reference" and normal.get("mode") == "normal",
             "C02 probe schema/mode drift")
    for field in ("probe_sha256", "projection_sha256"):
        _sha(native.get(field), "native " + field); _require(native[field] == normal.get(field), "C02 " + field + " drift")
    for field in ("fixture_base64", "header_ledger_base64", "inventory_ledger_base64",
                  "manifest_projection", "status_projection"):
        _require(native.get(field) == normal.get(field), "C02 projection input drift: " + field)
    _projection_semantics(native, "native"); _projection_semantics(normal, "normal")
    projection = _fields(_semantic_json(files, "reference/projection.json"),
                         ("schema", "probe_sha256", "projection_sha256"), "reference projection")
    _require(projection["schema"] == "hsai-p01b-reference-projection-v1" and
             projection["probe_sha256"] == native["probe_sha256"] and
             projection["projection_sha256"] == native["projection_sha256"],
             "C02 reference projection drift")
    probe_entry = next(row for row in snapshot["copy_entries"] if row["path"].endswith("p01b_container_probe.py"))
    _require(native["probe_sha256"] == probe_entry["sha256"], "C02 probe snapshot binding drift")
    _require(normal.get("input_manifest_sha256") == snapshot["copy_sha256"], "C02 input manifest drift")
    native_runtime = _runtime_core(native, "native")
    normal_runtime = _runtime_core(normal, "normal")
    _require((native_runtime["executable"], native_runtime["interpreter_sha256"], native_runtime["python_version"]) ==
             (bindings["native_python_path"], bindings["native_python_sha256"], bindings["native_python_version"]),
             "C02 native interpreter binding drift")
    _require(normal_runtime["executable"] == bindings["normal_python_path"] and
             normal_runtime["python_version"] == bindings["normal_python_version"],
             "C02 normal interpreter binding drift")
    return True


def _cgroup_raw_map(snapshot: object, label: str) -> Mapping[str, bytes]:
    row = _fields(snapshot, ("phase", "path", "observed_monotonic_ns", "files", "raw_files_base64"), label)
    _path(row["path"], label + " path", absolute=True); _nonnegative(row["observed_monotonic_ns"], label + " time")
    raw_map = row["raw_files_base64"]
    _require(isinstance(raw_map, dict) and set(raw_map) == set(CGROUP_FILES), label + " raw census drift")
    result = {name: _decode_b64(raw_map[name], label + " " + name) for name in CGROUP_FILES}
    normalized = row["files"]
    _require(isinstance(normalized, dict) and set(normalized) == set(CGROUP_FILES), label + " normalized census drift")
    for name, raw in result.items():
        if name == "cgroup.procs":
            parsed = [int(item) for item in raw.rstrip(b"\n").split(b"\n")]
        elif name == "cpu.max":
            quota, period = raw.rstrip(b"\n").split(b" "); parsed = ["max" if quota == b"max" else int(quota), int(period)]
        elif name in _KV_CGROUP:
            parsed = _parse_kv(raw)
        else:
            parsed = _parse_scalar(raw, allow_max=name in _MAX_CGROUP)
        _require(normalized[name] == parsed, label + " raw/normalized drift: " + name)
    return result


def _reconstruct_c03(files: Mapping[str, bytes], snapshot: Mapping[str, object]) -> bool:
    result = _semantic_json(files, "attempts/oom/result.json")
    _require(result.get("schema") == SCHEMAS["probe_result"] and result.get("mode") == "oom-child",
             "C03 probe schema/mode drift")
    _require(result.get("input_manifest_sha256") == snapshot["copy_sha256"], "C03 input manifest drift")
    workload = result.get("workload")
    _require(isinstance(workload, dict), "C03 workload missing")
    transcript = _decode_b64(workload.get("barrier_transcript_base64"), "OOM barrier")
    _require(transcript == b"P01B_OOM_CHILD_READY\nP01B_OOM_CHILD_RELEASE\n" and
             workload.get("barrier_sha256") == sha256_hex(transcript), "C03 barrier drift")
    order = [workload.get(name) for name in (
        "child_cgroup_read_monotonic_ns", "score_write_monotonic_ns",
        "score_readback_monotonic_ns", "child_ready_monotonic_ns",
        "release_monotonic_ns", "allocation_started_monotonic_ns", "child_wait_monotonic_ns")]
    _require(all(_is_int(item) for item in order) and order[0] < order[1] < order[2] <= order[3] < order[4] < order[5] < order[6],
             "C03 event order drift")
    raw_wait = workload.get("raw_wait_status")
    _require(_is_int(raw_wait) and raw_wait & 0x7f == 9 and workload.get("child_wait_signal") == 9,
             "C03 raw wait status is not SIGKILL")
    parent = result.get("parent"); child = result.get("child")
    _require(isinstance(parent, dict) and isinstance(child, dict), "C03 process records missing")
    _require(_decode_b64(child.get("oom_score_adj_base64"), "child OOM score") == b"1000\n" and
             child.get("oom_score_adj") == 1000 and child.get("wait_signal") == 9 and child.get("survived") is False,
             "C03 child readback/outcome drift")
    pre_raw = _cgroup_raw_map(result.get("cgroup_pre"), "OOM cgroup pre")
    terminal_raw = _cgroup_raw_map(result.get("cgroup_terminal"), "OOM cgroup terminal")
    _require(result["cgroup_pre"]["observed_monotonic_ns"] < result["cgroup_terminal"]["observed_monotonic_ns"], "C03 cgroup order drift")
    for name in ("memory.events", "memory.events.local"):
        before = _parse_kv(pre_raw[name]); after = _parse_kv(terminal_raw[name])
        _require(after.get("oom", 0) > before.get("oom", 0) and
                 after.get("oom_kill", 0) - before.get("oom_kill", 0) == 1 and
                 after.get("oom_group_kill", 0) == before.get("oom_group_kill", 0),
                 "C03 OOM counter drift: " + name)
    _require(files.get("operations/oom/008-wait/stdout.bin") == b"0\n", "C03 container wait transcript drift")
    return True


def _security_semantics(result: Mapping[str, object], label: str) -> Mapping[str, object]:
    security = _fields(
        result.get("security"),
        tuple(_SECURITY_FIELDS) + ("cgroup_base64", "oom_score_adj_base64"),
        label + " security",
    )
    _require(
        _is_int(security["pid"])
        and security["pid"] > 0
        and security["uid"] == security["gid"] == 65532
        and security["oom_score_adj"] == 0,
        label + " security identity drift",
    )
    proc_map = b"         0          0 4294967295\n"
    _require(
        _decode_b64(security["uid_map_base64"], label + " uid map") == proc_map
        and _decode_b64(security["gid_map_base64"], label + " gid map") == proc_map,
        label + " uid/gid map drift",
    )
    status = _status_rows(_decode_b64(security["status_base64"], label + " status"))
    expected_ids = b"65532\t65532\t65532\t65532"
    _require(
        status.get("Uid") == expected_ids
        and status.get("Gid") == expected_ids
        and status.get("NoNewPrivs") == b"1"
        and status.get("Seccomp") == b"2"
        and re.fullmatch(rb"[1-9][0-9]*", status.get("Seccomp_filters", b"")) is not None,
        label + " proc status drift",
    )
    for name in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"):
        _require(status.get(name) == b"0000000000000000", label + " " + name + " drift")
    cgroup_raw = _decode_b64(security["cgroup_base64"], label + " proc cgroup")
    match = re.fullmatch(rb"0::(/[^\n]*)\n", cgroup_raw)
    _require(match is not None, label + " proc cgroup grammar drift")
    cgroup_path = match.group(1).decode("ascii")
    _require(
        cgroup_path == result["cgroup_pre"]["path"] == result["cgroup_terminal"]["path"],
        label + " proc/cgroup path drift",
    )
    _require(
        _decode_b64(security["oom_score_adj_base64"], label + " oom score") == b"0\n",
        label + " collector oom score drift",
    )
    namespaces = security["namespaces"]
    _require(
        isinstance(namespaces, dict)
        and set(namespaces) == {"pid", "uts", "mnt", "net", "ipc", "cgroup", "user"},
        label + " namespace census drift",
    )
    for kind, value in namespaces.items():
        _require(
            isinstance(value, str)
            and value.startswith(kind + ":[")
            and _NS_RE.fullmatch(value) is not None,
            label + " namespace identity drift",
        )
    attr_current = _decode_b64(security["attr_current_base64"], label + " attr/current")
    _require(
        attr_current in (b"docker-default (enforce)\n", b"unconfined\n"),
        label + " LSM identity drift",
    )
    return {"security": security, "attr_current": attr_current, "namespaces": namespaces}


def _inspect_semantics(files: Mapping[str, bytes], path: str, state: str) -> Tuple[Mapping[str, object], Mapping[str, object]]:
    raw = _semantic_json_value(files, path)
    _require(isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], dict), path + " inspect framing drift")
    inspect = raw[0]
    projection = {name: _dotted(inspect, name) for name in INSPECT_FIELDS}
    validate_inspect_evaluation(inspect, projection, state)
    return inspect, projection


def _reconstruct_c04(files: Mapping[str, bytes], bindings: Mapping[str, object]) -> bool:
    normal = _semantic_json(files, "attempts/normal/result.json")
    oom = _semantic_json(files, "attempts/oom/result.json")
    normal_security = _security_semantics(normal, "normal")
    oom_security = _security_semantics(oom, "OOM")
    for process_name in ("parent", "child"):
        process = _fields(
            oom.get(process_name),
            tuple(_PROCESS_FIELDS) + ("cgroup_base64", "oom_score_adj_base64", "namespaces"),
            "OOM " + process_name,
        )
        _require(
            _decode_b64(process["cgroup_base64"], process_name + " cgroup")
            == _decode_b64(oom_security["security"]["cgroup_base64"], "OOM security cgroup"),
            process_name + " cgroup readback drift",
        )
        _require(
            _decode_b64(process["oom_score_adj_base64"], process_name + " oom score")
            == (str(process["oom_score_adj"]) + "\n").encode("ascii"),
            process_name + " oom score readback drift",
        )
        _require(process["namespaces"] == oom_security["namespaces"], process_name + " namespace drift")
    seccomp_raw = files.get("snapshot/files/tools/hsai-formal-preflight/p01b_container_seccomp.json")
    _require(isinstance(seccomp_raw, bytes) and sha256_hex(seccomp_raw) == bindings["seccomp_sha256"], "C04 seccomp snapshot binding drift")
    seccomp = strict_json_bytes(seccomp_raw, MAX_RESULT_BYTES)
    _require(isinstance(seccomp, dict) and seccomp, "C04 seccomp profile missing")
    for attempt, security in (("normal", normal_security), ("oom", oom_security)):
        _, pre = _inspect_semantics(files, "attempts/{}/inspect-prestart.json".format(attempt), "prestart")
        _, terminal = _inspect_semantics(files, "attempts/{}/inspect-terminal.json".format(attempt), "terminal")
        permitted_changes = {
            "NetworkSettings.Networks", "State.Status", "State.Running", "State.ExitCode",
            "State.OOMKilled", "State.Error", "State.Pid", "State.StartedAt", "State.FinishedAt",
        }
        for name in INSPECT_FIELDS:
            if name not in permitted_changes:
                _require(pre[name] == terminal[name], "C04 inspect invariant drift: " + name)
        _require(
            pre["Platform"] == "linux"
            and pre["HostConfig.Runtime"] == "runc"
            and pre["HostConfig.NetworkMode"] == "none"
            and pre["HostConfig.IpcMode"] == "private"
            and pre["HostConfig.PidMode"] == pre["HostConfig.UTSMode"] == ""
            and pre["HostConfig.CgroupnsMode"] == "private"
            and pre["HostConfig.CgroupParent"] == pre["HostConfig.UsernsMode"] == ""
            and pre["HostConfig.ReadonlyRootfs"] is True
            and pre["HostConfig.Privileged"] is False
            and pre["HostConfig.CapAdd"] is None
            and pre["HostConfig.CapDrop"] == ["ALL"]
            and pre["HostConfig.Memory"] == pre["HostConfig.MemorySwap"] == 536870912
            and pre["HostConfig.MemorySwappiness"] == 0
            and pre["HostConfig.OomKillDisable"] is False
            and pre["HostConfig.PidsLimit"] == 16
            and pre["HostConfig.CpuPeriod"] == pre["HostConfig.CpuQuota"] == 100000
            and pre["HostConfig.ShmSize"] == 1048576
            and pre["HostConfig.AutoRemove"] is False
            and pre["HostConfig.Devices"] == []
            and pre["HostConfig.DeviceRequests"] is None
            and pre["HostConfig.GroupAdd"] is None,
            "C04 targeted inspect controls drift",
        )
        security_opt = pre["HostConfig.SecurityOpt"]
        _require(
            isinstance(security_opt, list)
            and set(security_opt) == {"no-new-privileges:true", "seccomp=" + seccomp_raw.decode("ascii")},
            "C04 seccomp inspect binding drift",
        )
        expected_profile = "docker-default" if security["attr_current"] == b"docker-default (enforce)\n" else ""
        _require(pre["AppArmorProfile"] == expected_profile, "C04 LSM/inspect correspondence drift")
        mounts = pre["Mounts"]
        _require(
            isinstance(mounts, list)
            and len(mounts) == 1
            and mounts[0].get("Type") == "bind"
            and mounts[0].get("Destination") == "/input"
            and mounts[0].get("RW") is False
            and mounts[0].get("Propagation") == "rprivate",
            "C04 input mount drift",
        )
    return True


def _cgroup_values(snapshot: object, label: str) -> Mapping[str, object]:
    raw = _cgroup_raw_map(snapshot, label)
    values = snapshot["files"]
    _require(
        values["memory.max"] == 536870912
        and values["memory.swap.max"] == 0
        and values["memory.min"] == values["memory.low"] == 0
        and values["memory.high"] == "max"
        and values["memory.oom.group"] == 0
        and values["pids.max"] == 16
        and values["cpu.max"] == [100000, 100000]
        and values["memory.peak"] >= values["memory.current"],
        label + " cgroup controls drift",
    )
    _require(set(values["cgroup.events"]) == {"populated", "frozen"}, label + " cgroup.events census drift")
    return values


def _reconstruct_c05(files: Mapping[str, bytes]) -> bool:
    results = {
        "normal": _semantic_json(files, "attempts/normal/result.json"),
        "oom": _semantic_json(files, "attempts/oom/result.json"),
    }
    parsed = {}
    for attempt, result in results.items():
        pre = _cgroup_values(result.get("cgroup_pre"), attempt + " cgroup pre")
        terminal = _cgroup_values(result.get("cgroup_terminal"), attempt + " cgroup terminal")
        _require(result["cgroup_pre"]["path"] == result["cgroup_terminal"]["path"], attempt + " cgroup path drift")
        _require(result["cgroup_pre"]["observed_monotonic_ns"] < result["cgroup_terminal"]["observed_monotonic_ns"], attempt + " cgroup order drift")
        for name in ("memory.events", "memory.events.local", "memory.swap.events", "pids.events", "cpu.stat"):
            _require(set(pre[name]) == set(terminal[name]), attempt + " " + name + " key census drift")
            _require(all(terminal[name][key] >= pre[name][key] for key in pre[name]), attempt + " " + name + " counter decreased")
        parsed[attempt] = (pre, terminal)
    normal_pre, normal_terminal = parsed["normal"]
    for name in ("memory.events", "memory.events.local", "memory.swap.events", "pids.events"):
        _require(normal_pre[name] == normal_terminal[name], "C05 normal event delta drift: " + name)
    normal_security = _security_semantics(results["normal"], "normal")
    _require(normal_terminal["cgroup.procs"] == [normal_security["security"]["pid"]], "C05 normal process census drift")
    oom_pre, oom_terminal = parsed["oom"]
    deltas = _fields(results["oom"].get("workload", {}).get("local_event_deltas"), ("oom", "oom_kill", "oom_group_kill"), "OOM event deltas")
    _require(_is_int(deltas["oom"]) and deltas["oom"] >= 1 and deltas["oom_kill"] == 1 and deltas["oom_group_kill"] == 0, "C05 OOM delta contract drift")
    for name in ("memory.events", "memory.events.local"):
        for key in ("oom", "oom_kill", "oom_group_kill"):
            _require(oom_terminal[name].get(key, 0) - oom_pre[name].get(key, 0) == deltas[key], "C05 OOM event delta drift: " + name + "/" + key)
    for name in ("memory.swap.events", "pids.events"):
        _require(oom_pre[name] == oom_terminal[name], "C05 OOM non-memory event drift: " + name)
    parent = results["oom"].get("parent", {}).get("pid")
    child = results["oom"].get("child", {}).get("pid")
    _require(sorted(oom_pre["cgroup.procs"]) == sorted([parent, child]) and oom_terminal["cgroup.procs"] == [parent], "C05 OOM process census drift")
    return True


def _receipt_wrapper(files: Mapping[str, bytes], namespace: str, plan: Mapping[str, object], basenames: Sequence[str], wrapper_path: str) -> List[Mapping[str, object]]:
    items = []
    for basename in basenames:
        base = "operations/{}/{}/".format(namespace, basename)
        observation = _semantic_json(files, base + "observation.json")
        stdout = files[base + "stdout.bin"]; stderr = files[base + "stderr.bin"]
        validate_observation(observation, stdout, stderr)
        _require(observation["role"] == basename.split("-", 1)[1], "operation directory role drift")
        _require(observation["stdout_path"] == base + "stdout.bin" and observation["stderr_path"] == base + "stderr.bin",
                 "operation stream path drift")
        items.append((observation, stdout, stderr))
    wrapper = _semantic_json(files, wrapper_path)
    _require(wrapper.get("kind") == namespace, namespace + " receipt-wrapper kind drift")
    validate_receipt_chain(wrapper, plan, items)
    return wrapper["ordered_receipts"]


def _reconstruct_c06(files: Mapping[str, bytes], bindings: Mapping[str, object]) -> bool:
    gate = validate_a3l6_gate_bundle(_semantic_json(files, "authority/a3l6-gate-bundle.json"), bindings)
    _require(gate["result"] == "accept" and gate["focused_test_count"] == 65 and gate["discovery_test_count"] == 172,
             "C06 A3L6 gate not accepted")
    plans = {
        "campaign": validate_campaign_plan(_semantic_json(files, "readiness/campaign-plan.json")),
        "normal": validate_attempt_plan(_semantic_json(files, "readiness/normal-plan.json")),
        "oom": validate_attempt_plan(_semantic_json(files, "readiness/oom-plan.json")),
    }
    _receipt_wrapper(files, "campaign", plans["campaign"], _OPERATION_BASENAMES["campaign"], "reference/receipts.json")
    _receipt_wrapper(files, "normal", plans["normal"], _OPERATION_BASENAMES["normal"], "attempts/normal/receipts.json")
    _receipt_wrapper(files, "oom", plans["oom"], _OPERATION_BASENAMES["oom"], "attempts/oom/receipts.json")
    for attempt in ("normal", "oom"):
        result = _semantic_json(files, "attempts/{}/result.json".format(attempt))
        mounts = result.get("mounts"); rlimits = result.get("rlimits")
        _require(isinstance(mounts, dict) and isinstance(rlimits, dict), "C06 raw limits/mounts missing")
        mountinfo = _decode_b64(mounts.get("mountinfo_base64"), "mountinfo")
        _require(mounts.get("mountinfo_sha256") == sha256_hex(mountinfo) and b" /work " in mountinfo and b" /dev/shm " in mountinfo,
                 "C06 mountinfo correspondence drift")
        proc_limits = _decode_b64(rlimits.get("proc_limits_base64"), "proc limits")
        for needle in (b"Max cpu time", b"900", b"Max file size", b"67108864", b"Max open files", b"32", b"Max core file size"):
            _require(needle in proc_limits, "C06 proc limits correspondence drift")
    normal = _semantic_json(files, "attempts/normal/result.json")
    workload = normal.get("workload")
    _require(isinstance(workload, dict) and workload.get("returncode") == 0 and workload.get("signal") is None and
             workload.get("discovered_count") == workload.get("expected_count") == bindings["normal_expected_test_count"],
             "C06 normal workload drift")
    return True


_TRANSCRIPT_FIELDS = (
    "schema", "kind", "observation_sha256", "stdout_path", "stdout_bytes", "stdout_sha256",
    "stderr_path", "stderr_bytes", "stderr_sha256", "parsed",
)
_PROVENANCE_FIELDS = (
    "schema", "kind", "ordered_source_observation_sha256", "descriptor_set_sha256",
    "descriptor_set", "facts", "assumptions",
)
_PROVENANCE_FACT_FIELDS = {
    "docker-desktop": ("info_plist_sha256", "bundle_version", "short_version", "vm_image_sha256", "kernel_sha256", "codesign_verify_sha256", "codesign_display_sha256", "candidate_cdhash_full", "team_identifier"),
    "docker-client": ("path", "sha256", "client_version", "api_version", "go_version", "os", "arch"),
    "buildx": ("path", "sha256", "version", "revision", "buildx_version_stdout_sha256"),
    "docker-daemon": ("host", "context_name", "server_version", "api_version", "os", "arch", "kernel_version", "operating_system", "docker_root_dir", "containerd_version", "containerd_commit", "runc_version", "runc_commit", "version_observation_sha256", "info_observation_sha256"),
    "image-config": ("platform_reference", "image_id", "config_descriptor_digest", "architecture", "os", "variant", "config_sha256"),
    "rootfs": ("image_id", "rootfs_type", "ordered_diff_ids"),
}
_PROVENANCE_ASSUMPTIONS = {
    "docker-desktop": ["host-driver-honest", "signed-docker-app-honest"],
    "docker-client": ["host-driver-honest"],
    "buildx": ["host-driver-honest"],
    "docker-daemon": ["docker-daemon-honest", "host-driver-honest"],
    "image-config": ["docker-daemon-honest", "host-driver-honest"],
    "rootfs": ["docker-daemon-honest", "host-driver-honest"],
}

_CODESIGN_COMPONENT = rb"[A-Za-z0-9](?:[A-Za-z0-9 ._+@%=-]{0,126}[A-Za-z0-9._+@%=-])?"
_CODESIGN_PATH = rb"/Applications/Docker\.app(?:/" + _CODESIGN_COMPONENT + rb"){0,15}"
_CODESIGN_NESTED_PATH = rb"/Applications/Docker\.app(?:/" + _CODESIGN_COMPONENT + rb"){1,15}"
_DISPLAY_ROW_PATTERNS = (
    rb"Executable=/Applications/Docker\.app/Contents/MacOS/Docker Desktop",
    rb"Identifier=com\.docker\.docker",
    rb"Format=[A-Za-z0-9][A-Za-z0-9 ._+(),/-]{0,127}",
    rb"CodeDirectory v=(?:0|[1-9][0-9]{0,19}) size=(?:0|[1-9][0-9]{0,19}) flags=0x[0-9a-f]{1,16}(?:\([A-Za-z0-9,_+-]{1,64}\))? hashes=(?:0|[1-9][0-9]{0,19})\+(?:0|[1-9][0-9]{0,19}) location=embedded",
    rb"Hash type=sha256 size=32",
    rb"CandidateCDHash sha256=[0-9a-f]{40}",
    rb"CandidateCDHashFull sha256=[0-9a-f]{64}",
    rb"Hash choices=sha256",
    rb"CMSDigest=[0-9a-f]{64}",
    rb"CMSDigestType=2",
    rb"Executable Segment base=(?:0|[1-9][0-9]{0,19})",
    rb"Executable Segment limit=(?:0|[1-9][0-9]{0,19})",
    rb"Executable Segment flags=0x[0-9a-f]{1,16}",
    rb"Page size=(?:4096|16384)",
    rb"CDHash=[0-9a-f]{40}",
    rb"Signature size=(?:0|[1-9][0-9]{0,19})",
    rb"Authority=Developer ID Application: Docker Inc \(9BNSXJN65R\)",
    rb"Authority=Developer ID Certification Authority",
    rb"Authority=Apple Root CA",
    rb"Timestamp=[A-Z][a-z]{2} (?: [1-9]|[12][0-9]|3[01]), [0-9]{4} at (?:[1-9]|1[0-2]):[0-5][0-9]:[0-5][0-9] [AP]M",
    rb"Notarization Ticket=stapled",
    rb"Info\.plist entries=(?:0|[1-9][0-9]{0,19})",
    rb"TeamIdentifier=9BNSXJN65R",
    rb"Runtime Version=[0-9]{1,5}(?:\.[0-9]{1,5}){0,3}",
    rb"Sealed Resources version=(?:0|[1-9][0-9]{0,19}) rules=(?:0|[1-9][0-9]{0,19}) files=(?:0|[1-9][0-9]{0,19})",
    rb"Internal requirements count=(?:0|[1-9][0-9]{0,19}) size=(?:0|[1-9][0-9]{0,19})",
)


def _parse_codesign_verify(raw: bytes) -> Dict[str, object]:
    _require(len(raw) <= 262_144 and b"\r" not in raw, "codesign verify framing drift")
    try:
        raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise EvidenceError("codesign verify transcript is not ASCII") from error
    lines = raw.splitlines(keepends=True)
    _require(len(lines) >= 2, "codesign verify transcript is short")
    terminal = (
        b"/Applications/Docker.app: valid on disk\n",
        b"/Applications/Docker.app: satisfies its Designated Requirement\n",
    )
    _require(tuple(lines[-2:]) == terminal, "codesign verify terminal rows drift")
    prepared = []
    validated = []
    prefix_rows = lines[:-2]
    _require(len(prefix_rows) % 2 == 0, "codesign prepared/validated pairing drift")
    for index in range(0, len(prefix_rows), 2):
        prepared_match = re.fullmatch(rb"--prepared:(" + _CODESIGN_NESTED_PATH + rb")\n", prefix_rows[index])
        validated_match = re.fullmatch(rb"--validated:(" + _CODESIGN_NESTED_PATH + rb")\n", prefix_rows[index + 1])
        _require(prepared_match is not None and validated_match is not None, "codesign prepared/validated row drift")
        _require(prepared_match.group(1) == validated_match.group(1), "codesign prepared/validated path drift")
        prepared.append(prepared_match.group(1).decode("ascii"))
        validated.append(validated_match.group(1).decode("ascii"))
    return {"prepared_paths": prepared, "validated_paths": validated, "valid_on_disk": True, "satisfies_designated_requirement": True}


def _parse_codesign_display(raw: bytes) -> Dict[str, object]:
    _require(len(raw) <= 262_144 and b"\r" not in raw and raw.endswith(b"\n"), "codesign display framing drift")
    try:
        raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise EvidenceError("codesign display transcript is not ASCII") from error
    lines = raw.splitlines(keepends=True)
    _require(len(lines) == len(_DISPLAY_ROW_PATTERNS), "codesign display row census drift")
    for line, pattern in zip(lines, _DISPLAY_ROW_PATTERNS):
        _require(len(line) <= 1024 and re.fullmatch(pattern + rb"\n", line) is not None, "codesign display row grammar drift")
    rows = [line[:-1].decode("ascii") for line in lines]
    values = [line[:-1].decode("ascii").split("=", 1)[1] for line in lines]
    short = values[5]; full = values[6]; cms = values[8]; cdhash = values[14]
    _require(short == cdhash == full[:40] and cms == full, "codesign display digest chain drift")
    return {
        "ordered_rows": rows, "executable": values[0], "identifier": values[1],
        "format": values[2], "candidate_cdhash": short,
        "candidate_cdhash_full": full, "cms_digest": cms, "cdhash": cdhash,
        "authorities": [values[16], values[17], values[18]],
        "team_identifier": values[22], "runtime_version": values[23],
    }


def _validate_registry_document(value: object, kind: str) -> Mapping[str, object]:
    _require(isinstance(value, dict), kind + " registry transcript must be an object")
    _require(value.get("schemaVersion") == 2, kind + " registry schema version drift")
    descriptors = value.get("manifests") if kind == "registry-index" else value.get("layers")
    _require(isinstance(descriptors, list) and descriptors, kind + " descriptor census drift")
    for descriptor in descriptors:
        _require(isinstance(descriptor, dict), kind + " descriptor must be an object")
        _sha(descriptor.get("digest"), kind + " descriptor digest", prefixed=True)
        _ascii(descriptor.get("mediaType"), kind + " descriptor media type")
        _require(_is_int(descriptor.get("size")) and descriptor["size"] > 0, kind + " descriptor size drift")
    if kind == "registry-index":
        for descriptor in descriptors:
            platform = _fields(descriptor.get("platform"), ("os", "architecture", "variant"), "registry platform")
            _require(all(isinstance(item, str) and item for item in platform.values()), "registry platform value drift")
    else:
        config = _fields(value.get("config"), ("mediaType", "digest", "size"), "registry config descriptor")
        _sha(config["digest"], "registry config digest", prefixed=True)
        _ascii(config["mediaType"], "registry config media type")
        _require(_is_int(config["size"]) and config["size"] > 0, "registry config size drift")
    return value


def validate_transcript_binding(
    value: object, observation: object, stdout: bytes, stderr: bytes,
) -> Mapping[str, object]:
    binding = _fields(value, _TRANSCRIPT_FIELDS, "transcript binding")
    _require(binding["schema"] == SCHEMAS["transcript_binding"], "transcript binding schema drift")
    kind = binding["kind"]
    expected_roles = {
        "registry-index": "registry-index", "registry-platform": "registry-platform",
        "codesign-verify": "codesign-verify", "codesign-display": "codesign-display",
    }
    _require(kind in expected_roles, "transcript binding kind drift")
    checked_observation = validate_observation(observation, stdout, stderr)
    _require(checked_observation["role"] == expected_roles[kind], "transcript observation role drift")
    _require(
        binding["observation_sha256"] == observation_digest(checked_observation)
        and binding["stdout_path"] == checked_observation["stdout_path"]
        and binding["stdout_bytes"] == len(stdout)
        and binding["stdout_sha256"] == sha256_hex(stdout)
        and binding["stderr_path"] == checked_observation["stderr_path"]
        and binding["stderr_bytes"] == len(stderr)
        and binding["stderr_sha256"] == sha256_hex(stderr),
        "transcript raw stream binding drift",
    )
    if kind.startswith("registry-"):
        _require(stderr == b"", "registry transcript stderr drift")
        parsed = strict_json_bytes(stdout, MAX_RESULT_BYTES)
        _validate_registry_document(parsed, kind)
    elif kind == "codesign-verify":
        _require(stdout == b"", "codesign verify stdout drift")
        parsed = _parse_codesign_verify(stderr)
    else:
        _require(stdout == b"", "codesign display stdout drift")
        parsed = _parse_codesign_display(stderr)
    _require(binding["parsed"] == parsed, "transcript parsed/raw correspondence drift")
    return binding


def transcript_binding_digest(
    value: Mapping[str, object], observation: Optional[object] = None,
    stdout: Optional[bytes] = None, stderr: Optional[bytes] = None,
) -> str:
    _fields(value, _TRANSCRIPT_FIELDS, "transcript binding")
    if observation is not None or stdout is not None or stderr is not None:
        _require(observation is not None and isinstance(stdout, bytes) and isinstance(stderr, bytes), "transcript digest inputs incomplete")
        validate_transcript_binding(value, observation, stdout, stderr)
    return _digest("transcript_binding", value)


_PROVENANCE_SOURCE_ROLES = {
    "docker-desktop": ("codesign-verify", "codesign-display"),
    "docker-client": ("docker-version",),
    "buildx": ("buildx-version",),
    "docker-daemon": ("docker-version", "docker-info"),
    "image-config": ("image-config",),
    "rootfs": ("image-config",),
}


def _validate_host_tool_descriptor_set(value: object) -> Mapping[str, object]:
    descriptor_set = validate_descriptor_set(value)
    _require(descriptor_set["kind"] == "host-tools", "host-tools descriptor kind drift")
    expected = sorted((CODESIGN_PATH, DOCKER_PATH, BUILDX_PATH), key=lambda item: item.encode("ascii"))
    observations = descriptor_set["ordered_observations"]
    _require([item["path"] for item in observations] == expected, "host-tools descriptor path drift")
    expected_hashes = {CODESIGN_PATH: CODESIGN_SHA256, DOCKER_PATH: DOCKER_SHA256, BUILDX_PATH: BUILDX_SHA256}
    _require(all(item["sha256"] == expected_hashes[item["path"]] for item in observations), "host-tools descriptor hash drift")
    return descriptor_set


def _validate_desktop_descriptor_set(value: object) -> Mapping[str, object]:
    descriptor_set = validate_descriptor_set(value)
    _require(descriptor_set["kind"] == "docker-desktop", "Docker Desktop descriptor kind drift")
    expected = sorted((DOCKER_DESKTOP_INFO_PLIST_PATH, DOCKER_DESKTOP_VM_PATH, DOCKER_DESKTOP_KERNEL_PATH), key=lambda item: item.encode("ascii"))
    _require([item["path"] for item in descriptor_set["ordered_observations"]] == expected, "Docker Desktop descriptor path drift")
    return descriptor_set


def validate_host_provenance(
    value: object, source_observations: Sequence[Mapping[str, object]],
    raw_info_plist: Optional[bytes] = None,
) -> Mapping[str, object]:
    row = _fields(value, _PROVENANCE_FIELDS, "host provenance")
    _require(row["schema"] == SCHEMAS["host_provenance"], "host provenance schema drift")
    kind = row["kind"]
    _require(kind in _PROVENANCE_FACT_FIELDS, "host provenance kind drift")
    facts = _fields(row["facts"], _PROVENANCE_FACT_FIELDS[kind], kind + " provenance facts")
    _require(isinstance(source_observations, (list, tuple)), "host provenance observations must be ordered")
    _require(tuple(item.get("role") for item in source_observations) == _PROVENANCE_SOURCE_ROLES[kind], "host provenance source role order drift")
    for observation in source_observations:
        validate_observation(observation)
    _require(row["ordered_source_observation_sha256"] == [observation_digest(item) for item in source_observations], "host provenance observation digest drift")
    _require(row["assumptions"] == _PROVENANCE_ASSUMPTIONS[kind], "host provenance assumption drift")
    if kind == "docker-desktop":
        descriptor_set = _validate_desktop_descriptor_set(row["descriptor_set"])
    elif kind in ("docker-client", "buildx"):
        descriptor_set = _validate_host_tool_descriptor_set(row["descriptor_set"])
    else:
        descriptor_set = None
        _require(row["descriptor_set"] is None and row["descriptor_set_sha256"] is None, "host provenance descriptor nullability drift")
    if descriptor_set is not None:
        _require(row["descriptor_set_sha256"] == descriptor_set_digest(descriptor_set), "host provenance descriptor digest drift")
    if kind == "docker-desktop":
        by_path = {item["path"]: item for item in descriptor_set["ordered_observations"]}
        _require(
            facts["info_plist_sha256"] == by_path[DOCKER_DESKTOP_INFO_PLIST_PATH]["sha256"]
            and facts["vm_image_sha256"] == by_path[DOCKER_DESKTOP_VM_PATH]["sha256"] == DOCKER_DESKTOP_VM_SHA256
            and facts["kernel_sha256"] == by_path[DOCKER_DESKTOP_KERNEL_PATH]["sha256"] == DOCKER_DESKTOP_KERNEL_SHA256,
            "Docker Desktop descriptor fact drift",
        )
        _sha(facts["candidate_cdhash_full"], "Docker Desktop candidate CDHash")
        _require(facts["team_identifier"] == "9BNSXJN65R", "Docker Desktop team identifier drift")
        if raw_info_plist is not None:
            _require(isinstance(raw_info_plist, bytes) and sha256_hex(raw_info_plist) == facts["info_plist_sha256"], "Info.plist raw digest drift")
            info_observation = by_path[DOCKER_DESKTOP_INFO_PLIST_PATH]
            _require(info_observation["before"]["size"] == len(raw_info_plist), "Info.plist descriptor byte count drift")
            try:
                parsed_plist = plistlib.loads(raw_info_plist)
            except Exception as error:
                raise EvidenceError("Info.plist parse failed") from error
            _require(isinstance(parsed_plist, dict), "Info.plist root must be a dictionary")
            _require(parsed_plist.get("CFBundleIdentifier") == "com.docker.docker", "Info.plist identifier drift")
            _require(parsed_plist.get("CFBundleVersion") == facts["bundle_version"] and parsed_plist.get("CFBundleShortVersionString") == facts["short_version"], "Info.plist version fact drift")
    elif kind == "docker-client":
        _require((facts["path"], facts["sha256"]) == (DOCKER_PATH, DOCKER_SHA256), "Docker client provenance drift")
    elif kind == "buildx":
        _require((facts["path"], facts["sha256"]) == (BUILDX_PATH, BUILDX_SHA256), "Buildx provenance drift")
        _sha(facts["buildx_version_stdout_sha256"], "Buildx version transcript digest")
    elif kind == "image-config":
        _sha(facts["image_id"], "image id", prefixed=True); _sha(facts["config_descriptor_digest"], "config descriptor digest", prefixed=True)
        _sha(facts["config_sha256"], "config content digest")
    elif kind == "rootfs":
        _sha(facts["image_id"], "RootFS image id", prefixed=True)
        _require(facts["rootfs_type"] == "layers" and isinstance(facts["ordered_diff_ids"], list), "RootFS provenance drift")
        for digest in facts["ordered_diff_ids"]: _sha(digest, "RootFS diff id", prefixed=True)
    return row


def host_provenance_digest(
    value: Mapping[str, object], source_observations: Optional[Sequence[Mapping[str, object]]] = None,
    raw_info_plist: Optional[bytes] = None,
) -> str:
    _fields(value, _PROVENANCE_FIELDS, "host provenance")
    if source_observations is not None:
        validate_host_provenance(value, source_observations, raw_info_plist)
    return _digest("host_provenance", value)


def _validate_docker_context_capture(value: object, raw: bytes) -> Mapping[str, object]:
    context = _fields(
        value,
        ("schema", "path", "descriptor_observation", "descriptor_observation_sha256", "bytes", "sha256", "name", "host", "skip_tls_verify"),
        "Docker context",
    )
    _require(context["schema"] == SCHEMAS["docker_context"], "Docker context schema drift")
    _path(context["path"], "Docker context path", absolute=True)
    _require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_JSON_BYTES, "Docker context raw bytes drift")
    descriptor = validate_descriptor_observation(context["descriptor_observation"])
    _require(
        context["descriptor_observation_sha256"] == descriptor_observation_digest(descriptor)
        and descriptor["path"] == context["path"]
        and descriptor["relative_path"] is None
        and descriptor["sha256"] == context["sha256"] == sha256_hex(raw)
        and descriptor["before"]["size"] == context["bytes"] == len(raw),
        "Docker context descriptor/raw drift",
    )
    return context


def validate_docker_context(value: object, raw: bytes) -> Mapping[str, object]:
    context = _validate_docker_context_capture(value, raw)
    _require(
        len(raw) == 306
        and context["bytes"] == 306
        and context["sha256"] == DOCKER_CONTEXT_SHA256,
        "Docker context frozen byte identity drift",
    )
    # Docker owns this frozen external file and preserves semantic field order;
    # its exact byte identity is pinned above, so repository canonical ordering
    # is neither expected nor rewritten here.
    parsed = _parse_json_bytes(raw, MAX_JSON_BYTES)
    root = _fields(parsed, ("Name", "Metadata", "Endpoints"), "Docker context raw")
    metadata = _fields(
        root["Metadata"], ("Description", "GODEBUG", "otel"),
        "Docker context metadata",
    )
    otel = _fields(
        metadata["otel"], ("OTEL_EXPORTER_OTLP_ENDPOINT",),
        "Docker context telemetry endpoint",
    )
    endpoints = _fields(root["Endpoints"], ("docker",), "Docker context endpoints")
    docker = _fields(endpoints["docker"], ("Host", "SkipTLSVerify"), "Docker context Docker endpoint")
    _require(
        root["Name"] == context["name"] == "desktop-linux"
        and metadata["Description"] == "Docker Desktop"
        and metadata["GODEBUG"] == "x509negativeserial=1"
        and isinstance(otel["OTEL_EXPORTER_OTLP_ENDPOINT"], str)
        and otel["OTEL_EXPORTER_OTLP_ENDPOINT"].startswith("unix:///")
        and "\x00" not in otel["OTEL_EXPORTER_OTLP_ENDPOINT"]
        and docker["Host"] == context["host"]
        and context["skip_tls_verify"] is docker["SkipTLSVerify"] is False
        and isinstance(context["host"], str)
        and context["host"].startswith("unix:///")
        and "\x00" not in context["host"],
        "Docker context endpoint drift",
    )
    return context


def docker_context_digest(value: Mapping[str, object], raw: Optional[bytes] = None) -> str:
    if raw is None:
        _fields(value, ("schema", "path", "descriptor_observation", "descriptor_observation_sha256", "bytes", "sha256", "name", "host", "skip_tls_verify"), "Docker context")
    else:
        validate_docker_context(value, raw)
    return _digest("docker_context", value)


def _operation(files: Mapping[str, bytes], namespace: str, basename: str) -> Tuple[Mapping[str, object], bytes, bytes]:
    base = "operations/{}/{}/".format(namespace, basename)
    observation = _semantic_json(files, base + "observation.json")
    stdout = files[base + "stdout.bin"]; stderr = files[base + "stderr.bin"]
    validate_observation(observation, stdout, stderr)
    _require(observation["role"] == basename.split("-", 1)[1], "operation role drift: " + base)
    _require(observation["stdout_path"] == base + "stdout.bin" and observation["stderr_path"] == base + "stderr.bin", "operation path drift: " + base)
    return observation, stdout, stderr


def _transcript_semantics(files: Mapping[str, bytes], path: str, kind: str, namespace: str, basename: str) -> Mapping[str, object]:
    observation, stdout, stderr = _operation(files, namespace, basename)
    wrapper = _semantic_json(files, path)
    _require(wrapper.get("kind") == kind, kind + " transcript kind drift")
    return validate_transcript_binding(wrapper, observation, stdout, stderr)


def _host_provenance(files: Mapping[str, bytes], kind: str, source_observations: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    row = _semantic_json(files, "provenance/" + kind + ".json")
    raw_info = files.get("provenance/info-plist.raw") if kind == "docker-desktop" else None
    validate_host_provenance(row, source_observations, raw_info)
    return row["facts"]


def _json_lf(raw: bytes, label: str) -> Mapping[str, object]:
    _require(raw.endswith(b"\n") and raw.count(b"\n") == 1, label + " framing drift")
    value = strict_json_bytes(raw[:-1], MAX_RESULT_BYTES)
    _require(isinstance(value, dict), label + " must be an object")
    return value


def _reconstruct_c07(files: Mapping[str, bytes], bindings: Mapping[str, object]) -> bool:
    readiness = validate_readiness_result(_semantic_json(files, "readiness/readiness-result.json"))
    _require(readiness["accepted"] is True and readiness["failure"] is None, "C07 readiness rejected")
    readiness_ops = [_operation(files, "readiness", basename) for basename in _OPERATION_BASENAMES["readiness"]]
    campaign_ops = [_operation(files, "campaign", basename) for basename in _OPERATION_BASENAMES["campaign"]]
    _require(readiness["ordered_observation_sha256"] == [observation_digest(item[0]) for item in readiness_ops], "C07 readiness observation chain drift")
    index_binding = _transcript_semantics(files, "provenance/registry/index.json", "registry-index", "readiness", _OPERATION_BASENAMES["readiness"][0])
    platform_binding = _transcript_semantics(files, "provenance/registry/platform-manifest.json", "registry-platform", "readiness", _OPERATION_BASENAMES["readiness"][1])
    verify_binding = _transcript_semantics(files, "provenance/signature/verify.json", "codesign-verify", "readiness", _OPERATION_BASENAMES["readiness"][4])
    display_binding = _transcript_semantics(files, "provenance/signature/display.json", "codesign-display", "readiness", _OPERATION_BASENAMES["readiness"][5])
    index = index_binding["parsed"]; platform = platform_binding["parsed"]
    manifests = index.get("manifests")
    _require(isinstance(manifests, list), "C07 registry index manifests missing")
    selected = [item for item in manifests if item.get("platform") == bindings["selected_platform"]]
    _require(len(selected) == 1, "C07 selected registry descriptor drift")
    descriptor = selected[0]
    descriptor_projection = {name: descriptor[name] for name in ("digest", "mediaType", "size")}
    descriptor_projection.update({"os": descriptor["platform"]["os"], "architecture": descriptor["platform"]["architecture"], "variant": descriptor["platform"]["variant"]})
    _require(descriptor_projection == readiness["selected_descriptor"], "C07 selected registry projection drift")
    _require(
        sha256_hex(readiness_ops[0][1]) == readiness["index_sha256"] == bindings["index_manifest_sha256"]
        and descriptor["digest"] == bindings["selected_descriptor_digest"]
        and descriptor["size"] == bindings["selected_descriptor_size"]
        and descriptor["mediaType"] == bindings["selected_descriptor_media_type"]
        and sha256_hex(readiness_ops[1][1]) == readiness["platform_sha256"] == bindings["platform_manifest_sha256"]
        and len(readiness_ops[1][1]) == bindings["platform_manifest_size"],
        "C07 registry expected binding drift",
    )
    config = _fields(platform.get("config"), ("mediaType", "digest", "size"), "platform config descriptor")
    _require(config["digest"] == readiness["image_config_digest"] == bindings["image_config_digest"] and isinstance(platform.get("layers"), list) and platform["layers"], "C07 platform manifest config/layer drift")
    local = _json_lf(readiness_ops[2][1], "local image inspect")
    _require(readiness_ops[2][2] == b"" and local.get("Id") == config["digest"] and local.get("Architecture") == "arm64" and local.get("Os") == "linux" and local.get("Variant") == "v8", "C07 local image resolution drift")
    rootfs_value = _fields(local.get("RootFS"), ("Type", "Layers"), "local RootFS")
    _require(rootfs_value["Layers"] == readiness["rootfs_diff_ids"] == bindings["rootfs_diff_ids"] and rootfs_value["Type"] == "layers", "C07 local RootFS drift")
    context_raw = files["provenance/docker-context.raw"]
    context = validate_docker_context(
        _semantic_json(files, "provenance/docker-context.json"), context_raw
    )
    _require(
        context["sha256"] == bindings["docker_context_sha256"],
        "C07 context expected-binding drift",
    )
    desktop = _host_provenance(files, "docker-desktop", (readiness_ops[4][0], readiness_ops[5][0]))
    client = _host_provenance(files, "docker-client", (campaign_ops[1][0],))
    buildx = _host_provenance(files, "buildx", (readiness_ops[3][0],))
    daemon = _host_provenance(files, "docker-daemon", (campaign_ops[1][0], campaign_ops[2][0]))
    image = _host_provenance(files, "image-config", (campaign_ops[3][0],))
    rootfs = _host_provenance(files, "rootfs", (campaign_ops[3][0],))
    _require(desktop["codesign_verify_sha256"] == verify_binding["observation_sha256"] and desktop["codesign_display_sha256"] == display_binding["observation_sha256"] and desktop["candidate_cdhash_full"] == display_binding["parsed"]["candidate_cdhash_full"] == bindings["docker_app_candidate_cdhash_full"] and desktop["team_identifier"] == display_binding["parsed"]["team_identifier"] == bindings["docker_app_team_identifier"], "C07 signature provenance drift")
    _require(client["path"] == bindings["docker_path"] and client["sha256"] == bindings["docker_sha256"] and buildx["path"] == bindings["buildx_path"] and buildx["sha256"] == bindings["buildx_sha256"], "C07 tool provenance drift")
    _require(daemon["host"] == context["host"] and daemon["context_name"] == context["name"] and daemon["os"] == image["os"] == "linux" and daemon["arch"] in ("arm64", "aarch64") and image["architecture"] == "arm64" and image["variant"] == "v8", "C07 daemon/platform provenance drift")
    _require(image["platform_reference"] == bindings["platform_reference"] and image["image_id"] == config["digest"] and image["config_descriptor_digest"] == config["digest"] and image["config_sha256"] == config["digest"].split(":", 1)[1], "C07 image config provenance drift")
    _require(rootfs["image_id"] == image["image_id"] and rootfs["rootfs_type"] == "layers" and rootfs["ordered_diff_ids"] == bindings["rootfs_diff_ids"], "C07 RootFS provenance drift")
    normal = _semantic_json(files, "attempts/normal/result.json")
    runtime = _runtime_core(normal, "normal")
    _require(runtime["executable"] == bindings["normal_python_path"] and runtime["python_version"] == bindings["normal_python_version"] and _decode_b64(runtime.get("linker_version_stdout_base64"), "normal linker version") and runtime.get("linker_version_argv") == ["/usr/bin/ldd", "--version"], "C07 probe runtime provenance drift")
    os_release = _decode_b64(runtime.get("os_release_base64"), "normal os-release")
    _require(b"ID=" in os_release and daemon["operating_system"], "C07 runtime/daemon OS identity drift")
    return True


def _candidate_directory_order() -> List[str]:
    directories = {"."}
    for path in CANDIDATE_PAYLOAD_PATHS:
        parts = path.split("/")[:-1]
        for index in range(1, len(parts) + 1): directories.add("/".join(parts[:index]))
    _require(len(directories) == 62, "candidate directory grammar bug")
    nested = sorted(
        directories - {"."},
        key=lambda item: (-len(item.split("/")), item.encode("ascii")),
    )
    return nested + ["."]


def _publication_semantics(record: Mapping[str, object], files: Mapping[str, bytes], manifest: Mapping[str, object]) -> None:
    validate_publication_record(record)
    manifest_raw = canonical_json_bytes(manifest)
    expected_raw = dict(files); expected_raw["candidate-manifest.json"] = manifest_raw
    reopen_by_path = {row["path"]: row for row in record["ordered_file_reopens"]}
    _require(set(reopen_by_path) == set(expected_raw), "publication reopen path census drift")
    for path, raw in expected_raw.items():
        for side in ("prepublication", "postpublication"):
            observed = reopen_by_path[path][side]
            _require(observed["bytes"] == len(raw) and observed["sha256"] == sha256_hex(raw),
                     "publication reopen byte drift: " + path)
    events = record["ordered_publication_events"]
    for event, entry in zip(events[:201], manifest["entries"]):
        raw = files[entry["path"]]
        _require(event["target"] == entry["path"] and event["flags"] == [] and
                 event["result"] == event["errno"] == 0 and
                 event["sha256"] == entry["sha256"] == sha256_hex(raw) and
                 event["identity"] == reopen_by_path[entry["path"]]["prepublication"]["identity"],
                 "payload fsync evidence drift")
    manifest_event = events[201]
    _require(manifest_event["target"] == "candidate-manifest.json" and
             manifest_event["flags"] == [] and
             manifest_event["result"] == manifest_event["errno"] == 0 and
             manifest_event["identity"] == reopen_by_path["candidate-manifest.json"]["prepublication"]["identity"] and
             manifest_event["sha256"] == sha256_hex(manifest_raw),
             "manifest fsync evidence drift")
    for event, target in zip(events[202:264], _candidate_directory_order()):
        _require(event["target"] == target and event["flags"] == [] and
                 event["result"] == event["errno"] == 0 and
                 event["identity"] is not None and event["sha256"] is None,
                 "directory fsync evidence drift")
    _require(events[264]["identity"] == record["staging_identity"] and
             events[264]["sha256"] == record["prepublication_inventory_sha256"] and
             events[268]["identity"] == record["final_identity"] and
             events[269]["identity"] == record["final_identity"] and
             events[269]["sha256"] == record["postpublication_inventory_sha256"] and
             events[270]["target"] == "candidate-manifest.json" and
             events[270]["identity"] == reopen_by_path["candidate-manifest.json"]["postpublication"]["identity"] and
             events[270]["sha256"] == record["candidate_manifest_sha256"],
             "publication terminal evidence drift")


def _reconstruct_c09(files: Mapping[str, bytes], manifest: Mapping[str, object], publication: Mapping[str, object], snapshot: Mapping[str, object]) -> bool:
    plan = _fields(_semantic_json(files, "publication/prepublication-descriptor-plan.json"),
                   ("schema", "candidate_root", "parent_identity", "staging_identity", "expected_file_count", "expected_manifest_path", "overwrite_policy"),
                   "prepublication descriptor plan")
    _require(plan["schema"] == SCHEMAS["prepublication_plan"] and plan["expected_file_count"] == 202 and
             plan["overwrite_policy"] == "exclusive" and
             plan["expected_manifest_path"] == plan["candidate_root"] + "/candidate-manifest.json" and
             publication["final_path"] == plan["candidate_root"] and
             publication["parent_identity"] == plan["parent_identity"] and publication["staging_identity"] == plan["staging_identity"],
             "C09 prepublication/publication binding drift")
    _publication_semantics(publication, files, manifest)
    for attempt in ("normal", "oom"):
        tar_raw = files["attempts/{}/export.tar".format(attempt)]
        result_raw = files["attempts/{}/result.json".format(attempt)]
        _require(parse_docker_copy_tar(tar_raw) == result_raw, "C09 TAR/result correspondence drift: " + attempt)
    _require(snapshot["source_sha256"] and snapshot["copy_sha256"], "C09 snapshot binding missing")
    return True


def _reconstruct_retained_readiness_plan(
    files: Mapping[str, bytes], bindings: Mapping[str, object],
) -> Tuple[Mapping[str, object], List[Tuple[Mapping[str, object], bytes, bytes]]]:
    items = [
        _operation(files, "readiness", basename)
        for basename in _OPERATION_BASENAMES["readiness"]
    ]
    activations = (
        "always", "after_index", "after_platform", "after_platform",
        "after_platform", "after_platform",
    )
    commands = []
    for ordinal, ((observation, _, _), activation) in enumerate(
        zip(items, activations)
    ):
        argv = list(observation["argv"])
        if ordinal in (1, 2):
            replacements = sum(
                item.count(bindings["platform_reference"]) for item in argv
            )
            _require(replacements == 1, "retained readiness platform binding drift")
            argv = [
                item.replace(bindings["platform_reference"], PLATFORM_PLACEHOLDER)
                for item in argv
            ]
        commands.append({
            "ordinal": ordinal, "role": observation["role"], "argv": argv,
            "environment": observation["environment"], "cwd": observation["cwd"],
            "stdin_policy": observation["stdin_policy"],
            "stdout_cap": observation["stdout_cap"],
            "stderr_cap": observation["stderr_cap"],
            "timeout_ns": 1_800_000_000_000, "activation": activation,
            "expected_outcomes": ["exit_zero"],
        })
    plan = {
        "schema": SCHEMAS["readiness_plan"],
        "predecessor_commit": bindings["predecessor_commit"],
        "user_authorization_sha256": bindings["user_authorization_sha256"],
        "index_reference": bindings["index_reference"],
        "docker_path": bindings["docker_path"],
        "docker_sha256": bindings["docker_sha256"],
        "buildx_path": bindings["buildx_path"],
        "buildx_sha256": bindings["buildx_sha256"],
        "codesign_path": bindings["codesign_path"],
        "codesign_sha256": bindings["codesign_sha256"],
        "commands": commands,
        "selected_reference_rule": {
            "repository": "docker.io/library/python", "os": "linux",
            "architecture": "arm64", "variant": "v8", "count": 1,
        },
    }
    checked = validate_readiness_plan(plan)
    plan_sha = readiness_plan_digest(checked)
    _require(
        all(item[0]["plan_sha256"] == plan_sha for item in items),
        "retained readiness observation plan drift",
    )
    validate_receipt_chain(
        _semantic_json(files, "readiness/receipts.json"), checked, items
    )
    return checked, items


def _authorization_semantics(
    files: Mapping[str, bytes], bindings: Mapping[str, object],
    snapshot: Mapping[str, object],
) -> Mapping[str, object]:
    readiness_plan, _ = _reconstruct_retained_readiness_plan(files, bindings)
    return validate_authority_graph(
        files["authority/user-authorization.txt"],
        _semantic_json(files, "authority/action.json"),
        _semantic_json(files, "authority/policy.json"),
        _semantic_json(files, "authority/evidence-bundle.json"),
        _semantic_json(files, "authority/admission-decision.json"),
        _semantic_json(files, "authority/a3l6-gate-bundle.json"),
        readiness_plan,
        bindings["claim_boundary"],
        _semantic_json(files, "readiness/preauthorization-plan.json"),
        bindings,
        _semantic_json(files, "readiness/readiness-result.json"),
        _semantic_json(files, "authority/authorization-root.json"),
        _semantic_json(files, "readiness/authorization.json"),
        _semantic_json(files, "readiness/campaign-plan.json"),
        _semantic_json(files, "readiness/normal-plan.json"),
        _semantic_json(files, "readiness/oom-plan.json"),
        snapshot["copy_root"],
    )


def _intent_semantics(files: Mapping[str, bytes], attempt: str, plan: Mapping[str, object], authorization_sha256: str) -> Mapping[str, object]:
    intent = _fields(
        _semantic_json(files, "attempts/{}/intent.json".format(attempt)),
        ("schema", "campaign_id", "attempt_id", "authorization_sha256", "implementation_commit", "container_name",
         "expected_labels", "attempt_plan_sha256", "created_monotonic_ns"),
        attempt + " intent",
    )
    _require(intent["schema"] == SCHEMAS["intent"] and intent["attempt_id"] == attempt, attempt + " intent identity drift")
    _identifier(intent["campaign_id"], attempt + " campaign id"); _identifier(intent["attempt_id"], attempt + " attempt id")
    _ascii(intent["container_name"], attempt + " container name"); _nonnegative(intent["created_monotonic_ns"], attempt + " intent time")
    labels = intent["expected_labels"]
    _require(isinstance(labels, dict) and len(labels) == 4 and all(isinstance(key, str) and isinstance(value, str) for key, value in labels.items()), attempt + " intent labels drift")
    _require(
        intent["campaign_id"] == plan["campaign_id"]
        and intent["authorization_sha256"] == authorization_sha256 == plan["authorization_sha256"]
        and intent["implementation_commit"] == plan["implementation_commit"]
        and intent["attempt_plan_sha256"] == attempt_plan_digest(plan),
        attempt + " intent/plan binding drift",
    )
    binding = _fields(
        _semantic_json(files, "attempts/{}/cid-binding.json".format(attempt)),
        ("schema", "intent_sha256", "container_id", "create_observation_sha256", "bound_monotonic_ns"),
        attempt + " CID binding",
    )
    _require(binding["schema"] == SCHEMAS["cid_binding"] and _CID_RE.fullmatch(binding["container_id"] or "") is not None, attempt + " CID binding drift")
    _nonnegative(binding["bound_monotonic_ns"], attempt + " CID binding time")
    _require(binding["intent_sha256"] == _digest("intent", intent), attempt + " CID intent binding drift")
    return {"intent": intent, "binding": binding}


def _timing_semantics(files: Mapping[str, bytes], attempt: str, intent: Mapping[str, object], binding: Mapping[str, object], observations: Sequence[Mapping[str, object]], bindings: Mapping[str, object]) -> None:
    timing = _fields(
        _semantic_json(files, "attempts/{}/timing.json".format(attempt)),
        ("schema", "campaign_id", "attempt_id", "start_monotonic_ns", "deadline_monotonic_ns", "end_monotonic_ns",
         "ordered_durability_events", "deadline_met"),
        attempt + " timing",
    )
    _require(timing["schema"] == "hsai-p01b-attempt-timing-v1" and timing["campaign_id"] == intent["campaign_id"] and timing["attempt_id"] == attempt, attempt + " timing identity drift")
    start = timing["start_monotonic_ns"]; deadline = timing["deadline_monotonic_ns"]; end = timing["end_monotonic_ns"]
    _require(all(_is_int(value) for value in (start, deadline, end)) and deadline == start + bindings["attempt_deadline_ns"] and start <= end <= deadline and timing["deadline_met"] is True, attempt + " deadline drift")
    events = timing["ordered_durability_events"]
    expected = (
        ("intent-file-fsync", "intent.json", _digest("intent", intent)),
        ("intent-directory-fsync", ".", None),
        ("container-create", intent["container_name"], observation_digest(observations[2])),
        ("cid-binding-file-fsync", "cid-binding.json", _digest("cid_binding", binding)),
        ("cid-binding-directory-fsync", ".", None),
    )
    _require(isinstance(events, list) and len(events) == len(expected), attempt + " durability event census drift")
    for ordinal, (event, expected_row) in enumerate(zip(events, expected)):
        row = _fields(event, ("ordinal", "operation", "target", "started_monotonic_ns", "ended_monotonic_ns", "result", "errno", "sha256"), attempt + " durability event")
        _require(row["ordinal"] == ordinal and (row["operation"], row["target"], row["sha256"]) == expected_row and row["started_monotonic_ns"] < row["ended_monotonic_ns"], attempt + " durability event drift")
        _require(row["result"] == 0 and (row["errno"] == 0 if ordinal != 2 else row["errno"] is None), attempt + " durability outcome drift")
        if ordinal:
            _require(events[ordinal - 1]["ended_monotonic_ns"] <= row["started_monotonic_ns"], attempt + " durability event overlap")
    _require(events[1]["ended_monotonic_ns"] <= observations[2]["started_monotonic_ns"] and observations[2]["ended_monotonic_ns"] <= events[4]["ended_monotonic_ns"], attempt + " intent/create/binding order drift")
    _require(all(start <= item["started_monotonic_ns"] <= item["ended_monotonic_ns"] <= end for item in observations if item["outcome"] != "not_run"), attempt + " observation outside deadline")


def _reconstruct_c10(
    files: Mapping[str, bytes], bindings: Mapping[str, object],
    snapshot: Mapping[str, object],
) -> bool:
    authority = _authorization_semantics(files, bindings, snapshot)
    authorization_sha256 = _digest("authorization", authority["authorization"])
    plans = {
        "campaign": validate_campaign_plan(_semantic_json(files, "readiness/campaign-plan.json")),
        "normal": validate_attempt_plan(_semantic_json(files, "readiness/normal-plan.json")),
        "oom": validate_attempt_plan(_semantic_json(files, "readiness/oom-plan.json")),
    }
    _require(
        plans["campaign"]["authorization_sha256"] == authorization_sha256
        and plans["campaign"]["normal_plan_sha256"] == attempt_plan_digest(plans["normal"])
        and plans["campaign"]["oom_plan_sha256"] == attempt_plan_digest(plans["oom"])
        and plans["campaign"]["implementation_commit"] == bindings["implementation_commit"],
        "C10 campaign plan chain drift",
    )
    ingress_value = _semantic_json_value(files, "snapshot/ingress-certificates.json")
    _require(isinstance(ingress_value, list) and len(ingress_value) == 2, "ingress certificate census drift")
    ingress_certificates = [validate_certificate(item) for item in ingress_value]
    _require(
        [item["attempt_id"] for item in ingress_certificates] == ["normal", "oom"]
        and all(item["kind"] == "ingress" for item in ingress_certificates),
        "ingress certificate attempt order drift",
    )
    for attempt in ("normal", "oom"):
        retained = _intent_semantics(files, attempt, plans[attempt], authorization_sha256)
        observations = []
        for basename in _OPERATION_BASENAMES[attempt]:
            observation = _semantic_json(files, "operations/{}/{}/observation.json".format(attempt, basename))
            observations.append(observation)
        receipts = _receipt_wrapper(files, attempt, plans[attempt], _OPERATION_BASENAMES[attempt], "attempts/{}/receipts.json".format(attempt))
        _require(len(receipts) == 15 and [item["role"] for item in receipts] == [item.split("-", 1)[1] for item in _OPERATION_BASENAMES[attempt]], attempt + " lifecycle role drift")
        binding = retained["binding"]
        _require(binding["create_observation_sha256"] == observation_digest(observations[2]), attempt + " create/CID binding drift")
        _timing_semantics(files, attempt, retained["intent"], binding, observations, bindings)
        _require(
            observations[2]["outcome"] == "exit" and observations[2]["exit_code"] == 0
            and files["operations/{}/002-create/stdout.bin".format(attempt)] == (binding["container_id"] + "\n").encode("ascii")
            and observations[7]["outcome"] == "not_run"
            and observations[10]["outcome"] == "exit" and observations[10]["exit_code"] == 0
            and files["operations/{}/010-remove/stdout.bin".format(attempt)] == (binding["container_id"] + "\n").encode("ascii"),
            attempt + " create/remove lifecycle drift",
        )
        event = _semantic_json(files, "attempts/{}/readiness-event.json".format(attempt))
        validate_readiness_event(
            event,
            observations[6], files["operations/{}/006-start-attach/stdout.bin".format(attempt)],
            observations[4], observations[5],
        )
        _require(event["attempt_id"] == attempt, attempt + " readiness event identity drift")
        intent = retained["intent"]
        for state_path in ("inspect-prestart.json", "inspect-terminal.json"):
            raw = _semantic_json_value(files, "attempts/{}/{}".format(attempt, state_path))
            _require(isinstance(raw, list) and len(raw) == 1 and raw[0].get("Id") == binding["container_id"] and raw[0].get("Name") == "/" + intent["container_name"] and raw[0].get("Config", {}).get("Labels") == intent["expected_labels"], attempt + " inspect durable identity drift")
        _, prestart = _inspect_semantics(
            files, "attempts/{}/inspect-prestart.json".format(attempt), "prestart"
        )
        mounts = prestart["Mounts"]
        _require(
            isinstance(mounts, list) and len(mounts) == 1
            and mounts[0] == {
                "Type": "bind", "Source": snapshot["copy_root"],
                "Destination": "/input", "Mode": "ro", "RW": False,
                "Propagation": "rprivate",
            },
            attempt + " ingress mount reconstruction drift",
        )
        ingress = ingress_certificates[0 if attempt == "normal" else 1]
        expected_ingress = {
            "source_count": len(SNAPSHOT_PATHS),
            "source_manifest_sha256": snapshot["source_sha256"],
            "snapshot_manifest_sha256": snapshot["copy_sha256"],
            "source_descriptor_observation_sha256": descriptor_set_digest(
                snapshot["source_descriptor_set"]
            ),
            "snapshot_descriptor_observation_sha256": descriptor_set_digest(
                snapshot["copy_descriptor_set"]
            ),
            "container_mount_read_only": True,
        }
        _require(
            ingress["authorization_sha256"] == authorization_sha256
            and ingress["implementation_commit"] == bindings["implementation_commit"]
            and ingress["attempt_id"] == attempt
            and ingress["subject_manifest_sha256"] == snapshot["copy_sha256"]
            and ingress["observation_sha256"] == observation_digest(observations[3])
            and ingress["predicates"] == expected_ingress,
            attempt + " ingress certificate reconstruction drift",
        )
        export_tar = files["attempts/{}/export.tar".format(attempt)]
        result_raw = files["attempts/{}/result.json".format(attempt)]
        _require(
            files["operations/{}/004-export-running/stdout.bin".format(attempt)]
            == export_tar
            and parse_docker_copy_tar(export_tar) == result_raw,
            attempt + " egress TAR/result byte reconstruction drift",
        )
        egress = validate_certificate(
            _semantic_json(files, "attempts/{}/egress-certificate.json".format(attempt))
        )
        expected_egress = {
            "readiness_event_sha256": readiness_event_digest(event),
            "start_observation_sha256": observation_digest(observations[6]),
            "export_observation_sha256": observation_digest(observations[4]),
            "raw_tar_sha256": sha256_hex(export_tar),
            "result_sha256": sha256_hex(result_raw),
            "result_bytes": len(result_raw),
            "release_observation_sha256": observation_digest(observations[5]),
            "ordering_valid": True,
        }
        _require(
            egress["kind"] == "egress"
            and egress["authorization_sha256"] == authorization_sha256
            and egress["implementation_commit"] == bindings["implementation_commit"]
            and egress["attempt_id"] == attempt
            and egress["subject_manifest_sha256"] == snapshot["copy_sha256"]
            and egress["observation_sha256"] == observation_digest(observations[6])
            and egress["predicates"] == expected_egress,
            attempt + " egress certificate reconstruction drift",
        )
        daemon_raw = files["operations/{}/014-daemon-recheck/stdout.bin".format(attempt)]
        _require(daemon_raw.endswith(b"\n") and isinstance(strict_json_bytes(daemon_raw[:-1]), dict) and files["operations/{}/014-daemon-recheck/stderr.bin".format(attempt)] == b"" and observations[14]["exit_code"] == 0, attempt + " daemon recheck transcript drift")
        for index, subject in ((11, binding["container_id"]), (12, intent["container_name"])):
            stdout = files["operations/{}/{}/stdout.bin".format(attempt, _OPERATION_BASENAMES[attempt][index])]
            stderr = files["operations/{}/{}/stderr.bin".format(attempt, _OPERATION_BASENAMES[attempt][index])]
            _require(observations[index]["outcome"] == "exit" and observations[index]["exit_code"] == 1 and stdout == b"" and subject.encode("ascii") in stderr and b"No such container" in stderr, attempt + " subject absence transcript drift")
        _require(observations[13]["outcome"] == "exit" and observations[13]["exit_code"] == 0 and files["operations/{}/013-absence-label/stdout.bin".format(attempt)] == files["operations/{}/013-absence-label/stderr.bin".format(attempt)] == b"", attempt + " label absence transcript drift")
        cleanup = validate_certificate(_semantic_json(files, "attempts/{}/cleanup-certificate.json".format(attempt)))
        _require(cleanup["kind"] == "cleanup" and cleanup["authorization_sha256"] == authorization_sha256 and cleanup["attempt_id"] == attempt, attempt + " cleanup certificate binding drift")
        predicates = cleanup["predicates"]
        expected_cleanup = {
            "container_id": binding["container_id"], "container_name": intent["container_name"],
            "labels_sha256": sha256_hex(canonical_json_bytes(intent["expected_labels"])),
            "remove_observation_sha256": observation_digest(observations[10]),
            "cid_absence_observation_sha256": observation_digest(observations[11]),
            "name_absence_observation_sha256": observation_digest(observations[12]),
            "label_absence_observation_sha256": observation_digest(observations[13]),
            "daemon_recheck_observation_sha256": observation_digest(observations[14]), "absent": True,
        }
        _require(predicates == expected_cleanup, attempt + " cleanup reconstruction drift")
    return True


def _semantic_reconstruct_published_candidate(files: object, manifest: object, publication_record: object, repository_state: object, expected_bindings: object) -> List[Dict[str, object]]:
    pre = validate_prepublication_candidate(files, manifest, expected_bindings)
    _require(isinstance(files, dict), "candidate files must be a byte map")
    manifest_object = _coerce_object(manifest, "candidate manifest")
    bindings = validate_expected_bindings(_coerce_object(expected_bindings, "expected bindings"))
    publication = _coerce_object(publication_record, "publication record")
    repository = validate_repository_state(repository_state)
    _require(publication["candidate_manifest_sha256"] == pre["candidate_manifest_sha256"] and
             publication["repository_state_sha256"] == repository_state_digest(repository),
             "published graph digest drift")
    _require(repository["implementation_commit"] == manifest_object["implementation_commit"] == bindings["implementation_commit"],
             "published implementation drift")
    snapshot = _snapshot_semantics(files, bindings)
    predicates = {
        "C02": lambda: _reconstruct_c02(files, bindings, snapshot),
        "C03": lambda: _reconstruct_c03(files, snapshot),
        "C04": lambda: _reconstruct_c04(files, bindings),
        "C05": lambda: _reconstruct_c05(files),
        "C06": lambda: _reconstruct_c06(files, bindings),
        "C07": lambda: _reconstruct_c07(files, bindings),
        "C09": lambda: _reconstruct_c09(files, manifest_object, publication, snapshot),
        "C10": lambda: _reconstruct_c10(files, bindings, snapshot),
    }
    rows = []
    for class_id in CLASS_ORDER:
        try:
            closed = predicates[class_id]() is True
        except (EvidenceError, KeyError, TypeError, ValueError, binascii.Error):
            closed = False
        rows.append({"class_id": class_id, "closed": closed})
    return rows


# A3L5C corrected retained-evidence contracts.  The definitions below replace
# the superseded A3L5 publication/review surface while retaining its bounded
# stream, receipt, probe, and USTAR parsers.

SCHEMAS.update(
    {
        "descriptor_observation": "hsai-p01b-descriptor-observation-v1",
        "descriptor_set": "hsai-p01b-descriptor-set-v1",
        "transcript_binding": "hsai-p01b-transcript-binding-v1",
        "host_provenance": "hsai-p01b-host-provenance-v1",
        "readiness_plan": "hsai-p01b-container-readiness-plan-v2",
        "readiness_result": "hsai-p01b-container-readiness-result-v2",
        "intent": "hsai-p01b-container-intent-v1",
        "cid_binding": "hsai-p01b-container-cid-binding-v1",
        "publication": "hsai-p01b-container-publication-v2",
        "repository_state": "hsai-p01b-repository-state-v1",
        "repository_state_plan": "hsai-p01b-repository-state-plan-v1",
        "repository_capture": "hsai-p01b-repository-state-capture-v1",
        "decision": "hsai-p01b-container-decision-v3",
        "review": "hsai-p01b-container-review-v2",
        "review_session": "hsai-p01b-review-session-v1",
        "review_session_durability": "hsai-p01b-review-session-durability-v1",
        "review_launch": "hsai-p01b-review-launch-v1",
        "fresh_validation": "hsai-p01b-fresh-validation-receipt-v1",
        "review_aggregate": "hsai-p01b-container-review-aggregate-v2",
        "acceptance": "hsai-p01b-container-acceptance-v2",
        "snapshot_pair": "hsai-p01b-snapshot-manifest-pair-v1",
        "snapshot_source": "hsai-p01b-snapshot-source-manifest-v1",
        "snapshot_copy": "hsai-p01b-snapshot-copy-manifest-v1",
        "snapshot_descriptor": "hsai-p01b-snapshot-descriptor-set-v1",
        "prepublication_plan": "hsai-p01b-prepublication-descriptor-plan-v1",
        "expected_bindings": "hsai-p01b-expected-bindings-v1",
        "claim_boundary": "hsai-p01b-local-claim-boundary-v1",
        "docker_context": "hsai-p01b-docker-context-v1",
        "a3l6_gate_bundle": "hsai-p01b-a3l6-gate-bundle-v1",
        "a3l6_gate_plan": "hsai-p01b-a3l6-gate-plan-v1",
        "a3l6_gate_source": "hsai-p01b-a3l6-gate-source-manifest-v1",
        "a3l6_code_review": "hsai-p01b-a3l6-code-review-v1",
        "authorization_root": "hsai-p01b-local-authorization-root-v1",
        "receipt_chain": "hsai-p01b-container-receipt-chain-v1",
        "preauthorization": "hsai-p01b-container-preauthorization-plan-v2",
        "authorization": "hsai-p01b-container-authorization-v3",
        "probe_result": "hsai-p01b-probe-result-v2",
        "gateway_action_document": "hsai-p01b-gateway-action-document-v1",
        "gateway_policy_document": "hsai-p01b-gateway-policy-document-v1",
        "gateway_evidence_bundle": "hsai-p01b-gateway-evidence-bundle-v1",
        "gateway_admission_decision": "hsai-p01b-gateway-admission-decision-v1",
        "gateway_action_template": "hsai-p01b-gateway-action-template-v1",
        "gateway_action_input": "hsai-p01b-gateway-action-input-v1",
        "gateway_action_output": "hsai-p01b-gateway-action-output-v1",
    }
)

DOMAINS.update(
    {
        "descriptor_observation": "hsai:p01b-descriptor-observation:v1",
        "descriptor_set": "hsai:p01b-descriptor-set:v1",
        "transcript_binding": "hsai:p01b-transcript-binding:v1",
        "host_provenance": "hsai:p01b-host-provenance:v1",
        "readiness_plan": "hsai:p01b-container-readiness-plan:v2",
        "readiness_result": "hsai:p01b-container-readiness-result:v2",
        "intent": "hsai:p01b-container-intent:v1",
        "cid_binding": "hsai:p01b-container-cid-binding:v1",
        "recovery_inspection": "hsai:p01b-recovery-inspection-plan:v1",
        "recovery_inspect_failure": "hsai:p01b-recovery-inspection-failure:v1",
        "recovery_cleanup": "hsai:p01b-recovery-cleanup-plan:v1",
        "recovery_result": "hsai:p01b-recovery-result:v1",
        "publication": "hsai:p01b-container-publication:v2",
        "publication_inventory": "hsai:p01b-publication-inventory:v1",
        "repository_state": "hsai:p01b-repository-state:v1",
        "repository_state_plan": "hsai:p01b-repository-state-plan:v1",
        "repository_capture": "hsai:p01b-repository-state-capture:v1",
        "decision": "hsai:p01b-container-decision:v3",
        "review": "hsai:p01b-container-review:v2",
        "review_session": "hsai:p01b-review-session:v1",
        "review_session_durability": "hsai:p01b-review-session-durability:v1",
        "review_launch": "hsai:p01b-review-launch:v1",
        "fresh_validation": "hsai:p01b-fresh-validation-receipt:v1",
        "review_aggregate": "hsai:p01b-container-review-aggregate:v2",
        "acceptance": "hsai:p01b-container-acceptance:v2",
        "attempt_timing": "hsai:p01b-attempt-timing:v1",
        "snapshot_pair": "hsai:p01b-snapshot-manifest-pair:v1",
        "snapshot_source": "hsai:p01b-snapshot-source-manifest:v1",
        "snapshot_copy": "hsai:p01b-snapshot-copy-manifest:v1",
        "snapshot_descriptor": "hsai:p01b-snapshot-descriptor-set:v1",
        "prepublication_plan": "hsai:p01b-prepublication-descriptor-plan:v1",
        "expected_bindings": "hsai:p01b-expected-bindings:v1",
        "claim_boundary": "hsai:p01b-local-claim-boundary:v1",
        "docker_context": "hsai:p01b-docker-context:v1",
        "a3l6_gate_bundle": "hsai:p01b-a3l6-gate-bundle:v1",
        "a3l6_gate_plan": "hsai:p01b-a3l6-gate-plan:v1",
        "a3l6_gate_source": "hsai:p01b-a3l6-gate-source-manifest:v1",
        "a3l6_code_review": "hsai:p01b-a3l6-code-review:v1",
        "authorization_root": "hsai:p01b-local-authorization-root:v1",
        "receipt_chain": "hsai:p01b-container-receipt-chain:v1",
        "preauthorization": "hsai:p01b-container-preauthorization-plan:v2",
        "authorization": "hsai:p01b-container-authorization:v3",
        "gateway_action_document": "hsai:p01b-gateway-action-document:v1",
        "gateway_policy_document": "hsai:p01b-gateway-policy-document:v1",
        "gateway_evidence_bundle": "hsai:p01b-gateway-evidence-bundle:v1",
        "gateway_admission_decision": "hsai:p01b-gateway-admission-decision:v1",
        "gateway_action_template": "hsai:p01b-gateway-action-template:v1",
        "gateway_action_input": "hsai:p01b-gateway-action-input:v1",
        "gateway_action_output": "hsai:p01b-gateway-action-output:v1",
    }
)

DOMAIN_VECTORS.update(
    {
        "descriptor_observation": "7d075cc4f12c129ae6462455bddfc4d4d660906934c60fae7139a48bd87e461d",
        "descriptor_set": "9cadf313980658146a10eb1ab0dd32224e436bf074a8765834406de43da1c03f",
        "transcript_binding": "d952bf58ab94dae5069c7b75954bd20a2d27d433727c3db00be90a85eb9b5035",
        "host_provenance": "3aedd7d473bf4667af8767a5ee41671c1961531035a8e129dd9f281551fb1896",
        "readiness_plan": "22468c0f1d4e4b6e84916f22075bbd9cecb5e504859001683c84198a3d36dcd6",
        "readiness_result": "5aa3a99093842a6158edfc8ce635d946effdd9a132999d1472884125f5af7cc0",
        "intent": "323965bcf7fa6487e628241d1e389bf920a0dadc8ac0ebafa7cad4a02945a35e",
        "cid_binding": "849b872bc564e12e837daa37c28af9e4e5dc0ba25250b879faa555c41a0bd9b8",
        "recovery_inspection": "6f5e171a8a3c508aceb49be68bf0febb8e03938cd1d3d6cd1a093ad20d8c4787",
        "recovery_inspect_failure": "5749dc1105444219cfdf128b62592fd61f0a768d018e428050b3ee5da3dc59a4",
        "recovery_cleanup": "5820a836f3b38cd21a750a73658d1cd641c07a4049f7f332cb1b21f16c55e737",
        "recovery_result": "d0a267583ffa38485370c97817a500b69a6e9e63b9bddd58175d19505aad3776",
        "publication": "a97ea598ea7f4407319c9938578f7954ca1b0173876823e8e369e4d5e093d774",
        "publication_inventory": "16a3e6b263facfc1cef814a2848fb4ce23da665a7979e8c06c2098fbed4e7950",
        "repository_state": "bfa43a6596fa21e89efa05f355af5df20a589ece52adb9db5f7f9b8a390a8ba7",
        "repository_state_plan": "45e1aa74157473add63f741b40f174769e47b7f421c747dfdd630e96e3eb8b5f",
        "repository_capture": "5f99736abd662c4a14f920e27d9294da31852e0aaeeeae59142ef791bf41dd07",
        "decision": "8bd19a6cfb664faee136e0f56a8b3e5cec4c0f5dfa987f618609a80d6262a1b5",
        "review": "51359945d7a223b0ba7b338f39e01fed591122c7c161c866a5a1d4926e0e029a",
        "review_session": "118a5bc1291451881914a75ec6cc57a777113ff7b11497980b397d6b7d140757",
        "review_session_durability": "d95d9da5a21efa057501ea2aa314817b9a26201ec7597ed060ec4f820bca04f4",
        "review_launch": "56c5c43962abb4cbbafed4a84d3ea9cc651c557098c3afb2b2e40d846cb4224e",
        "fresh_validation": "ff1aeaf4762a843a89e3aa55abd154de900643c5d510e1dbe8bfa3bfa925cfbd",
        "review_aggregate": "2a40a172f911ac06bb17111bdb5583c04ed07fbcd0d7c472c2d579b66dfab879",
        "acceptance": "bdff1e0fdbb07f0c0ca92af173b319e7caad84e4f344cda25dd8dbb298064821",
        "attempt_timing": "571510140b0b6af682e737afca2b8948d31bba2cee271bbbd50b4ba589e1d396",
        "snapshot_pair": "4205228c67a1ee6edcca726a5d4fd51dcbb95109d0d465d0a58d86878f0b3d80",
        "snapshot_source": "0b61239a19ca0dd4c42c47f31c439d8538a2833998f4e637b6c4e66b86d3a654",
        "snapshot_copy": "da14ad924c103743ef65b1a6e6ccb9b66d505e0ccaff67e7f4e4fbff3a469fa2",
        "snapshot_descriptor": "27e6a1754d4839a9413c57afd1e854d59cf61375acc2e7a735f99a9d9fed7a79",
        "prepublication_plan": "db6460690b998fdba8c502e6c3fe485c527fcd7e9651ea2cf9e660140b912437",
        "expected_bindings": "89dde07525c79c731ab77e9f8fa3636fd9fa11f99821e5047a4ba34958d82543",
        "claim_boundary": "2788053e1498a8730b1bad7bba62bbe83455351802ef0ae82c234f31ec6d0912",
        "docker_context": "200f13d823d114f4955e6147aeb6adf6bf54c95abce0ff0c412e93a43e9ef928",
        "a3l6_gate_bundle": "de53fc8e310fe4330f7bccd04e83f256e348fed1487bb08fd23ff7c6b3af0341",
        "a3l6_gate_plan": "217a1e5d5e0fde2423460954d23be7ecd6b75c7af7837f8dea65b6eb3e73616c",
        "a3l6_gate_source": "77695148772b5dafdbfcdb028053417f80c23cbe2c030e6ebb8cba460e67b07e",
        "a3l6_code_review": "f28f323dd2a54c51b981985696a6d7eba41d0446a12ee555e4d35664581d20fe",
        "authorization_root": "3475fc80467ec7140cf2f33d72c33d099316fc4bd8d09f2076cbb77ef33b384f",
        "receipt_chain": "3459a485884ebdcb01810739187d2bc602ef6488ad194b0996e735db6132286b",
        "preauthorization": "93a0f949d4da91fecb607cdec7f29984c44368d0157c2023590b36b4f1c8ca9b",
        "authorization": "65e0ffed10bbdea3705a0d3f7dbd27d5d493996f1b54c6e2b5678fc258ddcf64",
        "gateway_action_document": "5583fd64e6dab08c03d25a478e380634fac45fed4b93ef1bae87c109ba13b3d9",
        "gateway_policy_document": "c75a491d000d7eb759e202c4ed207605c4b28a5731362e8e4f9ebe705b93ab41",
        "gateway_evidence_bundle": "db896051d190437c92de552cc224d5a44b7097972f6118e6526c13133e95702d",
        "gateway_admission_decision": "2c3ebf0c38e076cb94fb9f604cdd19457576f8ff4ed53cda9566ec43c80f2226",
        "gateway_action_template": "a07f52ce9a8e82e8a2e25cfc8b19b4b2ef9f7a06ca430480c66752a37ca6be1e",
        "gateway_action_input": "a6305ff8d1630ab036867b5eb2ec28e7bc52aa65cf7b00f54b46cb5c281ad423",
        "gateway_action_output": "280151bf4431ca28be7ec9a9fba362e7be19f3251d1b122daf838d21a50d4a81",
    }
)

HONESTY_ASSUMPTIONS = (
    "signed-docker-app-honest",
    "docker-daemon-honest",
    "probe-code-honest",
    "host-driver-honest",
    "native-python-runtime-stdlib-honest",
    "host-system-tool-honest",
    "reviewed-gate-test-code-honest",
    "formal-discovery-under-seatbelt-is-stubbed-census-not-full-suite-semantics",
)
NONCLAIMS = (
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

EXPECTED_BINDING_FIELDS = (
    "schema", "predecessor_commit", "implementation_commit", "implementation_tree",
    "user_authorization_sha256", "claim_boundary", "claim_boundary_sha256",
    "a3l6_audit_commit", "a3l6_gate_plan_sha256",
    "a3l6_gate_source_manifest_sha256", "a3l6_gate_bundle_sha256",
    "expected_focused_test_ids_sha256", "validator_sha256", "collector_sha256",
    "expected_focused_test_count", "protected_path", "protected_sha256",
    "native_python_path", "native_python_sha256", "native_python_version",
    "sandbox_exec_path", "sandbox_exec_sha256", "gate_sandbox_profile_sha256",
    "normal_python_path", "normal_python_version", "normal_interpreter_policy",
    "git_path", "git_sha256", "docker_path", "docker_sha256", "buildx_path",
    "buildx_sha256", "codesign_path", "codesign_sha256",
    "docker_desktop_info_plist_path", "docker_desktop_info_plist_sha256",
    "docker_desktop_vm_path", "docker_desktop_vm_sha256",
    "docker_desktop_kernel_path", "docker_desktop_kernel_sha256",
    "docker_app_candidate_cdhash_full", "docker_app_team_identifier",
    "docker_context_path", "docker_context_sha256", "index_reference",
    "index_manifest_sha256", "selected_platform", "selected_descriptor_digest",
    "selected_descriptor_size", "selected_descriptor_media_type",
    "platform_reference", "platform_manifest_sha256", "platform_manifest_size",
    "platform_manifest_media_type", "image_config_digest", "rootfs_diff_ids",
    "snapshot_source_manifest_sha256", "snapshot_copy_manifest_sha256",
    "seccomp_sha256", "normal_expected_test_count", "discovery_expected_test_count",
    "candidate_payload_count", "attempt_deadline_ns", "class_order", "evidence_level",
)

SNAPSHOT_PATHS = (
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

_FIXED_PAYLOAD_PATHS = (
    "authority/action.json", "authority/policy.json", "authority/evidence-bundle.json",
    "authority/a3l6-gate-bundle.json", "authority/admission-decision.json",
    "authority/authorization-root.json", "authority/expected-bindings.json",
    "authority/user-authorization.txt", "readiness/preauthorization-plan.json",
    "readiness/readiness-result.json", "readiness/authorization.json",
    "readiness/campaign-plan.json", "readiness/normal-plan.json",
    "readiness/oom-plan.json", "readiness/receipts.json", "provenance/git.json",
    "provenance/docker-desktop.json", "provenance/docker-client.json",
    "provenance/buildx.json", "provenance/docker-daemon.json",
    "provenance/docker-context.json", "provenance/image-config.json",
    "provenance/rootfs.json", "provenance/docker-context.raw",
    "provenance/info-plist.raw", "provenance/registry/index.json",
    "provenance/registry/platform-manifest.json", "provenance/signature/verify.json",
    "provenance/signature/display.json", "snapshot/source-manifest.json",
    "snapshot/source-descriptor-observations.json", "snapshot/ingress-observations.json",
    "snapshot/ingress-certificates.json", "reference/native-result.json",
    "reference/projection.json", "reference/receipts.json",
    "publication/prepublication-descriptor-plan.json",
)
_OPERATION_BASENAMES = {
    "readiness": ("000-registry-index", "001-registry-platform", "002-local-platform", "003-buildx-version", "004-codesign-verify", "005-codesign-display"),
    "campaign": ("000-native-reference", "001-docker-version", "002-docker-info", "003-image-config"),
    "normal": ("000-absence-name-pre", "001-absence-label-pre", "002-create", "003-inspect-prestart", "004-export-running", "005-release", "006-start-attach", "007-emergency-kill", "008-wait", "009-inspect-terminal", "010-remove", "011-absence-cid", "012-absence-name", "013-absence-label", "014-daemon-recheck"),
    "oom": ("000-absence-name-pre", "001-absence-label-pre", "002-create", "003-inspect-prestart", "004-export-running", "005-release", "006-start-attach", "007-emergency-kill", "008-wait", "009-inspect-terminal", "010-remove", "011-absence-cid", "012-absence-name", "013-absence-label", "014-daemon-recheck"),
}
_ATTEMPT_FILES = ("intent.json", "cid-binding.json", "timing.json", "receipts.json", "result.json", "readiness-event.json", "inspect-prestart.json", "inspect-terminal.json", "egress-certificate.json", "cleanup-certificate.json", "export.tar")


def _candidate_payload_paths() -> Tuple[str, ...]:
    paths = list(_FIXED_PAYLOAD_PATHS)
    paths.extend("snapshot/files/" + path for path in SNAPSHOT_PATHS)
    for namespace in ("readiness", "campaign", "normal", "oom"):
        for basename in _OPERATION_BASENAMES[namespace]:
            for leaf in ("observation.json", "stdout.bin", "stderr.bin"):
                paths.append("operations/{}/{}/{}".format(namespace, basename, leaf))
    for attempt in ("normal", "oom"):
        paths.extend("attempts/{}/{}".format(attempt, leaf) for leaf in _ATTEMPT_FILES)
    _require(len(paths) == 201 and len(set(paths)) == 201, "candidate grammar bug")
    return tuple(sorted(paths))


CANDIDATE_PAYLOAD_PATHS = _candidate_payload_paths()


def _nonnegative(value: object, label: str) -> int:
    _require(_is_int(value) and value >= 0, "invalid " + label)
    return value


def _identity(value: object, label: str, descriptor: bool = False) -> Mapping[str, object]:
    fields = ("device", "inode", "mode", "uid", "gid", "link_count")
    if descriptor:
        fields += ("size", "mtime_ns", "ctime_ns")
    identity = _fields(value, fields, label)
    for name in fields:
        _nonnegative(identity[name], label + " " + name)
    return identity


DESCRIPTOR_OBSERVATION_FIELDS = ("schema", "role", "path", "relative_path", "before", "after", "sha256")


def validate_descriptor_observation(value: object) -> Mapping[str, object]:
    row = _fields(value, DESCRIPTOR_OBSERVATION_FIELDS, "descriptor observation")
    _require(row["schema"] == SCHEMAS["descriptor_observation"], "descriptor schema drift")
    role = _ascii(row["role"], "descriptor role")
    _path(row["path"], "descriptor path", absolute=True)
    relative_roles = {"source", "snapshot", "gate-source-pre", "gate-source-post"}
    if role in relative_roles:
        _path(row["relative_path"], "descriptor relative path", absolute=False)
    else:
        _require(row["relative_path"] is None, "descriptor relative path forbidden")
    before = _identity(row["before"], "descriptor before", descriptor=True)
    after = _identity(row["after"], "descriptor after", descriptor=True)
    _require(before == after, "descriptor identity changed")
    if role == "review-python":
        _require(
            before["link_count"] >= 1,
            "review Python descriptor link count rejected",
        )
    else:
        _require(before["link_count"] == 1, "descriptor hard link rejected")
    _sha(row["sha256"], "descriptor digest")
    return row


def descriptor_observation_digest(value: Mapping[str, object]) -> str:
    validate_descriptor_observation(value)
    return _digest("descriptor_observation", value)


def validate_descriptor_set(value: object) -> Mapping[str, object]:
    _require(isinstance(value, dict), "descriptor set must be an object")
    kind = value.get("kind")
    if kind in ("host-tools", "docker-desktop"):
        row = _fields(
            value,
            ("schema", "kind", "ordered_observations"),
            "descriptor set",
        )
        _require(
            row["schema"] == SCHEMAS["descriptor_set"],
            "descriptor set schema drift",
        )
        expected_count = 3
        expected_paths = None
    elif kind in ("source", "snapshot"):
        row = _fields(
            value,
            ("schema", "kind", "manifest_sha256", "ordered_observations"),
            "snapshot descriptor set",
        )
        _require(
            row["schema"] == SCHEMAS["snapshot_descriptor"],
            "snapshot descriptor set schema drift",
        )
        _sha(row["manifest_sha256"], "snapshot descriptor manifest digest")
        expected_count = len(SNAPSHOT_PATHS)
        expected_paths = list(SNAPSHOT_PATHS)
    else:
        raise EvidenceError("descriptor set kind drift")
    observations = row["ordered_observations"]
    _require(
        isinstance(observations, list) and len(observations) == expected_count,
        "descriptor set census drift",
    )
    checked = [validate_descriptor_observation(item) for item in observations]
    paths = [item["path"] for item in checked]
    _require(len(set(paths)) == expected_count, "descriptor set path duplication")
    if expected_paths is not None:
        _require(
            [item["relative_path"] for item in checked] == expected_paths,
            "snapshot descriptor path order drift",
        )
        expected_role = "source" if kind == "source" else "snapshot"
        _require(
            all(item["role"] == expected_role for item in checked),
            "snapshot descriptor role drift",
        )
    else:
        _require(
            paths == sorted(paths, key=lambda item: item.encode("ascii")),
            "descriptor set order drift",
        )
    return row


def descriptor_set_digest(value: Mapping[str, object]) -> str:
    validate_descriptor_set(value)
    return _digest("descriptor_set", value)


SNAPSHOT_MANIFEST_ENTRY_FIELDS = (
    "path", "mode", "bytes", "sha256", "descriptor_observation_sha256",
)


def _validate_snapshot_manifest(value: object, kind: str) -> Mapping[str, object]:
    _require(kind in ("source", "copy"), "snapshot manifest kind drift")
    row = _fields(value, ("schema", "ordered_entries"), "snapshot " + kind + " manifest")
    schema_name = "snapshot_source" if kind == "source" else "snapshot_copy"
    _require(row["schema"] == SCHEMAS[schema_name], "snapshot manifest schema drift")
    entries = row["ordered_entries"]
    _require(
        isinstance(entries, list) and len(entries) == len(SNAPSHOT_PATHS),
        "snapshot manifest census drift",
    )
    for entry, path in zip(entries, SNAPSHOT_PATHS):
        checked = _fields(entry, SNAPSHOT_MANIFEST_ENTRY_FIELDS, "snapshot manifest entry")
        _require(checked["path"] == path, "snapshot manifest path order drift")
        _require(_is_int(checked["mode"]) and 0 <= checked["mode"] <= 0o7777, "snapshot manifest mode drift")
        if kind == "copy":
            _require(checked["mode"] == 0o444, "snapshot copy mode drift")
        _nonnegative(checked["bytes"], "snapshot manifest bytes")
        _sha(checked["sha256"], "snapshot manifest content digest")
        _sha(checked["descriptor_observation_sha256"], "snapshot manifest descriptor digest")
    return row


def validate_snapshot_source_manifest(value: object) -> Mapping[str, object]:
    return _validate_snapshot_manifest(value, "source")


def snapshot_source_manifest_digest(value: Mapping[str, object]) -> str:
    validate_snapshot_source_manifest(value)
    return _digest("snapshot_source", value)


def validate_snapshot_copy_manifest(value: object) -> Mapping[str, object]:
    return _validate_snapshot_manifest(value, "copy")


def snapshot_copy_manifest_digest(value: Mapping[str, object]) -> str:
    validate_snapshot_copy_manifest(value)
    return _digest("snapshot_copy", value)


def _cross_snapshot_descriptor_set(
    manifest: Mapping[str, object], descriptor_set: object, kind: str,
) -> Mapping[str, object]:
    checked = validate_descriptor_set(descriptor_set)
    _require(checked["kind"] == kind, "snapshot descriptor-set kind drift")
    digest = snapshot_source_manifest_digest(manifest) if kind == "source" else snapshot_copy_manifest_digest(manifest)
    _require(checked["manifest_sha256"] == digest, "snapshot descriptor manifest binding drift")
    for entry, observation in zip(manifest["ordered_entries"], checked["ordered_observations"]):
        _require(
            observation["relative_path"] == entry["path"]
            and observation["role"] == kind
            and observation["sha256"] == entry["sha256"]
            and observation["before"]["size"] == entry["bytes"]
            and observation["before"]["mode"] == entry["mode"]
            and descriptor_observation_digest(observation) == entry["descriptor_observation_sha256"],
            "snapshot descriptor/manifest correspondence drift",
        )
    return checked


def validate_snapshot_manifest_pair(
    value: object,
    source_descriptor_set: Optional[object] = None,
    snapshot_descriptor_set: Optional[object] = None,
    gate_bundle: Optional[object] = None,
) -> Mapping[str, object]:
    pair = _fields(
        value,
        ("schema", "implementation_commit", "implementation_tree", "source_manifest", "snapshot_manifest"),
        "snapshot manifest pair",
    )
    _require(pair["schema"] == SCHEMAS["snapshot_pair"], "snapshot pair schema drift")
    _git(pair["implementation_commit"], "snapshot pair implementation commit")
    _git(pair["implementation_tree"], "snapshot pair implementation tree")
    source = validate_snapshot_source_manifest(pair["source_manifest"])
    copied = validate_snapshot_copy_manifest(pair["snapshot_manifest"])
    for source_entry, copied_entry in zip(source["ordered_entries"], copied["ordered_entries"]):
        _require(
            source_entry["path"] == copied_entry["path"]
            and source_entry["bytes"] == copied_entry["bytes"]
            and source_entry["sha256"] == copied_entry["sha256"],
            "snapshot source/copy byte correspondence drift",
        )
    if source_descriptor_set is not None or snapshot_descriptor_set is not None:
        _require(source_descriptor_set is not None and snapshot_descriptor_set is not None, "snapshot descriptor pair incomplete")
        _cross_snapshot_descriptor_set(source, source_descriptor_set, "source")
        _cross_snapshot_descriptor_set(copied, snapshot_descriptor_set, "snapshot")
    if gate_bundle is not None:
        gate = validate_a3l6_gate_bundle(gate_bundle)
        _require(
            pair["implementation_commit"] == gate["implementation_commit"]
            and pair["implementation_tree"] == gate["implementation_tree"],
            "snapshot/gate implementation drift",
        )
        gate_sources = gate["gate_source_manifest"]["ordered_sources"]
        for source_entry, copied_entry, gate_entry in zip(source["ordered_entries"], copied["ordered_entries"], gate_sources):
            _require(
                source_entry["path"] == copied_entry["path"] == gate_entry["path"]
                and source_entry["bytes"] == copied_entry["bytes"] == gate_entry["bytes"]
                and source_entry["sha256"] == copied_entry["sha256"] == gate_entry["sha256"],
                "snapshot/gate source correspondence drift",
            )
        reviewed = {item["path"]: item["sha256"] for item in gate["ordered_review_records"][0]["ordered_file_sha256"]}
        _require(
            all(reviewed[path] == source["ordered_entries"][SNAPSHOT_PATHS.index(path)]["sha256"] for path in REVIEWED_PATHS),
            "snapshot/gate review projection drift",
        )
    return pair


def snapshot_manifest_pair_digest(value: Mapping[str, object]) -> str:
    validate_snapshot_manifest_pair(value)
    return _digest("snapshot_pair", value)


def validate_claim_boundary(value: object) -> Mapping[str, object]:
    boundary = _fields(value, ("schema", "evidence_level", "ordered_honesty_assumptions", "ordered_nonclaims"), "claim boundary")
    _require(boundary["schema"] == SCHEMAS["claim_boundary"], "claim boundary schema drift")
    _require(boundary["evidence_level"] == EVIDENCE_LEVEL, "claim evidence level drift")
    _require(boundary["ordered_honesty_assumptions"] == list(HONESTY_ASSUMPTIONS), "honesty assumptions drift")
    _require(boundary["ordered_nonclaims"] == list(NONCLAIMS), "nonclaims drift")
    return boundary


def claim_boundary_digest(value: Mapping[str, object]) -> str:
    validate_claim_boundary(value)
    return _digest("claim_boundary", value)


def validate_expected_bindings(value: object) -> Mapping[str, object]:
    bindings = _fields(value, EXPECTED_BINDING_FIELDS, "expected bindings")
    _require(bindings["schema"] == SCHEMAS["expected_bindings"], "expected bindings schema drift")
    for name in ("predecessor_commit", "implementation_commit", "implementation_tree", "a3l6_audit_commit"):
        _git(bindings[name], name.replace("_", " "))
    for name in EXPECTED_BINDING_FIELDS:
        if name.endswith("_sha256"):
            _sha(bindings[name], name.replace("_", " "))
    boundary = validate_claim_boundary(bindings["claim_boundary"])
    _require(bindings["claim_boundary_sha256"] == claim_boundary_digest(boundary), "claim boundary binding drift")
    _require(bindings["expected_focused_test_count"] == 65, "focused test count drift")
    _require(bindings["normal_expected_test_count"] == 151, "normal test count drift")
    _require(bindings["discovery_expected_test_count"] == 172, "discovery count drift")
    _require(bindings["candidate_payload_count"] == 201, "candidate payload count drift")
    _require(bindings["class_order"] == list(CLASS_ORDER), "class order binding drift")
    _require(bindings["evidence_level"] == EVIDENCE_LEVEL, "binding evidence level drift")
    _require(bindings["native_python_path"] == "/usr/bin/python3" and bindings["native_python_sha256"] == NATIVE_PYTHON_SHA256 and bindings["native_python_version"] == "3.9.6", "native Python binding drift")
    _require(bindings["normal_python_path"] == "/usr/local/bin/python3" and bindings["normal_python_version"] == "3.11.15", "normal Python binding drift")
    _require(bindings["normal_interpreter_policy"] == "probe-observed-ordered-chain-under-probe-honesty", "normal interpreter policy drift")
    _require(bindings["selected_platform"] == {"os": "linux", "architecture": "arm64", "variant": "v8"}, "selected platform drift")
    _require(bindings["rootfs_diff_ids"] == list(ROOTFS_DIFF_IDS), "RootFS binding drift")
    _require(bindings["attempt_deadline_ns"] == 1_800_000_000_000, "attempt deadline drift")
    _path(bindings["protected_path"], "protected path", absolute=True)
    fixed_tools = (
        ("docker_path", "docker_sha256", DOCKER_PATH, DOCKER_SHA256),
        ("buildx_path", "buildx_sha256", BUILDX_PATH, BUILDX_SHA256),
        ("codesign_path", "codesign_sha256", CODESIGN_PATH, CODESIGN_SHA256),
        ("sandbox_exec_path", "sandbox_exec_sha256", "/usr/bin/sandbox-exec", SANDBOX_EXEC_SHA256),
    )
    _require(all(bindings[path_name] == path and bindings[sha_name] == digest for path_name, sha_name, path, digest in fixed_tools), "expected tool identity drift")
    desktop_files = (
        ("docker_desktop_info_plist_path", "docker_desktop_info_plist_sha256", DOCKER_DESKTOP_INFO_PLIST_PATH, None),
        ("docker_desktop_vm_path", "docker_desktop_vm_sha256", DOCKER_DESKTOP_VM_PATH, DOCKER_DESKTOP_VM_SHA256),
        ("docker_desktop_kernel_path", "docker_desktop_kernel_sha256", DOCKER_DESKTOP_KERNEL_PATH, DOCKER_DESKTOP_KERNEL_SHA256),
    )
    _require(all(bindings[path_name] == path and (digest is None or bindings[sha_name] == digest) for path_name, sha_name, path, digest in desktop_files), "Docker Desktop expected identity drift")
    _path(bindings["docker_context_path"], "Docker context path", absolute=True)
    _require(bindings["docker_context_sha256"] == DOCKER_CONTEXT_SHA256, "Docker context frozen digest drift")
    _require(bindings["index_reference"] == INDEX_REFERENCE and bindings["index_manifest_sha256"] == INDEX_REFERENCE.rsplit(":", 1)[1], "registry index binding drift")
    _sha(bindings["selected_descriptor_digest"], "selected descriptor digest", prefixed=True)
    _require(bindings["selected_descriptor_media_type"] == bindings["platform_manifest_media_type"] == "application/vnd.oci.image.manifest.v1+json", "platform media type binding drift")
    _require(_is_int(bindings["selected_descriptor_size"]) and bindings["selected_descriptor_size"] > 0 and bindings["selected_descriptor_size"] == bindings["platform_manifest_size"], "platform size binding drift")
    _require(
        bindings["selected_descriptor_digest"] == "sha256:" + bindings["platform_manifest_sha256"]
        and bindings["platform_reference"] == "docker.io/library/python@" + bindings["selected_descriptor_digest"],
        "platform reference/digest binding drift",
    )
    _require(bindings["image_config_digest"] == IMAGE_CONFIG_DIGEST, "image config binding drift")
    _require(bindings["snapshot_source_manifest_sha256"] != bindings["snapshot_copy_manifest_sha256"], "source/copy manifest domains collapsed")
    return bindings


def expected_bindings_digest(value: Mapping[str, object]) -> str:
    validate_expected_bindings(value)
    return _digest("expected_bindings", value)


READINESS_PLAN_FIELDS = ("schema", "predecessor_commit", "user_authorization_sha256", "index_reference", "docker_path", "docker_sha256", "buildx_path", "buildx_sha256", "codesign_path", "codesign_sha256", "commands", "selected_reference_rule")
READINESS_RESULT_FIELDS = ("schema", "readiness_plan_sha256", "ordered_observation_sha256", "index_sha256", "selected_descriptor", "selected_reference", "platform_sha256", "local_image_observation_sha256", "buildx_version_observation_sha256", "codesign_verify_observation_sha256", "codesign_display_observation_sha256", "ordered_descriptor_set_sha256", "context_sha256", "image_config_digest", "rootfs_diff_ids", "accepted", "failure")
_READINESS_ROLES = ("registry-index", "registry-platform", "local-platform", "buildx-version", "codesign-verify", "codesign-display")
_FAILURES = {"registry_failed", "selection_failed", "platform_digest_failed", "local_resolution_failed", "context_drift", "identity_drift", "signature_drift", "descriptor_drift", "version_transcript_drift"}
UNAVAILABLE_SHA256 = "0" * 64
UNAVAILABLE_PREFIXED_SHA256 = "sha256:" + UNAVAILABLE_SHA256
_READINESS_ENVIRONMENT_FIELDS = ("HOME", "LANG", "LC_ALL", "PATH", "TMPDIR", "TZ", "DOCKER_CONFIG")
_READINESS_HOST_HOME_BASENAME = "host-home"
_READINESS_DOCKER_BIN_DIR = "/Applications/Docker.app/Contents/Resources/bin"
_READINESS_CLOSED_HOST_PATH = "/usr/bin:/bin:" + _READINESS_DOCKER_BIN_DIR


def _validate_readiness_environment(value: object) -> Mapping[str, object]:
    environment = _fields(value, _READINESS_ENVIRONMENT_FIELDS, "readiness environment")
    _path(environment["TMPDIR"], "readiness temporary root", absolute=True)
    expected_home = environment["TMPDIR"] + "/" + _READINESS_HOST_HOME_BASENAME
    _require(
        environment["LANG"] == environment["LC_ALL"] == "C"
        and environment["PATH"] == _READINESS_CLOSED_HOST_PATH
        and environment["TZ"] == "UTC"
        and environment["HOME"] == expected_home,
        "readiness environment constant drift",
    )
    _path(environment["DOCKER_CONFIG"], "readiness Docker config", absolute=True)
    _require(
        environment["TMPDIR"] != environment["DOCKER_CONFIG"],
        "readiness temp/config roots are not separated",
    )
    return environment


def _readiness_expected_argv(plan: Mapping[str, object]) -> Tuple[List[str], ...]:
    commands = plan["commands"]
    _require(isinstance(commands, list) and len(commands) == 6, "readiness command census drift")
    environment = commands[0].get("environment")
    _require(isinstance(environment, dict), "readiness environment missing")
    docker_config = environment.get("DOCKER_CONFIG")
    docker_host = None
    local_argv = commands[2].get("argv")
    if isinstance(local_argv, list) and len(local_argv) >= 8:
        docker_host = local_argv[4]
    _require(
        isinstance(docker_host, str)
        and docker_host.startswith("unix://")
        and docker_host[7:].startswith("/"),
        "readiness Docker host drift",
    )
    prefix = [plan["docker_path"], "--config", docker_config, "--host", docker_host, "--log-level", "error"]
    return (
        [plan["buildx_path"], "imagetools", "inspect", "--raw", plan["index_reference"]],
        [plan["buildx_path"], "imagetools", "inspect", "--raw", PLATFORM_PLACEHOLDER],
        prefix + ["image", "inspect", "--format={{json .}}", PLATFORM_PLACEHOLDER],
        [plan["buildx_path"], "version"],
        [plan["codesign_path"], "--verify", "--strict", "--verbose=4", "/Applications/Docker.app"],
        [plan["codesign_path"], "--display", "--verbose=4", "/Applications/Docker.app"],
    )


def validate_readiness_plan(value: object) -> Mapping[str, object]:
    plan = _fields(value, READINESS_PLAN_FIELDS, "readiness plan")
    _require(plan["schema"] == SCHEMAS["readiness_plan"], "readiness plan schema drift")
    _git(plan["predecessor_commit"], "predecessor commit")
    _sha(plan["user_authorization_sha256"], "user authorization digest")
    _require(plan["index_reference"] == INDEX_REFERENCE, "index reference drift")
    for name in ("docker_path", "buildx_path", "codesign_path"):
        _path(plan[name], name.replace("_", " "), absolute=True)
    for name in ("docker_sha256", "buildx_sha256", "codesign_sha256"):
        _sha(plan[name], name.replace("_", " "))
    _require(
        (plan["docker_path"], plan["docker_sha256"]) == (DOCKER_PATH, DOCKER_SHA256)
        and (plan["buildx_path"], plan["buildx_sha256"]) == (BUILDX_PATH, BUILDX_SHA256)
        and (plan["codesign_path"], plan["codesign_sha256"]) == (CODESIGN_PATH, CODESIGN_SHA256),
        "readiness tool identity drift",
    )
    commands = plan["commands"]
    _require(isinstance(commands, list) and len(commands) == 6, "readiness command census drift")
    roles = []
    for command in commands:
        checked = validate_command(command)
        roles.append(checked["role"])
    _require(tuple(roles) == _READINESS_ROLES, "readiness role order drift")
    _require([item["ordinal"] for item in commands] == list(range(6)), "readiness ordinal drift")
    expected_argv = _readiness_expected_argv(plan)
    environment = _validate_readiness_environment(commands[0]["environment"])
    activations = ("always", "after_index", "after_platform", "after_platform", "after_platform", "after_platform")
    for command, role, argv, activation in zip(commands, _READINESS_ROLES, expected_argv, activations):
        _require(
            command["role"] == role
            and command["argv"] == argv
            and command["environment"] == environment
            and command["cwd"] == "/"
            and command["stdin_policy"] == "closed-null"
            and command["stdout_cap"] == command["stderr_cap"] == 262_144
            and command["timeout_ns"] == 1_800_000_000_000
            and command["activation"] == activation
            and command["expected_outcomes"] == ["exit_zero"],
            "readiness command contract drift: " + role,
        )
    _require(plan["selected_reference_rule"] == {"repository": "docker.io/library/python", "os": "linux", "architecture": "arm64", "variant": "v8", "count": 1}, "selected reference rule drift")
    return plan


def readiness_plan_digest(value: Mapping[str, object]) -> str:
    validate_readiness_plan(value)
    return _digest("readiness_plan", value)


def validate_readiness_result(value: object) -> Mapping[str, object]:
    result = _fields(value, READINESS_RESULT_FIELDS, "readiness result")
    _require(result["schema"] == SCHEMAS["readiness_result"], "readiness result schema drift")
    for name in ("readiness_plan_sha256", "index_sha256", "platform_sha256", "local_image_observation_sha256", "buildx_version_observation_sha256", "codesign_verify_observation_sha256", "codesign_display_observation_sha256", "context_sha256"):
        _sha(result[name], name.replace("_", " "))
    _require(isinstance(result["ordered_observation_sha256"], list) and len(result["ordered_observation_sha256"]) == 6, "readiness observation census drift")
    _require(isinstance(result["ordered_descriptor_set_sha256"], list) and len(result["ordered_descriptor_set_sha256"]) == 2, "readiness descriptor census drift")
    for digest in result["ordered_observation_sha256"] + result["ordered_descriptor_set_sha256"]:
        _sha(digest, "readiness ordered digest")
    descriptor = _fields(result["selected_descriptor"], ("digest", "mediaType", "size", "os", "architecture", "variant"), "selected descriptor")
    _sha(descriptor["digest"], "selected descriptor digest", prefixed=True)
    _require(_is_int(descriptor["size"]) and descriptor["size"] > 0, "descriptor size drift")
    _require((descriptor["os"], descriptor["architecture"], descriptor["variant"]) == ("linux", "arm64", "v8"), "selected platform drift")
    _require(result["selected_reference"] == "docker.io/library/python@" + descriptor["digest"], "selected reference drift")
    _require(descriptor["mediaType"] == "application/vnd.oci.image.manifest.v1+json", "selected descriptor media type drift")
    _sha(result["image_config_digest"], "image config digest", prefixed=True)
    _require(isinstance(result["rootfs_diff_ids"], list) and all(_PREFIXED_SHA_RE.fullmatch(item or "") for item in result["rootfs_diff_ids"]), "RootFS digest drift")
    _require(isinstance(result["accepted"], bool), "accepted must be Boolean")
    if result["accepted"]:
        _require(result["failure"] is None, "accepted readiness carries failure")
        _require(result["index_sha256"] == INDEX_REFERENCE.rsplit(":", 1)[1], "index content digest drift")
        _require(result["platform_sha256"] == descriptor["digest"].split(":", 1)[1], "platform digest drift")
        _require(result["image_config_digest"] == IMAGE_CONFIG_DIGEST and result["rootfs_diff_ids"] == list(ROOTFS_DIFF_IDS), "accepted readiness image identity drift")
    else:
        _require(result["failure"] in _FAILURES, "unknown readiness failure")
        sentinel = {
            "digest": UNAVAILABLE_PREFIXED_SHA256,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "size": 1, "os": "linux", "architecture": "arm64", "variant": "v8",
        }
        _require(
            result["index_sha256"] == UNAVAILABLE_SHA256
            and result["selected_descriptor"] == sentinel
            and result["selected_reference"] == "docker.io/library/python@" + UNAVAILABLE_PREFIXED_SHA256
            and result["platform_sha256"] == UNAVAILABLE_SHA256
            and result["context_sha256"] == UNAVAILABLE_SHA256
            and result["image_config_digest"] == UNAVAILABLE_PREFIXED_SHA256
            and result["rootfs_diff_ids"] == [],
            "rejected readiness sentinel drift",
        )
    return result


def readiness_result_digest(value: Mapping[str, object]) -> str:
    validate_readiness_result(value)
    return _digest("readiness_result", value)


P01B_PROGRAM_ID = "hsai-p01b-retained-normal-oom-v1"
P01B_NETWORK_SCOPE = (
    "a3l7-registry-read-index-platform-only;"
    "a3l8-local-docker-unix-control-plane-only;container-network-none;"
    "no-pull;no-build;no-login;no-other-registry;no-remote-endpoint;"
    "a3l9-no-network"
)
P01B_SUBJECT = "hsai-p01b-local-operator"
P01B_GATEWAY_POLICY_ID = "hsai-p01b-local-policy-v1"
P01B_ADMISSION_POLICY_ID = "hsai-p01b-local-admission-v1"
P01B_GATEWAY_NONCLAIMS = (
    "no score-axis population",
    "not Level2+ evidence",
    "not accepted Evidence Ledger mutation",
    "not direct authority",
    "not model-granted authority",
    "not production readiness",
    "not semantic correctness",
)
P01B_SOURCE_ARTIFACT_IDS = (
    "p01b-a3l6-gate-bundle",
    "p01b-claim-boundary",
    "p01b-implementation-commit",
    "p01b-implementation-tree",
    "p01b-readiness-plan",
    "p01b-user-authorization",
)

GATEWAY_ACTION_DOCUMENT_FIELDS = (
    "schema", "program_id", "network_scope", "user_authorization_sha256",
    "implementation_commit", "implementation_tree", "a3l6_gate_bundle_sha256",
    "readiness_plan_sha256", "claim_boundary_sha256", "proposal_sha256", "proposal",
)
GATEWAY_POLICY_DOCUMENT_FIELDS = (
    "schema", "program_id", "network_scope", "implementation_commit",
    "implementation_tree", "readiness_plan_sha256", "claim_boundary_sha256",
    "gateway_policy",
)
GATEWAY_EVIDENCE_BUNDLE_FIELDS = (
    "schema", "action_sha256", "policy_sha256", "candidate_sha256", "candidate",
)
GATEWAY_ADMISSION_DECISION_FIELDS = (
    "schema", "action_sha256", "policy_sha256", "evidence_bundle_sha256",
    "decision_sha256", "decision",
)


def _rust_hash_array(digest: str, label: str) -> List[int]:
    _sha(digest, label)
    return list(bytes.fromhex(digest))


def _validate_rust_hash_array(value: object, label: str, *, nonzero: bool = True) -> List[int]:
    _require(
        isinstance(value, list) and len(value) == 32
        and all(_is_int(item) and 0 <= item <= 255 for item in value),
        label + " must be 32 integer bytes",
    )
    if nonzero:
        _require(any(value), label + " is zero")
    return value


def _rust_serde_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":"),
            sort_keys=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise EvidenceError("Rust Serde value is not JSON serializable") from error


def _rust_tagged_digest(tag: str, value: Mapping[str, object]) -> str:
    _ascii(tag, "Rust digest tag")
    return sha256_hex(_rust_serde_json_bytes([tag, value]))


def _validate_user_authorization_raw(raw: bytes) -> str:
    _require(isinstance(raw, bytes) and raw and b"\x00" not in raw, "user authorization bytes drift")
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EvidenceError("user authorization is not UTF-8") from error
    return sha256_hex(raw)


def _expected_gateway_proposal(
    *, user_authorization_sha256: str, implementation_commit: str,
    implementation_tree: str, a3l6_gate_bundle_sha256: str,
    readiness_plan_sha256: str, claim_boundary_sha256: str,
) -> Dict[str, object]:
    for value, label in (
        (user_authorization_sha256, "user authorization digest"),
        (a3l6_gate_bundle_sha256, "A3L6 gate bundle digest"),
        (readiness_plan_sha256, "readiness plan digest"),
        (claim_boundary_sha256, "claim boundary digest"),
    ):
        _sha(value, label)
    _git(implementation_commit, "authority implementation commit")
    _git(implementation_tree, "authority implementation tree")
    action_id = "p01b-{}-{}".format(
        user_authorization_sha256[:16], implementation_commit[:16]
    )
    source_digests = (
        a3l6_gate_bundle_sha256,
        claim_boundary_sha256,
        sha256_hex(implementation_commit.encode("ascii")),
        sha256_hex(implementation_tree.encode("ascii")),
        readiness_plan_sha256,
        user_authorization_sha256,
    )
    artifacts = [
        {"id": artifact_id, "sha256": _rust_hash_array(digest, artifact_id)}
        for artifact_id, digest in zip(P01B_SOURCE_ARTIFACT_IDS, source_digests)
    ]
    template = {
        "schema": SCHEMAS["gateway_action_template"],
        "program_id": P01B_PROGRAM_ID,
        "action_kind": "ToolCall", "target": P01B_PROGRAM_ID, "value_units": 0,
    }
    action_input = {
        "schema": SCHEMAS["gateway_action_input"], "program_id": P01B_PROGRAM_ID,
        "user_authorization_sha256": user_authorization_sha256,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "a3l6_gate_bundle_sha256": a3l6_gate_bundle_sha256,
        "readiness_plan_sha256": readiness_plan_sha256,
        "claim_boundary_sha256": claim_boundary_sha256,
    }
    action_output = {
        "schema": SCHEMAS["gateway_action_output"], "id": action_id,
        "subject": P01B_SUBJECT, "action_kind": "ToolCall",
        "target": P01B_PROGRAM_ID, "value_units": 0,
        "source_artifact_digests": artifacts,
        "nonclaims": list(P01B_GATEWAY_NONCLAIMS), "threat_labels": ["Benign"],
        "direct_authority_requested": False,
        "signer_or_tool_requested_before_admission": False,
    }
    model_lane = {
        "lane_kind": "Deterministic", "model_family": "hsai-p01b-authority-adapter",
        "artifact_id": "hsai-p01b-a3l7-authority-adapter-v1",
        "runtime": "python-stdlib-no-model-execution",
        "prompt_template_digest": _rust_hash_array(_digest("gateway_action_template", template), "action template digest"),
        "input_corpus_digest": _rust_hash_array(_digest("gateway_action_input", action_input), "action input digest"),
        "output_bundle_digest": _rust_hash_array(_digest("gateway_action_output", action_output), "action output digest"),
        "non_secret": True,
    }
    return {
        "id": action_id, "subject": P01B_SUBJECT, "action_kind": "ToolCall",
        "target": P01B_PROGRAM_ID, "value_units": 0,
        "source_artifact_digests": artifacts,
        "nonclaims": list(P01B_GATEWAY_NONCLAIMS), "model_lane": model_lane,
        "threat_labels": ["Benign"], "direct_authority_requested": False,
        "signer_or_tool_requested_before_admission": False,
    }


def gateway_action_proposal_digest(value: Mapping[str, object]) -> str:
    _fields(value, (
        "id", "subject", "action_kind", "target", "value_units",
        "source_artifact_digests", "nonclaims", "model_lane", "threat_labels",
        "direct_authority_requested", "signer_or_tool_requested_before_admission",
    ), "GatewayActionProposal")
    return _rust_tagged_digest(
        "hsai-agent-admission:gateway-action-proposal:v1", value
    )


def build_gateway_action_document(
    user_authorization_raw: bytes, implementation_commit: str,
    implementation_tree: str, a3l6_gate_bundle: Mapping[str, object],
    readiness_plan: Mapping[str, object], claim_boundary: Mapping[str, object],
) -> Dict[str, object]:
    user_sha = _validate_user_authorization_raw(user_authorization_raw)
    gate_sha = a3l6_gate_bundle_digest(a3l6_gate_bundle)
    readiness_sha = readiness_plan_digest(readiness_plan)
    claim_sha = claim_boundary_digest(claim_boundary)
    proposal = _expected_gateway_proposal(
        user_authorization_sha256=user_sha,
        implementation_commit=implementation_commit,
        implementation_tree=implementation_tree,
        a3l6_gate_bundle_sha256=gate_sha, readiness_plan_sha256=readiness_sha,
        claim_boundary_sha256=claim_sha,
    )
    value = {
        "schema": SCHEMAS["gateway_action_document"],
        "program_id": P01B_PROGRAM_ID, "network_scope": P01B_NETWORK_SCOPE,
        "user_authorization_sha256": user_sha,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "a3l6_gate_bundle_sha256": gate_sha,
        "readiness_plan_sha256": readiness_sha,
        "claim_boundary_sha256": claim_sha,
        "proposal_sha256": gateway_action_proposal_digest(proposal),
        "proposal": proposal,
    }
    validate_gateway_action_document(value)
    return value


def validate_gateway_action_document(value: object) -> Mapping[str, object]:
    row = _fields(value, GATEWAY_ACTION_DOCUMENT_FIELDS, "gateway action document")
    _require(row["schema"] == SCHEMAS["gateway_action_document"], "gateway action schema drift")
    _require(row["program_id"] == P01B_PROGRAM_ID and row["network_scope"] == P01B_NETWORK_SCOPE, "gateway action program/network drift")
    expected = _expected_gateway_proposal(
        user_authorization_sha256=row["user_authorization_sha256"],
        implementation_commit=row["implementation_commit"],
        implementation_tree=row["implementation_tree"],
        a3l6_gate_bundle_sha256=row["a3l6_gate_bundle_sha256"],
        readiness_plan_sha256=row["readiness_plan_sha256"],
        claim_boundary_sha256=row["claim_boundary_sha256"],
    )
    _require(row["proposal"] == expected, "GatewayActionProposal reconstruction drift")
    _require(row["proposal_sha256"] == gateway_action_proposal_digest(expected), "gateway proposal tagged digest drift")
    return row


def gateway_action_document_digest(value: Mapping[str, object]) -> str:
    validate_gateway_action_document(value)
    return _digest("gateway_action_document", value)


def _expected_gateway_policy() -> Dict[str, object]:
    return {
        "id": P01B_GATEWAY_POLICY_ID,
        "admission_policy": {
            "id": P01B_ADMISSION_POLICY_ID, "max_claim_boundary": "LocalOnly",
            "required_nonclaims": list(P01B_GATEWAY_NONCLAIMS),
            "require_source_artifacts": True,
            "allow_provider_direct_authority": False,
        },
        "allowed_action_kinds": ["ToolCall"],
        "allowed_targets": [P01B_PROGRAM_ID], "max_value_units": 0,
        "require_non_secret_model_lane": True,
    }


def build_gateway_policy_document(
    implementation_commit: str, implementation_tree: str,
    readiness_plan: Mapping[str, object], claim_boundary: Mapping[str, object],
) -> Dict[str, object]:
    _git(implementation_commit, "policy implementation commit")
    _git(implementation_tree, "policy implementation tree")
    value = {
        "schema": SCHEMAS["gateway_policy_document"],
        "program_id": P01B_PROGRAM_ID, "network_scope": P01B_NETWORK_SCOPE,
        "implementation_commit": implementation_commit,
        "implementation_tree": implementation_tree,
        "readiness_plan_sha256": readiness_plan_digest(readiness_plan),
        "claim_boundary_sha256": claim_boundary_digest(claim_boundary),
        "gateway_policy": _expected_gateway_policy(),
    }
    validate_gateway_policy_document(value)
    return value


def validate_gateway_policy_document(value: object) -> Mapping[str, object]:
    row = _fields(value, GATEWAY_POLICY_DOCUMENT_FIELDS, "gateway policy document")
    _require(row["schema"] == SCHEMAS["gateway_policy_document"], "gateway policy schema drift")
    _require(row["program_id"] == P01B_PROGRAM_ID and row["network_scope"] == P01B_NETWORK_SCOPE, "gateway policy program/network drift")
    _git(row["implementation_commit"], "policy implementation commit")
    _git(row["implementation_tree"], "policy implementation tree")
    _sha(row["readiness_plan_sha256"], "policy readiness digest")
    _sha(row["claim_boundary_sha256"], "policy claim digest")
    _require(row["gateway_policy"] == _expected_gateway_policy(), "GatewayActionPolicy reconstruction drift")
    return row


def gateway_policy_document_digest(value: Mapping[str, object]) -> str:
    validate_gateway_policy_document(value)
    return _digest("gateway_policy_document", value)


def _expected_gateway_candidate(action: Mapping[str, object]) -> Dict[str, object]:
    proposal = _expected_gateway_proposal(
        user_authorization_sha256=action["user_authorization_sha256"],
        implementation_commit=action["implementation_commit"],
        implementation_tree=action["implementation_tree"],
        a3l6_gate_bundle_sha256=action["a3l6_gate_bundle_sha256"],
        readiness_plan_sha256=action["readiness_plan_sha256"],
        claim_boundary_sha256=action["claim_boundary_sha256"],
    )
    return {
        "id": proposal["id"], "subject": proposal["subject"],
        "source_kind": "GatewayActionProposal", "strict_typed": True,
        "case": None, "proposed_envelope": None, "gateway_action": proposal,
        "requested_claim_boundary": "LocalOnly",
        "source_artifact_digests": proposal["source_artifact_digests"],
        "nonclaims": proposal["nonclaims"],
        "provider_direct_authority_requested": False,
        "accepted_ledger_mutation_requested": False,
        "score_axis_population_requested": False,
        "external_or_formal_evidence_claimed": False,
    }


def gateway_candidate_digest(value: Mapping[str, object]) -> str:
    _fields(value, (
        "id", "subject", "source_kind", "strict_typed", "case",
        "proposed_envelope", "gateway_action", "requested_claim_boundary",
        "source_artifact_digests", "nonclaims",
        "provider_direct_authority_requested", "accepted_ledger_mutation_requested",
        "score_axis_population_requested", "external_or_formal_evidence_claimed",
    ), "AgentAdmissionCandidate")
    return _rust_tagged_digest("hsai-agent-admission:candidate:v1", value)


def build_gateway_evidence_bundle_document(
    action_document: Mapping[str, object], policy_document: Mapping[str, object],
) -> Dict[str, object]:
    action = validate_gateway_action_document(action_document)
    policy = validate_gateway_policy_document(policy_document)
    candidate = _expected_gateway_candidate(action)
    value = {
        "schema": SCHEMAS["gateway_evidence_bundle"],
        "action_sha256": gateway_action_document_digest(action),
        "policy_sha256": gateway_policy_document_digest(policy),
        "candidate_sha256": gateway_candidate_digest(candidate),
        "candidate": candidate,
    }
    validate_gateway_evidence_bundle_document(value, action, policy)
    return value


def validate_gateway_evidence_bundle_document(
    value: object, action_document: Mapping[str, object],
    policy_document: Mapping[str, object],
) -> Mapping[str, object]:
    row = _fields(value, GATEWAY_EVIDENCE_BUNDLE_FIELDS, "gateway evidence bundle")
    _require(row["schema"] == SCHEMAS["gateway_evidence_bundle"], "gateway evidence schema drift")
    action = validate_gateway_action_document(action_document)
    policy = validate_gateway_policy_document(policy_document)
    expected = _expected_gateway_candidate(action)
    _require(policy["gateway_policy"] == _expected_gateway_policy(), "candidate policy drift")
    _require(row["candidate"] == expected, "gateway_action_candidate reconstruction drift")
    _require(
        row["action_sha256"] == gateway_action_document_digest(action)
        and row["policy_sha256"] == gateway_policy_document_digest(policy)
        and row["candidate_sha256"] == gateway_candidate_digest(expected),
        "gateway evidence digest graph drift",
    )
    return row


def gateway_evidence_bundle_document_digest(
    value: Mapping[str, object], action_document: Mapping[str, object],
    policy_document: Mapping[str, object],
) -> str:
    validate_gateway_evidence_bundle_document(value, action_document, policy_document)
    return _digest("gateway_evidence_bundle", value)


def _expected_gateway_decision(
    candidate: Mapping[str, object], policy: Mapping[str, object],
) -> Dict[str, object]:
    return {
        "candidate_id": candidate["id"],
        "policy_id": policy["admission_policy"]["id"], "verdict": "Accepted",
        "reasons": [],
        "candidate_digest": _rust_hash_array(gateway_candidate_digest(candidate), "candidate digest"),
        "accepted_envelope": None,
    }


def gateway_admission_decision_production_digest(value: Mapping[str, object]) -> str:
    _fields(value, (
        "candidate_id", "policy_id", "verdict", "reasons",
        "candidate_digest", "accepted_envelope",
    ), "AgentAdmissionDecision")
    _validate_rust_hash_array(value["candidate_digest"], "decision candidate digest")
    return _rust_tagged_digest("hsai-agent-admission:decision:v1", value)


def build_gateway_admission_decision_document(
    action_document: Mapping[str, object], policy_document: Mapping[str, object],
    evidence_bundle_document: Mapping[str, object],
) -> Dict[str, object]:
    action = validate_gateway_action_document(action_document)
    policy = validate_gateway_policy_document(policy_document)
    evidence_bundle = validate_gateway_evidence_bundle_document(
        evidence_bundle_document, action, policy
    )
    decision = _expected_gateway_decision(
        _expected_gateway_candidate(action), policy["gateway_policy"]
    )
    value = {
        "schema": SCHEMAS["gateway_admission_decision"],
        "action_sha256": gateway_action_document_digest(action),
        "policy_sha256": gateway_policy_document_digest(policy),
        "evidence_bundle_sha256": gateway_evidence_bundle_document_digest(
            evidence_bundle, action, policy
        ),
        "decision_sha256": gateway_admission_decision_production_digest(decision),
        "decision": decision,
    }
    validate_gateway_admission_decision_document(value, action, policy, evidence_bundle)
    return value


def validate_gateway_admission_decision_document(
    value: object, action_document: Mapping[str, object],
    policy_document: Mapping[str, object],
    evidence_bundle_document: Mapping[str, object],
) -> Mapping[str, object]:
    row = _fields(value, GATEWAY_ADMISSION_DECISION_FIELDS, "gateway admission decision")
    _require(row["schema"] == SCHEMAS["gateway_admission_decision"], "gateway decision schema drift")
    action = validate_gateway_action_document(action_document)
    policy = validate_gateway_policy_document(policy_document)
    evidence_bundle = validate_gateway_evidence_bundle_document(
        evidence_bundle_document, action, policy
    )
    expected = _expected_gateway_decision(
        _expected_gateway_candidate(action), policy["gateway_policy"]
    )
    _require(row["decision"] == expected, "evaluate_admission reconstruction drift")
    _require(
        row["action_sha256"] == gateway_action_document_digest(action)
        and row["policy_sha256"] == gateway_policy_document_digest(policy)
        and row["evidence_bundle_sha256"] == gateway_evidence_bundle_document_digest(evidence_bundle, action, policy)
        and row["decision_sha256"] == gateway_admission_decision_production_digest(expected),
        "gateway admission decision digest graph drift",
    )
    return row


def gateway_admission_decision_document_digest(
    value: Mapping[str, object], action_document: Mapping[str, object],
    policy_document: Mapping[str, object],
    evidence_bundle_document: Mapping[str, object],
) -> str:
    validate_gateway_admission_decision_document(
        value, action_document, policy_document, evidence_bundle_document
    )
    return _digest("gateway_admission_decision", value)


def _ephemeral_gateway_handoff(
    action: Mapping[str, object], policy: Mapping[str, object],
    evidence_bundle: Mapping[str, object], decision_document: Mapping[str, object],
) -> Dict[str, object]:
    candidate = _expected_gateway_candidate(action)
    decision = decision_document["decision"]
    _require(
        decision == _expected_gateway_decision(candidate, policy["gateway_policy"])
        and decision["verdict"] == "Accepted",
        "accepted gateway handoff unavailable",
    )
    proposal = _expected_gateway_proposal(
        user_authorization_sha256=action["user_authorization_sha256"],
        implementation_commit=action["implementation_commit"],
        implementation_tree=action["implementation_tree"],
        a3l6_gate_bundle_sha256=action["a3l6_gate_bundle_sha256"],
        readiness_plan_sha256=action["readiness_plan_sha256"],
        claim_boundary_sha256=action["claim_boundary_sha256"],
    )
    return {
        "action_id": proposal["id"], "subject": proposal["subject"],
        "action_kind": proposal["action_kind"], "target": proposal["target"],
        "value_units": proposal["value_units"],
        "candidate_digest": _rust_hash_array(gateway_candidate_digest(candidate), "handoff candidate digest"),
        "decision_digest": _rust_hash_array(gateway_admission_decision_production_digest(decision), "handoff decision digest"),
    }


def validate_preauthorization_graph(
    user_authorization_raw: bytes, action_document: object, policy_document: object,
    evidence_bundle_document: object, admission_decision_document: object,
    a3l6_gate_bundle: object, readiness_plan: object, claim_boundary: object,
    preauthorization: object,
) -> Mapping[str, object]:
    user_sha = _validate_user_authorization_raw(user_authorization_raw)
    action = validate_gateway_action_document(action_document)
    policy = validate_gateway_policy_document(policy_document)
    evidence_bundle = validate_gateway_evidence_bundle_document(
        evidence_bundle_document, action, policy
    )
    decision = validate_gateway_admission_decision_document(
        admission_decision_document, action, policy, evidence_bundle
    )
    gate = validate_a3l6_gate_bundle(a3l6_gate_bundle)
    ready_plan = validate_readiness_plan(readiness_plan)
    boundary = validate_claim_boundary(claim_boundary)
    common = (
        action["program_id"] == policy["program_id"] == P01B_PROGRAM_ID
        and action["network_scope"] == policy["network_scope"] == P01B_NETWORK_SCOPE
        and action["user_authorization_sha256"] == user_sha
        and action["implementation_commit"] == policy["implementation_commit"] == gate["implementation_commit"]
        and action["implementation_tree"] == policy["implementation_tree"] == gate["implementation_tree"]
        and action["a3l6_gate_bundle_sha256"] == a3l6_gate_bundle_digest(gate)
        and action["readiness_plan_sha256"] == policy["readiness_plan_sha256"] == readiness_plan_digest(ready_plan)
        and action["claim_boundary_sha256"] == policy["claim_boundary_sha256"] == claim_boundary_digest(boundary)
    )
    _require(common, "preauthorization authority wrapper cross-binding drift")
    preauth = validate_preauthorization(preauthorization)
    expected = {
        "user_authorization_sha256": user_sha,
        "predecessor_commit": ready_plan["predecessor_commit"],
        "action_sha256": gateway_action_document_digest(action),
        "policy_sha256": gateway_policy_document_digest(policy),
        "evidence_bundle_sha256": gateway_evidence_bundle_document_digest(evidence_bundle, action, policy),
        "a3l6_gate_bundle_sha256": a3l6_gate_bundle_digest(gate),
        "admission_decision_sha256": gateway_admission_decision_document_digest(decision, action, policy, evidence_bundle),
        "implementation_commit": action["implementation_commit"],
        "implementation_tree": action["implementation_tree"],
        "readiness_plan_sha256": readiness_plan_digest(ready_plan),
    }
    _require(all(preauth[name] == value for name, value in expected.items()), "preauthorization authority graph drift")
    return {
        "action": action, "policy": policy, "evidence_bundle": evidence_bundle,
        "decision": decision, "gate_bundle": gate, "readiness_plan": ready_plan,
        "claim_boundary": boundary, "preauthorization": preauth,
        "ephemeral_accepted_handoff": _ephemeral_gateway_handoff(action, policy, evidence_bundle, decision),
    }


def _validate_authorized_plan_scope(
    readiness_plan: Mapping[str, object], campaign_plan: object,
    normal_plan: object, oom_plan: object, authorization_sha256: str,
    implementation_commit: str, platform_reference: str,
    snapshot_copy_manifest_sha256: str, snapshot_copy_root: Optional[str],
) -> Mapping[str, object]:
    campaign = validate_campaign_plan(campaign_plan)
    normal = validate_attempt_plan(normal_plan)
    oom = validate_attempt_plan(oom_plan)
    _require(
        campaign["authorization_sha256"] == normal["authorization_sha256"] == oom["authorization_sha256"] == authorization_sha256
        and campaign["implementation_commit"] == normal["implementation_commit"] == oom["implementation_commit"] == implementation_commit
        and campaign["readiness_plan_sha256"] == readiness_plan_digest(readiness_plan)
        and campaign["normal_plan_sha256"] == attempt_plan_digest(normal)
        and campaign["oom_plan_sha256"] == attempt_plan_digest(oom),
        "postauthorization plan digest graph drift",
    )
    _require(
        normal["campaign_id"] == oom["campaign_id"] == campaign["campaign_id"]
        and (normal["attempt_id"], normal["attempt_kind"]) == ("normal", "normal")
        and (oom["attempt_id"], oom["attempt_kind"]) == ("oom", "oom-child")
        and normal["platform_manifest_reference"] == oom["platform_manifest_reference"] == platform_reference
        and normal["source_manifest_sha256"] == oom["source_manifest_sha256"] == snapshot_copy_manifest_sha256,
        "postauthorization plan identity drift",
    )
    if snapshot_copy_root is None:
        mount_rows = [
            item for item in normal["commands"][2]["argv"]
            if item.startswith("--mount=type=bind,src=")
        ]
        _require(len(mount_rows) == 1, "attempt snapshot root missing")
        match = re.fullmatch(
            r"--mount=type=bind,src=(/[^,\x00\r\n]+),dst=/input,readonly,bind-propagation=rprivate",
            mount_rows[0],
        )
        _require(match is not None, "attempt snapshot root invalid")
        snapshot_copy_root = match.group(1)
    readiness_environment = readiness_plan["commands"][0]["environment"]
    docker_prefix = readiness_plan["commands"][2]["argv"][:7]
    _require(
        docker_prefix[0] == DOCKER_PATH
        and docker_prefix[1:3] == ["--config", readiness_environment["DOCKER_CONFIG"]]
        and docker_prefix[3] == "--host"
        and isinstance(docker_prefix[4], str) and docker_prefix[4].startswith("unix:///")
        and docker_prefix[5:] == ["--log-level", "error"],
        "authorized local Docker prefix drift",
    )
    expected_roles = (
        "absence-name-pre", "absence-label-pre", "create", "inspect-prestart",
        "start-attach", "export-running", "release", "emergency-kill", "wait",
        "inspect-terminal", "remove", "absence-cid", "absence-name",
        "absence-label", "daemon-recheck",
    )
    for plan in (normal, oom):
        commands = plan["commands"]
        _require(
            tuple(item["role"] for item in commands) == expected_roles
            and [item["ordinal"] for item in commands] == list(range(15)),
            "attempt command role/order drift",
        )
        for command in commands:
            _require(
                command["environment"] == readiness_environment
                and command["cwd"] == "/"
                and command["stdin_policy"] == "closed-null"
                and command["timeout_ns"] == 1_800_000_000_000
                and command["argv"][:7] == docker_prefix,
                "attempt command authority override",
            )
        create = commands[2]["argv"]
        _require(
            create[7:10] == ["container", "create", "--pull=never"]
            and create.count("--pull=never") == 1
            and create.count("--network=none") == 1
            and "--platform=linux/arm64/v8" in create
            and platform_reference in create
            and create[-9:] == [
                "/usr/local/bin/python3", "-B",
                "tools/hsai-formal-preflight/p01b_container_probe.py", "--mode",
                plan["attempt_kind"], "--input-manifest-sha256",
                snapshot_copy_manifest_sha256, "--output", "/work/result.json",
            ],
            "attempt create network/workload scope drift",
        )
        forbidden = ("pull", "build", "login", "/bin/sh", "/bin/bash", "sh", "bash")
        _require(
            not any(item in forbidden for command in commands for item in command["argv"])
            and not any(item.startswith("tcp://") or item.startswith("ssh://") for command in commands for item in command["argv"]),
            "attempt plan broadened network/shell authority",
        )
        create = commands[2]["argv"]
        mounts = [item for item in create if item.startswith("--mount=type=bind,src=")]
        seccomp = [item for item in create if item.startswith("--security-opt=seccomp=")]
        _require(
            mounts == [
                "--mount=type=bind,src={},dst=/input,readonly,bind-propagation=rprivate".format(snapshot_copy_root)
            ]
            and seccomp == [
                "--security-opt=seccomp=" + snapshot_copy_root
                + "/tools/hsai-formal-preflight/p01b_container_seccomp.json"
            ],
            "attempt retained snapshot root authority drift",
        )
    campaign_commands = [campaign["native_command"], *campaign["metadata_commands"]]
    _require(
        tuple(item["role"] for item in campaign_commands)
        == ("native-reference", "docker-version", "docker-info", "image-config")
        and [item["ordinal"] for item in campaign_commands] == list(range(4)),
        "campaign command role/order drift",
    )
    for command in campaign_commands:
        _require(
            command["environment"] == readiness_environment
            and command["cwd"] == "/" and command["stdin_policy"] == "closed-null"
            and command["timeout_ns"] == 1_800_000_000_000,
            "campaign command authority override",
        )
    _require(
        campaign_commands[0]["argv"] == [
            "/usr/bin/python3", "-B",
            snapshot_copy_root + "/tools/hsai-formal-preflight/p01b_container_probe.py",
            "--mode", "native-reference",
        ]
        and all(item["argv"][:7] == docker_prefix for item in campaign_commands[1:])
        and campaign_commands[1]["argv"][7:] == ["version", "--format={{json .}}"]
        and campaign_commands[2]["argv"][7:] == ["info", "--format={{json .}}"]
        and campaign_commands[3]["argv"][7:] == ["image", "inspect", "--format={{json .}}", IMAGE_CONFIG_DIGEST],
        "campaign exact local command scope drift",
    )
    return {"campaign": campaign, "normal": normal, "oom": oom}


def validate_authority_graph(
    user_authorization_raw: bytes, action_document: object, policy_document: object,
    evidence_bundle_document: object, admission_decision_document: object,
    a3l6_gate_bundle: object, readiness_plan: object, claim_boundary: object,
    preauthorization: object, expected_bindings: object, readiness_result: object,
    authorization_root: object, authorization: object, campaign_plan: object,
    normal_plan: object, oom_plan: object,
    snapshot_copy_root: Optional[str] = None,
) -> Mapping[str, object]:
    graph = dict(validate_preauthorization_graph(
        user_authorization_raw, action_document, policy_document,
        evidence_bundle_document, admission_decision_document, a3l6_gate_bundle,
        readiness_plan, claim_boundary, preauthorization,
    ))
    bindings = validate_expected_bindings(expected_bindings)
    ready_result = validate_readiness_result(readiness_result)
    _require(ready_result["accepted"] is True and ready_result["failure"] is None, "authority readiness is not accepted")
    action = graph["action"]; policy = graph["policy"]
    evidence_bundle = graph["evidence_bundle"]; decision = graph["decision"]
    gate = graph["gate_bundle"]; preauth = graph["preauthorization"]
    _require(
        bindings["user_authorization_sha256"] == action["user_authorization_sha256"]
        and bindings["implementation_commit"] == action["implementation_commit"]
        and bindings["implementation_tree"] == action["implementation_tree"]
        and bindings["a3l6_gate_bundle_sha256"] == a3l6_gate_bundle_digest(gate)
        and bindings["claim_boundary_sha256"] == action["claim_boundary_sha256"]
        and ready_result["readiness_plan_sha256"] == action["readiness_plan_sha256"],
        "expected binding/authority input drift",
    )
    digests = {
        "user_authorization_sha256": action["user_authorization_sha256"],
        "action_sha256": gateway_action_document_digest(action),
        "policy_sha256": gateway_policy_document_digest(policy),
        "evidence_bundle_sha256": gateway_evidence_bundle_document_digest(evidence_bundle, action, policy),
        "a3l6_gate_bundle_sha256": a3l6_gate_bundle_digest(gate),
        "admission_decision_sha256": gateway_admission_decision_document_digest(decision, action, policy, evidence_bundle),
    }
    root = validate_authorization_root(authorization_root)
    auth = validate_authorization(authorization)
    for name, digest in digests.items():
        _require(preauth[name] == root[name] == auth[name] == digest, "authority common digest drift: " + name)
    expected_sha = expected_bindings_digest(bindings)
    readiness_sha = readiness_result_digest(ready_result)
    _require(
        root["preauthorization_sha256"] == preauthorization_digest(preauth)
        and root["expected_bindings_sha256"] == auth["expected_bindings_sha256"] == expected_sha
        and root["readiness_sha256"] == auth["readiness_sha256"] == readiness_sha
        and auth["authorization_root_sha256"] == authorization_root_digest(root)
        and root["implementation_commit"] == auth["implementation_commit"] == action["implementation_commit"]
        and root["implementation_tree"] == auth["implementation_tree"] == action["implementation_tree"],
        "final authority graph drift",
    )
    authorization_sha = authorization_digest(auth)
    plans = _validate_authorized_plan_scope(
        graph["readiness_plan"], campaign_plan, normal_plan, oom_plan,
        authorization_sha, action["implementation_commit"],
        bindings["platform_reference"], bindings["snapshot_copy_manifest_sha256"],
        snapshot_copy_root,
    )
    graph.update({
        "expected_bindings": bindings, "readiness_result": ready_result,
        "authorization_root": root, "authorization": auth, **plans,
    })
    return graph


def _reconstruct_readiness_failure(
    items: Sequence[Tuple[Mapping[str, object], bytes, bytes]],
) -> Tuple[Optional[str], int]:
    selected = None
    for ordinal, (observation, stdout, stderr) in enumerate(items):
        if observation["outcome"] == "not_run":
            _require(
                all(item[0]["outcome"] == "not_run" for item in items[ordinal:]),
                "rejected readiness not-run suffix drift",
            )
            return None, ordinal
        if ordinal == 0:
            if (
                observation["outcome"] != "exit" or observation["exit_code"] != 0
                or stderr != b""
                or sha256_hex(stdout) != INDEX_REFERENCE.rsplit(":", 1)[1]
            ):
                return "registry_failed", ordinal + 1
            try:
                index = strict_json_bytes(stdout, MAX_RESULT_BYTES)
                _validate_registry_document(index, "registry-index")
                matches = [
                    item for item in index["manifests"]
                    if item["platform"]
                    == {"os": "linux", "architecture": "arm64", "variant": "v8"}
                ]
                _require(len(matches) == 1, "registry platform selection was not unique")
                selected = matches[0]
            except EvidenceError:
                return "selection_failed", ordinal + 1
        elif ordinal == 1:
            if observation["outcome"] != "exit" or observation["exit_code"] != 0 or stderr != b"":
                return "platform_digest_failed", ordinal + 1
            try:
                _require(selected is not None, "selected platform is absent")
                _require(
                    len(stdout) == selected["size"]
                    and sha256_hex(stdout) == selected["digest"].split(":", 1)[1],
                    "platform content drift",
                )
                platform = strict_json_bytes(stdout, MAX_RESULT_BYTES)
                _validate_registry_document(platform, "registry-platform")
                _require(platform.get("mediaType") == selected["mediaType"], "platform media type drift")
                _require(platform["config"]["digest"] == IMAGE_CONFIG_DIGEST, "platform config drift")
                _require(len(platform["layers"]) == len(ROOTFS_DIFF_IDS), "platform layer count drift")
            except EvidenceError:
                return "platform_digest_failed", ordinal + 1
        elif ordinal == 2:
            if observation["outcome"] != "exit" or observation["exit_code"] != 0 or stderr != b"":
                return "local_resolution_failed", ordinal + 1
            try:
                _require(stdout.endswith(b"\n") and not stdout.endswith(b"\n\n"), "local image framing drift")
                local = strict_json_bytes(stdout[:-1], MAX_RESULT_BYTES)
                _require(isinstance(local, dict), "local image root drift")
                rootfs = _fields(local.get("RootFS"), ("Type", "Layers"), "local RootFS")
                _require(
                    local.get("Id") == IMAGE_CONFIG_DIGEST
                    and local.get("Os") == "linux"
                    and local.get("Architecture") == "arm64"
                    and local.get("Variant") in (None, "", "v8")
                    and rootfs == {"Type": "layers", "Layers": list(ROOTFS_DIFF_IDS)},
                    "local image identity drift",
                )
            except EvidenceError:
                return "local_resolution_failed", ordinal + 1
        elif ordinal == 3:
            expected = b"github.com/docker/buildx v0.34.1-desktop.1 c79576280a671664e17eb68da98ec3136b614aed\n"
            if (
                observation["outcome"] != "exit" or observation["exit_code"] != 0
                or stdout != expected or stderr != b""
            ):
                return "version_transcript_drift", ordinal + 1
        elif ordinal == 4:
            if observation["outcome"] != "exit" or observation["exit_code"] != 0 or stdout != b"":
                return "signature_drift", ordinal + 1
            try:
                _parse_codesign_verify(stderr)
            except EvidenceError:
                return "signature_drift", ordinal + 1
        else:
            if observation["outcome"] != "exit" or observation["exit_code"] != 0 or stdout != b"":
                return "signature_drift", ordinal + 1
            try:
                _parse_codesign_display(stderr)
            except EvidenceError:
                return "signature_drift", ordinal + 1
    return None, len(items)


def validate_readiness_graph(
    plan: object,
    result: object,
    observations_with_streams: Sequence[Tuple[Mapping[str, object], bytes, bytes]],
    host_descriptor_set: object,
    desktop_descriptor_set: object,
    transcript_bindings: object,
    context_companion: object,
    context_raw: bytes,
    readiness_provenance: object,
    receipt_chain: object,
) -> Mapping[str, object]:
    checked_plan = validate_readiness_plan(plan)
    checked_result = validate_readiness_result(result)
    _require(isinstance(observations_with_streams, (list, tuple)) and len(observations_with_streams) == 6, "readiness observation census drift")
    observations = []
    for item in observations_with_streams:
        _require(isinstance(item, (list, tuple)) and len(item) == 3 and isinstance(item[1], bytes) and isinstance(item[2], bytes), "readiness observation tuple drift")
        observations.append(validate_observation(item[0], item[1], item[2]))
    _require(tuple(item["role"] for item in observations) == _READINESS_ROLES, "readiness observation role order drift")
    _require(checked_result["readiness_plan_sha256"] == readiness_plan_digest(checked_plan), "readiness result plan binding drift")
    _require(checked_result["ordered_observation_sha256"] == [observation_digest(item) for item in observations], "readiness result observation binding drift")
    host_set = validate_descriptor_set(host_descriptor_set)
    desktop_set = validate_descriptor_set(desktop_descriptor_set)
    _require(host_set["kind"] == "host-tools" and desktop_set["kind"] == "docker-desktop", "readiness descriptor-set kind drift")
    _require(checked_result["ordered_descriptor_set_sha256"] == [descriptor_set_digest(host_set), descriptor_set_digest(desktop_set)], "readiness descriptor-set binding drift")
    context = _validate_docker_context_capture(context_companion, context_raw)
    validate_receipt_chain(receipt_chain, checked_plan, observations_with_streams)
    if not checked_result["accepted"]:
        if all(item["outcome"] == "not_run" for item in observations):
            _require(
                checked_result["failure"]
                in ("identity_drift", "context_drift", "descriptor_drift"),
                "rejected readiness all-not-run failure drift",
            )
            return checked_result
        reconstructed_failure, completed = _reconstruct_readiness_failure(
            observations_with_streams
        )
        if reconstructed_failure is None:
            _require(
                completed < len(observations)
                and checked_result["failure"] == "identity_drift",
                "rejected readiness lacks reconstructable failure",
            )
        else:
            _require(
                checked_result["failure"] == reconstructed_failure
                and all(item["outcome"] == "not_run" for item in observations[completed:]),
                "rejected readiness failure classification drift",
            )
        return checked_result
    host_set = _validate_host_tool_descriptor_set(host_set)
    desktop_set = _validate_desktop_descriptor_set(desktop_set)
    context = validate_docker_context(context, context_raw)
    _require(all(item["outcome"] == "exit" and item["exit_code"] == 0 and item["signal"] is None for item in observations), "accepted readiness command failure")
    bindings = transcript_bindings
    if isinstance(bindings, list):
        bindings = {item.get("kind"): item for item in bindings if isinstance(item, dict)}
    _require(isinstance(bindings, dict) and set(bindings) == {"registry-index", "registry-platform", "codesign-verify", "codesign-display"}, "readiness transcript-binding census drift")
    source_rows = {
        "registry-index": observations_with_streams[0],
        "registry-platform": observations_with_streams[1],
        "codesign-verify": observations_with_streams[4],
        "codesign-display": observations_with_streams[5],
    }
    checked_bindings = {}
    for kind, item in source_rows.items():
        checked_bindings[kind] = validate_transcript_binding(bindings[kind], item[0], item[1], item[2])
    index_raw = observations_with_streams[0][1]; platform_raw = observations_with_streams[1][1]
    index = checked_bindings["registry-index"]["parsed"]
    platform = checked_bindings["registry-platform"]["parsed"]
    selected_platform = {
        name: checked_plan["selected_reference_rule"][name]
        for name in ("os", "architecture", "variant")
    }
    selected = [
        item for item in index["manifests"]
        if item["platform"] == selected_platform
    ]
    _require(len(selected) == 1, "readiness selected descriptor cardinality drift")
    selected_descriptor = selected[0]
    selected_projection = {"digest": selected_descriptor["digest"], "mediaType": selected_descriptor["mediaType"], "size": selected_descriptor["size"], **selected_descriptor["platform"]}
    _require(checked_result["selected_descriptor"] == selected_projection, "readiness selected descriptor projection drift")
    _require(
        sha256_hex(index_raw) == checked_result["index_sha256"] == INDEX_REFERENCE.rsplit(":", 1)[1]
        and sha256_hex(platform_raw) == checked_result["platform_sha256"] == selected_descriptor["digest"].split(":", 1)[1]
        and len(platform_raw) == selected_descriptor["size"],
        "readiness registry content binding drift",
    )
    local_raw = observations_with_streams[2][1]
    _require(local_raw.endswith(b"\n") and observations_with_streams[2][2] == b"", "readiness local inspect framing drift")
    local = strict_json_bytes(local_raw[:-1], MAX_RESULT_BYTES)
    _require(isinstance(local, dict), "readiness local inspect root drift")
    config = _fields(platform["config"], ("mediaType", "digest", "size"), "readiness platform config")
    local_rootfs = _fields(local.get("RootFS"), ("Type", "Layers"), "readiness local RootFS")
    _require(
        local.get("Id") == config["digest"] == checked_result["image_config_digest"]
        and (local.get("Os"), local.get("Architecture"), local.get("Variant")) == ("linux", "arm64", "v8")
        and local_rootfs == {"Type": "layers", "Layers": checked_result["rootfs_diff_ids"]},
        "readiness local image correspondence drift",
    )
    expected_buildx = b"github.com/docker/buildx v0.34.1-desktop.1 c79576280a671664e17eb68da98ec3136b614aed\n"
    _require(observations_with_streams[3][1] == expected_buildx and observations_with_streams[3][2] == b"", "Buildx version transcript drift")
    _require(checked_result["local_image_observation_sha256"] == observation_digest(observations[2]) and checked_result["buildx_version_observation_sha256"] == observation_digest(observations[3]) and checked_result["codesign_verify_observation_sha256"] == observation_digest(observations[4]) and checked_result["codesign_display_observation_sha256"] == observation_digest(observations[5]), "readiness named observation binding drift")
    _require(checked_result["context_sha256"] == context["sha256"], "readiness context digest drift")
    provenance = readiness_provenance
    if isinstance(provenance, list): provenance = {item.get("kind"): item for item in provenance if isinstance(item, dict)}
    _require(isinstance(provenance, dict) and set(provenance) == {"docker-desktop", "buildx"}, "readiness provenance census drift")
    desktop = validate_host_provenance(provenance["docker-desktop"], (observations[4], observations[5]))
    buildx = validate_host_provenance(provenance["buildx"], (observations[3],))
    _require(desktop["descriptor_set"] == desktop_set and buildx["descriptor_set"] == host_set, "readiness provenance descriptor-set drift")
    _require(desktop["facts"]["codesign_verify_sha256"] == observation_digest(observations[4]) and desktop["facts"]["codesign_display_sha256"] == observation_digest(observations[5]), "readiness signature provenance drift")
    _require(buildx["facts"]["buildx_version_stdout_sha256"] == sha256_hex(expected_buildx), "readiness Buildx provenance drift")
    return checked_result


def validate_probe_result(value: object, expected_mode: str) -> Mapping[str, object]:
    _require(isinstance(value, dict), "probe result must be an object")
    _require(value.get("schema") == SCHEMAS["probe_result"], "probe result schema drift")
    legacy = copy.deepcopy(value)
    runtime = value.get("runtime")
    if expected_mode != "oom-child":
        checked_runtime = _fields(runtime, tuple(_RUNTIME_FIELDS) + ("sys_version", "sysconfig_paths", "linker_version_argv", "linker_version_stdout_base64"), "v2 runtime")
        _ascii(checked_runtime["sys_version"], "sys version")
        _require(isinstance(checked_runtime["sysconfig_paths"], dict) and list(checked_runtime["sysconfig_paths"]) == sorted(checked_runtime["sysconfig_paths"]), "sysconfig paths drift")
        for key, item in checked_runtime["sysconfig_paths"].items():
            _ascii(key, "sysconfig key"); _path(item, "sysconfig path", absolute=True)
        _require(isinstance(checked_runtime["linker_version_argv"], list), "linker argv drift")
        _decode_b64(checked_runtime["linker_version_stdout_base64"], "linker version stdout")
        chain = checked_runtime["executable_chain"]
        _require(isinstance(chain, list) and chain, "v2 executable chain missing")
        for index, item in enumerate(chain):
            checked_item = _fields(item, tuple(_INVENTORY_FIELDS) + ("kind", "target_base64"), "v2 executable chain item")
            _require(checked_item["kind"] in ("regular", "symlink"), "v2 executable chain kind drift")
            if checked_item["kind"] == "regular":
                _require(checked_item["target_base64"] is None, "regular executable carries symlink target")
            else:
                _decode_b64(checked_item["target_base64"], "executable symlink target")
            del legacy["runtime"]["executable_chain"][index]["kind"]
            del legacy["runtime"]["executable_chain"][index]["target_base64"]
        for name in ("sys_version", "sysconfig_paths", "linker_version_argv", "linker_version_stdout_base64"):
            del legacy["runtime"][name]
    if expected_mode in ("normal", "oom-child"):
        security = value["security"]
        _fields(security, tuple(_SECURITY_FIELDS) + ("cgroup_base64", "oom_score_adj_base64"), "v2 security")
        cgroup_raw = _decode_b64(security["cgroup_base64"], "security cgroup")
        score_raw = _decode_b64(security["oom_score_adj_base64"], "security oom score")
        _require(cgroup_raw.endswith(b"\n") and score_raw == (str(security["oom_score_adj"]) + "\n").encode("ascii"), "security raw scalar drift")
        del legacy["security"]["cgroup_base64"]; del legacy["security"]["oom_score_adj_base64"]
        _fields(value["mounts"], tuple(_MOUNTS_FIELDS) + ("mountinfo_base64",), "v2 mounts")
        mountinfo = _decode_b64(value["mounts"]["mountinfo_base64"], "mountinfo")
        _require(sha256_hex(mountinfo) == value["mounts"]["mountinfo_sha256"], "mountinfo digest drift")
        del legacy["mounts"]["mountinfo_base64"]
        _fields(value["rlimits"], tuple(_RLIMIT_FIELDS) + ("proc_limits_base64",), "v2 rlimits")
        _decode_b64(value["rlimits"]["proc_limits_base64"], "proc limits")
        del legacy["rlimits"]["proc_limits_base64"]
        for phase in ("cgroup_pre", "cgroup_terminal"):
            snapshot = value[phase]
            _fields(snapshot, ("phase", "path", "observed_monotonic_ns", "files", "raw_files_base64"), phase)
            _nonnegative(snapshot["observed_monotonic_ns"], phase + " time")
            raw_map = snapshot["raw_files_base64"]
            _require(isinstance(raw_map, dict) and set(raw_map) == set(CGROUP_FILES), phase + " raw cgroup census drift")
            for raw in raw_map.values(): _decode_b64(raw, phase + " cgroup raw")
            # The v2 public form retains both parsed values and exact bytes.  The
            # legacy validator consumes the latter; passing parsed values into
            # its base64 parser made every complete v2 result impossible.
            legacy[phase]["files"] = dict(raw_map)
            del legacy[phase]["observed_monotonic_ns"]; del legacy[phase]["raw_files_base64"]
        _require(value["cgroup_pre"]["observed_monotonic_ns"] < value["cgroup_terminal"]["observed_monotonic_ns"], "cgroup observation order drift")
    if expected_mode == "oom-child":
        for process_name in ("parent", "child"):
            process = value[process_name]
            _fields(process, tuple(_PROCESS_FIELDS) + ("cgroup_base64", "oom_score_adj_base64", "namespaces"), process_name)
            _decode_b64(process["cgroup_base64"], process_name + " cgroup")
            score = _decode_b64(process["oom_score_adj_base64"], process_name + " oom score")
            _require(score == (str(process["oom_score_adj"]) + "\n").encode("ascii"), process_name + " score readback drift")
            namespaces = process["namespaces"]
            _require(isinstance(namespaces, dict) and set(namespaces) == {"pid", "uts", "mnt", "net", "ipc", "cgroup", "user"}, process_name + " namespace census drift")
            for key, item in namespaces.items(): _require(_NS_RE.fullmatch(item) is not None, process_name + " namespace drift")
            for name in ("cgroup_base64", "oom_score_adj_base64", "namespaces"): del legacy[process_name][name]
        extras = ("barrier_transcript_base64", "child_cgroup_read_monotonic_ns", "score_write_monotonic_ns", "score_readback_monotonic_ns", "child_ready_monotonic_ns", "release_monotonic_ns", "allocation_started_monotonic_ns", "child_wait_monotonic_ns", "raw_wait_status")
        workload = value["workload"]
        _fields(workload, tuple(_OOM_WORKLOAD_FIELDS) + extras, "v2 OOM workload")
        _require(_decode_b64(workload["barrier_transcript_base64"], "OOM barrier") == b"P01B_OOM_CHILD_READY\nP01B_OOM_CHILD_RELEASE\n", "OOM barrier transcript drift")
        times = [workload[name] for name in extras[1:8]]
        _require(all(_is_int(item) for item in times) and times[0] < times[1] < times[2] <= times[3] < times[4] < times[5] < times[6], "OOM timing drift")
        _require(_is_int(workload["raw_wait_status"]) and workload["raw_wait_status"] > 0, "OOM raw wait drift")
        for name in extras: del legacy["workload"][name]
    _validate_probe_result_a3l5(legacy, expected_mode)
    return value


def parse_probe_result(raw: bytes, expected_mode: str) -> Mapping[str, object]:
    return validate_probe_result(strict_json_bytes(raw, MAX_RESULT_BYTES), expected_mode)


def _dotted(value: Mapping[str, object], dotted: str) -> object:
    current: object = value
    for part in dotted.split("."):
        _require(isinstance(current, dict) and part in current, "inspect field missing: " + dotted)
        current = current[part]
    return current


_NETWORK_ENDPOINT_FIELDS = ("IPAMConfig", "Links", "Aliases", "MacAddress", "DriverOpts", "GwPriority", "NetworkID", "EndpointID", "Gateway", "IPAddress", "IPPrefixLen", "IPv6Gateway", "GlobalIPv6Address", "GlobalIPv6PrefixLen", "DNSNames")


def validate_inspect_evaluation(inspect: object, expected: object, state: str) -> Mapping[str, object]:
    _require(isinstance(inspect, dict) and isinstance(expected, dict), "inspect inputs must be objects")
    _require(set(expected) == set(INSPECT_FIELDS), "expected inspect field census drift")
    actual = {name: _dotted(inspect, name) for name in INSPECT_FIELDS}
    _require(actual == expected, "inspect value drift")
    networks = actual["NetworkSettings.Networks"]
    _require(isinstance(networks, dict) and set(networks) == {"none"}, "explicit none network missing")
    endpoint = _fields(networks["none"], _NETWORK_ENDPOINT_FIELDS, "none endpoint")
    for name in ("IPAMConfig", "Links", "Aliases", "DriverOpts", "DNSNames"):
        _require(endpoint[name] is None, "network null field drift")
    for name in ("MacAddress", "Gateway", "IPAddress", "IPv6Gateway", "GlobalIPv6Address", "EndpointID"):
        _require(endpoint[name] == "", "network empty field drift")
    for name in ("GwPriority", "IPPrefixLen", "GlobalIPv6PrefixLen"):
        _require(endpoint[name] == 0 and not isinstance(endpoint[name], bool), "network integer field drift")
    if state == "prestart":
        _require(endpoint["NetworkID"] == "", "prestart network id drift")
        _require((actual["State.Status"], actual["State.Running"], actual["State.ExitCode"], actual["State.OOMKilled"], actual["State.Error"], actual["State.Pid"]) == ("created", False, 0, False, "", 0), "prestart state drift")
    elif state == "terminal":
        _sha(endpoint["NetworkID"], "terminal network id")
        _require((actual["State.Status"], actual["State.Running"], actual["State.ExitCode"], actual["State.OOMKilled"], actual["State.Error"], actual["State.Pid"]) == ("exited", False, 0, False, "", 0), "terminal state drift")
        _require(actual["State.StartedAt"] < actual["State.FinishedAt"], "terminal time order drift")
    else:
        raise EvidenceError("unknown inspect state")
    return actual


MANIFEST_ENTRY_FIELDS = ("path", "file_type", "mode", "link_count", "bytes", "sha256")
MANIFEST_FIELDS = ("schema", "authorization_sha256", "implementation_commit", "entries")


def validate_candidate_manifest(value: object) -> Mapping[str, object]:
    manifest = _fields(value, MANIFEST_FIELDS, "candidate manifest")
    _require(manifest["schema"] == SCHEMAS["manifest"], "manifest schema drift")
    _sha(manifest["authorization_sha256"], "manifest authorization digest")
    _git(manifest["implementation_commit"], "manifest implementation commit")
    entries = manifest["entries"]
    _require(isinstance(entries, list) and len(entries) == 201, "manifest payload census drift")
    checked_paths = []
    total = 0
    for value_entry in entries:
        entry = _fields(value_entry, MANIFEST_ENTRY_FIELDS, "manifest entry")
        path = _path(entry["path"], "manifest path", absolute=False)
        checked_paths.append(path)
        _require(entry["file_type"] == "regular" and entry["mode"] == 0o600 and entry["link_count"] == 1, "manifest identity drift")
        total += _nonnegative(entry["bytes"], "manifest bytes")
        _sha(entry["sha256"], "manifest entry digest")
    _require(tuple(checked_paths) == CANDIDATE_PAYLOAD_PATHS, "manifest path grammar drift")
    _require(total <= 134_217_728, "candidate aggregate size exceeded")
    return manifest


def build_candidate_manifest(authorization_sha256: str, implementation_commit: str, entries: Sequence[Mapping[str, object]]) -> Dict[str, object]:
    value = {"schema": SCHEMAS["manifest"], "authorization_sha256": authorization_sha256, "implementation_commit": implementation_commit, "entries": [dict(item) for item in entries]}
    validate_candidate_manifest(value)
    return value


def manifest_digest(value: Mapping[str, object]) -> str:
    validate_candidate_manifest(value)
    return _digest("manifest", value)


def _coerce_object(value: object, label: str) -> Mapping[str, object]:
    if isinstance(value, bytes):
        value = strict_json_bytes(value)
    _require(isinstance(value, dict), label + " must be an object")
    return value


def validate_prepublication_candidate(files: object, manifest: object, expected_bindings: object) -> Mapping[str, object]:
    _require(isinstance(files, dict), "candidate files must be a byte map")
    _require(tuple(sorted(files)) == CANDIDATE_PAYLOAD_PATHS, "candidate file census drift")
    for path, raw in files.items():
        _path(path, "candidate file path", absolute=False)
        _require(isinstance(raw, bytes), "candidate payload must be bytes")
    manifest_object = _coerce_object(manifest, "candidate manifest")
    validate_candidate_manifest(manifest_object)
    bindings = validate_expected_bindings(_coerce_object(expected_bindings, "expected bindings"))
    expected_raw = files["authority/expected-bindings.json"]
    _require(expected_raw == canonical_json_bytes(bindings), "expected bindings bytes drift")
    _require(manifest_object["implementation_commit"] == bindings["implementation_commit"], "manifest implementation drift")
    for entry in manifest_object["entries"]:
        raw = files[entry["path"]]
        _require(len(raw) == entry["bytes"] and sha256_hex(raw) == entry["sha256"], "manifest payload mismatch: " + entry["path"])
        if (
            entry["path"].endswith(".json")
            and not entry["path"].startswith("snapshot/files/")
        ):
            limit = (
                MAX_A3L6_GATE_JSON_BYTES
                if entry["path"] == A3L6_GATE_BUNDLE_PATH
                else MAX_RESULT_BYTES
            )
            strict_json_bytes(raw, limit)
    return {"candidate_manifest_sha256": manifest_digest(manifest_object), "expected_bindings_sha256": expected_bindings_digest(bindings), "payload_count": 201}


_PUBLICATION_IDENTITY_FIELDS = ("device", "inode", "mode", "uid", "gid", "link_count")
PUBLICATION_FIELDS = ("schema", "candidate_manifest_sha256", "repository_state_sha256", "staging_path", "final_path", "parent_identity", "prepublication_inventory_sha256", "postpublication_inventory_sha256", "staging_identity", "final_identity", "ordered_file_reopens", "ordered_publication_events", "final_manifest_sha256")


def _publication_inventory(rows: Sequence[Mapping[str, object]], side: str) -> List[Dict[str, object]]:
    inventory = []
    for row in rows:
        nested = _fields(row[side], ("identity", "bytes", "sha256"), "publication reopen " + side)
        _identity(nested["identity"], "publication file identity")
        _nonnegative(nested["bytes"], "publication reopen bytes")
        _sha(nested["sha256"], "publication reopen digest")
        inventory.append({"path": row["path"], "identity": nested["identity"], "bytes": nested["bytes"], "sha256": nested["sha256"]})
    return inventory


def validate_publication_record(value: object) -> Mapping[str, object]:
    record = _fields(value, PUBLICATION_FIELDS, "publication record")
    _require(record["schema"] == SCHEMAS["publication"], "publication schema drift")
    for name in ("candidate_manifest_sha256", "repository_state_sha256", "prepublication_inventory_sha256", "postpublication_inventory_sha256", "final_manifest_sha256"):
        _sha(record[name], name.replace("_", " "))
    staging_path = _path(record["staging_path"], "staging path", absolute=True)
    final_path = _path(record["final_path"], "final path", absolute=True)
    staging_parent, staging_name = staging_path.rsplit("/", 1)
    final_parent, final_name = final_path.rsplit("/", 1)
    _require(
        staging_parent == final_parent and staging_name != final_name,
        "publication path relationship drift",
    )
    parent = _identity(record["parent_identity"], "parent identity")
    staging = _identity(record["staging_identity"], "staging identity")
    final = _identity(record["final_identity"], "final identity")
    _require(staging == final and record["final_manifest_sha256"] == record["candidate_manifest_sha256"], "publication final identity drift")
    rows = record["ordered_file_reopens"]
    _require(isinstance(rows, list) and len(rows) == 202, "publication reopen census drift")
    expected_paths = list(CANDIDATE_PAYLOAD_PATHS) + ["candidate-manifest.json"]
    expected_paths.sort()
    for row, path in zip(rows, expected_paths):
        _fields(row, ("path", "prepublication", "postpublication"), "publication reopen")
        _require(row["path"] == path and row["prepublication"] == row["postpublication"], "publication reopen mismatch")
    pre = _publication_inventory(rows, "prepublication"); post = _publication_inventory(rows, "postpublication")
    _require(pre == post, "publication inventory changed")
    _require(domain_sha256(DOMAINS["publication_inventory"], pre) == record["prepublication_inventory_sha256"] == record["postpublication_inventory_sha256"], "publication inventory digest drift")
    events = record["ordered_publication_events"]
    _require(isinstance(events, list) and len(events) == 271, "publication event census drift")
    event_fields = ("ordinal", "operation", "target", "flags", "started_monotonic_ns", "ended_monotonic_ns", "result", "errno", "identity", "sha256")
    for ordinal, event in enumerate(events):
        _fields(event, event_fields, "publication event")
        _ascii(event["operation"], "publication event operation")
        _require(
            isinstance(event["flags"], list)
            and all(isinstance(flag, str) for flag in event["flags"]),
            "publication event flags drift",
        )
        for flag in event["flags"]:
            _ascii(flag, "publication event flag")
        _require(
            event["ordinal"] == ordinal
            and _is_int(event["started_monotonic_ns"])
            and _is_int(event["ended_monotonic_ns"])
            and event["started_monotonic_ns"] >= 0
            and event["started_monotonic_ns"] < event["ended_monotonic_ns"]
            and _is_int(event["result"])
            and _is_int(event["errno"])
            and event["errno"] >= 0,
            "publication event ordering or outcome type drift",
        )
        if event["identity"] is not None:
            _identity(event["identity"], "publication event identity")
        if event["sha256"] is not None:
            _sha(event["sha256"], "publication event digest")
        if ordinal:
            _require(events[ordinal - 1]["ended_monotonic_ns"] <= event["started_monotonic_ns"], "publication events overlap")
    operations = [item["operation"] for item in events]
    _require(operations[:201] == ["payload-file-fsync"] * 201 and operations[201] == "candidate-manifest-fsync" and operations[202:264] == ["candidate-directory-fsync"] * 62, "publication fsync sequence drift")
    _require(operations[264:] == ["prepublication-inventory", "renameatx-np", "final-parent-fsync", "staging-absence", "final-root-reopen", "postpublication-inventory", "final-manifest-read"], "publication terminal sequence drift")
    reopen_by_path = {row["path"]: row for row in rows}
    for event, path in zip(events[:201], CANDIDATE_PAYLOAD_PATHS):
        observed = reopen_by_path[path]["prepublication"]
        _require(
            event["target"] == path
            and event["flags"] == []
            and event["result"] == event["errno"] == 0
            and event["identity"] == observed["identity"]
            and event["sha256"] == observed["sha256"],
            "payload publication event drift: " + path,
        )
    manifest_observed = reopen_by_path["candidate-manifest.json"]
    manifest_event = events[201]
    _require(
        manifest_event["target"] == "candidate-manifest.json"
        and manifest_event["flags"] == []
        and manifest_event["result"] == manifest_event["errno"] == 0
        and manifest_event["identity"] == manifest_observed["prepublication"]["identity"]
        and manifest_event["sha256"] == manifest_observed["prepublication"]["sha256"],
        "candidate manifest publication event drift",
    )
    directory_order = _candidate_directory_order()
    for event, target in zip(events[202:264], directory_order):
        identity = _identity(event["identity"], "publication directory identity")
        _require(
            event["target"] == target
            and event["flags"] == []
            and event["result"] == event["errno"] == 0
            and identity["mode"] == 0o700
            and identity["link_count"] >= 1
            and event["sha256"] is None,
            "candidate directory publication event drift: " + target,
        )
    _require(
        events[263]["identity"] == staging,
        "candidate root fsync identity drift",
    )
    terminal_expectations = (
        (264, ".", [], 0, 0, staging, record["prepublication_inventory_sha256"]),
        (
            265,
            {"source": staging_name, "destination": final_name},
            ["RENAME_EXCL"],
            0,
            0,
            None,
            None,
        ),
        (266, final_parent, [], 0, 0, parent, None),
        (267, staging_name, [], -1, 2, None, None),
        (268, final_name, [], 0, 0, final, None),
        (269, ".", [], 0, 0, final, record["postpublication_inventory_sha256"]),
        (
            270,
            "candidate-manifest.json",
            [],
            0,
            0,
            manifest_observed["postpublication"]["identity"],
            record["candidate_manifest_sha256"],
        ),
    )
    for ordinal, target, flags, result, error_number, identity, digest in terminal_expectations:
        event = events[ordinal]
        _require(
            event["target"] == target
            and event["flags"] == flags
            and event["result"] == result
            and event["errno"] == error_number
            and event["identity"] == identity
            and event["sha256"] == digest,
            "publication terminal event drift: " + str(ordinal),
        )
    return record


def publication_record_digest(value: Mapping[str, object]) -> str:
    validate_publication_record(value)
    return _digest("publication", value)


REPOSITORY_PLAN_FIELDS = ("schema", "git_path", "git_sha256", "protected_path", "environment", "cwd", "stdin_policy", "commands")
REPOSITORY_CAPTURE_FIELDS = ("schema", "ordered_commands", "protected_observation")
REPOSITORY_STATE_FIELDS = ("schema", "plan", "implementation_commit", "implementation_tree", "before", "after", "unchanged")


def _validate_repository_command(
    value: object, expected_role: str, plan: Mapping[str, object],
    expected_argv: Sequence[str],
) -> Mapping[str, object]:
    fields = ("role", "argv", "environment", "cwd", "stdin_policy", "executable_path", "executable_sha256", "timeout_ns", "stdout_cap_bytes", "stderr_cap_bytes", "started_monotonic_ns", "ended_monotonic_ns", "outcome", "exit_code", "signal", "stdout_total_bytes", "stdout_retained_bytes", "stdout_truncated", "stdout_base64", "stdout_sha256", "stderr_total_bytes", "stderr_retained_bytes", "stderr_truncated", "stderr_base64", "stderr_sha256")
    row = _fields(value, fields, "repository command")
    _require(
        row["role"] == expected_role
        and row["argv"] == list(expected_argv)
        and row["environment"] == plan["environment"]
        and row["cwd"] == plan["cwd"]
        and row["stdin_policy"] == plan["stdin_policy"]
        and row["executable_path"] == plan["git_path"]
        and row["executable_sha256"] == plan["git_sha256"],
        "repository command/plan drift",
    )
    _require(
        _is_int(row["started_monotonic_ns"])
        and _is_int(row["ended_monotonic_ns"])
        and row["started_monotonic_ns"] < row["ended_monotonic_ns"]
        and row["ended_monotonic_ns"] - row["started_monotonic_ns"]
        <= row["timeout_ns"],
        "repository command timing drift",
    )
    _require(
        row["outcome"] == "completed" and row["exit_code"] == 0
        and row["signal"] is None,
        "repository command outcome drift",
    )
    for prefix in ("stdout", "stderr"):
        raw = _decode_b64(row[prefix + "_base64"], prefix)
        _require(row[prefix + "_total_bytes"] == row[prefix + "_retained_bytes"] == len(raw) and row[prefix + "_truncated"] is False and row[prefix + "_sha256"] == sha256_hex(raw), "repository stream drift")
    _require(_decode_b64(row["stderr_base64"], "stderr") == b"", "repository stderr drift")
    return row


def validate_repository_state(value: object) -> Mapping[str, object]:
    state = _fields(value, REPOSITORY_STATE_FIELDS, "repository state")
    _require(state["schema"] == SCHEMAS["repository_state"], "repository state schema drift")
    plan = _fields(state["plan"], REPOSITORY_PLAN_FIELDS, "repository plan")
    _require(plan["schema"] == SCHEMAS["repository_state_plan"], "repository plan schema drift")
    _path(plan["git_path"], "Git path", absolute=True); _sha(plan["git_sha256"], "Git digest"); _path(plan["protected_path"], "protected path", absolute=True)
    expected_argv = ([plan["git_path"], "rev-parse", "HEAD"], [plan["git_path"], "rev-parse", "HEAD^{tree}"], [plan["git_path"], "status", "--porcelain=v2", "-z", "--untracked-files=all"])
    _require(isinstance(plan["commands"], list) and len(plan["commands"]) == 3, "repository plan command census drift")
    _require(
        isinstance(plan["environment"], dict)
        and isinstance(plan["cwd"], str)
        and plan["stdin_policy"] == "closed",
        "repository plan execution boundary drift",
    )
    _path(plan["cwd"], "repository cwd", absolute=True)
    for command, argv in zip(plan["commands"], expected_argv):
        _require(
            isinstance(command, dict) and set(command) == {"argv"}
            and command["argv"] == argv,
            "repository plan argv drift",
        )
    captures = []
    for side in ("before", "after"):
        capture = _fields(state[side], REPOSITORY_CAPTURE_FIELDS, side + " capture")
        _require(capture["schema"] == SCHEMAS["repository_capture"], "repository capture schema drift")
        _require(isinstance(capture["ordered_commands"], list) and len(capture["ordered_commands"]) == 3, "repository command census drift")
        commands = [
            _validate_repository_command(item, role, plan, argv)
            for item, role, argv in zip(
                capture["ordered_commands"], ("head", "tree", "status"),
                expected_argv,
            )
        ]
        _require(
            all(
                commands[index - 1]["ended_monotonic_ns"]
                <= commands[index]["started_monotonic_ns"]
                for index in range(1, len(commands))
            ),
            side + " repository commands overlap",
        )
        protected = validate_descriptor_observation(capture["protected_observation"])
        _require(
            protected["role"] == "protected"
            and protected["path"] == plan["protected_path"],
            side + " protected observation drift",
        )
        captures.append((commands, protected))
    _require(
        captures[0][0][-1]["ended_monotonic_ns"]
        <= captures[1][0][0]["started_monotonic_ns"],
        "repository captures overlap",
    )
    for before_command, after_command in zip(captures[0][0], captures[1][0]):
        for field in (
            "role", "argv", "environment", "cwd", "stdin_policy",
            "executable_path", "executable_sha256", "timeout_ns",
            "stdout_cap_bytes", "stderr_cap_bytes", "outcome", "exit_code",
            "signal", "stdout_total_bytes", "stdout_retained_bytes",
            "stdout_truncated", "stdout_base64", "stdout_sha256",
            "stderr_total_bytes", "stderr_retained_bytes", "stderr_truncated",
            "stderr_base64", "stderr_sha256",
        ):
            _require(
                before_command[field] == after_command[field],
                "repository capture changed: " + field,
            )
    _require(
        captures[0][1] == captures[1][1],
        "protected repository observation changed",
    )
    _require(state["unchanged"] is True, "repository unchanged flag drift")
    head = _decode_b64(captures[0][0][0]["stdout_base64"], "HEAD")
    tree = _decode_b64(captures[0][0][1]["stdout_base64"], "tree")
    _require(head == (state["implementation_commit"] + "\n").encode("ascii") and tree == (state["implementation_tree"] + "\n").encode("ascii"), "repository identity transcript drift")
    return state


def repository_state_digest(value: Mapping[str, object]) -> str:
    validate_repository_state(value)
    return _digest("repository_state", value)


DECISION_FIELDS = ("schema", "authorization_sha256", "implementation_commit", "candidate_manifest_sha256", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "class_results", "atomic_result", "evidence_level", "accepted_evidence_created", "level2_plus_created", "authority_granted")


def validate_decision(value: object) -> Mapping[str, object]:
    decision = _fields(value, DECISION_FIELDS, "decision")
    _require(decision["schema"] == SCHEMAS["decision"], "decision schema drift")
    for name in ("authorization_sha256", "candidate_manifest_sha256", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256"): _sha(decision[name], name.replace("_", " "))
    _git(decision["implementation_commit"], "decision implementation commit")
    rows = _class_results(decision["class_results"], "decision class results")
    expected = "accept" if all(item["closed"] for item in rows) else "reject"
    _require(decision["atomic_result"] == expected and decision["evidence_level"] == EVIDENCE_LEVEL, "decision atomic result drift")
    _false_authority(decision)
    return decision


def build_atomic_decision(authorization_sha256: str, implementation_commit: str, manifest_sha256: str, class_results: Mapping[str, bool], expected_bindings_sha256: Optional[str] = None, claim_boundary_sha256: Optional[str] = None, repository_state_sha256: Optional[str] = None, publication_record_sha256: Optional[str] = None) -> Dict[str, object]:
    _require(set(class_results) == set(CLASS_ORDER), "atomic decision class set drift")
    _require(all(isinstance(item, bool) for item in class_results.values()), "atomic class result type drift")
    value = {"schema": SCHEMAS["decision"], "authorization_sha256": authorization_sha256, "implementation_commit": implementation_commit, "candidate_manifest_sha256": manifest_sha256, "expected_bindings_sha256": expected_bindings_sha256, "claim_boundary_sha256": claim_boundary_sha256, "repository_state_sha256": repository_state_sha256, "publication_record_sha256": publication_record_sha256, "class_results": [{"class_id": name, "closed": class_results[name]} for name in CLASS_ORDER], "atomic_result": "accept" if all(class_results.values()) else "reject", "evidence_level": EVIDENCE_LEVEL, "accepted_evidence_created": False, "level2_plus_created": False, "authority_granted": False}
    for name in ("expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256"):
        _require(value[name] is not None, name + " required by decision v3")
    validate_decision(value)
    return value


def decision_digest(value: Mapping[str, object]) -> str:
    validate_decision(value)
    return _digest("decision", value)


def _findings(value: object, label: str) -> List[str]:
    _require(isinstance(value, list), label + " must be an array")
    for item in value:
        _require(isinstance(item, str) and 1 <= len(item.encode("ascii")) <= 512 and all(32 <= ord(ch) <= 126 for ch in item), "invalid " + label)
    _require(value == sorted(set(value)), label + " order/uniqueness drift")
    return value


REVIEW_FIELDS = ("schema", "role", "reviewer_id", "review_session_sha256", "review_session_durability_sha256", "candidate_manifest_sha256", "candidate_decision_sha256", "implementation_commit", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "validator_sha256", "collector_sha256", "fresh_validation_receipt_sha256", "reconstructed_class_results", "findings", "result")


def validate_review_record(value: object) -> Mapping[str, object]:
    review = _fields(value, REVIEW_FIELDS, "review record")
    _require(review["schema"] == SCHEMAS["review"] and review["role"] in REVIEW_ROLE_ORDER, "review schema/role drift")
    _ascii(review["reviewer_id"], "reviewer id")
    _require(len(review["reviewer_id"].encode("ascii")) <= 128, "reviewer id too long")
    for name in REVIEW_FIELDS:
        if name.endswith("_sha256"): _sha(review[name], name.replace("_", " "))
    _git(review["implementation_commit"], "review implementation commit")
    rows = _class_results(review["reconstructed_class_results"], "review classes")
    findings = _findings(review["findings"], "review findings")
    expected = "accept" if not findings and all(item["closed"] for item in rows) else "reject"
    _require(review["result"] == expected, "review result drift")
    return review


def review_record_digest(value: Mapping[str, object]) -> str:
    validate_review_record(value)
    return _digest("review", value)


def validate_review_session(value: object) -> Mapping[str, object]:
    fields = ("schema", "session_id", "challenge_hex", "candidate_manifest_sha256", "candidate_decision_sha256", "decision_file_identity", "decision_file_sha256", "created_monotonic_ns")
    session = _fields(value, fields, "review session")
    _require(session["schema"] == SCHEMAS["review_session"], "review session schema drift")
    _sha(session["session_id"], "session id"); _sha(session["challenge_hex"], "review challenge"); _sha(session["candidate_manifest_sha256"], "session manifest"); _sha(session["candidate_decision_sha256"], "session decision"); _sha(session["decision_file_sha256"], "decision file")
    _identity(session["decision_file_identity"], "decision file identity")
    _nonnegative(session["created_monotonic_ns"], "session time")
    raw_challenge = bytes.fromhex(session["challenge_hex"]); raw_decision = bytes.fromhex(session["candidate_decision_sha256"])
    expected = hashlib.sha256(b"hsai:p01b-review-session-id:v1\0" + raw_challenge + raw_decision).hexdigest()
    _require(session["session_id"] == expected, "review session id drift")
    return session


def review_session_digest(value: Mapping[str, object]) -> str:
    validate_review_session(value); return _digest("review_session", value)


def validate_review_session_durability(value: object) -> Mapping[str, object]:
    fields = ("schema", "review_session_sha256", "decision_file_identity", "review_root_path", "review_root_identity", "review_root_inventory_started_monotonic_ns", "review_root_inventory_ended_monotonic_ns", "review_root_inventory_before", "review_root_inventory_before_sha256", "session_path_absence_observation", "session_file_identity", "ordered_events", "durable_monotonic_ns")
    row = _fields(value, fields, "review session durability")
    _require(row["schema"] == SCHEMAS["review_session_durability"], "review durability schema drift")
    _sha(row["review_session_sha256"], "review session digest"); _sha(row["review_root_inventory_before_sha256"], "review inventory digest")
    _identity(row["decision_file_identity"], "decision identity"); root = _identity(row["review_root_identity"], "review root identity"); _identity(row["session_file_identity"], "session identity")
    _path(row["review_root_path"], "review root", absolute=True)
    inventory = row["review_root_inventory_before"]
    _require(isinstance(inventory, list) and 1 <= len(inventory) <= 10000, "review inventory census drift")
    _require(sha256_hex(canonical_json_bytes(inventory)) == row["review_root_inventory_before_sha256"], "review inventory digest drift")
    inventory_fields = ("path", "type", "mode", "device", "inode", "uid", "gid", "link_count")
    checked_inventory = [_fields(item, inventory_fields, "review inventory row") for item in inventory]
    paths = [item["path"] for item in checked_inventory]
    _require(paths[:1] == ["."] and paths[1:] == sorted(paths[1:], key=lambda item: item.encode("ascii")) and len(paths) == len(set(paths)), "review inventory path order drift")
    inventory_by_path = {item["path"]: item for item in checked_inventory}
    inode_pairs = []
    for item in checked_inventory:
        if item["path"] != ".":
            _path(item["path"], "review inventory path", absolute=False)
        _require(item["type"] in ("directory", "regular"), "review inventory type drift")
        for name in _PUBLICATION_IDENTITY_FIELDS:
            _nonnegative(item[name], "review inventory " + name)
        _require(
            item["mode"] == (0o700 if item["type"] == "directory" else 0o600),
            "review inventory mode drift",
        )
        if item["type"] == "regular":
            _require(item["link_count"] == 1, "review inventory hard link rejected")
        if item["path"] != ".":
            parent = item["path"].rsplit("/", 1)[0] if "/" in item["path"] else "."
            _require(
                parent in inventory_by_path
                and inventory_by_path[parent]["type"] == "directory",
                "review inventory parent drift",
            )
        inode_pairs.append((item["device"], item["inode"]))
    _require(len(inode_pairs) == len(set(inode_pairs)), "review inventory inode reuse")
    first = checked_inventory[0]
    _require(first["path"] == "." and first["type"] == "directory" and {name: first[name] for name in _PUBLICATION_IDENTITY_FIELDS} == root, "review root inventory drift")
    absence = _fields(row["session_path_absence_observation"], ("path", "parent_identity", "started_monotonic_ns", "ended_monotonic_ns", "result", "errno"), "session absence")
    _path(absence["path"], "session absence path", absolute=True)
    _require(absence["parent_identity"] == root and absence["result"] == -1 and absence["errno"] == 2, "session absence drift")
    _require(_is_int(row["review_root_inventory_started_monotonic_ns"]) and _is_int(row["review_root_inventory_ended_monotonic_ns"]) and row["review_root_inventory_started_monotonic_ns"] < row["review_root_inventory_ended_monotonic_ns"], "review inventory timing drift")
    _require(_is_int(absence["started_monotonic_ns"]) and _is_int(absence["ended_monotonic_ns"]) and absence["started_monotonic_ns"] < absence["ended_monotonic_ns"], "session absence timing drift")
    events = row["ordered_events"]
    event_fields = ("ordinal", "operation", "target", "started_monotonic_ns", "ended_monotonic_ns", "result", "errno", "identity", "sha256")
    _require(isinstance(events, list) and len(events) == 4, "session event census drift")
    checked_events = [_fields(item, event_fields, "review durability event") for item in events]
    _require([item["ordinal"] for item in checked_events] == list(range(4)) and [item["operation"] for item in checked_events] == ["decision-reopen", "review-session-path-absence", "review-session-file-fsync", "review-session-parent-fsync"], "session event sequence drift")
    for index, event in enumerate(checked_events):
        _path(event["target"], "review durability event target", absolute=True)
        _require(_is_int(event["started_monotonic_ns"]) and _is_int(event["ended_monotonic_ns"]) and event["started_monotonic_ns"] < event["ended_monotonic_ns"], "review durability event timing drift")
        if index:
            _require(checked_events[index - 1]["ended_monotonic_ns"] <= event["started_monotonic_ns"], "review durability events overlap")
    _require(row["review_root_inventory_ended_monotonic_ns"] <= checked_events[0]["started_monotonic_ns"], "review inventory/event timing drift")
    _require(checked_events[1]["target"] == absence["path"] and checked_events[1]["started_monotonic_ns"] == absence["started_monotonic_ns"] and checked_events[1]["ended_monotonic_ns"] == absence["ended_monotonic_ns"] and checked_events[1]["result"] == absence["result"] == -1 and checked_events[1]["errno"] == absence["errno"] == 2, "session absence event projection drift")
    _require(checked_events[0]["result"] == checked_events[0]["errno"] == 0 and checked_events[2]["result"] == checked_events[2]["errno"] == 0 and checked_events[3]["result"] == checked_events[3]["errno"] == 0, "review durability event outcome drift")
    _require(checked_events[0]["identity"] is not None and checked_events[0]["sha256"] is not None and checked_events[1]["identity"] is None and checked_events[1]["sha256"] is None and checked_events[2]["identity"] is not None and checked_events[2]["sha256"] is not None and checked_events[3]["identity"] is not None and checked_events[3]["sha256"] is None, "review durability event identity/digest nullability drift")
    for index in (0, 2, 3):
        _identity(checked_events[index]["identity"], "review durability event identity")
    for index in (0, 2):
        _sha(checked_events[index]["sha256"], "review durability event digest")
    _require(events[-1]["ended_monotonic_ns"] == row["durable_monotonic_ns"], "session durability time drift")
    return row


def review_session_durability_digest(value: Mapping[str, object]) -> str:
    validate_review_session_durability(value); return _digest("review_session_durability", value)


def _reopened_canonical_object(
    raw: object, value: object, label: str,
) -> Mapping[str, object]:
    _require(isinstance(raw, bytes), label + " reopened bytes must be bytes")
    parsed = strict_json_bytes(raw)
    _require(parsed == value, label + " reopened object drift")
    return parsed


def validate_review_session_graph(
    review_session: object,
    review_session_raw: bytes,
    review_session_durability: object,
    review_session_durability_raw: bytes,
    candidate_decision: object,
    candidate_decision_raw: bytes,
    decision_file_identity: object,
    expected_candidate_manifest_sha256: str,
    expected_decision_path: str,
    expected_review_root_path: str,
    expected_review_session_path: str,
    expected_review_session_durability_path: str,
) -> Mapping[str, object]:
    """Validate the reopened decision -> session -> durability graph."""
    session = validate_review_session(
        _reopened_canonical_object(review_session_raw, review_session, "review session")
    )
    durability = validate_review_session_durability(
        _reopened_canonical_object(
            review_session_durability_raw,
            review_session_durability,
            "review session durability",
        )
    )
    decision = validate_decision(
        _reopened_canonical_object(
            candidate_decision_raw, candidate_decision, "candidate decision"
        )
    )
    identity = _identity(decision_file_identity, "reopened decision identity")
    _sha(expected_candidate_manifest_sha256, "expected candidate manifest digest")
    for label, path in (
        ("expected decision path", expected_decision_path),
        ("expected review root", expected_review_root_path),
        ("expected review session path", expected_review_session_path),
        ("expected review durability path", expected_review_session_durability_path),
    ):
        _path(path, label, absolute=True)
    expected_session_directory = expected_review_root_path + "/" + session["session_id"]
    _require(
        expected_review_root_path.endswith(
            "/reviews/" + expected_candidate_manifest_sha256
        )
        and expected_decision_path.endswith(
            "/decision/" + expected_candidate_manifest_sha256
            + "/candidate-decision.json"
        )
        and expected_review_session_path
        == expected_session_directory + "/review-session.json"
        and expected_review_session_durability_path
        == expected_session_directory + "/review-session-durability.json",
        "review session canonical layout drift",
    )
    _require(
        session["candidate_manifest_sha256"]
        == decision["candidate_manifest_sha256"]
        == expected_candidate_manifest_sha256,
        "review session manifest binding drift",
    )
    _require(
        session["candidate_decision_sha256"] == decision_digest(decision),
        "review session decision domain binding drift",
    )
    _require(
        session["decision_file_sha256"] == sha256_hex(candidate_decision_raw),
        "review session decision raw-file binding drift",
    )
    _require(
        session["decision_file_identity"]
        == durability["decision_file_identity"]
        == identity,
        "review session decision identity binding drift",
    )
    session_sha = review_session_digest(session)
    _require(
        durability["review_session_sha256"] == session_sha,
        "durability session domain binding drift",
    )
    _require(
        durability["review_root_path"] == expected_review_root_path,
        "durability review root path drift",
    )
    inventory_paths = [
        item["path"] for item in durability["review_root_inventory_before"]
    ]
    _require(
        session["session_id"] not in inventory_paths
        and not any(
            path.startswith(session["session_id"] + "/")
            for path in inventory_paths
        ),
        "review session preexisted in retained inventory",
    )
    absence = durability["session_path_absence_observation"]
    events = durability["ordered_events"]
    session_raw_sha256 = sha256_hex(review_session_raw)
    _require(
        absence["path"] == expected_session_directory
        and events[0]["target"] == expected_decision_path
        and events[0]["identity"] == identity
        and events[0]["sha256"] == session["decision_file_sha256"]
        and events[1]["target"] == expected_session_directory
        and events[2]["target"] == expected_review_session_path
        and events[2]["identity"] == durability["session_file_identity"]
        and events[2]["sha256"] == session_raw_sha256
        and events[3]["target"] == expected_session_directory,
        "review durability target/identity/digest graph drift",
    )
    parent_identity = _identity(
        events[3]["identity"], "review session directory identity"
    )
    root_identity = durability["review_root_identity"]
    _require(
        parent_identity["mode"] == 0o700
        and parent_identity["device"] == root_identity["device"]
        and parent_identity["uid"] == root_identity["uid"]
        and parent_identity["gid"] == root_identity["gid"],
        "review session directory identity drift",
    )
    _require(
        durability["review_root_inventory_started_monotonic_ns"]
        < durability["review_root_inventory_ended_monotonic_ns"]
        <= events[0]["started_monotonic_ns"]
        < events[0]["ended_monotonic_ns"]
        <= absence["started_monotonic_ns"]
        < absence["ended_monotonic_ns"]
        <= session["created_monotonic_ns"]
        < events[2]["started_monotonic_ns"]
        < events[2]["ended_monotonic_ns"]
        <= events[3]["started_monotonic_ns"]
        < events[3]["ended_monotonic_ns"]
        == durability["durable_monotonic_ns"],
        "review session durability timeline drift",
    )
    return {
        "candidate_decision_sha256": decision_digest(decision),
        "decision_file_sha256": sha256_hex(candidate_decision_raw),
        "review_session_sha256": session_sha,
        "review_session_durability_sha256": review_session_durability_digest(
            durability
        ),
        "review_session_raw_sha256": session_raw_sha256,
        "review_session_durability_raw_sha256": sha256_hex(
            review_session_durability_raw
        ),
        "review_root_path": expected_review_root_path,
        "review_session_path": expected_review_session_path,
        "review_session_durability_path": expected_review_session_durability_path,
    }


FRESH_INPUT_DIGEST_FIELDS = ("review_session_sha256", "review_session_durability_sha256", "authorization_sha256", "candidate_manifest_sha256", "candidate_decision_sha256", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "a3l6_gate_bundle_sha256", "validator_sha256", "collector_sha256")
FRESH_VALIDATION_FIELDS = ("schema", "role", "reviewer_id", "review_session_sha256", "review_session_durability_sha256", "process_id", "python_path", "python_sha256", "python_version", "argv", "environment", "cwd", "stdin_policy", "python_descriptor_observation", "snapshot_copy_manifest_sha256", "validator_path", "validator_sha256", "collector_path", "collector_sha256", "started_monotonic_ns", "ended_monotonic_ns", "input_digests", "reconstructed_class_results", "result")
REVIEW_ENVIRONMENT = {"HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
A3L9_DESCRIPTOR_BOOTSTRAP = "exec(" + repr("""import hashlib,os,stat,sys
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


def validate_fresh_validation_receipt(value: object) -> Mapping[str, object]:
    row = _fields(value, FRESH_VALIDATION_FIELDS, "fresh validation receipt")
    _require(row["schema"] == SCHEMAS["fresh_validation"] and row["role"] in REVIEW_ROLE_ORDER, "fresh validation schema/role drift")
    _ascii(row["reviewer_id"], "receipt reviewer"); _require(len(row["reviewer_id"].encode("ascii")) <= 128, "receipt reviewer too long"); _require(_is_int(row["process_id"]) and row["process_id"] > 0, "receipt process id drift")
    _require(row["python_path"] == "/usr/bin/python3" and row["python_sha256"] == NATIVE_PYTHON_SHA256 and row["python_version"] == "3.9.6", "receipt Python identity drift")
    descriptor = validate_descriptor_observation(row["python_descriptor_observation"])
    _require(descriptor["role"] == "review-python" and descriptor["path"] == row["python_path"] and descriptor["relative_path"] is None and descriptor["sha256"] == row["python_sha256"], "receipt Python descriptor drift")
    _require(isinstance(row["argv"], list) and len(row["argv"]) >= 9 and row["argv"][:5] == ["/usr/bin/python3", "-I", "-B", "-c", A3L9_DESCRIPTOR_BOOTSTRAP] and isinstance(row["argv"][5], str) and row["argv"][5].isdecimal() and all(isinstance(item, str) for item in row["argv"]), "receipt argv boundary drift")
    _require(row["environment"] == REVIEW_ENVIRONMENT and row["cwd"] == "/" and row["stdin_policy"] == "closed" and _is_int(row["started_monotonic_ns"]) and _is_int(row["ended_monotonic_ns"]) and row["started_monotonic_ns"] < row["ended_monotonic_ns"], "receipt execution bounds drift")
    _sha(row["snapshot_copy_manifest_sha256"], "snapshot copy manifest digest")
    for name in ("validator_path", "collector_path"):
        _path(row[name], name.replace("_", " "), absolute=True)
    _sha(row["validator_sha256"], "validator digest"); _sha(row["collector_sha256"], "collector digest")
    _require(row["argv"][6] == row["collector_sha256"] and row["argv"][7] == row["collector_path"], "receipt descriptor collector binding drift")
    digests = _fields(row["input_digests"], FRESH_INPUT_DIGEST_FIELDS, "fresh input digests")
    for name, item in digests.items(): _sha(item, name.replace("_", " "))
    for name in ("review_session_sha256", "review_session_durability_sha256", "validator_sha256", "collector_sha256"):
        _require(row[name] == digests[name], "fresh receipt input binding drift")
    rows = _class_results(row["reconstructed_class_results"], "fresh receipt classes")
    _require(row["result"] == ("accept" if all(item["closed"] for item in rows) else "reject"), "fresh receipt result drift")
    return row


def fresh_validation_receipt_digest(value: Mapping[str, object]) -> str:
    validate_fresh_validation_receipt(value); return _digest("fresh_validation", value)


def validate_review_launch(value: object) -> Mapping[str, object]:
    fields = ("schema", "review_session_sha256", "review_session_durability_sha256", "claim_boundary_sha256", "role", "reviewer_id", "command_observation", "receipt_path", "receipt_bytes", "receipt_sha256", "receipt_domain_sha256", "review_path", "review_bytes", "review_sha256", "review_domain_sha256")
    row = _fields(value, fields, "review launch")
    _require(row["schema"] == SCHEMAS["review_launch"] and row["role"] in REVIEW_ROLE_ORDER, "review launch schema/role drift")
    _ascii(row["reviewer_id"], "launch reviewer")
    _require(len(row["reviewer_id"].encode("ascii")) <= 128, "launch reviewer too long")
    for name in ("review_session_sha256", "review_session_durability_sha256", "claim_boundary_sha256", "receipt_sha256", "receipt_domain_sha256", "review_sha256", "review_domain_sha256"): _sha(row[name], name.replace("_", " "))
    _path(row["receipt_path"], "receipt path", absolute=True); _path(row["review_path"], "review path", absolute=True)
    _require(row["receipt_path"] != row["review_path"] and _is_int(row["receipt_bytes"]) and row["receipt_bytes"] > 0 and _is_int(row["review_bytes"]) and row["review_bytes"] > 0, "review launch output drift")
    observation = row["command_observation"]
    _require(isinstance(observation, dict) and observation.get("exit_code") == 0 and observation.get("signal") is None and observation.get("stdout_cap_bytes") == observation.get("stderr_cap_bytes") == 16384, "review launch observation drift")
    return row


def review_launch_digest(value: Mapping[str, object]) -> str:
    validate_review_launch(value); return _digest("review_launch", value)


REVIEW_PATH_FIELDS = (
    "snapshot_root", "candidate_root", "publication_record",
    "repository_state", "candidate_decision", "expected_bindings",
    "review_session", "review_session_durability", "receipt_output",
    "review_output",
)


def _expected_review_argv(
    receipt: Mapping[str, object], expected_paths: Mapping[str, object],
    implementation_commit: str,
) -> List[str]:
    paths = _fields(expected_paths, REVIEW_PATH_FIELDS, "review graph paths")
    for name, path in paths.items():
        _path(path, "review graph " + name.replace("_", " "), absolute=True)
    collector_path = paths["snapshot_root"] + "/tools/hsai-formal-preflight/p01b_container_execution.py"
    receipt_argv = receipt.get("argv")
    descriptor_fd = (
        receipt_argv[5]
        if isinstance(receipt_argv, list) and len(receipt_argv) > 5
        and isinstance(receipt_argv[5], str) and receipt_argv[5].isdecimal()
        else "9"
    )
    return [
        "/usr/bin/python3", "-I", "-B", "-c", A3L9_DESCRIPTOR_BOOTSTRAP,
        descriptor_fd, receipt["collector_sha256"], collector_path, "review-v2",
        "--candidate-root", paths["candidate_root"],
        "--collector-logical-path", collector_path,
        "--publication-record", paths["publication_record"],
        "--repository-state", paths["repository_state"],
        "--candidate-decision", paths["candidate_decision"],
        "--expected-bindings", paths["expected_bindings"],
        "--review-session", paths["review_session"],
        "--review-session-durability", paths["review_session_durability"],
        "--role", receipt["role"],
        "--reviewer-id", receipt["reviewer_id"],
        "--implementation-commit", implementation_commit,
        "--receipt-output", paths["receipt_output"],
        "--review-output", paths["review_output"],
    ]


def _validate_review_command_observation(
    value: object, expected_argv: Sequence[str], receipt: Mapping[str, object],
    durable_monotonic_ns: int,
) -> Mapping[str, object]:
    row = _fields(value, GATE_CAPTURE_FIELDS, "review launch command observation")
    _require(
        row["role"] == "review-v2" and row["argv"] == list(expected_argv),
        "review launch argv drift",
    )
    _require(
        row["environment"] == REVIEW_ENVIRONMENT and row["cwd"] == "/"
        and row["stdin_policy"] == "closed"
        and row["executable_path"] == "/usr/bin/python3"
        and row["executable_sha256"] == NATIVE_PYTHON_SHA256,
        "review launch execution context drift",
    )
    _require(
        _is_int(row["timeout_ns"]) and row["timeout_ns"] > 0
        and row["stdout_cap_bytes"] == row["stderr_cap_bytes"] == 16_384,
        "review launch bounds drift",
    )
    _require(
        _is_int(row["started_monotonic_ns"])
        and _is_int(row["ended_monotonic_ns"])
        and durable_monotonic_ns < row["started_monotonic_ns"]
        <= receipt["started_monotonic_ns"]
        < receipt["ended_monotonic_ns"]
        < row["ended_monotonic_ns"]
        and row["ended_monotonic_ns"] - row["started_monotonic_ns"]
        <= row["timeout_ns"],
        "review launch/receipt timing drift",
    )
    _require(
        row["outcome"] == "completed" and row["exit_code"] == 0
        and row["signal"] is None,
        "review launch process outcome drift",
    )
    _require(
        _validate_gate_stream(row, "stdout") == b""
        and _validate_gate_stream(row, "stderr") == b"",
        "review launch retained stream drift",
    )
    return row


def validate_fresh_review_graph(
    receipt: object,
    receipt_raw: bytes,
    review: object,
    review_raw: bytes,
    launch: object,
    *,
    review_session: object,
    review_session_durability: object,
    authorization: object,
    candidate_manifest: object,
    candidate_decision: object,
    expected_bindings: object,
    repository_state: object,
    publication_record: object,
    a3l6_gate_bundle: object,
    snapshot_copy_manifest: object,
    candidate_files: object,
    reconstructed_class_results: object,
    expected_argv: Sequence[str],
    expected_paths: Mapping[str, object],
) -> Mapping[str, object]:
    """Validate one independently launched fresh receipt/review pair."""
    receipt_row = validate_fresh_validation_receipt(
        _reopened_canonical_object(receipt_raw, receipt, "fresh validation receipt")
    )
    review_row = validate_review_record(
        _reopened_canonical_object(review_raw, review, "review record")
    )
    launch_row = validate_review_launch(launch)
    session = validate_review_session(review_session)
    durability = validate_review_session_durability(review_session_durability)
    authorization_row = validate_authorization(authorization)
    manifest = validate_candidate_manifest(candidate_manifest)
    decision = validate_decision(candidate_decision)
    bindings = validate_expected_bindings(expected_bindings)
    repository = validate_repository_state(repository_state)
    publication = validate_publication_record(publication_record)
    gate = validate_a3l6_gate_bundle(a3l6_gate_bundle, bindings)
    copied = validate_snapshot_copy_manifest(snapshot_copy_manifest)
    rows = _class_results(reconstructed_class_results, "fresh reconstructed classes")
    paths = _fields(expected_paths, REVIEW_PATH_FIELDS, "review graph paths")
    expected = _expected_review_argv(
        receipt_row, paths, manifest["implementation_commit"]
    )
    _require(list(expected_argv) == expected, "caller review argv drift")
    _require(receipt_row["argv"] == expected, "receipt review argv drift")
    fresh_rows = reconstruct_published_candidate(
        candidate_files, manifest, publication, repository, bindings
    )
    _require(rows == fresh_rows, "fresh candidate reconstruction drift")
    expected_session_directory = paths["review_session"].rsplit("/", 1)[0]
    _require(
        paths["candidate_root"] == publication["final_path"]
        and paths["publication_record"].endswith(
            "/publication/" + manifest_digest(manifest) + "/publication-record.json"
        )
        and paths["repository_state"].endswith(
            "/publication/" + manifest_digest(manifest) + "/repository-state.json"
        )
        and paths["candidate_decision"].endswith(
            "/decision/" + manifest_digest(manifest) + "/candidate-decision.json"
        )
        and paths["expected_bindings"]
        == paths["candidate_root"] + "/authority/expected-bindings.json"
        and paths["review_session"]
        == expected_session_directory + "/review-session.json"
        and paths["review_session_durability"]
        == expected_session_directory + "/review-session-durability.json"
        and paths["receipt_output"]
        == expected_session_directory + "/" + receipt_row["role"]
        + "/fresh-validation-receipt.json"
        and paths["review_output"]
        == expected_session_directory + "/" + receipt_row["role"] + "/review.json",
        "fresh review canonical path graph drift",
    )
    copy_sha = snapshot_copy_manifest_digest(copied)
    copy_entries = {item["path"]: item for item in copied["ordered_entries"]}
    validator_relative = "tools/hsai-formal-preflight/p01b_container_evidence.py"
    collector_relative = "tools/hsai-formal-preflight/p01b_container_execution.py"
    validator_path = paths["snapshot_root"] + "/" + validator_relative
    collector_path = paths["snapshot_root"] + "/" + collector_relative
    common = {
        "review_session_sha256": review_session_digest(session),
        "review_session_durability_sha256": review_session_durability_digest(durability),
        "authorization_sha256": authorization_digest(authorization_row),
        "candidate_manifest_sha256": manifest_digest(manifest),
        "candidate_decision_sha256": decision_digest(decision),
        "expected_bindings_sha256": expected_bindings_digest(bindings),
        "claim_boundary_sha256": claim_boundary_digest(bindings["claim_boundary"]),
        "repository_state_sha256": repository_state_digest(repository),
        "publication_record_sha256": publication_record_digest(publication),
        "a3l6_gate_bundle_sha256": a3l6_gate_bundle_digest(gate),
        "validator_sha256": copy_entries[validator_relative]["sha256"],
        "collector_sha256": copy_entries[collector_relative]["sha256"],
    }
    _require(
        receipt_row["input_digests"] == common,
        "fresh receipt complete input digest graph drift",
    )
    _require(
        receipt_row["snapshot_copy_manifest_sha256"]
        == copy_sha == bindings["snapshot_copy_manifest_sha256"]
        and receipt_row["validator_path"] == validator_path
        and receipt_row["collector_path"] == collector_path
        and receipt_row["validator_sha256"]
        == review_row["validator_sha256"]
        == bindings["validator_sha256"]
        == common["validator_sha256"]
        and receipt_row["collector_sha256"]
        == review_row["collector_sha256"]
        == bindings["collector_sha256"]
        == common["collector_sha256"],
        "fresh review immutable tool/snapshot binding drift",
    )
    _require(
        receipt_row["review_session_sha256"] == common["review_session_sha256"]
        and receipt_row["review_session_durability_sha256"]
        == common["review_session_durability_sha256"],
        "fresh receipt session binding drift",
    )
    review_common = (
        "review_session_sha256", "review_session_durability_sha256",
        "candidate_manifest_sha256", "candidate_decision_sha256",
        "expected_bindings_sha256", "claim_boundary_sha256",
        "repository_state_sha256", "publication_record_sha256",
        "validator_sha256", "collector_sha256",
    )
    _require(
        all(review_row[name] == common[name] for name in review_common)
        and review_row["implementation_commit"] == manifest["implementation_commit"]
        == decision["implementation_commit"] == bindings["implementation_commit"]
        and manifest["authorization_sha256"] == common["authorization_sha256"]
        and publication["candidate_manifest_sha256"] == common["candidate_manifest_sha256"]
        and publication["repository_state_sha256"] == common["repository_state_sha256"],
        "fresh review common input graph drift",
    )
    _require(
        receipt_row["role"] == review_row["role"] == launch_row["role"]
        and receipt_row["reviewer_id"] == review_row["reviewer_id"]
        == launch_row["reviewer_id"],
        "fresh review role/reviewer graph drift",
    )
    _require(
        launch_row["review_session_sha256"] == common["review_session_sha256"]
        and launch_row["review_session_durability_sha256"]
        == common["review_session_durability_sha256"]
        and launch_row["claim_boundary_sha256"] == common["claim_boundary_sha256"]
        and launch_row["receipt_path"] == paths["receipt_output"]
        and launch_row["review_path"] == paths["review_output"],
        "fresh review launch common/path drift",
    )
    _validate_review_command_observation(
        launch_row["command_observation"], expected, receipt_row,
        durability["durable_monotonic_ns"],
    )
    receipt_domain = fresh_validation_receipt_digest(receipt_row)
    review_domain = review_record_digest(review_row)
    _require(
        launch_row["receipt_bytes"] == len(receipt_raw)
        and launch_row["receipt_sha256"] == sha256_hex(receipt_raw)
        and launch_row["receipt_domain_sha256"] == receipt_domain
        and launch_row["review_bytes"] == len(review_raw)
        and launch_row["review_sha256"] == sha256_hex(review_raw)
        and launch_row["review_domain_sha256"] == review_domain
        and review_row["fresh_validation_receipt_sha256"] == receipt_domain,
        "fresh review reopened output binding drift",
    )
    _require(
        receipt_row["reconstructed_class_results"]
        == review_row["reconstructed_class_results"]
        == decision["class_results"] == rows,
        "fresh review reconstructed class graph drift",
    )
    return {
        "role": receipt_row["role"],
        "reviewer_id": receipt_row["reviewer_id"],
        "process_id": receipt_row["process_id"],
        "fresh_validation_receipt_sha256": receipt_domain,
        "review_sha256": review_domain,
        "review_launch_sha256": review_launch_digest(launch_row),
        "result": "accept" if receipt_row["result"] == review_row["result"] == "accept" else "reject",
    }


AGGREGATE_FIELDS = ("schema", "review_session_sha256", "review_session_durability_sha256", "candidate_manifest_sha256", "candidate_decision_sha256", "implementation_commit", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "validator_sha256", "collector_sha256", "ordered_fresh_validation_receipt_sha256", "ordered_review_sha256", "ordered_review_launch_sha256", "reconstructed_class_results", "atomic_result")


def validate_review_aggregate(value: object) -> Mapping[str, object]:
    row = _fields(value, AGGREGATE_FIELDS, "review aggregate")
    _require(row["schema"] == SCHEMAS["review_aggregate"], "aggregate schema drift")
    for name in AGGREGATE_FIELDS:
        if name.endswith("_sha256") and not name.startswith("ordered_"): _sha(row[name], name.replace("_", " "))
    _git(row["implementation_commit"], "aggregate implementation commit")
    for name in ("ordered_fresh_validation_receipt_sha256", "ordered_review_sha256", "ordered_review_launch_sha256"):
        _require(isinstance(row[name], list) and len(row[name]) == 2, name + " census drift")
        for digest in row[name]: _sha(digest, name)
    rows = _class_results(row["reconstructed_class_results"], "aggregate classes")
    _require(row["atomic_result"] in ("accept", "reject"), "aggregate atomic result drift")
    if not all(item["closed"] for item in rows):
        _require(row["atomic_result"] == "reject", "open aggregate class accepted")
    return row


def build_review_aggregate(reviews: Sequence[Mapping[str, object]], receipts: Optional[Sequence[Mapping[str, object]]] = None, launches: Optional[Sequence[Mapping[str, object]]] = None) -> Dict[str, object]:
    _require(receipts is not None and launches is not None, "aggregate v2 requires receipts and launches")
    _require(len(reviews) == len(receipts) == len(launches) == 2, "aggregate pair census drift")
    checked_reviews = [validate_review_record(item) for item in reviews]
    checked_receipts = [validate_fresh_validation_receipt(item) for item in receipts]
    checked_launches = [validate_review_launch(item) for item in launches]
    _require(tuple(item["role"] for item in checked_reviews) == REVIEW_ROLE_ORDER and tuple(item["role"] for item in checked_receipts) == REVIEW_ROLE_ORDER and tuple(item["role"] for item in checked_launches) == REVIEW_ROLE_ORDER, "aggregate role order drift")
    _require(checked_reviews[0]["reviewer_id"] != checked_reviews[1]["reviewer_id"], "reviewers are not distinct")
    _require(checked_receipts[0]["process_id"] != checked_receipts[1]["process_id"], "review processes are not distinct")
    first = checked_reviews[0]
    common = ("review_session_sha256", "review_session_durability_sha256", "candidate_manifest_sha256", "candidate_decision_sha256", "implementation_commit", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "validator_sha256", "collector_sha256")
    for review in checked_reviews[1:]: _require(all(review[name] == first[name] for name in common), "aggregate common input drift")
    rows = first["reconstructed_class_results"]
    for review, receipt, launch in zip(checked_reviews, checked_receipts, checked_launches):
        _require(review["reviewer_id"] == receipt["reviewer_id"] == launch["reviewer_id"] and review["role"] == receipt["role"] == launch["role"], "review pair identity drift")
        _require(review["fresh_validation_receipt_sha256"] == fresh_validation_receipt_digest(receipt), "review receipt digest drift")
        _require(review["reconstructed_class_results"] == receipt["reconstructed_class_results"] == rows, "review class correspondence drift")
        _require(launch["receipt_domain_sha256"] == fresh_validation_receipt_digest(receipt) and launch["review_domain_sha256"] == review_record_digest(review), "launch pair digest drift")
        _require(launch["review_session_sha256"] == review["review_session_sha256"] and launch["review_session_durability_sha256"] == review["review_session_durability_sha256"] and launch["claim_boundary_sha256"] == review["claim_boundary_sha256"], "launch common input drift")
        for name in ("review_session_sha256", "review_session_durability_sha256", "candidate_manifest_sha256", "candidate_decision_sha256", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "validator_sha256", "collector_sha256"):
            _require(receipt["input_digests"][name] == review[name], "receipt/review input digest drift: " + name)
    _require(checked_receipts[0]["input_digests"] == checked_receipts[1]["input_digests"], "review receipt common input drift")
    value = {"schema": SCHEMAS["review_aggregate"], **{name: first[name] for name in common}, "ordered_fresh_validation_receipt_sha256": [fresh_validation_receipt_digest(item) for item in checked_receipts], "ordered_review_sha256": [review_record_digest(item) for item in checked_reviews], "ordered_review_launch_sha256": [review_launch_digest(item) for item in checked_launches], "reconstructed_class_results": rows, "atomic_result": "accept" if all(item["result"] == "accept" for item in checked_reviews) and all(item["result"] == "accept" for item in checked_receipts) else "reject"}
    validate_review_aggregate(value); return value


def reconstruct_review_aggregate(
    reviews: Sequence[Mapping[str, object]],
    receipts: Sequence[Mapping[str, object]],
    launches: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    """Freshly reconstruct the aggregate from the two fixed-role records."""
    return build_review_aggregate(reviews, receipts, launches)


def review_aggregate_digest(value: Mapping[str, object]) -> str:
    validate_review_aggregate(value); return _digest("review_aggregate", value)


ACCEPTANCE_FIELDS = ("schema", "review_session_sha256", "review_session_durability_sha256", "candidate_manifest_sha256", "candidate_decision_sha256", "review_aggregate_sha256", "expected_bindings_sha256", "claim_boundary_sha256", "repository_state_sha256", "publication_record_sha256", "ordered_review_launch_sha256", "closed_classes", "correspondence_score", "evidence_level", "accepted_evidence_created", "level2_plus_created", "authority_granted")


def validate_acceptance_record(value: object) -> Mapping[str, object]:
    row = _fields(value, ACCEPTANCE_FIELDS, "acceptance record")
    _require(row["schema"] == SCHEMAS["acceptance"], "acceptance schema drift")
    for name in ACCEPTANCE_FIELDS:
        if name.endswith("_sha256") and name != "ordered_review_launch_sha256": _sha(row[name], name.replace("_", " "))
    _require(isinstance(row["ordered_review_launch_sha256"], list) and len(row["ordered_review_launch_sha256"]) == 2, "acceptance launch census drift")
    for digest in row["ordered_review_launch_sha256"]: _sha(digest, "acceptance launch digest")
    _require(row["closed_classes"] == list(CLASS_ORDER) and row["correspondence_score"] == "10/10" and row["evidence_level"] == EVIDENCE_LEVEL, "acceptance claim drift")
    _false_authority(row); return row


def build_acceptance_record(aggregate: Mapping[str, object], candidate_decision_sha256: str) -> Dict[str, object]:
    validate_review_aggregate(aggregate)
    _require(aggregate["atomic_result"] == "accept" and aggregate["candidate_decision_sha256"] == candidate_decision_sha256, "rejected aggregate cannot create acceptance")
    value = {"schema": SCHEMAS["acceptance"], "review_session_sha256": aggregate["review_session_sha256"], "review_session_durability_sha256": aggregate["review_session_durability_sha256"], "candidate_manifest_sha256": aggregate["candidate_manifest_sha256"], "candidate_decision_sha256": candidate_decision_sha256, "review_aggregate_sha256": review_aggregate_digest(aggregate), "expected_bindings_sha256": aggregate["expected_bindings_sha256"], "claim_boundary_sha256": aggregate["claim_boundary_sha256"], "repository_state_sha256": aggregate["repository_state_sha256"], "publication_record_sha256": aggregate["publication_record_sha256"], "ordered_review_launch_sha256": aggregate["ordered_review_launch_sha256"], "closed_classes": list(CLASS_ORDER), "correspondence_score": "10/10", "evidence_level": EVIDENCE_LEVEL, "accepted_evidence_created": False, "level2_plus_created": False, "authority_granted": False}
    validate_acceptance_record(value); return value


def acceptance_record_digest(value: Mapping[str, object]) -> str:
    validate_acceptance_record(value); return _digest("acceptance", value)


SESSION_GRAPH_PATH_FIELDS = (
    "decision", "review_root", "review_session", "review_session_durability",
)
PAIR_CONTEXT_FIELDS = (
    "receipt", "receipt_raw", "review", "review_raw", "launch",
    "expected_argv", "expected_paths",
)


def validate_acceptance_graph(
    acceptance: object,
    acceptance_raw: bytes,
    review_aggregate: object,
    review_aggregate_raw: bytes,
    pair_contexts: Sequence[Mapping[str, object]],
    *,
    review_session: object,
    review_session_raw: bytes,
    review_session_durability: object,
    review_session_durability_raw: bytes,
    candidate_decision: object,
    candidate_decision_raw: bytes,
    decision_file_identity: object,
    authorization: object,
    candidate_manifest: object,
    expected_bindings: object,
    repository_state: object,
    publication_record: object,
    a3l6_gate_bundle: object,
    snapshot_copy_manifest: object,
    candidate_files: object,
    reconstructed_class_results: object,
    session_paths: Mapping[str, object],
) -> Mapping[str, object]:
    """Recompute the complete two-review graph and final local acceptance."""
    manifest = validate_candidate_manifest(candidate_manifest)
    paths = _fields(session_paths, SESSION_GRAPH_PATH_FIELDS, "session graph paths")
    for name, path in paths.items():
        _path(path, "session graph " + name.replace("_", " "), absolute=True)
    session_graph = validate_review_session_graph(
        review_session,
        review_session_raw,
        review_session_durability,
        review_session_durability_raw,
        candidate_decision,
        candidate_decision_raw,
        decision_file_identity,
        manifest_digest(manifest),
        paths["decision"],
        paths["review_root"],
        paths["review_session"],
        paths["review_session_durability"],
    )
    _require(
        isinstance(pair_contexts, (list, tuple)) and len(pair_contexts) == 2,
        "acceptance review-pair census drift",
    )
    checked_contexts = [
        _fields(item, PAIR_CONTEXT_FIELDS, "review pair context")
        for item in pair_contexts
    ]
    pair_results = []
    for context in checked_contexts:
        pair_results.append(
            validate_fresh_review_graph(
                context["receipt"],
                context["receipt_raw"],
                context["review"],
                context["review_raw"],
                context["launch"],
                review_session=review_session,
                review_session_durability=review_session_durability,
                authorization=authorization,
                candidate_manifest=manifest,
                candidate_decision=candidate_decision,
                expected_bindings=expected_bindings,
                repository_state=repository_state,
                publication_record=publication_record,
                a3l6_gate_bundle=a3l6_gate_bundle,
                snapshot_copy_manifest=snapshot_copy_manifest,
                candidate_files=candidate_files,
                reconstructed_class_results=reconstructed_class_results,
                expected_argv=context["expected_argv"],
                expected_paths=context["expected_paths"],
            )
        )
    _require(
        tuple(item["role"] for item in pair_results) == REVIEW_ROLE_ORDER
        and pair_results[0]["reviewer_id"] != pair_results[1]["reviewer_id"]
        and pair_results[0]["process_id"] != pair_results[1]["process_id"],
        "acceptance reviewer/process independence drift",
    )
    reviews = [item["review"] for item in checked_contexts]
    receipts = [item["receipt"] for item in checked_contexts]
    launches = [item["launch"] for item in checked_contexts]
    reconstructed = reconstruct_review_aggregate(reviews, receipts, launches)
    aggregate = validate_review_aggregate(
        _reopened_canonical_object(
            review_aggregate_raw, review_aggregate, "review aggregate"
        )
    )
    _require(
        aggregate == reconstructed and aggregate["atomic_result"] == "accept",
        "retained review aggregate reconstruction drift",
    )
    expected_acceptance = build_acceptance_record(
        reconstructed, decision_digest(candidate_decision)
    )
    accepted = validate_acceptance_record(
        _reopened_canonical_object(acceptance_raw, acceptance, "acceptance record")
    )
    _require(accepted == expected_acceptance, "final acceptance graph drift")
    _require(
        accepted["review_session_sha256"] == session_graph["review_session_sha256"]
        and accepted["review_session_durability_sha256"]
        == session_graph["review_session_durability_sha256"]
        and accepted["candidate_decision_sha256"]
        == session_graph["candidate_decision_sha256"],
        "acceptance session/decision binding drift",
    )
    return {
        "acceptance_sha256": acceptance_record_digest(accepted),
        "review_aggregate_sha256": review_aggregate_digest(aggregate),
        "review_session_sha256": session_graph["review_session_sha256"],
        "review_session_durability_sha256": session_graph[
            "review_session_durability_sha256"
        ],
        "closed_classes": list(CLASS_ORDER),
        "correspondence_score": "10/10",
        "evidence_level": EVIDENCE_LEVEL,
        "accepted_evidence_created": False,
        "level2_plus_created": False,
        "authority_granted": False,
    }


GATE_PLAN_FIELDS = ("schema", "implementation_commit", "implementation_tree", "audit_commit", "python_path", "python_sha256", "python_version", "environment", "gate_source_root", "gate_source_root_identity", "gate_temp_root", "sandbox_exec_path", "sandbox_exec_sha256", "sandbox_profile_path", "sandbox_profile_sha256", "gate_source_manifest_sha256", "cwd", "commands", "reviewed_paths", "expected_focused_test_ids", "expected_focused_test_count", "expected_discovery_test_count")
GATE_SOURCE_FIELDS = ("schema", "implementation_commit", "implementation_tree", "audit_commit", "git_path", "git_sha256", "environment", "repository_cwd", "materialized_root", "materialized_root_identity", "gate_temp_root", "sandbox_exec_descriptor_observation", "sandbox_profile_path", "sandbox_profile_descriptor_observation", "sandbox_profile_base64", "sandbox_profile_sha256", "materialized_inventory_before_sha256", "materialized_inventory_before", "materialized_inventory_after_sha256", "materialized_inventory_after", "head_observation", "tree_observation", "status_before_observation", "ordered_blob_observations", "ordered_sources", "pre_gate_capture_ended_monotonic_ns", "post_gate_capture_started_monotonic_ns", "status_after_observation")
GATE_BUNDLE_FIELDS = ("schema", "gate_plan", "gate_source_manifest", "implementation_commit", "implementation_tree", "python_path", "python_sha256", "python_version", "python_version_observation", "ordered_gate_observations", "focused_test_ids", "focused_test_count", "discovery_test_count", "ordered_review_records", "result")
GATE_REVIEW_FIELDS = ("schema", "role", "reviewer_id", "implementation_commit", "implementation_tree", "ordered_file_sha256", "gate_plan_sha256", "gate_source_manifest_sha256", "gate_observation_sha256", "findings", "result")
GATE_COMMAND_FIELDS = ("role", "argv", "environment", "cwd", "stdin_policy", "timeout_ns", "stdout_cap_bytes", "stderr_cap_bytes", "activation", "expected_exit_code", "expected_signal")
GATE_OBSERVATION_FIELDS = ("role", "argv", "environment", "cwd", "stdin_policy", "executable_path", "executable_sha256", "cwd_identity_before", "cwd_identity_after", "timeout_ns", "stdout_cap_bytes", "stderr_cap_bytes", "started_monotonic_ns", "ended_monotonic_ns", "outcome", "exit_code", "signal", "stdout_total_bytes", "stdout_retained_bytes", "stdout_truncated", "stdout_base64", "stdout_sha256", "stderr_total_bytes", "stderr_retained_bytes", "stderr_truncated", "stderr_base64", "stderr_sha256")
GATE_CAPTURE_FIELDS = tuple(name for name in GATE_OBSERVATION_FIELDS if name not in ("cwd_identity_before", "cwd_identity_after"))
GATE_SOURCE_ROW_FIELDS = ("path", "git_object_expression", "git_blob_oid", "bytes", "sha256", "pre_gate_started_monotonic_ns", "pre_gate_ended_monotonic_ns", "pre_gate_descriptor_observation", "post_gate_started_monotonic_ns", "post_gate_ended_monotonic_ns", "post_gate_descriptor_observation")
GATE_INVENTORY_FIELDS = ("path", "type", "mode", "device", "inode", "uid", "gid", "link_count", "bytes", "sha256")
REVIEWED_PATHS = tuple("tools/hsai-formal-preflight/" + name for name in ("p01b_container_probe.py", "p01b_container_evidence.py", "p01b_container_execution.py", "p01b_container_evidence_tests.py", "p01b_container_execution_tests.py"))

_GATE_PARENT_RE = re.compile(r"^/private/tmp/hsai-p01b-gate-[0-9a-f]{32}$")
_GATE_TEST_ID_RE = re.compile(r"^__main__\.[A-Za-z_][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+$")
_GATE_RESULT_RE = re.compile(rb"Ran ([0-9]+) tests in ([0-9]+(?:\.[0-9]+)?)s")


def _gate_environment(temp_root: str) -> Dict[str, str]:
    return {
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        # Must match execution.gate_environment; marks the A3L6 execution-focused gate.
        "P01B_GATE_SANDBOX_ACTIVE": "1",
        "TMPDIR": temp_root,
    }


def _gate_profile(source_root: str, temp_root: str) -> bytes:
    return ("(version 1)\n"
            "(deny default)\n"
            "(allow process*)\n"
            "(allow signal)\n"
            "(allow sysctl-read)\n"
            "(allow file-read-metadata)\n"
            "(allow file-read-data (literal \"/\"))\n"
            "(allow file-read* (subpath \"{}\") (subpath \"{}\") (subpath \"/System/Library\") (subpath \"/usr/lib\") (subpath \"/usr/bin\") (subpath \"/bin\") (subpath \"/Library/Developer/CommandLineTools\") (subpath \"/private/etc\") (literal \"/dev/null\") (literal \"/dev/urandom\"))\n"
            "(allow file-write* (subpath \"{}\") (literal \"/dev/null\"))\n"
            "(deny network*)\n").format(source_root, temp_root, temp_root).encode("ascii")


def _gate_paths(source_root: object, temp_root: object, profile_path: object) -> str:
    source = _path(source_root, "gate source root", absolute=True)
    temp = _path(temp_root, "gate temp root", absolute=True)
    profile = _path(profile_path, "sandbox profile path", absolute=True)
    _require(source.endswith("/source"), "gate source child drift")
    parent = source[:-7]
    _require(_GATE_PARENT_RE.fullmatch(parent) is not None, "gate parent path drift")
    _require(temp == parent + "/scratch" and profile == parent + "/gate.sb", "gate child path drift")
    return parent


def _gate_expected_argv(plan: Mapping[str, object]) -> Tuple[List[str], ...]:
    prefix = [plan["sandbox_exec_path"], "-f", plan["sandbox_profile_path"], plan["python_path"], "-E", "-s", "-S", "-B"]
    return (
        prefix + ["tools/hsai-formal-preflight/p01b_container_evidence_tests.py", "-v"],
        prefix + ["tools/hsai-formal-preflight/p01b_container_execution_tests.py", "-v"],
        prefix + ["-m", "unittest", "discover", "-s", "tools/hsai-formal-preflight/tests", "-p", "test_*.py", "-v"],
    )


def _validate_gate_stream(row: Mapping[str, object], prefix: str) -> bytes:
    raw = _decode_b64(row[prefix + "_base64"], "gate " + prefix)
    _require(row[prefix + "_total_bytes"] == row[prefix + "_retained_bytes"] == len(raw), "gate stream length drift")
    _require(row[prefix + "_truncated"] is False and len(raw) <= row[prefix + "_cap_bytes"], "gate stream retention drift")
    _require(row[prefix + "_sha256"] == sha256_hex(raw), "gate stream digest drift")
    return raw


def _validate_gate_capture(value: object, role: str, argv: Sequence[str], environment: Mapping[str, str], cwd: str, executable_path: str, executable_sha256: str, stdout_cap: int) -> Tuple[Mapping[str, object], bytes]:
    row = _fields(value, GATE_CAPTURE_FIELDS, "gate source capture")
    _require(row["role"] == role and row["argv"] == list(argv), "gate source argv drift")
    _require(row["environment"] == environment and row["cwd"] == cwd and row["stdin_policy"] == "closed", "gate source execution context drift")
    _require(row["executable_path"] == executable_path and row["executable_sha256"] == executable_sha256, "gate source executable drift")
    _require(row["timeout_ns"] == 60_000_000_000 and row["stdout_cap_bytes"] == stdout_cap and row["stderr_cap_bytes"] == 16_384, "gate source bound drift")
    _require(_is_int(row["started_monotonic_ns"]) and _is_int(row["ended_monotonic_ns"]) and row["started_monotonic_ns"] < row["ended_monotonic_ns"], "gate source timing drift")
    _require(row["outcome"] == "completed" and row["exit_code"] == 0 and row["signal"] is None, "gate source outcome drift")
    stdout = _validate_gate_stream(row, "stdout")
    _require(_validate_gate_stream(row, "stderr") == b"", "gate source stderr drift")
    return row, stdout


def _git_blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _gate_inventory_paths() -> Tuple[str, ...]:
    paths = {"."}
    for path in SNAPSHOT_PATHS:
        paths.add(path)
        parts = path.split("/")[:-1]
        for index in range(1, len(parts) + 1):
            paths.add("/".join(parts[:index]))
    return tuple(["."] + sorted(paths - {"."}))


def _validate_gate_inventory(value: object, root_identity: Mapping[str, object], source_rows: Sequence[Mapping[str, object]]) -> List[Mapping[str, object]]:
    _require(isinstance(value, list), "gate inventory must be an array")
    rows = [_fields(item, GATE_INVENTORY_FIELDS, "gate inventory row") for item in value]
    _require(tuple(item["path"] for item in rows) == _gate_inventory_paths(), "gate inventory path census drift")
    regular = {item["path"]: item for item in rows if item["type"] == "regular"}
    _require(set(regular) == set(SNAPSHOT_PATHS), "gate inventory regular census drift")
    inode_pairs = []
    for item in rows:
        _path(item["path"], "gate inventory path", absolute=False) if item["path"] != "." else None
        for name in ("mode", "device", "inode", "uid", "gid", "link_count"):
            _nonnegative(item[name], "gate inventory " + name)
        if item["type"] == "directory":
            _require(item["mode"] == 365 and item["bytes"] is None and item["sha256"] is None, "gate directory inventory drift")
        else:
            _require(item["type"] == "regular" and item["mode"] == 292 and item["link_count"] == 1, "gate regular inventory drift")
            _nonnegative(item["bytes"], "gate inventory bytes"); _sha(item["sha256"], "gate inventory digest")
            inode_pairs.append((item["device"], item["inode"]))
    _require(len(inode_pairs) == len(set(inode_pairs)), "gate inventory inode reuse")
    _require({name: rows[0][name] for name in ("device", "inode", "mode", "uid", "gid", "link_count")} == root_identity, "gate inventory root identity drift")
    by_path = {item["path"]: item for item in source_rows}
    for path, item in regular.items():
        source = by_path[path]
        for observation in (source["pre_gate_descriptor_observation"], source["post_gate_descriptor_observation"]):
            identity = observation["before"]
            _require(item["bytes"] == identity["size"] and item["sha256"] == observation["sha256"], "gate inventory content drift")
            for name in ("mode", "device", "inode", "uid", "gid", "link_count"):
                _require(item[name] == identity[name], "gate inventory descriptor drift")
    return rows


def validate_a3l6_gate_plan(value: object) -> Mapping[str, object]:
    plan = _fields(value, GATE_PLAN_FIELDS, "A3L6 gate plan")
    _require(plan["schema"] == SCHEMAS["a3l6_gate_plan"], "gate plan schema drift")
    for name in ("implementation_commit", "implementation_tree", "audit_commit"): _git(plan[name], name.replace("_", " "))
    _require(plan["python_path"] == "/usr/bin/python3" and plan["python_sha256"] == NATIVE_PYTHON_SHA256 and plan["python_version"] == "3.9.6", "gate Python drift")
    _gate_paths(plan["gate_source_root"], plan["gate_temp_root"], plan["sandbox_profile_path"])
    _path(plan["sandbox_exec_path"], "sandbox executable path", absolute=True)
    _sha(plan["sandbox_exec_sha256"], "sandbox executable digest"); _sha(plan["sandbox_profile_sha256"], "sandbox profile digest"); _sha(plan["gate_source_manifest_sha256"], "gate source manifest digest")
    root_identity = _identity(plan["gate_source_root_identity"], "gate source root identity")
    _require(root_identity["mode"] == 365 and plan["environment"] == _gate_environment(plan["gate_temp_root"]), "gate root/environment drift")
    _require(plan["cwd"] == plan["gate_source_root"] and plan["reviewed_paths"] == list(REVIEWED_PATHS), "gate path binding drift")
    _require(plan["expected_focused_test_count"] == 65 and plan["expected_discovery_test_count"] == 172, "gate count drift")
    ids = plan["expected_focused_test_ids"]
    _require(isinstance(ids, list) and len(ids) == 65 and ids == sorted(set(ids)) and all(isinstance(item, str) and _GATE_TEST_ID_RE.fullmatch(item) for item in ids), "focused test id census drift")
    commands = plan["commands"]
    _require(isinstance(commands, list) and len(commands) == 3, "gate command census drift")
    roles = ("evidence-focused", "execution-focused", "formal-discovery")
    for row, role, argv in zip(commands, roles, _gate_expected_argv(plan)):
        command = _fields(row, GATE_COMMAND_FIELDS, "gate command")
        _require(command == {"role": role, "argv": argv, "environment": plan["environment"], "cwd": plan["cwd"], "stdin_policy": "closed", "timeout_ns": 600_000_000_000, "stdout_cap_bytes": 262_144, "stderr_cap_bytes": 262_144, "activation": "always", "expected_exit_code": 0, "expected_signal": None}, "gate command drift")
    return plan


def a3l6_gate_plan_digest(value: Mapping[str, object]) -> str:
    validate_a3l6_gate_plan(value); return _digest("a3l6_gate_plan", value)


def validate_a3l6_gate_source(value: object) -> Mapping[str, object]:
    source = _fields(value, GATE_SOURCE_FIELDS, "A3L6 gate source")
    _require(source["schema"] == SCHEMAS["a3l6_gate_source"], "gate source schema drift")
    for name in ("implementation_commit", "implementation_tree", "audit_commit"): _git(source[name], name.replace("_", " "))
    _gate_paths(source["materialized_root"], source["gate_temp_root"], source["sandbox_profile_path"])
    _path(source["git_path"], "gate Git path", absolute=True); _sha(source["git_sha256"], "gate Git digest"); _path(source["repository_cwd"], "gate repository cwd", absolute=True)
    _require(source["environment"] == _gate_environment(source["gate_temp_root"]), "gate source environment drift")
    root_identity = _identity(source["materialized_root_identity"], "materialized root identity")
    _require(root_identity["mode"] == 365, "materialized root mode drift")
    sandbox = validate_descriptor_observation(source["sandbox_exec_descriptor_observation"])
    profile_observation = validate_descriptor_observation(source["sandbox_profile_descriptor_observation"])
    _require(sandbox["path"] == "/usr/bin/sandbox-exec" and sandbox["relative_path"] is None, "sandbox descriptor path drift")
    _require(profile_observation["path"] == source["sandbox_profile_path"] and profile_observation["relative_path"] is None and profile_observation["before"]["mode"] == 256, "sandbox profile descriptor drift")
    profile = _decode_b64(source["sandbox_profile_base64"], "sandbox profile")
    _require(profile == _gate_profile(source["materialized_root"], source["gate_temp_root"]), "sandbox profile byte drift")
    _require(sha256_hex(profile) == source["sandbox_profile_sha256"] == profile_observation["sha256"], "sandbox profile digest drift")
    environment = source["environment"]; git = source["git_path"]
    head_obs, head = _validate_gate_capture(source["head_observation"], "gate-head", [git, "rev-parse", "HEAD"], environment, source["repository_cwd"], git, source["git_sha256"], 4096)
    tree_obs, tree = _validate_gate_capture(source["tree_observation"], "gate-tree", [git, "rev-parse", source["implementation_commit"] + "^{tree}"], environment, source["repository_cwd"], git, source["git_sha256"], 4096)
    status_argv = [git, "status", "--porcelain=v2", "-z", "--untracked-files=all"]
    status_before_obs, status_before = _validate_gate_capture(source["status_before_observation"], "gate-status-before", status_argv, environment, source["repository_cwd"], git, source["git_sha256"], 1_048_576)
    _require(head == (source["audit_commit"] + "\n").encode("ascii") and tree == (source["implementation_tree"] + "\n").encode("ascii"), "gate Git identity transcript drift")
    forbidden = tuple(path.encode("utf-8") for path in SNAPSHOT_PATHS) + (b".gitmodules",)
    _require(not any(path in status_before for path in forbidden), "gate protected source status drift")
    blob_observations = source["ordered_blob_observations"]
    _require(
        isinstance(blob_observations, list) and len(blob_observations) == len(SNAPSHOT_PATHS),
        "gate blob observation census drift",
    )
    source_values = source["ordered_sources"]
    _require(
        isinstance(source_values, list) and len(source_values) == len(SNAPSHOT_PATHS),
        "gate source census drift",
    )
    source_rows = []
    for ordinal, (path, observation_value, source_value) in enumerate(zip(SNAPSHOT_PATHS, blob_observations, source_values)):
        expression = source["implementation_commit"] + ":" + path
        observation, raw = _validate_gate_capture(observation_value, "gate-blob-%03d" % ordinal, [git, "cat-file", "blob", expression], environment, source["repository_cwd"], git, source["git_sha256"], 16_777_216)
        row = _fields(source_value, GATE_SOURCE_ROW_FIELDS, "gate source row")
        _require(row["path"] == path and row["git_object_expression"] == expression and row["git_blob_oid"] == _git_blob_oid(raw), "gate source object binding drift")
        _require(row["bytes"] == len(raw) and row["sha256"] == sha256_hex(raw), "gate source content drift")
        _require(row["pre_gate_started_monotonic_ns"] < row["pre_gate_ended_monotonic_ns"] <= source["pre_gate_capture_ended_monotonic_ns"], "gate pre descriptor timing drift")
        _require(source["post_gate_capture_started_monotonic_ns"] <= row["post_gate_started_monotonic_ns"] < row["post_gate_ended_monotonic_ns"], "gate post descriptor timing drift")
        pre = validate_descriptor_observation(row["pre_gate_descriptor_observation"]); post = validate_descriptor_observation(row["post_gate_descriptor_observation"])
        expected_path = source["materialized_root"] + "/" + path
        _require(pre["role"] == "gate-source-pre" and post["role"] == "gate-source-post" and pre["path"] == post["path"] == expected_path and pre["relative_path"] == post["relative_path"] == path, "gate source descriptor path drift")
        _require(pre["before"] == post["before"] and pre["sha256"] == post["sha256"] == row["sha256"] and pre["before"]["size"] == row["bytes"], "gate source descriptor content drift")
        _require(observation["ended_monotonic_ns"] <= source["pre_gate_capture_ended_monotonic_ns"], "gate blob timing drift")
        source_rows.append(row)
    _require([item["path"] for item in source_rows] == list(SNAPSHOT_PATHS), "gate source path order drift")
    _require(source["materialized_inventory_before"] == source["materialized_inventory_after"], "gate inventory changed")
    inventory = _validate_gate_inventory(source["materialized_inventory_before"], root_identity, source_rows)
    canonical_inventory = canonical_json_bytes(inventory)
    _require(sha256_hex(canonical_inventory) == source["materialized_inventory_before_sha256"] == source["materialized_inventory_after_sha256"], "gate inventory digest drift")
    status_after_obs, status_after = _validate_gate_capture(source["status_after_observation"], "gate-status-after", status_argv, environment, source["repository_cwd"], git, source["git_sha256"], 1_048_576)
    _require(status_after == status_before, "gate repository status changed")
    _require(_is_int(source["pre_gate_capture_ended_monotonic_ns"]) and _is_int(source["post_gate_capture_started_monotonic_ns"]) and source["pre_gate_capture_ended_monotonic_ns"] <= source["post_gate_capture_started_monotonic_ns"], "gate capture timing drift")
    _require(head_obs["ended_monotonic_ns"] <= source["pre_gate_capture_ended_monotonic_ns"] and tree_obs["ended_monotonic_ns"] <= source["pre_gate_capture_ended_monotonic_ns"] and status_before_obs["ended_monotonic_ns"] <= source["pre_gate_capture_ended_monotonic_ns"], "gate pre capture bracket drift")
    _require(status_after_obs["started_monotonic_ns"] >= source["post_gate_capture_started_monotonic_ns"], "gate post capture bracket drift")
    return source


def a3l6_gate_source_digest(value: Mapping[str, object]) -> str:
    validate_a3l6_gate_source(value); return _digest("a3l6_gate_source", value)


def validate_a3l6_code_review(value: object) -> Mapping[str, object]:
    review = _fields(value, GATE_REVIEW_FIELDS, "A3L6 code review")
    _require(review["schema"] == SCHEMAS["a3l6_code_review"] and review["role"] in REVIEW_ROLE_ORDER, "gate review schema/role drift")
    _ascii(review["reviewer_id"], "gate reviewer")
    _git(review["implementation_commit"], "gate review commit"); _git(review["implementation_tree"], "gate review tree")
    _require(isinstance(review["ordered_file_sha256"], list) and len(review["ordered_file_sha256"]) == 5, "gate review file census drift")
    for row, path in zip(review["ordered_file_sha256"], REVIEWED_PATHS):
        _fields(row, ("path", "sha256"), "gate review file"); _require(row["path"] == path, "gate review path drift"); _sha(row["sha256"], "gate review file digest")
    for name in ("gate_plan_sha256", "gate_source_manifest_sha256", "gate_observation_sha256"): _sha(review[name], name.replace("_", " "))
    findings = _findings(review["findings"], "gate findings")
    _require(review["result"] == ("accept" if not findings else "reject"), "gate review result drift")
    return review


def _gate_test_ids(stderr: bytes, expected_count: int) -> List[str]:
    _require(stderr.endswith(b"OK\n"), "gate unittest terminal drift")
    lines = stderr.splitlines()
    _require(len(lines) >= expected_count + 5, "gate unittest transcript short")
    test_lines = lines[:expected_count]
    ids = []
    for line in test_lines:
        match = re.fullmatch(rb"(test_[A-Za-z0-9_]+) \(([^()]+)\) \.\.\. ok", line)
        _require(match is not None, "gate unittest test line drift")
        ids.append(match.group(2).decode("ascii") + "." + match.group(1).decode("ascii"))
    _require(lines[expected_count:] == [b"", b"-" * 70, lines[expected_count + 2], b"", b"OK"], "gate unittest summary shape drift")
    summary = _GATE_RESULT_RE.fullmatch(lines[expected_count + 2])
    _require(summary is not None and int(summary.group(1)) == expected_count, "gate unittest count drift")
    return ids


def _validate_gate_observation(value: object, command: Mapping[str, object], root_identity: Mapping[str, object], expected_ids: Optional[Sequence[str]], expected_count: int) -> Mapping[str, object]:
    row = _fields(value, GATE_OBSERVATION_FIELDS, "A3L6 gate observation")
    for name in ("role", "argv", "environment", "cwd", "stdin_policy", "timeout_ns", "stdout_cap_bytes", "stderr_cap_bytes"):
        _require(row[name] == command[name], "gate observation command drift: " + name)
    _require(row["executable_path"] == command["argv"][0] and row["executable_sha256"] == SANDBOX_EXEC_SHA256, "gate observation executable drift")
    _require(_identity(row["cwd_identity_before"], "gate cwd identity") == root_identity == _identity(row["cwd_identity_after"], "gate cwd identity"), "gate cwd identity drift")
    _require(_is_int(row["started_monotonic_ns"]) and _is_int(row["ended_monotonic_ns"]) and row["started_monotonic_ns"] < row["ended_monotonic_ns"] and row["ended_monotonic_ns"] - row["started_monotonic_ns"] <= row["timeout_ns"], "gate observation timing drift")
    _require(row["outcome"] == "completed" and row["exit_code"] == command["expected_exit_code"] and row["signal"] is command["expected_signal"], "gate observation outcome drift")
    _require(_validate_gate_stream(row, "stdout") == b"", "gate observation stdout drift")
    ids = _gate_test_ids(_validate_gate_stream(row, "stderr"), expected_count)
    if expected_ids is not None:
        _require(ids == list(expected_ids), "gate focused test id drift")
    return row


def validate_a3l6_gate_bundle(value: object, expected_bindings: Optional[Mapping[str, object]] = None) -> Mapping[str, object]:
    bundle = _fields(value, GATE_BUNDLE_FIELDS, "A3L6 gate bundle")
    _require(bundle["schema"] == SCHEMAS["a3l6_gate_bundle"], "gate bundle schema drift")
    plan = validate_a3l6_gate_plan(bundle["gate_plan"]); source = validate_a3l6_gate_source(bundle["gate_source_manifest"])
    _require(bundle["implementation_commit"] == plan["implementation_commit"] == source["implementation_commit"] and bundle["implementation_tree"] == plan["implementation_tree"] == source["implementation_tree"] and plan["audit_commit"] == source["audit_commit"], "gate implementation drift")
    _require(plan["gate_source_manifest_sha256"] == a3l6_gate_source_digest(source), "gate source binding drift")
    _require(plan["gate_source_root"] == source["materialized_root"] and plan["gate_source_root_identity"] == source["materialized_root_identity"] and plan["gate_temp_root"] == source["gate_temp_root"] and plan["environment"] == source["environment"], "gate source plan chain drift")
    _require(plan["sandbox_exec_path"] == source["sandbox_exec_descriptor_observation"]["path"] and plan["sandbox_exec_sha256"] == source["sandbox_exec_descriptor_observation"]["sha256"] and plan["sandbox_profile_path"] == source["sandbox_profile_path"] and plan["sandbox_profile_sha256"] == source["sandbox_profile_sha256"], "gate sandbox chain drift")
    _require((bundle["python_path"], bundle["python_sha256"], bundle["python_version"]) == (plan["python_path"], plan["python_sha256"], plan["python_version"]), "gate Python chain drift")
    version_observation, version_stdout = _validate_gate_capture(bundle["python_version_observation"], "gate-python-version", [plan["python_path"], "--version"], plan["environment"], plan["cwd"], plan["python_path"], plan["python_sha256"], 16_384)
    _require(version_observation["stderr_cap_bytes"] == 16_384 and version_stdout == b"Python 3.9.6\n", "gate Python version transcript drift")
    _require(bundle["focused_test_ids"] == plan["expected_focused_test_ids"] and bundle["focused_test_count"] == 65 and bundle["discovery_test_count"] == 172, "gate test census drift")
    observations = bundle["ordered_gate_observations"]
    _require(isinstance(observations, list) and len(observations) == 3, "gate observation census drift")
    focused = plan["expected_focused_test_ids"]
    expected_sets = (None, None, None)
    counts = (32, 33, 172)
    checked_observations = [_validate_gate_observation(item, command, plan["gate_source_root_identity"], ids, count) for item, command, ids, count in zip(observations, plan["commands"], expected_sets, counts)]
    focused_observation_ids = [
        _gate_test_ids(_validate_gate_stream(observation, "stderr"), count)
        for observation, count in zip(checked_observations[:2], (32, 33))
    ]
    _require(
        all(ids == sorted(set(ids)) for ids in focused_observation_ids)
        and set(focused_observation_ids[0]).isdisjoint(focused_observation_ids[1])
        and sorted(focused_observation_ids[0] + focused_observation_ids[1]) == focused,
        "gate focused observation/source census drift",
    )
    for index, observation in enumerate(checked_observations):
        _require(source["pre_gate_capture_ended_monotonic_ns"] <= observation["started_monotonic_ns"] < observation["ended_monotonic_ns"] <= source["post_gate_capture_started_monotonic_ns"], "gate observation capture bracket drift")
        if index: _require(checked_observations[index - 1]["ended_monotonic_ns"] <= observation["started_monotonic_ns"], "gate observations overlap")
    reviews = [validate_a3l6_code_review(item) for item in bundle["ordered_review_records"]]
    _require(tuple(item["role"] for item in reviews) == REVIEW_ROLE_ORDER and reviews[0]["reviewer_id"] != reviews[1]["reviewer_id"], "gate reviewer independence drift")
    _require(all(item["gate_plan_sha256"] == a3l6_gate_plan_digest(plan) and item["gate_source_manifest_sha256"] == a3l6_gate_source_digest(source) for item in reviews), "gate review binding drift")
    gate_observation_sha256 = sha256_hex(canonical_json_bytes(observations))
    source_sha = {item["path"]: item["sha256"] for item in source["ordered_sources"]}
    expected_files = [{"path": path, "sha256": source_sha[path]} for path in REVIEWED_PATHS]
    _require(all(item["implementation_commit"] == bundle["implementation_commit"] and item["implementation_tree"] == bundle["implementation_tree"] and item["ordered_file_sha256"] == expected_files and item["gate_observation_sha256"] == gate_observation_sha256 for item in reviews), "gate review correspondence drift")
    expected_result = "accept" if all(item["result"] == "accept" for item in reviews) else "reject"
    _require(bundle["result"] == expected_result == "accept", "gate bundle result drift")
    if expected_bindings is not None:
        bindings = validate_expected_bindings(expected_bindings)
        _require(bindings["a3l6_audit_commit"] == plan["audit_commit"] and bindings["a3l6_gate_plan_sha256"] == a3l6_gate_plan_digest(plan) and bindings["a3l6_gate_source_manifest_sha256"] == a3l6_gate_source_digest(source), "gate expected binding drift")
        _require(bindings["expected_focused_test_ids_sha256"] == sha256_hex(canonical_json_bytes(focused)) and bindings["expected_focused_test_count"] == plan["expected_focused_test_count"] and bindings["discovery_expected_test_count"] == plan["expected_discovery_test_count"], "gate expected test binding drift")
        _require((bindings["native_python_path"], bindings["native_python_sha256"], bindings["native_python_version"]) == (plan["python_path"], plan["python_sha256"], plan["python_version"]), "gate expected Python drift")
        _require((bindings["sandbox_exec_path"], bindings["sandbox_exec_sha256"], bindings["gate_sandbox_profile_sha256"]) == (plan["sandbox_exec_path"], plan["sandbox_exec_sha256"], plan["sandbox_profile_sha256"]), "gate expected sandbox drift")
        _require(bindings["git_path"] == source["git_path"] and bindings["git_sha256"] == source["git_sha256"] and bindings["validator_sha256"] == source_sha[REVIEWED_PATHS[1]] and bindings["collector_sha256"] == source_sha[REVIEWED_PATHS[2]], "gate expected source digest drift")
        _require(bindings["a3l6_gate_bundle_sha256"] == _digest("a3l6_gate_bundle", bundle), "gate bundle expected binding drift")
    return bundle


def a3l6_gate_bundle_digest(value: Mapping[str, object], expected_bindings: Optional[Mapping[str, object]] = None) -> str:
    validate_a3l6_gate_bundle(value, expected_bindings); return _digest("a3l6_gate_bundle", value)


def verify_domain_vectors() -> None:
    for kind, expected in DOMAIN_VECTORS.items():
        _require(domain_sha256(DOMAINS[kind], {}) == expected, "domain vector drift: " + kind)


verify_domain_vectors()


def reconstruct_published_candidate(files: object, manifest: object, publication_record: object, repository_state: object, expected_bindings: object) -> List[Dict[str, object]]:
    """Reconstruct ordered class closure from retained bytes; never from path presence."""
    return _semantic_reconstruct_published_candidate(
        files, manifest, publication_record, repository_state, expected_bindings
    )
