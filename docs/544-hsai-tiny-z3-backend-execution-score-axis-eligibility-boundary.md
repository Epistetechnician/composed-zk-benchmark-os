# Phase 544 HSAI Tiny Z3 Backend Execution Score Axis Eligibility Boundary

State slice: `Phase 544 HSAI tiny Z3 backend execution score-axis eligibility boundary`.

Phase 544 defines the docs-first boundary for future score-axis eligibility
over the Phase 543 local backend-execution accepted-evidence package metadata:

```text
Phase 543 local backend-execution package metadata
  + explicit score-axis eligibility policy
  -> score-axis eligibility metadata
```

This phase does not implement Rust code, change Cargo metadata, write files,
create score-axis metadata, populate score axes, create accepted formal
evidence, create Level2+ evidence, generate proof artifacts, generate checker
transcripts, generate solver certificates, run Lean, run new SMT, run COBALT,
run Rust-to-Lean extraction, create benchmark evidence, claim semantic
correctness, claim production readiness, claim SOTA, claim breakthrough status,
claim full security, claim external audit status, claim independent external
reproduction, or grant authority to execute an action.

## Current Score Owner Surface

The existing scoring owner is `zkbench-core`:

- `ScoreReport`;
- `score_report_from_evidence`;
- `score_report_from_local_mutation_evidence`;
- `validate_score_report`.

Current scoring policy already rejects populated score axes at local claim
boundaries. `ScoreReport` may exist as a conservative local summary container,
but local-only `Level1LocalReplay` evidence must leave performance,
correctness, soundness-failure detection, recursion-stress, formal-evidence,
reproducibility, and adapter-portability axes unpopulated.

Phase 543 package metadata is local accepted-evidence package metadata only. It
does not satisfy the evidence requirements for populated score axes.

## Future Allowed Touch Surface

A future implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

No Cargo metadata change, external dependency, feature flag, binary, script,
runner, process-spawn API, network API, official submission API, solver API,
proof-assistant API, benchmark runner, score-axis output writer, or backend
execution output is authorized by this boundary.

## Future Eligibility Meaning

A future score-axis eligibility record may classify one Phase 543 package as:

- `score_axes_blocked_local_only`;
- `score_axes_waiting_for_level2_benchmark`;
- `score_axes_waiting_for_backend_proof`;
- `score_axes_waiting_for_external_reproduction`;
- `score_axes_eligible_after_future_evidence`.

Under current evidence, the only valid classification is:

```text
score_axes_blocked_local_only
```

The future metadata may bind why score axes remain blocked, but must not
populate any `ScoreReport` axis from Phase 543 local-only package metadata.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 543 local package metadata digest;
- one Phase 543 package input digest;
- the Phase 543 digest-binding map digest;
- the Phase 543 id-binding map digest;
- the Phase 543 label-binding map digest;
- the Phase 543 package policy digest;
- the Phase 543 package nonclaim digest;
- the Phase 543 package cap digest;
- the Phase 543 evidence class;
- the Phase 543 claim boundary;
- the Phase 541 materialized ledger artifact digest;
- the Phase 541 materialized append report digest;
- the Phase 541 materialized artifact byte length;
- the Phase 539 appended evidence class;
- the Phase 539 appended claim boundary;
- the inherited Phase 535/533/531/529/527 digest set;
- the score owner id `zkbench-core`;
- the score report type `ScoreReport`;
- the score validator `validate_score_report`;
- the eligibility policy digest;
- the score-axis blocker digest;
- the score-axis nonpopulation digest.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 543 package record is not exact;
- the Phase 543 evidence class is not `LocalReplay`;
- the Phase 543 claim boundary is not `Level1LocalReplay`;
- the Phase 543 package created accepted formal evidence;
- the Phase 543 package created Level2+ evidence;
- the Phase 543 package populated score axes;
- the Phase 543 package promoted Lean/SMT/COBALT/Rust-to-Lean evidence;
- the Phase 543 package promoted benchmark evidence, external audit evidence,
  or independent external reproduction;
- the score owner is not `zkbench-core`;
- the score report type is not `ScoreReport`;
- the score validator is not `validate_score_report`;
- any score axis is populated from Phase 543 local-only package metadata;
- the eligibility policy, blocker, or nonpopulation digest is missing or
  drifts;
- the metadata cites Lean/new-SMT/COBALT/Rust-to-Lean evidence;
- the metadata cites benchmark evidence, external audit evidence, or
  independent external reproduction;
- the metadata claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority.

## Backend Relationship

This boundary is not backend execution. It is not Lean, SMT, COBALT, or
Rust-to-Lean evidence. It is not proof authority. It is not benchmark evidence.
It is not score-axis evidence. It is not external audit evidence.

If a future eligibility record succeeds under current evidence, it may support
this claim only:

```text
HSAI classifies the local Phase 543 backend-execution package as score-axis
ineligible until Level2+ benchmark evidence, backend proof evidence, or
independent external reproduction exists.
```

That still would not be accepted formal evidence, Level2+ evidence, score-axis
population, Lean proof, SMT proof authority, COBALT containment evidence,
Rust-to-Lean proof, checker transcript authority, solver certificate authority,
benchmark evidence, external audit, independent external reproduction, SOTA,
semantic correctness, production readiness, full security, or authority to
execute an action.

## Phase 545 Implementation Exit Criteria

A future Phase 545 implementation satisfies this boundary only if it:

- touches only the allowed files listed above;
- performs no process or network calls;
- writes no score-axis artifact files;
- validates one exact Phase 543 package metadata record;
- binds the `zkbench-core` score owner, `ScoreReport`, and
  `validate_score_report`;
- records the current classification as `score_axes_blocked_local_only`;
- records every score axis as unpopulated;
- rejects formal evidence, Level2+, populated score axes, proof/checker/solver
  authority, Lean/SMT/COBALT/Rust-to-Lean evidence, benchmark evidence,
  external audit, independent external reproduction, strong claims, and action
  authority in the metadata itself.
