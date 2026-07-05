# Phase 554 HSAI Tiny Z3 Backend Execution Independent External Reproduction Handoff Boundary

State slice: `Phase 554 HSAI tiny Z3 backend execution independent external reproduction handoff boundary`.

Phase 554 defines the docs-first boundary for a future manual handoff package
that can ask an independent operator to reproduce the tiny-Z3 backend-execution
route outside the current local metadata chain:

```text
Phase 553 blocked import-review metadata
  + manual operator handoff contract
  -> future independent external-reproduction handoff metadata
```

This phase does not implement Rust code, change Cargo metadata, add
dependencies, add binaries, add scripts, write filesystem artifacts, run an
external replay, run a backend, run Lean, run SMT/Z3, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, import external results, mutate the accepted
Evidence Ledger, create accepted formal evidence, create Level2+ evidence,
populate score axes, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, claim external audit status, claim independent external
reproduction, or grant authority to execute an action.

## Future Handoff Meaning

A future implementation may create local handoff metadata that says:

- the Phase 553 review is blocked only because independent external
  reproduction is absent;
- the exact local candidate, review, and nonclaim digests are fixed;
- the external operator must produce a separate artifact bundle before any
  result can be imported;
- the handoff itself is `Level0DesignNote` metadata.

Under current evidence, the only valid classification is:

```text
independent_external_reproduction_handoff_declared_no_run
```

That classification may prepare an operator packet, but it cannot be treated as
external reproduction, accepted evidence, Level2+ evidence, or score-axis
evidence.

## Existing Owner Surface

The existing owner surface remains `zkbench-core` and the Phase H external
runner boundary:

- `ManualHandoffBundle`;
- manual-only `ExternalRunnerPolicy`;
- artifact capture contract metadata;
- provenance contract metadata;
- result import validation schema;
- quarantine behavior;
- `ClaimBoundary::Level0DesignNote`.

These APIs can describe how an operator should run and capture a result. They
do not execute the run, verify an independent operator, import external
results, accept evidence, populate score axes, or establish semantic
correctness.

## Required Future Bindings

A future implementation must bind:

- one Phase 553 import-review metadata digest;
- one Phase 553 import-review input digest;
- the Phase 553 classification
  `BackendExecutionImportReviewBlockedNoIndependentRun`;
- the Phase 553 review blocker, policy, and nonpromotion digests;
- the Phase 551 import-candidate digest and input digest;
- the Phase 551 classification `ImportCandidateQuarantinedLocalMetadata`;
- the Phase 551 candidate, validation, validation-issue, and quarantine-record
  digests;
- Phase 551 status `Quarantined`;
- Phase 551 requested boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 549 external-reproduction digest and classification
  `ExternalReproductionBlockedNoIndependentRun`;
- the Phase 547 Level2 eligibility digest and classification
  `Level2BlockedLocalOnly`;
- the Phase 545 score-axis eligibility and nonpopulation digests;
- the Phase 543 package digest, evidence class `LocalReplay`, and claim
  boundary `Level1LocalReplay`;
- the Phase 541 materialized ledger artifact digest;
- inherited Phase 535/533/531/529/527 digests;
- `zkbench-core` manual handoff owner id;
- manual handoff policy id;
- required external operator output roles;
- required provenance field digest;
- result import quarantine requirement digest;
- explicit nonclaims for independent reproduction, accepted formal evidence,
  Level2+ evidence, populated score axes, Lean proof, SMT proof authority,
  COBALT containment evidence, Rust-to-Lean proof, proof/checker/solver
  authority, benchmark evidence, external audit, SOTA, semantic correctness,
  production readiness, full security, and action authority.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 553 record is not exact;
- the Phase 553 classification is not
  `BackendExecutionImportReviewBlockedNoIndependentRun`;
- the Phase 551 import candidate is not exact, valid, and quarantined;
- the Phase 549 external-reproduction record is not blocked for missing
  independent external reproduction;
- any inherited Phase 547/545/543/541/535/533/531/529/527 binding is missing
  or drifted;
- the future handoff classification claims that a run occurred;
- the future handoff requests process execution, network access, credentials,
  external replay, artifact import, accepted-evidence mutation, Level2
  artifacts, score-axis artifacts, or score-axis population;
- proof artifacts, checker transcripts, solver certificates, Lean evidence,
  COBALT evidence, Rust-to-Lean evidence, or additional SMT/Z3 evidence are
  claimed present;
- benchmark evidence, external audit, SOTA, semantic correctness, production
  readiness, full security, independent external reproduction, or action
  authority is claimed.

## Evidence Meaning

If a future handoff record succeeds under current evidence, it may support this
claim only:

```text
HSAI can prepare a digest-bound manual handoff request for independent
external reproduction of the backend-execution route.
```

That still would not be independent external reproduction, accepted formal
evidence, Level2+ evidence, score-axis evidence, Lean proof, SMT proof
authority, COBALT containment evidence, Rust-to-Lean proof, checker transcript
authority, solver certificate authority, benchmark evidence, external audit,
SOTA, semantic correctness, production readiness, full security, or authority
to execute an action.

## Phase 555 Implementation Exit Criteria

A future Phase 555 may implement local handoff metadata only if it:

- touches only `crates/hsai-agent-admission/src/lib.rs`, focused tests in that
  file, future phase notes under `docs/`, and navigation/status updates under
  `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`;
- performs no process or network calls;
- writes no external-result artifact files;
- writes no accepted-evidence files;
- writes no Level2 or score-axis files;
- validates one exact Phase 553 blocked import-review metadata record;
- records `independent_external_reproduction_handoff_declared_no_run`;
- rejects any claim that a run, proof, checker transcript, solver certificate,
  external result import, Level2+ evidence, score-axis population, benchmark
  evidence, external audit, strong public claim, or action authority exists.
