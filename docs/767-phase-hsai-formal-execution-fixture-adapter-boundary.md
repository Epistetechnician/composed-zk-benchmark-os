# Phase 767 HSAI Formal Execution Fixture Adapter Boundary

## Status

Complete as a documentation-first compatibility correction.

State slice: `phase-767-hsai-formal-execution-fixture-adapter-boundary`.

Classification: `ExactFixtureAndBoundedAdapterSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Conflict Closure

Phase 732 requires two exact process-control fixture argv arrays rooted at
`/bin/sh -c`. Phase 765 prohibited all shell executables. Phase 768 may add one
fixture-only exception that accepts only the two byte-exact Phase 732 arrays
already enforced by `fixture_validator.py`:

```text
/bin/sh -c '/bin/sh -c "/bin/sleep 30" & child=$!; printf "%s\n" "$child" > "$RUN/grandchild.pid"; wait "$child"'
/bin/sh -c 'exec /usr/bin/yes x >&2'
```

The exception must require command role `exact-process-fixture`, stage
`client-and-fixtures`, network policy `none`, exact argv equality, and the
declared Phase 732 timeout/caps/outcome. Every other shell executable or
shell-like role remains prohibited. No user-supplied shell text is allowed.

## Authorized Phase 768 Surface

Phase 768 may modify only the Phase 766 state-machine module and tests, add one
implementation note, and update standard mirrors. It must add:

- absolute canonical cwd;
- positive finite timeout and positive stream caps;
- distinct status/stdout/stderr paths;
- expected bounded-runner reason, return code, and signal;
- command role validation;
- a producer adapter that invokes the committed `bounded_runner.py` as an argv
  array with explicit cwd and allowlisted environment; and
- canonical bounded status acceptance with direct failure mapping.

The adapter must use null stdin, never invoke a shell, preserve the child argv
byte-for-byte, reject pre-existing output paths, and treat bounded-runner
invocation failure, malformed status, argv drift, reason/return/signal drift,
or unexpected retained-stream size as terminal command failure. It may not
interpret backend semantics or promote evidence.

Hermetic tests must cover normal exit, nonzero expected exit, timeout, stdout
limit, stderr limit, wrong status identity, output reuse, cwd rejection,
environment replacement, exact fixture acceptance, near-match fixture
rejection, and first-failure short-circuiting. Tests may not use network or any
formal backend.

Phase 768 does not yet bind the complete production command plan. Phase 769
must bind the exact inherited commands to the tested adapter before a later
execution attempt is authorized.

Phase 767 runs no helper, producer, network, compiler, backend, or kernel
command and creates no proof, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.
