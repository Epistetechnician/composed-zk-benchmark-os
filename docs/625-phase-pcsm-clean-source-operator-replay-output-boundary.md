# Phase 625 PCSM Clean-Source Operator Replay Output Boundary

State slice: `phase-625-pcsm-clean-source-operator-replay-output-boundary`.

## Purpose

Define the docs-first boundary for a future local output bundle around one
Phase 624 validated PCSM clean-source operator replay packet.

The current local chain is:

```text
Phase 623 operator replay packet boundary
  -> Phase 624 in-memory operator replay metadata validator
  -> future Phase 626 materialized local output bundle
```

This boundary exists only to make a Phase 624 validated packet inspectable and
readback-valid under a caller-selected local output root. It does not execute
recoverable-ghost-states commands, parse the source repository, import PCSM
runtime behavior, import recoverable artifacts, import external results, or
promote evidence.

## Authorized Future Implementation

A following implementation slice may add local Rust source and focused tests
under `crates/hsai-agent-admission/src/lib.rs` only if it remains limited to:

- one materialization request type for a caller-selected output root;
- one declared-file manifest for the Phase 624 packet and validation result;
- deterministic JSON output for:
  - the operator replay packet;
  - the validation result;
  - the clean source coordinate;
  - operator provenance;
  - source observation;
  - command observations;
  - artifact-retention declaration;
  - redaction report;
  - nonpromotion report;
- a nonclaim Markdown file derived from the packet nonclaims;
- a validation report stating local metadata validity only;
- SHA-256 sidecars for every declared file;
- failure-atomic staged writes with protected-root, symlink, overwrite,
  undeclared-file, stale-digest, malformed-JSON, duplicate-JSON, and semantic
  drift rejection matching the existing admission-journal and PCSM
  reconciliation bundle styles;
- readback validation that recomputes manifest fields, declared-file digests,
  packet digest, validation digest, nonclaims, redaction, nonpromotion, and
  validation-report content;
- explicit nonpromotion fields preserving:
  `pcsm_runtime_imported=false`,
  `recoverable_artifacts_imported=false`,
  `accepted_evidence_created=false`,
  `accepted_independent_external_reproduction=false`,
  `level2_evidence_created=false`, and
  `score_axes_populated=false`.

The future implementation may reuse the existing local output-root,
declared-file, digest, sidecar, duplicate-JSON, and nonpromotion conventions
already used by admission-journal and Phase 619 materialization. It must not
add dependencies, command runners, network APIs, process-spawn APIs,
source-repository parsers, or accepted-evidence append paths.

## Required Tests For A Future Implementation

The next implementation must include focused tests for:

- valid Phase 624 packet materializing and reading back from a local output
  root;
- output-root protection, symlink, overwrite, and file-root rejection;
- undeclared-file, missing-file, stale sidecar digest, malformed JSON, and
  duplicate JSON rejection;
- packet semantic drift rejection even when sidecars and manifest digests are
  updated consistently;
- validation-result drift rejection;
- clean source coordinate drift rejection;
- operator provenance, source observation, command observation,
  artifact-retention, redaction, and nonpromotion drift rejection;
- nonclaim drift rejection;
- promotion drift rejection if any nonpromotion boolean is changed.

## Nonclaims

Phase 625 does not permit Rust implementation code in this slice, Cargo
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

Phase 625 is a boundary contract only. A future output bundle would still be
local operator replay metadata only. It would not be PCSM import, external
reproduction, accepted evidence, Level2+ evidence, score-axis evidence, proof,
semantic correctness, production readiness, SOTA, or full security.

## Exit Criteria

Phase 625 is complete when this boundary is documented and referenced from the
repo navigation/status files. Any implementation remains blocked until a
separate explicit implementation phase names the exact state slice it mutates.
