#!/usr/bin/env python3
"""Run one command with bounded time, output, and process-group lifetime."""

import argparse
import errno
import json
import math
import os
import selectors
import signal
import stat
import subprocess
import sys
import time
from typing import BinaryIO, Dict, List, Optional, Sequence, Tuple


STATUS_SCHEMA = "hsai-bounded-runner-status-v1"
TERMINATION_GRACE_SECONDS = 2.0
READ_CHUNK_BYTES = 65536


class RunnerError(Exception):
    """A bounded-runner invocation could not be completed safely."""


def _canonical_json_line(value: object) -> bytes:
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


def _exclusive_regular_file(path: str) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise RunnerError("output is not a regular file: {}".format(path))
    return fd


def _reserve_outputs(paths: Sequence[str]) -> Dict[str, int]:
    absolute = [os.path.abspath(path) for path in paths]
    if len(set(absolute)) != len(absolute):
        raise RunnerError("output paths must be distinct")

    opened: Dict[str, int] = {}
    try:
        for path in paths:
            opened[path] = _exclusive_regular_file(path)
    except BaseException:
        for fd in opened.values():
            os.close(fd)
        for path in opened:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        raise
    return opened


def _group_exists(process_group: int) -> bool:
    try:
        os.killpg(process_group, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _signal_group(process_group: int, signum: int) -> None:
    try:
        os.killpg(process_group, signum)
    except ProcessLookupError:
        pass


def _terminate_process_group(process: subprocess.Popen) -> None:
    process_group = process.pid
    _signal_group(process_group, signal.SIGTERM)
    deadline = time.monotonic() + TERMINATION_GRACE_SECONDS
    while time.monotonic() < deadline:
        process.poll()
        if not _group_exists(process_group):
            break
        time.sleep(0.01)
    if _group_exists(process_group):
        _signal_group(process_group, signal.SIGKILL)
    try:
        process.wait(timeout=TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        _signal_group(process_group, signal.SIGKILL)
        process.wait()


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise RunnerError("short output write")
        view = view[written:]


def _drain_available(
    pipes: Sequence[Tuple[BinaryIO, int, int]],
    retained: Dict[int, int],
) -> None:
    for pipe, output_fd, cap in pipes:
        if pipe.closed:
            continue
        descriptor = pipe.fileno()
        while True:
            remaining = cap - retained[descriptor]
            try:
                chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining + 1))
            except BlockingIOError:
                break
            except OSError as error:
                if error.errno == errno.EBADF:
                    break
                raise
            if not chunk:
                break
            kept = chunk[:remaining]
            if kept:
                _write_all(output_fd, kept)
                retained[descriptor] += len(kept)


