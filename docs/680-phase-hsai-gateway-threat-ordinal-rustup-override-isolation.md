# Phase 680 HSAI Gateway Threat Ordinal Rustup-Override Isolation

## Status

Complete as a documentation-first toolchain-context correction.

State slice:
`phase-680-hsai-gateway-threat-ordinal-rustup-override-isolation`.

Execution status: `NotRun`.

Classification: `RustupOverrideIsolationSpecified`.

Evidence ceiling: `Level1LocalReplayOrLower`.

## Corrected Rule

Phase 681 inherits the Phase 678 ordered protocol except for this controlling
rustup correction.

All rustup identity, component, and driver-load preflight commands must run
with `workdir=$RUN`, never from `CHARON_PACKAGE`, and must set:

```text
RUSTUP_HOME=$RUSTUP_ROOT
RUSTUP_TOOLCHAIN=nightly-2026-06-01
PATH=$RUSTUP_BIN_DIR:$TOOLCHAIN/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

The required identity commands are only:

```bash
"$RUSTUP_BIN" --version
"$RUSTUP_BIN" component list \
  --toolchain nightly-2026-06-01 \
  --installed
"$RUSTC" -Vv
"$CARGO" -V
```

Capture the installed-component list before and after these commands and
require byte equality. Any `syncing`, `downloading`, `installing`, or component
list change stops as `UnexpectedRustupAutoInstall`.

`CHARON_PACKAGE` may run only direct `$CARGO fetch` and direct `$CARGO build`
with the Phase 678 explicit compiler, Cargo-home, target, manifest, lock,
offline, and sandbox bindings. No bare rustup command may execute there.

Later `CHARON_BIN cargo` runs from the HSAI repository workdir with
`RUSTUP_HOME=$RUSTUP_ROOT`, `RUSTUP_TOOLCHAIN=nightly-2026-06-01`, the bound
rustup directory first in `PATH`, and `CHARON_TOOLCHAIN_IS_IN_PATH` unset.
Charon's internal explicit `rustup run nightly-2026-06-01` is allowed only for
driver loading. The installed-component list must remain byte-identical after
extraction.

## Phase 681 Authorization

After this boundary is committed and the disk gate passes, Phase 681 may make
one attempt under Phase 678 plus this correction. The first named failure
terminates it; no same-phase command correction or replay is allowed.

## Cleanup and Claims

Attempt ownership, cleanup, retention, process bounds, sandboxing, evidence
ceiling, and all nonclaims remain exactly as specified by Phase 678.

Phase 680 runs no tool and creates no backend result, proof, accepted evidence,
Level2+, score axis, source correspondence, semantic correctness, production
readiness, SOTA, breakthrough, full security, independent reproduction,
external audit, or action authority.

## Repository Validation

The documentation-only boundary passed repository hygiene 1/1,
documentation claim-boundary coverage 1/1, source claim-boundary coverage 6/6,
Rust formatting, and diff hygiene. Root `pnpm run lint` was inapplicable
because there is no root `package.json`.
