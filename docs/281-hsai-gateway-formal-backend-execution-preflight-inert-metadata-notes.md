# Phase 281 HSAI Gateway Formal Backend Execution Preflight Inert Metadata Notes

State slice: `Phase 281 HSAI gateway formal backend execution preflight inert metadata`.

## Status

Complete for inert backend execution preflight metadata.

## Purpose

Phase 280 defined the docs-first boundary for a future formal backend execution
preflight. Phase 281 implements that boundary as pure Rust metadata and
validation in `crates/hsai-agent-admission/src/lib.rs`.

This phase still does not execute a backend.

## Implemented Surface

Phase 281 adds:

- preflight schema, state-slice, and claim-boundary constants;
- backend preflight modes for Rust-to-Lean, SMT containment, COBALT
  containment, and federated dispatch planning;
- argv-only command descriptor metadata;
- bounded environment descriptor metadata;
- artifact-root descriptor metadata;
- operator acknowledgement metadata;
- redaction-policy metadata;
- execution preflight request and report metadata;
- deterministic digest helpers;
- fail-closed validation for command, environment, artifact root,
  acknowledgement, redaction, and nonpromotion flags;
- focused tests for the candidate-only path and adversarial drift.

## Accepted Valid Path

The valid path produces a `ReadyCandidateOnly` preflight report when all inputs
bind to the Phase 273 adapter request/report, Phase 276 run metadata, and Phase
278 backend-run bundle manifest.

The valid report sets:

- `backend_executed = false`;
- `proof_artifact_created = false`;
- `checker_transcript_created = false`;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- `grants_authority = false`.

## Rejection Coverage

The validator rejects:

- schema, id, state-slice, and digest drift;
- invalid backend-run artifact metadata;
- escalated backend-run manifests;
- shell-like argv fragments;
- credential-looking command values;
- wrong backend preflight mode;
- inherited full environment;
- undeclared or disallowed environment variables;
- credential-looking environment names or values;
- network-enabled policy;
- secret-enabled policy;
- unsafe artifact-root labels;
- overwrite requests;
- repository-root, protected-root, file, symlink, and symlink-parent artifact
  roots;
- accepted Evidence Ledger output paths;
- benchmark-output paths;
- source-correspondence bundle paths;
- Phase 278 backend-run input bundle paths;
- missing or mismatched operator acknowledgement;
- acknowledgement authority grants;
- raw prover, checker, solver, cache, source, ledger, benchmark, proof, or
  checker-artifact retention;
- backend execution flags;
- proof artifact creation flags;
- checker transcript creation flags;
- accepted evidence creation;
- Level2+ evidence creation;
- score-axis population;
- authority grants;
- semantic-correctness, production-readiness, SOTA, and full-security claims;
- forbidden public claim text;
- missing required nonclaims.

## Tests

Focused tests added:

- `gateway_formal_backend_preflight_accepts_inert_metadata_only`;
- `gateway_formal_backend_preflight_rejects_command_environment_and_root_drift`;
- `gateway_formal_backend_preflight_rejects_ack_redaction_and_claim_escalation`.

## Anti-Goals

This phase does not permit:

- command execution;
- process spawning;
- backend runner implementation;
- filesystem materialization for preflight output bundles;
- Cargo metadata changes;
- package runtime files;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifacts;
- generated checker transcripts;
- raw prover logs;
- raw checker logs;
- raw solver traces;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims;
- authority to execute an action.

## Next Slice

Implemented by Phase 282 as a docs-first materialized preflight output-bundle
boundary.

The next implementation slice, if explicitly authorized, should add local
filesystem materialization and readback for Phase 281 preflight request/report
metadata. It still should not execute any command, create proof artifacts,
create checker transcripts, or promote evidence.
