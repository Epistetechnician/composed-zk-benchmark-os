# Phase 181 Soak Shard Coverage Sixteenth Tranche Notes

State slice: `phase-181-soak-shard-coverage-sixteenth-tranche`.

## Claim

Phase 181 continues the bounded local coverage campaign by hardening the
deterministic local soak shard planning and validation surface in
`crates/zkbench-core`. The tranche adds focused local regression tests for
existing public contracts only. It changes no production Rust source.

## Implemented Coverage

- Public helper paths for `SoakShardProgress::new`, `SoakShardId::from_index`,
  `SoakShardResumeToken::new`, and `SoakShardPlanner::new().plan()`.
- `max_cases_per_shard` overflow rejection in shard planning.
- Shard-plan drift rejection for invalid nested manifests, config digest drift,
  duplicate assignment, and missing assignment.
- Shard-manifest validation for empty ids, invalid indexes, shard-count drift,
  claim-boundary drift, and nonportable artifact references.
- Shard-summary validation for empty ids, claim-boundary drift, impossible
  progress counters, and valid partial-progress neutral status paths.

## Coverage Result

Baseline target-file coverage before this tranche:

```text
crates/zkbench-core/src/soak/shard.rs
Regions:   84.88%
Functions: 75.00%
Lines:     73.55%
```

Post-tranche target-file coverage:

```text
crates/zkbench-core/src/soak/shard.rs
Regions:   97.94%
Functions: 100.00%
Lines:     98.91%
```

Post-tranche `zkbench-core` package coverage:

```text
Regions:   86.73%
Functions: 82.46%
Lines:     86.74%
```

Post-tranche workspace coverage:

```text
Regions:   89.57%
Functions: 85.91%
Lines:     89.16%
```

The next package coverage floor after this tranche is
`crates/zkbench-core/src/evidence/eligibility.rs` at `73.75%` line coverage.

## Validation

```sh
cargo test -p zkbench-core --test phase_181_soak_shard_coverage
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

The full gate set for the tranche is recorded in
`docs/90-whole-codebase-validation-report.md`.
