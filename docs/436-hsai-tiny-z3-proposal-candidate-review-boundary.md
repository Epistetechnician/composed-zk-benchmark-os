# Phase 436 HSAI Tiny Z3 Proposal Candidate Review Boundary

State slice: `Phase 436 HSAI tiny Z3 proposal candidate review boundary`.

Phase 436 defines a docs-first boundary for reviewing a Phase 435 local tiny-Z3
accepted-evidence proposal candidate before any accepted append policy decision
is considered. This boundary does not implement review metadata, mutate the
accepted Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Future Review Purpose

The future proposal-candidate review may classify one Phase 435 proposal
candidate for local review readiness. It may only review candidate digest
consistency, disposition consistency, proposal policy metadata, nonclaim
completeness, tiny-Z3 replay binding preservation, and promotion safety.

The future review is not an accepted append policy decision. It is not an
accepted Evidence Ledger mutation and does not create accepted formal evidence.

## Allowed Future Review Labels

The allowed future review labels are:

- `tiny_z3_proposal_candidate_scope_acceptable`;
- `tiny_z3_proposal_candidate_rejected`;
- `tiny_z3_proposal_policy_blocked`;
- `tiny_z3_accepted_append_decision_still_blocked`;
- `tiny_z3_accepted_ledger_mutation_still_blocked`.

The two accepted-append blocking labels are non-promotional. They do not
authorize append policy changes, ledger mutation, accepted evidence, Level2+
evidence, or score axes.

## Required Future Inputs

A future proposal-candidate review input must bind:

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
- the Phase 435 candidate digest is drifted;
- the Phase 435 candidate input digest is drifted;
- the Phase 433 review digest is drifted;
- the Phase 431 manifest digest is drifted;
- the Phase 429 review digest is drifted;
- the Phase 427 preview digest is drifted;
- the Phase 425 package digest is drifted;
- the Phase 423 review-record digest is drifted;
- the Phase 421 metadata digest is drifted;
- the Phase 405 output manifest digest is drifted;
- the Phase 404 execution digest is drifted;
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

HSAI can locally review one tiny-Z3 accepted-evidence proposal candidate while
preserving the current accepted append and accepted-ledger blockers.

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
- new SMT execution evidence;
- COBALT execution evidence;
- Rust-to-Lean extraction evidence;
- benchmark evidence;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- action authority.

## Phase 437 Implementation Exit Criteria

Phase 437 may implement local tiny-Z3 proposal-candidate review metadata only if
it:

- stays inside `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 435 candidate digest;
- binds one Phase 435 candidate input digest;
- binds one Phase 433 review digest;
- binds one Phase 431 materialized package manifest digest;
- binds one Phase 429 review digest;
- binds one Phase 427 preview digest;
- binds one Phase 425 package digest;
- binds one Phase 423 review-record digest;
- binds one Phase 421 local reviewed metadata digest;
- binds Phase 404/405 local Z3 replay digests through the candidate;
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
- does not run Lean, new SMT, COBALT, or Rust-to-Lean extraction;
- does not submit benchmarks;
- does not claim semantic correctness, production readiness, SOTA, breakthrough
  status, full security, or action authority.

## Phase 437 Implementation Result

Phase 437 implemented this boundary as deterministic local metadata in
`crates/hsai-agent-admission/src/lib.rs`. It added no Cargo metadata, writes no
filesystem artifacts, performs no process or network calls, mutates no accepted
Evidence Ledger, changes no accepted append policy, creates no accepted formal
evidence, creates no Level2+ evidence, populates no score axes, and makes no
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or action-authority claim.
