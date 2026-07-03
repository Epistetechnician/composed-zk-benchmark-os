# Phase 331 HSAI Reviewed Formal Evidence Preview Metadata Notes

State slice: `Phase 331 HSAI reviewed-formal-evidence preview metadata implementation`.

## Boundary

Phase 331 implements local review-preview metadata for Phase 329 formal-evidence
candidates. It can classify one candidate as scoped-acceptable, rejected,
replay-blocked, or checker-lane-blocked under an explicit review policy and
explicit nonclaims.

This is review-preview metadata only. It is not reviewed formal evidence,
accepted formal evidence, Level2+ evidence, score-axis evidence, proof
authority, semantic correctness, production readiness, SOTA, breakthrough
status, full security, or authority to execute an action.

## Implemented Surface

Phase 331 adds:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_REVIEW_PREVIEW_SCHEMA_VERSION`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_REVIEW_PREVIEW_STATE_SLICE`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_REVIEW_PREVIEW_CLAIM_BOUNDARY`.
- `GatewayFormalRealCommandLaneReviewPreviewDecisionLabel`.
- `GatewayFormalRealCommandLaneReviewPreviewInput`.
- `GatewayFormalRealCommandLaneReviewPreview`.
- `GatewayFormalRealCommandLaneReviewPreviewIssue`.
- `GatewayFormalRealCommandLaneReviewPreviewValidation`.
- Canonical replay-readiness and promotion-rejection checklist helpers.
- `build_gateway_formal_real_command_lane_review_preview`.
- `validate_gateway_formal_real_command_lane_review_preview_input`.

## Validation Rules

Review-preview construction requires:

- Phase 329 candidate digest match;
- candidate input digest match;
- Phase 327 manifest digest match;
- Phase 325 preflight digest match;
- Phase 323 source-manifest digest match;
- candidate state exactly `formal_evidence_candidate`;
- candidate next state exactly `reviewed_formal_evidence`;
- reviewer policy id match;
- verifier policy id match;
- single-segment review preview and decision ids;
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

These labels classify preview status only. They do not append evidence or imply
proof authority.

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
- review/accepted/SOTA/score-axis promotion rejection;
- promoted-candidate state rejection.

## Claim Boundary

Phase 331 supports this claim:

```text
HSAI has a local reviewed-formal-evidence preview lane that can classify one
formal-evidence candidate as scoped-acceptable, rejected, replay-blocked, or
checker-lane-blocked without creating reviewed or accepted evidence.
```

It does not support reviewed formal evidence, accepted formal evidence, Level2+
formal evidence, score-axis evidence, a system Z3 proof, a Lean proof, a COBALT
containment proof, Rust-to-Lean extraction, checker transcript evidence, solver
certificate evidence, source correspondence proof, whole-system proof, semantic
correctness, production readiness, SOTA, breakthrough status, full security,
accepted Evidence Ledger mutation, or authority to execute an action.

## Next Slice

Phase 332 may define a docs-first reviewed-formal-evidence record boundary for
Phase 331 previews. It must still avoid accepted Evidence Ledger mutation,
Level2+ evidence, score-axis population, SOTA claims, full-security claims,
production-readiness claims, semantic-correctness claims, and action authority.
