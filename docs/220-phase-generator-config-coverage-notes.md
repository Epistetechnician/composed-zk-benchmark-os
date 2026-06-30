# Phase 220 Generator Config Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/generator_determinism.rs`
- `docs/220-phase-generator-config-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, generator semantics,
or external execution behavior changed.

## Purpose

After Phase 219, the next fresh non-serializer low surface in the
`zkbench-core` package coverage table was
`crates/zkbench-core/src/generator/config.rs` at `80.23%` line coverage.

This tranche adds focused regression coverage for reachable generator
configuration validation branches.

## Coverage Added

The added tests cover:

- explicit trace-length limit rejection;
- derived transition-count limit rejection;
- baseline FSM `state_count >= 2` rejection;
- baseline FSM `trace_length >= state_count - 1` rejection;
- branching FSM `branching_factor >= 2` rejection;
- bounded counter loop `loop_bound >= 1` rejection;
- the public `branching_factor` builder path.

These are normal public validation paths exercised through `GeneratorConfig`.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.37%` region coverage, `85.82%` function execution, and
  `91.48%` line coverage;
- `generator/config.rs`: `92.68%` region coverage, `94.74%` function
  execution, and `80.23%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.41%` region coverage, `85.88%` function execution, and
  `91.62%` line coverage;
- `generator/config.rs`: `97.56%` region coverage, `100.00%` function
  execution, and `90.70%` line coverage.

The remaining uncovered generator-config lines are capped under the current
API shape: all current `FamilyKind` variants are implemented, so the
future-placeholder family rejection path is not constructible, and the generic
transition/trace limit checks fail before duplicate family-specific
transition/trace checks for baseline, branching, and bounded-loop configs.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer public surface is
`mutation/missing_constraints.rs` at `80.43%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
generator semantics, generated family semantics, mutation semantics, Cargo
metadata, dependencies, external execution, generated artifact materialization,
accepted Evidence Ledger policy, formal evidence, benchmark evidence,
score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test generator_determinism
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
