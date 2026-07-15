"""Pure-data P01B container command and receipt contract.

State slice:
phase-796a3l4i-hsai-p01b-container-command-receipt-contract-implementation.

This module builds and validates data. It does not read environment variables,
touch the filesystem, contact Docker, execute a command, or grant authority.
"""

from dataclasses import asdict, dataclass, replace
import hashlib
import json
import re
from typing import Dict, Iterable, Optional, Sequence, Tuple


AUTHORIZATION_ROOT_SCHEMA = "hsai-p01b-portable-authorization-root-v1"
PLACEHOLDER_BINDINGS_SCHEMA = "hsai-p01b-container-placeholder-bindings-v1"
COMMAND_PLAN_SCHEMA = "hsai-p01b-container-command-plan-v1"
COMMAND_RECEIPT_SCHEMA = "hsai-p01b-container-command-receipt-v1"
ATTEMPT_STATE_SCHEMA = "hsai-p01b-container-attempt-state-v1"

AUTHORIZATION_ROOT_DOMAIN = "hsai:p01b-portable-authorization-root:v1"
PLACEHOLDER_BINDINGS_DOMAIN = "hsai:p01b-container-placeholder-bindings:v1"
COMMAND_PLAN_DOMAIN = "hsai:p01b-container-command-plan:v1"
COMMAND_RECEIPT_DOMAIN = "hsai:p01b-container-command-receipt:v1"

DOCKER_EXECUTABLE = "/Applications/Docker.app/Contents/Resources/bin/docker"
DOCKER_EXECUTABLE_SHA256 = (
    "73206884cd100a165e20fbab2b1f9e09e0ae8fc959ec9b02fed46152a99c5e79"
)
DOCKER_HOST_URI = "unix:///Users/shaanp/.docker/run/docker.sock"
PLATFORM = "linux/arm64/v8"
IMAGE_CONFIG_DIGEST = (
    "sha256:d9c8998514b4afbe5517a7cca405ddf59c33b9240a21c029feab133d8beaa8a4"
)
SECCOMP_PROFILE_SHA256 = (
    "536529b665dd0972c37bfb569f5d4ac8a53592e7b00752bc39ff063ca9864c74"
)
CORPUS_SHA256 = "6f719e8a113464334b368e6470126b8339c5ed66f115ebced4c724555405b064"
SOURCE_MANIFEST_SHA256 = (
    "adebe965254ffa43e3c2579262dc365486c27eadb492d1fe55eaf73cf3eb00b6"
)
TEST_ID_SHA256 = "1439a56e935a1c0194db37e5a7e4ad926658e16aa8491246c56e88d8bb5a6726"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
CREATED_CONTAINER_ID = "${CREATED_CONTAINER_ID}"

HOST_ENV_KEYS = ("HOME", "LANG", "LC_ALL", "PATH", "TMPDIR", "TZ")
CONTAINER_ENVIRONMENT = (
    ("HOME", "/nonexistent"),
    ("LANG", "C.UTF-8"),
    ("LC_ALL", "C.UTF-8"),
    ("PATH", "/usr/local/bin:/usr/bin:/bin"),
    ("PYTHONHASHSEED", "0"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONNOUSERSITE", "1"),
    ("TMPDIR", "/work"),
    ("TZ", "UTC"),
)
FOCUSED_WORKLOAD_ARGV = (
    "/usr/local/bin/python3",
    "-B",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tools/hsai-formal-preflight/tests",
    "-p",
    "test_p01b_archive_ledger.py",
)
FULL_WORKLOAD_ARGV = (
    "/usr/local/bin/python3",
    "-B",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tools/hsai-formal-preflight/tests",
    "-p",
    "test_*.py",
)
WORKLOADS = {"focused": FOCUSED_WORKLOAD_ARGV, "full": FULL_WORKLOAD_ARGV}
NORMAL_ROLES = (
    "create",
    "inspect-prestart",
    "start-attach",
    "wait",
    "inspect-terminal",
    "remove",
)
ALL_ROLES = (
    "create",
    "inspect-prestart",
    "start-attach",
    "kill",
    "wait",
    "inspect-terminal",
    "remove",
)
OUTCOMES = ("exit", "signal", "timeout", "stdout_limit", "stderr_limit", "not_run")
BOUNDED_OUTCOMES = ("timeout", "stdout_limit", "stderr_limit")
TERMINAL_STATUSES = (
    "succeeded",
    "failed",
    "cleanup_failed",
    "cleanup_not_applicable_no_container_created",
)
MAX_RECEIPT_BYTES = 65536
COMMAND_TIMEOUT_NS = 1_800_000_000_000

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PREFIXED_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ATTEMPT_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}[a-z0-9]$")
AUTHORIZATION_ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,126}[a-z0-9]$")
CONTAINER_ID_RE = re.compile(r"^[0-9a-f]{64}$")
OCI_REPOSITORY_RE = re.compile(
    r"^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$"
)
SAFE_PATH_RE = re.compile(r"^/[A-Za-z0-9._/@+\-/]+$")
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 4096


