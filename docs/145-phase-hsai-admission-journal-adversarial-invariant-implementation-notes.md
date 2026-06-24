# Phase 145 HSAI Admission Journal Adversarial Invariant Implementation Notes

Status: implemented for fail-closed admission-decision and journal-readback
invariants.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/145-phase-hsai-admission-journal-adversarial-invariant-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, dependencies, fixtures, committed generated bundles, package
runtime, source-repo parser, command-line tool, or external runtime surface was
added.

## Implemented Invariants

### Verdict-Envelope Consistency

- `AgentAdmissionDecision::accepted_envelope` now returns an envelope only for
  `AdmissionVerdict::Accepted`.
- `AgentAdmissionJournal::validate` emits
  `JournalError::NonAcceptedVerdictRetainsEnvelope` when a rejected or
  quarantined decision retains an envelope.
- Invalid existing journals cannot accept another append.
- Invalid journals are rejected before materialization creates an output root.
- Fully rehashed malicious journal content is rejected during semantic
  readback.

### Strict JSON Structures

Declared JSON and JSONL values now pass strict typed round-trip validation:

```text
raw JSON value
-> typed deserialize
-> typed serialize
-> exact JSON value equality
```

Unknown fields are therefore rejected recursively in manifests, journal
entries, nested decisions, decision rows, artifact digests, source indexes,
redaction reports, and validation reports.

### Root Symlink Safety

Readback now rejects:

- symlink output roots;
- non-directory output roots;
- symlink `admission-journal` directories;
- non-directory `admission-journal` paths;
- the existing primary-file and sidecar symlink cases.

## Coverage Hardening

The focused test suite increased from 17 to 27 tests and covers:

- missing primary files and sidecars;
- digest drift and undeclared nested directories;
- malformed declared JSON files;
- malformed, blank, duplicated, omitted, reordered, and unterminated decision
  rows;
- manifest schema, id, file-order, digest-map, claim-boundary, policy, tip, and
  count drift;
- empty, file, symlink, protected, existing, and overwritten output roots;
- primary-file and directory substitution;
- PCSM missing identity, bounded-evidence, surrogate, governance, and journal
  prerequisites;
- verdict-envelope adversarial states;
- recursive unknown-field retention attempts.

Focused `cargo llvm-cov` measured:

```text
regions: 96.80%
functions: 94.92%
lines: 97.45%
```

These are local coverage measurements, not a 100% coverage claim.

## Claim Boundary

This phase establishes local fail-closed invariants only. It does not establish
source authenticity, committed-source PCSM intake, PCSM runtime correctness,
external replication, provider or production authority, accepted Evidence
Ledger admission, benchmark evidence, official submission, proof, semantic
correctness, production readiness, score-axis validity, Level2+ evidence, or
full breakthrough-threshold admission.

The recoverable-ghost-states handoff remained staged in a dirty checkout on
2026-06-23. No source commit or handoff digest is admitted by this phase.

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
cargo llvm-cov -p hsai-agent-admission --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

No `pnpm` gate exists because this repository still has no package runtime
surface.
