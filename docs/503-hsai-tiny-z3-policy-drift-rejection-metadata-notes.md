# Phase 503 HSAI Tiny Z3 Policy Drift Rejection Metadata Notes

State slice: `Phase 503 HSAI tiny Z3 policy drift rejection metadata`.

Phase 503 implements local in-memory metadata for the Phase 488 accepted-path
prerequisite gate:

```text
rejection behavior for policy drift
```

The implemented record binds one Phase 501 reviewer policy decision record to
a closed policy drift source set, closed rejection action set, inherited digest
requirements, explicit nonclaims, and fail-closed promotion rejection flags.

This phase does not create a drift report artifact, repair drift, proceed
after drift, write filesystem artifacts, create an accepted append decision,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run new SMT, run COBALT, run Rust-to-Lean extraction,
create benchmark evidence, claim semantic correctness, claim production
readiness, claim SOTA, claim breakthrough status, claim full security, claim
external audit status, or grant authority to execute an action.

## Implemented Surface

`crates/hsai-agent-admission/src/lib.rs` now defines:

- `GATEWAY_FORMAL_TINY_Z3_POLICY_DRIFT_REJECTION_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_POLICY_DRIFT_REJECTION_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_POLICY_DRIFT_REJECTION_CLAIM_BOUNDARY`;
- `GatewayFormalTinyZ3PolicyDriftRejectionLabel`;
- `GatewayFormalTinyZ3PolicyDriftRejectionInput`;
- `GatewayFormalTinyZ3PolicyDriftRejection`;
- `GatewayFormalTinyZ3PolicyDriftRejectionIssue`;
- `GatewayFormalTinyZ3PolicyDriftRejectionValidation`;
- policy drift nonclaim, drift-source, rejection-action, and inherited digest
  requirement helpers;
- digest, id, and label binding helpers;
- `build_gateway_formal_tiny_z3_policy_drift_rejection`;
- `validate_gateway_formal_tiny_z3_policy_drift_rejection_input`.

The metadata binds:

- one Phase 501 reviewer policy decision record digest;
- one Phase 501 reviewer policy decision input digest;
- the Phase 501 digest-binding map digest;
- the Phase 501 id-binding map digest;
- the Phase 501 label-binding map digest;
- the Phase 501 explicit nonclaim digest;
- the Phase 501 reviewer policy digest;
- the Phase 501 reviewer decision digest;
- the Phase 501 drift rejection policy digest;
- the Phase 501 promotion rejection policy digest;
- current accepted append blocker digest;
- inherited Phase 499, Phase 497, Phase 495, Phase 493, and Phase 491 digest
  requirements.

The closed rejection actions are:

- `reject_accepted_append_evaluation`;
- `reject_accepted_evidence_ledger_mutation`;
- `reject_accepted_formal_evidence_creation`;
- `reject_level2_plus_creation`;
- `reject_score_axis_population`;
- `reject_backend_execution_authority`;
- `reject_benchmark_claim`;
- `reject_public_strong_claim`;
- `require_new_review_cycle`.

The validator rejects:

- Phase 501 digest/id/label/nonclaim drift;
- Phase 501 reviewer decision state drift;
- policy drift source set drift;
- rejection action set drift;
- inherited digest requirement drift;
- policy drift summary promotion claims;
- drift report artifact creation;
- drift repair;
- proceeding after drift;
- accepted append decisions;
- accepted Evidence Ledger mutation attempts;
- accepted append policy changes;
- accepted formal evidence creation;
- Level2+ evidence creation;
- score-axis population;
- proof/checker/solver authority;
- Lean/new-SMT/COBALT/Rust-to-Lean execution evidence;
- benchmark evidence;
- external audit claims;
- SOTA, semantic-correctness, production-readiness, breakthrough,
  full-security, or action-authority claims.

## Validation

Focused tests cover:

- successful Phase 503 metadata construction over a valid Phase 501 reviewer
  policy decision record;
- Phase 501 digest drift rejection;
- policy drift source set drift rejection;
- rejection action set drift rejection;
- promotion-attempt rejection, including drift artifact creation, drift repair,
  proceeding after drift, backend evidence, benchmark evidence, and external
  audit claims.

## Meaning Limit

The new metadata supports only this claim:

```text
HSAI locally records fail-closed policy drift sources and rejection actions for
the reviewed tiny-Z3 accepted-path prerequisite chain.
```

It is still not accepted append, not accepted evidence, not accepted formal
evidence, not accepted Evidence Ledger mutation, not accepted append policy
change, not drift repair, not a drift report artifact, not Level2+ evidence,
not score-axis evidence, not proof authority, not checker transcript
authority, not solver certificate authority, not backend execution evidence,
not benchmark evidence, not external audit evidence, not SOTA, not semantic
correctness, not production readiness, not full security, and not action
authority.

## Next Responsible Slice

The next responsible slice is a docs-first boundary for the next Phase 488
accepted-path prerequisite gate: rejection behavior for stale current accepted
append blockers. It must not implement accepted append, mutate the accepted
Evidence Ledger, create accepted formal evidence, create Level2+ evidence,
populate score axes, run Lean/new-SMT/COBALT/Rust-to-Lean extraction, create
benchmark evidence, or claim SOTA, full security, semantic correctness, or
production readiness.
