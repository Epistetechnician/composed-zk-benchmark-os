# Phase 291 HSAI Gateway Formal Backend Execution Authorization Output-Bundle Boundary

State slice: `Phase 291 HSAI gateway formal backend execution authorization output-bundle boundary`.

## Status

Complete for the docs-first authorization output-bundle boundary.

## Purpose

Phase 290 implemented inert execution-authorization metadata in
`hsai-agent-admission`. Phase 291 defines the future filesystem contract for
materializing that metadata into a local bundle.

This phase does not implement bundle materialization, does not execute a
backend, and does not authorize a runner.

## Future Declared Files

A future authorization output bundle should materialize only files under:

`gateway-formal-backend-authorization/`

The initial declared file set should be:

- `gateway-formal-backend-authorization/manifest.json`;
- `gateway-formal-backend-authorization/authorization-request.json`;
- `gateway-formal-backend-authorization/preflight-binding.json`;
- `gateway-formal-backend-authorization/transcript-binding.json`;
- `gateway-formal-backend-authorization/command-binding.json`;
- `gateway-formal-backend-authorization/environment-binding.json`;
- `gateway-formal-backend-authorization/quarantine-descriptor.json`;
- `gateway-formal-backend-authorization/operator-acknowledgement.json`;
- `gateway-formal-backend-authorization/nonclaims.md`.

Every declared file must have a sibling `.sha256` sidecar over exact file bytes.

No proof artifact, checker transcript, solver trace, prover log, raw stdout,
raw stderr, cache directory, accepted Evidence Ledger file, benchmark output,
external repo snapshot, or executable script may be declared in this bundle.

## Future Manifest Contract

The future manifest must bind:

- schema version;
- bundle id;
- state slice;
- creation timestamp;
- authorization request digest;
- Phase 283 preflight output-manifest digest;
- Phase 281 preflight request digest;
- Phase 281 preflight report digest;
- Phase 285 transcript metadata digest;
- Phase 287 transcript output-manifest digest;
- command descriptor digest;
- environment descriptor digest;
- artifact-root descriptor digest;
- authorization operator-acknowledgement digest;
- preflight redaction-policy digest;
- backend kind;
- tool name;
- tool version;
- toolchain lock digest;
- executable path label;
- argv digest;
- environment binding digest;
- quarantine descriptor digest;
- nonclaims digest;
- declared files;
- declared file digests;
- claim boundary;
- all nonpromotion flags set to false;
- required nonclaims.

The manifest must reject any digest-consistent semantic drift between the
manifest and the declared component files.

## Future Readback Rules

Future readback must reject:

- missing declared files;
- missing sidecars;
- stale sidecars;
- undeclared files;
- malformed JSON;
- non-UTF-8 Markdown;
- output-root symlinks;
- declared-file symlinks;
- declared-sidecar symlinks;
- declared directories where files are expected;
- protected output roots;
- repository-root output;
- accepted Evidence Ledger paths;
- benchmark-output paths;
- source-correspondence output-bundle paths;
- backend-run input-bundle paths;
- preflight output-bundle paths;
- transcript output-bundle paths;
- command-binding drift;
- argv drift;
- environment-binding drift;
- quarantine descriptor drift;
- operator-acknowledgement drift;
- claim-boundary drift;
- required-nonclaim drift;
- any backend-executed, command-spawned, proof-artifact, checker-transcript,
  checker-success, accepted-evidence, Level2+, score-axis, authority, semantic
  correctness, production-readiness, SOTA, or full-security flag.

## Future Required Tests

A future implementation phase must add tests for:

- valid authorization output-bundle materialization and readback;
- invalid authorization rejection before write;
- exact authorization-request digest binding;
- exact preflight binding;
- exact transcript binding;
- exact command binding;
- exact argv binding;
- exact environment binding;
- exact quarantine descriptor binding;
- exact operator acknowledgement binding;
- exact nonclaim Markdown binding;
- stale sidecar rejection;
- missing sidecar rejection;
- undeclared file rejection;
- malformed JSON rejection;
- protected output-root rejection;
- repository-root rejection;
- accepted Evidence Ledger output-root rejection;
- benchmark-output-root rejection;
- source-correspondence, backend-run, preflight, and transcript bundle-root
  rejection;
- declared-file symlink rejection;
- declared-sidecar symlink rejection;
- nonpromotion flag rejection;
- SOTA, full-security, semantic-correctness, and production-readiness claim
  rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem authorization bundle materialization;
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

Phase 292 implemented the local authorization output-bundle materializer and
readback validator in `hsai-agent-admission`.

The next slice should be docs-first:

`Phase 293 HSAI gateway formal backend execution quarantine artifact boundary`

It should define the future output quarantine artifact contract before any
runner can materialize process results. It should still not execute any command.
