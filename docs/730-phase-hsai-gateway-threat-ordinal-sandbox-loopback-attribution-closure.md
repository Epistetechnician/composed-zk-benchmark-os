# Phase 730 HSAI Gateway Threat Ordinal Sandbox Loopback Attribution Closure

## Status

Complete as a documentation-first sandbox-attribution correction.

State slice:
`phase-730-hsai-gateway-threat-ordinal-sandbox-loopback-attribution-closure`.

Classification: `ControlledLoopbackSandboxAttributionSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 731 uses canonical run root `hsai-phase731-efa3782c`, canonical detached
repository root `hsai-phase731-repo-efa3782c`, and witness
`phase731ExtractedThreatOrdinalWitnesses`.

Before any backend build, Phase 731 must start one attempt-owned loopback-only
TCP listener on a dynamically assigned port. It must capture the selected port
in a regular file, prove one unsandboxed loopback connection succeeds, and then
prove the byte-identical connection command exits nonzero under the pinned
deny-network profile. The listener must have a bounded lifetime, accept only
the declared control connections, write no repository state, and be terminated
and reaped before any backend command or cleanup.

The inherited sandboxed hostname and direct-IP probes must still exit nonzero.
Their stderr remains captured and bounded, but operating-system diagnostic text
is informative rather than authoritative. Sandbox attribution now depends on
the controlled contrast between a successful unsandboxed loopback connection
and a failed sandboxed connection to the same listener, not on one unstable
`nc` error string. A missing listener, failed positive control, successful
sandboxed connection, unbounded listener, unreaped process, or changed command
must stop the attempt before Charon build.

After commit and detached-worktree gates, Phase 731 may make one attempt. The
separate materialization producers, exact twelve-file Rust identity set,
fourteen-`rfl` witness, direct `.olean` sequence, independent network records,
exact version, fixture, token, client, identity allowlist, component, runner,
source, cache, cleanup, evidence, and claim rules remain.

Phase 730 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
