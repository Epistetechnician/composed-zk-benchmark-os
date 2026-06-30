# Phase 222 zk-Harness Mapping Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/zk_harness_pack_mapping.rs`
- `docs/222-phase-zk-harness-mapping-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, zk-Harness adapter
semantics, or external execution behavior changed.

## Purpose

After Phase 221, the next visible low non-serializer public surface in the
`zkbench-core` package coverage table was
`crates/zkbench-core/src/adapters/zk_harness/mapping.rs` at `82.05%` line
coverage.

This tranche adds focused regression coverage for reachable zk-Harness
candidate mapping behavior.

## Coverage Added

The added tests cover:

- current family-label helper coverage for recursive, memory-heavy,
  public/private-boundary, and zkML control-flow families;
- unsupported mutation-label helper coverage;
- invalid source-pack rejection before mapping;
- malformed generated-instance payload rejection after digest-repaired pack
  validation;
- malformed mutated-instance payload rejection after digest-repaired pack
  validation;
- missing optional generated-instance payload rejection after pack validation;
- unsupported mutation-class warning and unsupported-feature recording;
- non-default expected outcome labels for backend-error, capability-gap, and
  inconclusive traces.

These paths are exercised through public pack writer/reader APIs and the
public zk-Harness mapping function. They do not execute zk-Harness or import
external results.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.44%` region coverage, `85.99%` function execution, and
  `91.66%` line coverage;
- `adapters/zk_harness/mapping.rs`: `81.33%` region coverage, `85.71%`
  function execution, and `82.05%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.56%` region coverage, `86.10%` function execution, and
  `91.76%` line coverage;
- `adapters/zk_harness/mapping.rs`: `94.67%` region coverage, `100.00%`
  function execution, and `94.36%` line coverage.

The remaining uncovered mapping regions are capped under the current API shape:
all current `FamilyKind` variants have candidate labels, so the unsupported
family branch is not constructible, and `compute_artifact_digest` over the
concrete pack manifest is not expected to fail during local mapping.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer public surface is
`evidence/external_submission_preflight_output.rs` at `82.11%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
zk-Harness adapter semantics, pack semantics, mutation semantics, generator
semantics, Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable branch forcing, or whole-workspace 100% coverage
claims.

## Validation

Validation passed for this tranche:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test zk_harness_pack_mapping
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
