# Phase 494 HSAI Tiny Z3 Accepted Evidence Class And Claim Boundary

State slice: `Phase 494 HSAI tiny Z3 accepted evidence class and
claim-boundary boundary`.

Phase 494 defines the docs-first boundary for the third Phase 489
accepted-path prerequisite gate:

```text
accepted_evidence_class_and_claim_boundary
```

Phase 493 recorded accepted append policy-version metadata. Phase 488 already
listed the accepted evidence class and exact claim boundary as unresolved
accepted-path prerequisites. Phase 494 records the next boundary: any future
HSAI accepted-path bridge must bind the exact `zkbench-core` accepted evidence
class and claim-boundary pair before any accepted append, accepted formal
evidence, Level2+, score-axis, benchmark, SOTA, semantic-correctness,
production-readiness, full-security, breakthrough, or action-authority claim
can be considered.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate the accepted Evidence Ledger, create an accepted
append decision, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Current Class And Boundary Surface

The current evidence class and claim-boundary surface remains owned by
`zkbench-core`:

- `crates/zkbench-core/src/evidence/mod.rs`;
- `EvidenceClass`;
- `ClaimBoundary`;
- `EvidenceRecord`;
- `crates/zkbench-core/src/evidence/candidate.rs`;
- `EvidenceRecordCandidate`;
- `validate_evidence_record_candidate`;
- `build_evidence_record_candidate_from_reviewed_proposal`;
- `crates/zkbench-core/src/evidence/accepted_append.rs`;
- `AcceptedLedgerAppendTransactionRequest`;
- `validate_accepted_ledger_append_transaction_request`;
- `build_evidence_record_from_transaction`;
- `crates/zkbench-core/src/evidence/ledger.rs`;
- `EvidenceLedger`;
- `EvidenceAppendPolicy::RejectAboveLevel1Actual`.

The current tiny-Z3 accepted-path class and boundary pair is:

```text
accepted evidence class: LocalReplay
accepted claim boundary: Level1LocalReplay
maximum accepted append claim boundary: Level1LocalReplay
```

`DesignNote` and `Level0DesignNote` remain valid lower local metadata in the
current `zkbench-core` policy surface, but Phase 494 does not broaden the
tiny-Z3 accepted bridge around them.

The current rejected classes are:

```text
ReproducibleBenchmarkArtifact
CrossBackendReplay
FormalPropertyStatement
MachineCheckedScopedProof
IndependentlyReproducedEvidence
```

The current rejected claim-boundary floor for actual accepted evidence is:

```text
Level2ReproducibleBenchmarkArtifact or above
```

That means the current tiny-Z3 accepted bridge can only target local replay at
the Level1 cap. It cannot carry accepted formal evidence, proof authority,
benchmark evidence, cross-backend replay evidence, or independent reproduction.

The source-grounded facts behind this boundary are:

- `EvidenceClass` and `ClaimBoundary` are defined by `zkbench-core` in
  `crates/zkbench-core/src/evidence/mod.rs`;
- `EvidenceAcceptancePolicy::phase_j_level1_local_only` allows only
  `Level0DesignNote` and `Level1LocalReplay` while keeping Level2+ and formal
  evidence disallowed;
- `build_evidence_record_candidate_from_reviewed_proposal` maps
  `Level1LocalReplay` to `EvidenceClass::LocalReplay`;
- `validate_accepted_ledger_append_transaction_request` caps accepted-ledger
  append requests at `Level1LocalReplay` and rejects Level2+/formal classes.

## HSAI Admission Role

`crates/hsai-agent-admission` may record local metadata that references the
class and claim-boundary envelope. It may not define a competing class
taxonomy, widen `zkbench-core` claim-boundary semantics, infer Level2+ or
formal evidence from local metadata, or use class/boundary metadata as
accepted evidence.

A future HSAI-to-accepted-append bridge may only satisfy this prerequisite if
it binds the exact evidence class and claim boundary that `zkbench-core` will
evaluate for the accepted-ledger append transaction. If a future value is
unknown, the future metadata must record it as unresolved instead of inventing
one.

## Required Future Bindings

A future implementation that tries to satisfy this gate must bind:

