# Phase 711 HSAI Gateway Threat Ordinal Charon Fetch Toolchain Token Stop

## Status

Complete as one cleaned nonconforming pre-build stop.

State slice:
`phase-711-hsai-gateway-threat-ordinal-charon-fetch-toolchain-token-stop`.

Classification: `UnexpectedCommand`.

Diagnostic: `WrongRustupToolchainTokenInCharonFetch`.

Execution status: `SucceededNonconforming` for Charon dependency fetch and
`NotRun` for Charon build, Lake update/cache, sandbox controls, backend
extraction, and Lean checking. Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

Canonical UTF-8 client hashes, run-root ownership, bounded-runner fixtures,
frozen-source gates, exact Rust identity, Charon source, Aeneas safety and
equivalence, Aeneas identity, Lean/Lake identity, and the direct
`rustc_private` probe passed.

The direct locked Charon fetch was then invoked with
`RUSTUP_TOOLCHAIN=nightly-2026-01` instead of the required
`nightly-2026-06-01`. The direct Cargo, rustc, rustdoc, Cargo-home, target, and
manifest paths were otherwise bound, and the fetch exited zero, but the wrong
environment token makes the result nonconforming. Phase 711 did not use that
cache or continue to build.

## Cleanup and Claims

The isolated dependency cache and all other attempt-owned roots were removed.
No Charon binary was produced. Protected Cargo and repository state were
preserved.

Phase 711 creates no LLBC, generated Lean source, kernel result, proof artifact,
accepted evidence, Level2+, score axis, semantic correctness, production
readiness, SOTA, breakthrough, or full-security claim.
