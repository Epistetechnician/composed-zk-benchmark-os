# Phase 519 HSAI Tiny Z3 Level2 Eligibility Metadata Notes

State slice: `Phase 519 HSAI tiny Z3 Level2 eligibility metadata`.

Phase 519 implements the local Level2 eligibility metadata path authorized by
`docs/518-hsai-tiny-z3-level2-evidence-eligibility-boundary.md`:

```text
Phase 517 score-axis eligibility metadata
  + zkbench-core Level2 eligibility owner invariants
  -> local Level2 eligibility metadata
```

This phase is pure metadata. It does not write Level2 artifact files, write
score-axis artifact files, populate score axes, add a dependency, add a binary,
add a script, spawn a process, call the network, run a solver, run a proof
assistant, run a benchmark, or create proof/checker/solver artifacts.

## Implemented Surface

Phase 519 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3Level2EligibilityInput`;
- `GatewayFormalTinyZ3Level2Eligibility`;
- `GatewayFormalTinyZ3Level2EligibilityClassification`;
- `GatewayFormalTinyZ3Level2EligibilityLabel`;
- `GatewayFormalTinyZ3Level2EligibilityIssue`;
- `GatewayFormalTinyZ3Level2EligibilityValidation`;
- deterministic blocker, nonclaim, rule, forbidden-API, inherited-digest,
  nonpromotion, policy-digest, digest-binding, id-binding, and label-binding
  helpers;
- `validate_gateway_formal_tiny_z3_level2_eligibility_input`;
- `build_gateway_formal_tiny_z3_level2_eligibility`.

The builder validates one exact Phase 517 score-axis eligibility metadata
record, then records local Level2 eligibility metadata only. It binds:

- the Phase 517 score-axis eligibility digest and input digest;
- the Phase 517 digest, id, and label binding map digests;
- the Phase 517 classification `score_axes_blocked_local_only`;
- the Phase 517 score-axis blocker digest;
- the Phase 517 score-axis nonpopulation digest;
- the Phase 515 package digest and input digest;
- the Phase 515 evidence class `LocalReplay`;
- the Phase 515 claim boundary `Level1LocalReplay`;
- the Phase 513 materialized ledger artifact digest;
- the Phase 513 materialized append report digest;
- Level2 owner id `zkbench-core`;
- checker type `Level2EligibilityChecker`;
- checker function `check_level2_eligibility`;
- report type `Level2EligibilityReport`;
- report boundary `ClaimBoundary::Level0DesignNote`;
- report invariant `creates_level2_evidence = false`;
- Level2 policy digest;
- Level2 blocker digest;
- Level2 nonpromotion digest.

## Guardrails

Phase 519 fails closed if the Phase 517 record is not exact, if the Phase 517
classification is not `score_axes_blocked_local_only`, if any score axis is
populated, if Phase 515 evidence is not `LocalReplay` /
`Level1LocalReplay`, if Level2 owner/type/function/report identifiers drift, if
the report boundary is not `ClaimBoundary::Level0DesignNote`, if the report or
wrapper creates Level2 evidence, if the classification is not
`level2_blocked_local_only`, or if blocker, nonpromotion, rule, forbidden-API,
inherited-digest, or policy bindings drift.

It also rejects Level2 artifact writes, score-axis artifact writes, score-axis
population, accepted formal evidence, Level2+ evidence, proof/checker/solver
promotion, backend execution evidence, benchmark evidence, external-audit
evidence, semantic-correctness claims, production-readiness claims, SOTA
claims, breakthrough claims, full-security claims, and action authority.

## Evidence Meaning

Phase 519 supports this claim only:

```text
HSAI records that the local tiny-Z3 package remains Level2-blocked until
external reproduction, replay review, provenance, and accepted-evidence policy
requirements are satisfied.
```

The result is still not Level2+ evidence, not accepted formal evidence, not
score-axis evidence, not Lean proof, not SMT proof authority, not COBALT
containment evidence, not Rust-to-Lean proof, not checker transcript authority,
not solver certificate authority, not benchmark evidence, not external audit,
not SOTA, not semantic correctness, not production readiness, not full
security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful Level2 eligibility metadata over a real Phase 517 score-axis
  eligibility metadata record;
- rejection when the Phase 517 state is invalid;
- rejection of report-created Level2 evidence, Level2 artifact writes,
  score-axis artifact writes, score-axis population, formal-evidence, Level2+,
  proof/checker/solver, backend, benchmark, external-audit, strong-claim, and
  action-authority promotion attempts.

The tests assert that the metadata remains local, records classification
`level2_blocked_local_only`, binds `zkbench-core` /
`Level2EligibilityChecker` / `check_level2_eligibility` /
`Level2EligibilityReport`, records `ClaimBoundary::Level0DesignNote`, records
`creates_level2_evidence = false`, and creates no formal evidence, Level2+
evidence, score-axis evidence, backend execution evidence, benchmark evidence,
external audit evidence, or action authority.
