# Phase 343 HSAI Local Reviewed Formal Evidence Metadata Class Notes

State slice: `Phase 343 HSAI local reviewed formal-evidence metadata class implementation`.

## Boundary

Phase 343 implements `LocalReviewedFormalEvidenceMetadata` as a local
non-accepted metadata class in `crates/hsai-agent-admission`.

This class records reviewed local formal-evidence metadata only. It does not
approve accepted formal evidence, mutate the accepted Evidence Ledger, change
accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, execute Lean, execute COBALT, run
Rust-to-Lean extraction, submit benchmarks, or deploy to production.

## Implemented Surface

Phase 343 adds these public Rust surfaces:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_REVIEWED_METADATA_SCHEMA_VERSION`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_REVIEWED_METADATA_STATE_SLICE`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_REVIEWED_METADATA_CLAIM_BOUNDARY`.
- `GatewayFormalRealCommandLaneLocalReviewedFormalEvidenceMetadataInput`.
- `GatewayFormalRealCommandLaneLocalReviewedFormalEvidenceMetadata`.
- `GatewayFormalRealCommandLaneLocalReviewedFormalEvidenceMetadataIssue`.
- `GatewayFormalRealCommandLaneLocalReviewedFormalEvidenceMetadataValidation`.
- `gateway_formal_real_command_lane_local_reviewed_metadata_claim_boundary`.
- `gateway_formal_real_command_lane_local_reviewed_metadata_required_nonclaims`.
- `build_gateway_formal_real_command_lane_local_reviewed_formal_evidence_metadata`.
- `validate_gateway_formal_real_command_lane_local_reviewed_formal_evidence_metadata_input`.

The metadata record binds:

- Phase 341 class-policy digest.
- Phase 341 class-policy input digest.
- Phase 339 feasibility digest.
- Phase 337 policy-decision digest.
- Phase 335 handoff digest.
- Phase 333 reviewed-record digest.
- current accepted append blocker digest.
- class name.
- owner path.
- class status.
- reviewed-scope digest.
- source-correspondence requirement digest.
- replay requirement digest.
- reviewer-policy digest.
- explicit nonclaim digest.

## Required State

The only valid class name is:

```text
LocalReviewedFormalEvidenceMetadata
```

The only valid owner path is:

```text
local_non_accepted_metadata_class
```

The only valid class status is:

```text
not_accepted_formal_evidence
```

## Validation

The validator rejects:

- invalid schema version, metadata id, or timestamp;
- missing or zero digests;
- Phase 341 class-policy digest drift;
- Phase 341 class-policy state drift;
- current accepted append blocker drift;
- class name drift;
- owner path drift;
- class status drift;
- requirement digest drift;
- explicit nonclaim drift;
- accepted Evidence Ledger mutation attempts;
- accepted append policy-change attempts;
- accepted formal-evidence creation attempts;
- Level2+ evidence attempts;
- score-axis population attempts;
- proof artifact promotion;
- checker transcript promotion;
- solver certificate promotion;
- benchmark/SOTA comparison claims;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, or action-authority claims.

## Tests

Focused tests now cover:

- local reviewed formal-evidence metadata construction from a Phase 341
  class-policy record;
- Phase 341 class-policy digest drift;
- promoted Phase 341 class-policy state;
- class name drift;
- owner path drift;
- class status drift;
- requirement digest drift;
- accepted evidence mutation, accepted append policy change, accepted
  formal-evidence creation, Level2+, score-axis, proof/checker/solver
  promotion, SOTA, full-security, and authority attempts.

## Claim Boundary

The maximum claim after Phase 343 is:

```text
HSAI has a local non-accepted LocalReviewedFormalEvidenceMetadata class for
reviewed formal-evidence metadata, bound to prior HSAI admission artifacts and
the current accepted append blocker set.
```

That still does not support:

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

## Next Slice

Phase 344 should define a docs-first local reviewed metadata review boundary.
It may specify how a future reviewer can classify the Phase 343 metadata class,
but it must not approve accepted formal evidence, mutate the accepted Evidence
Ledger, change accepted append policy, create Level2+ evidence, populate score
axes, or claim semantic correctness, production readiness, SOTA, full security,
or action authority.
