# Phase 301 HSAI Gateway Formal Backend Quarantine Validation-Summary Output-Bundle Boundary

State slice: `Phase 301 HSAI gateway formal backend quarantine validation-summary output-bundle boundary`.

## Status

Complete for the docs-first validation-summary output-bundle boundary.

## Purpose

Phase 300 implemented a pure-data validation summary for the local quarantine
output-bundle readback and drift-test surface. Phase 301 defines the future
filesystem boundary for materializing that summary as a local declared-file
bundle.

This phase does not add Rust code. It defines the future implementation
contract.

## Future Bundle Shape

A future implementation may materialize a local bundle under:

`gateway-formal-backend-quarantine-validation-summary/*`

The future declared files should be:

- `gateway-formal-backend-quarantine-validation-summary/summary.json`;
- `gateway-formal-backend-quarantine-validation-summary/source-manifest.json`;
- `gateway-formal-backend-quarantine-validation-summary/coverage-labels.json`;
- `gateway-formal-backend-quarantine-validation-summary/nonclaims.md`;
- `gateway-formal-backend-quarantine-validation-summary/validation-report.json`;
- `gateway-formal-backend-quarantine-validation-summary/manifest.json`.

Each declared file must have a sibling `.sha256` sidecar.

The future bundle manifest should include:

- schema version;
- bundle id;
- state slice;
- created-at timestamp supplied by the caller;
- validation summary digest;
- source quarantine output manifest digest;
- source quarantine artifact digest;
- declared files;
- declared file digests;
- claim boundary;
- local-regression-only flag;
- no backend-executed flag;
- no proof-artifact-promoted flag;
- no checker-transcript-promoted flag;
- no accepted-evidence-mutation flag;
- no Level2+ evidence flag;
- no score-axis population flag;
- no semantic-correctness claim flag;
- no production-readiness claim flag;
- no SOTA claim flag;
- no breakthrough claim flag;
- no full-security claim flag;
- no action-authority flag;
- required nonclaim labels.

## Future Readback Rules

The future reader must:

- reject protected output roots;
- reject existing output roots unless explicit overwrite is set;
- use a staging directory before final rename;
- reject output-root symlinks;
- reject bundle-directory symlinks;
- reject declared-file symlinks;
- reject declared-sidecar symlinks;
- reject missing declared files;
- reject missing declared sidecars;
- reject stale sidecars;
- reject undeclared files;
- reject undeclared directories;
- reject malformed declared JSON;
- reject summary/source-manifest digest drift;
- reject coverage-label drift;
- reject nonclaim Markdown drift;
- reject validation-report drift;
- reject manifest claim-boundary drift;
- reject manifest accepted-evidence drift;
- reject manifest Level2+ drift;
- reject manifest score-axis drift;
- reject manifest authority drift;
- reject raw proof artifacts;
- reject raw checker transcripts;
- reject raw solver traces;
- reject accepted Evidence Ledger files;
- reject benchmark output files.

## Future Validation Report

The future validation report should state only that the local bundle has passed
declared-file, digest-sidecar, semantic readback, and claim-boundary checks.

It must not state that:

- a formal backend executed;
- Lean executed;
- SMT or Z3 executed;
- COBALT executed;
- Aeneas, Hax, or rust-lean executed;
- a proof artifact is valid;
- a checker transcript is valid;
- a solver certificate is valid;
- a proof corresponds to HSAI source;
- accepted Evidence Ledger state changed;
- Level2+ evidence exists;
- score axes are populated;
- benchmark evidence exists;
- HSAI is semantically correct;
- HSAI is production ready;
- HSAI is SOTA;
- HSAI is a breakthrough;
- HSAI is fully secure;
- the gateway has authority to execute an action.

## Required Future Tests

The implementation slice should include focused tests for:

- valid materialization and readback;
- invalid summary rejection before write;
- unsafe bundle id rejection;
- protected output-root rejection;
- existing output-root overwrite rejection;
- stale sidecar rejection;
- missing sidecar rejection;
- malformed summary JSON rejection;
- malformed manifest JSON rejection;
- source manifest drift rejection;
- coverage-label drift rejection;
- nonclaim Markdown drift rejection;
- validation-report drift rejection;
- manifest claim-boundary drift rejection;
- manifest accepted-evidence drift rejection;
- manifest Level2+ drift rejection;
- manifest score-axis drift rejection;
- manifest authority drift rejection;
- undeclared raw proof artifact rejection;
- undeclared checker transcript rejection;
- undeclared solver trace rejection;
- undeclared accepted Evidence Ledger file rejection;
- undeclared benchmark output rejection;
- output-root symlink rejection;
- bundle-directory symlink rejection;
- declared-file symlink rejection;
- declared-sidecar symlink rejection.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- filesystem materialization behavior;
- command execution;
- process spawning;
- backend runner implementation;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifact promotion;
- generated checker transcript promotion;
- raw prover log retention;
- raw checker log retention;
- raw solver trace retention;
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

Phase 302 implements the local validation-summary output-bundle data types,
materialization/readback helpers, and focused tests under
`crates/hsai-agent-admission/src/lib.rs`. Phase 303 defines the docs-first
hermetic backend execution boundary. It still does not promote checker
transcripts, mutate accepted evidence, create Level2+ evidence, populate score
axes, or change public claims.
