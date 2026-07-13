#!/usr/bin/env python3
"""Canonical state and preservation rules for HSAI formal execution."""

import argparse
import base64
import hashlib
import json
import os
import pathlib
import re
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
    output_paths: Tuple[str, ...]

    def validate(self) -> None:
        if not COMMAND_ID_RE.fullmatch(self.command_id):
            raise StateMachineError("invalid command id: {}".format(self.command_id))
        stage = STAGE_BY_ID.get(self.stage_id)
        if stage is None:
            raise StateMachineError("unknown command stage: {}".format(self.stage_id))
        if self.network_policy != stage.network_policy:
            raise StateMachineError("command network policy differs from stage")
        if not self.argv or not os.path.isabs(self.argv[0]):
            raise StateMachineError("command executable must be absolute")
        for argument in self.argv:
            if not isinstance(argument, str) or "\x00" in argument:
                raise StateMachineError("invalid argv value")
        if self.argv[0] in ("/bin/bash", "/bin/sh", "/bin/zsh"):
            raise StateMachineError("shell command execution is prohibited")
        keys = [key for key, _ in self.env]
        if len(keys) != len(set(keys)):
            raise StateMachineError("duplicate environment key")
        for key, value in self.env:
            if not ENV_KEY_RE.fullmatch(key) or key not in ALLOWED_ENV_KEYS:
                raise StateMachineError("unknown environment key: {}".format(key))
            if "\x00" in value:
                raise StateMachineError("invalid environment value")
        absolute_outputs = [os.path.abspath(path) for path in self.output_paths]
        if len(absolute_outputs) != len(set(absolute_outputs)):
            raise StateMachineError("command reuses an output path")

    def to_dict(self) -> Dict[str, object]:
        return {
            "argv": list(self.argv),
            "command_id": self.command_id,
            "env": {key: value for key, value in self.env},
            "network_policy": self.network_policy,
            "output_paths": list(self.output_paths),
            "stage_id": self.stage_id,
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
