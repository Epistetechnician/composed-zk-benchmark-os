# Phase 128 Soak Serialization Coverage Notes

Status: complete for a bounded local soak serialization coverage campaign.

## State Slice

This phase touches only local `zkbench-core` soak serialization tests,
documentation navigation, and the whole-codebase validation report.

Code changes are limited to:

- `crates/zkbench-core/tests/soak_serialization.rs`

## Purpose

Phase 128 continues the local coverage loop after Phase 127 by targeting the
pure JSON serialization wrapper surface for local soak artifacts. The goal is
higher local line coverage with regression checks over already-implemented
hermetic behavior.

This phase does not change production Rust APIs. It does not add runtime
behavior, external replay, live backend execution, benchmark outputs, official
submission, accepted Evidence Ledger mutation, score-axis population, Level2+
evidence, production-readiness claims, semantic-correctness claims, or 100%
coverage.

## Added Coverage

The soak serialization tests now cover successful pretty-JSON round-trips for:

- soak run configs;
- soak shard plans;
- soak shard manifests;
- soak shard checkpoints;
- soak telemetry reports;
- soak health reports;
- failure corpus indexes;
- failure reproduction manifests;
- soak artifact manifests; and
- soak report bundles.

The tests also cover malformed JSON error-context preservation for every
corresponding soak deserializer wrapper.

## Measurement

Before this phase, the Phase 127 all-feature workspace coverage pass reported:

- region coverage: `85.32%`
- function execution: `82.13%`
- line coverage: `83.45%`

After this phase, the all-feature workspace coverage pass reported:

- region coverage: `85.46%`
- function execution: `82.54%`
- line coverage: `83.55%`

The targeted `zkbench-core/src/soak/serialization.rs` line coverage improved to
`98.65%` in the all-feature workspace coverage pass.

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
cargo test -p zkbench-core --test soak_serialization
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS='-D warnings' cargo doc --workspace --all-features --no-deps
cargo llvm-cov --workspace --all-features --summary-only
rg --files -g 'package.json' -g 'pnpm-lock.yaml' || true
```
