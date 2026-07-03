# Phase 419 HSAI Tiny Z3 Local Non-Accepted Class Policy Notes

State slice: `Phase 419 HSAI tiny Z3 local non-accepted class policy metadata`.

## Boundary

Phase 419 implements local tiny-Z3 non-accepted class policy metadata under the
Phase 418 boundary. It binds one Phase 417 feasibility record and records that
`TinyZ3LocalReviewedFormalEvidenceMetadata` may only be handled through a local
non-accepted policy path.

The implemented owner path is:

```text
local_non_accepted_metadata_class
```

The implemented class status is:

```text
not_accepted_formal_evidence
```

This phase does not implement `TinyZ3LocalReviewedFormalEvidenceMetadata`
itself.

## Implemented Surface

Phase 419 adds:

- `GatewayFormalTinyDigestBackendZ3LocalNonAcceptedClassPolicyInput`;
- `GatewayFormalTinyDigestBackendZ3LocalNonAcceptedClassPolicy`;
- `GatewayFormalTinyDigestBackendZ3LocalNonAcceptedClassPolicyIssue`;
- `GatewayFormalTinyDigestBackendZ3LocalNonAcceptedClassPolicyValidation`;
- canonical claim-boundary, nonclaim, and requirement-digest helpers;
- builder and validator functions;
- focused tests for valid policy metadata, feasibility digest drift, class-name
  drift, owner-path drift, class-status drift, requirement digest drift,
  promoted feasibility state, and promotion attempts.

## Validation Rules

The validator requires:

- Phase 419 schema and single-segment policy id;
- nonzero digests;
- exact Phase 417 feasibility digest binding;
- exact Phase 417 feasibility input digest binding;
- exact Phase 415 policy-decision digest binding;
- exact Phase 413 handoff digest binding;
- exact Phase 411 reviewed-record digest binding;
- Phase 417 feasibility state with policy decision
  `AcceptedFormalEvidenceStillForbidden`;
- class name `TinyZ3LocalReviewedFormalEvidenceMetadata`;
- owner path `local_non_accepted_metadata_class`;
- class status `not_accepted_formal_evidence`;
- reviewed-scope requirement digest;
- source-correspondence requirement digest;
- replay requirement digest;
- reviewer-policy requirement digest;
- exact nonclaim digest;
- every promotion flag set to false.

## Evidence Meaning

The maximum claim after Phase 419 is:

```text
HSAI has local tiny-Z3 non-accepted class policy metadata bound to a Phase 417
feasibility record and current accepted-evidence blocker.
```

That is still not:

- an implemented tiny-Z3 reviewed metadata class;
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
- source correspondence proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Next Slice

The next responsible slice is a docs-first boundary for implementing
`TinyZ3LocalReviewedFormalEvidenceMetadata` as local non-accepted metadata. That
future boundary must still keep accepted evidence, accepted append policy
changes, Level2+ evidence, score axes, proof/checker/solver authority,
Lean/COBALT/Rust-to-Lean execution, and strong public claims out of scope.
