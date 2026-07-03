# Phase 377 HSAI Accepted-Append Decision Quarantine-Resolution Planning Metadata Notes

State slice: `Phase 377 HSAI accepted-append decision quarantine-resolution
planning metadata implementation`.

Phase 377 implements deterministic pure-data quarantine-resolution planning
metadata over one Phase 375 accepted-append decision quarantine review. The
plan stores only digests, resolution metadata, quarantine metadata, proposal
metadata, the candidate disposition, the candidate-review label, the blocker
label, the blocker-review label, the quarantine label, the quarantine-review
label, a bounded resolution-planning label, explicit nonclaims, and
nonpromotion flags. It does not make an accepted append decision, write
filesystem artifacts, mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean
extraction, submit benchmarks, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, or grant
authority to execute an action.

## Implemented Surface

The implementation is additive in `crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalRealCommandLaneAcceptedAppendDecisionQuarantineResolutionPlanInput`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionQuarantineResolutionPlan`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionQuarantineResolutionPlanLabel`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionQuarantineResolutionPlanIssue`;
- `GatewayFormalRealCommandLaneAcceptedAppendDecisionQuarantineResolutionPlanValidation`;
- `gateway_formal_real_command_lane_accepted_append_decision_quarantine_resolution_plan_claim_boundary`;
- `gateway_formal_real_command_lane_accepted_append_decision_quarantine_resolution_plan_required_nonclaims`;
- `build_gateway_formal_real_command_lane_accepted_append_decision_quarantine_resolution_plan`;
- `validate_gateway_formal_real_command_lane_accepted_append_decision_quarantine_resolution_plan_input`.

## Planning Labels

The implemented resolution-planning labels are:

- `resolution_plan_scope_acceptable`;
- `resolution_plan_rejected`;
- `accepted_append_decision_still_blocked`;
- `accepted_ledger_mutation_still_blocked`;
- `level2_evidence_still_blocked`.

All five labels are non-promotional. They do not authorize accepted append
decisions, accepted Evidence Ledger mutation, accepted append policy changes,
accepted formal evidence, Level2+ evidence, score axes, or action execution.

## Required Bindings

Each resolution-plan input must bind:

- one Phase 375 accepted-append decision quarantine review digest;
- one Phase 375 accepted-append decision quarantine review input digest;
- one Phase 373 accepted-append decision quarantine digest;
- one Phase 373 accepted-append decision quarantine input digest;
- one Phase 371 accepted-append decision blocker review digest;
- one Phase 371 accepted-append decision blocker review input digest;
- one Phase 369 accepted-append decision blocker digest;
- one Phase 369 accepted-append decision blocker input digest;
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
- quarantine policy id;
- quarantine decision id;
- resolution policy id;
- resolution decision id;
- proposal policy id;
- proposal candidate id;
- proposal review id;
- append preflight id;
- append preflight review id;
- accepted append decision candidate id;
- accepted append decision candidate review id;
- accepted append decision blocker id;
- accepted append decision blocker review id;
- accepted append decision quarantine id;
- accepted append decision quarantine review id;
- accepted append decision quarantine-resolution plan id;
- planning decision timestamp;
- current accepted append blocker digest;
- Phase 365 candidate disposition;
- Phase 367 review label;
- Phase 369 blocker label;
- Phase 371 blocker review label;
- Phase 373 quarantine label;
- Phase 375 quarantine review label;
- accepted-append decision quarantine-resolution planning label.

## Rejection Cases

Validation rejects:

- wrong schema version;
- invalid accepted append decision quarantine-resolution plan id;
- invalid quarantine, resolution, proposal, append-preflight, candidate,
  blocker, blocker-review, quarantine, and quarantine-review ids;
- missing planning decision timestamp;
- zero required digests;
- Phase 375 quarantine review digest or input digest drift;
- Phase 373, Phase 371, Phase 369, Phase 367, Phase 365, Phase 363, Phase 361,
  Phase 359, Phase 357, Phase 355, Phase 353, Phase 351, Phase 349, Phase 347,
  Phase 345, or Phase 343 digest drift through the planning chain;
- promoted or drifted Phase 375 quarantine review state;
- accepted append blocker drift;
- nonclaim drift;
- planning summaries that claim accepted evidence, Level2+ evidence,
  score-axis evidence, proof authority, checker authority,
  solver-certificate authority, benchmark evidence, semantic correctness,
  production readiness, SOTA, breakthrough status, full security, or action
  authority;
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

The maximum claim after Phase 377 is:

HSAI can locally plan why one accepted-append decision quarantine review still
keeps the accepted append path blocked.

This is not an accepted append decision, not accepted evidence, not formal
proof, not backend execution, not a Lean/SMT/COBALT run, not Rust-to-Lean
extraction evidence, not Level2+ evidence, not score-axis evidence, not
semantic correctness, not production readiness, not SOTA, not breakthrough
status, and not full security.

## Tests

Phase 377 adds tests that:

- build deterministic accepted-append decision quarantine-resolution planning
  metadata;
- verify the plan binds the Phase 375 quarantine review digest;
- verify the plan binds the Phase 375 quarantine review input digest;
- verify the plan binds the Phase 373 quarantine digest;
- verify quarantine-review and resolution-planning labels remain
  non-promotional;
- reject Phase 375 quarantine review digest drift;
- reject promotional planning-summary text;
- reject accepted-append decision, accepted-evidence, Level2, score-axis,
  proof, checker, solver, SOTA, full-security, and action-authority promotion
  attempts.

## Next Slice

Phase 378 defines a docs-first boundary for accepted-append decision
quarantine-resolution review metadata before any accepted append decision is
allowed. That boundary keeps resolution review metadata separate from
accepted formal evidence, accepted Evidence Ledger mutation, accepted append
policy changes, Level2+ evidence, score axes, Lean execution, SMT execution,
COBALT execution, Rust-to-Lean extraction, semantic correctness, production
readiness, SOTA, breakthrough status, full security, and action authority.
