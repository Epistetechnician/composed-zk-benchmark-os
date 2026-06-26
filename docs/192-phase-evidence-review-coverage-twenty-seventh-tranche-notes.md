# Phase 192 Evidence Review Coverage Twenty-Seventh Tranche Notes

State slice: `phase-192-evidence-review-coverage-twenty-seventh-tranche`.

## Claim

Phase 192 continues the bounded local coverage campaign by hardening reachable
manual evidence-review policy and decision behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 192 therefore targets the next reachable pure-data floor,
`evidence/review.rs`, without forcing unreachable branches or suppressing
coverage.

## Implemented Coverage

- Evidence review policy default id, required human reviewer roles, and
  nonclaim notes.
- Reviewer-role human/non-human classification, including
  `FutureExternalReviewer` and `AutomatedPolicyCheck`.
- Direct rejection and changes-requested review decision builders.
- Future append-preview review routing through `review_evidence_append_proposal`.
- Candidate-only approval rejection when reviewer role, checklist, id, or
  source proposal shape is invalid.
- Forbidden claim-language scanning across decision notes, blocking issues,
  findings, and checklist-item notes.
- Checklist helper behavior for empty and optional-only item sets.
- Review checklist JSON round-trip and malformed checklist/decision JSON
  deserialization contexts.

## Coverage Result

Baseline target: `evidence/review.rs` reported `73.60%` region coverage,
`76.67%` function execution, and `77.40%` line coverage.

Post-tranche target: `evidence/review.rs` reported `95.03%` region coverage,
`93.33%` function execution, and `95.36%` line coverage.

Post-tranche `zkbench-core` package coverage reported `88.73%` region coverage,
`84.05%` function execution, and `89.34%` line coverage.

Post-tranche workspace coverage reported `90.87%` region coverage, `87.01%`
function execution, and `91.00%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `pack/reader.rs` at `77.40%` line
coverage.

## Nonclaims

Phase 192 does not change manual-review semantics, evidence-review policy
semantics, production source, Cargo metadata, dependencies, external execution,
generated artifact materialization, accepted Evidence Ledger policy, formal
evidence, benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.
