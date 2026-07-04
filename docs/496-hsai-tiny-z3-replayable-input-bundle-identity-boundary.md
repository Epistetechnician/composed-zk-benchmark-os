# Phase 496 HSAI Tiny Z3 Replayable Input Bundle Identity Boundary

State slice: `Phase 496 HSAI tiny Z3 replayable input bundle identity
boundary`.

Phase 496 defines the docs-first boundary for the next Phase 488 accepted-path
prerequisite gate:

```text
replayable input bundle identity
```

Phase 495 implemented local metadata for the accepted evidence class and claim
boundary gate. Phase 496 records the next boundary: any future HSAI
accepted-path bridge must bind the exact replayable input identity fields that
`zkbench-core` already validates before accepted-ledger append evaluation.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, create a bundle, create an accepted append decision,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run new SMT, run COBALT, run Rust-to-Lean extraction,
submit benchmarks, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, or grant authority
to execute an action.

## Current Replayable Input Surface

The current accepted-append replay surface remains owned by `zkbench-core`:

- `crates/zkbench-core/src/evidence/accepted_append.rs`;
- `AcceptedLedgerAppendTransactionRequest`;
- `AcceptedLedgerAppendTransactionVersion`;
- `validate_accepted_ledger_append_transaction_request`;
- `build_evidence_record_from_transaction`;
- `crates/zkbench-core/src/evidence/promotion_preflight.rs`;
- `ReviewedPromotionPreflightRequest`;
- `ReviewedPromotionPreflightReport`;
- `build_reviewed_promotion_preflight_report`;
- `validate_reviewed_promotion_preflight_request`;
- `crates/zkbench-core/src/evidence/candidate.rs`;
- `EvidenceRecordCandidate`;
- `EvidenceRecordCandidateSource`;
- `crates/zkbench-core/src/evidence/append_preview.rs`;
- `EvidenceAppendPreview`.

The replayable identity fields are:

```text
AcceptedLedgerAppendTransactionRequest.transaction_id
AcceptedLedgerAppendTransactionRequest.version
AcceptedLedgerAppendTransactionRequest.target_evidence_ledger_id
AcceptedLedgerAppendTransactionRequest.expected_current_ledger_tip
ReviewedPromotionPreflightRequest.id
ReviewedPromotionPreflightRequest.version
ReviewedPromotionPreflightRequest.candidate
ReviewedPromotionPreflightRequest.append_preview
ReviewedPromotionPreflightRequest.review_decision
ReviewedPromotionPreflightRequest.expected_current_ledger_tip
ReviewedPromotionPreflightRequest.source_artifact_digests
ReviewedPromotionPreflightReport
EvidenceRecordCandidate.id
EvidenceRecordCandidate.source
EvidenceAppendPreview.id
EvidenceAppendPreview.source_candidate_id
EvidenceAppendPreview.proposed_append_entries
```

The replayable identity checks already performed by `zkbench-core` include:

- preflight request validation;
- preflight report recomputation from the supplied preflight request;
- current ledger tip equality across the transaction, preflight request, append
  preview, and target ledger;
- candidate id equality with append preview source candidate id;
- append preview entry equality with candidate id, evidence class, claim
  boundary, and candidate digest;
- source artifact digest presence;
- local accepted append cap at `Level1LocalReplay`;
- rejection of Level2+/formal classes;
- rejection of official submission and score-axis attempts.

## HSAI Admission Role

`crates/hsai-agent-admission` may record local metadata that references the
accepted append replayable input identity fields. It may not materialize a
bundle, infer accepted evidence from metadata, bypass `zkbench-core`
validation, compute a substitute ledger tip, define a competing accepted
append input schema, or treat local metadata as an accepted append
transaction.

A future HSAI bridge may satisfy this gate only if it binds a digest-stable
identity over the existing `zkbench-core` request/preflight/report/candidate
and append-preview fields. Unknown future bridge inputs must remain unresolved.

## Required Future Bindings

A future implementation that tries to satisfy this gate must bind:

