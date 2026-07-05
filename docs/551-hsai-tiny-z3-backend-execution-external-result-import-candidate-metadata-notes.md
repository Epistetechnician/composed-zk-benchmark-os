# Phase 551 HSAI Tiny Z3 Backend Execution External Result Import Candidate Metadata Notes

State slice: `Phase 551 HSAI tiny Z3 backend execution external result import candidate metadata`.

Phase 551 implements the local external-result import candidate metadata path
authorized by
`docs/550-hsai-tiny-z3-backend-execution-external-result-import-candidate-boundary.md`:

```text
Phase 549 backend-execution external-reproduction metadata
  + zkbench-core ExternalResultCandidate validation
  -> local external-result import candidate metadata
```

This phase is pure metadata. It does not write external-result artifact files,
write external-reproduction artifact files, write Level2 artifact files, write
score-axis artifact files, populate score axes, add a dependency, add a binary,
add a script, spawn a process, call the network, run a solver, run a proof
assistant, run a benchmark, or create proof/checker/solver artifacts.

## Implemented Surface

Phase 551 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3BackendExecutionExternalImportCandidateInput`;
- `GatewayFormalTinyZ3BackendExecutionExternalImportCandidate`;
- `GatewayFormalTinyZ3BackendExecutionExternalImportCandidateClassification`;
- `GatewayFormalTinyZ3BackendExecutionExternalImportCandidateLabel`;
- `GatewayFormalTinyZ3BackendExecutionExternalImportCandidateIssue`;
- `GatewayFormalTinyZ3BackendExecutionExternalImportCandidateValidation`;
- deterministic blocker, nonclaim, rule, forbidden-API, inherited-digest,
  candidate, nonpromotion-digest, policy-digest, digest-binding, id-binding,
  and label-binding helpers;
- `validate_gateway_formal_tiny_z3_backend_execution_external_import_candidate_input`;
- `build_gateway_formal_tiny_z3_backend_execution_external_import_candidate`.

The builder validates one exact Phase 549 external-reproduction metadata
record, constructs one in-memory `zkbench_core::ExternalResultCandidate`, calls
`validate_external_result_candidate`, calls
`external_result_quarantine_record`, and records local quarantined import
candidate metadata only.

## Binding Surface

The implementation binds:

- the Phase 549 external-reproduction digest and input digest;
- the Phase 549 digest, id, and label binding map digests;
- the Phase 549 classification `ExternalReproductionBlockedNoIndependentRun`;
- the Phase 549 reproduction blocker digest;
- the Phase 549 reproduction nonpromotion digest;
- the Phase 549 reproduction input-status digest;
- the Phase 547 Level2 eligibility digest;
- the Phase 547 classification `Level2BlockedLocalOnly`;
- the Phase 547 report claim boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 547 `report_creates_level2_evidence=false` invariant;
- the Phase 545 score-axis eligibility digest;
- the Phase 545 score-axis nonpopulation digest;
- the Phase 543 package digest;
- the Phase 543 evidence class `LocalReplay`;
- the Phase 543 claim boundary `Level1LocalReplay`;
- the Phase 541 materialized ledger artifact digest;
- the inherited Phase 535 owner-decision digest;
- the inherited Phase 533 review digest;
- the inherited Phase 531 package digest;
- the inherited Phase 529 backend execution result digest;
- the inherited Phase 527 candidate digest;
- external owner id `zkbench-core`;
- candidate type `ExternalResultCandidate`;
- validator id `validate_external_result_candidate`;
- quarantine type `ExternalResultQuarantineRecord`;
- quarantine function `external_result_quarantine_record`;
- requested claim boundary `ClaimBoundary::Level0DesignNote`;
- candidate status `Quarantined`;
- candidate, validation, validation-issue, and quarantine-record digests;
- import policy, blocker, and nonpromotion digests.

## Guardrails

Phase 551 fails closed if the Phase 549 record is not exact, if the Phase 549
classification is not `ExternalReproductionBlockedNoIndependentRun`, if any
Phase 549 external-reproduction input is marked present, if the Phase 547
Level2 record is not exact, if the Phase 547 report boundary is not
`ClaimBoundary::Level0DesignNote`, if Phase 547 creates Level2 evidence, if the
Phase 545 score-axis record has populated axes, if the Phase 543 package is not
`LocalReplay` with `Level1LocalReplay`, if inherited Phase
541/535/533/531/529/527 bindings are missing, or if the source metadata
promoted accepted formal evidence, Level2+ evidence, score axes, proof,
checker, solver, Lean, SMT, COBALT, Rust-to-Lean, benchmark, audit,
semantic-correctness, production-readiness, SOTA, breakthrough, full-security,
or action-authority claims.

It also rejects import owner/type/function drift, candidate status drift,
requested claim-boundary drift, candidate/validation/quarantine digest drift,
invalid candidate validation, non-quarantined status, import blocker/policy/
nonpromotion drift, external-result artifact writes, independent external
reproduction, accepted formal evidence, Level2+ evidence, proof/checker/solver
promotion, Lean/COBALT/Rust-to-Lean evidence, additional SMT/Z3 execution,
backend execution evidence, benchmark evidence, external-audit evidence,
strong claims, and action authority.

## Evidence Meaning

Phase 551 supports this claim only:

```text
HSAI can construct and validate a quarantined local external-result import
candidate for the backend-execution route while preserving that no independent
external reproduction has occurred.
```

The result is still not independent external reproduction, not accepted formal
evidence, not Level2+ evidence, not score-axis evidence, not populated score
axes, not Lean proof, not SMT proof authority, not COBALT containment evidence,
not Rust-to-Lean proof, not checker transcript authority, not solver
certificate authority, not benchmark evidence, not external audit, not SOTA,
not semantic correctness, not production readiness, not full security, and not
authority to execute an action.

## Tests

Focused tests cover:

- successful quarantined import candidate metadata over a real Phase 549
  external-reproduction metadata record;
- rejection when the Phase 549 state is invalid;
- rejection of candidate digest drift, external-result artifact writes,
  independent external reproduction, Level2 artifact writes, score-axis
  artifact writes, score-axis population, accepted formal evidence, Level2+,
  proof/checker/solver, Lean, COBALT, Rust-to-Lean, additional SMT/Z3
  execution, backend execution evidence, benchmark, external-audit,
  strong-claim, and action-authority promotion attempts.

The tests assert that the import candidate remains local metadata, records
classification `ImportCandidateQuarantinedLocalMetadata`, validates cleanly via
`zkbench-core`, records quarantine status `Quarantined`, requests
`ClaimBoundary::Level0DesignNote`, and creates no independent external
reproduction, formal evidence, Level2+ evidence, benchmark evidence, external
audit evidence, or action authority.

## Next Boundary

The next responsible boundary is backend-execution external import review over
the Phase 551 quarantined import candidate. Until that separate boundary and
implementation exist, there is no independent external reproduction and no
Level2+ evidence.
