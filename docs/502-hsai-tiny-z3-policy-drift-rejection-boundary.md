# Phase 502 HSAI Tiny Z3 Policy Drift Rejection Boundary

State slice: `Phase 502 HSAI tiny Z3 policy drift rejection boundary`.

Phase 502 defines the docs-first boundary for the next Phase 488
accepted-path prerequisite gate:

```text
rejection behavior for policy drift
```

Phase 501 implemented local reviewer policy/decision metadata. Phase 502
records the next boundary: any future accepted-path bridge must fail closed if
the accepted append owner, mutation route, policy version, evidence class,
claim boundary, replay identity, source correspondence, reviewer policy,
reviewer decision, explicit nonclaims, or current accepted append blocker
digests drift from the reviewed local prerequisite chain.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, create a drift report artifact, create an accepted append
decision, mutate the accepted Evidence Ledger, change accepted append policy,
create accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run new SMT, run COBALT, run Rust-to-Lean extraction,
submit benchmarks, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, claim external
audit status, or grant authority to execute an action.

## Policy Drift Sources

A future implementation must treat these as policy drift sources:

- accepted append owner drift;
- accepted append mutation route drift;
- accepted append materialized route drift;
- accepted append policy owner drift;
- accepted append policy id drift;
- accepted append policy version drift;
- accepted append transaction version drift;
- accepted evidence class owner drift;
- accepted evidence class drift;
- accepted claim boundary owner drift;
- accepted claim boundary drift;
- rejected evidence class set drift;
- replay identity owner drift;
- replay identity field-set drift;
- replay validation rule drift;
- source correspondence source path drift;
- source correspondence source anchor drift;
- source correspondence statement digest input drift;
- reviewer policy id drift;
- reviewer policy digest drift;
- reviewer decision label drift;
- reviewer decision digest drift;
- explicit nonclaim set drift;
- explicit nonclaim digest drift;
- current accepted append blocker digest drift.

## Required Future Bindings

A future implementation that tries to satisfy this gate must bind:

- one Phase 501 reviewer policy decision record digest;
- one Phase 501 reviewer policy decision input digest;
- the Phase 501 digest-binding map digest;
- the Phase 501 id-binding map digest;
- the Phase 501 label-binding map digest;
- the Phase 501 explicit nonclaim digest;
- the Phase 501 reviewer policy digest;
- the Phase 501 reviewer decision digest;
- the Phase 501 current accepted append blocker digest;
- the Phase 499 source correspondence digest inherited through Phase 501;
- the Phase 497 replay identity digest inherited through Phase 499;
- the Phase 495 accepted evidence class/claim-boundary digest inherited
  through Phase 497;
- the Phase 493 accepted append policy-version digest inherited through Phase
  495;
- the Phase 491 accepted append owner/mutation-route digest inherited through
  Phase 493;
- a closed policy drift source set;
- a closed policy drift rejection action set;
- a policy drift summary constraint;
- explicit nonclaim set and digest.

The policy drift record must not recompute or substitute accepted append policy.
It may only compare bound digests, labels, and declared source values from the
local prerequisite chain.

## Required Rejection Actions

A future validator must use closed rejection actions:

- `reject_accepted_append_evaluation`;
- `reject_accepted_evidence_ledger_mutation`;
- `reject_accepted_formal_evidence_creation`;
- `reject_level2_plus_creation`;
- `reject_score_axis_population`;
- `reject_backend_execution_authority`;
- `reject_benchmark_claim`;
- `reject_public_strong_claim`;
- `require_new_review_cycle`.

The rejection action set means the local prerequisite chain remains blocked.
It does not create a quarantine artifact, rollback operation, accepted append
decision, or ledger mutation.

## Required Future Validation

A future validator must reject the policy drift gate input if:

- the schema version is not the future Phase 503 schema;
- any Phase 501 digest/id/label/nonclaim binding drifts;
- the Phase 501 reviewer policy digest drifts;
- the Phase 501 reviewer decision digest drifts;
- the current accepted append blocker digest drifts;
- any inherited Phase 499, Phase 497, Phase 495, Phase 493, or Phase 491 digest
  is absent;
- the policy drift source set is incomplete;
- the rejection action set is incomplete;
- the summary contains a promotion claim;
- the record attempts to repair drift;
- the record attempts to proceed after drift;
- the record attempts to approve accepted append;
- the record attempts to approve accepted formal evidence;
- the record attempts to approve proof/checker/solver authority;
- the record attempts to approve Lean/new-SMT/COBALT/Rust-to-Lean execution
  evidence;
- the record attempts to approve Level2+ evidence;
- the record attempts to approve score-axis evidence;
- the record attempts to approve benchmark evidence;
- the record attempts to approve SOTA, semantic correctness, production
  readiness, full security, breakthrough status, external audit status, or
  action authority.

## Backend Relationship

Policy drift rejection is a prerequisite for later backend execution. It does
not authorize backend execution.

A future backend run may only be considered after the accepted-path chain has a
stable reviewed policy state. If any bound policy digest drifts, later Lean,
SMT, COBALT, Rust-to-Lean, benchmark, score-axis, or accepted append work must
restart from the appropriate review boundary.

## Meaning Limit

The future policy drift rejection metadata may support this claim only:

```text
HSAI locally records fail-closed policy drift sources and rejection actions for
the reviewed tiny-Z3 accepted-path prerequisite chain.
```

That still is not:

- accepted append;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- drift repair;
- review artifact materialization;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- checker transcript authority;
- solver certificate authority;
- benchmark evidence;
- external audit;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 503 Implementation Status

Phase 503 implements local policy drift rejection metadata in
`docs/503-hsai-tiny-z3-policy-drift-rejection-metadata-notes.md`. That
implementation:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 501 reviewer policy decision record digest;
- binds one Phase 501 reviewer policy decision input digest;
- binds the Phase 501 digest/id/label map digests;
- binds the Phase 501 explicit nonclaim digest;
- binds the Phase 501 reviewer policy digest;
- binds the Phase 501 reviewer decision digest;
- binds current accepted append blocker digest;
- records inherited Phase 499, Phase 497, Phase 495, Phase 493, and Phase 491
  digest requirements;
- records the closed policy drift source set listed above;
- records the closed rejection action set listed above;
- rejects summary promotion claims in the gate metadata itself;
- rejects drift repair in the gate metadata itself;
- rejects proceeding after drift in the gate metadata itself;
- rejects accepted append decisions in the gate metadata itself;
- rejects accepted Evidence Ledger mutation in the gate metadata itself;
- rejects accepted append policy changes in the gate metadata itself;
- rejects accepted formal evidence creation in the gate metadata itself;
- rejects Level2+ evidence creation in the gate metadata itself;
- rejects score-axis population in the gate metadata itself;
- rejects proof/checker/solver authority creation in the gate metadata itself;
- rejects Lean/new-SMT/COBALT/Rust-to-Lean execution evidence creation in the
  gate metadata itself;
- rejects benchmark evidence creation in the gate metadata itself;
- rejects SOTA, semantic-correctness, production-readiness, full-security,
  breakthrough, external-audit, and action-authority claims in the gate
  metadata itself.
