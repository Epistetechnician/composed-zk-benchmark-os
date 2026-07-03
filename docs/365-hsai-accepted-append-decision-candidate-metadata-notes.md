# Phase 365 HSAI Accepted-Append Decision Candidate Metadata Notes

State slice: `Phase 365 HSAI accepted-append decision candidate metadata
implementation`.

Phase 365 implements deterministic pure-data accepted-append decision candidate
metadata over one Phase 363 append-decision preflight review. The candidate
stores only digests, reviewer metadata, proposal metadata, a bounded
disposition label, explicit nonclaims, and nonpromotion flags. It does not
write filesystem artifacts, mutate the accepted Evidence Ledger, change
accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run SMT, run COBALT, run
Rust-to-Lean extraction, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneAcceptedAppendDecisionCandidateInput`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionCandidate`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionCandidateDisposition`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionCandidateIssue`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionCandidateValidation`;
- `gateway_formal_real_command_lane_accepted_append_decision_candidate_claim_boundary`;
- `gateway_formal_real_command_lane_accepted_append_decision_candidate_required_nonclaims`;
- `build_gateway_formal_real_command_lane_accepted_append_decision_candidate`;
- `validate_gateway_formal_real_command_lane_accepted_append_decision_candidate_input`.

## Disposition Labels

The implemented disposition labels are:

- `decision_candidate_scope_acceptable`;
- `decision_candidate_rejected`;
- `accepted_append_policy_still_blocked`;
- `accepted_ledger_mutation_still_blocked`;
- `level2_evidence_still_blocked`.

The three blocking labels remain non-promotional. They do not authorize accepted
Evidence Ledger mutation, accepted append policy changes, accepted formal
evidence, Level2+ evidence, or score axes.

## Required Bindings

Each candidate input must bind:

- one Phase 363 append-decision preflight review digest;
- one Phase 363 append-decision preflight review input digest;
- one Phase 361 append-decision preflight digest;
- one Phase 361 append-decision preflight input digest;
- one Phase 359 proposal candidate review digest;
- one Phase 359 proposal candidate review input digest;
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
- append preflight id;
- append preflight review id;
- accepted append decision candidate id;
- candidate timestamp;
- current accepted append blocker digest;
- Phase 363 review label;
- accepted-append decision candidate disposition.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid accepted append decision candidate id;
- invalid reviewer policy id;
- invalid reviewer decision id;
- invalid proposal policy id;
- invalid proposal candidate id;
- invalid proposal review id;
- invalid append preflight id;
- invalid append preflight review id;
- missing candidate timestamp;
- zero required digests;
- Phase 363 review digest drift;
- promoted or drifted Phase 363 review state;
- accepted append blocker drift;
- nonclaim drift;
- candidate summaries that claim accepted evidence, Level2+ evidence,
  score-axis evidence, proof authority, checker authority, solver-certificate
  authority, benchmark evidence, semantic correctness, production readiness,
  SOTA, breakthrough status, full security, or action authority;
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

The maximum claim after Phase 365 is:

HSAI can locally package one append-decision preflight review as a decision
candidate while preserving the current accepted append and accepted-ledger
blockers.

This is not accepted evidence, not formal proof, not backend execution, not a
Lean/SMT/COBALT run, not Rust-to-Lean extraction evidence, not Level2+ evidence,
not score-axis evidence, not semantic correctness, not production readiness, not
SOTA, not breakthrough status, and not full security.

## Tests

Phase 365 adds tests that:

- build deterministic accepted-append decision candidate metadata;
- verify the candidate binds the Phase 363 review digest;
- verify the candidate binds the Phase 363 review input digest;
- verify the candidate binds the Phase 361 preflight digest;
- verify blocking dispositions remain non-promotional;
- reject Phase 363 review digest drift;
- reject promotional candidate-summary text;
- reject accepted-evidence, Level2, score-axis, proof, checker, solver, SOTA,
  full-security, and action-authority promotion attempts.

## Next Slice

Phase 366 should define a docs-first boundary for reviewing local
accepted-append decision candidate metadata before any accepted append decision.
That boundary must keep decision-candidate review separate from accepted formal
evidence, accepted Evidence Ledger mutation, accepted append policy changes,
Level2+ evidence, score axes, Lean execution, SMT execution, COBALT execution,
Rust-to-Lean extraction, semantic correctness, production readiness, SOTA,
breakthrough status, full security, and action authority.
