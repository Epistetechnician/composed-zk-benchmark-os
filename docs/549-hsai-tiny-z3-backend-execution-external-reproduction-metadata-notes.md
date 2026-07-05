# Phase 549 HSAI Tiny Z3 Backend Execution External Reproduction Metadata Notes

State slice: `Phase 549 HSAI tiny Z3 backend execution external reproduction metadata`.

Phase 549 implements the local external-reproduction metadata path authorized
by
`docs/548-hsai-tiny-z3-backend-execution-external-reproduction-boundary.md`:

```text
Phase 547 backend-execution Level2 eligibility metadata
  + external reproduction provenance policy
  -> local external-reproduction metadata
```

This phase is pure metadata. It does not write external-reproduction artifact
files, write Level2 artifact files, write score-axis artifact files, populate
score axes, add a dependency, add a binary, add a script, spawn a process, call
the network, run a solver, run a proof assistant, run a benchmark, or create
proof/checker/solver artifacts.

## Implemented Surface

Phase 549 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3BackendExecutionExternalReproductionInput`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproduction`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionClassification`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionLabel`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionIssue`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionValidation`;
- deterministic missing-input, blocker, nonclaim, rule, forbidden-API,
  inherited-digest, nonpromotion-digest, policy-digest, digest-binding,
  id-binding, and label-binding helpers;
- `validate_gateway_formal_tiny_z3_backend_execution_external_reproduction_input`;
- `build_gateway_formal_tiny_z3_backend_execution_external_reproduction`.

The builder validates one exact Phase 547 Level2 eligibility metadata record,
then records local external-reproduction metadata only.

## Binding Surface

The implementation binds:

- the Phase 547 Level2 eligibility digest and input digest;
- the Phase 547 digest, id, and label binding map digests;
- the Phase 547 classification `Level2BlockedLocalOnly`;
- the Phase 547 Level2 blocker digest;
- the Phase 547 Level2 nonpromotion digest;
- the Phase 547 report claim boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 547 `report_creates_level2_evidence=false` invariant;
- the Phase 545 score-axis eligibility digest;
- the Phase 545 score-axis nonpopulation digest;
- the Phase 543 package digest;
- the Phase 543 evidence class `LocalReplay`;
- the Phase 543 claim boundary `Level1LocalReplay`;
- the Phase 541 materialized ledger artifact digest;
- the Phase 539 appended evidence class and claim boundary;
- the inherited Phase 535 owner-decision digest;
- the inherited Phase 533 review digest;
- the inherited Phase 531 package digest;
- the inherited Phase 529 backend execution result digest;
- the inherited Phase 527 candidate digest;
- external owner id `zkbench-core`;
- artifact-capture contract type `ArtifactCaptureContract`;
- provenance contract type `ProvenanceContract`;
- external-result import schema type `ExternalResultImportSchema`;
- external-result candidate type `ExternalResultCandidate`;
- external-result quarantine type `ExternalResultQuarantineRecord`;
- artifact-capture, provenance, import-schema, and required-provenance-field
  digests;
- external-reproduction input-status digest;
- external-reproduction policy digest;
- external-reproduction blocker digest;
- external-reproduction nonpromotion digest.

## Guardrails

Phase 549 fails closed if the Phase 547 record is not exact, if the Phase 547
classification is not `Level2BlockedLocalOnly`, if the Phase 547 report claim
boundary is not `ClaimBoundary::Level0DesignNote`, if the Phase 547 report or
wrapper creates Level2 evidence, if the Phase 545 source is not
`ScoreAxesBlockedLocalOnly`, if the Phase 543 package is not `LocalReplay`
with `Level1LocalReplay`, if inherited Phase 541/539/535/533/531/529/527
bindings are missing, or if the source metadata promoted accepted formal
evidence, Level2+ evidence, score axes, proof, checker, solver, Lean, SMT,
COBALT, Rust-to-Lean, benchmark, audit, independent-reproduction,
semantic-correctness, production-readiness, SOTA, breakthrough,
full-security, or action-authority claims.

It also rejects external owner/type drift, artifact-capture/provenance/
import-schema/required-provenance-field digest drift, any classification other
than `ExternalReproductionBlockedNoIndependentRun`, any external-reproduction
input claimed present, missing or drifted blocker/nonpromotion/policy digests,
external-reproduction artifact writes, external replay claims, accepted formal
evidence, Level2+ evidence, proof/checker/solver promotion, Lean/COBALT/
Rust-to-Lean evidence, additional SMT/Z3 execution, benchmark evidence,
external-audit evidence, strong claims, and action authority.

## Evidence Meaning

Phase 549 supports this claim only:

```text
HSAI records that the local Phase 547 backend-execution route still lacks
independent external reproduction and remains blocked under current evidence.
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

- successful external-reproduction metadata over a real Phase 547 Level2
  eligibility metadata record;
- rejection when the Phase 547 state is invalid;
- rejection of fabricated independent external reproduction,
  external-reproduction artifact writes, Level2 artifact writes, score-axis
  artifact writes, score-axis population, accepted formal evidence, Level2+,
  proof/checker/solver, Lean, COBALT, Rust-to-Lean, additional SMT/Z3
  execution, benchmark, external-audit, strong-claim, and action-authority
  promotion attempts.

The tests assert that the metadata record remains local, records
classification `ExternalReproductionBlockedNoIndependentRun`, records every
external-reproduction input as missing, binds `zkbench-core` external owner
contracts, and creates no independent external reproduction, formal evidence,
Level2+ evidence, benchmark evidence, external audit evidence, or action
authority.

## Next Boundary

The next responsible boundary is external-result import candidate preparation
or accepted formal policy gating over the Phase 549 blocked-reproduction
record. Until that separate boundary and implementation exist, there is no
independent external reproduction and no Level2+ evidence.
