# Phase 305 HSAI Gateway Formal Backend Hermetic Descriptor-Report Output-Bundle Boundary

State slice: `Phase 305 HSAI gateway formal backend hermetic descriptor-report output-bundle boundary`.

## Status

Complete for the docs-first descriptor-report output-bundle boundary.

## Purpose

Phase 304 implemented a no-spawn descriptor and report for the future
`local_smt_tiny_gateway_invariant` lane. Phase 305 defines the future local
declared-file output bundle for materializing that descriptor report.

This phase does not add Rust code. It defines the future implementation
contract.

## Future Bundle Shape

A future implementation may materialize a local bundle under:

`gateway-formal-backend-hermetic-descriptor-report/*`

The future declared files should be:

- `gateway-formal-backend-hermetic-descriptor-report/descriptor.json`;
- `gateway-formal-backend-hermetic-descriptor-report/report.json`;
- `gateway-formal-backend-hermetic-descriptor-report/validation.json`;
- `gateway-formal-backend-hermetic-descriptor-report/command-contract.json`;
- `gateway-formal-backend-hermetic-descriptor-report/nonclaims.md`;
- `gateway-formal-backend-hermetic-descriptor-report/manifest.json`.

Each declared file must have a sibling `.sha256` sidecar.

The future manifest should include:

- schema version;
- bundle id;
- state slice;
- created-at timestamp supplied by the caller;
- descriptor digest;
- report digest;
- validation digest;
- input manifest digest;
- toolchain lock digest;
- lane label;
- backend kind;
- invariant property;
- command kind;
- executable path label;
- argv template digest;
- output-root label;
- timeout policy;
- stdout/stderr retention limits;
- declared files;
- declared file digests;
- claim boundary;
- no-spawn flag;
- no backend-executed flag;
- no proof-artifact-created flag;
- no checker-transcript-created flag;
- no accepted-evidence flag;
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
- reject descriptor digest drift;
- reject report digest drift;
- reject validation digest drift;
- reject command-contract digest drift;
- reject nonclaim Markdown drift;
- reject manifest state-slice drift;
- reject manifest claim-boundary drift;
- reject manifest no-spawn drift;
- reject manifest backend-executed drift;
- reject manifest proof-artifact drift;
- reject manifest checker-transcript drift;
- reject manifest accepted-evidence drift;
- reject manifest Level2+ drift;
- reject manifest score-axis drift;
- reject manifest semantic-correctness drift;
- reject manifest production-readiness drift;
- reject manifest SOTA drift;
- reject manifest breakthrough drift;
- reject manifest full-security drift;
- reject manifest authority drift.

## Future Validation Report

The future validation file should state only that the local descriptor/report
bundle passed declared-file, sidecar, semantic readback, and claim-boundary
checks.

It must not state that:

- a process spawned;
- a formal backend executed;
- SMT or Z3 executed;
- COBALT executed;
- Lean executed;
- Aeneas, Hax, or rust-lean executed;
- a proof artifact is valid;
- a checker transcript is valid;
- a solver certificate is valid;
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
- invalid descriptor rejection before write;
- unsafe bundle id rejection;
- protected output-root rejection;
- existing output-root overwrite rejection;
- missing sidecar rejection;
- stale sidecar rejection;
- malformed descriptor JSON rejection;
- malformed report JSON rejection;
- malformed manifest JSON rejection;
- descriptor digest drift rejection;
- report digest drift rejection;
- validation digest drift rejection;
- command-contract drift rejection;
- nonclaim Markdown drift rejection;
- manifest state-slice drift rejection;
- manifest no-spawn drift rejection;
- manifest backend-executed drift rejection;
- manifest proof-artifact drift rejection;
- manifest checker-transcript drift rejection;
- manifest accepted-evidence drift rejection;
- manifest Level2+ drift rejection;
- manifest score-axis drift rejection;
- manifest semantic-correctness drift rejection;
- manifest production-readiness drift rejection;
- manifest SOTA drift rejection;
- manifest breakthrough drift rejection;
- manifest full-security drift rejection;
- manifest authority drift rejection;
- undeclared raw stdout rejection;
- undeclared raw stderr rejection;
- undeclared solver trace rejection;
- undeclared proof artifact rejection;
- undeclared checker transcript rejection;
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

Phase 306 implements this local descriptor-report output-bundle boundary with
materialization, readback, sidecar checks, and focused negative tests. It still
does not spawn a process or execute a backend.
