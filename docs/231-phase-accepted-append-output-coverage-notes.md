# Phase 231 Accepted Append Output Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/phase_184_accepted_append_output_coverage.rs`
- `docs/231-phase-accepted-append-output-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, accepted-append
semantics, accepted-append output semantics, endpoint submission behavior, or
external replay behavior changed.

## Purpose

After Phase 230, the next visible low non-serializer surface routed by the
local package coverage table was
`crates/zkbench-core/src/evidence/accepted_append_output.rs` at `86.36%` line
coverage.

This tranche adds focused regression coverage for the remaining reachable
public materialized accepted-ledger append path guard.

## Coverage Added

The added test covers root-path rejection for materialized accepted-ledger
append requests. That exercises the public `validate_ledger_path` parent-path
guard and proves that a root path is rejected before any ledger write is
attempted.

The remaining uncovered lines in `accepted_append_output.rs` are internal
`write_ledger_atomically` parent/file-name error closures. They are unreachable
through the public API because `validate_ledger_path` rejects non-materializable
paths before atomic writing starts. This tranche records that cap instead of
weakening the production guard or forcing structurally unreachable branches.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.51%` region coverage, `87.19%` function execution, and
  `93.20%` line coverage;
- `evidence/accepted_append_output.rs`: `78.95%` region coverage, `57.14%`
  function execution, and `86.36%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.53%` region coverage, `87.24%` function execution, and
  `93.21%` line coverage;
- `evidence/accepted_append_output.rs`: `82.24%` region coverage, `64.29%`
  function execution, and `90.00%` line coverage.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer file in the current coverage table is
`dsl/ir.rs` at `85.19%` line coverage, subject to a fresh missing-line audit
before mutation.

## Claim Boundary

This is local regression coverage only. It does not change production source,
accepted-append semantics, accepted-append output semantics, endpoint
submission behavior, credential handling, accepted Evidence Ledger policy,
formal evidence, benchmark evidence, score-axis population, generated artifact
materialization, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_184_accepted_append_output_coverage
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
