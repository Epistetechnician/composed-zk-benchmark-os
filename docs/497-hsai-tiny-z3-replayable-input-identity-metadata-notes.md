# Phase 497 HSAI Tiny Z3 Replayable Input Identity Metadata Notes

State slice: `Phase 497 HSAI tiny Z3 replayable input identity metadata`.

Phase 497 implements local in-memory metadata for the Phase 488 accepted-path
prerequisite gate:

```text
replayable input bundle identity
```

The implemented record binds one Phase 495 accepted evidence class
claim-boundary record to the existing `zkbench-core` accepted-append replay
identity surface:

```text
AcceptedLedgerAppendTransactionRequest
AcceptedLedgerAppendTransactionVersion
ReviewedPromotionPreflightRequest
ReviewedPromotionPreflightReport
EvidenceRecordCandidate
EvidenceRecordCandidateSource
EvidenceAppendPreview
```

This phase does not materialize a replayable bundle, write filesystem
artifacts, create an accepted append decision, mutate the accepted Evidence
Ledger, change accepted append policy, create accepted formal evidence, create
Level2+ evidence, populate score axes, generate proof artifacts, generate
checker transcripts, generate solver certificates, run Lean, run new SMT, run
COBALT, run Rust-to-Lean extraction, create benchmark evidence, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough
status, claim full security, or grant authority to execute an action.

## Implemented Surface

`crates/hsai-agent-admission/src/lib.rs` now defines:

- `GATEWAY_FORMAL_TINY_Z3_REPLAYABLE_INPUT_IDENTITY_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_REPLAYABLE_INPUT_IDENTITY_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_REPLAYABLE_INPUT_IDENTITY_CLAIM_BOUNDARY`;
- replay identity owner and `zkbench-core` type constants;
- `GatewayFormalTinyZ3ReplayableInputIdentityInput`;
- `GatewayFormalTinyZ3ReplayableInputIdentity`;
- `GatewayFormalTinyZ3ReplayableInputIdentityIssue`;
- `GatewayFormalTinyZ3ReplayableInputIdentityValidation`;
- digest, id, label, nonclaim, field-set, and validation-rule helpers;
- `build_gateway_formal_tiny_z3_replayable_input_identity`;
- `validate_gateway_formal_tiny_z3_replayable_input_identity_input`.

The metadata binds these replay-critical field sets:

- transaction fields: transaction id, transaction version, target evidence
  ledger id, and expected current ledger tip;
- preflight fields: preflight id, version, candidate, append preview, review
  decision, expected current ledger tip, source artifact digests, and preflight
  report;
- candidate fields: candidate id and candidate source;
- append-preview fields: append-preview id, source candidate id, and proposed
  append entries.

The validator requires these replay validation rules:

- preflight request validation;
- preflight report recomputation from the supplied request;
- current ledger tip equality;
- candidate/append-preview source id alignment;
- append-preview entry candidate id, evidence class, claim boundary, and
  candidate digest alignment;
- source artifact digest presence;
- local replay Level1 cap;
- Level2+/formal class rejection;
- official submission and score-axis rejection.

The validator rejects:

- Phase 495 digest/id/label/nonclaim drift;
- Phase 495 class-boundary state drift;
- owner and type drift;
- transaction, preflight, candidate, or append-preview field drift;
- replay validation rule drift;
- accepted evidence class or claim-boundary drift;
- filesystem bundle creation;
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

- successful Phase 497 metadata construction over a valid Phase 495
  class-boundary record;
- Phase 495 digest drift rejection;
- transaction field-set drift rejection;
- replay validation rule drift rejection;
- promotion-attempt rejection, including filesystem bundle creation.

## Meaning Limit

The new metadata supports only this claim:

```text
HSAI locally records the existing zkbench-core accepted-append request,
preflight, report, candidate, append-preview, source-digest, and ledger-tip
identity fields that a future bridge must bind before transaction evaluation.
```

It is still not accepted append, not accepted evidence, not accepted formal
evidence, not accepted Evidence Ledger mutation, not accepted append policy
change, not a replayable bundle, not Level2+ evidence, not score-axis evidence,
not proof authority, not benchmark evidence, not SOTA, not semantic
correctness, not production readiness, not full security, and not action
authority.

## Next Responsible Slice

The next responsible slice is a docs-first boundary for the next Phase 488
accepted-path prerequisite gate: source correspondence statement and digest.
It must not implement accepted append, mutate the accepted Evidence Ledger,
create accepted formal evidence, create Level2+ evidence, populate score axes,
run Lean/new-SMT/COBALT/Rust-to-Lean extraction, create benchmark evidence, or
claim SOTA, full security, semantic correctness, or production readiness.
