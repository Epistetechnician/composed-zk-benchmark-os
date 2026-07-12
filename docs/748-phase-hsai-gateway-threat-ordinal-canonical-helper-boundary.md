# Phase 748 HSAI Gateway Threat Ordinal Canonical Helper Boundary

## Status

Complete as a documentation-first helper-retention boundary.

State slice:
`phase-748-hsai-gateway-threat-ordinal-canonical-helper-boundary`.

Classification: `CanonicalExecutionHelperImplementationSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Authorized Phase 749 Surface

Phase 749 may add only this standard-library Python helper surface:

```text
tools/hsai-formal-preflight/bounded_runner.py
tools/hsai-formal-preflight/raw_archive_validator.py
tools/hsai-formal-preflight/fixture_validator.py
tools/hsai-formal-preflight/tests/test_bounded_runner.py
tools/hsai-formal-preflight/tests/test_raw_archive_validator.py
tools/hsai-formal-preflight/tests/test_fixture_validator.py
```

It may also add one Phase 749 implementation note and the standard mirrors.
No dependency file, package manager, executable shell wrapper, network client,
download command, backend adapter, archive fixture, binary fixture, generated
artifact, or machine path may be committed.

All helpers must run under host `/usr/bin/python3` 3.9.6 using only the Python
standard library. Tests must be hermetic and create all temporary files beneath
test-owned directories.

## Bounded Runner Contract

`bounded_runner.py` must expose one versioned CLI schema with explicit timeout,
stdout cap, stderr cap, status path, stdout path, stderr path, and argv after
`--`. It must use null stdin, `start_new_session=True`, concurrent nonblocking
pipe reads, exact retained-byte caps, process-group `SIGTERM`, a bounded
two-second grace period, and process-group `SIGKILL` fallback.

The status file is canonical single-line duplicate-key-free JSON with sorted
keys and exactly these fields:

```text
schema, argv, reason, returncode, signal, elapsed_ms,
stdout_bytes, stdout_cap, stderr_bytes, stderr_cap
```

`schema` is `hsai-bounded-runner-status-v1`. `reason` is exactly one of
`exit`, `timeout`, `stdout_limit`, or `stderr_limit`. Output and status files
must be absent before invocation and created with exclusive regular-file
writes. The runner exits zero only after it has durably written all three
records; producer success remains represented inside the status record.

Tests must prove normal exit, nonzero exit, complete child/grandchild timeout
termination, exact stdout cap, exact stderr cap, invalid argument rejection,
pre-existing output rejection, and canonical status serialization.

## Raw Archive Validator Contract

`raw_archive_validator.py` must expose `self-test` and `validate` subcommands.
It must use a `TarInfo` subclass that captures raw USTAR name, prefix, and type
bytes before Python normalization, while preserving PAX `path`,
`GNU.sparse.name`, and GNU long-name effective names. UTF-8 decoding is strict.

Only direct `REGTYPE`, `AREGTYPE`, and `DIRTYPE` logical members are accepted.
The validator must reject missing raw metadata, malformed headers, invalid
checksums, unsupported extension semantics, links, devices, FIFOs, contiguous
or sparse members, absolute paths, empty names, repeated separators,
repeated-leading `./`, internal `.` or `..`, invalid trailing separators,
duplicate raw names, duplicate extraction keys, and regular-file ancestors.
Only `.` or `./` directory root markers are permitted, under an exact
profile-specific root count.

Archive inputs must be regular non-symlink descriptors whose device, inode,
size, mtime, and SHA-256 remain stable through validation. Profiles must bind
logical member count, root count, direct type counts, top-level set, and the
Phase 742 inventory digest. The structural inventory algorithm is canonical.
For every logical member, encode this array as compact `ensure_ascii=True`
JSON followed by one LF:

```text
[archive_index, effective_raw_name, collision_key, kind, member_size]
```

`kind` is exactly `regular` or `directory`; a root marker uses collision key
`.`. Sort the complete encoded records by their corresponding tuple and
SHA-256 the concatenation. The inventory deliberately binds archive structure
and order, not uncompressed file contents.

The real validator must also require byte equality between the separate Lean
asset and main member
`backends/lean/.lake/lean-build-aeneas-arm64-apple-darwin24.6.0.tar.gz`.
Success emits one canonical single-line JSON summary with schema
`hsai-raw-archive-validation-v1`; failure emits no stdout and one canonical
single-line JSON error on stderr without a traceback.

The hermetic self-test must name and execute exactly 31 cases covering safe
regular/directory members; both root spellings; every path alias class; raw
and extraction-key duplicates; ancestor collision; symlink, hard-link,
character, block, FIFO, contiguous, sparse, and unknown types; root type/count;
top-level/count drift; PAX path; GNU long name; and malformed checksum/header.
The summary must bind the ordered case names and report 31 passed, zero failed.

## Fixture Validator Contract

`fixture_validator.py` must parse bounded-runner JSON with duplicate-key
rejection and require the exact Phase 732 four argv arrays, timeouts, and
1,024-byte caps. It must require `ok\n`, empty normal stderr, timeout reason,
a decimal grandchild PID that is no longer live, `stdout_limit` with exactly
1,024 retained stdout bytes, and `stderr_limit` with exactly 1,024 retained
stderr bytes. Success emits one canonical JSON summary; failure is bounded and
nonzero.

## Listener Ordering Correction

Phase 749 retains no listener source because Phase 732 already commits its
exact bytes and digest. A future execution phase must materialize that listener
exactly once after all acquisition and immediately before sandbox controls.
It must not materialize the listener with pre-acquisition helpers.

## Exit Gate And Claims

Phase 749 must publish SHA-256 values for all three helper sources, exact CLI
help transcripts, exact self-test summaries, and focused test results. Source
and tests must pass `python3 -m py_compile`, `python3 -m unittest`, repository
hygiene, claim-boundary, formatting, and diff gates before another execution
phase may be authorized.

Phase 748 runs no helper, network, archive, compiler, Cargo, Lake, Charon,
Aeneas, Lean, sandbox backend, or kernel command. It creates no proof, accepted
evidence, Level2+, score axis, semantic correctness, production readiness,
SOTA, breakthrough, full-security claim, external audit, or action authority.
