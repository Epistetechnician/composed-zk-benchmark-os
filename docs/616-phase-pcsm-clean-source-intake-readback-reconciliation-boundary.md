# Phase 616 PCSM Clean-Source Intake Readback Reconciliation Boundary

State slice:
`phase-616-pcsm-clean-source-intake-readback-reconciliation-boundary`.

## Purpose

Define the smallest future reconciliation step after the
recoverable-ghost-states PCSM CL12 bounded-proof handoff became a clean,
committed source snapshot.

The source handoff coordinate is:

```text
repo=recoverable-ghost-states
commit=8b342fe159324395174a149052b9ea1d937a50ce
path=docs/pcsm-cl12-bounded-proof-handoff.md
sha256=93e07a250c9a6a5f530d02f07095074e7df8a5b5ce7e8e2dfa6e5feb376ea149
state_slice=pcsm-cl12-bounded-proof-package
schema=pcsm-cl12-bounded-proof-handoff-v1
```

This boundary exists only to reconcile that clean source coordinate through
the already-local Phase 140 through Phase 143 metadata path:

- Phase 140 PCSM bounded-proof intake metadata validation;
- Phase 141 admission-journal materialization;
- Phase 142 semantic readback boundary;
- Phase 143 semantic readback implementation.

It does not create a new evidence lane and does not import PCSM runtime code or
recoverable-ghost artifacts.

## Authorized Future Implementation

A following implementation slice may add local Rust source and tests under
`crates/hsai-agent-admission/src/lib.rs` only if it remains limited to:

- one typed clean-source reconciliation record over a valid
  `PcsmBoundedProofHandoffIntake`;
- source coordinate fields for repo label, commit, handoff path, handoff
  digest, schema, and state slice;
- digest checks proving that the reconciliation record preserves the Phase 140
  `source-handoff` artifact digest binding;
- local-only construction of one PCSM admission candidate with
  `AdmissionSourceKind::PcsmBoundedProofHandoff`;
- local-only admission-journal materialization and semantic readback checks
  using existing Phase 141 and Phase 143 APIs;
- fail-closed rejection when the source status is dirty, staged, uncommitted,
  digest-mismatched, threshold-promoted, authority-promoted, missing required
  nonclaims, or missing PCSM accepted/rejected count evidence;
- deterministic nonpromotion output stating that the reconciliation is
  `LocalOnly` metadata and not accepted evidence.

## Required Tests For A Future Implementation

The next implementation must include focused tests for:

- valid clean-source PCSM handoff metadata reaching candidate construction,
  local journal materialization, and semantic readback;
- digest mismatch between `source_handoff_sha256` and the required
  `source-handoff` artifact digest;
- dirty or staged source status rejection;
- missing source commit rejection;
- threshold admission or live external runtime promotion rejection;
- provider authority, production authority, raw provider payload, accepted
  ledger mutation, score-axis, Level2+, and official-submission rejection;
- source coordinate drift after candidate construction;
- semantic readback rejection when the materialized source digest index or
  nonclaim set is tampered while sidecar digests remain otherwise valid.

## Nonclaims

Phase 616 does not permit source-repo parsing, source-repo command execution,
filesystem reads from recoverable-ghost-states, PCSM runtime import or
vendoring, recoverable-ghost artifact import, generated committed bundles,
network access, credential reads, external result import, accepted Evidence
Ledger mutation, accepted external evidence, accepted formal evidence,
accepted independent external reproduction, Level2+ evidence, score-axis
population, proof artifact generation or promotion, checker transcript
generation or promotion, solver certificate generation or promotion, Lean
execution, SMT/Z3 execution, COBALT execution, Rust-to-Lean extraction,
benchmark submission, production deployment, external-audit claims,
semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, human-review acceptance claims, or authority to execute an action.

Clean-source PCSM reconciliation is not proof, not benchmark evidence, not
external reproduction, not accepted evidence, not Level2+ evidence, not
score-axis evidence, not semantic correctness, not production readiness, not
SOTA, and not full security.

## Exit Criteria

Phase 616 is complete when this boundary is documented and referenced from the
repo navigation/status files. Any implementation remains blocked until a
separate explicit implementation phase names the exact state slice it mutates.
