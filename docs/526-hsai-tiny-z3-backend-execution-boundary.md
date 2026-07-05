# Phase 526 HSAI Tiny Z3 Backend Execution Boundary

State slice: `Phase 526 HSAI tiny Z3 backend execution boundary`.

Phase 526 defines the docs-first boundary for the first future backend
execution crossing after Phase 525 import-review metadata:

```text
Phase 525 blocked import-review metadata
  + explicit executable backend crossing policy
  -> future scoped backend execution candidate metadata
```

Phase 527 implements the Lane A candidate metadata in
`docs/527-hsai-tiny-z3-backend-execution-candidate-metadata-notes.md`.

This phase does not implement Rust code, change Cargo metadata, run a process,
run Z3, run Lean, run COBALT, run Rust-to-Lean extraction, call the network,
write backend artifacts, mutate accepted ledgers, accept formal evidence, create
Level2+ evidence, populate score axes, submit benchmarks, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough status,
claim full security, claim external audit status, or grant authority to execute
an action.

## Execution Lanes

The future execution surface is intentionally split:

- **Lane A: scoped SMT/Z3 replay.** Immediate future candidate. It may only
  replay one already-materialized tiny-Z3 obligation with a fixed command
  descriptor, fixed input digest, fixed expected-output grammar, no network,
  caller-selected local scratch output, and explicit timeout.
- **Lane B: Lean/Rust-to-Lean.** Future-only. It requires a separate
  source-correspondence boundary, proof-obligation extraction boundary, Lean
  toolchain lock, checker transcript grammar, and proof-authority nonclaims.
- **Lane C: COBALT-style containment.** Future-only. It requires a separate
  model-boundary contract, solver/certificate interpretation contract,
  containment-property scope, and correspondence statement from the HSAI gateway
  property to the COBALT-style model.

Phase 526 only opens the planning boundary for Lane A. It records that Lane B
and Lane C are not authorized by this phase.

## Required Future Lane A Bindings

A future implementation may construct backend execution candidate metadata only
if it binds:

- one Phase 525 import-review metadata digest;
- one Phase 525 import-review input digest;
- Phase 525 classification `ImportReviewBlockedNoIndependentRun`;
- one Phase 523 import-candidate metadata digest;
- one Phase 523 candidate digest;
- one Phase 523 validation digest;
- one Phase 523 quarantine-record digest;
- Phase 523 status `ExternalResultStatus::Quarantined`;
- Phase 523 requested boundary `ClaimBoundary::Level0DesignNote`;
- one Phase 521 external-reproduction metadata digest;
- one Phase 519 Level2 eligibility digest;
- one Phase 517 score-axis eligibility digest;
- one Phase 515 package digest;
- one Phase 513 materialized accepted-ledger artifact digest;
- one obligation artifact digest;
- one executable/toolchain descriptor digest;
- one command descriptor digest;
- one expected-output grammar digest;
- one timeout policy digest;
- one scratch-output-root policy digest;
- explicit nonclaims for independent reproduction, accepted formal evidence,
  Level2+ evidence, populated score axes, Lean proof, COBALT containment,
  Rust-to-Lean extraction, benchmark evidence, external audit, SOTA, semantic
  correctness, production readiness, full security, and action authority.

## Required Future Lane A Validation Rules

A future implementation must fail closed if:

- the Phase 525 review is not exact;
- the Phase 525 classification is not `ImportReviewBlockedNoIndependentRun`;
- the Phase 523 candidate is not exact;
- the Phase 523 candidate is not quarantined;
- the Phase 523 validator result is invalid or has issues;
- the obligation digest is zero or not bound to the existing tiny-Z3 source;
- the command descriptor is not fixed and single-purpose;
- any process-spawn request is not explicitly described by the descriptor;
- any network access is requested;
- any path is absolute, traversing, or repository-root writing;
- stdout/stderr retention is raw and unredacted;
- the expected-output grammar is missing;
- the timeout policy is missing;
- the result is classified as accepted evidence;
- any Level2+, score-axis, Lean, COBALT, Rust-to-Lean, benchmark, external
  audit, SOTA, semantic-correctness, production-readiness, full-security, or
  action-authority claim is set.

## Future Touch Surface

A future Lane A implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

That future implementation may introduce candidate metadata for a backend
execution crossing. It may not create accepted evidence, Level2+ evidence,
score-axis evidence, benchmark evidence, or proof authority.

## Backend Relationship

This boundary is the first controlled path toward backend execution after the
tiny-Z3 external import review lane. It does not itself run a backend.

If a future Lane A implementation succeeds under current evidence, it may
support this claim only:

```text
HSAI has a scoped backend-execution candidate lane for one tiny-Z3 gateway
obligation, with explicit command, timeout, output, and nonclaim boundaries.
```

That still would not be independent external reproduction, accepted formal
evidence, Level2+ evidence, populated score axes, Lean proof, COBALT
containment evidence, Rust-to-Lean proof, benchmark evidence, external audit,
SOTA, semantic correctness, production readiness, full security, or authority
to execute an action.

## Phase 527 Implementation Exit Criteria

A future Phase 527 may implement Lane A backend-execution candidate metadata
only if it:

- validates one exact Phase 525 review metadata record;
- records Lane A as the only future-open execution lane;
- records Lane B and Lane C as closed;
- binds obligation, toolchain, command, expected-output, timeout, and
  scratch-output-root policy digests;
- records that no backend has yet been run unless the future phase explicitly
  implements a hermetic execution result record under this boundary;
- rejects accepted evidence, Level2+ evidence, populated score axes,
  proof/checker/solver authority, Lean, COBALT, Rust-to-Lean, benchmark
  evidence, external audit, strong claims, and action authority in the metadata
  itself.
