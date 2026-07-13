# Phase 763 HSAI Gateway Threat Ordinal Rustup Inventory Closure

## Status

Complete as a documentation-first identity-parser correction.

State slice: `phase-763-hsai-gateway-threat-ordinal-rustup-inventory-closure`.

Classification: `MarkedInstalledComponentParsingSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

Phase 764 uses run root `hsai-phase764-efa3782c`, detached repository root
`hsai-phase764-repo-efa3782c`, and witness
`phase764ExtractedThreatOrdinalWitnesses`.

Phase 764 must bind rustup stdout exactly to
`rustup 1.29.0 (28d1352db 2026-03-05)`. Each of the three component producers
must return zero and emit byte-identical stdout with SHA-256
`ffc5bb10b299bd6a907ca781249ea3e88474b8ea47bcee48b52d0eb42a72674e`.
The acceptance parser must require every installed entry to end in exactly
` (installed)`, strip only that suffix, and compare the resulting ordered set
to:

```text
cargo-aarch64-apple-darwin
llvm-tools-aarch64-apple-darwin
miri-aarch64-apple-darwin
rust-src
rust-std-aarch64-apple-darwin
rustc-aarch64-apple-darwin
rustc-dev-aarch64-apple-darwin
```

It must require exactly seven marked entries, preserve the exact rustc commit
and Cargo identity assertions, and reject any extra marked component. Every
acceptance command must be a standalone top-level command or begin with
`set -eu`; no later negative scan, checkpoint, display, or print may mask an
earlier nonzero status. The no-transfer scan remains a separate command after
identity acceptance.

After commit and all inherited Phase 749-762 gates, Phase 764 may make one
attempt. The first failure stops the phase without repair or replay.

Phase 763 runs no tool, network, compiler, backend, or kernel command and
creates no proof, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, full-security claim, external audit,
or action authority.
