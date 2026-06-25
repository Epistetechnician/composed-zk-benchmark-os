# Phase 157 — Mutation Distinguishability Scoring Implementation Notes

## Status

Implemented and tested.

## Purpose

Phase 156 deepened the mutation surface from 3 to 8 implemented `MutationClass`
variants. Without an analytical lens over that surface, "adversarial mutation
scoring" — half of the SOTA wedge — remains a label. Phase 157 introduces a
local distinguishability matrix that composes each mutation's declared
`ExpectedVerdict` with each `BackendOutcome` variant via the existing
`classify_result` to produce a deterministic complete matrix. This turns the
mutation surface into something that can be triaged.

## Surface

`crates/zkbench-core/src/scoring/distinguishability.rs` adds:

- `MutationDistinguishabilityAxis` (`TruePositive`, `DetectedRejection`,
  `UnsoundAcceptanceCandidate`, `FalseRejectionCandidate`, `Inconclusive`).
- `axis_severity(&self) -> u8` returning the documented priority values
  (4/3/2/1/0). Higher is more interesting for downstream triage.
- `MutationDistinguishabilityCell` carrying `expected_verdict`,
  `backend_outcome`, `classification`, and `axis`.
- `MutationDistinguishabilityMatrix` carrying `mutation_class` and one cell per
  `BackendOutcome` variant.
- `MutationDistinguishabilitySummary` aggregating counts per axis across
  multiple matrices, plus mandatory nonclaims.
- `classify_mutation_distinguishability(mutation_class, expected_verdict)
   -> MutationDistinguishabilityMatrix` iterating over all `BackendOutcome`
  variants. The matrix is deterministic and complete by construction — no
  sampling, no randomness.
- `summarize_mutation_distinguishability(matrices) ->
  MutationDistinguishabilitySummary`.
- `mandatory_distinguishability_nonclaims()` returning the nonclaim language
  every summary must carry.
- `DISTINGUISHABILITY_CLAIM_BOUNDARY` constant pinned at
  `ClaimBoundary::Level1LocalReplay`.

The module re-exports through `crates/zkbench-core/src/scoring/mod.rs`,
`crates/zkbench-core/src/prelude.rs`, and `crates/zkbench-core/src/lib.rs`.

## Design Decisions

### Reuse `classify_result` rather than re-implementing classification

The matrix composes each mutation's `ExpectedVerdict` with each
`BackendOutcome` by calling the existing `crate::evidence::classify_result`.
This keeps the matrix mechanically tied to the shipped classification helper.
If `classify_result` ever changes, the matrix updates through that helper. The
only local logic is `axis_for_classification`, which is a pure mapping from the
existing `ResultClassification` enum to the new axis enum.

### Complete matrix, not sampling

`classify_mutation_distinguishability` iterates over all seven `BackendOutcome`
variants. This produces a complete matrix deterministically. There is no
randomness, no sampling, and no early termination. The same inputs always
produce the same outputs, which is verified by a determinism test.

### Severity is a triage hint, not a score

`axis_severity` returns 4 for `UnsoundAcceptanceCandidate` down to 0 for
`TruePositive`. These are local-only priority hints for downstream triage,
not benchmark scores. They are not populated on any `ScoreReport` axis, and
the boundary spec explicitly forbids score-axis population. The summary is
reported separately as local analysis metadata.

## Tests

`crates/zkbench-core/src/scoring/distinguishability.rs` carries inline unit
tests for matrix completeness, axis severity values, the
`Reject` × `Accepted` → `UnsoundAcceptanceCandidate` path, summary
aggregation, and determinism.

`crates/zkbench-core/tests/phase_157_distinguishability.rs` carries 11
integration tests:

- One test exercising every `ExpectedVerdict` × `BackendOutcome` pairing,
  verifying the classification and axis are computed correctly.
- One test verifying the matrix is complete for each of the 14 declared
  `MutationClass` variants.
- One test per interesting axis mapping (unsound acceptance, detected
  rejection, false rejection, true positive).
- One test verifying summary aggregation across multiple matrices.
- One test verifying the summary carries mandatory nonclaims.
- One test verifying `axis_severity` is monotonic.
- One test verifying determinism.
- One scope-guard test asserting `ExpectedVerdict`, `BackendOutcome`, and
  `ResultClassification` variant counts are unchanged.

All 11 tests pass.

## Claim Boundary

Every distinguishability matrix and summary is local metadata analysis capped
at `Level1LocalReplay`. A cell classifying as `UnsoundAcceptanceCandidate` is a
*hypothetical* signal under a *hypothetical* backend outcome — it is not
proof, not benchmark evidence, not accepted evidence, not formal evidence, not
ZK backend performance evidence, not semantic correctness, not global
software-agent uniqueness, and not evidence that any real backend would
produce that outcome. The matrix does not call any real backend and does not
populate any `ScoreReport` axis.

## What This Does Not Do

- Does not change `ExpectedVerdict`, `BackendOutcome`, `ResultClassification`,
  `classify_result`, `ScoreReport`, `LocalMutationEvidenceSummary`, or any
  scoring constructor.
- Does not change any `MutationClass`, mutation pass, the `MutationPass` trait,
  the DSL, or the oracle.
- Does not populate any `ScoreReport` axis.
- Does not call any real backend.
- Does not produce Level2+ evidence or formal evidence.
- Does not mutate the accepted Evidence Ledger or any official submission.
