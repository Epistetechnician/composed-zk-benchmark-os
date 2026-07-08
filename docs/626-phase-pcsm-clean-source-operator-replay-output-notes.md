# Phase 626 PCSM Clean-Source Operator Replay Output Notes

State slice: `phase-626-pcsm-clean-source-operator-replay-output`.

## Purpose

Materialize and read back a caller-owned local output bundle around one Phase
624 validated PCSM clean-source operator replay packet.

The local chain is now:

```text
Phase 623 operator replay packet boundary
  -> Phase 624 in-memory operator replay metadata validator
  -> Phase 625 output bundle boundary
  -> Phase 626 materialized local output bundle
```

This phase makes a validated Phase 624 packet inspectable as local metadata
only. It does not execute recoverable-ghost-states commands, parse the source
repository, import PCSM runtime behavior, import recoverable artifacts, import
external results, or promote evidence.

## Implemented Surface

Phase 626 adds the following local Rust surface under
`crates/hsai-agent-admission/src/lib.rs`:

- `PcsmCleanSourceOperatorReplayOutputRequest`;
- `PcsmCleanSourceOperatorReplayOutputManifest`;
- `PcsmCleanSourceOperatorReplayOutputValidationReport`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_OUTPUT_SCHEMA_VERSION`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_OUTPUT_VALIDATION_SCHEMA_VERSION`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_OUTPUT_STATE_SLICE`;
- `materialize_pcsm_clean_source_operator_replay_bundle`;
- `read_pcsm_clean_source_operator_replay_bundle`.

The materialized bundle writes the declared
`pcsm-clean-source-operator-replay/*` files for:

- manifest;
- Phase 624 packet;
- Phase 624 validation result;
- clean source coordinate;
- operator provenance;
- source observation;
- command observations;
- artifact-retention declaration;
- redaction report;
- nonpromotion report;
- nonclaim Markdown;
- validation report.

Every declared file gets a SHA-256 sidecar. The manifest binds packet,
validation, coordinate, operator-provenance, source-observation, command,
artifact-retention, redaction, nonpromotion, declared-file, nonclaim, and
nonpromotion-flag state.

## Readback Validation

Readback rejects:

- symlinked output roots, bundle directories, declared files, or sidecars;
- file output roots;
- undeclared files;
- missing declared files or sidecars;
- stale sidecar digests;
- malformed declared JSON;
- semantic drift between split JSON files and the packet;
- packet, validation, manifest, nonclaim, or validation-report drift.

The validation report states only local metadata validity and repeats the
nonpromotion fields:

- `pcsm_runtime_imported=false`;
- `recoverable_artifacts_imported=false`;
- `accepted_evidence_created=false`;
- `accepted_independent_external_reproduction=false`;
- `level2_evidence_created=false`;
- `score_axes_populated=false`.

## Validation Coverage

Focused tests cover:

- valid bundle materialization and readback;
- output-root overwrite and protected-root rejection;
- validation-result promotion drift rejection;
- undeclared-file rejection;
- stale packet sidecar digest rejection;
- packet semantic drift rejection even after file and manifest digest updates;
- validation semantic drift rejection after file and manifest digest updates.

## Nonclaims

Phase 626 does not permit Cargo metadata changes, new dependencies,
source-repo parsing, source-repo command execution by HSAI, filesystem reads
from recoverable-ghost-states, PCSM runtime import or vendoring,
recoverable-ghost artifact import, generated committed bundles, package
runtime additions, command-line tools, network access, credential reads,
external result import, accepted Evidence Ledger mutation, accepted external
evidence, accepted formal evidence, accepted independent external
reproduction, Level2+ evidence, score-axis population, proof artifact
generation or promotion, checker transcript generation or promotion, solver
certificate generation or promotion, Lean execution, SMT/Z3 execution, COBALT
execution, Rust-to-Lean extraction, benchmark submission, production
deployment, external-audit claims, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, human-review acceptance
claims, or authority to execute an action.

Phase 626 is a local output-bundle surface only. The bundle is not PCSM import,
external reproduction, accepted evidence, Level2+ evidence, score-axis
evidence, proof, semantic correctness, production readiness, SOTA, or full
security.

## Exit Criteria

Phase 626 is complete when the bundle materializer and readback validator are
implemented, focused tests pass, and the repo navigation/status files name the
state slice and the remaining nonclaims.
