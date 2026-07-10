# Phase 673 HSAI Gateway Threat Ordinal Charon Cargo-Lock Mismatch

## Status

Complete as one cleaned-up pre-build failure.

State slice:
`phase-673-hsai-gateway-threat-ordinal-charon-cargo-lock-mismatch`.

Classification: `CharonCargoLockMismatch`.

Execution status: `NotRun` for source build, Charon, Aeneas, Lean, and Lake.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Observation

The disk gate passed and the attempt reacquired the exact Rust nightly and
verified Charon source commit
`909ff09ad0f144f83d354f2c3d26f631fb9f8e9a`. Before the first build, the
network-enabled Cargo fetch command ran with the HSAI repository as its current
directory rather than the pinned Charon `charon/` directory.

The two lockfile digests were:

| Lockfile | SHA-256 |
|---|---|
| HSAI workspace `Cargo.lock` used by the fetch | `87e72fd27531b91d25097d810efa2a876971310fba77ac464c0169ef0d0df893` |
| Required Charon `charon/Cargo.lock` | `4e361622e601cfe93fce40e5a13bf6b5a89a84394875b409f8c8f27ec86272db` |

This contaminated the isolated Charon Cargo home with dependencies selected by
the wrong lockfile. No build command had started, but the Phase 670 source
acquisition contract required `cargo fetch --locked` from the pinned Charon
package directory. The first mismatch therefore terminated Phase 673 as
`CharonCargoLockMismatch`; correcting the directory in place would have been a
same-phase retry.

## Cleanup

The attempt removed:

- the complete temporary Phase 673 source/run tree;
- the 1.6 GiB isolated Rust toolchain; and
- the 198 MiB contaminated isolated Cargo home.

No Aeneas or Lean asset was downloaded. No source build, compiler-driver,
`ring` build script, selector resolution, LLBC generation, Aeneas extraction,
generated source, witness, Lean kernel, Lake build, proof artifact, accepted
evidence, Level2+ evidence, or score-axis value occurred.

## Repository Validation

The retained documentation-only state passed repository hygiene 1/1,
documentation claim-boundary coverage 1/1, source claim-boundary coverage 6/6,
Rust formatting, and diff hygiene. Root `pnpm run lint` remained inapplicable
because there is no root `package.json`.

## Claim Boundary

Phase 673 creates no backend result and no formal evidence. It does not
establish extraction, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, independent reproduction,
external audit, or authority to execute an HSAI action.

## Defensible Claim

```text
HSAI stopped the corrected Aeneas retry before source build because Cargo
acquisition was bound to the wrong lockfile, then removed all acquired state.
```

## Next Gate

Phase 674 must be documentation-first and require both an exact current-directory
assertion and an absolute `--manifest-path` on every Charon Cargo fetch/build
operation. No identical Phase 673 replay is authorized.

Phase 674 completed that correction in
`docs/674-phase-hsai-gateway-threat-ordinal-charon-manifest-binding-closure.md`.
