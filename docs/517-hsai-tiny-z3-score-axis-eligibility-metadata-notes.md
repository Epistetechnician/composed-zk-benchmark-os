# Phase 517 HSAI Tiny Z3 Score Axis Eligibility Metadata Notes

State slice: `Phase 517 HSAI tiny Z3 score-axis eligibility metadata`.

Phase 517 implements the local score-axis eligibility metadata path authorized
by `docs/516-hsai-tiny-z3-score-axis-eligibility-boundary.md`:

```text
Phase 515 local accepted-evidence package metadata
  + explicit score-axis eligibility policy
  -> local score-axis eligibility metadata
```

This phase is pure metadata. It does not write score-axis artifact files,
populate score axes, add a dependency, add a binary, add a script, spawn a
process, call the network, run a solver, run a proof assistant, run a
benchmark, or create proof/checker/solver artifacts.

## Implemented Surface

Phase 517 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3ScoreAxisEligibilityInput`;
- `GatewayFormalTinyZ3ScoreAxisEligibility`;
- `GatewayFormalTinyZ3ScoreAxisEligibilityClassification`;
- `GatewayFormalTinyZ3ScoreAxisEligibilityLabel`;
- `GatewayFormalTinyZ3ScoreAxisEligibilityIssue`;
- `GatewayFormalTinyZ3ScoreAxisEligibilityValidation`;
- deterministic score-axis name, nonpopulation, blocker, nonclaim, rule,
  forbidden-API, inherited-digest, policy-digest, digest-binding, id-binding,
  and label-binding helpers;
- `validate_gateway_formal_tiny_z3_score_axis_eligibility_input`;
- `build_gateway_formal_tiny_z3_score_axis_eligibility`.

The builder validates one exact Phase 515 package metadata record, then
records local eligibility metadata only. It binds:

- the Phase 515 package digest and input digest;
- the Phase 515 digest, id, and label binding map digests;
- the Phase 515 package policy digest;
- the Phase 515 package nonclaim digest;
- the Phase 515 package cap digest;
- the Phase 515 evidence class `LocalReplay`;
- the Phase 515 claim boundary `Level1LocalReplay`;
- the Phase 513 materialized ledger artifact digest;
- the Phase 513 materialized append report digest;
- score owner id `zkbench-core`;
- score report type `ScoreReport`;
- score validator id `validate_score_report`;
- eligibility policy digest;
- score-axis blocker digest;
- score-axis nonpopulation digest.

## Guardrails

Phase 517 fails closed if the Phase 515 package metadata state is not exact, if
the package evidence class is not `LocalReplay`, if the claim boundary is not
`Level1LocalReplay`, if the package created accepted formal evidence, if the
package created Level2+ evidence, if the package populated score axes, or if
the package promoted proof, checker, solver, backend, benchmark, audit,
semantic-correctness, production-readiness, SOTA, breakthrough,
full-security, or action-authority claims.

It also rejects score owner/type/validator drift, any classification other
than `score_axes_blocked_local_only`, missing or drifted blocker and
nonpopulation digests, any populated axis, score-axis artifact writes, accepted
formal evidence, Level2+ evidence, proof/checker/solver promotion, backend
execution evidence, benchmark evidence, external-audit evidence,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, and action authority.

## Evidence Meaning

Phase 517 supports this claim only:

```text
HSAI classifies the local Phase 515 package as score-axis ineligible until
Level2+ benchmark evidence, backend proof evidence, or external reproduction
exists.
```

The result is still not accepted formal evidence, not Level2+ evidence, not
score-axis evidence, not Lean proof, not SMT proof authority, not COBALT
containment evidence, not Rust-to-Lean proof, not checker transcript authority,
not solver certificate authority, not benchmark evidence, not external audit,
not SOTA, not semantic correctness, not production readiness, not full
security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful score-axis eligibility metadata over a real Phase 515 package
  metadata record;
- rejection when the Phase 515 package state is invalid;
- rejection of axis population, score-axis artifact writes, formal-evidence,
  Level2+, proof/checker/solver, backend, benchmark, external-audit,
  strong-claim, and action-authority promotion attempts.

The tests assert that the eligibility record remains local metadata, records
classification `score_axes_blocked_local_only`, leaves every score axis
unpopulated, binds `zkbench-core` / `ScoreReport` /
`validate_score_report`, and creates no formal evidence, Level2+ evidence,
backend execution evidence, benchmark evidence, external audit evidence, or
action authority.
