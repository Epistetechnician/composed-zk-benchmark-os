# Phase 500 HSAI Tiny Z3 Reviewer Policy Decision Boundary

State slice: `Phase 500 HSAI tiny Z3 reviewer policy decision boundary`.

Phase 500 defines the docs-first boundary for the next Phase 488
accepted-path prerequisite gate:

```text
reviewer policy and reviewer decision requirements
```

Phase 499 implemented local source correspondence statement metadata. Phase
500 records the next boundary: any future accepted-path bridge must bind a
reviewer policy and a reviewer decision over the exact Phase 499 source
correspondence metadata before any accepted append, accepted formal evidence,
Level2+ evidence, score-axis population, or strong public claim can be
considered.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, create a review artifact, create an accepted append
decision, mutate the accepted Evidence Ledger, change accepted append policy,
create accepted formal evidence, create Level2+ evidence, populate score axes,
generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run new SMT, run COBALT, run Rust-to-Lean extraction,
submit benchmarks, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, or grant authority
to execute an action.

## Required Reviewer Policy Fields

A future reviewer policy may satisfy this gate only if it records:

- reviewer policy schema version;
- reviewer policy id;
- reviewer policy digest;
- reviewer role requirements;
- reviewer independence requirement;
- reviewer decision labels;
- required input record type;
- required input record digest;
- required input record source correspondence digest;
- required current accepted append blocker digest;
- required explicit nonclaim digest;
- required drift rejection policy;
- required promotion rejection policy;
- required decision timestamp;
- required reviewer decision id;
- required reviewer decision digest;
- required reviewer decision summary constraints.

The reviewer policy must make the reviewer decision scoped to the Phase 499
source correspondence statement metadata. It must not approve a hidden input,
an unstated source correspondence claim, a backend execution result, a future
accepted append transaction, or any public claim.

## Required Decision Labels

A future implementation must use closed decision labels:

- `source_correspondence_review_accepted_for_local_metadata`;
- `source_correspondence_review_rejected`;
- `source_correspondence_review_blocked_by_policy_drift`;
- `source_correspondence_review_blocked_by_source_drift`;
- `source_correspondence_review_blocked_by_current_blocker_drift`;
- `source_correspondence_review_blocked_by_promotion_claim`.

The accepted label means only that the reviewer accepts the local Phase 499
source correspondence metadata as satisfying the Phase 488 source
correspondence prerequisite for later accepted-path evaluation. It is not an
accepted append decision, not accepted evidence, not formal evidence, and not
proof authority.

## Required Future Bindings

A future implementation that tries to satisfy this gate must bind:

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
- reviewer policy id;
- reviewer policy digest;
- reviewer decision id;
- reviewer decision digest;
- reviewer decision label;
- reviewer decision timestamp;
- explicit nonclaim set and digest.

The decision digest must cover the policy id, policy digest, input record
digest, source correspondence digest, reviewer decision label, reviewer
decision timestamp, reviewer summary, and explicit nonclaim digest.

## Required Future Validation

A future validator must reject the reviewer policy/decision gate input if:

- the schema version is not the future Phase 501 schema;
- any Phase 499 digest/id/label/nonclaim binding drifts;
- the Phase 499 source anchor set digest drifts;
- the Phase 499 statement digest input set digest drifts;
- the Phase 499 source path digest requirement digest drifts;
- the Phase 499 drift rejection policy digest drifts;
- the current accepted append blocker digest drifts;
- the reviewer policy id is empty or malformed;
- the reviewer policy digest is empty or malformed;
- the reviewer decision id is empty or malformed;
- the reviewer decision digest is empty or malformed;
- the reviewer decision timestamp is missing;
- the reviewer decision label is outside the closed label set;
- the reviewer summary contains a promotion claim;
- the reviewer policy attempts to approve accepted append;
- the reviewer policy attempts to approve accepted formal evidence;
- the reviewer policy attempts to approve proof/checker/solver authority;
- the reviewer policy attempts to approve Lean/new-SMT/COBALT/Rust-to-Lean
  execution evidence;
- the reviewer policy attempts to approve Level2+ evidence;
- the reviewer policy attempts to approve score-axis evidence;
- the reviewer policy attempts to approve benchmark evidence;
- the reviewer policy attempts to approve SOTA, semantic correctness,
  production readiness, full security, breakthrough status, or action
  authority.

## Reviewer Independence Limit

This boundary can require an independence declaration, but it does not create a
real identity, credential, conflict-of-interest, or governance system. A future
metadata implementation may record only local reviewer policy metadata unless a
separate explicit phase opens a stronger identity or governance route.

Reviewer approval is a local review control. It is not an external audit, not a
third-party certification, not independent reproduction, and not production
readiness evidence.

## Backend Relationship

The reviewer policy is a prerequisite for later backend execution and accepted
append evaluation. It does not cross either boundary.

- It may accept or reject the Phase 499 source correspondence metadata.
- It may require future backend evidence to cite the reviewed source
  correspondence digest.
- It may not certify a Lean proof, SMT solver result, COBALT containment
  result, Rust-to-Lean extraction result, benchmark run, or accepted append
  transaction that does not yet exist.

## Meaning Limit

The future reviewer policy/decision metadata may support this claim only:

```text
HSAI locally records a reviewer policy and reviewer decision requirement for
the Phase 499 source correspondence metadata before later accepted-path
evaluation.
```

That still is not:

- accepted append;
- accepted evidence;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
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

## Phase 501 Implementation Exit Criteria

A future Phase 501 may implement local reviewer policy/decision metadata only
if it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds one Phase 499 source correspondence record digest;
- binds one Phase 499 source correspondence input digest;
- binds the Phase 499 digest/id/label map digests;
- binds the Phase 499 explicit nonclaim digest;
- binds the Phase 499 source anchor set digest;
- binds the Phase 499 statement digest input set digest;
- binds the Phase 499 source path digest requirement digest;
- binds the Phase 499 drift rejection policy digest;
- binds current accepted append blocker digest;
- records the closed reviewer decision labels listed above;
- records reviewer policy id and reviewer policy digest requirements;
- records reviewer decision id, label, timestamp, and digest requirements;
- rejects reviewer summary promotion claims in the gate metadata itself;
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
  breakthrough, and action-authority claims in the gate metadata itself.
