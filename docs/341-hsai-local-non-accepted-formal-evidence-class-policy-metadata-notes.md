# Phase 341 HSAI Local Non-Accepted Formal Evidence Class Policy Metadata Notes

State slice: `Phase 341 HSAI local non-accepted formal-evidence class policy metadata implementation`.

## Boundary

Phase 341 implements local policy metadata over one Phase 339 feasibility
record. It records that `LocalReviewedFormalEvidenceMetadata` may be specified
only as a local non-accepted metadata class.

This phase does not implement the class, approve accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, execute Lean, execute COBALT, run Rust-to-Lean extraction, submit
benchmarks, or deploy to production.

## Implemented Surface

Phase 341 adds these public Rust surfaces in `crates/hsai-agent-admission`:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_NON_ACCEPTED_CLASS_POLICY_SCHEMA_VERSION`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_NON_ACCEPTED_CLASS_POLICY_STATE_SLICE`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_NON_ACCEPTED_CLASS_POLICY_CLAIM_BOUNDARY`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_NON_ACCEPTED_CLASS_POLICY_OWNER_PATH`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_LOCAL_NON_ACCEPTED_CLASS_POLICY_CLASS_STATUS`.
- `GatewayFormalRealCommandLaneLocalNonAcceptedClassPolicyInput`.
- `GatewayFormalRealCommandLaneLocalNonAcceptedClassPolicy`.
- `GatewayFormalRealCommandLaneLocalNonAcceptedClassPolicyIssue`.
- `GatewayFormalRealCommandLaneLocalNonAcceptedClassPolicyValidation`.
- `gateway_formal_real_command_lane_local_non_accepted_class_policy_claim_boundary`.
- `gateway_formal_real_command_lane_local_non_accepted_class_policy_required_nonclaims`.
- `gateway_formal_real_command_lane_local_non_accepted_class_policy_requirement_digests`.
- `build_gateway_formal_real_command_lane_local_non_accepted_class_policy`.
- `validate_gateway_formal_real_command_lane_local_non_accepted_class_policy_input`.

The policy record binds:

- Phase 339 feasibility digest.
- Phase 339 feasibility-input digest.
- Phase 337 policy-decision digest.
- Phase 335 handoff digest.
- Phase 333 reviewed-record digest.
- current accepted append blocker digest.
- local non-accepted owner path.
- not-accepted class status.
- reviewed-scope requirement digest.
- source-correspondence requirement digest.
- replay requirement digest.
- reviewer-policy requirement digest.
- explicit nonclaim digest.

## Policy State

The only valid owner path is:

```text
local_non_accepted_metadata_class
```

The only valid class status is:

```text
not_accepted_formal_evidence
```

The policy record intentionally does not implement
`LocalReviewedFormalEvidenceMetadata`. It only records the constraints a future
class boundary must satisfy.

## Validation

The validator rejects:

- invalid schema version, policy id, or timestamp;
- missing or zero digests;
- Phase 339 feasibility digest drift;
- Phase 339 feasibility state drift;
- current accepted append blocker drift;
- class name drift;
- owner path drift;
- class status drift;
- requirement digest drift;
- explicit nonclaim drift;
- accepted Evidence Ledger mutation attempts;
- accepted append policy-change attempts;
- bounded formal-evidence class implementation attempts;
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

- local non-accepted class policy metadata construction from a Phase 339
  feasibility record;
- Phase 339 feasibility digest drift;
- promoted Phase 339 feasibility state;
- class name drift;
- owner path drift;
- class status drift;
- requirement digest drift;
- accepted evidence mutation, accepted append policy change, bounded class
  implementation, accepted formal-evidence creation, Level2+, score-axis,
  proof/checker/solver promotion, SOTA, full-security, and authority attempts.

## Claim Boundary

The maximum claim after Phase 341 is:

```text
HSAI has local policy metadata saying a future
LocalReviewedFormalEvidenceMetadata class may only be local non-accepted
metadata, bound to one Phase 339 feasibility record and the current accepted
append blocker set.
```

That still does not support:

- an implemented bounded formal-evidence class;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy changes;
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

Phase 342 should define the docs-first local reviewed formal-evidence metadata
class boundary. It may specify the future class shape, but must not implement
the class unless a later explicit implementation phase authorizes it. It must
not approve accepted formal evidence, mutate the accepted Evidence Ledger,
change accepted append policy, create Level2+ evidence, populate score axes, or
claim semantic correctness, production readiness, SOTA, full security, or action
authority.
