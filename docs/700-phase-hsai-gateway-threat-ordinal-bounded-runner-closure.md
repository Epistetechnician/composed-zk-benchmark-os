# Phase 700 HSAI Gateway Threat Ordinal Bounded Runner Closure

## Status

Complete as a documentation-first process-envelope correction.

State slice: `phase-700-hsai-gateway-threat-ordinal-bounded-runner-closure`.

Classification: `BoundedProcessGroupRunnerSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Runner Contract

Phase 701 uses canonical run root `hsai-phase701-efa3782c` and witness
`phase701ExtractedThreatOrdinalWitnesses`.

The future runner is a temporary Python standard-library helper under the run
root. Host `/usr/bin/python3` is pinned to version `3.9.6`, SHA-256
`7f30f076d0e9c38f772a76449fca9da8cf97f6a3d43b94c90a00e4f9ce7ad39e`,
and the observed universal arm64e/x86_64 Mach-O binary.

It must spawn with `start_new_session=True`, null stdin, piped stdout/stderr,
concurrent nonblocking reads, live per-stream byte caps, and complete-process-
group `SIGTERM` followed by `SIGKILL` after two seconds on timeout or overflow.
It must record exit, timeout, overflow, signal, and byte counts in bounded
run-local files and retain no bytes beyond declared caps.

Before build, fixtures must prove normal exit, child-plus-grandchild timeout
termination, stdout flood termination, and stderr flood termination. Runner
source, Python binary, fixture commands, and outputs must be hashed. Failure
stops as `BoundedExecutionUnavailable`.

The helper is temporary operator tooling, not proof authority, and may wrap
only already authorized sandboxed commands.

After commit, clean-tree, and disk gates, Phase 701 may make one attempt. All
pins, cache closure, sandbox attribution, cleanup, evidence, and claim rules
remain.

Phase 700 runs no backend and creates no proof, accepted evidence, Level2+,
score axis, semantic correctness, production readiness, SOTA, breakthrough,
or full-security claim.

