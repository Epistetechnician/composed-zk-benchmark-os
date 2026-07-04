# Phase 492 HSAI Tiny Z3 Accepted Append Policy Version Boundary

State slice: `Phase 492 HSAI tiny Z3 accepted append policy version
boundary`.

Phase 492 defines the docs-first boundary for the second Phase 489
accepted-path prerequisite gate:

```text
accepted_append_policy_version
```

Phase 491 recorded the accepted append owner and mutation route. Phase 492
records the next boundary: any future HSAI accepted-path bridge must bind the
actual `zkbench-core` acceptance-policy and append-transaction version
surfaces before any accepted append, accepted formal evidence, Level2+,
score-axis, benchmark, SOTA, semantic-correctness, production-readiness,
full-security, breakthrough, or action-authority claim can be considered.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate the accepted Evidence Ledger, create an accepted
append decision, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, generate proof
artifacts, generate checker transcripts, generate solver certificates, run
Lean, run new SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Current Policy Surface

The current policy/version surface remains owned by `zkbench-core`:

- `crates/zkbench-core/src/evidence/acceptance_policy.rs`;
- `EvidenceAcceptancePolicyVersion`;
- `EvidenceAcceptancePolicy::phase_j_conservative`;
- `EvidenceAcceptancePolicy::phase_j_level1_local_only`;
- `crates/zkbench-core/src/evidence/accepted_append.rs`;
- `AcceptedLedgerAppendTransactionVersion`;
- `AcceptedLedgerAppendTransactionRequest`;
- `crates/zkbench-core/src/evidence/accepted_append_output.rs`;
- `MaterializedAcceptedLedgerAppendRequest`.

The current source-defined version strings are:

```text
zkbench-core-accepted-append-local-level1-replay-formal-evidence-blocked:v1
phase-j-evidence-acceptance-policy-v0
phase-w-accepted-ledger-append-transaction-v0
```

The first string is the current HSAI admission accepted-append policy-version
marker used by both the tiny-Z3 and real-command accepted-handoff lanes. The
second string is the default `EvidenceAcceptancePolicyVersion` value in
`zkbench-core`. The third string is the default
`AcceptedLedgerAppendTransactionVersion` value in the Phase W accepted-ledger
append transaction.

The current local accepted-append policy lane is still conservative:

- candidate creation is policy-gated;
- local Level1 candidate creation is the upper accepted transaction boundary;
- Level2+ actual evidence remains blocked;
- formal evidence classes remain disallowed for this accepted append path;
- official benchmark claims remain rejected;
- score-axis population remains rejected;
- accepted append requires the existing reviewed preflight, candidate, append
  preview, review decision, artifact digest, and ledger-tip alignment.

## HSAI Admission Role

`crates/hsai-agent-admission` may record local metadata that references the
policy/version surface. It may not define a competing accepted append policy,
change `zkbench-core` policy semantics, infer a newer policy version, or use
policy-version metadata as accepted evidence.

A future HSAI-to-accepted-append bridge may only satisfy this prerequisite if
it binds the exact policy identifiers and transaction schema version that the
`zkbench-core` append path will use. If those identifiers are unknown, the
future metadata must record them as unresolved instead of inventing values.

## Required Future Bindings

A future implementation that tries to satisfy this gate must bind:

- one Phase 491 owner/mutation-route record digest;
- one Phase 491 owner/mutation-route input digest;
- the Phase 491 digest-binding map digest;
- the Phase 491 id-binding map digest;
- the Phase 491 label-binding map digest;
- the Phase 491 explicit nonclaim digest;
- current accepted append blocker digest;
- accepted append owner `zkbench-core`;
- local transaction route `AcceptedLedgerAppendTransactionRequest`;
- materialized route `MaterializedAcceptedLedgerAppendRequest`;
- evidence acceptance policy owner `zkbench-core`;
- exact acceptance-policy type `EvidenceAcceptancePolicy`;
- exact acceptance-policy version type `EvidenceAcceptancePolicyVersion`;
- exact HSAI accepted-append policy-version marker
  `zkbench-core-accepted-append-local-level1-replay-formal-evidence-blocked:v1`;
