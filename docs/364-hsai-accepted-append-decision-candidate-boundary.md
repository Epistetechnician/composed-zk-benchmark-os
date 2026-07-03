# Phase 364 HSAI Accepted-Append Decision Candidate Boundary

State slice: `Phase 364 HSAI accepted-append decision candidate boundary`.

Phase 364 defines a docs-first boundary for future local accepted-append
decision candidate metadata over one Phase 363 append-decision preflight review.
This boundary does not implement decision candidate metadata, mutate the
accepted Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Future Candidate Purpose

The future accepted-append decision candidate may package one Phase 363 review
as local decision-candidate metadata while the real accepted append path remains
blocked. It may only record digest consistency, review-label consistency,
append-blocker consistency, nonclaim completeness, and promotion safety.

The future candidate is not an accepted append decision. It is not an accepted
Evidence Ledger mutation and does not create accepted formal evidence.

## Allowed Future Candidate Dispositions

The allowed future candidate dispositions are:

- `decision_candidate_scope_acceptable`;
- `decision_candidate_rejected`;
- `accepted_append_policy_still_blocked`;
- `accepted_ledger_mutation_still_blocked`;
- `level2_evidence_still_blocked`.

The three blocking labels are non-promotional. They do not authorize append
policy changes, ledger mutation, accepted evidence, Level2+ evidence, or score
axes.

## Required Future Inputs

A future accepted-append decision candidate input must bind:

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
- explicit nonclaim digest;
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

## Required Future Validation

A future implementation must reject a candidate if:

- any required digest is zero or missing;
- the Phase 363 review digest is drifted;
- the Phase 363 review input digest is drifted;
- the Phase 361 preflight digest is drifted;
- the Phase 361 preflight input digest is drifted;
- the Phase 359 review digest is drifted;
- the Phase 359 review input digest is drifted;
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
- append preflight id is missing or not a single-segment id;
- append preflight review id is missing or not a single-segment id;
- accepted append decision candidate id is missing or not a single-segment id;
- candidate timestamp is missing;
- Phase 363 review state is promoted or drifted;
- review label or candidate disposition is outside its bounded label set;
- candidate text claims accepted evidence, Level2+ evidence, score-axis
  evidence, proof authority, checker authority, solver-certificate authority,
  benchmark evidence, semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority;
- the candidate attempts to mutate the accepted Evidence Ledger;
- the candidate attempts to change accepted append policy;
- the candidate attempts to create accepted formal evidence;
- the candidate attempts to create Level2+ evidence;
- the candidate attempts to populate score axes.

## Meaning Limit

The future candidate may support this claim only:

HSAI can locally package one append-decision preflight review as a decision
candidate while preserving the current accepted append and accepted-ledger
blockers.

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

## Phase 365 Implementation Exit Criteria

Phase 365 may implement local accepted-append decision candidate metadata only
if it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 363 review digest;
- binds one Phase 363 review input digest;
- binds one Phase 361 preflight digest;
- binds one Phase 361 preflight input digest;
- binds one Phase 359 review digest;
- binds one Phase 359 review input digest;
- binds one Phase 357 candidate digest;
- binds one Phase 357 candidate input digest;
- binds one Phase 355 review digest;
- binds one Phase 353 manifest digest;
- binds one Phase 351 review digest;
- binds one Phase 349 preview digest;
- binds one Phase 347 package digest;
- binds one Phase 345 review record digest;
- binds one Phase 343 local reviewed metadata digest;
- binds declared file digest map and explicit nonclaim digests;
- binds the current accepted append blocker digest;
- restricts candidate dispositions to the five labels above;
- treats the three blocking labels as non-promotional;
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
