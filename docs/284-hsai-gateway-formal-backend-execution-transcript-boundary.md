# Phase 284 HSAI Gateway Formal Backend Execution Transcript Boundary

State slice: `Phase 284 HSAI gateway formal backend execution transcript boundary`.

## Status

Complete for the docs-first execution transcript boundary.

## Purpose

Phase 283 can materialize local preflight metadata. Phase 284 defines the future
boundary for backend execution transcript references and checker-output
admission rules.

This phase does not implement transcript metadata and does not execute a
backend.

## Future Transcript Scope

A future transcript lane may describe only redacted, bounded references to
execution diagnostics after a separate phase explicitly authorizes backend
execution.

The future transcript metadata may include:

- transcript id;
- backend kind;
- preflight bundle digest;
- command descriptor digest;
- toolchain lock digest;
- execution start and finish timestamps;
- exit status;
- checker status;
- redacted stdout summary digest;
- redacted stderr summary digest;
- proof artifact reference;
- checker transcript reference;
- proof obligation discharge summary;
- nondischarge summary;
- verifier trust-root disclosure;
- redaction report;
- claim boundary;
- nonclaims.

The metadata must distinguish:

- command execution;
- proof artifact creation;
- checker transcript creation;
- checker success;
- semantic correctness;
- accepted evidence eligibility.

Checker success alone must not imply semantic correctness.

## Reference Rules

Future proof and checker references must be:

- relative logical paths;
- digest-bound;
- redacted;
- declared in a manifest;
- free of raw transcript content;
- free of credentials or secrets;
- free of accepted Evidence Ledger JSON;
- free of benchmark-output payloads;
- free of external repo source snapshots;
- tied to the exact preflight bundle digest.

References must not be accepted when they point to:

- absolute paths;
- parent traversal;
- repository roots;
- protected roots;
- accepted Evidence Ledger paths;
- benchmark-output paths;
- source correspondence bundles;
- Phase 278 backend-run input bundles;
- Phase 283 preflight input bundles.

## Checker-Output Admission Rules

A future checker-output admission lane must require:

- a valid Phase 283 preflight bundle;
- explicit operator approval for execution;
- exact command descriptor match;
- exact toolchain lock match;
- exact source correspondence digest match;
- exact proof obligation set match;
- proof artifact digest when a proof is claimed;
- checker transcript digest when a checker result is claimed;
- redaction report proving no raw logs, secrets, or caches are retained;
- explicit nondischarged obligations when the checker is incomplete;
- explicit nonclaims for semantic correctness, production readiness, SOTA,
  breakthrough status, and full security.

The lane must reject:

- checker success without proof obligation coverage;
- proof artifact references without checker transcript references;
- checker transcript references without command/preflight binding;
- raw prover logs;
- raw checker logs;
- raw solver traces;
- retained proof assistant caches;
- accepted Evidence Ledger mutation;
- Level2+ evidence creation;
- score-axis population;
- authority grants;
- public claim escalation.

## Required Future Tests

A future implementation phase must add tests for:

- valid transcript reference metadata;
- missing preflight bundle digest rejection;
- command descriptor drift rejection;
- toolchain lock drift rejection;
- source correspondence digest drift rejection;
- proof obligation coverage drift rejection;
- proof artifact without checker transcript rejection;
- checker transcript without proof artifact rejection;
- raw stdout/stderr retention rejection;
- proof assistant cache retention rejection;
- credential-looking transcript summary rejection;
- absolute path rejection;
- parent traversal rejection;
- accepted Evidence Ledger path rejection;
- benchmark-output path rejection;
- Phase 283 input-bundle mutation path rejection;
- checker-success semantic-correctness claim rejection;
- Level2+ evidence escalation rejection;
- score-axis population rejection;
- authority grant rejection;
- forbidden public claim text rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem transcript bundle materialization code;
- command execution;
- process spawning;
- backend runner implementation;
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

Implemented by Phase 285 as inert backend execution transcript metadata in
`hsai-agent-admission`.

The next responsible slice is a docs-first boundary for transcript output-bundle
materialization. It should define declared files, digest sidecars, readback
checks, redaction-report rules, and drift tests. It still should not execute
any command or create proof/checker artifacts.
