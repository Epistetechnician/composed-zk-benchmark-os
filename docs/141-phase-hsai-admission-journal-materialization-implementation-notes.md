# Phase 141 HSAI Admission Journal Materialization Implementation Notes

Status: implemented for local filesystem materialization of admission-journal
review bundles.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/141-phase-hsai-admission-journal-materialization-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No other source, fixture, committed artifact, package-runtime, or output-bundle
surface is part of this phase.

## Implemented Surface

The `hsai-agent-admission` crate now implements local admission-journal bundle
materialization:

- `AdmissionJournalMaterializationRequest`
- `AdmissionJournalBundleManifest`
- `AdmissionDecisionReviewRow`
- `AdmissionSourceDigestIndex`
- `AdmissionJournalRedactionReport`
- `AdmissionJournalValidationReport`
- `AdmissionJournalMaterializationError`
- `admission_journal_required_nonclaims`
- `materialize_admission_journal_bundle`
- `read_admission_journal_bundle`

The materializer writes exactly the declared `admission-journal/*` files under
a caller-selected output root:

- `manifest.json`
- `journal.json`
- `decisions.jsonl`
- `source-digests.json`
- `non-claims.md`
- `redaction-report.json`
- `validation-report.json`
- SHA-256 sidecars for each declared file

The manifest records digest entries for all non-manifest content files. The
`manifest.json.sha256` sidecar binds the manifest bytes themselves, avoiding a
self-referential manifest digest.

## Validation Behavior

The implementation rejects:

- empty or path-shaped bundle ids;
- missing required nonclaims;
- invalid journal chains;
- stale declared journal tips;
- empty output roots;
- protected output roots;
- existing output roots without explicit overwrite;
- file or symlink output roots;
- symlink bundle files;
- undeclared bundle files;
- stale digest sidecars;
- serialization or filesystem errors.

Readback validates declared files, sidecar digests, and absence of undeclared
files before returning the manifest.

## Claim Boundary

The bundle is local admission-trace metadata only. It is not accepted Evidence
Ledger mutation, official benchmark evidence, official benchmark submission,
external replay evidence, provider evidence, proof, semantic correctness,
production readiness, Level2+ evidence, or score-axis population.

This phase does not import PCSM runtime code, import recoverable-ghost
artifacts, parse recoverable-ghost files, run source repo commands, call
providers, use credentials, run external replay, create committed generated
bundles, or add package runtime files.

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

No `pnpm` gate exists in this repository because there is no package runtime
surface.
