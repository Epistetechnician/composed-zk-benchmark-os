# Phase 627 PCSM Clean-Source Operator Replay Output Audit Boundary

State slice:
`phase-627-pcsm-clean-source-operator-replay-output-audit-boundary`.

## Purpose

Define the smallest future audit step after Phase 626 materialized a local
declared-file bundle for a Phase 624 validated PCSM clean-source operator
replay packet.

This boundary permits only an in-memory audit summary over an already
readback-valid Phase 626 output manifest, its source Phase 624 packet, and its
source Phase 624 validation result. It does not add new files, run
source-repo commands, import PCSM runtime behavior, import recoverable-ghost
artifacts, import external results, or promote evidence.

## Authorized Future Implementation

A following implementation slice may add local Rust source and tests under
`crates/hsai-agent-admission/src/lib.rs` only if it remains limited to:

- one audit-summary type over a
  `PcsmCleanSourceOperatorReplayOutputManifest`,
  `PcsmCleanSourceOperatorReplayPacket`, and
  `PcsmCleanSourceOperatorReplayValidation`;
- one fail-closed audit function that checks manifest schema, bundle ID,
  manifest/packet digest agreement, manifest/validation digest agreement,
  clean source coordinate digest agreement, operator-provenance digest
  agreement, source-observation digest agreement, command-observation digest
  agreement, artifact-retention digest agreement, redaction-report digest
  agreement, nonpromotion-report digest agreement, claim-boundary text,
  nonclaims, and nonpromotion booleans;
- deterministic summary digesting;
- a local validity flag that means only "Phase 626 local operator replay
  output metadata is internally consistent";
- explicit nonpromotion fields preserving:
  `pcsm_runtime_imported=false`,
  `recoverable_artifacts_imported=false`,
  `accepted_evidence_created=false`,
  `accepted_independent_external_reproduction=false`,
  `level2_evidence_created=false`, and
  `score_axes_populated=false`.

The future implementation may reuse the Phase 621 audit-summary style. It
must not add filesystem output, command runners, network APIs, process-spawn
APIs, source-repository parsers, PCSM runtime adapters, recoverable artifact
importers, or accepted-evidence append paths.

## Required Tests For A Future Implementation

The next implementation must include focused tests for:

- a valid Phase 626 manifest, Phase 624 packet, and Phase 624 validation
  producing a local audit summary;
- manifest/packet digest drift rejection;
- manifest/validation digest drift rejection;
- coordinate, provenance, source-observation, command-observation,
  artifact-retention, redaction, and nonpromotion digest drift rejection;
- claim-boundary drift rejection;
- nonclaim drift rejection;
- promotion drift rejection if any nonpromotion boolean is changed on the
  manifest, packet, or validation result.

## Nonclaims

Phase 627 does not permit Rust implementation code in this slice, Cargo
metadata changes, new dependencies, source-repo parsing, source-repo command
execution by HSAI, filesystem reads from recoverable-ghost-states, PCSM
runtime import or vendoring, recoverable-ghost artifact import, generated
committed bundles, package runtime additions, command-line tools, network
access, credential reads, external result import, accepted Evidence Ledger
mutation, accepted external evidence, accepted formal evidence, accepted
independent external reproduction, Level2+ evidence, score-axis population,
proof artifact generation or promotion, checker transcript generation or
promotion, solver certificate generation or promotion, Lean execution, SMT/Z3
execution, COBALT execution, Rust-to-Lean extraction, benchmark submission,
production deployment, external-audit claims, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global software-agent uniqueness claims, human-review acceptance
claims, or authority to execute an action.

The future audit summary would be local metadata only. It would not be PCSM
import, proof, benchmark evidence, external reproduction, accepted evidence,
Level2+ evidence, score-axis evidence, semantic correctness, production
readiness, SOTA, or full security.

## Exit Criteria

Phase 627 is complete when this boundary is documented and referenced from the
repo navigation/status files. Any implementation remains blocked until a
separate explicit implementation phase names the exact state slice it mutates.
