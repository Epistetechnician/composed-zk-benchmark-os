# Phase 230 Audit Index Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/phase_r_audit_index.rs`
- `docs/230-phase-audit-index-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, audit-index
semantics, audit-index ergonomics semantics, cross-bundle audit-index
semantics, pack writer/reader semantics, or external replay behavior changed.

## Purpose

After Phase 229, the next visible low non-serializer surface routed by the
local package coverage table was `crates/zkbench-core/src/audit_index.rs` at
`83.71%` line coverage.

This tranche adds focused regression coverage for reachable local Phase R
audit-index validation and readback paths.

## Coverage Added

The added tests cover:

- malformed audit-index manifest JSON deserialization context;
- empty `index_id`, `version.value`, and `indexed_pack_id` validation paths;
- duplicate input id and duplicate artifact URI validation paths;
- missing required limitation labels;
- missing inputs without elevating the validation report boundary;
- file output roots rejected during writes;
- missing materialized audit-index files rejected during reads;
- non-UTF-8 digest sidecars rejected during reads;
- digest-consistent non-UTF-8 manifests rejected during reads;
- digest-consistent invalid manifests rejected after local validation.

These paths are exercised through the public local audit-index APIs. They do
not mutate accepted ledgers, run backend adapters, generate official benchmark
results, run external replay, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.38%` region coverage, `87.02%` function execution, and
  `92.97%` line coverage;
- `audit_index.rs`: `83.71%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.51%` region coverage, `87.19%` function execution, and
  `93.20%` line coverage;
- `audit_index.rs`: `85.51%` region coverage, `74.07%` function execution, and
  `86.49%` line coverage.

Remaining misses are concentrated in Phase S/Phase T materialized-view
readback and protected-path branch combinations, cross-bundle grouping/sorting
variants, and filesystem error paths. They are not forced in this tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer surface in the current coverage table
is `evidence/accepted_append_output.rs` at `86.36%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
audit-index semantics, audit-index ergonomics semantics, cross-bundle
audit-index semantics, pack writer/reader semantics, external replay behavior,
endpoint submission behavior, credential handling, accepted Evidence Ledger
policy, formal evidence, benchmark evidence, score-axis population, generated
artifact materialization, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_r_audit_index
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
