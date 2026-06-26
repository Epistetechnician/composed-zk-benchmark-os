# Phase 175 Acceptance Policy Coverage Tenth Tranche Notes

State slice: `phase-175-coverage-tenth-tranche`.

## Claim

Phase 175 continues the bounded coverage campaign by hardening the local
evidence acceptance policy validator with focused tests. It does not change
policy semantics or claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/evidence/acceptance_policy.rs`, which reported the
following package-level coverage after Phase 174:

```text
Regions:   73.61%
Functions: 73.68%
Lines:     69.23%
```

## Implemented

Focused tests now cover:

- policy JSON round trip and malformed JSON error mapping,
- the `Default` policy path,
- static policy rejection for empty id, proposal-only mode, and Level2+
  allowed boundaries,
- proposal-only mode rule-result failure,
- source proposal rejection paths for non-reviewable status, rejected state,
  blocking issues, disallowed evidence class, missing artifacts, and missing
  provenance,
- changes-requested review state, and
- invalid review decision, automated-review, official, formal, and soundness
  text rejection paths.

No production code changed in this tranche.

## Result

After the tranche, the selected module reports:

```text
Regions:   98.26%
Functions: 94.74%
Lines:     98.82%
```

The remaining uncovered target-file branch is the impossible
`serde_json::to_string_pretty` serialization-error closure for a structurally
serializable policy type. It is left as an honest residual instead of being
hidden behind unsafe construction or coverage suppression.

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   85.42%
Functions: 81.61%
Lines:     84.42%
```

The workspace coverage summary moved to:

```text
Regions:   88.72%
Functions: 85.32%
Lines:     87.52%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test proposal_acceptance_policy
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
