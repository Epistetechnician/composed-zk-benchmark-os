# Phase 218 External Runner Serialization Coverage Audit Notes

Status: complete for local coverage-floor audit.

## State Slice

This phase touched only:

- `docs/218-phase-external-runner-serialization-coverage-audit-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Rust source, tests, Cargo metadata, generated artifacts, accepted Evidence
Ledger state, benchmark output, or score-axis state changed.

## Purpose

Audit the next visible `zkbench-core` package coverage floor after Phase 217
confirmed `crates/zkbench-core/src/replay/serialization.rs` is capped by
structurally unreachable concrete serializer error paths.

The next measured low file is
`crates/zkbench-core/src/external_runner/serialization.rs`.

## Coverage Measurement

The local package coverage command:

```sh
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

reported for `zkbench-core`:

- region coverage: `90.28%`;
- function execution: `85.76%`;
- line coverage: `91.35%`.

The audited file reported:

- `crates/zkbench-core/src/external_runner/serialization.rs`: `76.65%` line
  coverage, `75.00%` function coverage, and `75.00%` region coverage.

The local missing-line audit command:

```sh
cargo llvm-cov report --text --show-missing-lines --output-path /tmp/zkbench-core-coverage-missing.txt
```

showed that the uncovered lines in `external_runner/serialization.rs` are only
serializer `map_err` closures around `serde_json::to_string_pretty` for these
concrete external-runner boundary types:

- `ExternalRunnerPolicy`;
- `ManualHandoffBundle`;
- `ArtifactCaptureContract`;
- `ProvenanceContract`;
- `ExternalResultImportSchema`;
- `ExternalResultCandidate`;
- `QuarantineManifest`;
- `SyntheticResultImportBundle`;
- `NormalizedExternalResultDraft`;
- `EvidenceAppendProposal`;
- `EvidenceAppendProposalLedger`.

The malformed JSON deserializer branches for those same helper pairs are
already exercised by `phase_v_coverage_hardening.rs`.

## Audit Decision

No new Rust test was added.

The remaining uncovered lines are structurally capped under the current public
API because the helpers serialize concrete derived data types. Reaching those
`serde_json::to_string_pretty` error closures would require changing those
types, adding dependency behavior, or adding a failing serializer injection path
that the production API does not expose.

That would be coverage forcing, not regression coverage.

## Next Reachable Floor

The next coverage slice should move past serializer-wrapper floors and target a
real reachable module with public behavior. In the same package coverage run,
the next visible low areas include:

- `external_runner/artifact_capture.rs` at `80.84%` line coverage;
- `adapters/zk_harness/mapping.rs` at `82.05%` line coverage;
- `evidence/external_submission_preflight_output.rs` at `82.11%` line coverage;
- `report_bundle.rs` at `82.30%` line coverage;
- `soak/artifact_layout.rs` at `83.81%` line coverage;

The next tranche should choose the lowest reachable public-API surface after a
fresh missing-line audit.

## Claim Boundary

This is a coverage audit only. It does not change external-runner semantics,
serialization semantics, production source, Cargo metadata, dependencies,
external execution, generated artifact materialization, accepted Evidence Ledger
policy, formal evidence, benchmark evidence, score-axis population, Level2+
evidence, semantic-correctness claims, production-readiness claims, unsafe
coverage forcing, coverage suppression, structurally unreachable branch forcing,
or whole-workspace 100% coverage claims.

## Validation

Validation passed for this docs-only audit:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test phase_v_coverage_hardening
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
