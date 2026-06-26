# Phase 177 Promotion Preflight Coverage Twelfth Tranche Notes

State slice: `phase-177-coverage-twelfth-tranche`.

## Claim

Phase 177 continues the bounded coverage campaign by hardening local reviewed
promotion preflight and official-submission package metadata validation tests.
It does not change promotion semantics or claim strength.

## Baseline

The selected target was
`crates/zkbench-core/src/evidence/promotion_preflight.rs`, which reported the
following package-level coverage after Phase 176:

```text
Regions:   81.35%
Functions: 88.57%
Lines:     70.49%
```

## Implemented

Focused tests now cover:

- reviewed-promotion preflight empty request identity rejection,
- invalid candidate and invalid append-preview forwarding,
- append-preview mutation flag rejection,
- candidate/preview mismatch rejection,
- non-`PreviewOnly` append-preview status rejection,
- review decision id/source/kind/status rejection,
- malformed and missing source artifact digests,
- missing required nonclaims,
- unresolved quarantine and blocking markers,
- score-axis rejection for local evidence classes at a Level2 request boundary,
- official, formal, broad leaderboard, and local-soak performance claim text,
- invalid-report Markdown issue rendering,
- missing report nonclaims during Markdown rendering,
- malformed reviewed-promotion preflight JSON error mapping,
- official-submission package empty identity, source pack, replay provenance,
  artifact digest, nonclaim, and forbidden text rejection,
- invalid official-submission package Markdown rejection, and
- malformed official-submission package JSON error mapping.

No production code changed in this tranche.

## Result

After the tranche, the selected module reports:

```text
Regions:   98.05%
Functions: 94.29%
Lines:     98.62%
```

The remaining uncovered target-file spans are the `serde_json::to_string_pretty`
serialization-error closures for structurally serializable metadata structs,
plus a narrow external-provenance scanner loop edge already covered for
forbidden text semantics. These are left as honest residuals instead of being
hidden behind unsafe construction, coverage suppression, or behavior changes.

The package-level `zkbench-core` coverage summary moved to:

```text
Regions:   85.95%
Functions: 81.83%
Lines:     85.44%
```

The workspace coverage summary moved to:

```text
Regions:   89.06%
Functions: 85.48%
Lines:     88.24%
```

## Validation

Focused validation:

```sh
cargo fmt --all -- --check
git diff --check
cargo test -p zkbench-core --test phase_w_promotion_preflight
cargo llvm-cov -p zkbench-core --all-features --json --summary-only
cargo llvm-cov --workspace --all-features --json --summary-only
```

Nonclaims: this tranche is local regression coverage only. It is not proof,
not semantic correctness, not benchmark evidence, not accepted evidence, not
Level2+ evidence, not whole-workspace 100% coverage, and not production
readiness.
