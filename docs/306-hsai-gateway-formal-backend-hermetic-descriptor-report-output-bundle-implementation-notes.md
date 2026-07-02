# Phase 306 HSAI Gateway Formal Backend Hermetic Descriptor-Report Output-Bundle Implementation Notes

State slice: `Phase 306 HSAI gateway formal backend hermetic descriptor-report output-bundle implementation`.

## Status

Complete for the local descriptor-report output-bundle implementation slice.

## Purpose

Phase 305 defined the local declared-file output-bundle boundary for the Phase
304 no-spawn descriptor report. Phase 306 implements that local bundle surface.

This phase still does not spawn a process and does not execute SMT, Z3, COBALT,
Lean, or any formal backend.

## Implemented Surface

This phase adds:

- descriptor-report output-bundle state-slice and claim-boundary constants;
- output schema version;
- declared file and sidecar registries for
  `gateway-formal-backend-hermetic-descriptor-report/*`;
- output request type;
- command-contract record and digest helper;
- output validation-report record and digest helper;
- output manifest record and digest helper;
- output error labels;
- declared-files helper;
- output claim-boundary helper;
- staged materialization with SHA-256 sidecars;
- readback with root, bundle-dir, declared-file, and sidecar symlink rejection;
- undeclared-file rejection;
- stale sidecar rejection;
- semantic readback for descriptor, report, validation, command contract,
  nonclaims, and manifest;
- focused tests for valid materialization/readback, invalid descriptor rejection
  before write, unsafe bundle id rejection, stale sidecar rejection, validation
  drift, command-contract drift, manifest escalation, undeclared proof artifact
  rejection, and Unix symlink rejection.

## Local Meaning

The output bundle means only this:

`A local no-spawn hermetic descriptor report was materialized and read back
under a declared-file, digest-sidecar, claim-bounded bundle contract.`

It is not:

- process spawning;
- backend execution;
- SMT execution;
- Z3 execution;
- COBALT execution;
- Lean execution;
- Rust-to-Lean extraction;
- proof evidence;
- checker transcript evidence;
- solver certificate evidence;
- accepted Evidence Ledger evidence;
- Level2+ evidence;
- benchmark evidence;
- score-axis evidence;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- action authority.

## Validation

Required validation for this slice:

```text
cargo fmt --all -- --check
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_descriptor_report_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_descriptor
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 307 defines the no-spawn quarantine-output boundary for a future hermetic
execution result shape. Actual process spawning should remain deferred until
the descriptor/report output bundle, result-quarantine output bundle, and
negative tests are stable.
