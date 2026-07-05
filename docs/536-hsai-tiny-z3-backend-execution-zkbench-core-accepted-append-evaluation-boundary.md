# Phase 536 HSAI Tiny Z3 Backend Execution Zkbench-Core Accepted Append Evaluation Boundary

State slice: `Phase 536 HSAI tiny Z3 backend execution zkbench-core accepted append evaluation boundary`.

Phase 536 defines the docs-first boundary for the first owner-validator
crossing after
`docs/535-hsai-tiny-z3-backend-execution-accepted-evidence-owner-decision-metadata-notes.md`:

```text
Phase 535 local owner-decision metadata
  + zkbench-core accepted append validator boundary
  -> future validation-only accepted append evaluation metadata
```

This boundary is necessary because Phase 535 can only say that a reviewed local
SMT/Z3 backend execution package may proceed to a later `zkbench-core`
evaluation boundary. It cannot call the accepted append validator, create an
accepted append decision, mutate an accepted Evidence Ledger, or create
accepted evidence.

This phase does not implement Rust code, change Cargo metadata, add a
`zkbench-core` dependency to `hsai-agent-admission`, call
`validate_accepted_ledger_append_transaction_request`, call accepted append
mutation APIs, read accepted Evidence Ledger files, write accepted Evidence
Ledger files, create accepted evidence, create accepted formal evidence, create
Level2+ evidence, populate score axes, generate proof artifacts, generate
checker transcripts, generate solver certificates, run Lean, run another
SMT/Z3 execution, run COBALT, run Rust-to-Lean extraction, run external replay,
submit benchmarks, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, claim independent
external reproduction, or grant authority to execute an action.

## Required Future Input

A future implementation may evaluate only one exact Phase 535 owner-decision
record with:

- schema `hsai-gateway-formal-tiny-z3-backend-execution-accepted-evidence-owner-decision:v1`;
- state slice
  `phase-535-hsai-tiny-z3-backend-execution-accepted-evidence-owner-decision-metadata`;
- decision label
  `BackendExecutionAcceptedEvidenceRouteNeedsZkbenchCoreEvaluation`;
- accepted-evidence owner `zkbench-core`;
- local transaction route `AcceptedLedgerAppendTransactionRequest`;
- materialized route `MaterializedAcceptedLedgerAppendRequest`;
- evidence-class and claim-boundary owners `zkbench-core`;
- maximum claim boundary `Level1LocalReplay`;
- rejected Level2 floor `Level2ReproducibleBenchmarkArtifact`;
- no accepted evidence, accepted formal evidence, Level2+, score axes,
  proof/checker/solver authority, Lean/COBALT/Rust-to-Lean evidence,
  additional SMT/Z3 execution, benchmark evidence, external audit, independent
  reproduction, strong public claim, or action authority.

The future implementation must bind the inherited Phase 533, Phase 531, Phase
529, and Phase 527 digests from the Phase 535 record. It must not recompute
the chain from unreviewed source metadata.

## Zkbench-Core Owner Surface

The future boundary may name these existing owner surfaces:

- `AcceptedLedgerAppendTransactionRequest`;
- `AcceptedLedgerAppendTransactionValidation`;
- `AcceptedLedgerAppendTransactionIssueKind`;
- `ReviewedPromotionPreflightRequest`;
- `ReviewedPromotionPreflightReport`;
- `EvidenceLedger`;
- `EvidenceRecordCandidate`;
- `EvidenceClass`;
- `ClaimBoundary`;
- `validate_accepted_ledger_append_transaction_request`.

The future boundary must not call or wrap these mutation surfaces:

- `apply_accepted_ledger_append_transaction`;
- `apply_materialized_accepted_ledger_append_transaction`;
- `EvidenceLedger::save_json`;
- any filesystem materialization path for an accepted Evidence Ledger.

## Required Future Evaluation Inputs

A future validation-only implementation must bind:

