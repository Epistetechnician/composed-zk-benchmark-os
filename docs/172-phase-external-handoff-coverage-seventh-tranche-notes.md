# Phase 172 External Handoff Coverage Seventh Tranche Notes

State slice: `phase-172-coverage-seventh-tranche`.

## Claim

Phase 172 continues the bounded coverage campaign by hardening one local
external-runner manual handoff validator module with focused tests and one
behavior-preserving source cleanup. It does not change claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/external_runner/handoff.rs`, which reported the
following package-level coverage after Phase 171:

```text
Regions:   75.69%
Functions: 100.00%
Lines:     65.64%
```

## Implemented

Focused tests now cover:

- bundle id, claim-boundary, subject, and empty-step rejection,
- step id, manual-only, instruction text, inert program, inert argument, and
  artifact-reference rejection,
- export id, relative URI, and export claim-boundary rejection,
- nested provenance-contract and result-import-schema issue forwarding, and
- `contains_manual_instructions_only` false branches for invalid step
  validation and non-manual instructions.

The implementation now delegates the manual-handoff mode check to
`ExternalExecutionMode::is_phase_h_allowed()`. This removes a redundant
live-mode disjunction without changing manual handoff validation behavior.

## Result

After the tranche, the selected module reports:

```text
Regions:   100.00%
Functions: 100.00%
Lines:     100.00%
```

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   84.91%
Functions: 81.09%
Lines:     83.73%
```

The workspace coverage summary moved to:

```text
Regions:   88.40%
Functions: 85.05%
Lines:     87.03%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
cargo test -p zkbench-core --test manual_handoff_bundle
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
