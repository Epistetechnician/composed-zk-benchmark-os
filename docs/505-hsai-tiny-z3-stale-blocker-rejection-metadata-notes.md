# Phase 505 HSAI Tiny Z3 Stale Blocker Rejection Metadata Notes

State slice: `Phase 505 HSAI tiny Z3 stale blocker rejection metadata`.

Phase 505 implements local in-memory metadata for the Phase 488 accepted-path
prerequisite gate:

```text
rejection behavior for stale current accepted append blockers
```

The implemented record binds one Phase 503 policy drift rejection record to a
reviewed current accepted append blocker digest, an expected current accepted
append blocker digest, a closed freshness comparison rule set, a closed stale
blocker rejection action set, inherited digest requirements, explicit
nonclaims, and fail-closed promotion rejection flags.

This phase does not create a stale blocker report artifact, refresh blockers,
repair blockers, proceed after stale blocker detection, write filesystem
artifacts, create an accepted append decision, mutate the accepted Evidence
Ledger, change accepted append policy, create accepted formal evidence, create
Level2+ evidence, populate score axes, generate proof artifacts, generate
checker transcripts, generate solver certificates, run Lean, run new SMT, run
COBALT, run Rust-to-Lean extraction, create benchmark evidence, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough
status, claim full security, claim external audit status, or grant authority
to execute an action.

## Implemented Surface

`crates/hsai-agent-admission/src/lib.rs` now defines:

- `GATEWAY_FORMAL_TINY_Z3_STALE_BLOCKER_REJECTION_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_Z3_STALE_BLOCKER_REJECTION_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_Z3_STALE_BLOCKER_REJECTION_CLAIM_BOUNDARY`;
- `GatewayFormalTinyZ3StaleBlockerRejectionLabel`;
- `GatewayFormalTinyZ3StaleBlockerRejectionInput`;
- `GatewayFormalTinyZ3StaleBlockerRejection`;
- `GatewayFormalTinyZ3StaleBlockerRejectionIssue`;
- `GatewayFormalTinyZ3StaleBlockerRejectionValidation`;
- stale blocker nonclaim, freshness-rule, rejection-action, and inherited
  digest requirement helpers;
- digest, id, and label binding helpers;
- `build_gateway_formal_tiny_z3_stale_blocker_rejection`;
- `validate_gateway_formal_tiny_z3_stale_blocker_rejection_input`.

The metadata binds:

- one Phase 503 policy drift rejection record digest;
- one Phase 503 policy drift rejection input digest;
- the Phase 503 digest-binding map digest;
- the Phase 503 id-binding map digest;
- the Phase 503 label-binding map digest;
- the Phase 503 explicit nonclaim digest;
- the Phase 503 policy drift source set digest;
- the Phase 503 rejection action set digest;
- the Phase 503 inherited digest requirement digest;
- the reviewed current accepted append blocker digest inherited through Phase
  503;
- the expected current accepted append blocker digest supplied to the local
  gate metadata.

The closed freshness comparison rules are:

- `blocker_digest_equality_required`;
- `missing_expected_blocker_digest_rejected`;
- `missing_reviewed_blocker_digest_rejected`;
- `zero_blocker_digest_rejected`;
- `stale_blocker_digest_rejected`;
- `new_review_cycle_required_on_mismatch`.

The closed stale blocker rejection actions are:

- `reject_accepted_append_evaluation`;
- `reject_accepted_evidence_ledger_mutation`;
- `reject_accepted_formal_evidence_creation`;
- `reject_level2_plus_creation`;
- `reject_score_axis_population`;
- `reject_backend_execution_authority`;
- `reject_benchmark_claim`;
- `reject_public_strong_claim`;
- `require_new_current_blocker_review`.

The validator rejects:

- Phase 503 digest/id/label/nonclaim drift;
- Phase 503 policy drift source, rejection action, or inherited digest
  requirement digest drift;
- Phase 503 policy drift rejection state drift;
- missing reviewed blocker digests;
- missing expected blocker digests;
- reviewed blocker digest drift from Phase 503;
- stale blocker digest mismatch between reviewed and expected blocker digests;
- freshness comparison rule set drift;
- stale blocker rejection action set drift;
- inherited digest requirement drift;
- stale blocker summary promotion claims;
- stale blocker report artifact creation;
- blocker refresh;
- blocker repair;
- proceeding after stale blocker detection;
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

- successful Phase 505 metadata construction over a valid Phase 503 policy
  drift rejection record;
- Phase 503 digest binding and inherited blocker digest preservation;
- stale blocker digest mismatch rejection;
- missing reviewed blocker digest rejection;
- freshness comparison rule drift rejection;
- stale blocker rejection action drift rejection;
- promotion-attempt rejection, including stale blocker artifact creation,
  blocker refresh, blocker repair, proceeding after stale blocker detection,
  backend evidence, benchmark evidence, and external audit claims.

## Meaning Limit

The new metadata supports only this claim:

```text
HSAI locally records fail-closed stale current accepted append blocker
freshness rules and rejection actions for the reviewed tiny-Z3 accepted-path
prerequisite chain.
```

It is still not accepted append, not accepted evidence, not accepted formal
evidence, not accepted Evidence Ledger mutation, not accepted append policy
change, not blocker refresh, not blocker repair, not stale blocker report
materialization, not Level2+ evidence, not score-axis evidence, not Lean proof,
not SMT proof authority, not COBALT containment evidence, not Rust-to-Lean
proof, not checker transcript authority, not solver certificate authority, not
benchmark evidence, not external audit, not SOTA, not semantic correctness,
not production readiness, not full security, and not authority to execute an
action.

## Phase 506 Boundary Status

Phase 506 defines the docs-first accepted append evaluation handoff boundary in
`docs/506-hsai-tiny-z3-accepted-append-evaluation-handoff-boundary.md`.

That boundary still does not authorize accepted Evidence Ledger reads or
writes, accepted append mutation, materialized accepted ledger output, accepted
formal evidence, Level2+ evidence, score axes, Lean/new-SMT/COBALT/
Rust-to-Lean execution, benchmark evidence, or
production/SOTA/security/correctness claims.
