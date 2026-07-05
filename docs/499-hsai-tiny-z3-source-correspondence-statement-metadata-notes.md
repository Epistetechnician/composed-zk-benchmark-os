# Phase 499 HSAI Tiny Z3 Source Correspondence Statement Metadata Notes

State slice: `Phase 499 HSAI tiny Z3 source correspondence statement
metadata`.

Phase 499 implements local in-memory metadata for the Phase 488 accepted-path
prerequisite gate:

```text
source correspondence statement and digest
```

The implemented record binds one Phase 497 replayable input identity record to
the source anchor requirements defined in Phase 498. It records the source
paths, source anchors, statement digest input requirements, source path digest
requirements, reviewer policy requirement, drift rejection policy, and explicit
nonclaims that a future accepted-path bridge must satisfy.

This phase does not create a correspondence artifact, write digest sidecars,
write filesystem artifacts, create an accepted append decision, mutate the
accepted Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, create benchmark
evidence, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant authority to execute
an action.

## Implemented Surface

`crates/hsai-agent-admission/src/lib.rs` now defines:

- `GATEWAY_FORMAL_TINY_Z3_SOURCE_CORRESPONDENCE_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_SOURCE_CORRESPONDENCE_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_SOURCE_CORRESPONDENCE_CLAIM_BOUNDARY`;
- source path and source commit requirement constants;
- `GatewayFormalTinyZ3SourceCorrespondenceInput`;
- `GatewayFormalTinyZ3SourceCorrespondence`;
- `GatewayFormalTinyZ3SourceCorrespondenceIssue`;
- `GatewayFormalTinyZ3SourceCorrespondenceValidation`;
- source path, source anchor, statement digest input, nonclaim, unsupported
  claim, and drift rejection helpers;
- digest, id, and label binding helpers;
- `build_gateway_formal_tiny_z3_source_correspondence`;
- `validate_gateway_formal_tiny_z3_source_correspondence_input`.

The metadata binds these HSAI admission anchors:

- `GatewayFormalTinyZ3ReplayableInputIdentityInput`;
- `GatewayFormalTinyZ3ReplayableInputIdentity`;
- `GatewayFormalTinyZ3ReplayableInputIdentityIssue`;
- `GatewayFormalTinyZ3ReplayableInputIdentityValidation`;
- Phase 497 schema, state-slice, and claim-boundary constants;
- Phase 497 transaction, preflight, candidate, append-preview, and validation
  rule helpers;
- Phase 497 replay identity builder and validator.

The metadata binds these `zkbench-core` anchors:

- `AcceptedLedgerAppendTransactionRequest`;
- `validate_accepted_ledger_append_transaction_request`;
- `build_evidence_record_from_transaction`;
- `ReviewedPromotionPreflightRequest`;
- `ReviewedPromotionPreflightReport`;
- `build_reviewed_promotion_preflight_report`;
- `validate_reviewed_promotion_preflight_request`;
- `EvidenceRecordCandidate`;
- `EvidenceRecordCandidateSource`;
- `EvidenceAppendPreview`;
- `EvidenceClass`;
- `ClaimBoundary`;
- `EvidenceRecord`.

The validator requires statement digest inputs for source paths, source
digests, source anchors, Phase 497 binding digests, current accepted append
blocker digest, explicit nonclaim digest, reviewer policy, reviewer decision
requirement, and drift rejection policy.

The validator rejects:

- Phase 497 digest/id/label/nonclaim drift;
- Phase 497 replay identity state drift;
- source commit requirement drift;
- HSAI admission source path drift;
- accepted append source path drift;
- HSAI admission source anchor drift;
- `zkbench-core` accepted append source anchor drift;
- statement digest input drift;
- source path digest requirement drift;
- correspondence claim drift;
- unsupported claim set drift;
- missing reviewer decision requirement;
- drift rejection policy drift;
- correspondence artifact creation;
- digest sidecar creation;
- accepted append decisions;
- accepted Evidence Ledger mutation attempts;
- accepted append policy changes;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof/checker/solver authority;
- Lean/new-SMT/COBALT/Rust-to-Lean execution evidence;
- benchmark evidence;
- SOTA, semantic-correctness, production-readiness, breakthrough,
  full-security, or action-authority claims.

## Validation

Focused tests cover:

- successful Phase 499 metadata construction over a valid Phase 497 replayable
  input identity record;
- Phase 497 digest drift rejection;
- HSAI admission source anchor drift rejection;
- statement digest input drift rejection;
- promotion-attempt rejection, including correspondence artifact and digest
  sidecar creation.

## Meaning Limit

The new metadata supports only this claim:

```text
HSAI locally records the source anchors and digest requirements that must tie a
future tiny-Z3 accepted-path bridge to the current HSAI replay identity metadata
and the current zkbench-core accepted-append replay validators.
```

It is still not accepted append, not accepted evidence, not accepted formal
evidence, not accepted Evidence Ledger mutation, not accepted append policy
change, not a correspondence artifact, not a digest sidecar, not Level2+
evidence, not score-axis evidence, not proof authority, not checker transcript
authority, not solver certificate authority, not backend execution evidence,
not benchmark evidence, not SOTA, not semantic correctness, not production
readiness, not full security, and not action authority.

## Next Responsible Slice

The next responsible slice is a docs-first boundary for the next Phase 488
accepted-path prerequisite gate: reviewer policy and reviewer decision
requirements. It must not implement accepted append, mutate the accepted
Evidence Ledger, create accepted formal evidence, create Level2+ evidence,
populate score axes, run Lean/new-SMT/COBALT/Rust-to-Lean extraction, create
benchmark evidence, or claim SOTA, full security, semantic correctness, or
production readiness.
