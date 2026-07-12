# Phase 732 HSAI Gateway Threat Ordinal Exact Fixture And Loopback Closure

## Status

Complete as a documentation-first fixture and sandbox-command correction.

State slice:
`phase-732-hsai-gateway-threat-ordinal-exact-fixture-and-loopback-closure`.

Classification: `ExactRunnerAndLoopbackControlsSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Canonical Attempt Identity

Phase 733 uses canonical run root `hsai-phase733-efa3782c`, canonical detached
repository root `hsai-phase733-repo-efa3782c`, and witness
`phase733ExtractedThreatOrdinalWitnesses`.

## Exact Runner Fixtures

Immediately after canonical client hashes, only these four bounded-runner
producers may execute, in this order. `RUN` must be exported as the exact
canonical run root before the fixture subprocesses start:

1. `/bin/echo ok`, with five seconds and 1,024 bytes per stream;
2. `/bin/sh -c '/bin/sh -c "/bin/sleep 30" & child=$!; printf "%s\n" "$child" > "$RUN/grandchild.pid"; wait "$child"'`, with one second and 1,024 bytes per stream;
3. `/usr/bin/yes x`, with five seconds and 1,024 bytes per stream; and
4. `/bin/sh -c 'exec /usr/bin/yes x >&2'`, with five seconds and 1,024 bytes per stream.

One validator must then require `ok\n`, timeout/process-group termination,
the recorded grandchild PID no longer live, `stdout_limit` with exactly 1,024
stdout bytes, and `stderr_limit` with exactly 1,024 stderr bytes. It must hash
the runner, host Python binary, exact command records, statuses, and retained
streams. Alternate producers, caps, wrappers, description loops, parser probes,
dry runs, or unused commands stop the attempt before acquisition.

## Exact Loopback Control

After all network acquisition and immediately before sandbox controls, Phase
733 must materialize `loopback_listener.py` under the run root with SHA-256
`31dbedb07e9a75a3d70ed8b3a070d3e394137aa698c1ef1295d3f13e5c525b8d`
and this exact content:

```python
#!/usr/bin/python3
import os
import socket
import sys
import time

if len(sys.argv) != 2:
    sys.exit(64)

port_path = sys.argv[1]
deadline = time.monotonic() + 30.0
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(2)
    listener.settimeout(0.25)
    fd = os.open(port_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as out:
        out.write(f"{listener.getsockname()[1]}\n")
        out.flush()
        os.fsync(out.fileno())
    accepted = 0
    while time.monotonic() < deadline:
        try:
            connection, _ = listener.accept()
        except socket.timeout:
            continue
        with connection:
            pass
        accepted += 1
        if accepted > 1:
            sys.exit(65)
sys.exit(124)
```

The exact listener argv is host `/usr/bin/python3`, the pinned script path, and
the absent run-local `loopback-port.txt` path. Stdout and stderr go to separate
run-local regular files capped at 1,024 bytes. After a bounded readiness wait,
the port file must contain one decimal port in `1..65535` and have mode `0600`.

The exact connection argv is:

```text
/usr/bin/nc -G 2 -z 127.0.0.1 PORT
```

The expanded six-element argv must be recorded once. It must exit zero
unsandboxed, then the byte-identical argv must exit nonzero under the pinned
deny-network profile. The listener must remain live between those commands,
must accept exactly the positive control, and must then be terminated and
reaped. A second accepted connection, listener timeout, changed argv, missing
port file, failed positive control, sandboxed success, output overflow, or
unreaped listener stops before Charon build. The inherited sandboxed
`/usr/bin/true`, hostname, and direct-IP controls remain mandatory; their
diagnostic text is informational.

After commit and detached-worktree gates, Phase 733 may make one attempt. Every
identity, independent acquisition/materialization, exact version, token,
client, scanner, component, source, cache, rfl witness, direct `.olean`, cleanup,
evidence, and claim rule remains.

Phase 732 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
