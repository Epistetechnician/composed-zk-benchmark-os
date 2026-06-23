# Phase 129 Proposal Validation Coverage Notes

Status: complete for a bounded local evidence append proposal validation
coverage campaign.

## State Slice

This phase touches only local `zkbench-core` evidence append proposal tests,
documentation navigation, and the whole-codebase validation report.

Code changes are limited to:

- `crates/zkbench-core/tests/evidence_append_proposal.rs`

## Purpose

Phase 129 continues the local coverage loop after Phase 128 by targeting the
pure metadata validation surface for evidence append proposals. The goal is
higher local line coverage with regression checks over already-implemented
claim-boundary rejection behavior.

This phase does not change production Rust APIs. It does not add runtime
behavior, external replay, live backend execution, benchmark outputs, official
submission, accepted Evidence Ledger mutation, score-axis population, Level2+
evidence, production-readiness claims, semantic-correctness claims, or 100%
coverage.

## Added Coverage

The evidence append proposal tests now cover rejection paths for:

- empty proposal id;
- empty source normalized draft id;
- proposed evidence class above local design-note metadata;
- proposed Level2 claim boundary;
- accepted-evidence flag assertion;
- empty proposed artifact reference;
- unresolved blocking import issue;
- blocked claim-boundary issue kinds;
- forbidden official-evidence wording in proposal notes;
- forbidden formal-proof wording in provenance summaries;
- forbidden proof wording in review requirement notes; and
- forbidden soundness-proof wording in review findings.

The focused regression also verifies that every reported issue in this
multi-fault proposal remains an error-severity validation issue.

## Measurement

Before this phase, the Phase 128 all-feature workspace coverage pass reported:

- region coverage: `85.46%`
- function execution: `82.54%`
- line coverage: `83.55%`

After this phase, the all-feature workspace coverage pass reported:

- region coverage: `85.58%`
- function execution: `82.59%`
- line coverage: `83.74%`

The targeted `zkbench-core/src/external_runner/proposal.rs` line coverage
improved to `96.45%` in the all-feature workspace coverage pass.

These are local instrumentation metrics only. They are not proof, not official
benchmark evidence, not accepted evidence, not Level2+ evidence, and not 100%
coverage.

## Anti-Goals

This phase does not permit production source changes, new public APIs, generated
artifacts, committed output bundles, external replay, live backend execution,
network access, credentials, official endpoint submission, accepted Evidence
Ledger mutation, score-axis population, ZK backend performance claims, formal
evidence, SOTA claims, production-readiness claims, semantic-correctness
claims, or claiming 100% coverage.

## Validation

Required validation for this phase:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test evidence_append_proposal
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```
