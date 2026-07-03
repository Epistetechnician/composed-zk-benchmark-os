# Phase 358 HSAI Proposal Candidate Review Boundary

State slice: `Phase 358 HSAI proposal candidate review boundary`.

Phase 358 defines a docs-first boundary for reviewing a Phase 357 local
accepted-evidence proposal candidate before any accepted append policy decision
is considered. This boundary does not implement review metadata, mutate the
accepted Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks, claim
semantic correctness, claim production readiness, claim SOTA, claim breakthrough
status, claim full security, or grant authority to execute an action.

## Future Review Purpose

The future proposal-candidate review may classify one Phase 357 proposal
candidate for local review readiness. It may only review candidate digest
consistency, disposition consistency, proposal policy metadata, nonclaim
completeness, and promotion safety.

The future review is not an accepted append policy decision. It is not an
accepted Evidence Ledger mutation and does not create accepted formal evidence.

## Allowed Future Review Labels

The allowed future review labels are:

- `proposal_candidate_scope_acceptable`;
- `proposal_candidate_rejected`;
- `proposal_policy_blocked`;
- `accepted_append_decision_still_blocked`;
- `accepted_ledger_mutation_still_blocked`.

The two blocking labels are non-promotional. They do not authorize append
policy changes, ledger mutation, accepted evidence, Level2+ evidence, or score
axes.

## Required Future Inputs

A future proposal-candidate review input must bind:

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
- explicit nonclaim digest;
- reviewer policy id;
- reviewer decision id;
- proposal policy id;
- proposal candidate id;
- proposal review id;
- reviewer decision timestamp;
- current accepted append blocker digest;
- proposal-candidate disposition label;
- proposal-candidate review label.

## Required Future Validation

A future implementation must reject a review if:

- any required digest is zero or missing;
- the Phase 357 candidate digest is drifted;
- the Phase 357 candidate input digest is drifted;
- the Phase 355 review digest is drifted;
- the Phase 353 manifest digest is drifted;
- the Phase 351 review digest is drifted;
- the Phase 349 preview digest is drifted;
- the Phase 347 package digest is drifted;
- the declared file digest map digest is drifted;
- explicit nonclaims are missing or drifted;
- current accepted append blocker digest is zero, missing, or drifted;
- reviewer policy id is missing or not a single-segment id;
- reviewer decision id is missing or not a single-segment id;
- proposal policy id is missing or not a single-segment id;
- proposal candidate id is missing or not a single-segment id;
- proposal review id is missing or not a single-segment id;
- reviewer decision timestamp is missing;
- candidate disposition label is promotional;
- review label is outside the five-label set;
- review text claims accepted evidence, Level2+ evidence, score-axis evidence,
  proof authority, checker authority, solver-certificate authority, benchmark
  evidence, semantic correctness, production readiness, SOTA, breakthrough
  status, full security, or action authority;
- the review attempts to mutate the accepted Evidence Ledger;
- the review attempts to change accepted append policy;
- the review attempts to create accepted formal evidence;
- the review attempts to create Level2+ evidence;
- the review attempts to populate score axes.

## Meaning Limit

The future review may support this claim only:

HSAI can locally review one accepted-evidence proposal candidate while preserving
the current accepted append and accepted-ledger blockers.

It cannot support:

- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- proof authority;
- checker transcript authority;
- solver certificate authority;
- Lean execution evidence;
- SMT execution evidence;
- COBALT execution evidence;
- Rust-to-Lean extraction evidence;
- benchmark evidence;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- action authority.

## Phase 359 Implementation Exit Criteria

Phase 359 may implement local proposal-candidate review metadata only if it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 357 candidate digest;
- binds one Phase 355 review digest;
- binds one Phase 353 manifest digest;
- binds one Phase 351 review digest;
- binds one Phase 349 preview digest;
- binds one Phase 347 package digest;
- binds one Phase 345 review record digest;
- binds one Phase 343 local reviewed metadata digest;
- binds declared file digest map and explicit nonclaim digests;
- binds the current accepted append blocker digest;
- restricts review labels to the five labels above;
- treats the two blocking labels as non-promotional;
- rejects all promotion attempts listed in this boundary;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- does not generate or promote proof artifacts, checker transcripts, or solver
  certificates;
- does not run Lean, SMT, COBALT, or Rust-to-Lean extraction;
- does not submit benchmarks;
- does not claim semantic correctness, production readiness, SOTA, breakthrough
  status, full security, or action authority.
