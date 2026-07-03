# Phase 357 HSAI Accepted Evidence Proposal Candidate Metadata Notes

State slice: `Phase 357 HSAI accepted evidence proposal candidate metadata
implementation`.

Phase 357 implements deterministic pure-data proposal candidate metadata over
one Phase 355 materialized audit package review. The candidate stores only
digests, reviewer metadata, proposal metadata, a bounded disposition label,
explicit nonclaims, and nonpromotion flags. It does not write filesystem
artifacts, mutate the accepted Evidence Ledger, change accepted append policy,
create accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit
benchmarks, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant authority to execute an
action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneAcceptedEvidenceProposalCandidateInput`;
- `GatewayFormalRealCommandLaneAcceptedEvidenceProposalCandidate`;
- `GatewayFormalRealCommandLaneAcceptedEvidenceProposalCandidateDisposition`;
- `GatewayFormalRealCommandLaneAcceptedEvidenceProposalCandidateIssue`;
- `GatewayFormalRealCommandLaneAcceptedEvidenceProposalCandidateValidation`;
- `gateway_formal_real_command_lane_accepted_evidence_proposal_candidate_claim_boundary`;
- `gateway_formal_real_command_lane_accepted_evidence_proposal_candidate_required_nonclaims`;
- `build_gateway_formal_real_command_lane_accepted_evidence_proposal_candidate`;
- `validate_gateway_formal_real_command_lane_accepted_evidence_proposal_candidate_input`.

## Disposition Labels

The implemented disposition labels are:

- `candidate_scope_acceptable`;
- `candidate_rejected`;
- `accepted_append_policy_review_required`;
- `accepted_ledger_mutation_still_blocked`;
- `level2_evidence_still_blocked`.

The two blocking labels remain non-promotional. They do not authorize accepted
Evidence Ledger mutation or Level2+ evidence.

## Required Bindings

Each candidate input must bind:

- one Phase 355 materialized audit package review digest;
- one Phase 355 review input digest;
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
- current accepted append blocker digest;
- candidate disposition label.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid proposal candidate id;
- invalid reviewer policy id;
- invalid reviewer decision id;
- invalid proposal policy id;
- missing candidate timestamp;
- zero required digests;
- Phase 355 review digest drift;
- promoted or drifted Phase 355 review state;
- accepted append blocker drift;
- nonclaim drift;
- candidate summaries that claim accepted evidence, Level2+ evidence, score-axis
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

The maximum claim after Phase 357 is:

HSAI can construct deterministic digest-only proposal candidate metadata for one
Phase 355 materialized audit package review while preserving the current
accepted formal-evidence blocker.

This is not accepted evidence, not formal proof, not backend execution, not a
Lean/SMT/COBALT run, not Rust-to-Lean extraction evidence, not Level2+ evidence,
not score-axis evidence, not semantic correctness, not production readiness, not
SOTA, not breakthrough status, and not full security.

## Tests

Phase 357 adds tests that:

- build deterministic proposal candidate metadata;
- verify the candidate binds the Phase 355 review digest;
- verify the candidate binds the Phase 353 manifest digest;
- verify blocking dispositions remain non-promotional;
- reject Phase 355 review digest drift;
- reject promotional candidate-summary text;
- reject accepted-evidence, Level2, score-axis, proof, checker, solver, SOTA,
  full-security, and action-authority promotion attempts.

## Next Slice

Phase 358 should define a docs-first boundary for reviewing a local proposal
candidate before any accepted append policy decision is considered. That
boundary must keep candidate review separate from accepted formal evidence,
accepted Evidence Ledger mutation, accepted append policy changes, Level2+
evidence, score axes, Lean execution, SMT execution, COBALT execution,
Rust-to-Lean extraction, semantic correctness, production readiness, SOTA,
breakthrough status, full security, and action authority.
