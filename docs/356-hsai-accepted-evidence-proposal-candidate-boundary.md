# Phase 356 HSAI Accepted Evidence Proposal Candidate Boundary

State slice: `Phase 356 HSAI accepted evidence proposal candidate boundary`.

Phase 356 defines a docs-first boundary for a future local accepted-evidence
proposal candidate after Phase 355 materialized audit package review metadata.
The candidate is not accepted evidence. This boundary does not implement
proposal metadata, mutate the accepted Evidence Ledger, change accepted append
policy, create accepted formal evidence, create Level2+ evidence, populate score
axes, generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit
benchmarks, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant authority to execute an
action.

## Future Candidate Purpose

The future proposal candidate may package one Phase 355 review as a local
candidate for later human review. It may only state that a local package passed
the previous metadata gates and that acceptance remains blocked pending a
separate accepted-append policy decision.

The candidate must be quarantine-like metadata. It is not an append transaction,
not an accepted Evidence Ledger entry, and not permission to run a backend.

## Required Future Candidate Inputs

A future proposal candidate input must bind:

- one Phase 355 materialized audit package review digest;
- one Phase 355 review input digest;
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
- current accepted append blocker digest;
- candidate disposition label.

## Allowed Future Disposition Labels

The allowed future disposition labels are:

- `candidate_scope_acceptable`;
- `candidate_rejected`;
- `accepted_append_policy_review_required`;
- `accepted_ledger_mutation_still_blocked`;
- `level2_evidence_still_blocked`.

`accepted_ledger_mutation_still_blocked` and `level2_evidence_still_blocked`
are blocking labels. They do not authorize acceptance, Level2+ evidence, score
axes, or ledger mutation.

## Required Future Validation

A future implementation must reject a candidate if:

- any required digest is zero or missing;
- the Phase 355 review digest is drifted;
- the Phase 353 manifest digest is drifted;
- the Phase 351 review digest is drifted;
- the Phase 349 preview digest is drifted;
- the Phase 347 package digest is drifted;
- declared file digest map digest is missing or drifted;
- explicit nonclaims are missing or drifted;
- current accepted append blocker digest is zero, missing, or drifted;
- reviewer policy id is missing or not a single-segment id;
- reviewer decision id is missing or not a single-segment id;
- proposal policy id is missing or not a single-segment id;
- proposal candidate id is missing or not a single-segment id;
- disposition label is outside the five-label set;
- any candidate text claims accepted evidence, Level2+ evidence, score-axis
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

HSAI can prepare local candidate metadata for later review of one Phase 355
materialized audit package review while preserving the current accepted
formal-evidence blocker.

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

## Phase 357 Implementation Exit Criteria

Phase 357 may implement local accepted-evidence proposal candidate metadata only
if it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 355 review digest;
- binds one Phase 353 manifest digest;
- binds one Phase 351 review digest;
- binds one Phase 349 preview digest;
- binds one Phase 347 package digest;
- binds one Phase 345 review record digest;
- binds one Phase 343 local reviewed metadata digest;
- binds declared file digest map and explicit nonclaim digests;
- binds the current accepted append blocker digest;
- restricts disposition labels to the five labels above;
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
