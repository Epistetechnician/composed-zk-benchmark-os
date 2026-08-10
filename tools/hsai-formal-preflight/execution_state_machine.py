#!/usr/bin/env python3
"""Canonical state and preservation rules for HSAI formal execution."""

import argparse
import base64
import hashlib
import json
import math
import os
import pathlib
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple


PLAN_SCHEMA = "hsai-formal-execution-plan-v1"
STATE_SCHEMA = "hsai-formal-execution-state-v1"
SNAPSHOT_SCHEMA = "hsai-primary-snapshot-v1"
NETWORK_POLICIES = ("none", "acquisition", "closed")
STATE_STATUSES = ("ready", "running", "failed", "complete")
COMMAND_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
ALLOWED_ENV_KEYS = frozenset(
    {
        "CARGO_HOME",
        "CARGO_NET_OFFLINE",
        "CARGO_TARGET_DIR",
        "HSAI_AENEAS_LEAN_ROOT",
        "LC_ALL",
        "MATHLIB_CACHE_DIR",
        "MATHLIB_NO_CACHE_ON_UPDATE",
        "PATH",
        "RUSTDOC",
        "RUSTUP_HOME",
        "RUSTUP_TOOLCHAIN",
    }
)
COMMAND_ROLES = ("producer", "exact-process-fixture")
BOUNDED_REASONS = ("exit", "timeout", "stdout_limit", "stderr_limit")
OPERATION_KINDS = (
    "internal-assertion",
    "atomic-materialization",
    "bounded-producer",
    "persistent-loopback-control",
    "cleanup-and-verify",
)
COMPLETE_PLAN_SCHEMA = "hsai-formal-complete-operation-plan-v1"
CONTRACT_REF_RE = re.compile(r"^phase[0-9]+-[a-z0-9-]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXACT_TIMEOUT_FIXTURE = (
    "/bin/sh",
    "-c",
    '/bin/sh -c "/bin/sleep 30" & child=$!; printf "%s\\n" "$child" '
    '> "$RUN/grandchild.pid"; wait "$child"',
)
EXACT_STDERR_FIXTURE = ("/bin/sh", "-c", "exec /usr/bin/yes x >&2")


class StateMachineError(Exception):
    """The plan, state, transition, or primary snapshot is invalid."""


@dataclass(frozen=True)
class Stage:
    stage_id: str
    ordinal: int
    network_policy: str
    mutation_owner: str
    predecessor: Optional[str]

    def to_dict(self) -> Dict[str, object]:
        return {
            "mutation_owner": self.mutation_owner,
            "network_policy": self.network_policy,
            "ordinal": self.ordinal,
            "predecessor": self.predecessor,
            "stage_id": self.stage_id,
        }


STAGES: Tuple[Stage, ...] = (
    Stage("primary-preservation", 0, "none", "attempt-roots", None),
    Stage("frozen-identities", 1, "none", "detached-repository", "primary-preservation"),
    Stage("helper-self-tests", 2, "none", "attempt-run-root", "frozen-identities"),
    Stage("client-and-fixtures", 3, "none", "attempt-run-root", "helper-self-tests"),
    Stage("rust-acquisition", 4, "acquisition", "isolated-rustup-root", "client-and-fixtures"),
    Stage("charon-source", 5, "acquisition", "attempt-run-root", "rust-acquisition"),
    Stage("aeneas-assets", 6, "acquisition", "isolated-aeneas-root", "charon-source"),
    Stage("archive-equivalence", 7, "none", "isolated-aeneas-root", "aeneas-assets"),
    Stage("lean-acquisition", 8, "acquisition", "isolated-lean-root", "archive-equivalence"),
    Stage("dependency-freeze", 9, "acquisition", "attempt-owned-caches", "lean-acquisition"),
    Stage("sandboxed-backends", 10, "closed", "attempt-run-root", "dependency-freeze"),
    Stage("retention-and-cleanup", 11, "closed", "attempt-roots", "sandboxed-backends"),
)
STAGE_BY_ID = {stage.stage_id: stage for stage in STAGES}


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise StateMachineError("duplicate JSON key: {}".format(key))
        value[key] = item
    return value


def canonical_json_line(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        + b"\n"
    )


