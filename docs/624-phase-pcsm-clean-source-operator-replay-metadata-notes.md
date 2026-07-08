# Phase 624 PCSM Clean-Source Operator Replay Metadata Notes

State slice: `phase-624-pcsm-clean-source-operator-replay-metadata`.

## Purpose

Implement the local in-memory metadata validator authorized by
`docs/623-phase-pcsm-clean-source-operator-replay-boundary.md`.

This phase validates a caller-provided operator replay packet for the clean
recoverable-ghost-states PCSM source coordinate. It does not execute
recoverable-ghost-states commands, parse the source repository, import PCSM
runtime behavior, import recoverable artifacts, materialize a filesystem
packet, import external results, or promote evidence.

## Implemented Surface

The implementation adds these public Rust surfaces under
`crates/hsai-agent-admission/src/lib.rs`:

- `PcsmCleanSourceOperatorReplayProvenance`;
- `PcsmCleanSourceOperatorReplaySourceObservation`;
- `PcsmCleanSourceOperatorReplayCommandObservation`;
- `PcsmCleanSourceOperatorReplayArtifactRetentionDeclaration`;
- `PcsmCleanSourceOperatorReplayRedactionReport`;
- `PcsmCleanSourceOperatorReplayNonpromotionReport`;
- `PcsmCleanSourceOperatorReplayPacket`;
- `PcsmCleanSourceOperatorReplayValidation`;
- `PcsmCleanSourceOperatorReplayError`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_SCHEMA_VERSION`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_VALIDATION_SCHEMA_VERSION`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_STATE_SLICE`;
- `PCSM_CLEAN_SOURCE_OPERATOR_REPLAY_CLAIM_BOUNDARY`;
- `pcsm_clean_source_operator_replay_declared_files`;
- `validate_pcsm_clean_source_operator_replay_packet`.

The validator checks:

- exact clean source coordinate binding;
- Phase 622 closure-report digest binding;
- optional Phase 621 audit digest binding;
- operator provenance fields and toolchain-version metadata;
- source observation agreement with the clean coordinate;
- clean source status;
- command IDs, command lines, time windows, exit statuses, skipped flags,
  result summaries, and transcript digests;
- retained-artifact relative path safety and digest presence;
- forbidden raw log, provider response, accepted-evidence, Level2, score-axis,
  proof, checker, solver, benchmark, and production artifact retention;
- redaction-report safety;
- nonpromotion booleans;
- logical packet role list and deterministic role digests;
- required PCSM nonclaims.

The validation result records only that the packet is local operator replay
metadata. It records all promotion booleans as false.

## Validation Coverage

Focused tests cover:

- valid operator replay metadata validation;
- Phase 622 digest drift, coordinate drift, source observation drift, and dirty
  source status rejection;
- command-line, command-window, skipped, failed, missing-summary, and missing
  transcript-digest rejection;
- unsafe retained-artifact paths, missing retained-artifact digests, and
  forbidden artifact retention;
- redaction-report drift, nonpromotion drift, claim-boundary drift,
  declared-role digest drift, and missing nonclaim rejection.

## Nonclaims

Phase 624 does not permit Cargo metadata changes, new dependencies,
source-repo parsing, source-repo command execution by HSAI, filesystem reads
from recoverable-ghost-states, PCSM runtime import or vendoring,
recoverable-ghost artifact import, generated committed bundles, filesystem
packet materialization, package runtime additions, command-line tools, network
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

Phase 624 is not PCSM import, not external reproduction, not accepted evidence,
not Level2+ evidence, not score-axis evidence, not proof, not semantic
correctness, not production readiness, not SOTA, and not full security.

## Exit Criteria

Phase 624 is complete when the focused operator replay metadata tests, the
`hsai-agent-admission` package tests, clippy for `hsai-agent-admission`, repo
claim-boundary docs tests, repo hygiene tests, and diff hygiene pass.
