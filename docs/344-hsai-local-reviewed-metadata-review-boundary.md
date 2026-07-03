# Phase 344 HSAI Local Reviewed Metadata Review Boundary

State slice: `Phase 344 HSAI local reviewed metadata review boundary`.

## Boundary

Phase 344 defines a docs-first review boundary for the Phase 343
`LocalReviewedFormalEvidenceMetadata` class.

The review boundary may classify a local metadata record as one of:

- `review_scope_acceptable`;
- `review_rejected`;
- `replay_blocked`;
- `source_correspondence_blocked`;
- `accepted_evidence_blocked`.

These labels are review metadata only. They do not turn the Phase 343 class into
accepted formal evidence, proof authority, Level2+ evidence, score-axis
evidence, semantic correctness, production readiness, SOTA, full security, or
action authority.

This phase does not implement review metadata, approve accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes, generate
proof artifacts, generate checker transcripts, generate solver certificates,
execute Lean, execute COBALT, run Rust-to-Lean extraction, submit benchmarks, or
deploy to production.

## Future Review Inputs

A future review metadata implementation must bind:

- Phase 343 local metadata digest;
- Phase 341 class-policy digest;
- Phase 339 feasibility digest;
- Phase 337 policy-decision digest;
- Phase 335 handoff digest;
- Phase 333 reviewed-record digest;
- current accepted append blocker digest;
- reviewer policy id;
- reviewer decision id;
- reviewer decision timestamp;
- review classification label;
- reviewed-scope statement digest;
- explicit nonclaim digest.

## Allowed Review Labels

The allowed review labels have these meanings:

- `review_scope_acceptable`: the local metadata record is internally scoped for
  the declared non-accepted class.
- `review_rejected`: the local metadata record is rejected by reviewer policy.
- `replay_blocked`: replay requirements are not satisfied.
- `source_correspondence_blocked`: source-correspondence requirements are not
  satisfied.
- `accepted_evidence_blocked`: the record cannot enter the accepted Evidence
  Ledger because formal evidence remains blocked in the accepted append path.

No label may imply accepted formal evidence.

## Required Future Validation

A future implementation must reject:

- missing Phase 343 local metadata digest;
- missing Phase 341 class-policy digest;
- missing Phase 337 policy-decision digest;
- missing current accepted append blocker digest;
- invalid reviewer policy id;
- invalid reviewer decision id;
- missing reviewer decision timestamp;
- unknown review labels;
- review labels that imply accepted evidence;
- reviewed-scope statements with SOTA, production-readiness,
  semantic-correctness, full-security, or authority claims;
- explicit nonclaim drift;
- accepted Evidence Ledger mutation requests;
- accepted append policy-change requests;
- accepted formal-evidence creation requests;
- Level2+ evidence creation requests;
- score-axis population requests;
- proof artifact promotion;
- checker transcript promotion;
- solver certificate promotion;
- benchmark/SOTA comparison claims;
- semantic-correctness claims;
- production-readiness claims;
- full-security claims;
- action-authority claims.

## Evidence Meaning

The maximum claim after Phase 344 is:

```text
HSAI has a boundary for reviewing local non-accepted formal-evidence metadata,
while accepted formal evidence remains forbidden.
```

That still is not:

- implemented review metadata;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a checker transcript;
- a solver certificate;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Phase 345 Implementation Exit Criteria

Phase 345 may implement local metadata review records only if it:

- binds one Phase 343 local metadata digest;
- binds one Phase 341 class-policy digest;
- binds one Phase 337 policy-decision digest;
- preserves the current accepted append blocker digest;
- restricts review labels to the five labels above;
- treats `accepted_evidence_blocked` as non-promotional;
- requires explicit nonclaims;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- rejects proof/checker/solver promotion;
- rejects benchmark/SOTA, semantic-correctness, production-readiness,
  full-security, and action-authority claims.