def load_canonical_json(raw: bytes) -> object:
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise StateMachineError("invalid canonical JSON: {}".format(error))
    if raw != canonical_json_line(value):
        raise StateMachineError("JSON is not canonical")
    return value


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    stage_id: str
    argv: Tuple[str, ...]
    env: Tuple[Tuple[str, str], ...]
    network_policy: str
    role: str
    cwd: str
    timeout_seconds: float
    stdout_cap: int
    stderr_cap: int
    status_path: str
    stdout_path: str
    stderr_path: str
    expected_reason: str
    expected_returncode: Optional[int]
    expected_signal: Optional[int]

    @property
    def output_paths(self) -> Tuple[str, str, str]:
        return (self.status_path, self.stdout_path, self.stderr_path)

    def validate(self) -> None:
        if not COMMAND_ID_RE.fullmatch(self.command_id):
            raise StateMachineError("invalid command id: {}".format(self.command_id))
        stage = STAGE_BY_ID.get(self.stage_id)
        if stage is None:
            raise StateMachineError("unknown command stage: {}".format(self.stage_id))
        if self.network_policy != stage.network_policy:
            raise StateMachineError("command network policy differs from stage")
        if self.role not in COMMAND_ROLES:
            raise StateMachineError("unknown command role")
        if not self.argv or not os.path.isabs(self.argv[0]):
            raise StateMachineError("command executable must be absolute")
        for argument in self.argv:
            if not isinstance(argument, str) or "\x00" in argument:
                raise StateMachineError("invalid argv value")
        if self.argv[0] in ("/bin/bash", "/bin/sh", "/bin/zsh"):
            self._validate_exact_shell_fixture()
        keys = [key for key, _ in self.env]
        if len(keys) != len(set(keys)):
            raise StateMachineError("duplicate environment key")
        for key, value in self.env:
            if not ENV_KEY_RE.fullmatch(key) or key not in ALLOWED_ENV_KEYS:
                raise StateMachineError("unknown environment key: {}".format(key))
            if "\x00" in value:
                raise StateMachineError("invalid environment value")
        if not os.path.isabs(self.cwd) or os.path.normpath(self.cwd) != self.cwd:
            raise StateMachineError("command cwd must be absolute and canonical")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise StateMachineError("command timeout must be finite and positive")
        if (
            not isinstance(self.stdout_cap, int)
            or isinstance(self.stdout_cap, bool)
            or self.stdout_cap <= 0
            or not isinstance(self.stderr_cap, int)
            or isinstance(self.stderr_cap, bool)
            or self.stderr_cap <= 0
        ):
            raise StateMachineError("stream caps must be positive integers")
        if self.expected_reason not in BOUNDED_REASONS:
            raise StateMachineError("invalid expected bounded reason")
        if self.expected_reason == "exit":
            if self.expected_returncode is None or self.expected_returncode < 0:
                raise StateMachineError("exit requires a nonnegative return code")
            if self.expected_signal is not None:
                raise StateMachineError("exit cannot expect a signal")
        elif self.expected_returncode is not None:
            raise StateMachineError("bounded termination cannot expect a return code")
        elif self.expected_signal is None or self.expected_signal <= 0:
            raise StateMachineError("bounded termination requires a positive signal")
        if not all(os.path.isabs(path) for path in self.output_paths):
            raise StateMachineError("command output paths must be absolute")
        absolute_outputs = [os.path.abspath(path) for path in self.output_paths]
        if len(absolute_outputs) != len(set(absolute_outputs)):
            raise StateMachineError("command reuses an output path")

    def _validate_exact_shell_fixture(self) -> None:
        if self.role != "exact-process-fixture":
            raise StateMachineError("shell command execution is prohibited")
        if self.stage_id != "client-and-fixtures" or self.network_policy != "none":
            raise StateMachineError("exact fixture has the wrong stage or network policy")
        if self.argv == EXACT_TIMEOUT_FIXTURE:
            expected = (1.0, 1024, 1024, "timeout", None, 15)
        elif self.argv == EXACT_STDERR_FIXTURE:
            expected = (5.0, 1024, 1024, "stderr_limit", None, 15)
        else:
            raise StateMachineError("shell fixture argv does not match Phase 732")
        observed = (
            self.timeout_seconds,
            self.stdout_cap,
            self.stderr_cap,
            self.expected_reason,
            self.expected_returncode,
            self.expected_signal,
        )
        if observed != expected:
            raise StateMachineError("shell fixture bounds or outcome drift")

    def to_dict(self) -> Dict[str, object]:
        return {
            "argv": list(self.argv),
            "command_id": self.command_id,
            "env": {key: value for key, value in self.env},
            "cwd": self.cwd,
            "expected_reason": self.expected_reason,
            "expected_returncode": self.expected_returncode,
            "expected_signal": self.expected_signal,
            "network_policy": self.network_policy,
            "output_paths": list(self.output_paths),
            "role": self.role,
            "stage_id": self.stage_id,
            "stderr_cap": self.stderr_cap,
            "stdout_cap": self.stdout_cap,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class ExecutionPlan:
    attempt_id: str
    commands: Tuple[CommandSpec, ...]

    def validate(self) -> None:
        if not COMMAND_ID_RE.fullmatch(self.attempt_id):
            raise StateMachineError("invalid attempt id")
        command_ids = [command.command_id for command in self.commands]
        if len(command_ids) != len(set(command_ids)):
            raise StateMachineError("duplicate command id")
        outputs = []
        previous_ordinal = -1
        for command in self.commands:
            command.validate()
            ordinal = STAGE_BY_ID[command.stage_id].ordinal
            if ordinal < previous_ordinal:
                raise StateMachineError("commands are not in stage order")
            previous_ordinal = ordinal
            outputs.extend(os.path.abspath(path) for path in command.output_paths)
        if len(outputs) != len(set(outputs)):
            raise StateMachineError("plan reuses an output path")

    def to_dict(self) -> Dict[str, object]:
        self.validate()
        return {
            "attempt_id": self.attempt_id,
            "commands": [command.to_dict() for command in self.commands],
            "schema": PLAN_SCHEMA,
            "stages": [stage.to_dict() for stage in STAGES],
        }


@dataclass(frozen=True)
class CommandResult:
    command_id: str
    succeeded: bool
    failure_code: Optional[str] = None


class AttemptState:
    def __init__(self, attempt_id: str):
        if not COMMAND_ID_RE.fullmatch(attempt_id):
            raise StateMachineError("invalid attempt id")
        self.attempt_id = attempt_id
        self.status = "ready"
        self.completed_stage_ids: List[str] = []
        self.first_failure: Optional[Dict[str, object]] = None

    @property
    def next_stage(self) -> Optional[Stage]:
        ordinal = len(self.completed_stage_ids)
        return STAGES[ordinal] if ordinal < len(STAGES) else None

    def record_stage(self, stage_id: str, results: Sequence[CommandResult]) -> None:
        if self.status in ("failed", "complete"):
            raise StateMachineError("attempt is terminal")
        expected = self.next_stage
        if expected is None or stage_id != expected.stage_id:
            raise StateMachineError("stage skip or replay")
        seen = set()
        for result in results:
            if result.command_id in seen:
                raise StateMachineError("duplicate command result")
            seen.add(result.command_id)
            if not result.succeeded:
                self.status = "failed"
                self.first_failure = {
                    "command_id": result.command_id,
                    "failure_code": result.failure_code or "UnspecifiedFailure",
                    "stage_id": stage_id,
                }
                return
        self.completed_stage_ids.append(stage_id)
        self.status = "complete" if self.next_stage is None else "running"

    def to_dict(self) -> Dict[str, object]:
        if self.status not in STATE_STATUSES:
            raise StateMachineError("invalid state status")
        return {
            "attempt_id": self.attempt_id,
            "completed_stage_ids": list(self.completed_stage_ids),
            "first_failure": self.first_failure,
            "next_stage_id": self.next_stage.stage_id if self.next_stage else None,
            "schema": STATE_SCHEMA,
            "status": self.status,
        }


def execute_stage(
    plan: ExecutionPlan,
    state: AttemptState,
    stage_id: str,
    producer: Callable[[CommandSpec], CommandResult],
) -> None:
    """Execute one exact stage and stop invoking producers at first failure."""
    plan.validate()
    expected = state.next_stage
    if expected is None or expected.stage_id != stage_id:
        raise StateMachineError("stage skip or replay")
    commands = [command for command in plan.commands if command.stage_id == stage_id]
    results = []
    for command in commands:
        try:
            result = producer(command)
        except BaseException as error:
            result = CommandResult(
                command.command_id,
                False,
                "ProducerException:{}".format(error.__class__.__name__),
            )
        if result.command_id != command.command_id:
            raise StateMachineError("producer returned the wrong command id")
        results.append(result)
        if not result.succeeded:
            break
    state.record_stage(stage_id, results)


class BoundedRunnerAdapter:
    """Invoke the committed bounded runner and accept one exact status."""

    def __init__(self, python_path: str, runner_path: str):
        if not os.path.isabs(python_path) or not os.path.isabs(runner_path):
            raise StateMachineError("adapter paths must be absolute")
        self.python_path = python_path
        self.runner_path = runner_path

    def __call__(self, command: CommandSpec) -> CommandResult:
        try:
            command.validate()
            for path in command.output_paths:
                if os.path.lexists(path):
                    return CommandResult(command.command_id, False, "OutputPathAlreadyExists")
            argv = [
                self.python_path,
                self.runner_path,
                "run-v1",
                "--timeout-seconds",
                str(command.timeout_seconds),
                "--stdout-cap",
                str(command.stdout_cap),
                "--stderr-cap",
                str(command.stderr_cap),
                "--status-path",
                command.status_path,
                "--stdout-path",
                command.stdout_path,
                "--stderr-path",
                command.stderr_path,
                "--",
            ] + list(command.argv)
            completed = subprocess.run(
                argv,
                cwd=command.cwd,
                env={key: value for key, value in command.env},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if completed.returncode != 0:
                return CommandResult(command.command_id, False, "BoundedRunnerInvocationFailed")
            status = self._read_status(command)
            if status["argv"] != list(command.argv):
                return CommandResult(command.command_id, False, "BoundedStatusArgvDrift")
            if status["reason"] != command.expected_reason:
                return CommandResult(command.command_id, False, "BoundedStatusReasonDrift")
            if status["returncode"] != command.expected_returncode:
                return CommandResult(command.command_id, False, "BoundedStatusReturncodeDrift")
            if status["signal"] != command.expected_signal:
                return CommandResult(command.command_id, False, "BoundedStatusSignalDrift")
            if status["stdout_cap"] != command.stdout_cap or status["stderr_cap"] != command.stderr_cap:
                return CommandResult(command.command_id, False, "BoundedStatusCapDrift")
            if status["stdout_bytes"] > command.stdout_cap or status["stderr_bytes"] > command.stderr_cap:
                return CommandResult(command.command_id, False, "BoundedStatusByteCountDrift")
            if (
                os.stat(command.stdout_path).st_size != status["stdout_bytes"]
                or os.stat(command.stderr_path).st_size != status["stderr_bytes"]
            ):
                return CommandResult(command.command_id, False, "BoundedStreamSizeDrift")
            return CommandResult(command.command_id, True)
        except (OSError, StateMachineError):
            return CommandResult(command.command_id, False, "BoundedStatusInvalid")

    def _read_status(self, command: CommandSpec) -> Mapping[str, object]:
        expected_keys = {
            "argv",
            "elapsed_ms",
            "reason",
            "returncode",
            "schema",
            "signal",
            "stderr_bytes",
            "stderr_cap",
            "stdout_bytes",
            "stdout_cap",
        }
        for path in command.output_paths:
            path_stat = os.lstat(path)
            if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISREG(path_stat.st_mode):
                raise StateMachineError("bounded output is not a regular file")
        value = load_canonical_json(pathlib.Path(command.status_path).read_bytes())
        if not isinstance(value, dict) or set(value) != expected_keys:
            raise StateMachineError("bounded status shape drift")
        if value["schema"] != "hsai-bounded-runner-status-v1":
            raise StateMachineError("bounded status schema drift")
        integer_fields = (
            "elapsed_ms",
            "stderr_bytes",
            "stderr_cap",
            "stdout_bytes",
            "stdout_cap",
        )
        if any(
            not isinstance(value[field], int)
            or isinstance(value[field], bool)
            or value[field] < 0
            for field in integer_fields
        ):
            raise StateMachineError("bounded status numeric drift")
        return value


@dataclass(frozen=True)
class OperationSpec:
    operation_id: str
    stage_id: str
    predecessor: Optional[str]
    mutation_owner: str
    network_policy: str
    kind: str
    payload: Tuple[Tuple[str, str], ...]

    def validate(self) -> None:
        if not COMMAND_ID_RE.fullmatch(self.operation_id):
            raise StateMachineError("invalid operation id")
        stage = STAGE_BY_ID.get(self.stage_id)
        if stage is None:
            raise StateMachineError("unknown operation stage")
        if self.mutation_owner != stage.mutation_owner:
            raise StateMachineError("operation mutation owner differs from stage")
        if self.network_policy != stage.network_policy:
            raise StateMachineError("operation network policy differs from stage")
        if self.kind not in OPERATION_KINDS:
            raise StateMachineError("unknown operation kind")
        keys = [key for key, _ in self.payload]
        if (
            len(keys) != len(set(keys))
            or any(not key for key in keys)
            or any(not isinstance(value, str) or "\x00" in value or "\n" in value for _, value in self.payload)
        ):
            raise StateMachineError("invalid operation payload keys")
        values = dict(self.payload)
        if not CONTRACT_REF_RE.fullmatch(values.get("contract_ref", "")):
            raise StateMachineError("operation lacks a contract reference")
        if any(shell in value for value in values.values() for shell in ("/bin/sh", "/bin/bash", "/bin/zsh")):
            raise StateMachineError("operation payload contains hidden shell text")
        if self.kind == "internal-assertion":
            required = {"contract_ref"}
        elif self.kind == "atomic-materialization":
            required = {"contract_ref", "target_template"}
            if values.get("target_template") != "{{RUN}}/operations/{}".format(self.operation_id):
                raise StateMachineError("materialization target drift")
        elif self.kind == "bounded-producer":
            required = {"command_id", "contract_ref"}
            if values.get("command_id") != self.operation_id:
                raise StateMachineError("bounded command identity drift")
        elif self.kind == "persistent-loopback-control":
            required = {
                "contract_ref",
                "listener_sha256",
                "positive_argv",
                "sandboxed_negative_argv",
            }
            if not SHA256_RE.fullmatch(values.get("listener_sha256", "")):
                raise StateMachineError("loopback listener identity drift")
            try:
                positive = json.loads(values["positive_argv"])
                negative = json.loads(values["sandboxed_negative_argv"])
            except (KeyError, json.JSONDecodeError) as error:
                raise StateMachineError("loopback argv is invalid JSON") from error
            if positive != ["/usr/bin/nc", "-G", "2", "-z", "127.0.0.1", "{PORT}"]:
                raise StateMachineError("loopback positive argv drift")
            if negative != ["/usr/bin/sandbox-exec", "-f", "{SANDBOX_PROFILE}"] + positive:
                raise StateMachineError("loopback probe argv is not byte-identical")
        else:
            required = {"contract_ref", "roots", "verify_primary"}
            expected_roots = (
                "{RUN},{DETACHED_REPO},{RUSTUP_ROOT},{CHARON_CARGO_HOME},"
                "{AENEAS_ROOT},{LEAN_ROOT}"
            )
            if values.get("verify_primary") != "true" or values.get("roots") != expected_roots:
                raise StateMachineError("cleanup contract drift")
        if set(values) != required:
            raise StateMachineError("operation payload shape drift")

    def to_dict(self) -> Dict[str, object]:
        self.validate()
        return {
            "kind": self.kind,
            "mutation_owner": self.mutation_owner,
            "network_policy": self.network_policy,
            "operation_id": self.operation_id,
            "payload": dict(self.payload),
            "predecessor": self.predecessor,
            "stage_id": self.stage_id,
        }


@dataclass(frozen=True)
class CompleteOperationPlan:
    attempt_id: str
    operations: Tuple[OperationSpec, ...]

    def validate(self) -> None:
        if not COMMAND_ID_RE.fullmatch(self.attempt_id):
            raise StateMachineError("invalid operation-plan attempt id")
        if not self.operations:
            raise StateMachineError("operation plan is empty")
        ids = [operation.operation_id for operation in self.operations]
        if len(ids) != len(set(ids)):
            raise StateMachineError("duplicate operation id")
        seen_stages = set()
        previous = None
        previous_ordinal = -1
        for operation in self.operations:
            operation.validate()
            if operation.predecessor != previous:
                raise StateMachineError("operation predecessor gap")
            ordinal = STAGE_BY_ID[operation.stage_id].ordinal
            if ordinal < previous_ordinal:
                raise StateMachineError("operation stage order drift")
            previous_ordinal = ordinal
            previous = operation.operation_id
            seen_stages.add(operation.stage_id)
        if seen_stages != set(STAGE_BY_ID):
            raise StateMachineError("one or more stages are empty")
        if self.operations[-1].kind != "cleanup-and-verify":
            raise StateMachineError("cleanup must be the final operation")
        if any(operation.kind == "cleanup-and-verify" for operation in self.operations[:-1]):
            raise StateMachineError("cleanup appears before the final operation")

    def to_dict(self) -> Dict[str, object]:
        self.validate()
        return {
            "attempt_id": self.attempt_id,
            "operations": [operation.to_dict() for operation in self.operations],
            "schema": COMPLETE_PLAN_SCHEMA,
        }

    def sha256(self) -> str:
        return hashlib.sha256(canonical_json_line(self.to_dict())).hexdigest()


class OperationAttemptState:
    def __init__(self, plan: CompleteOperationPlan):
        plan.validate()
        self.plan = plan
        self.completed: List[str] = []
        self.first_failure: Optional[Dict[str, str]] = None
        self.status = "running"

    @property
    def cleanup(self) -> OperationSpec:
        return self.plan.operations[-1]

    @property
    def next_operation(self) -> Optional[OperationSpec]:
        if self.status in ("complete", "failed-cleaned", "cleanup-failed"):
            return None
        if self.first_failure is not None:
            return self.cleanup
        return self.plan.operations[len(self.completed)]

    def record(self, operation_id: str, succeeded: bool, failure_code: str = "") -> None:
        expected = self.next_operation
        if expected is None or expected.operation_id != operation_id:
            raise StateMachineError("operation skip, replay, or post-terminal transition")
        if not succeeded:
            if expected.kind == "cleanup-and-verify":
                self.status = "cleanup-failed"
            else:
                self.first_failure = {
                    "failure_code": failure_code or "UnspecifiedFailure",
                    "operation_id": operation_id,
                }
            return
        self.completed.append(operation_id)
        if expected.kind == "cleanup-and-verify":
            self.status = "failed-cleaned" if self.first_failure else "complete"


def _payload(**values: str) -> Tuple[Tuple[str, str], ...]:
    return tuple(sorted(values.items()))


def build_complete_operation_plan(attempt_id: str = "phase770-plan") -> CompleteOperationPlan:
    """Build the path-normalized complete inherited operation inventory."""
    rows = (
        ("snapshot-primary", "primary-preservation", "internal-assertion", "phase753-primary-snapshot"),
        ("create-owned-roots", "primary-preservation", "atomic-materialization", "phase744-owned-roots"),
        ("verify-frozen-repository", "frozen-identities", "internal-assertion", "phase668-source-and-lock-pins"),
        ("verify-helper-identities", "frozen-identities", "internal-assertion", "phase749-helper-hashes"),
        ("compile-helper-sources", "helper-self-tests", "bounded-producer", "phase749-py-compile"),
        ("run-helper-tests", "helper-self-tests", "bounded-producer", "phase749-focused-tests"),
        ("run-raw-parser-self-test", "helper-self-tests", "bounded-producer", "phase761-bounded-self-test"),
        ("accept-raw-parser-self-test", "helper-self-tests", "internal-assertion", "phase761-self-test-acceptance"),
        ("materialize-client-metadata", "client-and-fixtures", "atomic-materialization", "phase702-client-bytes"),
        ("fixture-normal-exit", "client-and-fixtures", "bounded-producer", "phase732-fixture-1"),
        ("fixture-process-timeout", "client-and-fixtures", "bounded-producer", "phase732-fixture-2"),
        ("fixture-stdout-limit", "client-and-fixtures", "bounded-producer", "phase732-fixture-3"),
        ("fixture-stderr-limit", "client-and-fixtures", "bounded-producer", "phase732-fixture-4"),
        ("validate-process-fixtures", "client-and-fixtures", "bounded-producer", "phase749-fixture-validator"),
        ("download-rust-manifest", "rust-acquisition", "bounded-producer", "phase744-rust-manifest"),
        ("verify-rust-manifest", "rust-acquisition", "internal-assertion", "phase744-rust-manifest-pin"),
        ("install-rust-toolchain", "rust-acquisition", "bounded-producer", "phase751-exact-toolchain-token"),
        ("capture-rust-identities", "rust-acquisition", "bounded-producer", "phase728-six-identity-transcripts"),
        ("accept-rust-identities", "rust-acquisition", "internal-assertion", "phase763-marked-components"),
        ("initialize-charon-source", "charon-source", "bounded-producer", "phase744-charon-init"),
        ("fetch-charon-source", "charon-source", "bounded-producer", "phase755-charon-commit"),
        ("checkout-charon-source", "charon-source", "bounded-producer", "phase755-detached-checkout"),
        ("assert-charon-head", "charon-source", "internal-assertion", "phase757-independent-head"),
        ("assert-charon-status", "charon-source", "internal-assertion", "phase757-independent-status"),
        ("assert-charon-paths", "charon-source", "internal-assertion", "phase755-five-regular-paths"),
        ("hash-charon-paths", "charon-source", "bounded-producer", "phase757-five-independent-hashes"),
        ("assert-charon-license-absence", "charon-source", "internal-assertion", "phase757-license-absence"),
        ("assert-charon-stability", "charon-source", "internal-assertion", "phase757-final-stability"),
        ("download-aeneas-main", "aeneas-assets", "bounded-producer", "phase741-main-asset"),
        ("download-aeneas-lean", "aeneas-assets", "bounded-producer", "phase741-lean-asset"),
        ("verify-aeneas-assets", "aeneas-assets", "internal-assertion", "phase742-asset-pins"),
        ("validate-aeneas-archives", "aeneas-assets", "bounded-producer", "phase742-raw-archive-profile"),
        ("extract-aeneas-main", "archive-equivalence", "bounded-producer", "phase726-main-extraction"),
        ("extract-aeneas-lean-staging", "archive-equivalence", "bounded-producer", "phase726-lean-extraction"),
        ("assert-lean-tree-equivalence", "archive-equivalence", "internal-assertion", "phase744-lean-tree-equivalence"),
        ("remove-lean-staging", "archive-equivalence", "atomic-materialization", "phase744-remove-duplicate-staging"),
        ("download-lean", "lean-acquisition", "bounded-producer", "phase668-lean-4-31-asset"),
        ("verify-lean-archive", "lean-acquisition", "internal-assertion", "phase668-lean-size-sha"),
        ("extract-lean", "lean-acquisition", "bounded-producer", "phase744-lean-extraction"),
        ("accept-lean-identities", "lean-acquisition", "internal-assertion", "phase692-lean-lake-identities"),
        ("compile-rustc-private-probe", "dependency-freeze", "bounded-producer", "phase678-rustc-private-probe"),
        ("fetch-charon-dependencies", "dependency-freeze", "bounded-producer", "phase678-locked-cargo-fetch"),
        ("lake-update", "dependency-freeze", "bounded-producer", "phase678-client-lake-update"),
        ("lake-cache-get", "dependency-freeze", "bounded-producer", "phase678-client-cache-get"),
        ("freeze-dependencies", "dependency-freeze", "internal-assertion", "phase678-nine-package-freeze"),
        ("materialize-sandbox-profile", "sandboxed-backends", "atomic-materialization", "phase672-deny-network-profile"),
        ("materialize-loopback-listener", "sandboxed-backends", "atomic-materialization", "phase732-listener-bytes"),
        ("run-loopback-control", "sandboxed-backends", "persistent-loopback-control", "phase732-loopback-lifetime"),
        ("run-sandbox-controls", "sandboxed-backends", "bounded-producer", "phase678-network-denial-controls"),
        ("build-charon", "sandboxed-backends", "bounded-producer", "phase678-sandboxed-charon-build"),
        ("verify-charon-binaries", "sandboxed-backends", "internal-assertion", "phase678-charon-version-and-driver"),
        ("freeze-checker-cargo-cache", "sandboxed-backends", "internal-assertion", "phase678-checker-cache-digest"),
        ("extract-checker-llbc", "sandboxed-backends", "bounded-producer", "phase668-charon-cargo-extraction"),
        ("pretty-print-checker-llbc", "sandboxed-backends", "bounded-producer", "phase668-charon-pretty-print"),
        ("assert-single-ordinal-body", "sandboxed-backends", "internal-assertion", "phase668-target-selector"),
        ("generate-aeneas-lean", "sandboxed-backends", "bounded-producer", "phase678-aeneas-generation"),
        ("assert-generated-source", "sandboxed-backends", "internal-assertion", "phase678-generated-source-review"),
        ("materialize-rfl-witness", "sandboxed-backends", "atomic-materialization", "phase724-fourteen-rfl-witness"),
        ("check-types-olean", "sandboxed-backends", "bounded-producer", "phase720-types-olean"),
        ("check-funs-olean", "sandboxed-backends", "bounded-producer", "phase720-funs-olean"),
        ("check-witness-olean", "sandboxed-backends", "bounded-producer", "phase720-witness-olean"),
        ("lake-build", "sandboxed-backends", "bounded-producer", "phase678-final-lake-build"),
        ("assert-final-freeze", "sandboxed-backends", "internal-assertion", "phase678-final-state-freeze"),
        ("retain-path-free-proof-slice", "retention-and-cleanup", "atomic-materialization", "phase678-success-retention"),
        ("cleanup-and-verify-primary", "retention-and-cleanup", "cleanup-and-verify", "phase753-cleanup-preservation"),
    )
    operations = []
    predecessor = None
    for operation_id, stage_id, kind, contract_ref in rows:
        stage = STAGE_BY_ID[stage_id]
        values = {"contract_ref": contract_ref}
        if kind == "atomic-materialization":
            values["target_template"] = "{{RUN}}/operations/{}".format(operation_id)
        elif kind == "bounded-producer":
            values["command_id"] = operation_id
        elif kind == "persistent-loopback-control":
            positive = ["/usr/bin/nc", "-G", "2", "-z", "127.0.0.1", "{PORT}"]
            values.update(
                {
                    "listener_sha256": "31dbedb07e9a75a3d70ed8b3a070d3e394137aa698c1ef1295d3f13e5c525b8d",
                    "positive_argv": json.dumps(positive, separators=(",", ":")),
                    "sandboxed_negative_argv": json.dumps(
                        ["/usr/bin/sandbox-exec", "-f", "{SANDBOX_PROFILE}"] + positive,
                        separators=(",", ":"),
                    ),
                }
            )
        elif kind == "cleanup-and-verify":
            values.update(
                {
                    "roots": "{RUN},{DETACHED_REPO},{RUSTUP_ROOT},{CHARON_CARGO_HOME},{AENEAS_ROOT},{LEAN_ROOT}",
                    "verify_primary": "true",
                }
            )
        operation = OperationSpec(
            operation_id,
            stage_id,
            predecessor,
            stage.mutation_owner,
            stage.network_policy,
            kind,
            _payload(**values),
        )
        operations.append(operation)
        predecessor = operation_id
    plan = CompleteOperationPlan(attempt_id, tuple(operations))
    plan.validate()
    return plan


def _git(repo_root: pathlib.Path, arguments: Sequence[str]) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo_root)] + list(arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise StateMachineError(
            "git command failed: {}".format(completed.stderr.decode("utf-8", "replace").strip())
        )
    return completed.stdout


def _porcelain_paths(raw: bytes) -> List[str]:
    if not raw.endswith(b"\x00") and raw:
        raise StateMachineError("porcelain output is not NUL terminated")
    paths = []
    for entry in raw.split(b"\x00")[:-1]:
        if len(entry) < 4 or entry[2:3] != b" ":
            raise StateMachineError("invalid porcelain entry")
        status = entry[:2].decode("ascii")
        if "R" in status or "C" in status:
            raise StateMachineError("rename/copy status is unsupported")
        try:
            path = entry[3:].decode("utf-8")
        except UnicodeDecodeError as error:
            raise StateMachineError("non-UTF-8 primary path") from error
        paths.append(path)
    return paths


def _sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_primary(repo_root: pathlib.Path) -> Dict[str, object]:
    root = repo_root.resolve(strict=True)
    head = _git(root, ("rev-parse", "HEAD")).decode("ascii").strip()
    raw = _git(root, ("status", "--porcelain=v1", "-z", "--untracked-files=all"))
    files = {}
    for relative in sorted(set(_porcelain_paths(raw))):
        path = root / relative
        if path.is_file() and not path.is_symlink():
            files[relative] = _sha256_file(path)
    return {
        "files": files,
        "head": head,
        "porcelain_v1_z_base64": base64.b64encode(raw).decode("ascii"),
        "schema": SNAPSHOT_SCHEMA,
    }


def verify_primary(repo_root: pathlib.Path, snapshot: Mapping[str, object]) -> None:
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise StateMachineError("invalid snapshot schema")
    observed = snapshot_primary(repo_root)
    if observed != dict(snapshot):
        raise StateMachineError("primary checkout changed")


def _write_stdout(value: object) -> None:
    sys.stdout.buffer.write(canonical_json_line(value))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan-v1", allow_abbrev=False)
    plan.add_argument("--attempt-id", required=True)
    snapshot = subparsers.add_parser("snapshot-v1", allow_abbrev=False)
    snapshot.add_argument("--repo-root", required=True)
    verify = subparsers.add_parser("verify-snapshot-v1", allow_abbrev=False)
    verify.add_argument("--repo-root", required=True)
    verify.add_argument("--snapshot", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan-v1":
            _write_stdout(ExecutionPlan(args.attempt_id, ()).to_dict())
        elif args.command == "snapshot-v1":
            _write_stdout(snapshot_primary(pathlib.Path(args.repo_root)))
        else:
            raw = pathlib.Path(args.snapshot).read_bytes()
            value = load_canonical_json(raw)
            if not isinstance(value, dict):
                raise StateMachineError("snapshot must be a JSON object")
            verify_primary(pathlib.Path(args.repo_root), value)
            _write_stdout({"schema": "hsai-primary-snapshot-verification-v1", "verified": True})
    except (OSError, StateMachineError) as error:
        sys.stderr.buffer.write(
            canonical_json_line(
                {
                    "code": error.__class__.__name__,
                    "detail": str(error),
                    "schema": "hsai-formal-execution-state-machine-error-v1",
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
