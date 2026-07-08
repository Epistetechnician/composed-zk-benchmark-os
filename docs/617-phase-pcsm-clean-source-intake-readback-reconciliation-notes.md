# Phase 617 PCSM Clean-Source Intake Readback Reconciliation Notes

State slice:
`phase-617-pcsm-clean-source-intake-readback-reconciliation`.

## Purpose

Implement the narrow local reconciliation authorized by Phase 616 for the clean
recoverable-ghost-states PCSM CL12 bounded-proof handoff coordinate:

```text
repo=recoverable-ghost-states
commit=8b342fe159324395174a149052b9ea1d937a50ce
path=docs/pcsm-cl12-bounded-proof-handoff.md
sha256=93e07a250c9a6a5f530d02f07095074e7df8a5b5ce7e8e2dfa6e5feb376ea149
state_slice=pcsm-cl12-bounded-proof-package
schema=pcsm-cl12-bounded-proof-handoff-v1
```

The implementation remains entirely local. It reconciles a valid
`PcsmBoundedProofHandoffIntake` through the existing candidate, admission
journal, materialization, and semantic readback APIs. It does not parse or read
the source repository.

## Implemented Surface

Phase 617 adds:

- `PcsmCleanSourceHandoffCoordinate`, a typed source-coordinate record with a
  deterministic digest;
- `PcsmCleanSourceIntakeReadbackReconciliation`, a deterministic nonpromotion
  reconciliation summary;
- `PcsmCleanSourceReconciliationError`, a fail-closed rejection taxonomy;
- `reconcile_pcsm_clean_source_intake_readback`, which checks coordinate,
  intake, candidate, journal, materialized manifest, and readback manifest
  agreement.

The reconciliation rejects coordinate drift, dirty or staged source status,
invalid intake metadata, candidate drift, candidate claim escalation, authority
or promotion requests, missing `source-handoff` or
`pcsm-bounded-proof-intake` digests, invalid journals, non-accepted journal
decisions, accepted-envelope retention, manifest/readback drift, manifest
journal mismatch, claim-boundary drift, and missing admission-journal
nonclaims.

## Validation

Focused tests cover:

- clean-source PCSM metadata reaching candidate construction, accepted local
  journal decision, materialization, readback, and reconciliation;
- coordinate digest drift;
- dirty source intake rejection;
- candidate claim-boundary and mutation-promotion rejection;
- readback manifest drift rejection.

These tests build on the existing Phase 140 through Phase 143 PCSM intake and
journal readback tests.

## Nonclaims

Phase 617 does not permit source-repo parsing, source-repo command execution,
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

Clean-source PCSM reconciliation is local admission metadata only. It is not
proof, not benchmark evidence, not external reproduction, not accepted
evidence, not Level2+ evidence, not score-axis evidence, not semantic
correctness, not production readiness, not SOTA, and not full security.
