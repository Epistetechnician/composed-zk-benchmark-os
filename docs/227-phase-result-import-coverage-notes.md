# Phase 227 Result Import Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/result_import_validation.rs`
- `docs/227-phase-result-import-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, result-import
semantics, quarantine semantics, or external replay behavior changed.

## Purpose

After Phase 226, the next visible low non-serializer surface routed by the
local package coverage table was
`crates/zkbench-core/src/external_runner/result_import.rs` at `83.61%` line
coverage.

This tranche adds focused regression coverage for reachable local
external-result import schema validation, candidate validation, policy toggles,
and quarantine-record context.

## Coverage Added

The added tests cover:

- schema validation for empty schema ids, elevated schema boundaries, unknown
  units, and missing required provenance-field declarations;
- candidate validation for empty candidate ids, missing source benchmark pack
  ids, missing dry-run plan ids, missing provenance drafts, rejected initial
  statuses, and unsafe raw output refs;
- metric validation for empty metric kinds, unsafe metric source refs, metric
  notes that contain forbidden claim text, and candidate notes that contain
  forbidden claim text;
- policy-controlled validation paths for source id, dry-run id, provenance,
  Level2+ request, official benchmark, formal evidence, proof-system
  soundness, and absolute raw-output path rejection toggles;
- direct quarantine-record construction preserving candidate id, quarantined
  status, requested local claim boundary, validation issue paths, and local
  quarantine notes.

These paths are exercised through the public local result-import and
quarantine APIs. They do not run backend adapters, generate official benchmark
results, mutate accepted ledgers, run external replay, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.06%` region coverage, `86.67%` function execution, and
  `92.51%` line coverage;
- `external_runner/result_import.rs`: `87.39%` region coverage, `88.89%`
  function execution, and `83.61%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.15%` region coverage, `86.73%` function execution, and
  `92.66%` line coverage;
- `external_runner/result_import.rs`: `97.83%` region coverage, `100.00%`
  function execution, and `97.95%` line coverage.

Remaining misses are limited to currently unforced local branch combinations
inside the result-import validation helpers. They are not forced in this
tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer surface is
`evidence/append_preview.rs` at `83.87%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
result-import semantics, quarantine semantics, external replay behavior,
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
cargo test -p zkbench-core --test result_import_validation
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
