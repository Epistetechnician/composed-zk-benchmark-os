# Phase 304 HSAI Gateway Formal Backend Hermetic Execution No-Spawn Descriptor Notes

State slice: `Phase 304 HSAI gateway formal backend hermetic execution no-spawn descriptor implementation`.

## Status

Complete for the no-spawn descriptor implementation slice.

## Purpose

Phase 303 defined the first future hermetic backend execution crossing. Phase
304 implements only the pure-data descriptor and fail-closed validation surface
for that crossing.

This phase still does not spawn a process and does not execute SMT, Z3, COBALT,
Lean, or any other backend.

## Implemented Surface

This phase adds:

- hermetic execution descriptor schema, report schema, state-slice, and
  claim-boundary constants;
- `GatewayFormalBackendHermeticExecutionLane`;
- `GatewayFormalBackendHermeticCommandKind`;
- `GatewayFormalBackendHermeticInvariantProperty`;
- `GatewayFormalBackendHermeticExecutionDescriptor`;
- `GatewayFormalBackendHermeticExecutionDescriptorIssue`;
- `GatewayFormalBackendHermeticExecutionDescriptorValidation`;
- `GatewayFormalBackendHermeticExecutionDescriptorReport`;
- required nonclaims for no-spawn hermetic descriptor metadata;
- a deterministic descriptor builder for `local_smt_tiny_gateway_invariant`;
- a fail-closed descriptor validator;
- a descriptor report builder;
- focused tests for valid no-spawn metadata, execution/claim escalation
  rejection, shell/environment/raw-retention rejection, and digest sensitivity.

## Local Meaning

The descriptor means only this:

`A future tiny local SMT invariant lane has a no-spawn, claim-bounded command
descriptor candidate that passes local validation.`

It is not:

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
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_descriptor
cargo test -p hsai-agent-admission gateway_formal_backend_execution_quarantine_validation_summary_output_bundle
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 305 defines the docs-first no-spawn output-bundle boundary for the
descriptor report. Actual process spawning remains deferred until the
descriptor/report bundle, quarantine output, and negative tests are stable.
