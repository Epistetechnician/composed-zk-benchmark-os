# Phase 327 HSAI Real Formal Command Lane Fixed SMT Execution Output Readback Notes

State slice: `Phase 327 HSAI real formal command lane fixed SMT execution output materialization and readback`.

## Boundary

Phase 327 materializes and reads back the Phase 326 quarantined fixed-SMT
process output. It does not run a new backend, create proof artifacts, create
checker transcripts, create solver certificates, mutate accepted evidence,
create Level2+ evidence, populate score axes, or claim semantic correctness,
production readiness, SOTA, breakthrough status, full security, or authority to
execute an action.

The bundle is a local filesystem durability layer for a result that Phase 326
already kept quarantined.

## Implemented Surface

Phase 327 adds:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_FIXED_SMT_EXECUTION_OUTPUT_SCHEMA_VERSION`.
- `GatewayFormalRealCommandLaneFixedSmtExecutionOutputManifest`.
- `GatewayFormalRealCommandLaneFixedSmtExecutionOutputRequest`.
- `GatewayFormalRealCommandLaneFixedSmtExecutionOutputError`.
- Declared file and sidecar helpers for
  `gateway-formal-real-command-lane-fixed-smt-execution/*`.
- `materialize_gateway_formal_real_command_lane_fixed_smt_execution_output_bundle`.
- `read_gateway_formal_real_command_lane_fixed_smt_execution_output_bundle`.

The declared bundle contains:

```text
gateway-formal-real-command-lane-fixed-smt-execution/manifest.json
gateway-formal-real-command-lane-fixed-smt-execution/process-output.json
gateway-formal-real-command-lane-fixed-smt-execution/stdout-summary.json
gateway-formal-real-command-lane-fixed-smt-execution/stderr-summary.json
gateway-formal-real-command-lane-fixed-smt-execution/nonclaims.md
```

Each declared file has a sibling `.sha256` sidecar.

## Readback Rules

Readback rejects:

- protected or malformed output roots;
- symlinked roots, bundle directories, declared files, or sidecars;
- undeclared files;
- missing declared files;
- sidecar digest drift;
- duplicate-key or noncanonical JSON;
- manifest/process-output digest drift;
- stdout/stderr summary drift;
- promotion flags for proof artifacts, checker transcripts, solver
  certificates, accepted evidence, Level2+ evidence, score axes, semantic
  correctness, production readiness, SOTA, breakthrough, full security, or
  action authority;
- nonclaim Markdown drift.

## Tests

Focused tests cover:

- materialization and readback of a Phase 326 fixed-SMT process output;
- confirmation that execution is recorded only as local quarantined output;
- sidecar digest drift rejection;
- manifest promotion drift rejection;
- undeclared proof-artifact rejection.

## Claim Boundary

Phase 327 supports this claim:

```text
HSAI has a local materialized/readback bundle for one quarantined fixed-SMT
formal command-lane execution output, with digest sidecars and promotion-drift
rejection.
```

It does not support SOTA, full security, semantic correctness, production
readiness, accepted formal evidence, Level2+ formal evidence, backend score
axes, a system Z3 proof, a Lean proof, a COBALT containment proof,
Rust-to-Lean extraction, proof artifacts as accepted evidence, checker
transcripts as accepted evidence, solver certificates as accepted evidence,
source correspondence proof, accepted Evidence Ledger mutation, or authority to
execute an action.

## Next Slice

Phase 328 defines a docs-first formal-evidence promotion boundary for the
quarantined fixed-SMT output. Phase 329 may implement a local
formal-evidence-candidate data model if it preserves the Phase 328 state ladder
and still rejects accepted evidence, Level2+ evidence, score axes, semantic
correctness claims, production-readiness claims, SOTA claims, full-security
claims, and action authority.
