# Phase 420 HSAI Tiny Z3 Local Reviewed Metadata Class Boundary

State slice: `Phase 420 HSAI tiny Z3 local reviewed metadata class boundary`.

## Boundary

Phase 420 defines the docs-first boundary for a future
`TinyZ3LocalReviewedFormalEvidenceMetadata` class.

This boundary is intentionally narrower than accepted evidence. The future
class may describe reviewed local tiny-Z3 formal-evidence metadata only when it
is bound to prior HSAI admission artifacts and explicit nonclaims. It must
remain outside the accepted Evidence Ledger and below Level2+.

This phase does not implement the class, approve accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes, generate
proof artifacts, generate checker transcripts, generate solver certificates,
execute Lean, execute COBALT, run Rust-to-Lean extraction, submit benchmarks, or
deploy to production.

## Future Class Name

The only valid future class name is:

```text
TinyZ3LocalReviewedFormalEvidenceMetadata
```

This class name means local reviewed tiny-Z3 metadata only. It must not be
treated as:

- `AcceptedFormalEvidence`;
- `MachineCheckedScopedProof`;
- `FormalPropertyStatement`;
- `ProofCertificate`;
- `Z3ProofCertificate`;
- `SemanticCorrectnessProof`;
- `GatewayCorrectnessProof`.

## Required Future Fields

A future class implementation must include:

- schema version;
- metadata id;
- creation timestamp;
- Phase 419 class-policy digest;
- Phase 419 class-policy input digest;
- Phase 417 feasibility digest;
- Phase 415 policy-decision digest;
- Phase 413 handoff digest;
- Phase 411 reviewed-record digest;
- current accepted append blocker digest;
- class name;
- owner path;
- class status;
- reviewed-scope digest;
- source-correspondence requirement digest;
- replay requirement digest;
- reviewer-policy digest;
- explicit nonclaim digest.

The required owner path is:

```text
local_non_accepted_metadata_class
```

The required class status is:

```text
not_accepted_formal_evidence
```

## Required Future Validation

A future implementation must validate:

- Phase 419 class-policy digest equality;
- Phase 419 class-policy input digest equality;
- Phase 417 feasibility digest equality;
- Phase 415 policy-decision digest equality;
- Phase 413 handoff digest equality;
- Phase 411 reviewed-record digest equality;
- current accepted append blocker digest equality;
- class name equality;
- owner path equality;
- class status equality;
- reviewed-scope digest presence;
- source-correspondence requirement digest presence;
- replay requirement digest presence;
- reviewer-policy digest presence;
- explicit nonclaim equality.

It must fail closed on drift in any field above.

## Required Rejection Cases

A future implementation must reject:

- class names other than `TinyZ3LocalReviewedFormalEvidenceMetadata`;
- owner paths other than `local_non_accepted_metadata_class`;
- class statuses other than `not_accepted_formal_evidence`;
- missing Phase 419 class-policy digest;
- missing Phase 417 feasibility digest;
- missing Phase 415 policy-decision digest;
- missing current accepted append blocker digest;
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
- breakthrough claims;
- action-authority claims.

## Evidence Meaning

The maximum claim after Phase 420 is:

```text
HSAI has a boundary for a future local reviewed tiny-Z3 formal-evidence metadata
class, while accepted formal evidence remains forbidden.
```

That still is not:

- an implemented class;
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

## Phase 421 Implementation Exit Criteria

Phase 421 implements `TinyZ3LocalReviewedFormalEvidenceMetadata` in
`docs/421-hsai-tiny-z3-local-reviewed-metadata-class-notes.md`. The
implementation:

- binds one Phase 419 class-policy digest;
- binds one Phase 417 feasibility digest;
- binds one Phase 415 policy-decision digest;
- binds one Phase 413 handoff digest;
- binds one Phase 411 reviewed-record digest;
- preserves the current accepted append blocker digest;
- records owner path as `local_non_accepted_metadata_class`;
- records class status as `not_accepted_formal_evidence`;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- rejects proof/checker/solver promotion;
- rejects benchmark/SOTA, semantic-correctness, production-readiness,
  full-security, breakthrough, and action-authority claims.

It still does not create accepted formal evidence.
