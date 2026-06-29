# Phase 215 Soak Health Coverage Thirty-Seventh Tranche Notes

Status: complete for focused local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/soak_health_report.rs`
- `docs/215-phase-soak-health-coverage-thirty-seventh-tranche-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production source, Cargo metadata, generated artifacts, accepted Evidence
Ledger state, benchmark output, or score-axis state changed.

## Purpose

Add focused regression coverage for `crates/zkbench-core/src/soak/health.rs`,
continuing the local coverage campaign from the prior reported package floor of
79.00%.

This tranche targets validation and aggregation branches rather than changing
health-report semantics.

## Coverage Measurement

After this phase, the local package coverage command:

```sh
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

reported for `zkbench-core`:

- region coverage: `90.28%`;
- function execution: `85.76%`;
- line coverage: `91.35%`.

The targeted `soak/health.rs` module reported:

- region coverage: `97.49%`;
- function execution: `100.00%`;
- line coverage: `98.67%`.

The package floor moved away from `soak/health.rs`. In this local package run,
the lowest line-coverage file was `replay/serialization.rs` at `75.00%`.

## Implemented

The `soak_health_report` integration tests now cover:

- empty report version rejection;
- empty shard id rejection;
- empty aggregate id rejection;
- nested health-finding claim-boundary elevation rejection;
- unsafe health note text that implies ZK backend performance;
- summary drift for mutation variants, local replays, and failures;
- aggregate report construction over healthy and warning shard reports;
- aggregate failure-corpus warning propagation;
- aggregate regression-signal activation;
- aggregate status precedence for degraded and failed reports;
- telemetry-derived local replay failure findings;
- telemetry validation failure findings.

## Claim Boundary

This is coverage hardening only. It does not change local soak health semantics,
status precedence, telemetry semantics, failure-corpus semantics, production
source, Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Run from repository root:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test soak_health_report
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