- one Phase 535 owner-decision digest and input digest;
- the Phase 535 digest-binding map digest;
- the Phase 535 id-binding map digest;
- the Phase 535 label-binding map digest;
- the Phase 535 explicit nonclaim digest;
- the Phase 535 owner-decision policy digest;
- the Phase 535 owner-decision rule digest;
- the Phase 535 forbidden-API digest;
- the Phase 535 inherited-digest requirement digest;
- the Phase 533 review digest and input digest;
- the Phase 531 package digest and input digest;
- the Phase 529 backend execution result digest and request digest;
- the Phase 527 candidate digest and input digest;
- the exact `AcceptedLedgerAppendTransactionRequest` type name;
- the exact `ReviewedPromotionPreflightRequest` and
  `ReviewedPromotionPreflightReport` type names;
- the exact `EvidenceLedger` type name and target ledger id;
- the target transaction id;
- the expected current ledger tip digest;
- the append-preview current ledger tip digest;
- the accepted append request digest;
- the candidate digest;
- the append preview digest;
- the review decision digest;
- the source artifact digest set digest;
- the validation function identifier
  `validate_accepted_ledger_append_transaction_request`;
- a validation-only output classification that distinguishes validator
  accepted, validator rejected, and evaluation input incomplete.

Unknown ledger ids, ledger tips, preflight reports, append previews, review
decisions, and source artifact digests must remain unresolved. The future
implementation must not invent them.

## Required Future Validation

A future implementation must fail closed if:

- the Phase 535 record is not exact;
- the Phase 535 decision label is not
  `BackendExecutionAcceptedEvidenceRouteNeedsZkbenchCoreEvaluation`;
- any Phase 535, Phase 533, Phase 531, Phase 529, or Phase 527 digest drifts;
- the accepted-evidence owner is not `zkbench-core`;
- the transaction route is not `AcceptedLedgerAppendTransactionRequest`;
- the materialized route is not `MaterializedAcceptedLedgerAppendRequest`;
- the maximum claim boundary is above `Level1LocalReplay`;
- the validation function identifier is not
  `validate_accepted_ledger_append_transaction_request`;
- the request asks for accepted append mutation;
- the request asks for materialized accepted ledger append output;
- the request asks to read or write accepted Evidence Ledger files;
- the request lacks the target ledger id, transaction id, preflight report,
  append preview, review decision, source artifact digest set, candidate, or
  current-tip binding required by the existing `zkbench-core` validator;
- the request tries to create accepted formal evidence;
- the request tries to create Level2+ evidence;
- the request tries to populate score axes;
- the request tries to create proof/checker/solver authority;
- the request tries to claim Lean, COBALT, Rust-to-Lean, additional SMT/Z3,
  benchmark, external-audit, independent-reproduction, semantic-correctness,
  production-readiness, SOTA, breakthrough, full-security, or action-authority
  status.

## Meaning Limit

The future evaluation metadata may support this claim only:

```text
HSAI locally records a validation-only boundary for asking the existing
zkbench-core accepted append validator to evaluate one reviewed local SMT/Z3
backend execution package under the existing Level1 cap.
```

That still is not:

- accepted append mutation;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- materialized accepted ledger output;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- checker transcript authority;
- solver certificate authority;
- benchmark evidence;
- independent external reproduction;
- external audit;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 537 Implementation Exit Criteria

A future Phase 537 may implement local validation-only evaluation metadata only
if it:

- stays within explicitly authorized files for that phase;
- adds any required `zkbench-core` dependency only under a separate explicit
  Cargo-change allowance;
- writes no filesystem artifacts;
- performs no process or network calls;
- runs no Lean, COBALT, Rust-to-Lean extraction, or additional SMT/Z3 process;
- reads or mutates no accepted Evidence Ledger files;
- does not call accepted append mutation APIs;
- validates one exact Phase 535 owner-decision record;
- binds the existing `zkbench-core` accepted append validator surface;
- records unresolved accepted append inputs explicitly instead of inventing
  them;
- records a validation-only result or incomplete-input result without creating
  accepted evidence;
- rejects accepted-evidence mutation, accepted formal evidence, Level2+,
  score-axis, proof/checker/solver-authority, backend-execution, benchmark,
  independent-reproduction, external-audit, strong-claim, and action-authority
  attempts.
