# Phase 437 HSAI Tiny Z3 Proposal Candidate Review Notes

State slice: `Phase 437 HSAI tiny Z3 proposal candidate review metadata`.

Phase 437 implements deterministic pure-data review metadata over one Phase
435 tiny-Z3 accepted-evidence proposal candidate. The review stores only
digests, reviewer metadata, proposal metadata, candidate disposition, bounded
review label, explicit nonclaims, and nonpromotion flags. It does not write
filesystem artifacts, mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run new SMT, run COBALT, run
Rust-to-Lean extraction, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyDigestBackendZ3ProposalCandidateReviewInput`;
- `GatewayFormalTinyDigestBackendZ3ProposalCandidateReview`;
- `GatewayFormalTinyDigestBackendZ3ProposalCandidateReviewLabel`;
- `GatewayFormalTinyDigestBackendZ3ProposalCandidateReviewIssue`;
- `GatewayFormalTinyDigestBackendZ3ProposalCandidateReviewValidation`;
- `gateway_formal_tiny_digest_backend_z3_proposal_candidate_review_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_proposal_candidate_review_required_nonclaims`;
- `build_gateway_formal_tiny_digest_backend_z3_proposal_candidate_review`;
- `validate_gateway_formal_tiny_digest_backend_z3_proposal_candidate_review_input`.

## Review Labels

The implemented review labels are:

- `tiny_z3_proposal_candidate_scope_acceptable`;
- `tiny_z3_proposal_candidate_rejected`;
- `tiny_z3_proposal_policy_blocked`;
- `tiny_z3_accepted_append_decision_still_blocked`;
- `tiny_z3_accepted_ledger_mutation_still_blocked`.

The accepted-append blocking labels remain non-promotional. They do not
authorize accepted append policy changes, accepted Evidence Ledger mutation,
accepted evidence, Level2+ evidence, or score axes.

## Required Bindings

Each review input must bind:

- one Phase 435 proposal candidate digest;
- one Phase 435 proposal candidate input digest;
- one Phase 433 materialized audit package review digest;
- one Phase 431 materialized audit package manifest digest;
- one Phase 429 serialization-preview review digest;
- one Phase 427 serialization-preview digest;
- one Phase 425 audit package digest;
- one Phase 423 review-record digest;
- one Phase 421 local reviewed metadata digest;
- one Phase 405 local Z3 output manifest digest;
- one Phase 404 local Z3 execution digest;
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
- review label.

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
- Phase 435 candidate digest drift;
- promoted or drifted Phase 435 candidate state;
- accepted append blocker drift;
- nonclaim drift;
- `tiny_z3_accepted_append_policy_review_required` candidate disposition;
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

The maximum claim after Phase 437 is:

HSAI can construct deterministic digest-only review metadata for one Phase 435
tiny-Z3 proposal candidate while preserving the current accepted append and
accepted-ledger blockers.

This is not accepted evidence, not formal proof, not new backend execution, not
a Lean/COBALT/Rust-to-Lean run, not Level2+ evidence, not score-axis evidence,
not semantic correctness, not production readiness, not SOTA, not breakthrough
status, and not full security.

## Tests

Phase 437 adds tests that:

- build deterministic proposal-candidate review metadata;
- verify the review binds the Phase 435 candidate digest;
- verify the review binds the Phase 435 candidate input digest;
- verify the Phase 433 and Phase 431 digests remain bound through the candidate;
- verify Phase 404/405 local Z3 replay digests remain bound through the
  candidate;
- verify blocking review labels remain non-promotional;
- reject Phase 435 candidate digest drift;
- reject promotional review-summary text;
- reject promotional candidate disposition;
- reject accepted-evidence, Level2, score-axis, proof, checker, solver, SOTA,
  full-security, and action-authority promotion attempts.

## Next Slice

The next responsible slice is Phase 438, a docs-first boundary for
accepted-append decision preflight over the Phase 437 review. That boundary
must keep preflight separate from accepted formal evidence, accepted Evidence
Ledger mutation, accepted append policy changes, Level2+ evidence, score axes,
Lean execution, new SMT execution, COBALT execution, Rust-to-Lean extraction,
semantic correctness, production readiness, SOTA, breakthrough status, full
security, and action authority.
