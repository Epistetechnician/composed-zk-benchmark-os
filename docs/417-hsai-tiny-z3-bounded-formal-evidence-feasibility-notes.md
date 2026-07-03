# Phase 417 HSAI Tiny Z3 Bounded Formal Evidence Feasibility Notes

State slice: `Phase 417 HSAI tiny Z3 bounded formal-evidence feasibility metadata`.

## Boundary

Phase 417 implements local tiny-Z3 bounded formal-evidence feasibility metadata
under the Phase 416 boundary. It binds one Phase 415 policy-decision record and
records that a possible tiny-Z3 class remains feasibility-only, not approved,
and owner-unresolved.

The implemented candidate class label is:

```text
TinyZ3LocalReviewedFormalEvidenceMetadata
```

The implemented class status is:

```text
feasibility_only_not_approved
```

The implemented ownership decision is:

```text
ownership_unresolved
```

## Implemented Surface

Phase 417 adds:

- `GatewayFormalTinyDigestBackendZ3BoundedFormalEvidenceFeasibilityInput`;
- `GatewayFormalTinyDigestBackendZ3BoundedFormalEvidenceFeasibility`;
- `GatewayFormalTinyDigestBackendZ3BoundedFormalEvidenceFeasibilityIssue`;
- `GatewayFormalTinyDigestBackendZ3BoundedFormalEvidenceFeasibilityValidation`;
- canonical claim-boundary, feasibility-question, and nonclaim helpers;
- builder and validator functions;
- focused tests for valid metadata, drift rejection, class/status/owner
  rejection, promoted policy-decision rejection, and promotion-attempt rejection.

## Validation Rules

The validator requires:

- Phase 417 schema and single-segment feasibility id;
- nonzero digests;
- exact Phase 415 policy-decision digest binding;
- exact Phase 415 policy-decision input digest binding;
- exact Phase 413 handoff digest binding;
- exact Phase 411 reviewed-record digest binding;
- Phase 415 policy state
  `AcceptedFormalEvidenceStillForbidden`;
- current accepted append blocker digest preservation;
- exact candidate class name;
- exact feasibility-only class status;
- unresolved ownership decision;
- exact feasibility-question digest;
- exact nonclaim digest;
- every promotion flag set to false.

## Evidence Meaning

The maximum claim after Phase 417 is:

```text
HSAI has local tiny-Z3 bounded formal-evidence feasibility metadata bound to a
forbidden accepted-evidence policy decision.
```

That is still not:

- a bounded formal-evidence class approval;
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

The next responsible slice is a docs-first policy boundary for whether this
tiny-Z3 feasibility metadata may become a local non-accepted class. That slice
must still keep accepted evidence, accepted append policy changes, Level2+
evidence, score axes, Lean/COBALT/Rust-to-Lean execution, and strong public
claims out of scope.
