# Phase 166 Mutation Coverage First Tranche Notes

State slice: `phase-166-coverage-first-tranche`.

## Claim

Phase 166 starts the path toward higher end-to-end coverage by hardening one
bounded local mutation module with focused tests. It does not change production
behavior or claim strength.

## Baseline

Fresh workspace coverage before this tranche:

```text
TOTAL regions:   87.94%
TOTAL functions: 84.18%
TOTAL lines:     86.40%
Branch coverage: not reported
```

The first selected target was
`crates/zkbench-core/src/mutation/public_private_boundary_mismatch.rs`, which
had weak coverage:

```text
Regions:   55.41%
Functions: 20.00%
Lines:     50.00%
```

## Implemented

Focused tests now cover:

- the mutation pass class reporter,
- public-input witness-policy movement,
- public-field reclassification when witness policy is empty,
- observed-field reclassification when all fields are already private,
- fail-closed behavior when no public or observed target exists, and
- fail-closed behavior when no declared trace exists.

## Result

After the tranche, the selected module reports:

```text
Regions:   98.65%
Functions: 100.00%
Lines:     100.00%
```

One region remains uncovered in the module under LLVM region accounting, while
line and function coverage for the module are complete.

## Validation

Focused validation:

```sh
cargo test -p zkbench-core --test phase_161_mutation_completion
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, and not production readiness.