class ContainerContractError(Exception):
    """A command, receipt, or state violates the frozen contract."""


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContainerContractError(message)


def _wire(value: object) -> object:
    if hasattr(value, "to_dict"):
        return value.to_dict()  # type: ignore[no-any-return, union-attr]
    if isinstance(value, tuple):
        return [_wire(item) for item in value]
    if isinstance(value, list):
        return [_wire(item) for item in value]
    if isinstance(value, dict):
        return {key: _wire(item) for key, item in value.items()}
    return value


def canonical_json_bytes(value: object) -> bytes:
    """Return compact sorted-key ASCII JSON without a trailing newline."""
    try:
        return json.dumps(
            _wire(value),
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as error:
        raise ContainerContractError("value is not canonical-JSON encodable") from error


def domain_sha256(domain: str, value: object) -> str:
    _require(isinstance(domain, str) and domain and "\x00" not in domain, "invalid digest domain")
    return hashlib.sha256(domain.encode("ascii") + b"\0" + canonical_json_bytes(value)).hexdigest()


def _reject_duplicate_keys(pairs: Iterable[Tuple[str, object]]) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ContainerContractError("duplicate JSON key: {}".format(key))
        result[key] = value
    return result


def _strict_json(raw: bytes) -> object:
    _require(isinstance(raw, bytes), "JSON input must be bytes")
    _require(len(raw) <= MAX_RECEIPT_BYTES, "JSON input exceeds size limit")
    try:
        text = raw.decode("ascii")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ContainerContractError("non-finite JSON value: {}".format(value))
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ContainerContractError("malformed canonical JSON") from error
    stack = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        _require(nodes <= MAX_JSON_NODES, "JSON node count exceeds limit")
        _require(depth <= MAX_JSON_DEPTH, "JSON nesting exceeds limit")
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
    _require(raw == canonical_json_bytes(value), "JSON is not canonical")
    return value


def _validate_sha256(value: object, name: str) -> None:
    _require(isinstance(value, str) and SHA256_RE.fullmatch(value) is not None, "invalid {}".format(name))


def _validate_prefixed_sha256(value: object, name: str) -> None:
    _require(
        isinstance(value, str) and PREFIXED_SHA256_RE.fullmatch(value) is not None,
        "invalid {}".format(name),
    )


def _validate_absolute_path(value: object, name: str) -> None:
    _require(isinstance(value, str) and value.startswith("/") and not value.startswith("//"), "invalid {}".format(name))
    _require("\x00" not in value, "invalid {}".format(name))
    if value == "/":
        return
    _require(SAFE_PATH_RE.fullmatch(value) is not None, "unsafe characters in {}".format(name))
    components = value.split("/")[1:]
    _require(all(component not in ("", ".", "..") for component in components), "noncanonical {}".format(name))


def _validate_environment(environment: Sequence[Tuple[str, str]], expected: Tuple[Tuple[str, str], ...]) -> None:
    _require(isinstance(environment, tuple), "environment must be an immutable tuple")
    _require(environment == expected, "environment drift")
    for key, value in environment:
        _require(isinstance(key, str) and isinstance(value, str), "invalid environment entry")
        _require("\x00" not in key and "\x00" not in value, "invalid environment entry")


@dataclass(frozen=True)
class AuthorizationRoot:
    authorization_id: str
    action_sha256: str
    policy_sha256: str
    evidence_bundle_sha256: str
    admission_decision_sha256: str
    schema: str = AUTHORIZATION_ROOT_SCHEMA

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    @property
    def digest(self) -> str:
        validate_authorization_root(self)
        return domain_sha256(AUTHORIZATION_ROOT_DOMAIN, self.to_dict())


def validate_authorization_root(root: AuthorizationRoot) -> None:
    _require(isinstance(root, AuthorizationRoot), "authorization root has wrong type")
    _require(root.schema == AUTHORIZATION_ROOT_SCHEMA, "authorization root schema drift")
    _require(AUTHORIZATION_ID_RE.fullmatch(root.authorization_id) is not None, "invalid authorization id")
    for name in (
        "action_sha256",
        "policy_sha256",
        "evidence_bundle_sha256",
        "admission_decision_sha256",
    ):
        _validate_sha256(getattr(root, name), name)


@dataclass(frozen=True)
class PlaceholderBindings:
    attempt_id: str
    authorization_root_sha256: str
    docker_executable: str
    docker_executable_sha256: str
    empty_docker_config_abs: str
    docker_host_uri: str
    seccomp_profile_abs: str
    seccomp_profile_sha256: str
    clean_corpus_root_abs: str
    corpus_sha256: str
    source_manifest_sha256: str
    test_id_sha256: str
    attempt_tmpdir_abs: str
    platform_manifest_reference: str
    image_config_digest: str
    workload_profile: str
    schema: str = PLACEHOLDER_BINDINGS_SCHEMA

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    @property
    def digest(self) -> str:
        validate_placeholder_bindings(self)
        return domain_sha256(PLACEHOLDER_BINDINGS_DOMAIN, self.to_dict())

    @property
    def host_environment(self) -> Tuple[Tuple[str, str], ...]:
        return (
            ("HOME", "/nonexistent"),
            ("LANG", "C"),
            ("LC_ALL", "C"),
            ("PATH", "/usr/bin:/bin"),
            ("TMPDIR", self.attempt_tmpdir_abs),
            ("TZ", "UTC"),
        )


def validate_placeholder_bindings(bindings: PlaceholderBindings) -> None:
    _require(isinstance(bindings, PlaceholderBindings), "bindings have wrong type")
    _require(bindings.schema == PLACEHOLDER_BINDINGS_SCHEMA, "bindings schema drift")
    _require(ATTEMPT_ID_RE.fullmatch(bindings.attempt_id) is not None, "invalid attempt id")
    _validate_sha256(bindings.authorization_root_sha256, "authorization root digest")
    _require(bindings.docker_executable == DOCKER_EXECUTABLE, "Docker executable path drift")
    _require(bindings.docker_executable_sha256 == DOCKER_EXECUTABLE_SHA256, "Docker executable digest drift")
    for name in (
        "docker_executable",
        "empty_docker_config_abs",
        "seccomp_profile_abs",
        "clean_corpus_root_abs",
        "attempt_tmpdir_abs",
    ):
        _validate_absolute_path(getattr(bindings, name), name)
    roots = (
        bindings.empty_docker_config_abs,
        bindings.seccomp_profile_abs,
        bindings.clean_corpus_root_abs,
        bindings.attempt_tmpdir_abs,
    )
    _require(len(roots) == len(set(roots)), "placeholder paths must be distinct")
    _require(bindings.docker_host_uri == DOCKER_HOST_URI, "Docker host endpoint drift")
    _require(bindings.seccomp_profile_sha256 == SECCOMP_PROFILE_SHA256, "seccomp digest drift")
    _require(bindings.corpus_sha256 == CORPUS_SHA256, "corpus digest drift")
    _require(bindings.source_manifest_sha256 == SOURCE_MANIFEST_SHA256, "source-manifest digest drift")
    _require(bindings.test_id_sha256 == TEST_ID_SHA256, "test-id digest drift")
    _require(bindings.workload_profile in WORKLOADS, "unknown workload profile")
    _require(
        isinstance(bindings.platform_manifest_reference, str)
        and "@sha256:" in bindings.platform_manifest_reference
        and not bindings.platform_manifest_reference.startswith("sha256:"),
        "platform manifest must be a repository digest reference",
    )
    repository, digest = bindings.platform_manifest_reference.rsplit("@", 1)
    _require(
        OCI_REPOSITORY_RE.fullmatch(repository) is not None
        and PREFIXED_SHA256_RE.fullmatch(digest) is not None,
        "invalid platform manifest",
    )
    _validate_prefixed_sha256(bindings.image_config_digest, "image config digest")
    _require(bindings.image_config_digest == IMAGE_CONFIG_DIGEST, "image config digest drift")
    _validate_environment(bindings.host_environment, bindings.host_environment)
    _require(tuple(key for key, _ in bindings.host_environment) == HOST_ENV_KEYS, "host environment key drift")


@dataclass(frozen=True)
class ContainerCommand:
    template_ordinal: int
    role: str
    argv: Tuple[str, ...]
    environment: Tuple[Tuple[str, str], ...]
    cwd: str
    stdout_cap: int
    stderr_cap: int
    timeout_ns: int
    activation: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "activation": self.activation,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "environment": dict(self.environment),
            "role": self.role,
            "stderr_cap": self.stderr_cap,
            "stdout_cap": self.stdout_cap,
            "template_ordinal": self.template_ordinal,
            "timeout_ns": self.timeout_ns,
        }


