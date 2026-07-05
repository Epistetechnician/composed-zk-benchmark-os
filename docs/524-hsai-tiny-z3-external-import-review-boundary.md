# Phase 524 HSAI Tiny Z3 External Import Review Boundary

State slice: `Phase 524 HSAI tiny Z3 external import review boundary`.

Phase 524 defines the docs-first boundary for future review metadata over the
Phase 523 quarantined external-result import candidate:

```text
Phase 523 quarantined import candidate metadata
  + explicit review policy
  -> future local import-review metadata
```

Phase 525 implements this boundary as local metadata in
`docs/525-hsai-tiny-z3-external-import-review-metadata-notes.md`.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate accepted ledgers, accept external-result evidence,
run an external replay, run a backend, run Lean, run SMT/Z3, run COBALT, run
Rust-to-Lean extraction, create proof artifacts, create checker transcripts,
create solver certificates, create accepted formal evidence, create Level2+
evidence, populate score axes, submit benchmarks, claim semantic correctness,
claim production readiness, claim SOTA, claim breakthrough status, claim full
security, claim external audit status, or grant authority to execute an action.

## Future Review Classifications

A future implementation may classify one exact Phase 523 candidate as:

- `import_review_blocked_no_independent_run`;
- `import_review_rejected`;
- `import_review_waiting_for_operator_review`;
- `import_review_ready_for_future_review_only`.

Under current evidence, the only valid classification is:

```text
import_review_blocked_no_independent_run
```

The review lane may recognize that the Phase 523 candidate was structurally
valid and quarantined, but it must preserve that independent external
reproduction is absent.

## Required Future Bindings

A future implementation must bind:

- one Phase 523 import-candidate metadata digest;
- one Phase 523 import-candidate input digest;
- the Phase 523 classification
  `import_candidate_quarantined_local_metadata`;
- the Phase 523 candidate digest;
- the Phase 523 validation digest;
- the Phase 523 validation-issue digest;
- the Phase 523 quarantine-record digest;
- Phase 523 status `ExternalResultStatus::Quarantined`;
- Phase 523 requested boundary `ClaimBoundary::Level0DesignNote`;
- the Phase 521 external-reproduction metadata digest;
- the Phase 521 classification
  `external_reproduction_blocked_no_independent_run`;
- the Phase 519 Level2 eligibility digest;
- the Phase 517 score-axis eligibility digest;
- the Phase 515 package digest;
- the Phase 513 materialized accepted-ledger artifact digest;
- a review policy id;
- a review decision id;
- a review blocker digest;
- a review nonpromotion digest;
- explicit nonclaims for independent reproduction, accepted formal evidence,
  Level2+ evidence, score axes, proof/checker/solver authority, backend
  execution evidence, benchmark evidence, external audit, SOTA, semantic
  correctness, production readiness, full security, and action authority.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 523 record is not exact;
- the Phase 523 classification is not
  `import_candidate_quarantined_local_metadata`;
- the Phase 523 validator result is invalid or has issues;
- the Phase 523 quarantine status is not `Quarantined`;
- the Phase 523 requested boundary is not `ClaimBoundary::Level0DesignNote`;
- the Phase 521 record is not exact;
- the Phase 521 classification is not
  `external_reproduction_blocked_no_independent_run`;
- independent external reproduction is claimed present;
- accepted formal evidence is claimed present;
- Level2+ evidence is claimed present;
- score-axis population is claimed present;
- proof artifacts, checker transcripts, or solver certificates are promoted;
- backend execution evidence, benchmark evidence, external audit, SOTA,
  semantic correctness, production readiness, full security, or action authority
  is claimed.

## Backend Relationship

This boundary is not backend execution and not evidence acceptance. It is a
future local review layer over the already-quarantined Phase 523 candidate.

If a future review record succeeds under current evidence, it may support this
claim only:

```text
HSAI can locally review a structurally valid tiny-Z3 external-result import
candidate and keep it blocked because independent external reproduction is
absent.
```

That still would not be independent external reproduction, Level2+ evidence,
accepted formal evidence, score-axis evidence, Lean proof, SMT proof authority,
COBALT containment evidence, Rust-to-Lean proof, checker transcript authority,
solver certificate authority, benchmark evidence, external audit, SOTA,
semantic correctness, production readiness, full security, or authority to
execute an action.

## Phase 525 Implementation Exit Criteria

A future Phase 525 may implement local import-review metadata only if it:

- touches only `crates/hsai-agent-admission/src/lib.rs`, focused tests in that
  file, future phase notes under `docs/`, and navigation/status updates under
  `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`;
- performs no process or network calls;
- writes no external-result artifact files;
- writes no accepted-evidence files;
- writes no Level2 or score-axis files;
- validates one exact Phase 523 import-candidate metadata record;
- records `import_review_blocked_no_independent_run`;
- rejects accepted formal evidence, Level2+ evidence, populated score axes,
  proof/checker/solver authority, backend execution evidence, benchmark
  evidence, external audit, strong claims, and action authority in the metadata
  itself.
