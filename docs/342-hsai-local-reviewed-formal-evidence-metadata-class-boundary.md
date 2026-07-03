# Phase 342 HSAI Local Reviewed Formal Evidence Metadata Class Boundary

State slice: `Phase 342 HSAI local reviewed formal-evidence metadata class boundary`.

## Boundary

Phase 342 defines the docs-first boundary for a future
`LocalReviewedFormalEvidenceMetadata` class.

This boundary is intentionally narrower than accepted evidence. The future
class may describe reviewed local formal-evidence metadata only when it is bound
to prior HSAI admission artifacts and explicit nonclaims. It must remain outside
the accepted Evidence Ledger and below Level2+.

This phase does not implement the class, approve accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes, generate
proof artifacts, generate checker transcripts, generate solver certificates,
execute Lean, execute COBALT, run Rust-to-Lean extraction, submit benchmarks, or
deploy to production.

## Future Class Name

The only valid future class name is:

```text
LocalReviewedFormalEvidenceMetadata
```

This class name means local reviewed metadata only. It must not be treated as:

- `AcceptedFormalEvidence`;
- `MachineCheckedScopedProof`;
- `FormalPropertyStatement`;
- `ProofCertificate`;
- `SemanticCorrectnessProof`.

## Required Future Fields

A future class implementation must include:

- schema version;
- metadata id;
- creation timestamp;
- Phase 341 class-policy digest;
- Phase 339 feasibility digest;
- Phase 337 policy-decision digest;
- Phase 335 handoff digest;
- Phase 333 reviewed-record digest;
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

- Phase 341 class-policy digest equality;
- Phase 339 feasibility digest equality;
- Phase 337 policy-decision digest equality;
- Phase 335 handoff digest equality;
- Phase 333 reviewed-record digest equality;
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

- class names other than `LocalReviewedFormalEvidenceMetadata`;
- owner paths other than `local_non_accepted_metadata_class`;
- class statuses other than `not_accepted_formal_evidence`;
- missing Phase 341 class-policy digest;
- missing Phase 339 feasibility digest;
- missing Phase 337 policy-decision digest;
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
- action-authority claims.

## Evidence Meaning

The maximum claim after Phase 342 is:

```text
HSAI has a boundary for a future local reviewed formal-evidence metadata class,
while accepted formal evidence remains forbidden.
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
- a checker transcript;
- a solver certificate;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Phase 343 Implementation Outcome

Phase 343 implements `LocalReviewedFormalEvidenceMetadata` in
`docs/343-hsai-local-reviewed-formal-evidence-metadata-class-notes.md`. It:

- binds one Phase 341 class-policy digest;
- binds one Phase 339 feasibility digest;
- binds one Phase 337 policy-decision digest;
- binds one Phase 335 handoff digest;
- binds one Phase 333 reviewed-record digest;
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
  full-security, and action-authority claims.

It still does not create accepted formal evidence.