@dataclass(frozen=True)
class ContainerCommandPlan:
    attempt_id: str
    authorization_root_sha256: str
    bindings_sha256: str
    docker_executable_sha256: str
    platform_manifest_reference: str
    image_config_digest: str
    seccomp_profile_sha256: str
    corpus_sha256: str
    source_manifest_sha256: str
    test_id_sha256: str
    commands: Tuple[ContainerCommand, ...]
    schema: str = COMMAND_PLAN_SCHEMA

    def to_dict(self) -> Dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "authorization_root_sha256": self.authorization_root_sha256,
            "bindings_sha256": self.bindings_sha256,
            "commands": [command.to_dict() for command in self.commands],
            "corpus_sha256": self.corpus_sha256,
            "docker_executable_sha256": self.docker_executable_sha256,
            "image_config_digest": self.image_config_digest,
            "platform_manifest_reference": self.platform_manifest_reference,
            "schema": self.schema,
            "seccomp_profile_sha256": self.seccomp_profile_sha256,
            "source_manifest_sha256": self.source_manifest_sha256,
            "test_id_sha256": self.test_id_sha256,
        }

    @property
    def digest(self) -> str:
        return domain_sha256(COMMAND_PLAN_DOMAIN, self.to_dict())


def _command_prefix(bindings: PlaceholderBindings) -> Tuple[str, ...]:
    return (
        bindings.docker_executable,
        "--config",
        bindings.empty_docker_config_abs,
        "--host",
        bindings.docker_host_uri,
        "--log-level",
        "error",
    )


