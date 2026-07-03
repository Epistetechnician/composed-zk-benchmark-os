# Phase 359 HSAI Proposal Candidate Review Metadata Notes

State slice: `Phase 359 HSAI proposal candidate review metadata implementation`.

Phase 359 implements deterministic pure-data review metadata over one Phase 357
accepted-evidence proposal candidate. The review stores only digests, reviewer
metadata, proposal metadata, a bounded review label, explicit nonclaims, and
nonpromotion flags. It does not write filesystem artifacts, mutate the accepted
Evidence Ledger, change accepted append policy, create accepted formal evidence,
create Level2+ evidence, populate score axes, generate proof artifacts,
generate checker transcripts, generate solver certificates, run Lean, run SMT,
run COBALT, run Rust-to-Lean extraction, submit benchmarks, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough status,
claim full security, or grant authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneProposalCandidateReviewInput`;
- `GatewayFormalRealCommandLaneProposalCandidateReview`;
- `GatewayFormalRealCommandLaneProposalCandidateReviewLabel`;
- `GatewayFormalRealCommandLaneProposalCandidateReviewIssue`;
- `GatewayFormalRealCommandLaneProposalCandidateReviewValidation`;
- `gateway_formal_real_command_lane_proposal_candidate_review_claim_boundary`;
- `gateway_formal_real_command_lane_proposal_candidate_review_required_nonclaims`;
- `build_gateway_formal_real_command_lane_proposal_candidate_review`;
- `validate_gateway_formal_real_command_lane_proposal_candidate_review_input`.

## Review Labels

The implemented review labels are:

- `proposal_candidate_scope_acceptable`;
- `proposal_candidate_rejected`;
- `proposal_policy_blocked`;
- `accepted_append_decision_still_blocked`;
- `accepted_ledger_mutation_still_blocked`.

The two accepted-append blocking labels remain non-promotional. They do not
authorize accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, or score axes.

## Required Bindings

Each review input must bind:

- one Phase 357 proposal candidate digest;
- one Phase 357 proposal candidate input digest;
- one Phase 355 materialized audit package review digest;
- one Phase 353 materialized audit package manifest digest;
- one Phase 351 serialization-preview review digest;
- one Phase 349 serialization-preview digest;
- one Phase 347 audit package digest;
- one Phase 345 review record digest;
- one Phase 343 local reviewed metadata digest;
- declared file digest map digest;
- explicit nonclaims and their digest;
- reviewer policy id;
- reviewer decision id;
- proposal policy id;
- proposal candidate id;
- proposal review id;
- reviewer decision timestamp;
- current accepted append blocker digest;
- candidate disposition label;
- proposal-candidate review label.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid proposal review id;
- invalid reviewer policy id;
- invalid reviewer decision id;
- invalid proposal policy id;
- invalid proposal candidate id;
- missing reviewer decision timestamp;
- zero required digests;
- Phase 357 candidate digest drift;
- promoted or drifted Phase 357 candidate state;
- accepted append blocker drift;
- nonclaim drift;
- promotional `accepted_append_policy_review_required` candidate disposition;
- review summaries that claim accepted evidence, Level2+ evidence, score-axis
  evidence, proof authority, checker authority, solver-certificate authority,
  benchmark evidence, semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority;
- accepted evidence mutation requests;
- accepted append policy change requests;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof artifact promotion;
- checker transcript promotion;
- solver certificate promotion;
- benchmark or SOTA comparison claims;
- semantic correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- action-authority claims.

## Claim Boundary

The maximum claim after Phase 359 is:

HSAI can locally review one accepted-evidence proposal candidate while
preserving the current accepted append and accepted-ledger blockers.

This is not accepted evidence, not formal proof, not backend execution, not a
Lean/SMT/COBALT run, not Rust-to-Lean extraction evidence, not Level2+ evidence,
not score-axis evidence, not semantic correctness, not production readiness, not
SOTA, not breakthrough status, and not full security.

## Tests

Phase 359 adds tests that:

- build deterministic proposal candidate review metadata;
- verify the review binds the Phase 357 candidate digest;
- verify the review binds the Phase 357 candidate input digest;
- verify the review binds the Phase 355 review digest;
- verify blocking review labels remain non-promotional;
- reject Phase 357 candidate digest drift;
- reject promotional review-summary text;
- reject accepted-evidence, Level2, score-axis, proof, checker, solver, SOTA,
  full-security, and action-authority promotion attempts;
- reject the promotional `accepted_append_policy_review_required` candidate
  disposition.

## Next Slice

Phase 360 should define a docs-first boundary for packaging a reviewed proposal
candidate as local append-decision preflight metadata. That boundary must keep
preflight metadata separate from accepted formal evidence, accepted Evidence
Ledger mutation, accepted append policy changes, Level2+ evidence, score axes,
Lean execution, SMT execution, COBALT execution, Rust-to-Lean extraction,
semantic correctness, production readiness, SOTA, breakthrough status, full
security, and action authority.
