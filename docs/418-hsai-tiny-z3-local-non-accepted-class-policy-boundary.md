# Phase 418 HSAI Tiny Z3 Local Non-Accepted Class Policy Boundary

State slice: `Phase 418 HSAI tiny Z3 local non-accepted formal-evidence class policy boundary`.

## Boundary

Phase 418 defines a docs-first policy boundary for the Phase 417 feasibility
candidate `TinyZ3LocalReviewedFormalEvidenceMetadata`.

The policy decision is narrow:

```text
TinyZ3LocalReviewedFormalEvidenceMetadata may be specified only as a local
non-accepted metadata class.
```

That means a later phase may describe reviewed local tiny-Z3 metadata, but it
may not treat that metadata as accepted formal evidence, proof authority,
Level2+ evidence, score-axis evidence, semantic correctness, production
readiness, SOTA, full security, breakthrough status, or action authority.

This phase does not implement the class, approve accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
Level2+ evidence, populate score axes, generate proof artifacts, generate
checker transcripts, generate solver certificates, execute Lean, execute
COBALT, run Rust-to-Lean extraction, submit benchmarks, or deploy to
production.

## Policy Outcome

Phase 418 rejects two stronger outcomes:

- `accepted_append_path`: rejected because the current accepted append path
  still forbids tiny-Z3 formal-evidence classes.
- `accepted_formal_evidence_class`: rejected because no accepted evidence route
  exists for tiny-Z3 formal evidence.

Phase 418 allows one bounded future outcome:

- `local_non_accepted_metadata_class`: allowed for a later implementation phase
  only if the policy record stays outside the accepted Evidence Ledger and below
  Level2+.

The candidate remains non-authoritative until an explicit later phase
implements and tests local policy metadata.

## Required Future Policy Metadata Constraints

A future implementation of tiny-Z3 local non-accepted class policy metadata
must include:

- schema version;
- policy id;
- creation timestamp;
- Phase 417 feasibility digest binding;
- Phase 417 feasibility input digest binding;
- Phase 415 policy-decision digest binding;
- Phase 413 handoff digest binding;
- Phase 411 reviewed-record digest binding;
- current accepted append blocker digest binding;
- exact class name `TinyZ3LocalReviewedFormalEvidenceMetadata`;
- explicit `local_non_accepted_metadata_class` owner path;
- explicit `not_accepted_formal_evidence` status;
- reviewed-scope requirement digest;
- source-correspondence requirement digest;
- replay requirement digest;
- reviewer-policy requirement digest;
- explicit nonclaim digest.

The policy metadata must not include:

- class implementation authority;
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

- missing Phase 417 feasibility digest;
- missing Phase 415 policy-decision digest;
- missing current accepted append blocker digest;
- class names other than `TinyZ3LocalReviewedFormalEvidenceMetadata`;
- owner paths other than `local_non_accepted_metadata_class`;
- class status other than `not_accepted_formal_evidence`;
- any accepted Evidence Ledger mutation request;
- any accepted append policy-change request;
- any bounded formal-evidence class implementation request;
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
- any breakthrough claim;
- any action-authority claim.

## Evidence Meaning

The maximum claim after Phase 418 is:

```text
HSAI has a policy boundary allowing a future local non-accepted tiny-Z3 metadata
class policy for reviewed formal-evidence metadata, while current accepted
formal evidence remains forbidden.
```

That still is not:

- an implemented tiny-Z3 local non-accepted class policy;
- an implemented bounded formal-evidence class;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a proof artifact;
- a checker transcript;
- a solver certificate;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Phase 419 Implementation Exit Criteria

Phase 419 may implement local tiny-Z3 non-accepted class policy metadata only if
it:

- binds one Phase 417 feasibility digest;
- binds one Phase 415 policy-decision digest;
- records class name as `TinyZ3LocalReviewedFormalEvidenceMetadata`;
- records owner path as `local_non_accepted_metadata_class`;
- records class status as `not_accepted_formal_evidence`;
- preserves the current accepted append blocker digest;
- does not implement the class itself;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- rejects proof/checker/solver promotion;
- rejects benchmark/SOTA, semantic-correctness, production-readiness,
  full-security, breakthrough, and action-authority claims.

Phase 419 still must not implement `TinyZ3LocalReviewedFormalEvidenceMetadata`.
