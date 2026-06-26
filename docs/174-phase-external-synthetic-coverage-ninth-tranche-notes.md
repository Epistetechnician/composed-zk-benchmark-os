# Phase 174 External Synthetic Coverage Ninth Tranche Notes

State slice: `phase-174-coverage-ninth-tranche`.

## Claim

Phase 174 continues the bounded coverage campaign by hardening one local
external-runner synthetic quarantine helper with focused tests. It does not
change claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/external_runner/synthetic.rs`, which reported the
following package-level coverage after Phase 173:

```text
Regions:   69.88%
Functions: 72.73%
Lines:     69.05%
```

## Implemented

Focused tests now cover:

- synthetic quarantine reason selection for claim-boundary, official
  benchmark, formal evidence, proof-system soundness, digest mismatch, invalid
  digest, provenance, and metric rejection kinds,
- the pending-review fallback for non-classified synthetic validation issues,
  and
- priority ordering when multiple synthetic validation issues are present.

No production code changed in this tranche.

## Result

After the tranche, the selected module reports:

```text
Regions:   100.00%
Functions: 100.00%
Lines:     100.00%
```

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   85.14%
Functions: 81.38%
Lines:     84.01%
```

The workspace coverage summary moved to:

```text
Regions:   88.55%
Functions: 85.24%
Lines:     87.23%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test synthetic_result_import
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
