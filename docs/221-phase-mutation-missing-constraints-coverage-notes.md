# Phase 221 Mutation Missing Constraints Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/mutation_engine.rs`
- `docs/221-phase-mutation-missing-constraints-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, mutation semantics,
or external execution behavior changed.

## Purpose

After Phase 220, the next visible low non-serializer public surface in the
`zkbench-core` package coverage table was
`crates/zkbench-core/src/mutation/missing_constraints.rs` at `80.43%` line
coverage.

This tranche adds focused regression coverage for reachable
`MissingConstraintsPass` behavior.

## Coverage Added

The added tests cover:

- `MissingConstraintsPass::mutation_class`;
- fail-closed behavior when no rejected trace provides an eligible target;
- deterministic skip-ahead behavior for empty rejected traces;
- deterministic skip-ahead behavior for rejected trace steps that reference an
  unknown transition before a later eligible target.

These are normal public mutation paths exercised through
`apply_mutation_pass`.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.41%` region coverage, `85.88%` function execution, and
  `91.62%` line coverage;
- `mutation/missing_constraints.rs`: `85.92%` region coverage, `33.33%`
  function execution, and `80.43%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.44%` region coverage, `85.99%` function execution, and
  `91.66%` line coverage;
- `mutation/missing_constraints.rs`: `98.59%` region coverage, `100.00%`
  function execution, and `100.00%` line coverage.

The remaining uncovered region is capped under the current API shape:
`transition_mut(&mut surface_spec, &transition_id)?` cannot fail after
`transition_id` was selected from the same `surface_spec` immediately before
the cloned mutation surface is edited.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer public surface is
`adapters/zk_harness/mapping.rs` at `82.05%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
mutation semantics, generated family semantics, generator semantics, Cargo
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
cargo test -p zkbench-core --test mutation_engine
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
