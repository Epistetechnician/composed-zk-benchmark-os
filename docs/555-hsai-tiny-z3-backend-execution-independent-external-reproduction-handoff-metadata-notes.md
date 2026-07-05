# Phase 555 HSAI Tiny Z3 Backend Execution Independent External Reproduction Handoff Metadata Notes

State slice: `Phase 555 HSAI tiny Z3 backend execution independent external reproduction handoff metadata`.

Phase 555 implements the local handoff metadata path authorized by
`docs/554-hsai-tiny-z3-backend-execution-independent-external-reproduction-handoff-boundary.md`:

```text
Phase 553 blocked import-review metadata
  + zkbench-core ManualHandoffBundle validation
  -> local independent external-reproduction handoff metadata
```

This phase is pure metadata. It does not write handoff bundle files, write
external-result artifacts, write external-reproduction artifacts, write
accepted-evidence artifacts, write Level2 artifacts, write score-axis
artifacts, populate score axes, add a dependency, add a binary, add a script,
spawn a process, call the network, read credentials, run a solver, run a proof
assistant, run a benchmark, or create proof/checker/solver artifacts.

## Implemented Surface

Phase 555 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3BackendExecutionExternalReproductionHandoffInput`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionHandoff`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionHandoffClassification`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionHandoffLabel`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionHandoffIssue`;
- `GatewayFormalTinyZ3BackendExecutionExternalReproductionHandoffValidation`;
- deterministic blocker, nonclaim, rule, forbidden-API, inherited-digest,
  output-role, quarantine-requirement, nonpromotion-digest, policy-digest,
  digest-binding, id-binding, and label-binding helpers;
- `gateway_formal_tiny_z3_backend_execution_external_reproduction_manual_handoff_bundle`;
- `validate_gateway_formal_tiny_z3_backend_execution_external_reproduction_handoff_input`;
- `build_gateway_formal_tiny_z3_backend_execution_external_reproduction_handoff`.

The builder validates one exact Phase 553 import-review metadata record,
constructs one in-memory `zkbench_core::ManualHandoffBundle`, calls
`zkbench_core::validate_manual_handoff_bundle`, and records local handoff
metadata only. Under current evidence the only valid classification is
`IndependentExternalReproductionHandoffDeclaredNoRun`.

## Binding Surface

The implementation binds:

- the Phase 553 import-review digest and input digest;
- the Phase 553 classification
  `BackendExecutionImportReviewBlockedNoIndependentRun`;
- the Phase 553 review blocker, policy, and nonpromotion digests;
- the Phase 551 import-candidate digest and input digest;
- the Phase 551 classification `ImportCandidateQuarantinedLocalMetadata`;
- the Phase 551 candidate, validation, validation-issue, and quarantine-record
  digests;
- Phase 551 status `Quarantined`;
- Phase 551 requested claim boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 549 external-reproduction digest and classification
  `ExternalReproductionBlockedNoIndependentRun`;
- the Phase 547 Level2 eligibility digest and classification
  `Level2BlockedLocalOnly`;
- the Phase 545 score-axis eligibility and nonpopulation digests;
- the Phase 543 package digest, evidence class `LocalReplay`, and claim
  boundary `Level1LocalReplay`;
- the Phase 541 materialized ledger artifact digest;
- inherited Phase 535 owner-decision, Phase 533 review, Phase 531 package,
  Phase 529 backend execution result, and Phase 527 candidate digests;
- owner id `zkbench-core`;
- bundle type `ManualHandoffBundle`;
- validator id `validate_manual_handoff_bundle`;
- handoff bundle, handoff validation, and validation-issue digests;
- `ClaimBoundary::Level0DesignNote` for the handoff bundle;
- required operator output roles;
- `zkbench-core` required provenance fields;
- result-import quarantine requirements;
- handoff policy, blocker, and nonpromotion digests.

## Guardrails

Phase 555 fails closed if the Phase 553 record is not exact, if the Phase 553
classification is not `BackendExecutionImportReviewBlockedNoIndependentRun`,
if the Phase 551 candidate is not exact, valid, and quarantined, if Phase 549
is not blocked for missing independent external reproduction, if inherited
Phase 547/545/543/541/535/533/531/529/527 bindings drift, if the
`ManualHandoffBundle` digest or validation digest drifts, if
`validate_manual_handoff_bundle` reports any issue, if manual handoff steps are
not manual-only, or if the bundle boundary rises above
`ClaimBoundary::Level0DesignNote`.

It also rejects process execution, network access, credentials, external
replay, external result import, external-result artifact writes, accepted
external-result evidence, accepted-evidence artifact writes, independent
external reproduction, Level2 artifacts, score-axis artifacts, score-axis
population, accepted formal evidence, Level2+ evidence, proof/checker/solver
promotion, Lean/COBALT/Rust-to-Lean evidence, additional SMT/Z3 execution,
backend execution evidence, benchmark evidence, external audit evidence,
strong claims, and action authority.

## Evidence Meaning

Phase 555 supports this claim only:

```text
HSAI can prepare a digest-bound manual handoff request for independent
external reproduction of the backend-execution route.
```

The result is still not independent external reproduction, not external result
import, not accepted formal evidence, not Level2+ evidence, not score-axis
evidence, not populated score axes, not Lean proof, not SMT proof authority,
not COBALT containment evidence, not Rust-to-Lean proof, not checker
transcript authority, not solver certificate authority, not benchmark
evidence, not external audit, not SOTA, not semantic correctness, not
production readiness, not full security, and not authority to execute an
action.

## Tests

Focused tests cover:

- successful manual handoff metadata over a real Phase 553 blocked import
  review record;
- rejection when the Phase 553 state is invalid;
- rejection of handoff bundle digest drift and promotion attempts across
  process execution, network access, credentials, external replay, external
  result import, external-result artifact writes, accepted external-result
  evidence, accepted-evidence artifact writes, independent external
  reproduction, Level2 artifacts, score-axis artifacts, axis population,
  accepted formal evidence, Level2+, Lean, COBALT, Rust-to-Lean, additional
  SMT/Z3 execution, backend execution evidence, proof/checker/solver,
  benchmark, external audit, strong claims, and action authority.

## Next Boundary

The next responsible boundary is the materialized handoff packet boundary: a
docs-first contract for writing the already validated manual handoff metadata
to a declared local output namespace without executing it or importing results.
Until a separate operator run and import-review path exists, there is no
independent external reproduction and no Level2+ evidence.
