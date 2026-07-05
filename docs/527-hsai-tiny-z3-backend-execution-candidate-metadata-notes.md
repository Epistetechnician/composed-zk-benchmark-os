# Phase 527 HSAI Tiny Z3 Backend Execution Candidate Metadata Notes

State slice: `Phase 527 HSAI tiny Z3 backend execution candidate metadata`.

Phase 527 implements the Lane A metadata authorized by Phase 526. It declares a
scoped SMT/Z3 replay as the only open future backend-execution lane over one
exact Phase 525 import-review metadata record.

The valid classification is:

```text
LaneAExecutionCandidateDeclaredNoRun
```

The record binds:

- the Phase 525 review metadata digest;
- the Phase 525 review input digest;
- Phase 525 classification `ImportReviewBlockedNoIndependentRun`;
- the Phase 523 import-candidate digest;
- the Phase 523 candidate, validation, and quarantine-record digests;
- Phase 523 status `ExternalResultStatus::Quarantined`;
- Phase 523 requested boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 521 external-reproduction metadata digest;
- the Phase 519 Level2 eligibility digest;
- the Phase 517 score-axis eligibility digest;
- the Phase 515 package digest;
- the Phase 513 materialized accepted-ledger artifact digest;
- one obligation artifact digest;
- one toolchain descriptor digest;
- one command descriptor digest;
- one expected-output grammar digest;
- one timeout policy digest;
- one scratch-output-root policy digest.

Lane state is explicit:

- Lane A scoped SMT/Z3 replay: open as future candidate.
- Lane B Lean/Rust-to-Lean: closed.
- Lane C COBALT-style containment: closed.

Validation is fail-closed when:

- the Phase 525 review is not exact;
- Lane A is not the only open lane;
- any descriptor digest is zero;
- the process-spawn request is not described;
- backend execution is marked performed;
- backend artifacts are marked written;
- network access, repository-root writes, or raw stdout/stderr retention are
  requested;
- accepted evidence, Level2+ evidence, score-axis population, Lean, COBALT,
  Rust-to-Lean, benchmark evidence, external audit, strong claims, or action
  authority are claimed.

Implemented tests cover a successful Lane A candidate with no backend run,
rejection of invalid Phase 525 state, and rejection of lane drift plus
promotion flags.

This phase does not run Z3, run Lean, run COBALT, run Rust-to-Lean extraction,
write backend artifacts, write accepted-evidence artifacts, accept
external-result evidence, create accepted formal evidence, create Level2+
evidence, populate score axes, create benchmark evidence, create external-audit
evidence, prove semantic correctness, establish production readiness, establish
SOTA, establish breakthrough status, establish full security, or grant
authority to execute an action.
