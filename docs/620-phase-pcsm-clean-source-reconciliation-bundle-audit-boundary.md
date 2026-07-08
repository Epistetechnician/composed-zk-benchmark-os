# Phase 620 PCSM Clean-Source Reconciliation Bundle Audit Boundary

State slice:
`phase-620-pcsm-clean-source-reconciliation-bundle-audit-boundary`.

## Purpose

Define the smallest future audit step after Phase 619 materialized a local
declared-file bundle for a valid Phase 617 PCSM clean-source reconciliation.

This boundary permits only an in-memory audit summary over an already
readback-valid Phase 619 output manifest and its source Phase 617
reconciliation record. It does not add new files, run source-repo commands, or
promote evidence.

## Authorized Future Implementation

A following implementation slice may add local Rust source and tests under
`crates/hsai-agent-admission/src/lib.rs` only if it remains limited to:

- one audit-summary type over a `PcsmCleanSourceReconciliationOutputManifest`
  and `PcsmCleanSourceIntakeReadbackReconciliation`;
- one fail-closed audit function that checks manifest/reconciliation digest
  agreement, coordinate digest agreement, intake digest agreement, candidate
  digest agreement, journal-tip digest agreement, claim-boundary text,
  nonclaims, and nonpromotion booleans;
- deterministic summary digesting;
- a local validity flag that means only “Phase 619 local bundle metadata is
  internally consistent”;
- explicit nonpromotion fields preserving:
  `accepted_evidence_created=false`, `level2_evidence_created=false`, and
  `score_axes_populated=false`.

## Required Tests For A Future Implementation

The next implementation must include focused tests for:

- a valid Phase 619 manifest and Phase 617 reconciliation producing a local
  audit summary;
- manifest/reconciliation digest drift rejection;
- coordinate digest drift rejection;
- nonclaim drift rejection;
- claim-boundary drift rejection;
- promotion drift rejection if accepted-evidence, Level2, or score-axis flags
  are changed.

## Nonclaims

Phase 620 does not permit Rust implementation code in this slice, Cargo
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

The future audit summary would be local metadata only. It would not be proof,
benchmark evidence, external reproduction, accepted evidence, Level2+
evidence, score-axis evidence, semantic correctness, production readiness,
SOTA, or full security.

## Exit Criteria

Phase 620 is complete when this boundary is documented and referenced from the
repo navigation/status files. Any implementation remains blocked until a
separate explicit implementation phase names the exact state slice it mutates.
