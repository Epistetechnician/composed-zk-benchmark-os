# Phase 219 External Runner Artifact Capture Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/artifact_capture_contract.rs`
- `docs/219-phase-external-runner-artifact-capture-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, or external runner
runtime behavior changed.

## Purpose

Phase 218 routed coverage work away from serializer wrappers and toward a
reachable public API. The next fresh package summary showed
`crates/zkbench-core/src/external_runner/artifact_capture.rs` at `80.84%` line
coverage.

This tranche adds focused regression coverage for that artifact-capture
contract surface.

## Coverage Added

The added tests cover:

- default artifact formats, requirements, relative path hints, and nonclaim
  notes;
- empty contract id rejection;
- claim-boundary elevation rejection;
- empty expected-artifact id rejection;
- expected-artifact traversal path rejection;
- captured-artifact warning emission;
- unreviewed captured-artifact warning emission;
- captured-artifact traversal URI rejection.

These are normal public validator paths, not synthetic serializer failures.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.28%` region coverage, `85.76%` function execution, and
  `91.35%` line coverage;
- `external_runner/artifact_capture.rs`: `82.69%` region coverage, `87.50%`
  function execution, and `80.84%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.37%` region coverage, `85.82%` function execution, and
  `91.48%` line coverage;
- `external_runner/artifact_capture.rs`: `98.08%` region coverage, `100.00%`
  function execution, and `99.40%` line coverage.

The remaining lower file entries are no longer this artifact-capture surface.
The fresh table still includes serializer-wrapper floors at
`replay/serialization.rs` and `external_runner/serialization.rs`; those were
audited as structurally capped in Phases 217 and 218. Among non-serializer
surfaces, the next visible low areas include `generator/config.rs` at `80.23%`
line coverage, `mutation/missing_constraints.rs` at `80.43%` line coverage,
and `adapters/zk_harness/mapping.rs` at `82.05%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
artifact-capture semantics, external-runner semantics, Cargo metadata,
dependencies, external execution, generated artifact materialization, accepted
Evidence Ledger policy, formal evidence, benchmark evidence, score-axis
population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test artifact_capture_contract
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