- one Phase 495 accepted evidence class claim-boundary record digest;
- one Phase 495 accepted evidence class claim-boundary input digest;
- the Phase 495 digest-binding map digest;
- the Phase 495 id-binding map digest;
- the Phase 495 label-binding map digest;
- the Phase 495 explicit nonclaim digest;
- current accepted append blocker digest;
- accepted append owner `zkbench-core`;
- replay identity owner `zkbench-core`;
- transaction request type `AcceptedLedgerAppendTransactionRequest`;
- transaction version type `AcceptedLedgerAppendTransactionVersion`;
- preflight request type `ReviewedPromotionPreflightRequest`;
- preflight report type `ReviewedPromotionPreflightReport`;
- candidate type `EvidenceRecordCandidate`;
- candidate source type `EvidenceRecordCandidateSource`;
- append preview type `EvidenceAppendPreview`;
- transaction id field;
- transaction version field;
- target evidence ledger id field;
- transaction expected current ledger tip field;
- preflight request id field;
- preflight request version field;
- candidate field;
- append preview field;
- review decision field;
- preflight expected current ledger tip field;
- source artifact digests field;
- preflight report recomputation rule;
- candidate/append-preview alignment rule;
- source artifact digest requirement;
- local replay class and Level1 claim-boundary cap from Phase 495.

## Required Future Validation

A future validator must reject the replayable input identity gate input if:

- the schema version is not the future Phase 497 schema;
- any Phase 495 digest/id/label/nonclaim binding drifts;
- the current accepted append blocker digest drifts;
- the accepted append owner is not `zkbench-core`;
- the replay identity owner is not `zkbench-core`;
- any required `zkbench-core` type or field name drifts;
- the metadata omits transaction id, transaction version, target ledger id, or
  expected current ledger tip;
- the metadata omits preflight request id, version, candidate, append preview,
  review decision, expected current ledger tip, or source artifact digests;
- the metadata omits preflight report recomputation;
- the metadata omits candidate/append-preview alignment;
- the metadata omits source artifact digest presence;
- the metadata tries to create a filesystem bundle;
- the metadata tries to create an accepted append decision;
- the metadata tries to mutate the accepted Evidence Ledger;
- the metadata tries to change accepted append policy;
- the metadata tries to create accepted formal evidence;
- the metadata tries to create Level2+ evidence;
- the metadata tries to populate score axes;
- the metadata tries to create proof/checker/solver authority;
- the metadata tries to create Lean/new-SMT/COBALT/Rust-to-Lean execution
  evidence;
- the metadata tries to create benchmark evidence;
- the metadata tries to claim SOTA, semantic correctness, production
  readiness, full security, breakthrough status, or action authority.

## Meaning Limit

The future replayable input identity gate record may support this claim only:

```text
HSAI locally records the existing zkbench-core accepted-append request,
preflight, candidate, append-preview, source-digest, and ledger-tip identity
fields that a future accepted append bridge must bind before transaction
evaluation.
```

That still is not:

- accepted append;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- benchmark evidence;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 497 Implementation Exit Criteria

Phase 497 may implement local replayable input bundle identity metadata only if
it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds the Phase 495 record digest and input digest;
- binds the Phase 495 digest/id/label map digests;
- binds the Phase 495 explicit nonclaim digest;
- identifies `zkbench-core` as the accepted append and replay identity owner;
- identifies the current `zkbench-core` transaction, preflight, report,
  candidate, candidate-source, and append-preview types;
- identifies the replay-critical field names listed in this boundary;
- records source artifact digest presence as required;
- records preflight report recomputation as required;
- records candidate/append-preview alignment as required;
- records current ledger tip equality as required;
- records unknown future bridge inputs as unresolved;
- rejects filesystem bundle creation in the gate metadata itself;
- rejects accepted append decisions in the gate metadata itself;
- rejects accepted Evidence Ledger mutation in the gate metadata itself;
- rejects accepted append policy changes in the gate metadata itself;
- rejects accepted formal evidence creation in the gate metadata itself;
- rejects Level2+ evidence creation in the gate metadata itself;
- rejects score-axis population in the gate metadata itself;
- rejects proof/checker/solver authority creation in the gate metadata itself;
- rejects Lean/new-SMT/COBALT/Rust-to-Lean execution evidence creation in the
  gate metadata itself;
- rejects benchmark evidence creation in the gate metadata itself;
- rejects SOTA, semantic-correctness, production-readiness, full-security,
  breakthrough, and action-authority claims in the gate metadata itself.
