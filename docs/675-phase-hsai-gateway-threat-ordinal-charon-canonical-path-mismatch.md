# Phase 675 HSAI Gateway Threat Ordinal Charon Canonical-Path Mismatch

## Status

Complete as one cleaned-up pre-Cargo failure.

State slice:
`phase-675-hsai-gateway-threat-ordinal-charon-canonical-path-mismatch`.

Classification: `CharonPackageCanonicalPathMismatch`.

Execution status: `NotRun` for Cargo fetch/build, Charon, Aeneas, Lean, and
Lake. Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

The attempt reacquired and verified the exact Rust nightly and Charon source.
The new Phase 674 directory assertion then compared:

```text
declared:  /tmp/hsai-phase675-efa3782c/charon-source/charon
canonical: /private/tmp/hsai-phase675-efa3782c/charon-source/charon
```

On this macOS host, `/tmp` resolves to `/private/tmp`. The assertion correctly
failed before Cargo, but the Phase 674 contract incorrectly compared a
canonical `pwd -P` result against a noncanonical variable. The isolated Cargo
home did not exist and no Cargo command ran.

## Cleanup

The temporary source tree and 1.6 GiB isolated Rust toolchain were removed.
No dependency, source build, compiler driver, build script, LLBC, generated
source, witness, kernel check, proof artifact, accepted evidence, Level2+, or
score-axis value was created.

Focused repository hygiene passed 1/1, documentation claim-boundary coverage
passed 1/1, source claim-boundary coverage passed 6/6, and formatting/diff
hygiene passed. Root `pnpm run lint` was inapplicable because there is no root
`package.json`.

## Claim Boundary

Phase 675 creates no backend or formal result. It does not establish source
correspondence, semantic correctness, production readiness, SOTA,
breakthrough, full security, independent reproduction, external audit, or
action authority.

## Next Gate

Phase 676 must be documentation-first and canonicalize the run root before
deriving any source, manifest, lock, target, or output path. No identical Phase
675 replay is authorized.
