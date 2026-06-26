# Phase 173 External Quarantine Coverage Eighth Tranche Notes

State slice: `phase-173-coverage-eighth-tranche`.

## Claim

Phase 173 continues the bounded coverage campaign by hardening one local
external-runner quarantine module with focused tests and one behavior cleanup.
It does not change claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/external_runner/quarantine.rs`, which reported the
following package-level coverage after Phase 172:

```text
Regions:   72.48%
Functions: 66.67%
Lines:     68.32%
```

## Implemented

Focused tests now cover:

- specific quarantine reasons for Level2+ boundary, official benchmark,
  formal evidence, and proof-system soundness claims,
- absolute-path, unsupported-metric, unknown-source, and pending-review reason
  selection,
- manifest id, entry id, and source-artifact reference rejection, and
- preservation of a valid manifest status summary.

The implementation now checks absolute-path validation issues before the
generic artifact-ref/unit bucket. This reports absolute path failures as
`AbsolutePathRejected` instead of the less specific `UnsupportedMetric`.

## Result

After the tranche, the selected module reports:

```text
Regions:   100.00%
Functions: 100.00%
Lines:     100.00%
```

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   85.05%
Functions: 81.21%
Lines:     83.90%
```

The workspace coverage summary moved to:

```text
Regions:   88.49%
Functions: 85.13%
Lines:     87.15%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
cargo test -p zkbench-core --test result_import_validation
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
