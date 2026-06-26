# Phase 171 Mutation Coverage Sixth Tranche Notes

State slice: `phase-171-coverage-sixth-tranche`.

## Claim

Phase 171 continues the bounded mutation coverage campaign by hardening one
additional local mutation module with focused tests and one behavior-preserving
source cleanup. It does not change claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/mutation/corrupted_guards.rs`, which reported the
following package-level coverage after Phase 170:

```text
Regions:   85.33%
Functions: 33.33%
Lines:     80.39%
```

## Implemented

Focused tests now cover:

- the mutation pass class reporter,
- guard-provenance metadata for the mutated transition,
- fail-closed behavior when no accepted trace exists,
- skipping an accepted trace step that references a missing transition, and
- fail-closed behavior when guards are raw text and not corruptible.

The implementation now carries the selected transition index through target
selection before mutating the cloned surface. This removes an impossible
fallible re-lookup edge without changing emitted provenance or mutation
semantics.

## Result

After the tranche, the selected module reports:

```text
Regions:   100.00%
Functions: 100.00%
Lines:     100.00%
```

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   84.65%
Functions: 81.04%
Lines:     83.33%
```

The workspace coverage summary moved to:

```text
Regions:   88.23%
Functions: 84.97%
Lines:     86.75%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
cargo test -p zkbench-core --test mutation_engine
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