def _expected_commands(bindings: PlaceholderBindings) -> Tuple[ContainerCommand, ...]:
    prefix = _command_prefix(bindings)
    cid = CREATED_CONTAINER_ID
    create = prefix + (
        "container",
        "create",
        "--pull=never",
        "--platform={}".format(PLATFORM),
        "--name=hsai-p01b-{}".format(bindings.attempt_id),
        "--hostname=hsai-p01b",
        "--runtime=runc",
        "--network=none",
        "--ipc=none",
        "--cgroupns=private",
        "--user=65532:65532",
        "--read-only",
        "--privileged=false",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges:true",
        "--security-opt=seccomp={}".format(bindings.seccomp_profile_abs),
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
        "--mount=type=bind,src={},dst=/input,readonly,bind-propagation=rprivate".format(
            bindings.clean_corpus_root_abs
        ),
        "--workdir=/input",
        "--entrypoint=/usr/bin/env",
        bindings.platform_manifest_reference,
        "-i",
    ) + tuple("{}={}".format(key, value) for key, value in CONTAINER_ENVIRONMENT) + WORKLOADS[
        bindings.workload_profile
    ]
    role_argv = (
        ("create", create, "always"),
        ("inspect-prestart", prefix + ("container", "inspect", "--format={{json .}}", cid), "after-create"),
        ("start-attach", prefix + ("container", "start", "--attach", cid), "after-prestart-inspect"),
        ("kill", prefix + ("container", "kill", "--signal=KILL", cid), "on-bounded-start-failure"),
        ("wait", prefix + ("container", "wait", cid), "after-start"),
        ("inspect-terminal", prefix + ("container", "inspect", "--format={{json .}}", cid), "after-start"),
        ("remove", prefix + ("container", "rm", cid), "after-create"),
    )
    commands = []
    for ordinal, (role, argv, activation) in enumerate(role_argv):
        commands.append(
            ContainerCommand(
                template_ordinal=ordinal,
                role=role,
                argv=argv,
                environment=bindings.host_environment,
                cwd="/",
                stdout_cap=16384,
                stderr_cap=16384,
                timeout_ns=COMMAND_TIMEOUT_NS,
                activation=activation,
            )
        )
    return tuple(commands)


