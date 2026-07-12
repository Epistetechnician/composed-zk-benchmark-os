# Phase 731 HSAI Gateway Threat Ordinal Runner Fixture Stop

## Status

Complete as one cleaned detached-worktree pre-source stop.

State slice:
`phase-731-hsai-gateway-threat-ordinal-runner-fixture-stop`.

Classification: `BoundedRunnerFixtureContractMismatch`.

Diagnostic: `AlternateFixtureCommandsAndCaps`.

Execution status: `Failed` for bounded-runner fixture conformance;
`SucceededNonconformingAfterStopPoint` for the later Rust manifest,
installation, and first identity producer; and `NotRun` for Charon source,
Aeneas, Lean, Cargo, Lake, sandbox attribution, backend extraction, and kernel
checking. Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

Phase 731 created a clean detached execution worktree at committed
`7ac014239fa72bdd57585e04e7a9e90fcec4600a`. Frozen repository hashes,
canonical roots, disk reserve, client metadata, and the temporary process-group
runner passed their immediate checks.

The four runner invocations did not match the inherited Phase 714 sequence.
They used a shell `printf` normal command, a different shell timeout command,
and Python stdout/stderr flood producers instead of `/bin/echo ok`, the exact
child-plus-grandchild fixture, `/usr/bin/yes x`, and the declared shell stderr
flood. Both flood fixtures also retained 64 bytes instead of the previously
observed and required 1,024-byte caps. The post-run audit identified this as
the first nonconforming gate.

The Rust channel manifest, isolated Rust installation, and first identity
producer had already completed before that audit. They cannot cure the earlier
fixture mismatch and are classified only as nonconforming activity after the
stop point. Phase 731 ran no Charon, Aeneas, Lean, Cargo, Lake, sandbox, backend,
or kernel command.

## Cleanup and Claims

All attempt-owned roots and persistent tool roots were removed, and the
detached worktree was deregistered. The primary Phase 183 and Phase W test files
retained SHA-256 values
`cca84d855ccbb7433b18a67470b0eb87ec57ea651e95193b8284e9b16ab20440`
and `70ace59109856d96122b6ba45ddecbb2ee28a45fc57c722f55611e25a062620a`.
The primary branch advanced independently after cleanup; no primary content was
imported into the detached execution checkout.

Phase 731 creates no backend result, generated Lean source, kernel result,
proof artifact, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, or full-security claim.
