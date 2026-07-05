# Phase 501 HSAI Tiny Z3 Reviewer Policy Decision Metadata Notes

State slice: `Phase 501 HSAI tiny Z3 reviewer policy decision metadata`.

Phase 501 implements local in-memory metadata for the Phase 488 accepted-path
prerequisite gate:

```text
reviewer policy and reviewer decision requirements
```

The implemented record binds one Phase 499 source correspondence statement
metadata record to a local reviewer policy digest, reviewer decision digest,
closed decision labels, reviewer role requirements, reviewer independence
declarations, drift rejection policy, promotion rejection policy, and explicit
nonclaims.

This phase does not create a review artifact, write filesystem artifacts,
create an accepted append decision, mutate the accepted Evidence Ledger,
change accepted append policy, create accepted formal evidence, create Level2+
evidence, populate score axes, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run new SMT, run COBALT,
run Rust-to-Lean extraction, create benchmark evidence, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough
status, claim full security, claim external audit status, or grant authority
to execute an action.

## Implemented Surface

`crates/hsai-agent-admission/src/lib.rs` now defines:

- `GATEWAY_FORMAL_TINY_Z3_REVIEWER_POLICY_DECISION_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_REVIEWER_POLICY_DECISION_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_REVIEWER_POLICY_DECISION_CLAIM_BOUNDARY`;
- `GATEWAY_FORMAL_TINY_Z3_REVIEWER_POLICY_DECISION_INPUT_TYPE`;
- `GatewayFormalTinyZ3ReviewerDecisionLabel`;
- `GatewayFormalTinyZ3ReviewerPolicyDecisionInput`;
- `GatewayFormalTinyZ3ReviewerPolicyDecision`;
- `GatewayFormalTinyZ3ReviewerPolicyDecisionIssue`;
- `GatewayFormalTinyZ3ReviewerPolicyDecisionValidation`;
- reviewer nonclaim, decision-label, role-requirement, independence,
  drift-rejection, and promotion-rejection helpers;
- reviewer policy digest and reviewer decision digest helpers;
- digest, id, and label binding helpers;
- `build_gateway_formal_tiny_z3_reviewer_policy_decision`;
- `validate_gateway_formal_tiny_z3_reviewer_policy_decision_input`.

The closed decision labels are:

- `source_correspondence_review_accepted_for_local_metadata`;
- `source_correspondence_review_rejected`;
- `source_correspondence_review_blocked_by_policy_drift`;
- `source_correspondence_review_blocked_by_source_drift`;
- `source_correspondence_review_blocked_by_current_blocker_drift`;
- `source_correspondence_review_blocked_by_promotion_claim`.

The metadata binds:

- one Phase 499 source correspondence record digest;
- one Phase 499 source correspondence input digest;
- the Phase 499 digest-binding map digest;
- the Phase 499 id-binding map digest;
- the Phase 499 label-binding map digest;
- the Phase 499 explicit nonclaim digest;
- the Phase 499 source anchor set digest;
- the Phase 499 statement digest input set digest;
- the Phase 499 source path digest requirement digest;
- the Phase 499 drift rejection policy digest;
- current accepted append blocker digest;
- reviewer policy id and digest;
- reviewer decision id, label, timestamp, summary, and digest;
- required input record type;
- reviewer role and independence requirements;
- drift and promotion rejection policies.

The validator rejects:

- Phase 499 digest/id/label/nonclaim drift;
- Phase 499 source correspondence state drift;
- reviewer policy digest drift;
- reviewer decision digest drift;
- required input record type drift;
- reviewer role requirement drift;
- reviewer independence requirement drift;
- closed reviewer decision-label drift;
- drift rejection policy drift;
- promotion rejection policy drift;
- reviewer decision summary promotion claims;
- review artifact creation;
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

- successful Phase 501 metadata construction over a valid Phase 499 source
  correspondence record;
- Phase 499 digest drift rejection;
- reviewer decision-label set drift rejection;
- reviewer decision digest drift rejection;
- promotion-attempt rejection, including review artifact creation and external
  audit claims.

## Meaning Limit

The new metadata supports only this claim:

```text
HSAI locally records reviewer policy and reviewer decision metadata for the
Phase 499 source correspondence metadata before later accepted-path evaluation.
```

It is still not accepted append, not accepted evidence, not accepted formal
evidence, not accepted Evidence Ledger mutation, not accepted append policy
change, not a review artifact, not Level2+ evidence, not score-axis evidence,
not proof authority, not checker transcript authority, not solver certificate
authority, not backend execution evidence, not benchmark evidence, not
external audit evidence, not SOTA, not semantic correctness, not production
readiness, not full security, and not action authority.

## Next Responsible Slice

The next responsible slice is a docs-first boundary for the next Phase 488
accepted-path prerequisite gate: rejection behavior for policy drift. It must
not implement accepted append, mutate the accepted Evidence Ledger, create
accepted formal evidence, create Level2+ evidence, populate score axes, run
Lean/new-SMT/COBALT/Rust-to-Lean extraction, create benchmark evidence, or
claim SOTA, full security, semantic correctness, or production readiness.
