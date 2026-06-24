# Phase 143 HSAI Admission Journal Semantic Readback Implementation Notes

Status: implemented for complete local semantic validation of Phase 141
admission-journal bundles.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/143-phase-hsai-admission-journal-semantic-readback-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, fixture, committed generated artifact, package runtime,
source-repo parser, command-line tool, or external runtime surface is part of
this phase.

## Implemented Surface

`read_admission_journal_bundle` now:

- rejects non-regular declared files;
- rejects symlink primary files and digest sidecars;
- verifies every adjacent SHA-256 sidecar;
- parses every declared bundle file;
- validates the serialized journal chain;
- recomputes manifest counts, tips, policy alignment, file declarations, and
  content digests;
- recomputes and compares decision review rows;
- recomputes and compares the source digest index;
- rejects conflicting hashes under one artifact id before materialization and
  during readback;
- requires canonical nonclaim Markdown matching manifest nonclaims;
- requires every redaction retention flag to remain false;
- recomputes and compares the validation report.

New explicit errors distinguish malformed declared files, manifest drift,
invalid serialized journals, decision-index drift, source-index drift,
nonclaim drift, unsafe redaction, validation-report drift, sidecar symlinks,
and declared file type drift.

The Phase 141 bundle format is unchanged.

## Regression Coverage

Focused tests cover:

- valid legacy Phase 141 bundle round-trip;
- digest-consistent manifest count drift;
- digest-consistent journal-chain drift;
- digest-consistent decision-row drift;
- digest-consistent source-index drift;
- digest-consistent nonclaim drift;
- digest-consistent redaction-policy drift;
- digest-consistent validation-report drift;
- sidecar symlink rejection;
- complete local PCSM bounded-proof intake through candidate, admission,
  journal append, materialization, and semantic readback.

The PCSM path remains local metadata only and exports no accepted claim
envelope.

## Claim Boundary

Semantic readback establishes internal consistency of one local bundle. It is
not source authenticity, PCSM runtime import, external replication, provider
authority, production or serving authority, accepted Evidence Ledger mutation,
official benchmark evidence, official submission, proof, semantic correctness,
production readiness, score-axis population, Level2+ evidence, or full
breakthrough-threshold admission.

The recoverable-ghost-states handoff remained staged in a dirty checkout on
2026-06-23. This phase does not parse that checkout or admit a current source
commit or handoff digest.

## Validation

Run from repository root:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p hsai-agent-admission
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

No `pnpm` gate exists because the repository still has no package runtime
surface.
