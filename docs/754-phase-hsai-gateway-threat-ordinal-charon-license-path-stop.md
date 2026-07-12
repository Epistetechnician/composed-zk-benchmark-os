# Phase 754 HSAI Gateway Threat Ordinal Charon License Path Stop

## Status

Complete as one cleaned pre-Aeneas acquisition stop.

State slice:
`phase-754-hsai-gateway-threat-ordinal-charon-license-path-stop`.

Classification: `CharonSourceIdentityPathMismatch`.

Diagnostic: `PinnedLicensePathUsesLicenseInsteadOfLicenseMd`.

Execution status: `Succeeded` for dirty-primary preservation, detached source
and helper hashes, parser self-tests, client hashes, exact fixtures, Rust
manifest/install/identities, immutable toolchain-token checks, forbidden-
transfer scan, and pinned Charon fetch; `Failed` for Charon source-file identity;
and `NotRun` for Aeneas/Lean acquisition, archives, Cargo, Lake, sandbox,
backend extraction, generated source, and kernel checking. Evidence ceiling:
`Level1LocalReplayOrLower`.

## First Failure

Phase 754 fetched exact Charon commit
`909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` into a clean detached source
checkout. The five-file identity assertion requested root path `LICENSE`, which
does not exist. Read-only failure diagnosis found root path `LICENSE.md` with
the expected SHA-256
`c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`.
The hash pin was correct; the documented path was not.

## Cleanup And Claims

The Rustup root, run root, and detached worktree were removed. The primary
checkout's committed HEAD, porcelain bytes, dirty file set, and every recorded
file digest matched the pre-attempt preservation record exactly. The record was
then removed.

Phase 754 creates no Aeneas asset, archive result, backend result, generated
source, kernel result, proof, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.
