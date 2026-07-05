# Phase 548 HSAI Tiny Z3 Backend Execution External Reproduction Boundary

State slice: `Phase 548 HSAI tiny Z3 backend execution external reproduction boundary`.

Phase 548 defines the docs-first boundary for future external-reproduction
metadata over the Phase 547 backend-execution Level2 eligibility record:

```text
Phase 547 backend-execution Level2 eligibility metadata
  + external reproduction provenance policy
  -> future local external-reproduction metadata
```

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, run a backend, run an external replay, run Lean, run
SMT/Z3, run COBALT, run Rust-to-Lean extraction, create proof artifacts,
create checker transcripts, create solver certificates, mutate the accepted
Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, claim external audit status, claim
independent external reproduction, or grant authority to execute an action.

## Existing Owner Surface

The current `zkbench-core` external-run and provenance owner surface includes:

- `ArtifactCaptureContract`;
- `ProvenanceContract`;
- `ExternalResultImportSchema`;
- `ExternalResultCandidate`;
- `ExternalResultQuarantine`;
- required provenance fields;
- external result import validation and quarantine flow.

Those contracts can describe the shape of future externally produced evidence.
They do not prove independent reproduction by themselves. A future HSAI record
may cite these owners only as local policy metadata unless an actual external
run, artifact capture, provenance review, and import validation are present and
bound by digest.

## Future Allowed Touch Surface

A future implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

This boundary does not authorize new dependencies, Cargo metadata edits,
binaries, scripts, filesystem artifact writes, process-spawn APIs, network
APIs, official submission APIs, solver APIs, proof-assistant APIs, benchmark
runners, external replay runners, or score-axis writers.

## Future Classification Meaning

A future HSAI backend-execution external reproduction record may classify one
Phase 547 record as:

- `external_reproduction_blocked_no_independent_run`;
- `external_reproduction_waiting_for_artifact_capture`;
- `external_reproduction_waiting_for_provenance_review`;
- `external_reproduction_waiting_for_external_result_import_validation`;
- `external_reproduction_ready_for_future_human_review_only`.

Under current evidence, the only valid HSAI classification is:

```text
external_reproduction_blocked_no_independent_run
```

The classification must not be represented as independent external
reproduction, Level2+ evidence, accepted formal evidence, score-axis evidence,
proof authority, benchmark evidence, external audit evidence, or SOTA
evidence.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 547 Level2 eligibility digest;
- one Phase 547 Level2 eligibility input digest;
- the Phase 547 digest-binding map digest;
- the Phase 547 id-binding map digest;
- the Phase 547 label-binding map digest;
- the Phase 547 classification `Level2BlockedLocalOnly`;
- the Phase 547 Level2 blocker digest;
- the Phase 547 Level2 nonpromotion digest;
- the Phase 547 report claim boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 547 `creates_level2_evidence=false` invariant;
- the Phase 545 score-axis eligibility digest;
- the Phase 545 score-axis nonpopulation digest;
- the Phase 543 package digest;
- the Phase 543 evidence class `LocalReplay`;
- the Phase 543 claim boundary `Level1LocalReplay`;
- the Phase 541 materialized ledger artifact digest;
- the Phase 539 appended evidence class and claim boundary;
- the inherited Phase 535/533/531/529/527 digest set;
- external owner id `zkbench-core`;
- artifact-capture contract type and digest;
- provenance contract type and digest;
- external-result import schema type and digest;
- external-result candidate type;
- external-result quarantine type;
- required provenance-field digest;
- external-reproduction input-status digest;
- external-reproduction policy digest;
- external-reproduction blocker digest;
- external-reproduction nonpromotion digest.

The required input-status map must record these missing inputs under current
evidence:

- independent external run;
- artifact capture review;
- provenance review;
- external result import validation;
- replay manifest review;
- external reproduction human review.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 547 record is not exact;
- the Phase 547 classification is not `Level2BlockedLocalOnly`;
- the Phase 547 report claim boundary is not `ClaimBoundary::Level0DesignNote`;
- the Phase 547 report or wrapper sets `creates_level2_evidence=true`;
- the Phase 545 score-axis eligibility record is not exact;
- any Phase 545 score axis is populated;
- the Phase 543 package record is not exact;
- the Phase 543 evidence class is not `LocalReplay`;
- the Phase 543 claim boundary is not `Level1LocalReplay`;
- inherited Phase 541/539/535/533/531/529/527 digest bindings are missing or
  zero;
- the external owner is not `zkbench-core`;
- artifact-capture, provenance, import-schema, required-provenance-field,
  input-status, blocker, nonpromotion, or policy digests drift;
- any external-reproduction input is claimed present without explicit digest
  evidence;
- external artifact files are written;
- external replay execution is requested;
- accepted formal evidence, Level2+ evidence, score-axis evidence, benchmark
  evidence, external audit evidence, proof authority, checker transcript
  authority, solver certificate authority, Lean evidence, SMT proof authority,
  COBALT evidence, or Rust-to-Lean proof is cited as present;
- the metadata claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, independent external reproduction, or
  action authority.

## Backend Relationship

This boundary is not a new backend run and not an external reproduction. Phase
529 already recorded one local hermetic SMT/Z3 backend execution observation,
Phase 541 materialized one local accepted-ledger artifact over the reviewed
route, Phase 543 packaged that artifact as local replay evidence, Phase 545
classified score axes as unpopulated and blocked, and Phase 547 classified the
route as Level2-blocked under current evidence.

This boundary does not authorize another Z3 run, Lean execution, COBALT
execution, Rust-to-Lean extraction, proof artifact generation, checker
transcript generation, solver certificate generation, benchmark submission,
external replay execution, or score-axis population.

If a future external-reproduction metadata record succeeds under current
evidence, it may support this claim only:

```text
HSAI records that the local backend-execution route still lacks independent
external reproduction and remains blocked pending external run, artifact
capture, provenance review, import validation, replay review, and human review.
```

That still would not be independent external reproduction, Level2+ evidence,
accepted formal evidence, score-axis evidence, Lean proof, SMT proof authority,
COBALT containment evidence, Rust-to-Lean proof, checker transcript authority,
solver certificate authority, benchmark evidence, external audit, SOTA,
semantic correctness, production readiness, full security, or authority to
execute an action.

## Phase 549 Implementation Exit Criteria

A future Phase 549 implementation satisfies this boundary only if it:

- touches only the allowed files listed above;
- performs no process or network calls;
- writes no external-reproduction, Level2, or score-axis artifact files;
- validates one exact Phase 547 Level2 eligibility metadata record;
- binds the `zkbench-core` external reproduction owner surface;
- records the current HSAI classification as
  `external_reproduction_blocked_no_independent_run`;
- records every external-reproduction input as missing under current evidence;
- rejects accepted formal evidence, Level2+ evidence, populated score axes,
  proof/checker/solver authority, Lean/SMT/COBALT/Rust-to-Lean evidence,
  benchmark evidence, external audit, independent external reproduction,
  strong claims, and action authority in the metadata itself.