- one Phase 493 accepted append policy-version record digest;
- one Phase 493 accepted append policy-version input digest;
- the Phase 493 digest-binding map digest;
- the Phase 493 id-binding map digest;
- the Phase 493 label-binding map digest;
- the Phase 493 explicit nonclaim digest;
- current accepted append blocker digest;
- accepted append owner `zkbench-core`;
- local transaction route `AcceptedLedgerAppendTransactionRequest`;
- materialized route `MaterializedAcceptedLedgerAppendRequest`;
- evidence class owner `zkbench-core`;
- claim boundary owner `zkbench-core`;
- exact evidence class type `EvidenceClass`;
- exact claim boundary type `ClaimBoundary`;
- exact accepted evidence record type `EvidenceRecord`;
- exact candidate type `EvidenceRecordCandidate`;
- exact accepted evidence class `LocalReplay`;
- exact accepted claim boundary `Level1LocalReplay`;
- lower local metadata class `DesignNote`;
- lower local metadata boundary `Level0DesignNote`;
- exact maximum accepted append claim boundary `Level1LocalReplay`;
- exact rejected class set or explicit unresolved marker;
- exact rejected Level2+ boundary floor `Level2ReproducibleBenchmarkArtifact`;
- exact append policy `RejectAboveLevel1Actual`;
- exact rejection policy for Level2+, cross-backend replay, formal property,
  machine-checked proof, independent reproduction, score-axis, benchmark, and
  strong public-claim attempts.

## Required Future Validation

A future validator must reject the class/boundary gate input if:

- the schema version is not the future Phase 495 schema;
- the Phase 493 policy-version digest or input digest drifts;
- the Phase 493 digest/id/label map digests drift;
- the Phase 493 explicit nonclaim digest drifts;
- the current accepted append blocker digest drifts;
- the accepted append owner is not `zkbench-core`;
- the local transaction route is not `AcceptedLedgerAppendTransactionRequest`;
- the materialized route is not `MaterializedAcceptedLedgerAppendRequest`;
- the evidence class owner is not `zkbench-core`;
- the claim boundary owner is not `zkbench-core`;
- the evidence class type is not `EvidenceClass`;
- the claim boundary type is not `ClaimBoundary`;
- the accepted evidence record type is not `EvidenceRecord`;
- the candidate type is not `EvidenceRecordCandidate`;
- the accepted evidence class is not `LocalReplay`;
- the accepted claim boundary is not `Level1LocalReplay`;
- lower local metadata handling treats `DesignNote` or `Level0DesignNote` as
  accepted bridge authority;
- the maximum accepted append claim boundary is above `Level1LocalReplay`;
- the rejected class set omits `ReproducibleBenchmarkArtifact`,
  `CrossBackendReplay`, `FormalPropertyStatement`,
  `MachineCheckedScopedProof`, or `IndependentlyReproducedEvidence`;
- the rejected Level2+ boundary floor is not
  `Level2ReproducibleBenchmarkArtifact`;
- the append policy is not `RejectAboveLevel1Actual`;
- the metadata tries to change accepted append policy;
- the metadata tries to create an accepted append decision;
- the metadata tries to mutate the accepted Evidence Ledger;
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

The future class/boundary gate record may support this claim only:

```text
HSAI locally records the accepted evidence class and claim-boundary pair that a
future accepted append bridge must bind before it can ask zkbench-core to
evaluate an accepted-ledger append transaction.
```

That still is not:

- accepted append;
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

## Phase 495 Implementation Exit Criteria

Phase 495 may implement local accepted evidence class and claim-boundary
metadata only if it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds the Phase 493 policy-version digest and input digest;
- binds the Phase 493 digest/id/label map digests;
- binds the Phase 493 explicit nonclaim digest;
- identifies `zkbench-core` as the only accepted append, evidence class, and
  claim boundary owner;
- identifies `EvidenceClass` as the evidence class type;
- identifies `ClaimBoundary` as the claim boundary type;
- identifies `EvidenceRecord` as the accepted evidence record type;
- identifies `EvidenceRecordCandidate` as the candidate type;
- identifies `LocalReplay` as the accepted evidence class;
- identifies `Level1LocalReplay` as the accepted claim boundary;
- identifies `DesignNote` and `Level0DesignNote` as lower local metadata only;
- identifies `Level1LocalReplay` as the maximum accepted append claim boundary;
- identifies the rejected Level2+, formal, proof, cross-backend, and
  independent-reproduction class set;
- identifies `RejectAboveLevel1Actual` as the current append policy;
- records unknown future bridge inputs as unresolved;
- rejects accepted append policy changes in the gate metadata itself;
- rejects accepted append decisions in the gate metadata itself;
- rejects accepted Evidence Ledger mutation in the gate metadata itself;
- rejects accepted formal evidence creation in the gate metadata itself;
- rejects Level2+ evidence creation in the gate metadata itself;
- rejects score-axis population in the gate metadata itself;
- rejects proof/checker/solver authority creation in the gate metadata itself;
- rejects Lean/new-SMT/COBALT/Rust-to-Lean execution evidence creation in the
  gate metadata itself;
- rejects benchmark evidence creation in the gate metadata itself;
- rejects SOTA, semantic-correctness, production-readiness, full-security,
  breakthrough, and action-authority claims in the gate metadata itself.
