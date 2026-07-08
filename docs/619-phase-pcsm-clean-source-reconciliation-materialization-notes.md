# Phase 619 PCSM Clean-Source Reconciliation Materialization Notes

State slice:
`phase-619-pcsm-clean-source-reconciliation-materialization`.

## Purpose

Implement the local materialized audit bundle authorized by Phase 618 for a
valid Phase 617 `PcsmCleanSourceIntakeReadbackReconciliation`.

The bundle makes the clean-source PCSM reconciliation inspectable through a
readback-valid local directory. It does not parse the source repository, import
PCSM runtime code, import recoverable-ghost artifacts, or promote evidence.

## Implemented Surface

Phase 619 adds:

- `PcsmCleanSourceReconciliationMaterializationRequest`;
- `PcsmCleanSourceReconciliationOutputManifest`;
- `PcsmCleanSourceReconciliationValidationReport`;
- `materialize_pcsm_clean_source_reconciliation_bundle`;
- `read_pcsm_clean_source_reconciliation_bundle`.

The output bundle declares:

- `pcsm-clean-source-reconciliation/manifest.json`;
- `pcsm-clean-source-reconciliation/reconciliation.json`;
- `pcsm-clean-source-reconciliation/nonclaims.md`;
- `pcsm-clean-source-reconciliation/validation-report.json`;
- SHA-256 sidecars for each declared file.

Readback rejects undeclared files, missing declared files, stale sidecar
digests, malformed JSON, manifest semantic drift, reconciliation promotion
drift, nonclaim drift, and validation-report drift.

## Validation

Focused tests cover:

- valid Phase 617 reconciliation materialization and readback;
- output-root overwrite and protected-root rejection;
- promotion drift rejection before write;
- undeclared-file rejection;
- stale sidecar digest rejection;
- reconciliation semantic drift rejection after rehashing;
- nonclaim semantic drift rejection after rehashing.

## Nonclaims

Phase 619 does not permit Cargo metadata changes, new dependencies,
source-repo parsing, source-repo command execution, filesystem reads from
recoverable-ghost-states, PCSM runtime import or vendoring, recoverable-ghost
artifact import, generated committed bundles, package runtime additions,
command-line tools, network access, credential reads, external result import,
accepted Evidence Ledger mutation, accepted external evidence, accepted formal
evidence, accepted independent external reproduction, Level2+ evidence,
score-axis population, proof artifact generation or promotion, checker
transcript generation or promotion, solver certificate generation or
promotion, Lean execution, SMT/Z3 execution, COBALT execution, Rust-to-Lean
extraction, benchmark submission, production deployment, external-audit
claims, semantic-correctness claims, production-readiness claims, SOTA claims,
breakthrough claims, full-security claims, global software-agent uniqueness
claims, human-review acceptance claims, or authority to execute an action.

Clean-source PCSM reconciliation materialization is a local audit bundle only.
It is not proof, benchmark evidence, external reproduction, accepted evidence,
Level2+ evidence, score-axis evidence, semantic correctness, production
readiness, SOTA, or full security.
