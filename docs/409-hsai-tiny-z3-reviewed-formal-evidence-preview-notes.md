# Phase 409 HSAI Tiny Z3 Reviewed Formal Evidence Preview Notes

State slice: `Phase 409 HSAI tiny Z3 reviewed-formal-evidence preview`.

## Boundary

Phase 409 implements local reviewed-formal-evidence preview metadata over a
Phase 407 tiny-Z3 formal-evidence candidate for:

```text
gateway-local-digest-binding-determinism-v1
```

The preview can classify one candidate as scoped-acceptable, rejected,
replay-blocked, or checker-lane-blocked under an explicit review policy and
explicit nonclaims. It is review-preview metadata only. It is not reviewed
formal evidence, accepted formal evidence, Level2+ evidence, score-axis
evidence, proof authority, semantic correctness, production readiness, SOTA,
breakthrough status, full security, or authority to execute an action.

## Implemented Surface

Phase 409 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_REVIEW_PREVIEW_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_REVIEW_PREVIEW_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_REVIEW_PREVIEW_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3ReviewPreviewDecisionLabel`;
- `GatewayFormalTinyDigestBackendZ3ReviewPreviewInput`;
- `GatewayFormalTinyDigestBackendZ3ReviewPreview`;
- `GatewayFormalTinyDigestBackendZ3ReviewPreviewIssue`;
- `GatewayFormalTinyDigestBackendZ3ReviewPreviewValidation`;
- `gateway_formal_tiny_digest_backend_z3_review_preview_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_review_preview_replay_readiness_checklist`;
- `gateway_formal_tiny_digest_backend_z3_review_preview_promotion_rejection_checklist`;
- `build_gateway_formal_tiny_digest_backend_z3_review_preview`;
- `validate_gateway_formal_tiny_digest_backend_z3_review_preview_input`.

## Validation Rules

Review-preview construction requires:

- Phase 407 candidate digest match;
- candidate input digest match;
- Phase 405 output-manifest digest match;
- Phase 404 execution digest match;
- Phase 403 probe digest match;
- candidate state exactly `formal_evidence_candidate`;
- candidate next state exactly `reviewed_formal_evidence`;
- reviewer policy id match;
- verifier policy id match;
- single-segment preview and reviewer decision ids;
- nonzero preview and decision timestamps;
- exact nonclaim acknowledgement digest;
- exact source correspondence statement digest;
- exact replay-readiness checklist and digest;
- exact promotion-rejection checklist and digest;
- no reviewed-evidence emission;
- no accepted-evidence emission;
- no Level2+ evidence;
- no score-axis population;
- no benchmark/SOTA comparison claim;
- no semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, or authority claim.

## Decision Labels

The implemented labels are:

- `ReviewPreviewAcceptCandidateScope`;
- `ReviewPreviewRejectCandidateScope`;
- `ReviewPreviewNeedsReplay`;
- `ReviewPreviewNeedsCheckerLane`.

These labels classify preview status only. They do not append evidence, create
reviewed formal evidence, or imply proof authority.

## Tests

Focused tests cover:

- successful review-preview construction for all four decision labels;
- preservation of the promotion ladder:
  `formal_evidence_candidate -> reviewed_formal_evidence_preview ->
  reviewed_formal_evidence`;
- proof/evidence/score/claim/authority flags held false;
- candidate digest drift rejection;
- policy drift rejection;
- nonclaim acknowledgement drift rejection;
- promotion-rejection checklist drift rejection;
- reviewed/accepted/Level2+/score/SOTA promotion rejection;
- promoted-candidate state rejection.

## Claim Boundary

Phase 409 supports only this claim:

```text
HSAI has a local tiny-Z3 reviewed-formal-evidence preview lane that can classify
one Phase 407 candidate as scoped-acceptable, rejected, replay-blocked, or
checker-lane-blocked without creating reviewed or accepted evidence.
```

It does not support reviewed formal evidence, accepted formal evidence, Level2+
formal evidence, score-axis evidence, a system Z3 proof, a Lean proof, a COBALT
containment proof, Rust-to-Lean extraction, checker transcript evidence, solver
certificate evidence, source correspondence proof, whole-system proof, semantic
correctness, production readiness, SOTA, breakthrough status, full security,
accepted Evidence Ledger mutation, or authority to execute an action.

## Next Slice

Phase 410 should define a docs-first reviewed-formal-evidence record boundary
for Phase 409 preview metadata. It must not mutate accepted evidence, create
Level2+ evidence, populate score axes, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.
