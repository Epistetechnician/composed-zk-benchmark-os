# Phase 317 HSAI Tiny Hermetic Formal-Backend Adapter Data Model Notes

State slice: `Phase 317 HSAI tiny hermetic formal-backend adapter data model and quarantine bundle`.

## Scope

Phase 317 implements the first typed local data-model surface for the Phase 316
tiny hermetic formal-backend adapter contract in `crates/hsai-agent-admission`.
It is a not-run adapter quarantine surface. It does not execute a solver,
checker, proof assistant, model checker, Lean, SMT, Z3, COBALT, Aeneas, Hax, or
rust-lean.

## Implemented

- `GATEWAY_FORMAL_BACKEND_TINY_HERMETIC_ADAPTER_*` state, schema, and claim-boundary constants.
- `GatewayFormalBackendTinyHermeticAdapterRequest`, binding one source-correspondence certificate digest, descriptor-report manifest digest, process-spawn interface digest, fixture digest, command descriptor digest, expected transcript schema digest, operator acknowledgement, and required nonclaims.
- `GatewayFormalBackendTinyHermeticAdapterFixtureInput`, encoding the fixed non-secret input fixture for `attestation_challenge_binding_deterministic_input_sensitive`.
- `GatewayFormalBackendTinyHermeticAdapterCommandDescriptor`, encoding a direct-process/no-shell/no-stdin/no-network command policy as metadata only.
- `GatewayFormalBackendTinyHermeticAdapterTranscriptSummary`, restricted to `NotRun` and `NotEvaluated`.
- `GatewayFormalBackendTinyHermeticAdapterNonpromotionReport`, keeping proof artifacts, checker transcripts, solver certificates, accepted evidence, Level2+ evidence, score axes, authority, raw logs, and broad claims disabled.
- `GatewayFormalBackendTinyHermeticAdapterOutputManifest` plus validation, materialization, readback, SHA-256 sidecars, nonclaim Markdown, and declared-file enforcement.
- Focused tests for valid materialization/readback, pre-write escalation rejection, stale digest rejection, manifest drift rejection, and undeclared proof-artifact rejection.

## Hard Boundary

This phase creates local adapter metadata and quarantine files only. It does not
create proof evidence, accepted evidence, Level2+ evidence, benchmark evidence,
official submission evidence, checker-transcript evidence, solver-certificate
evidence, score-axis evidence, production evidence, or live provider evidence.

The imported `report_data_binding` dependency remains explicit:

```text
report_data_binding imported from hsai_attestation and not proved here
```

## Claim Boundary

The exact claim this phase can support is:

```text
HSAI has a typed, reproducible, not-run tiny formal-backend adapter quarantine surface for one selected gateway admission invariant.
```

It does not support:

- `HSAI is SOTA.`
- `HSAI is fully secure.`
- `HSAI proves semantic correctness.`
- `HSAI is production ready.`
- `HSAI has accepted formal evidence.`
- `HSAI has Level2+ formal evidence.`
- `HSAI has backend score axes.`

## Validation

Focused validation:

```text
cargo test -p hsai-agent-admission gateway_formal_backend_tiny_hermetic_adapter -- --nocapture
```

Full phase validation should also include:

```text
cargo fmt --all -- --check
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

The next responsible slice is Phase 318: a backend execution readiness boundary
for the already typed Phase 317 adapter bundle. That phase should define the
operator acknowledgement, exact command fixture, transcript schema, raw-output
redaction, and checker transcript quarantine rules before any new execution
code is added.
