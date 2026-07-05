# Phase 521 HSAI Tiny Z3 External Reproduction Provenance Metadata Notes

State slice: `Phase 521 HSAI tiny Z3 external reproduction provenance metadata`.

Phase 521 implements the local external-reproduction provenance metadata path
authorized by
`docs/520-hsai-tiny-z3-external-reproduction-provenance-boundary.md`:

```text
Phase 519 Level2 eligibility metadata
  + zkbench-core artifact capture / provenance / external result import contracts
  -> local external-reproduction provenance metadata
```

This phase is pure metadata. It does not write external-reproduction artifact
files, write Level2 artifact files, write score-axis artifact files, populate
score axes, add a dependency, add a binary, add a script, spawn a process, call
the network, run a solver, run a proof assistant, run a benchmark, or create
proof/checker/solver artifacts.

## Implemented Surface

Phase 521 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3ExternalReproductionInput`;
- `GatewayFormalTinyZ3ExternalReproduction`;
- `GatewayFormalTinyZ3ExternalReproductionClassification`;
- `GatewayFormalTinyZ3ExternalReproductionLabel`;
- `GatewayFormalTinyZ3ExternalReproductionIssue`;
- `GatewayFormalTinyZ3ExternalReproductionValidation`;
- deterministic missing-input, blocker, nonclaim, rule, forbidden-API,
  inherited-digest, contract-digest, nonpromotion, policy-digest,
  digest-binding, id-binding, and label-binding helpers;
- `validate_gateway_formal_tiny_z3_external_reproduction_input`;
- `build_gateway_formal_tiny_z3_external_reproduction`.

The builder validates one exact Phase 519 Level2 eligibility metadata record,
then records local external-reproduction provenance metadata only. It binds:

- the Phase 519 Level2 eligibility digest and input digest;
- the Phase 519 digest, id, and label binding map digests;
- the Phase 519 classification `level2_blocked_local_only`;
- the Phase 519 Level2 blocker digest;
- the Phase 519 Level2 nonpromotion digest;
- the Phase 517 score-axis eligibility digest;
- the Phase 517 score-axis nonpopulation digest;
- the Phase 515 package digest;
- the Phase 515 evidence class `LocalReplay`;
- the Phase 515 claim boundary `Level1LocalReplay`;
- the Phase 513 materialized ledger artifact digest;
- external owner id `zkbench-core`;
- default `ArtifactCaptureContract` digest;
- default `ProvenanceContract` digest;
- default `ExternalResultImportSchema` digest;
- required provenance-field digest;
- external-reproduction blocker digest;
- external-reproduction nonpromotion digest.

## Guardrails

Phase 521 fails closed if the Phase 519 record is not exact, if the Phase 519
classification is not `level2_blocked_local_only`, if the Phase 519 report
boundary is not `ClaimBoundary::Level0DesignNote`, if Phase 519 creates Level2
evidence, if Phase 517 score axes are populated, if Phase 515 evidence is not
`LocalReplay` / `Level1LocalReplay`, if external owner/type identifiers drift,
if default `zkbench-core` contract digests drift, if required provenance fields
drift, if the classification is not
`external_reproduction_blocked_no_independent_run`, or if any
external-reproduction input is marked present without a future explicit digest
boundary.

It also rejects external-reproduction artifact writes, independent external
reproduction claims, Level2 artifact writes, score-axis artifact writes,
score-axis population, accepted formal evidence, Level2+ evidence,
proof/checker/solver promotion, backend execution evidence, benchmark
evidence, external-audit evidence, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, and action authority.

## Evidence Meaning

Phase 521 supports this claim only:

```text
HSAI records that the local tiny-Z3 package still lacks independent external
reproduction and identifies the artifact-capture, provenance, and import
validation contracts required before future human Level2 review.
```

The result is still not independent external reproduction, not Level2+
evidence, not accepted formal evidence, not score-axis evidence, not Lean
proof, not SMT proof authority, not COBALT containment evidence, not
Rust-to-Lean proof, not checker transcript authority, not solver certificate
authority, not benchmark evidence, not external audit, not SOTA, not semantic
correctness, not production readiness, not full security, and not authority to
execute an action.

## Tests

Focused tests cover:

- successful external-reproduction provenance metadata over a real Phase 519
  Level2 eligibility metadata record;
- rejection when the Phase 519 state is invalid;
- rejection of fabricated independent external reproduction, external
  reproduction artifact writes, Level2 artifact writes, score-axis artifact
  writes, score-axis population, formal-evidence, Level2+,
  proof/checker/solver, backend, benchmark, external-audit, strong-claim, and
  action-authority promotion attempts.

The tests assert that the metadata remains local, records classification
`external_reproduction_blocked_no_independent_run`, binds the exact default
`zkbench-core` contract digests, records every external-reproduction input as
missing, and creates no independent external reproduction, formal evidence,
Level2+ evidence, score-axis evidence, backend execution evidence, benchmark
evidence, external audit evidence, or action authority.
