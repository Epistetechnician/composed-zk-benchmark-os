# Phase 176 Evidence Candidate Coverage Eleventh Tranche Notes

State slice: `phase-176-coverage-eleventh-tranche`.

## Claim

Phase 176 continues the bounded coverage campaign by hardening the local
evidence-record candidate validator and constructor with focused tests. It does
not change candidate semantics or claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/evidence/candidate.rs`, which reported the following
package-level coverage after Phase 175:

```text
Regions:   76.33%
Functions: 78.57%
Lines:     69.92%
```

## Implemented

Focused tests now cover:

- candidate-only policy creation of design-note candidates,
- invalid policy rejection before candidate creation,
- non-candidate policy mode rejection,
- rejected and superseded candidate status behavior,
- malformed candidate JSON error mapping,
- acceptance-validation failure through the public constructor,
- Level2+ boundary and claim-flag rejection,
- each individual candidate claim flag,
- each disallowed evidence class,
- empty local metadata, missing artifact digest, invalid acceptance validation,
  and forbidden claim text rejection, and
- missing-provenance rejection.

No production code changed in this tranche.

## Result

After the tranche, the selected module reports:

```text
Regions:   96.14%
Functions: 92.86%
Lines:     93.50%
```

The remaining uncovered target-file spans are defensive or unreachable through
the public constructor and validator:

- invalid policy-mode rejection after policy validation already rejects
  non-candidate modes,
- future external replay candidate kind selection after the constructor narrows
  target boundaries to Level0 or Level1,
- created-candidate validation failure after acceptance-policy validation
  prevents invalid proposal metadata from constructing a candidate, and
- the `serde_json::to_string_pretty` serialization-error closure for a
  structurally serializable candidate type.

These are left as honest residuals instead of being hidden behind unsafe
construction, coverage suppression, or behavior changes.

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   85.58%
Functions: 81.72%
Lines:     84.66%
```

The workspace coverage summary moved to:

```text
Regions:   88.82%
Functions: 85.40%
Lines:     87.69%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test evidence_record_candidate
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
