# Phase 498 HSAI Tiny Z3 Source Correspondence Statement Digest Boundary

State slice: `Phase 498 HSAI tiny Z3 source correspondence statement digest
boundary`.

Phase 498 defines the docs-first boundary for the next Phase 488
accepted-path prerequisite gate:

```text
source correspondence statement and digest
```

Phase 497 implemented local metadata for the replayable input identity gate.
Phase 498 records the next boundary: any future accepted-path bridge must bind
the exact source anchors that connect the HSAI tiny-Z3 metadata record to the
`zkbench-core` accepted-append replay validators before any accepted append,
accepted formal evidence, Level2+ evidence, score-axis population, or strong
public claim can be considered.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, create a correspondence statement artifact, create a
digest sidecar, create an accepted append decision, mutate the accepted
Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Required Source Anchor Set

The future source correspondence statement must bind both sides of the bridge.

### HSAI Admission Anchors

The HSAI side is owned by `crates/hsai-agent-admission/src/lib.rs` and must
cite these anchors:

- `GatewayFormalTinyZ3ReplayableInputIdentityInput`;
- `GatewayFormalTinyZ3ReplayableInputIdentity`;
- `GatewayFormalTinyZ3ReplayableInputIdentityIssue`;
- `GatewayFormalTinyZ3ReplayableInputIdentityValidation`;
- `GATEWAY_FORMAL_TINY_Z3_REPLAYABLE_INPUT_IDENTITY_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_REPLAYABLE_INPUT_IDENTITY_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_REPLAYABLE_INPUT_IDENTITY_CLAIM_BOUNDARY`;
- `gateway_formal_tiny_z3_replayable_input_identity_transaction_fields`;
- `gateway_formal_tiny_z3_replayable_input_identity_preflight_fields`;
- `gateway_formal_tiny_z3_replayable_input_identity_candidate_fields`;
- `gateway_formal_tiny_z3_replayable_input_identity_append_preview_fields`;
- `gateway_formal_tiny_z3_replayable_input_identity_validation_rules`;
- `build_gateway_formal_tiny_z3_replayable_input_identity`;
- `validate_gateway_formal_tiny_z3_replayable_input_identity_input`.

### Accepted Append Anchors

The accepted append side remains owned by `zkbench-core` and must cite these
anchors:

- `crates/zkbench-core/src/evidence/accepted_append.rs`;
- `AcceptedLedgerAppendTransactionRequest`;
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
- `EvidenceAppendPreview`;
- `crates/zkbench-core/src/evidence/mod.rs`;
- `EvidenceClass`;
- `ClaimBoundary`;
- `EvidenceRecord`.

The statement must fail closed if it cites docs without citing source anchors,
if it cites only HSAI metadata without the `zkbench-core` accepted append
surface, or if it treats any source anchor as implied by imports.

## Required Statement Fields

A future correspondence statement may satisfy this gate only if it records:

- statement schema version;
- statement id;
- statement digest;
- state slice;
- source commit;
- source file paths;
- source file digests;
- source anchor names;
- Phase 497 replayable input identity record digest;
- Phase 497 replayable input identity input digest;
- Phase 497 digest-binding map digest;
- Phase 497 id-binding map digest;
- Phase 497 label-binding map digest;
- Phase 497 explicit nonclaim digest;
- current accepted append blocker digest;
- exact correspondence claim text;
- unsupported correspondence claims;
- explicit nonclaim set;
- explicit nonclaim digest;
- reviewer policy id;
- reviewer decision requirement;
- drift rejection policy;
- next required state.

The future statement digest must be computed over the statement content, the
source anchor list, the source file digests, the Phase 497 binding digests, the
current blocker digest, and the explicit nonclaim digest. A digest over only
free-form prose is not enough.

## Required Correspondence Claim

The maximum future correspondence claim for this gate is:

```text
The Phase 497 HSAI tiny-Z3 replayable input identity metadata names the current
zkbench-core accepted-append request, preflight, report, candidate,
append-preview, source-digest, ledger-tip, evidence-class, and claim-boundary
source anchors that a future accepted-path bridge must bind before transaction
evaluation.
```

That claim is only a source correspondence statement. It is not a proof that
the bridge is correct, not accepted evidence, not formal evidence, not a
checker transcript, not a solver certificate, and not semantic correctness.

## Required Future Validation

A future implementation that tries to satisfy this gate must reject the source
correspondence input if:

- the schema version is not the future Phase 499 schema;
- any required HSAI admission anchor is missing;
- any required `zkbench-core` accepted append anchor is missing;
- any source path is empty, nonportable, or points outside the repository;
- any source digest is empty or malformed;
- the source commit is empty;
- any Phase 497 digest/id/label/nonclaim binding drifts;
- the current accepted append blocker digest drifts;
- the statement digest omits source file digests;
- the statement digest omits the Phase 497 binding digests;
- the statement digest omits the explicit nonclaim digest;
- the statement claims executable bridge correctness;
- the statement claims accepted append authority;
- the statement claims accepted formal evidence;
- the statement claims proof/checker/solver authority;
- the statement claims Lean/new-SMT/COBALT/Rust-to-Lean execution evidence;
- the statement claims Level2+ evidence;
- the statement claims score-axis evidence;
- the statement claims benchmark evidence;
- the statement claims SOTA, semantic correctness, production readiness, full
  security, breakthrough status, or action authority.

## Backend Relationship

This boundary is a prerequisite for later backend execution. It does not cross
the backend execution boundary.

- A Lean or Rust-to-Lean run would still need an extraction/model policy and a
  checked theorem scoped to the cited anchors.
- An SMT or COBALT-style run would still need a model correspondence policy
  that states which Rust behavior is abstracted away.
- A checker transcript would still need a checker authority policy.
- A solver transcript would still need a solver authority policy.
- A benchmark or score-axis result would still need an accepted benchmark
  evidence policy.

Cross-backend agreement is not proof unless each backend result has its own
source correspondence statement, claim boundary, transcript authority, and
review decision.

## Meaning Limit

The future source correspondence statement digest may support this claim only:

```text
HSAI locally records the source anchors and digest requirements that must tie a
future tiny-Z3 accepted-path bridge to the current HSAI replay identity metadata
and the current zkbench-core accepted-append replay validators.
```

That still is not:

- accepted append;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- replayable bundle materialization;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- checker transcript authority;
- solver certificate authority;
- benchmark evidence;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 499 Implementation Status

Phase 499 implements local source correspondence statement metadata in
`docs/499-hsai-tiny-z3-source-correspondence-statement-metadata-notes.md`.
That implementation:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 497 replayable input identity record digest;
- binds one Phase 497 replayable input identity input digest;
- binds the Phase 497 digest/id/label map digests;
- binds the Phase 497 explicit nonclaim digest;
- binds current accepted append blocker digest;
- records every required HSAI admission source anchor listed above;
- records every required `zkbench-core` source anchor listed above;
- records source file path and digest requirements;
- records statement digest construction requirements;
- rejects source-anchor drift in the gate metadata itself;
- rejects statement-digest drift in the gate metadata itself;
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
