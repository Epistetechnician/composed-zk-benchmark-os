#!/usr/bin/python3
"""Validate the four canonical Phase 732 bounded-runner fixtures."""

import argparse
import base64
import binascii
import json
import os
import signal
import sys


INPUT_SCHEMA = "hsai-fixture-validation-input-v1"
OUTPUT_SCHEMA = "hsai-fixture-validation-v1"
ERROR_SCHEMA = "hsai-fixture-validation-error-v1"
STATUS_SCHEMA = "hsai-bounded-runner-status-v1"
MAX_INPUT_BYTES = 64 * 1024

STATUS_KEYS = {
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
FIXTURE_KEYS = {"name", "status", "stderr_base64", "stdout_base64", "timeout_seconds"}
INPUT_KEYS = {"fixtures", "grandchild_pid", "schema"}

TIMEOUT_COMMAND = (
    '/bin/sh -c "/bin/sleep 30" & child=$!; printf "%s\\n" "$child" '
    '> "$RUN/grandchild.pid"; wait "$child"'
)
FIXTURES = (
    ("normal_exit", ["/bin/echo", "ok"], 5, "exit", b"ok\n", b""),
    ("process_group_timeout", ["/bin/sh", "-c", TIMEOUT_COMMAND], 1, "timeout", b"", b""),
    ("stdout_limit", ["/usr/bin/yes", "x"], 5, "stdout_limit", b"x\n" * 512, b""),
    (
        "stderr_limit",
        ["/bin/sh", "-c", "exec /usr/bin/yes x >&2"],
        5,
        "stderr_limit",
        b"",
        b"x\n" * 512,
    ),
)


class ValidationError(Exception):
    """A bounded, user-facing fixture validation failure."""


def canonical_json(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError("duplicate JSON key")
        result[key] = value
    return result


def require_exact_keys(value, expected, label):
    if not isinstance(value, dict):
        raise ValidationError("{0} must be an object".format(label))
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValidationError(
            "{0} keys differ: missing={1}, extra={2}".format(label, missing, extra)
        )


def require_plain_int(value, label, minimum=None):
    if type(value) is not int:  # bool is intentionally excluded.
        raise ValidationError("{0} must be an integer".format(label))
    if minimum is not None and value < minimum:
        raise ValidationError("{0} must be at least {1}".format(label, minimum))


def decode_stream(encoded, label):
    if not isinstance(encoded, str) or not encoded.isascii():
        raise ValidationError("{0} must be an ASCII base64 string".format(label))
    try:
        decoded = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError("{0} is not canonical base64".format(label))
    if base64.b64encode(decoded).decode("ascii") != encoded:
        raise ValidationError("{0} is not canonical base64".format(label))
    return decoded


def pid_is_live(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def validate_status(status, expected_argv, expected_reason, stdout, stderr, label):
    require_exact_keys(status, STATUS_KEYS, label + ".status")
    if status["schema"] != STATUS_SCHEMA:
        raise ValidationError("{0}.status schema differs".format(label))
    if status["argv"] != expected_argv:
        raise ValidationError("{0}.status argv differs".format(label))
    if status["reason"] != expected_reason:
        raise ValidationError("{0}.status reason differs".format(label))

    for field in ("elapsed_ms", "stdout_bytes", "stdout_cap", "stderr_bytes", "stderr_cap"):
        require_plain_int(status[field], label + ".status." + field, 0)
    if status["stdout_cap"] != 1024 or status["stderr_cap"] != 1024:
        raise ValidationError("{0}.status stream caps must both equal 1024".format(label))
    if status["stdout_bytes"] != len(stdout) or status["stderr_bytes"] != len(stderr):
        raise ValidationError("{0}.status retained byte count differs".format(label))

    returncode = status["returncode"]
    status_signal = status["signal"]
    if status_signal is not None:
        require_plain_int(status_signal, label + ".status.signal", 1)

    if expected_reason == "exit":
        if type(returncode) is not int or returncode != 0 or status_signal is not None:
            raise ValidationError("{0}.status must record a clean exit".format(label))
    else:
        if returncode is not None:
            raise ValidationError("{0}.status returncode must be null after signal termination".format(label))
        if status_signal not in (signal.SIGTERM, signal.SIGKILL):
            raise ValidationError("{0}.status termination signal differs".format(label))


def validate_document(document):
    require_exact_keys(document, INPUT_KEYS, "input")
    if document["schema"] != INPUT_SCHEMA:
        raise ValidationError("input schema differs")
    fixtures = document["fixtures"]
    if not isinstance(fixtures, list) or len(fixtures) != len(FIXTURES):
        raise ValidationError("input must contain exactly four fixtures")

    for index, expected in enumerate(FIXTURES):
        name, argv, timeout, reason, expected_stdout, expected_stderr = expected
        fixture = fixtures[index]
        label = "fixtures[{0}]".format(index)
        require_exact_keys(fixture, FIXTURE_KEYS, label)
        if fixture["name"] != name:
            raise ValidationError("{0}.name differs".format(label))
        if fixture["timeout_seconds"] != timeout or type(fixture["timeout_seconds"]) is not int:
            raise ValidationError("{0}.timeout_seconds differs".format(label))
        stdout = decode_stream(fixture["stdout_base64"], label + ".stdout_base64")
        stderr = decode_stream(fixture["stderr_base64"], label + ".stderr_base64")
        if stdout != expected_stdout or stderr != expected_stderr:
            raise ValidationError("{0} retained stream content differs".format(label))
        validate_status(fixture["status"], argv, reason, stdout, stderr, label)

    grandchild_pid = document["grandchild_pid"]
    if not isinstance(grandchild_pid, str) or not grandchild_pid.isascii():
        raise ValidationError("grandchild_pid must be an ASCII decimal string")
    if not grandchild_pid.isdecimal() or grandchild_pid.startswith("0"):
        raise ValidationError("grandchild_pid must be a positive canonical decimal PID")
    pid = int(grandchild_pid, 10)
    if pid <= 0:
        raise ValidationError("grandchild_pid must be positive")
    if pid_is_live(pid):
        raise ValidationError("recorded grandchild PID is still live")

    return {
        "fixtures_validated": len(FIXTURES),
        "grandchild_dead": True,
        "ordered_fixtures": [fixture[0] for fixture in FIXTURES],
        "schema": OUTPUT_SCHEMA,
    }


def load_canonical_document(path):
    try:
        with open(path, "rb") as input_file:
            raw = input_file.read(MAX_INPUT_BYTES + 1)
    except (OSError, IOError) as error:
        raise ValidationError("cannot read input: {0}".format(error.strerror or "I/O error"))
    if len(raw) > MAX_INPUT_BYTES:
        raise ValidationError("input exceeds 65536 bytes")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise ValidationError("input must be ASCII JSON")
    try:
        document = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except ValidationError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError):
        raise ValidationError("input is not valid JSON")
    if text != canonical_json(document):
        raise ValidationError("input is not canonical single-line JSON")
    return document


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate canonical Phase 732 fixtures")
    validate.add_argument("--input", required=True, help="canonical fixture input JSON path")
    return parser


def main(argv=None):
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command != "validate":
            raise ValidationError("unsupported command")
        summary = validate_document(load_canonical_document(arguments.input))
    except ValidationError as error:
        sys.stderr.write(canonical_json({"error": str(error), "schema": ERROR_SCHEMA}))
        return 1
    sys.stdout.write(canonical_json(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
