# Phase 127 DSL Coverage Campaign Notes

Status: complete for a bounded local DSL/oracle coverage campaign.

## State Slice

This phase touches only local `zkbench-core` DSL/oracle tests, documentation
navigation, and the whole-codebase validation report.

Code changes are limited to:

- `crates/zkbench-core/tests/oracle_eval.rs`
- `crates/zkbench-core/tests/lowering.rs`

## Purpose

Phase 127 continues the local coverage loop after Phase 126 by targeting the
central hermetic DSL/oracle path. The goal is higher local line coverage with
stronger regression tests over already-implemented local behavior.

This phase does not change production Rust APIs. It does not add runtime
behavior, external replay, live backend execution, benchmark outputs, official
submission, accepted Evidence Ledger mutation, score-axis population, Level2+
evidence, production-readiness claims, semantic-correctness claims, or 100%
coverage.

## Added Coverage

The oracle tests now cover:

- boolean guard combinators;
- text and boolean value comparisons;
- `noop`, `assign`, and `sub_assign` actions;
- raw guard and raw action capability gaps;
- undeclared initial state rejection;
- undeclared transition rejection;
- transition current-state mismatch rejection;
- expected final-state mismatch rejection;
- expected final-field mismatch and missing-field rejection;
- missing initial field errors;
- arithmetic non-integer field rejection;
- arithmetic non-integer operand rejection;
- arithmetic overflow rejection; and
- public expression helper reference collection and raw-text detection.

The lowering/validation tests now cover:

- empty machine id rejection;
- undeclared initial state rejection;
- field initial-value type mismatch rejection;
- undeclared transition source rejection;
- action, invariant, observation, public-input, private-witness, and
  witness-policy unknown-field rejection;
- invalid trace id, initial state, final state, initial field, final field, and
  transition references;
- duplicate transition and target ids; and
- actual Level2 claim-boundary rejection while preserving planned metadata.

## Measurement

Before this phase, the Phase 126 all-feature workspace coverage pass reported:

- region coverage: `84.89%`
- function execution: `81.86%`
- line coverage: `82.82%`

After this phase, the all-feature workspace coverage pass reported:

- region coverage: `85.32%`
- function execution: `82.13%`
- line coverage: `83.45%`

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
cargo test -p zkbench-core --test oracle_eval
cargo test -p zkbench-core --test lowering
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```

