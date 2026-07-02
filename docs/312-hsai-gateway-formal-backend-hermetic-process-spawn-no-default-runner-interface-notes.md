# Phase 312 HSAI Gateway Formal Backend Hermetic Process-Spawn No-Default-Runner Interface Notes

State slice: `Phase 312 HSAI gateway formal backend hermetic process-spawn no-default-runner interface`.

## Status

Complete for the local no-default-runner interface slice.

## Purpose

Phase 311 defined the future process-spawn crossing contract for the tiny
`local_smt_tiny_gateway_invariant` lane. Phase 312 implements the stable Rust
interface and validator for that boundary without adding a runner.

This phase does not spawn a process, does not execute Lean, SMT, Z3, COBALT, or
any proof backend, and does not create proof artifacts, checker transcripts, or
accepted evidence.

## Implemented Surface

This phase adds:

- process-spawn interface schema/state/claim-boundary constants;
- executable policy metadata for the fixed local SMT lane;
- runtime policy metadata for no stdin, no shell, no network, bounded output,
  redaction, and no raw artifact retention;
- nonpromotion policy metadata for no proof artifacts, no checker transcripts,
  no solver certificates, no accepted evidence, no Level2+ evidence, no score
  axes, and no authority;
- `GatewayFormalBackendHermeticProcessSpawnInterface`;
- fail-closed validation issues for runner, policy, source-binding, environment,
  retention, nonpromotion, and forbidden-claim drift;
- a deterministic builder bound to a valid Phase 304 descriptor, Phase 306
  descriptor-report manifest, and Phase 308 result-quarantine manifest;
- focused tests for valid no-default-runner metadata, runner/policy escalation
  rejection, and source-manifest drift rejection.

## Local Meaning

The interface means only:

`The repository can represent and validate the exact no-default-runner policy
that must be satisfied before a future process-spawn implementation is allowed.`

It does not mean:

- a backend executed;
- a solver ran;
- Lean, SMT, Z3, COBALT, Aeneas, Hax, rust-lean, Coq, TLA+, CBMC, or a model
  checker ran;
- a proof exists;
- a solver certificate is valid;
- a checker transcript is accepted evidence;
- an accepted Evidence Ledger changed;
- Level2+ evidence exists;
- score axes are populated;
- semantic correctness is proved;
- HSAI is production ready;
- HSAI is SOTA;
- HSAI is a breakthrough;
- HSAI is fully secure;
- authority to execute an action exists.

## Validation

Required validation for this slice:

```text
cargo fmt --all -- --check
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_process_spawn_interface
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_result_quarantine_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_descriptor_report_output_bundle
cargo test -p hsai-agent-admission gateway_formal_backend_hermetic_execution_descriptor
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

Phase 313 implements the explicit fixture process-spawn crossing slice. It keeps
the Phase 312 policy validator in front of execution and writes only
quarantined local fixture-result metadata. It does not promote proof artifacts,
checker transcripts, solver certificates, accepted evidence, Level2+ evidence,
score axes, semantic-correctness claims, production-readiness claims, SOTA
claims, full-security claims, or authority claims.
