# Phase 226 Observation Omission Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/phase_156_mutation_depth.rs`
- `docs/226-phase-observation-omission-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, mutation semantics,
or external replay behavior changed.

## Purpose

After Phase 225, the next visible low non-serializer surface routed by the
local package coverage table was
`crates/zkbench-core/src/mutation/observation_omission.rs` at `83.33%` line
coverage.

This tranche adds focused regression coverage for reachable local
ObservationOmission fail-closed and trace-rewrite behavior.

## Coverage Added

The added tests cover:

- fail-closed rejection when the source instance declares no public
  observation;
- fail-closed rejection when an observation exists but no accepted or rejected
  trace exists;
- removing the selected observation from the mutated surface spec;
- injecting the sentinel final-field mismatch into the primary trace;
- replacing the accepted trace copy inside the mutated surface spec;
- replacing the rejected trace copy when no accepted trace exists;
- preserving local diagnostic notes that explain the sentinel mismatch.

These paths are exercised through the public local mutation pass API. They do
not run backend adapters, generate official benchmark results, mutate accepted
ledgers, run external replay, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.03%` region coverage, `86.56%` function execution, and
  `92.48%` line coverage;
- `mutation/observation_omission.rs`: `87.50%` region coverage, `57.14%`
  function execution, and `83.33%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.06%` region coverage, `86.67%` function execution, and
  `92.51%` line coverage;
- `mutation/observation_omission.rs`: `96.59%` region coverage, `85.71%`
  function execution, and `95.45%` line coverage.

Remaining misses are capped by the current helper shape around in-slice trace
replacement and validation composition. They are not forced in this tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer surface is
`external_runner/result_import.rs` at `83.61%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
mutation semantics, oracle semantics, generator semantics, external replay
behavior, endpoint submission behavior, credential handling, accepted Evidence
Ledger policy, formal evidence, benchmark evidence, score-axis population,
generated artifact materialization, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable branch forcing, or whole-workspace 100%
coverage claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_156_mutation_depth
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
