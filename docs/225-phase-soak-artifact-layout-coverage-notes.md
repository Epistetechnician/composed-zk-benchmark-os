# Phase 225 Soak Artifact Layout Coverage Notes

Status: complete for local coverage hardening.

## State Slice

This phase touched only:

- `crates/zkbench-core/tests/phase_l_soak_campaign.rs`
- `docs/225-phase-soak-artifact-layout-coverage-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No production Rust source, Cargo metadata, generated artifacts, accepted
Evidence Ledger state, benchmark output, score-axis state, soak artifact-layout
semantics, report-bundle semantics, or external replay behavior changed.

## Purpose

After Phase 224, the next visible low non-serializer surface routed by the
local package coverage table was
`crates/zkbench-core/src/soak/artifact_layout.rs` at `83.81%` line coverage.

This tranche adds focused regression coverage for reachable local soak
report-bundle validation and filesystem read/write behavior.

## Coverage Added

The added tests cover:

- bundle-level claim-boundary drift;
- nested shard-plan claim-boundary drift;
- artifact relative-path drift inside a report bundle;
- artifact claim-boundary drift inside a report bundle;
- health-report artifact count drift;
- failure-corpus-index artifact count drift;
- report-bundle writes rejecting file roots;
- report-bundle writes rejecting non-empty directories;
- report-bundle writes rejecting invalid bundles before materialization;
- report-bundle write/read round trips;
- readback rejection for missing `soak_report_bundle.json`;
- readback rejection for malformed bundle JSON.

These paths are exercised through the public local soak report-bundle
validation, write, and readback APIs. They do not generate official benchmark
results, mutate accepted ledgers, run external replay, or populate score axes.

## Coverage Measurement

Before this tranche, the full local package coverage run reported:

- `zkbench-core`: `90.82%` region coverage, `86.28%` function execution, and
  `92.33%` line coverage;
- `soak/artifact_layout.rs`: `77.19%` region coverage, `60.71%` function
  execution, and `83.81%` line coverage.

After this tranche, the full local package coverage run reported:

- `zkbench-core`: `91.03%` region coverage, `86.56%` function execution, and
  `92.48%` line coverage;
- `soak/artifact_layout.rs`: `88.49%` region coverage, `78.57%` function
  execution, and `93.73%` line coverage.

Remaining misses are mostly filesystem error closures, serde serialization
error closures for infallible in-memory structs, digest computation error
closures, and platform-specific path component branches. They are not forced in
this tranche.

After ignoring serializer-wrapper floors already audited in Phases 217 and
218, the next visible low non-serializer surface is
`mutation/observation_omission.rs` at `83.33%` line coverage.

## Claim Boundary

This is local regression coverage only. It does not change production source,
soak artifact-layout semantics, report-bundle semantics, external replay
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
cargo test -p zkbench-core --test phase_l_soak_campaign
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
