# Phase 520 HSAI Tiny Z3 External Reproduction Provenance Boundary

State slice: `Phase 520 HSAI tiny Z3 external reproduction provenance boundary`.

Phase 520 defines the docs-first boundary for future external-reproduction and
provenance metadata over the Phase 519 Level2 eligibility record:

```text
Phase 519 Level2 eligibility metadata
  + zkbench-core artifact capture / provenance / external result import contracts
  -> future local external-reproduction provenance metadata
```

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, run an external replay, run a backend, run Lean, run
SMT/Z3, run COBALT, run Rust-to-Lean extraction, create proof artifacts,
create checker transcripts, create solver certificates, mutate the accepted
Evidence Ledger, change accepted append policy, create accepted formal
evidence, create Level2+ evidence, populate score axes, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, claim external audit status, or
grant authority to execute an action.

## Existing External-Reproduction Owner Surface

The existing owner surface is `zkbench-core`:

- `build_default_artifact_capture_contract`;
- `validate_artifact_capture_contract`;
- `ArtifactCaptureContract`;
- `build_default_provenance_contract`;
- `validate_provenance_contract`;
- `validate_external_run_provenance_draft`;
- `ExternalRunProvenanceDraft`;
- `build_default_external_result_import_schema`;
- `validate_external_result_import_schema`;
- `validate_external_result_candidate`;
- `ExternalResultCandidate`;
- `ExternalResultStatus`;
- `ExternalResultQuarantineRecord`.

These surfaces define contracts and validation for future external-result
imports. They do not, by themselves, run an external backend, prove semantic
correctness, create accepted formal evidence, create Level2+ evidence, or
populate score axes.

## Future Allowed Touch Surface

A future implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

This boundary does not authorize new dependencies, Cargo metadata edits,
binaries, scripts, process-spawn APIs, network APIs, official submission APIs,
solver APIs, proof-assistant APIs, benchmark runners, score-axis writers, or
accepted-ledger writers.

## Future Metadata Meaning

A future HSAI tiny-Z3 external-reproduction provenance record may classify one
Phase 519 record as:

- `external_reproduction_blocked_no_independent_run`;
- `external_reproduction_waiting_for_artifact_capture`;
- `external_reproduction_waiting_for_provenance_review`;
- `external_reproduction_waiting_for_import_validation`;
- `external_reproduction_ready_for_future_human_review_only`.

Under current evidence, the only valid HSAI classification is:

```text
external_reproduction_blocked_no_independent_run
```

This classification may record the exact missing external-reproduction inputs,
but it must not represent a local Z3 run as an independent external
reproduction and must not convert local metadata into Level2 actual evidence.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 519 Level2 eligibility digest;
- one Phase 519 Level2 eligibility input digest;
- the Phase 519 digest-binding map digest;
- the Phase 519 id-binding map digest;
- the Phase 519 label-binding map digest;
- the Phase 519 classification `level2_blocked_local_only`;
- the Phase 519 Level2 blocker digest;
- the Phase 519 Level2 nonpromotion digest;
- the Phase 517 score-axis eligibility digest;
- the Phase 517 score-axis nonpopulation digest;
- the Phase 515 package digest;
- the Phase 515 evidence class `LocalReplay`;
- the Phase 515 claim boundary `Level1LocalReplay`;
- the Phase 513 materialized ledger artifact digest;
- the Phase 405 fixed local Z3 output readback artifact identity when
  available through inherited Phase 515/513 bindings;
- the external owner id `zkbench-core`;
- the artifact-capture contract digest;
- the provenance contract digest;
- the external-result import schema digest;
- the required provenance-field digest;
- the current external-reproduction blocker digest;
- the external-reproduction nonpromotion digest.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 519 record is not exact;
- the Phase 519 classification is not `level2_blocked_local_only`;
- the Phase 519 report boundary is not `ClaimBoundary::Level0DesignNote`;
- the Phase 519 record creates Level2 evidence;
- any Phase 517 score axis is populated;
- the Phase 515 package record is not exact;
- the Phase 515 evidence class is not `LocalReplay`;
- the Phase 515 claim boundary is not `Level1LocalReplay`;
- the external owner is not `zkbench-core`;
- the artifact-capture contract digest is missing or drifts;
- the provenance contract digest is missing or drifts;
- the external-result import schema digest is missing or drifts;
- required provenance fields are missing from the future metadata;
- the metadata asserts independent external reproduction without explicit
  artifact, provenance, and import-validation digest bindings;
- the metadata cites accepted formal evidence, Level2+ evidence, score-axis
  evidence, benchmark evidence, external audit evidence, proof authority,
  checker transcript authority, solver certificate authority, Lean evidence,
  SMT proof authority, COBALT evidence, or Rust-to-Lean proof;
- the metadata claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority.

## Backend Relationship

This boundary is not a new backend run and not an external reproduction. Phase
404 already performed a quarantined fixed local Z3 execution for one tiny
digest-binding property, and Phase 405 already materialized/read back that
output bundle. Those artifacts remain local and nonpromoted.

This boundary does not authorize another Z3 run, Lean execution, COBALT
execution, Rust-to-Lean extraction, external replay execution, proof artifact
generation, checker transcript generation, solver certificate generation,
benchmark submission, or score-axis population.

If a future external-reproduction provenance record succeeds under current
evidence, it may support this claim only:

```text
HSAI records that the local tiny-Z3 package still lacks independent external
reproduction and identifies the artifact-capture, provenance, and import
validation contracts required before future human Level2 review.
```

That still would not be independent external reproduction, Level2+ evidence,
accepted formal evidence, score-axis evidence, Lean proof, SMT proof authority,
COBALT containment evidence, Rust-to-Lean proof, checker transcript authority,
solver certificate authority, benchmark evidence, external audit, SOTA,
semantic correctness, production readiness, full security, or authority to
execute an action.

## Phase 521 Implementation Exit Criteria

Phase 521 implemented local external-reproduction provenance metadata in
`docs/521-hsai-tiny-z3-external-reproduction-provenance-metadata-notes.md`.
The implementation met this boundary by:

- touching only the allowed files listed above;
- performing no process or network calls;
- writing no external-reproduction artifact files;
- writing no Level2 artifact files;
- writing no score-axis artifact files;
- validating one exact Phase 519 Level2 eligibility metadata record;
- binding the `zkbench-core` artifact-capture, provenance, and external-result
  import owner surface;
- recording the current HSAI classification as
  `external_reproduction_blocked_no_independent_run`;
- recording every required external-reproduction input as missing;
- rejecting accepted formal evidence, Level2+ evidence, populated score axes,
  proof/checker/solver authority, backend execution evidence, benchmark
  evidence, external audit, strong claims, and action authority in the metadata
  itself.