def run_bounded(
    argv: Sequence[str],
    timeout_seconds: float,
    stdout_cap: int,
    stderr_cap: int,
    status_path: str,
    stdout_path: str,
    stderr_path: str,
) -> None:
    """Run argv and durably emit bounded streams plus one canonical status."""
    paths = (stdout_path, stderr_path, status_path)
    outputs = _reserve_outputs(paths)
    stdout_fd = outputs[stdout_path]
    stderr_fd = outputs[stderr_path]
    status_fd = outputs[status_path]
    process: Optional[subprocess.Popen] = None

    try:
        started = time.monotonic()
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            close_fds=True,
        )
        if process.stdout is None or process.stderr is None:
            raise RunnerError("failed to create producer pipes")

        stdout_descriptor = process.stdout.fileno()
        stderr_descriptor = process.stderr.fileno()
        pipes = {
            stdout_descriptor: (process.stdout, stdout_fd, stdout_cap, "stdout_limit"),
            stderr_descriptor: (process.stderr, stderr_fd, stderr_cap, "stderr_limit"),
        }
        retained = {descriptor: 0 for descriptor in pipes}
        selector = selectors.DefaultSelector()
        for descriptor in pipes:
            os.set_blocking(descriptor, False)
            selector.register(descriptor, selectors.EVENT_READ)

        reason: Optional[str] = None
        deadline = started + timeout_seconds
        while selector.get_map():
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                reason = "timeout"
                break
            events = selector.select(remaining_time)
            if not events:
                reason = "timeout"
                break
            for key, _ in events:
                descriptor = key.fd
                pipe, output_fd, cap, limit_reason = pipes[descriptor]
                remaining = cap - retained[descriptor]
                try:
                    chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining + 1))
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(descriptor)
                    pipe.close()
                    continue
                kept = chunk[:remaining]
                if kept:
                    _write_all(output_fd, kept)
                    retained[descriptor] += len(kept)
                if len(chunk) > remaining:
                    reason = limit_reason
                    break
            if reason is not None:
                break

        selector.close()
        if reason is not None:
            _terminate_process_group(process)
            _drain_available(
                (
                    (process.stdout, stdout_fd, stdout_cap),
                    (process.stderr, stderr_fd, stderr_cap),
                ),
                retained,
            )
        else:
            process.wait()
            reason = "exit"

        returncode_value = process.returncode
        returncode = returncode_value if returncode_value is not None and returncode_value >= 0 else None
        terminating_signal = -returncode_value if returncode_value is not None and returncode_value < 0 else None
        elapsed_ms = int((time.monotonic() - started) * 1000)

        os.fsync(stdout_fd)
        os.fsync(stderr_fd)
        status = {
            "schema": STATUS_SCHEMA,
            "argv": list(argv),
            "reason": reason,
            "returncode": returncode,
            "signal": terminating_signal,
            "elapsed_ms": elapsed_ms,
            "stdout_bytes": retained[stdout_descriptor],
            "stdout_cap": stdout_cap,
            "stderr_bytes": retained[stderr_descriptor],
            "stderr_cap": stderr_cap,
        }
        _write_all(status_fd, _canonical_json_line(status))
        os.fsync(status_fd)

        for directory in sorted({os.path.dirname(os.path.abspath(path)) for path in paths}):
            directory_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except BaseException:
        if process is not None and process.poll() is None:
            _terminate_process_group(process)
        for fd in outputs.values():
            try:
                os.close(fd)
            except OSError:
                pass
        for path in paths:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
        raise
    else:
        for fd in outputs.values():
            os.close(fd)


def _finite_positive(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return parsed


def _nonnegative_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return parsed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run-v1", help="run one bounded producer")
    run_parser.add_argument("--timeout-seconds", required=True, type=_finite_positive)
    run_parser.add_argument("--stdout-cap", required=True, type=_nonnegative_integer)
    run_parser.add_argument("--stderr-cap", required=True, type=_nonnegative_integer)
    run_parser.add_argument("--status-path", required=True)
    run_parser.add_argument("--stdout-path", required=True)
    run_parser.add_argument("--stderr-path", required=True)
    run_parser.add_argument("argv", nargs=argparse.REMAINDER, help="producer argv after --")
    return parser


def main(arguments: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    raw_arguments = list(sys.argv[1:] if arguments is None else arguments)
    help_requested = any(argument in ("-h", "--help") for argument in raw_arguments)
    if "--" not in raw_arguments and not help_requested:
        parser.error("producer argv must follow --")
    options = parser.parse_args(raw_arguments)
    if options.argv and options.argv[0] == "--":
        options.argv = options.argv[1:]
    if not options.argv:
        parser.error("producer argv is required after --")
    try:
        run_bounded(
            argv=options.argv,
            timeout_seconds=options.timeout_seconds,
            stdout_cap=options.stdout_cap,
            stderr_cap=options.stderr_cap,
            status_path=options.status_path,
            stdout_path=options.stdout_path,
            stderr_path=options.stderr_path,
        )
    except (OSError, RunnerError) as error:
        print("bounded_runner.py: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
