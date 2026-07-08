# Phase 618 PCSM Clean-Source Reconciliation Materialization Boundary

State slice:
`phase-618-pcsm-clean-source-reconciliation-materialization-boundary`.

## Purpose

Define the smallest future materialization step after Phase 617 reconciled the
clean recoverable-ghost-states PCSM CL12 bounded-proof handoff through local
HSAI admission metadata and semantic readback.

The source coordinate remains:

```text
repo=recoverable-ghost-states
commit=8b342fe159324395174a149052b9ea1d937a50ce
path=docs/pcsm-cl12-bounded-proof-handoff.md
sha256=93e07a250c9a6a5f530d02f07095074e7df8a5b5ce7e8e2dfa6e5feb376ea149
state_slice=pcsm-cl12-bounded-proof-package
schema=pcsm-cl12-bounded-proof-handoff-v1
```

This boundary exists only to permit a future local audit bundle around a valid
`PcsmCleanSourceIntakeReadbackReconciliation`. The bundle may make the Phase
617 reconciliation result inspectable and readback-valid, but it may not import
PCSM artifacts or promote evidence.

## Authorized Future Implementation

A following implementation slice may add local Rust source and tests under
`crates/hsai-agent-admission/src/lib.rs` only if it remains limited to:

- one materialization request type for a caller-selected output root;
- one declared-file manifest for the Phase 617 reconciliation summary;
- deterministic JSON output for the reconciliation record;
- a nonclaim Markdown file derived from Phase 617 nonclaims;
- a validation report stating local metadata validity only;
- SHA-256 sidecars for every declared file;
- failure-atomic staged writes with protected-root, symlink, overwrite,
  undeclared-file, stale-digest, and malformed-JSON rejection matching the
  existing admission-journal bundle style;
- readback validation that recomputes manifest fields, declared-file digests,
  reconciliation digest, nonclaims, and validation-report content;
- explicit nonpromotion fields preserving:
  `accepted_evidence_created=false`, `level2_evidence_created=false`, and
  `score_axes_populated=false`.

The future implementation may reuse existing local output-root helpers,
duplicate-JSON rejection, digest helpers, and sidecar conventions already used
by admission-journal materialization.

## Required Tests For A Future Implementation

The next implementation must include focused tests for:

- valid Phase 617 reconciliation materializing and reading back from a local
  output root;
- output-root protection, symlink, and overwrite rejection;
- undeclared-file and missing-file rejection;
- stale sidecar digest rejection;
- manifest semantic drift rejection;
- reconciliation JSON drift rejection even when sidecars and manifest digests
  are updated consistently;
- nonclaim drift rejection;
- validation-report drift rejection;
- promotion drift rejection if any nonpromotion boolean is changed.

## Nonclaims

Phase 618 does not permit Rust implementation code in this slice, Cargo
metadata changes, new dependencies, source-repo parsing, source-repo command
execution, filesystem reads from recoverable-ghost-states, PCSM runtime import
or vendoring, recoverable-ghost artifact import, generated committed bundles,
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

Clean-source PCSM reconciliation materialization would be a local audit bundle
only. It would not be proof, benchmark evidence, external reproduction,
accepted evidence, Level2+ evidence, score-axis evidence, semantic
correctness, production readiness, SOTA, or full security.

## Exit Criteria

Phase 618 is complete when this boundary is documented and referenced from the
repo navigation/status files. Any implementation remains blocked until a
separate explicit implementation phase names the exact state slice it mutates.
