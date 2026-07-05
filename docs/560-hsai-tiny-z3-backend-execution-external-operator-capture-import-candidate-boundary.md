# Phase 560 HSAI Tiny Z3 Backend Execution External Operator Capture Import Candidate Boundary

State slice: `Phase 560 HSAI tiny Z3 backend execution external operator capture import candidate boundary`.

Phase 560 defines the docs-first boundary for a future local import-candidate
metadata record over one exact Phase 559 quarantined capture packet:

```text
Phase 559 quarantined operator capture metadata
  + zkbench-core external-result candidate contract
  -> future local external-result import candidate metadata
```

This phase does not implement Rust code, change Cargo metadata, add
dependencies, add binaries, add scripts, write filesystem artifacts, run an
external replay, run a backend, run Lean, run SMT/Z3, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, import external results, mutate the accepted
Evidence Ledger, create accepted formal evidence, create Level2+ evidence,
populate score axes, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, claim external audit status, accept independent external
reproduction, or grant authority to execute an action.

## Future Import Candidate Meaning

A future implementation may build only an in-memory local import-candidate
metadata record from one Phase 559 capture manifest. That record may bind the
candidate fields needed by `zkbench_core::validate_external_result_candidate`
and `zkbench_core::external_result_quarantine_record`, but it must remain
quarantined metadata until a separate review phase.

The future record must not write external-result artifacts, accepted-evidence
artifacts, Level2 artifacts, score-axis artifacts, proof artifacts, checker
transcripts, solver certificates, benchmark artifacts, production deployment
artifacts, raw stdout/stderr, raw provider responses, secrets, credentials, or
undeclared files.

## Required Future Bindings

A future implementation must bind:

- one Phase 559 capture manifest digest;
- the Phase 559 readback validation digest;
- the Phase 559 nonpromotion report digest;
- the Phase 559 Phase 557 handoff packet manifest digest;
- the Phase 557 Phase 555 handoff digest;
- the Phase 555 manual handoff bundle digest;
- the Phase 555 manual handoff validation digest and zero issue count;
- the Phase 553 blocked import-review digest;
- inherited Phase 551/549/547/545/543/541/535/533/531/529/527 digests;
- the Phase 559 operator provenance digest;
- the Phase 559 execution observation digest;
- the Phase 559 captured-artifact index digest;
- the Phase 559 redaction report digest;
- a future external-result candidate digest;
- a future `validate_external_result_candidate` validation digest;
- a future `external_result_quarantine_record` digest;
- requested claim boundary `ClaimBoundary::Level0DesignNote`;
- explicit nonclaims for accepted evidence, accepted formal evidence,
  independent external reproduction accepted by the repo, Level2+ evidence,
  populated score axes, proof/checker/solver authority, Lean evidence, COBALT
  evidence, Rust-to-Lean evidence, benchmark evidence, external audit, SOTA,
  semantic correctness, production readiness, full security, and action
  authority.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 559 capture manifest is missing, stale, malformed, or not exact;
- the Phase 559 capture manifest claims local backend execution, external
  result import, accepted independent external reproduction, accepted formal
  evidence, Level2+ evidence, score-axis population, proof artifacts, checker
  transcripts, solver certificates, Lean execution, COBALT execution,
  Rust-to-Lean execution, benchmark evidence, external audit, strong public
  claims, or action authority;
- the Phase 559 redaction report is invalid or any captured artifact retains
  raw content;
- the Phase 559 captured-artifact index contains proof, checker, solver, Lean,
  COBALT, Rust-to-Lean, benchmark, production, accepted-evidence, Level2,
  score-axis, raw stdout/stderr, provider response, secret, credential, or
  undeclared artifact labels;
- the future external-result candidate requests a claim boundary above
  `ClaimBoundary::Level0DesignNote`;
- the future external-result validation has any issue;
- the future quarantine record does not remain quarantined local metadata;
- any import-candidate metadata claims that external result import has already
  occurred or that accepted evidence exists.

## Evidence Meaning

If a future import-candidate metadata record succeeds under this boundary, it
may support only:

```text
HSAI can derive a quarantined local external-result import candidate from a
locally validated operator capture packet.
```

That still would not be external result import, accepted evidence, accepted
formal evidence, independent external reproduction accepted by the repo,
Level2+ evidence, score-axis evidence, Lean proof, SMT proof authority, COBALT
containment evidence, Rust-to-Lean proof, checker transcript authority, solver
certificate authority, benchmark evidence, external audit, SOTA, semantic
correctness, production readiness, full security, or authority to execute an
action.

## Phase 561 Implementation Exit Criteria

Phase 561 implemented local import-candidate metadata under this boundary. The
implementation:

- touched only `crates/hsai-agent-admission/src/lib.rs`, focused tests in that
  file, phase notes under `docs/`, and navigation/status updates under
  `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`;
- performs no process or network calls;
- reads no credentials;
- writes no filesystem artifact bundle;
- validates one exact Phase 559 capture manifest;
- constructs only in-memory `zkbench_core` external-result candidate and
  quarantine metadata;
- records candidate, validation, and quarantine digests only;
- keeps the candidate status quarantined and requested claim boundary
  `ClaimBoundary::Level0DesignNote`;
- rejects any claim that external result import, accepted formal evidence,
  Level2+ evidence, score-axis population, benchmark evidence, external audit,
  strong public claim, or action authority exists.