def build_container_command_plan(
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> ContainerCommandPlan:
    validate_authorization_root(authorization_root)
    validate_placeholder_bindings(bindings)
    _require(bindings.authorization_root_sha256 == authorization_root.digest, "authorization root binding drift")
    plan = ContainerCommandPlan(
        attempt_id=bindings.attempt_id,
        authorization_root_sha256=authorization_root.digest,
        bindings_sha256=bindings.digest,
        docker_executable_sha256=bindings.docker_executable_sha256,
        platform_manifest_reference=bindings.platform_manifest_reference,
        image_config_digest=bindings.image_config_digest,
        seccomp_profile_sha256=bindings.seccomp_profile_sha256,
        corpus_sha256=bindings.corpus_sha256,
        source_manifest_sha256=bindings.source_manifest_sha256,
        test_id_sha256=bindings.test_id_sha256,
        commands=_expected_commands(bindings),
    )
    validate_container_command_plan(plan, authorization_root, bindings)
    return plan


def validate_container_command_plan(
    plan: ContainerCommandPlan,
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> None:
    _require(isinstance(plan, ContainerCommandPlan), "plan has wrong type")
    validate_authorization_root(authorization_root)
    validate_placeholder_bindings(bindings)
    _require(plan.schema == COMMAND_PLAN_SCHEMA, "plan schema drift")
    expected_fields = (
        plan.attempt_id == bindings.attempt_id,
        plan.authorization_root_sha256 == authorization_root.digest == bindings.authorization_root_sha256,
        plan.bindings_sha256 == bindings.digest,
        plan.docker_executable_sha256 == DOCKER_EXECUTABLE_SHA256,
        plan.platform_manifest_reference == bindings.platform_manifest_reference,
        plan.image_config_digest == IMAGE_CONFIG_DIGEST,
        plan.seccomp_profile_sha256 == SECCOMP_PROFILE_SHA256,
        plan.corpus_sha256 == CORPUS_SHA256,
        plan.source_manifest_sha256 == SOURCE_MANIFEST_SHA256,
        plan.test_id_sha256 == TEST_ID_SHA256,
        plan.commands == _expected_commands(bindings),
    )
    _require(all(expected_fields), "plan binding or command drift")
    _require(tuple(command.role for command in plan.commands) == ALL_ROLES, "command role order drift")
    for command in plan.commands:
        _require(_is_int(command.template_ordinal), "invalid template ordinal")
        _require(command.argv and all(isinstance(arg, str) and arg and "\x00" not in arg for arg in command.argv), "invalid argv")
        _validate_environment(command.environment, bindings.host_environment)
        _validate_absolute_path(command.cwd, "command cwd")
        _require(command.stdout_cap == 16384 and command.stderr_cap == 16384, "stream cap drift")
        _require(command.timeout_ns == COMMAND_TIMEOUT_NS, "command timeout drift")
        unresolved = [arg for arg in command.argv if "${" in arg]
        if command.role == "create":
            _require(not unresolved, "create command contains a placeholder")
        else:
            _require(unresolved == [CREATED_CONTAINER_ID], "runtime placeholder drift")


@dataclass(frozen=True)
class CommandReceipt:
    plan_sha256: str
    authorization_root_sha256: str
    ordinal: int
    role: str
    argv: Tuple[str, ...]
    environment: Tuple[Tuple[str, str], ...]
    cwd: str
    docker_executable_sha256: str
    started_monotonic_ns: int
    ended_monotonic_ns: int
    duration_ns: int
    outcome: str
    exit_code: Optional[int]
    signal: Optional[int]
    stdout_bytes: int
    stdout_total_bytes: int
    stdout_sha256: str
    stdout_cap: int
    stdout_truncated: bool
    stderr_bytes: int
    stderr_total_bytes: int
    stderr_sha256: str
    stderr_cap: int
    stderr_truncated: bool
    container_id: Optional[str]
    previous_receipt_sha256: Optional[str]
    observation_class: str
    container_action_observed: bool
    accepted_evidence_created: bool
    level2_plus_created: bool
    authority_granted: bool
    schema: str = COMMAND_RECEIPT_SCHEMA

    def to_dict(self) -> Dict[str, object]:
        value = asdict(self)
        value["argv"] = list(self.argv)
        value["environment"] = dict(self.environment)
        return value

    @property
    def digest(self) -> str:
        return domain_sha256(COMMAND_RECEIPT_DOMAIN, self.to_dict())


RECEIPT_FIELDS = frozenset(CommandReceipt.__dataclass_fields__.keys())


def parse_command_receipt(raw: bytes) -> CommandReceipt:
    value = _strict_json(raw)
    _require(isinstance(value, dict), "receipt must be a JSON object")
    _require(set(value) == RECEIPT_FIELDS, "receipt fields drift")
    argv = value["argv"]
    environment = value["environment"]
    _require(isinstance(argv, list) and all(isinstance(item, str) for item in argv), "invalid receipt argv")
    _require(isinstance(environment, dict), "invalid receipt environment")
    _require(all(isinstance(key, str) and isinstance(item, str) for key, item in environment.items()), "invalid receipt environment")
    try:
        receipt = CommandReceipt(
            schema=value["schema"],
            plan_sha256=value["plan_sha256"],
            authorization_root_sha256=value["authorization_root_sha256"],
            ordinal=value["ordinal"],
            role=value["role"],
            argv=tuple(argv),
            environment=tuple(sorted(environment.items())),
            cwd=value["cwd"],
            docker_executable_sha256=value["docker_executable_sha256"],
            started_monotonic_ns=value["started_monotonic_ns"],
            ended_monotonic_ns=value["ended_monotonic_ns"],
            duration_ns=value["duration_ns"],
            outcome=value["outcome"],
            exit_code=value["exit_code"],
            signal=value["signal"],
            stdout_bytes=value["stdout_bytes"],
            stdout_total_bytes=value["stdout_total_bytes"],
            stdout_sha256=value["stdout_sha256"],
            stdout_cap=value["stdout_cap"],
            stdout_truncated=value["stdout_truncated"],
            stderr_bytes=value["stderr_bytes"],
            stderr_total_bytes=value["stderr_total_bytes"],
            stderr_sha256=value["stderr_sha256"],
            stderr_cap=value["stderr_cap"],
            stderr_truncated=value["stderr_truncated"],
            container_id=value["container_id"],
            previous_receipt_sha256=value["previous_receipt_sha256"],
            observation_class=value["observation_class"],
            container_action_observed=value["container_action_observed"],
            accepted_evidence_created=value["accepted_evidence_created"],
            level2_plus_created=value["level2_plus_created"],
            authority_granted=value["authority_granted"],
        )
    except TypeError as error:
        raise ContainerContractError("receipt construction failed") from error
    _require(raw == canonical_json_bytes(receipt.to_dict()), "receipt is not canonical")
    _validate_receipt_shape(receipt)
    return receipt


@dataclass(frozen=True)
class AttemptState:
    plan_sha256: str
    authorization_root_sha256: str
    status: str
    next_role: Optional[str]
    container_id: Optional[str]
    container_started: bool
    bounded_start_failure: bool
    skip_mode: Optional[str]
    completed_receipt_sha256: Tuple[str, ...]
    previous_receipt_sha256: Optional[str]
    first_failure: Optional[str]
    schema: str = ATTEMPT_STATE_SCHEMA

    @classmethod
    def initial(
        cls,
        plan: ContainerCommandPlan,
        authorization_root: AuthorizationRoot,
        bindings: PlaceholderBindings,
    ) -> "AttemptState":
        validate_container_command_plan(plan, authorization_root, bindings)
        return cls(
            plan_sha256=plan.digest,
            authorization_root_sha256=plan.authorization_root_sha256,
            status="ready",
            next_role="create",
            container_id=None,
            container_started=False,
            bounded_start_failure=False,
            skip_mode=None,
            completed_receipt_sha256=(),
            previous_receipt_sha256=None,
            first_failure=None,
        )

    def to_dict(self) -> Dict[str, object]:
        value = asdict(self)
        value["completed_receipt_sha256"] = list(self.completed_receipt_sha256)
        return value


def _template(plan: ContainerCommandPlan, role: str) -> ContainerCommand:
    for command in plan.commands:
        if command.role == role:
            return command
    raise ContainerContractError("plan is missing role: {}".format(role))


def _next_container_command_for_state(
    plan: ContainerCommandPlan,
    state: AttemptState,
) -> Optional[ContainerCommand]:
    _require(state.plan_sha256 == plan.digest, "state plan binding drift")
    _require(state.authorization_root_sha256 == plan.authorization_root_sha256, "state authorization binding drift")
    _require(state.status not in TERMINAL_STATUSES, "attempt is terminal")
    _require(state.next_role is not None, "state has no next role")
    if state.skip_mode is not None and state.next_role != "remove":
        return None
    if state.skip_mode == "no-container" and state.next_role == "remove":
        return None
    command = _template(plan, state.next_role)
    if state.next_role == "create":
        return command
    _require(state.container_id is not None, "container id is unavailable")
    argv = tuple(state.container_id if argument == CREATED_CONTAINER_ID else argument for argument in command.argv)
    _require(all("${" not in argument for argument in argv), "unresolved executable placeholder")
    return replace(command, argv=argv)


def _validate_receipt_shape(receipt: CommandReceipt) -> None:
    _require(isinstance(receipt, CommandReceipt), "receipt has wrong type")
    _require(receipt.schema == COMMAND_RECEIPT_SCHEMA, "receipt schema drift")
    _validate_sha256(receipt.plan_sha256, "plan digest")
    _validate_sha256(receipt.authorization_root_sha256, "authorization root digest")
    _require(_is_int(receipt.ordinal) and receipt.ordinal >= 0, "invalid receipt ordinal")
    _require(receipt.role in ALL_ROLES, "unknown receipt role")
    _require(isinstance(receipt.argv, tuple) and all(isinstance(arg, str) and arg and "\x00" not in arg for arg in receipt.argv), "invalid receipt argv")
    _validate_absolute_path(receipt.cwd, "receipt cwd")
    _validate_sha256(receipt.docker_executable_sha256, "Docker executable digest")
    for name in (
        "started_monotonic_ns",
        "ended_monotonic_ns",
        "duration_ns",
        "stdout_bytes",
        "stdout_total_bytes",
        "stdout_cap",
        "stderr_bytes",
        "stderr_total_bytes",
        "stderr_cap",
    ):
        value = getattr(receipt, name)
        _require(_is_int(value) and value >= 0, "invalid {}".format(name))
    _require(isinstance(receipt.stdout_truncated, bool) and isinstance(receipt.stderr_truncated, bool), "invalid truncation flag")
    _require(receipt.outcome in OUTCOMES, "unknown receipt outcome")
    if receipt.outcome == "exit":
        _require(_is_int(receipt.exit_code) and receipt.exit_code >= 0 and receipt.signal is None, "invalid exit outcome")
    elif receipt.outcome == "signal":
        _require(receipt.exit_code is None and _is_int(receipt.signal) and receipt.signal > 0, "invalid signal outcome")
    else:
        _require(receipt.exit_code is None and receipt.signal is None, "bounded/not-run outcome carries exit or signal")
    _validate_sha256(receipt.stdout_sha256, "stdout digest")
    _validate_sha256(receipt.stderr_sha256, "stderr digest")
    _require(receipt.stdout_bytes <= receipt.stdout_cap and receipt.stderr_bytes <= receipt.stderr_cap, "retained stream exceeds cap")
    if receipt.outcome == "stdout_limit":
        _require(
            receipt.stdout_bytes == receipt.stdout_cap
            and receipt.stdout_total_bytes > receipt.stdout_cap
            and receipt.stdout_truncated,
            "stdout-limit arithmetic drift",
        )
    else:
        _require(
            receipt.stdout_total_bytes == receipt.stdout_bytes and not receipt.stdout_truncated,
            "stdout length or truncation drift",
        )
    if receipt.outcome == "stderr_limit":
        _require(
            receipt.stderr_bytes == receipt.stderr_cap
            and receipt.stderr_total_bytes > receipt.stderr_cap
            and receipt.stderr_truncated,
            "stderr-limit arithmetic drift",
        )
    else:
        _require(
            receipt.stderr_total_bytes == receipt.stderr_bytes and not receipt.stderr_truncated,
            "stderr length or truncation drift",
        )
    if receipt.container_id is not None:
        _require(CONTAINER_ID_RE.fullmatch(receipt.container_id) is not None, "invalid container id")
    if receipt.previous_receipt_sha256 is not None:
        _validate_sha256(receipt.previous_receipt_sha256, "previous receipt digest")
    _require(receipt.observation_class in ("synthetic_fixture", "untrusted_external_candidate"), "invalid observation class")
    for name in (
        "container_action_observed",
        "accepted_evidence_created",
        "level2_plus_created",
        "authority_granted",
    ):
        _require(isinstance(getattr(receipt, name), bool), "invalid authority/observation flag")
    _require(
        not receipt.accepted_evidence_created and not receipt.level2_plus_created and not receipt.authority_granted,
        "authority escalation attempt",
    )
    if receipt.outcome == "not_run":
        _require(not receipt.container_action_observed, "not-run receipt fabricates an observation")
        _require(receipt.started_monotonic_ns == receipt.ended_monotonic_ns == receipt.duration_ns == 0, "not-run receipt carries time")
        _require(
            receipt.stdout_bytes
            == receipt.stdout_total_bytes
            == receipt.stderr_bytes
            == receipt.stderr_total_bytes
            == 0,
            "not-run receipt carries stream bytes",
        )
        _require(receipt.stdout_sha256 == EMPTY_SHA256 and receipt.stderr_sha256 == EMPTY_SHA256, "not-run receipt carries stream digests")
        _require(receipt.container_id is None, "not-run receipt carries container identity")
    else:
        _require(receipt.container_action_observed, "executed receipt lacks observation marker")
        _require(receipt.ended_monotonic_ns >= receipt.started_monotonic_ns, "monotonic time order drift")
        _require(receipt.duration_ns == receipt.ended_monotonic_ns - receipt.started_monotonic_ns, "duration drift")


def _validate_command_receipt_for_state(
    receipt: CommandReceipt,
    plan: ContainerCommandPlan,
    state: AttemptState,
) -> None:
    _validate_receipt_shape(receipt)
    _require(state.status not in TERMINAL_STATUSES and state.next_role is not None, "receipt after terminal state")
    _require(receipt.plan_sha256 == plan.digest == state.plan_sha256, "receipt plan binding drift")
    _require(
        receipt.authorization_root_sha256 == plan.authorization_root_sha256 == state.authorization_root_sha256,
        "receipt authorization binding drift",
    )
    _require(receipt.ordinal == len(state.completed_receipt_sha256), "receipt ordinal drift")
    _require(receipt.role == state.next_role, "receipt role drift")
    _require(receipt.previous_receipt_sha256 == state.previous_receipt_sha256, "receipt chain drift")
    expected = _next_container_command_for_state(plan, state)
    if expected is None:
        _require(receipt.outcome == "not_run", "skipped role must be not-run")
        template = _template(plan, receipt.role)
        expected_argv = template.argv
        if state.container_id is not None:
            expected_argv = tuple(
                state.container_id if argument == CREATED_CONTAINER_ID else argument
                for argument in expected_argv
            )
        _require(receipt.argv == expected_argv, "not-run argv drift")
        _require(receipt.environment == template.environment and receipt.cwd == template.cwd, "not-run command context drift")
        _require(receipt.stdout_cap == template.stdout_cap and receipt.stderr_cap == template.stderr_cap, "not-run cap drift")
    else:
        _require(receipt.argv == expected.argv, "receipt argv drift")
        _require(receipt.environment == expected.environment, "receipt environment drift")
        _require(receipt.cwd == expected.cwd, "receipt cwd drift")
        _require(receipt.stdout_cap == expected.stdout_cap and receipt.stderr_cap == expected.stderr_cap, "receipt cap drift")
        if receipt.outcome == "timeout":
            _require(receipt.duration_ns >= expected.timeout_ns, "timeout below command bound")
    _require(receipt.docker_executable_sha256 == plan.docker_executable_sha256, "receipt Docker digest drift")
    if receipt.role == "create":
        if receipt.outcome == "exit" and receipt.exit_code == 0:
            _require(receipt.container_id is not None, "successful create lacks container id")
        else:
            _require(receipt.container_id is None, "failed create carries container id")
    elif receipt.outcome != "not_run":
        _require(state.container_id is not None and receipt.container_id == state.container_id, "container identity drift")
    if receipt.role == "kill" and receipt.outcome != "not_run":
        _require(state.container_started and state.bounded_start_failure, "kill without bounded started container")


def _next_skipped_role(role: str) -> Optional[str]:
    index = ALL_ROLES.index(role)
    return ALL_ROLES[index + 1] if index + 1 < len(ALL_ROLES) else None


def _is_success(receipt: CommandReceipt) -> bool:
    return receipt.outcome == "exit" and receipt.exit_code == 0


def _advance_attempt_state_for_state(
    plan: ContainerCommandPlan,
    state: AttemptState,
    receipt: CommandReceipt,
) -> AttemptState:
    _validate_command_receipt_for_state(receipt, plan, state)
    digest = receipt.digest
    completed = state.completed_receipt_sha256 + (digest,)
    common = {
        "completed_receipt_sha256": completed,
        "previous_receipt_sha256": digest,
        "status": "running",
    }

    if state.skip_mode == "no-container":
        next_role = _next_skipped_role(receipt.role)
        if next_role is None:
            return replace(
                state,
                **{**common, "status": "cleanup_not_applicable_no_container_created"},
                next_role=None,
            )
        return replace(state, **common, next_role=next_role)

    if state.skip_mode == "prestart-failed" and receipt.role != "remove":
        next_role = _next_skipped_role(receipt.role)
        _require(next_role is not None, "prestart skip lost cleanup")
        return replace(state, **common, next_role=next_role)

    failure = state.first_failure
    if not _is_success(receipt) and receipt.outcome != "not_run" and failure is None:
        failure = "{}:{}".format(receipt.role, receipt.outcome)

    if receipt.role == "create":
        if _is_success(receipt):
            return replace(
                state,
                **common,
                next_role="inspect-prestart",
                container_id=receipt.container_id,
                first_failure=failure,
            )
        return replace(
            state,
            **common,
            next_role="inspect-prestart",
            skip_mode="no-container",
            first_failure=failure or "create:failed",
        )

    if receipt.role == "inspect-prestart":
        if _is_success(receipt):
            return replace(state, **common, next_role="start-attach", first_failure=failure)
        return replace(
            state,
            **common,
            next_role="start-attach",
            skip_mode="prestart-failed",
            first_failure=failure or "inspect-prestart:failed",
        )

    if receipt.role == "start-attach":
        if receipt.outcome in BOUNDED_OUTCOMES:
            return replace(
                state,
                **common,
                next_role="kill",
                container_started=True,
                bounded_start_failure=True,
                first_failure=failure,
            )
        if _is_success(receipt):
            return replace(
                state,
                **common,
                next_role="wait",
                container_started=True,
                first_failure=failure,
            )
        return replace(
            state,
            **common,
            next_role="wait",
            first_failure=failure or "start-attach:failed",
        )

    if receipt.role == "kill":
        return replace(state, **common, next_role="wait", first_failure=failure)

    if receipt.role == "wait":
        return replace(state, **common, next_role="inspect-terminal", first_failure=failure)

    if receipt.role == "inspect-terminal":
        return replace(state, **common, next_role="remove", first_failure=failure)

    _require(receipt.role == "remove", "unknown state transition")
    if not _is_success(receipt):
        return replace(
            state,
            **{**common, "status": "cleanup_failed"},
            next_role=None,
            first_failure=failure or "remove:failed",
        )
    return replace(
        state,
        **{**common, "status": "succeeded" if failure is None else "failed"},
        next_role=None,
        first_failure=failure,
    )


def _replay_receipt_prefix(
    plan: ContainerCommandPlan,
    receipts: Sequence[CommandReceipt],
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> AttemptState:
    _require(isinstance(receipts, (tuple, list)), "receipt chain has wrong type")
    _require(len(receipts) <= len(ALL_ROLES), "receipt chain exceeds lifecycle bound")
    state = AttemptState.initial(plan, authorization_root, bindings)
    for receipt in receipts:
        state = _advance_attempt_state_for_state(plan, state, receipt)
    return state


def next_container_command(
    plan: ContainerCommandPlan,
    prior_receipts: Sequence[CommandReceipt],
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> Optional[ContainerCommand]:
    state = _replay_receipt_prefix(plan, prior_receipts, authorization_root, bindings)
    return _next_container_command_for_state(plan, state)


def validate_command_receipt(
    receipt: CommandReceipt,
    plan: ContainerCommandPlan,
    prior_receipts: Sequence[CommandReceipt],
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> None:
    state = _replay_receipt_prefix(plan, prior_receipts, authorization_root, bindings)
    _validate_command_receipt_for_state(receipt, plan, state)


def advance_attempt_state(
    plan: ContainerCommandPlan,
    prior_receipts: Sequence[CommandReceipt],
    receipt: CommandReceipt,
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> AttemptState:
    state = _replay_receipt_prefix(plan, prior_receipts, authorization_root, bindings)
    return _advance_attempt_state_for_state(plan, state, receipt)


def validate_receipt_chain(
    plan: ContainerCommandPlan,
    receipts: Sequence[CommandReceipt],
    authorization_root: AuthorizationRoot,
    bindings: PlaceholderBindings,
) -> AttemptState:
    state = _replay_receipt_prefix(plan, receipts, authorization_root, bindings)
    _require(state.status in TERMINAL_STATUSES, "receipt chain is missing terminal cleanup")
    return state
