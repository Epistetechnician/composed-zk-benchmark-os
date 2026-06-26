# Phase 179 zkML Coverage Fourteenth Tranche Notes

State slice: `phase-179-zkml-coverage-fourteenth-tranche`.

## Claim

Phase 179 continues the bounded local coverage campaign by hardening the inert
Phase N zkML workload manifest validation surface in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

## Implemented Coverage

- `ZkMlWorkloadManifestVersion::default()`.
- `ZkMlMetricKind::requires_executable_adapter()` for every declared metric kind.
- Missing top-level identity fields.
- Missing source inputs, public inputs, private witnesses, model artifacts, and
  threshold policy metadata.
- Invalid workload digest root shape.
- Input id, artifact ref, digest, append-preview boundary, and Level2
  eligibility boundary rejection paths.
- Model artifact id, artifact ref, digest, and claim-boundary rejection paths.
- Output claim-boundary escalation, weakest-input boundary escalation,
  executable-adapter authorization, executable metric value, metric-boundary
  escalation, and missing limitation rejection paths.
- Malformed manifest JSON deserialization context.

## Coverage Result

Baseline target-file coverage before this tranche:

```text
crates/zkbench-core/src/zkml.rs
Regions:   82.42%
Functions: 87.50%
Lines:     71.68%
```

Post-tranche target-file coverage:

```text
crates/zkbench-core/src/zkml.rs
Regions:   97.80%
Functions: 93.75%
Lines:     98.53%
```

Post-tranche `zkbench-core` package coverage:

```text
Regions:   86.26%
Functions: 82.18%
Lines:     85.99%
```

Post-tranche workspace coverage:

```text
Regions:   89.27%
Functions: 85.71%
Lines:     88.63%
```

The remaining counted target-file uncovered spans are the defensive
`compute_zkml_workload_digest_root` error branch inside validation and the
`serialize_zkml_workload_manifest_json` serialization-error closure. Both are
not reachable through ordinary valid public construction without changing
semantics or forcing artificial serde failure.

## Validation

```sh
cargo test -p zkbench-core --test phase_179_zkml_coverage
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov -p zkbench-core --all-features --json
cargo llvm-cov --workspace --all-features --json --summary-only
```

The full gate set for the tranche is recorded in
`docs/90-whole-codebase-validation-report.md`.

## Nonclaims

This tranche is local Rust regression coverage only. It is not zkML execution,
not a zkML adapter, not model-accuracy evidence, not proof-system soundness
evidence, not semantic correctness, not benchmark evidence, not accepted
Evidence Ledger mutation, not formal evidence, not Level2+ evidence, not
production readiness, and not whole-workspace 100% coverage.