- exact candidate-policy id or explicit unresolved marker;
- exact candidate-policy version or explicit unresolved marker;
- exact candidate-policy mode or explicit unresolved marker;
- exact append transaction version type `AcceptedLedgerAppendTransactionVersion`;
- exact append transaction version string or explicit unresolved marker;
- exact claim-boundary cap or explicit unresolved marker;
- exact disallowed evidence classes or explicit unresolved marker;
- exact review-decision requirements or explicit unresolved marker;
- exact rejection policy for Level2+, formal evidence, official benchmark,
  score-axis, stale-tip, missing artifact-digest, and strong public-claim
  attempts.

## Required Future Validation

A future validator must reject the policy-version gate input if:

- the schema version is not the future Phase 493 schema;
- the Phase 491 owner/mutation-route digest or input digest drifts;
- the Phase 491 digest/id/label map digests drift;
- the Phase 491 explicit nonclaim digest drifts;
- the current accepted append blocker digest drifts;
- the accepted append owner is not `zkbench-core`;
- the local transaction route is not `AcceptedLedgerAppendTransactionRequest`;
- the materialized route is not `MaterializedAcceptedLedgerAppendRequest`;
- the evidence acceptance policy owner is not `zkbench-core`;
- the acceptance-policy type is not `EvidenceAcceptancePolicy`;
- the acceptance-policy version type is not `EvidenceAcceptancePolicyVersion`;
- the HSAI accepted-append policy-version marker is not
  `zkbench-core-accepted-append-local-level1-replay-formal-evidence-blocked:v1`;
- the append transaction version type is not
  `AcceptedLedgerAppendTransactionVersion`;
- an unresolved policy id, policy version, policy mode, transaction version,
  claim-boundary cap, evidence-class set, or review-decision requirement is
  replaced by an invented value;
- the metadata tries to change accepted append policy;
- the metadata tries to create an accepted append decision;
- the metadata tries to mutate the accepted Evidence Ledger;
- the metadata tries to create accepted formal evidence;
- the metadata tries to create Level2+ evidence;
- the metadata tries to populate score axes;
- the metadata tries to create proof/checker/solver authority;
- the metadata tries to create Lean/new-SMT/COBALT/Rust-to-Lean execution
  evidence;
- the metadata tries to create benchmark evidence;
- the metadata tries to claim SOTA, semantic correctness, production
  readiness, full security, breakthrough status, or action authority.

## Meaning Limit

The future policy-version gate record may support this claim only:

```text
HSAI locally records the accepted append policy/version identifiers that a
future accepted append bridge must bind before it can ask zkbench-core to
evaluate an accepted-ledger append transaction.
```

That still is not:

- accepted append;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- benchmark evidence;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Phase 493 Implementation Exit Criteria

Phase 493 may implement local accepted append policy-version metadata only if
it:

- remains in `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes no filesystem artifacts;
- performs no process or network calls;
- binds the Phase 491 owner/mutation-route digest and input digest;
- binds the Phase 491 digest/id/label map digests;
- binds the Phase 491 explicit nonclaim digest;
- identifies `zkbench-core` as the only accepted append and policy owner;
- identifies `EvidenceAcceptancePolicy` as the acceptance-policy type;
- identifies `EvidenceAcceptancePolicyVersion` as the acceptance-policy
  version type;
- identifies `AcceptedLedgerAppendTransactionVersion` as the accepted append
  transaction version type;
- records exact known version strings only when derived from `zkbench-core`;
- records unknown future bridge inputs as unresolved;
- rejects accepted append policy changes in the gate metadata itself;
- rejects accepted append decisions in the gate metadata itself;
- rejects accepted Evidence Ledger mutation in the gate metadata itself;
- rejects accepted formal evidence creation in the gate metadata itself;
- rejects Level2+ evidence creation in the gate metadata itself;
- rejects score-axis population in the gate metadata itself;
- rejects proof/checker/solver authority creation in the gate metadata itself;
- rejects Lean/new-SMT/COBALT/Rust-to-Lean execution evidence creation in the
  gate metadata itself;
- rejects benchmark evidence creation in the gate metadata itself;
- rejects SOTA, semantic-correctness, production-readiness, full-security,
  breakthrough, and action-authority claims in the gate metadata itself.
