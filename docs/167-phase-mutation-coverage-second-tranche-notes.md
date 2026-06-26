# Phase 167 Mutation Coverage Second Tranche Notes

State slice: `phase-167-coverage-second-tranche`.

## Claim

Phase 167 continues the bounded mutation coverage campaign by hardening one
additional local mutation module with focused tests. It does not change
production behavior or claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/mutation/trace_ordering_corruption.rs`, which reported
the following package-level coverage after Phase 166:

```text
Regions:   83.33%
Functions: 33.33%
Lines:     69.44%
```

## Implemented

Focused tests now cover:

- the mutation pass class reporter,
- deterministic swapping of the first two accepted trace steps,
- provenance transition ids, description, and notes on the success path,
- fail-closed behavior when no accepted trace exists, and
- fail-closed behavior when the accepted trace has fewer than two steps.

## Result

After the tranche, the selected module reports:

```text
Regions:   100.00%
Functions: 100.00%
Lines:     100.00%
```

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   84.39%
Functions: 80.34%
Lines:     83.05%
```

The workspace-level coverage summary after this tranche reports:

```text
Regions:   88.05%
Functions: 84.45%
Lines:     86.55%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
cargo test -p zkbench-core --test phase_161_mutation_completion
cargo llvm-cov --workspace --all-features --summary-only
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
