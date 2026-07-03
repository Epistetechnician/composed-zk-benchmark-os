# Phase 340 HSAI Bounded Formal Evidence Class Policy Boundary

State slice: `Phase 340 HSAI bounded formal-evidence class policy boundary`.

## Boundary

Phase 340 defines a docs-first policy boundary for the Phase 339 feasibility
candidate `LocalReviewedFormalEvidenceMetadata`.

The policy decision is narrow:

```text
LocalReviewedFormalEvidenceMetadata may be specified only as a local
non-accepted metadata class.
```

That means the class may describe reviewed local evidence metadata in a later
phase, but it may not be treated as accepted formal evidence, proof authority,
Level2+ evidence, score-axis evidence, semantic correctness, production
readiness, SOTA, full security, or action authority.

This phase does not implement the class, approve accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
Level2+ evidence, populate score axes, generate proof artifacts, generate
checker transcripts, generate solver certificates, execute Lean, execute
COBALT, run Rust-to-Lean extraction, submit benchmarks, or deploy to
production.

## Policy Outcome

Phase 340 rejects two stronger outcomes:

- `accepted_append_path`: rejected because the current accepted append path
  still forbids formal-evidence classes.
- `accepted_formal_evidence_class`: rejected because no accepted evidence route
  exists for formal evidence.

Phase 340 allows one bounded future outcome:

- `local_non_accepted_metadata_class`: allowed for a later implementation phase
  only if the class remains outside the accepted Evidence Ledger and below
  Level2+.

The candidate remains non-authoritative until an explicit later phase
implements and tests the local class data model.

## Required Future Class Constraints

A future implementation of `LocalReviewedFormalEvidenceMetadata` must include:

- schema version;
- class id;
- creation timestamp;
- Phase 339 feasibility digest binding;
- Phase 337 policy-decision digest binding;
- Phase 335 handoff digest binding;
- Phase 333 reviewed-record digest binding;
- current accepted append blocker digest binding;
- explicit `local_non_accepted_metadata_class` owner path;
- explicit `not_accepted_formal_evidence` status;
- reviewed-scope statement digest;
- source correspondence requirement digest;
- replay requirement digest;
- reviewer-policy digest;
- explicit nonclaim digest.

The class must not include:

- proof artifact authority;
- checker transcript authority;
- solver certificate authority;
- accepted Evidence Ledger mutation authority;
- accepted append policy mutation authority;
- Level2+ evidence authority;
- score-axis authority;
- benchmark/SOTA comparison authority;
- semantic-correctness authority;
- production-readiness authority;
- full-security authority;
- action authority.

## Required Rejection Cases

A future implementation must reject:

- missing Phase 339 feasibility digest;
- missing Phase 337 policy-decision digest;
- missing current accepted append blocker digest;
- owner paths other than `local_non_accepted_metadata_class`;
- class status other than `not_accepted_formal_evidence`;
- any accepted Evidence Ledger mutation request;
- any accepted append policy-change request;
- any accepted formal-evidence creation request;
- any Level2+ evidence creation request;
- any score-axis population request;
- any proof artifact promotion;
- any checker transcript promotion;
- any solver certificate promotion;
- any benchmark/SOTA comparison claim;
- any semantic-correctness claim;
- any production-readiness claim;
- any full-security claim;
- any action-authority claim.

## Evidence Meaning

The maximum claim after Phase 340 is:

```text
HSAI has a policy boundary allowing a future local non-accepted metadata class
for reviewed formal-evidence metadata, while current accepted formal evidence
remains forbidden.
```

That still is not:

- an implemented bounded formal-evidence class;
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

## Phase 341 Implementation Exit Criteria

Phase 341 may implement local non-accepted class policy metadata only if it:

- binds one Phase 339 feasibility digest;
- binds one Phase 337 policy-decision digest;
- records owner path as `local_non_accepted_metadata_class`;
- records class status as `not_accepted_formal_evidence`;
- preserves the current accepted append blocker digest;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- rejects proof/checker/solver promotion;
- rejects benchmark/SOTA, semantic-correctness, production-readiness,
  full-security, and action-authority claims.
