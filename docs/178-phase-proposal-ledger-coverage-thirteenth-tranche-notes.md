# Phase 178 Proposal Ledger Coverage Thirteenth Tranche Notes

State slice: `phase-178-coverage-thirteenth-tranche`.

## Claim

Phase 178 continues the bounded coverage campaign by hardening local evidence
append proposal ledger tests. It does not change proposal-ledger semantics or
claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/external_runner/proposal_ledger.rs`, which reported the
following package-level coverage after Phase 177:

```text
Regions:   76.50%
Functions: 62.50%
Lines:     71.50%
```

## Implemented

Focused tests now cover:

- `Default` construction matching `new`,
- multi-entry append chaining with previous-digest linkage,
- sequence-number drift detection,
- previous-digest drift detection,
- proposal-validation issue forwarding from stored entries,
- future-append proposal state mismatch rejection,
- entry-digest mismatch after entry mutation,
- JSON save failure when the destination is a directory,
- missing JSON file load failure, and
- malformed JSON file load error mapping.

No production code changed in this tranche.

## Result

After the tranche, the selected module reports:

```text
Regions:   93.59%
Functions: 93.75%
Lines:     92.27%
```

The remaining uncovered target-file spans are defensive or unreachable through
normal public construction: accepted-evidence append rejection for a proposal
type whose `is_accepted_evidence()` method always returns false, a
post-validation claim-boundary guard already rejected by proposal validation,
and serialization-error closures for structurally serializable ledger digest and
save paths. These are left as honest residuals instead of being hidden behind
unsafe construction, coverage suppression, or behavior changes.

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   86.10%
Functions: 82.12%
Lines:     85.61%
```

The workspace coverage summary moved to:

```text
Regions:   89.16%
Functions: 85.68%
Lines:     88.36%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test proposal_ledger
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
