# Phase 550 HSAI Tiny Z3 Backend Execution External Result Import Candidate Boundary

State slice: `Phase 550 HSAI tiny Z3 backend execution external result import candidate boundary`.

Phase 550 defines the docs-first boundary for future external-result import
candidate metadata over the Phase 549 backend-execution external-reproduction
metadata record:

```text
Phase 549 backend-execution external-reproduction metadata
  + zkbench-core ExternalResultCandidate validation
  -> future local external-result import candidate metadata
```

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, run an external replay, run a backend, run Lean, run
SMT/Z3, run COBALT, run Rust-to-Lean extraction, create proof artifacts,
create checker transcripts, create solver certificates, mutate the accepted
Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, claim external audit status, claim
independent external reproduction, or grant authority to execute an action.

## Existing Import Owner Surface

The existing owner surface is `zkbench-core`:

- `ExternalResultCandidate`;
- `ExternalRunProvenanceDraft`;
- `ExternalResultStatus`;
- `ExternalMetricCandidate`;
- `ExternalMetricUnit`;
- `validate_external_result_candidate`;
- `external_result_quarantine_record`;
- `ExternalResultValidation`;
- `ExternalResultQuarantineRecord`;
- `ClaimBoundary::Level0DesignNote`.

These APIs can validate an in-memory external-result candidate and produce a
quarantine summary. They do not, by themselves, prove external reproduction,
create accepted evidence, create Level2+ evidence, populate score axes, or
establish semantic correctness.

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
binaries, scripts, process-spawn APIs, network APIs, official submission APIs,
solver APIs, proof-assistant APIs, benchmark runners, external replay runners,
score-axis writers, accepted-ledger writers, or filesystem output writers.

## Future Metadata Meaning

A future HSAI backend-execution external-result import candidate record may
classify one Phase 549 record as:

- `import_candidate_quarantined_local_metadata`;
- `import_candidate_invalid`;
- `import_candidate_waiting_for_independent_external_run`;
- `import_candidate_waiting_for_operator_review`;
- `import_candidate_ready_for_future_review_only`.

Under current evidence, the only valid HSAI classification is:

```text
import_candidate_quarantined_local_metadata
```

That classification may record an in-memory candidate validated by
`zkbench-core`, but it must preserve the Phase 549 fact that independent
external reproduction is still missing.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 549 external-reproduction metadata digest;
- one Phase 549 external-reproduction input digest;
- the Phase 549 digest-binding map digest;
- the Phase 549 id-binding map digest;
- the Phase 549 label-binding map digest;
- the Phase 549 classification
  `ExternalReproductionBlockedNoIndependentRun`;
- the Phase 549 reproduction blocker digest;
- the Phase 549 reproduction nonpromotion digest;
- the Phase 549 reproduction input-status digest;
- the Phase 549 external owner and contract digests;
- the Phase 547 Level2 eligibility digest;
- the Phase 547 classification `Level2BlockedLocalOnly`;
- the Phase 547 report claim boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 547 `creates_level2_evidence=false` invariant;
- the Phase 545 score-axis eligibility digest;
- the Phase 545 score-axis nonpopulation digest;
- the Phase 543 package digest;
- the Phase 543 evidence class `LocalReplay`;
- the Phase 543 claim boundary `Level1LocalReplay`;
- the Phase 541 materialized ledger artifact digest;
- the inherited Phase 535/533/531/529/527 digest set;
- the import owner id `zkbench-core`;
- candidate type `ExternalResultCandidate`;
- provenance draft type `ExternalRunProvenanceDraft`;
- validation function `validate_external_result_candidate`;
- quarantine function `external_result_quarantine_record`;
- candidate digest;
- validation result digest;
- validation issue digest;
- quarantine record digest;
- candidate status `Quarantined`;
- requested claim boundary `ClaimBoundary::Level0DesignNote`;
- explicit flags that official benchmark evidence, formal evidence, proof
  soundness, independent external reproduction, Level2+ evidence, and score
  axes are not claimed.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 549 record is not exact;
- the Phase 549 classification is not
  `ExternalReproductionBlockedNoIndependentRun`;
- any Phase 549 external-reproduction input is marked present;
- the Phase 547 Level2 record is not exact;
- the Phase 547 report boundary is not `ClaimBoundary::Level0DesignNote`;
- Phase 547 creates Level2 evidence;
- the Phase 545 score-axis record is not exact or has populated axes;
- the Phase 543 package record is not `LocalReplay` / `Level1LocalReplay`;
- inherited Phase 541/539/535/533/531/529/527 bindings are missing or zero;
- the import owner is not `zkbench-core`;
- the candidate status is not `Quarantined`;
- the candidate claim boundary is not `ClaimBoundary::Level0DesignNote`;
- `validate_external_result_candidate` reports invalid;
- the quarantine record status is not `Quarantined`;
- the candidate claims official benchmark evidence, formal evidence, proof
  soundness, Level2+ evidence, populated score axes, independent external
  reproduction, external audit, semantic correctness, production readiness,
  SOTA, breakthrough status, full security, or action authority;
- the candidate records Lean, COBALT, Rust-to-Lean, or additional SMT/Z3
  evidence as present.

## Backend Relationship

This boundary is not a new backend run, not an external reproduction, and not a
benchmark submission. It may only authorize an in-memory validation path for a
quarantined local candidate that keeps independent reproduction absent.

If a future import-candidate record succeeds under current evidence, it may
support this claim only:

```text
HSAI can construct and validate a quarantined local external-result import
candidate for the backend-execution route while preserving that no independent
external reproduction has occurred.
```

That still would not be independent external reproduction, Level2+ evidence,
accepted formal evidence, score-axis evidence, Lean proof, SMT proof authority,
COBALT containment evidence, Rust-to-Lean proof, checker transcript authority,
solver certificate authority, benchmark evidence, external audit, SOTA,
semantic correctness, production readiness, full security, or authority to
execute an action.

## Phase 551 Implementation Exit Criteria

A future Phase 551 may implement local external-result import candidate
metadata only if it:

- touches only the allowed files listed above;
- performs no process or network calls;
- writes no external-result artifact files;
- writes no external-reproduction artifact files;
- writes no Level2 artifact files;
- writes no score-axis artifact files;
- validates one exact Phase 549 external-reproduction metadata record;
- constructs one in-memory `zkbench-core::ExternalResultCandidate`;
- calls `validate_external_result_candidate`;
- calls `external_result_quarantine_record`;
- records `Quarantined` status;
- records `ClaimBoundary::Level0DesignNote`;
- rejects independent external reproduction, accepted formal evidence, Level2+
  evidence, populated score axes, proof/checker/solver authority, Lean/SMT/
  COBALT/Rust-to-Lean evidence, benchmark evidence, external audit, strong
  claims, and action authority in the metadata itself.
