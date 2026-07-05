# Phase 504 HSAI Tiny Z3 Stale Accepted Append Blocker Rejection Boundary

State slice: `Phase 504 HSAI tiny Z3 stale accepted append blocker rejection
boundary`.

Phase 504 defines the docs-first boundary for the next Phase 488
accepted-path prerequisite gate:

```text
rejection behavior for stale current accepted append blockers
```

Phase 503 implemented local policy drift rejection metadata. Phase 504 records
the next boundary: any future accepted-path bridge must fail closed if the
current accepted append blocker digest used by the local prerequisite chain is
stale relative to the blocker digest expected at the moment of accepted append
evaluation.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, read or mutate the accepted Evidence Ledger, create a
stale-blocker report artifact, repair stale blockers, create an accepted append
decision, change accepted append policy, create accepted formal evidence,
create Level2+ evidence, populate score axes, generate proof artifacts,
generate checker transcripts, generate solver certificates, run Lean, run new
SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, claim external audit status, or
grant authority to execute an action.

## Stale Blocker Meaning

`current_accepted_append_blockers_digest` is stale when the digest bound into
the reviewed tiny-Z3 accepted-path prerequisite chain no longer matches the
digest required by the accepted append owner at evaluation time.

This boundary treats stale blocker detection as a comparison between declared
digests. It does not define a live ledger reader, ledger lock, append
transaction, rollback path, or mutation protocol.

## Required Future Bindings

A future implementation that tries to satisfy this gate must bind:

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
- the expected current accepted append blocker digest supplied by the accepted
  append owner;
- the blocker freshness comparison rule;
- the blocker stale rejection action set;
- explicit nonclaim set and digest.

The stale blocker record must not recompute blocker state from unreviewed
inputs. It may only compare an inherited reviewed blocker digest with an
expected blocker digest supplied by the accepted append owner surface.

## Required Freshness Comparison Rules

A future implementation must use closed freshness comparison rules:

- `blocker_digest_equality_required`;
- `missing_expected_blocker_digest_rejected`;
- `missing_reviewed_blocker_digest_rejected`;
- `zero_blocker_digest_rejected`;
- `stale_blocker_digest_rejected`;
- `new_review_cycle_required_on_mismatch`.

## Required Rejection Actions

A future implementation must use closed stale blocker rejection actions:

- `reject_accepted_append_evaluation`;
- `reject_accepted_evidence_ledger_mutation`;
- `reject_accepted_formal_evidence_creation`;
- `reject_level2_plus_creation`;
- `reject_score_axis_population`;
- `reject_backend_execution_authority`;
- `reject_benchmark_claim`;
- `reject_public_strong_claim`;
- `require_new_current_blocker_review`.

The rejection action set means the local prerequisite chain remains blocked.
It does not create a quarantine artifact, rollback operation, accepted append
decision, or ledger mutation.

## Required Future Validation

A future validator must reject the stale blocker gate input if:

- the schema version is not the future Phase 505 schema;
- any Phase 503 digest/id/label/nonclaim binding drifts;
- the Phase 503 policy drift source set digest drifts;
- the Phase 503 rejection action set digest drifts;
- the Phase 503 inherited digest requirement digest drifts;
- the reviewed current accepted append blocker digest is missing;
- the expected current accepted append blocker digest is missing;
- either blocker digest is zero;
- the reviewed and expected blocker digests differ;
- the freshness comparison rule set is incomplete;
- the stale blocker rejection action set is incomplete;
- the summary contains a promotion claim;
- the record attempts to refresh blockers directly;
- the record attempts to repair stale blockers;
- the record attempts to proceed after stale blocker detection;
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

Stale blocker rejection is a prerequisite for later backend execution and
accepted append evaluation. It does not authorize backend execution.

A future backend run may only be considered after the accepted-path chain has a
fresh reviewed blocker digest. If the blocker digest is stale, later Lean,
SMT, COBALT, Rust-to-Lean, benchmark, score-axis, or accepted append work must
restart from the appropriate review boundary.

## Meaning Limit

The future stale blocker rejection metadata may support this claim only:

```text
HSAI locally records fail-closed stale current accepted append blocker
freshness rules and rejection actions for the reviewed tiny-Z3 accepted-path
prerequisite chain.
```

That still is not:

- accepted append;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- blocker refresh;
- blocker repair;
- stale blocker report materialization;
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

## Phase 505 Implementation Exit Criteria

A future Phase 505 may implement local stale blocker rejection metadata only if
it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- reads no accepted Evidence Ledger files;
- mutates no accepted Evidence Ledger files;
- binds one Phase 503 policy drift rejection record digest;
- binds one Phase 503 policy drift rejection input digest;
- binds the Phase 503 digest/id/label map digests;
- binds the Phase 503 explicit nonclaim digest;
- binds the Phase 503 policy drift source set digest;
- binds the Phase 503 rejection action set digest;
- binds the Phase 503 inherited digest requirement digest;
- binds the reviewed current accepted append blocker digest;
- records an expected current accepted append blocker digest field;
- records the closed freshness comparison rule set listed above;
- records the closed stale blocker rejection action set listed above;
- rejects missing, zero, or unequal blocker digests in the gate metadata
  itself;
- rejects summary promotion claims in the gate metadata itself;
- rejects blocker refresh or repair in the gate metadata itself;
- rejects proceeding after stale blocker detection in the gate metadata itself;
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
