# Phase 369 HSAI Accepted-Append Decision Blocker Metadata Notes

State slice: `Phase 369 HSAI accepted-append decision blocker metadata
implementation`.

Phase 369 implements deterministic pure-data accepted-append decision blocker
metadata over one Phase 367 accepted-append decision candidate review. The
blocker stores only digests, reviewer metadata, proposal metadata, the candidate
disposition, the candidate-review label, a bounded blocker label, explicit
nonclaims, and nonpromotion flags. It does not make an accepted append decision,
write filesystem artifacts, mutate the accepted Evidence Ledger, change
accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run SMT, run COBALT, run
Rust-to-Lean extraction, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneAcceptedAppendDecisionBlockerInput`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionBlocker`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionBlockerLabel`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionBlockerIssue`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionBlockerValidation`;
- `gateway_formal_real_command_lane_accepted_append_decision_blocker_claim_boundary`;
- `gateway_formal_real_command_lane_accepted_append_decision_blocker_required_nonclaims`;
- `build_gateway_formal_real_command_lane_accepted_append_decision_blocker`;
- `validate_gateway_formal_real_command_lane_accepted_append_decision_blocker_input`.

## Blocker Labels

The implemented blocker labels are:

- `accepted_append_decision_blocked`;
- `accepted_ledger_mutation_blocked`;
- `accepted_formal_evidence_blocked`;
- `level2_evidence_blocked`;
- `score_axis_population_blocked`.

All five labels are non-promotional. They do not authorize accepted append
decisions, accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score axes, or action execution.

## Required Bindings

Each blocker input must bind:

- one Phase 367 accepted-append decision candidate review digest;
- one Phase 367 accepted-append decision candidate review input digest;
- one Phase 365 accepted-append decision candidate digest;
- one Phase 365 accepted-append decision candidate input digest;
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
- accepted append decision candidate review id;
- accepted append decision blocker id;
- blocker decision timestamp;
- current accepted append blocker digest;
- Phase 365 candidate disposition;
- Phase 367 review label;
- accepted-append decision blocker label.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid accepted append decision blocker id;
- invalid reviewer policy id;
- invalid reviewer decision id;
- invalid proposal policy id;
- invalid proposal candidate id;
- invalid proposal review id;
- invalid append preflight id;
- invalid append preflight review id;
- invalid accepted append decision candidate id;
- invalid accepted append decision candidate review id;
- missing blocker decision timestamp;
- zero required digests;
- Phase 367 review digest or input digest drift;
- Phase 365, Phase 363, Phase 361, Phase 359, Phase 357, Phase 355, Phase 353,
  Phase 351, Phase 349, Phase 347, Phase 345, or Phase 343 digest drift through
  the review chain;
- promoted or drifted Phase 367 review state;
- accepted append blocker drift;
- nonclaim drift;
- blocker summaries that claim accepted evidence, Level2+ evidence, score-axis
  evidence, proof authority, checker authority, solver-certificate authority,
  benchmark evidence, semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority;
- accepted append decision requests;
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

The maximum claim after Phase 369 is:

HSAI can locally record why one accepted-append decision candidate review still
cannot become an accepted append decision.

This is not an accepted append decision, not accepted evidence, not formal
proof, not backend execution, not a Lean/SMT/COBALT run, not Rust-to-Lean
extraction evidence, not Level2+ evidence, not score-axis evidence, not
semantic correctness, not production readiness, not SOTA, not breakthrough
status, and not full security.

## Tests

Phase 369 adds tests that:

- build deterministic accepted-append decision blocker metadata;
- verify the blocker binds the Phase 367 review digest;
- verify the blocker binds the Phase 367 review input digest;
- verify the blocker binds the Phase 365 candidate digest;
- verify the blocker binds the Phase 363 review digest;
- verify blocker labels remain non-promotional;
- reject Phase 367 review digest drift;
- reject promotional blocker-summary text;
- reject accepted-append decision, accepted-evidence, Level2, score-axis,
  proof, checker, solver, SOTA, full-security, and action-authority promotion
  attempts.

## Next Slice

Phase 370 defines a docs-first boundary for accepted-append decision blocker
review metadata before any accepted append decision is allowed. That boundary
keeps blocker-review metadata separate from accepted formal evidence, accepted
Evidence Ledger mutation, accepted append policy changes, Level2+ evidence,
score axes, Lean execution, SMT execution, COBALT execution, Rust-to-Lean
extraction, semantic correctness, production readiness, SOTA, breakthrough
status, full security, and action authority.
