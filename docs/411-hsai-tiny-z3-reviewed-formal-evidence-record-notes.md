# Phase 411 HSAI Tiny Z3 Reviewed Formal Evidence Record Notes

State slice: `Phase 411 HSAI tiny Z3 reviewed-formal-evidence record`.

## Boundary

Phase 411 implements local reviewed formal-evidence record metadata over a
Phase 409 tiny-Z3 review preview for:

```text
gateway-local-digest-binding-determinism-v1
```

The record may be built only from a Phase 409
`ReviewPreviewAcceptCandidateScope` preview. It is reviewed-record metadata
only. It is not accepted formal evidence, Level2+ evidence, score-axis
evidence, proof authority, semantic correctness, production readiness, SOTA,
breakthrough status, full security, or authority to execute an action.

## Implemented Surface

Phase 411 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_REVIEWED_RECORD_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_REVIEWED_RECORD_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_REVIEWED_RECORD_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3ReviewedRecordInput`;
- `GatewayFormalTinyDigestBackendZ3ReviewedRecord`;
- `GatewayFormalTinyDigestBackendZ3ReviewedRecordIssue`;
- `GatewayFormalTinyDigestBackendZ3ReviewedRecordValidation`;
- `gateway_formal_tiny_digest_backend_z3_reviewed_record_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_reviewed_record_required_nonclaims`;
- `gateway_formal_tiny_digest_backend_z3_reviewed_record_accepted_evidence_disabled_acknowledgement`;
- `build_gateway_formal_tiny_digest_backend_z3_reviewed_record`;
- `validate_gateway_formal_tiny_digest_backend_z3_reviewed_record_input`.

## Validation Rules

Reviewed-record construction requires:

- Phase 409 preview digest match;
- Phase 409 preview-input digest match;
- Phase 407 candidate digest match;
- Phase 407 candidate-input digest match;
- Phase 405 output-manifest digest match;
- Phase 404 execution digest match;
- Phase 403 probe digest match;
- Phase 409 preview state exactly `reviewed_formal_evidence_preview`;
- Phase 409 preview next state exactly `reviewed_formal_evidence`;
- Phase 409 decision exactly `ReviewPreviewAcceptCandidateScope`;
- reviewer policy id match;
- verifier policy id match;
- reviewer decision id and timestamp match;
- reviewed-scope statement digest match;
- exact preview nonclaim acknowledgement;
- exact source correspondence statement digest;
- exact replay-readiness checklist and digest;
- exact promotion-rejection checklist and digest;
- exact accepted-evidence-disabled acknowledgement and digest;
- no accepted-evidence mutation;
- no accepted formal-evidence creation;
- no Level2+ evidence;
- no score-axis population;
- no benchmark/SOTA comparison claim;
- no semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, or authority claim.

## Tests

Focused tests cover:

- successful reviewed-record construction from `ReviewPreviewAcceptCandidateScope`;
- preservation of the promotion ladder:
  `reviewed_formal_evidence_preview -> reviewed_formal_evidence ->
  accepted_formal_evidence`;
- rejection of reject-preview, replay-blocked, and checker-lane-blocked
  decisions;
- preview digest drift rejection;
- candidate digest drift rejection;
- policy drift rejection;
- preview nonclaim acknowledgement drift rejection;
- accepted-evidence-disabled acknowledgement drift rejection;
- reviewed-scope claim escalation rejection;
- accepted-evidence, accepted-formal-evidence, Level2+, score-axis, SOTA, and
  full-security promotion rejection;
- promoted-preview state rejection.

## Claim Boundary

Phase 411 supports only this claim:

```text
HSAI has a local tiny-Z3 reviewed formal-evidence record metadata lane for one
scoped digest-binding admission invariant, with digest-bound candidate,
preview, execution, output, and probe provenance plus explicit nonclaims and
accepted-evidence-disabled acknowledgement.
```

It does not support accepted formal evidence, Level2+ formal evidence,
score-axis evidence, a system Z3 proof, a Lean proof, a COBALT containment
proof, Rust-to-Lean extraction, checker transcript evidence, solver certificate
evidence, source correspondence proof, whole-system proof, semantic
correctness, production readiness, SOTA, breakthrough status, full security,
accepted Evidence Ledger mutation, or authority to execute an action.

## Next Slice

Phase 412 should define a docs-first tiny-Z3 accepted-formal-evidence handoff
boundary. It must keep the accepted Evidence Ledger path separate and must not
mutate accepted evidence, create Level2+ evidence, populate score axes, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.
