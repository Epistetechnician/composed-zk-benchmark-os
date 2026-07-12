# Phase 739 HSAI Gateway Threat Ordinal Archive Profile Stop

## Status

Complete as one cleaned detached-worktree pre-extraction stop.

State slice:
`phase-739-hsai-gateway-threat-ordinal-archive-profile-stop`.

Classification: `PinnedArchiveProfileMismatch`.

Diagnostic: `MainTopLevelSetMismatchAndAcceptanceStatusMasked`.

Execution status: `Succeeded` for raw-parser self-tests, exact runner fixtures,
Rust identity, Charon source, and both Aeneas asset downloads; `Failed` for the
real archive-profile validator; and `NotRun` for materialization, Lean, Cargo,
Lake, sandbox attribution, backend extraction, and kernel checking. Evidence
ceiling: `Level1LocalReplayOrLower`.

## Observation

Phase 739 created a clean detached execution worktree at committed
`e2092a49becbedbc170d1d6152bbc10ea50f1f07`. The raw-aware parser passed its
bounded 31-case pre-acquisition self-test with empty stderr. Frozen repository,
canonical root, disk, client, exact four-fixture, Rust identity, Charon source,
and independent Aeneas asset gates then passed.

The real bounded parser returned one canonical error:
`top-level set mismatch`. This means the guessed main-archive allowlist in
Phase 736 was incorrect. It is not an unsafe-archive finding because the failure
record did not identify an unsafe member. Stdout was empty, stderr was bounded,
and no extraction ran.

The following acceptance shell correctly detected the validator return code 1,
but then ran checkpoint and hash commands without immediate shell failure
propagation. Its overall status was therefore zero and it wrote a false local
checkpoint. All such run-local state was discarded. No acceptance, extraction,
or backend claim survived cleanup.

## Cleanup and Claims

All attempt-owned roots and persistent tool roots were removed, and the
detached worktree was deregistered. Repository state remained clean.

Phase 739 creates no accepted archive profile, archive-validation result,
materialized external tool, backend result, generated Lean source, kernel
result, proof artifact, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, or full-security claim.
