# Phase 609 HSAI Tiny Z3 Real Materialized Staging Runner Implementation Notes

State slice: `Phase 609 HSAI tiny Z3 real materialized staging runner`.

Phase 609 implements the narrow local staging runner boundary from
`docs/608-phase-hsai-tiny-z3-real-materialized-staging-runner-boundary.md`.

```text
exact Phase 604 focused command
  -> bounded in-memory transcript digests
  -> Phase 607 quarantined capture packet
  -> readback-validated local output root
```

This phase is a staging-data collection surface. It does not import external
results, mutate accepted evidence outside the Phase 604 focused local test
fixture path, accept independent external reproduction, create accepted formal
evidence, create Level2+ evidence, populate score axes, run Lean, run COBALT,
run Rust-to-Lean extraction, create proof artifacts, create checker
transcripts, create solver certificates, create benchmark evidence, record
human-review acceptance, or claim semantic correctness, production readiness,
SOTA status, breakthrough status, full security, global uniqueness, external
audit status, or authority to execute an action.

## Implemented Surface

Phase 609 adds typed Rust normalizer inputs under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3RealMaterializedStagingRunnerRequest`;
- `GatewayFormalTinyZ3RealMaterializedStagingRunnerObservedProcess`;
- `GatewayFormalTinyZ3RealMaterializedStagingRunnerCaptureInputs`;
- `GatewayFormalTinyZ3RealMaterializedStagingRunnerError`;
- `build_gateway_formal_tiny_z3_real_materialized_staging_runner_capture_inputs`;
- `materialize_gateway_formal_tiny_z3_real_materialized_staging_runner_capture`.

It also adds the operator-facing example:

```text
crates/hsai-agent-admission/examples/phase609_real_materialized_staging_runner.rs
```

The example requires:

```text
HSAI_PHASE609_ACK
HSAI_PHASE609_OUTPUT_ROOT
```

Optional environment variables:

```text
HSAI_PHASE609_RUN_ID
HSAI_PHASE609_OPERATOR_ID
HSAI_PHASE609_CREATED_AT_UNIX
HSAI_PHASE609_OVERWRITE
HSAI_PHASE609_Z3_EXECUTABLE
```

The acknowledgement literal is:

```text
I acknowledge Phase 609 writes local quarantined staging capture metadata only under .gateway-demo-runs.
```

The output root must be absolute and under the repo-local ignored
`.gateway-demo-runs/` directory.

## Staging Invocation

From the repository root:

```text
HSAI_PHASE609_ACK='I acknowledge Phase 609 writes local quarantined staging capture metadata only under .gateway-demo-runs.' \
HSAI_PHASE609_OUTPUT_ROOT="$PWD/.gateway-demo-runs/phase609-staging-run" \
cargo run -p hsai-agent-admission --example phase609_real_materialized_staging_runner
```

The example executes only:

```text
cargo test -p hsai-agent-admission phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation -- --nocapture
```

It stores only the Phase 607 declared JSON files and SHA-256 sidecars. Raw
stdout and stderr are hashed in memory and are not retained as files.

## Guardrails

The implementation rejects:

- invalid run ids or operator ids;
- missing or malformed repository commit;
- missing branch, dirty-status, OS, architecture, Rust version, Z3 path, or Z3
  version;
- command drift from the exact Phase 604 focused command;
- nonzero process exit status;
- missing expected Phase 604 focused result line;
- skipped runs or missing Z3;
- oversized in-memory transcript bytes;
- Phase 607 materializer rejection;
- readback drift.

## Evidence Meaning

Phase 609 supports only this claim:

```text
HSAI can locally execute the exact Phase 604 focused command from an
operator-facing staging runner and package the resulting telemetry through the
Phase 607 quarantined capture materializer.
```

It is not external result import, not accepted external evidence, not accepted
formal evidence, not independent external reproduction accepted by the repo,
not Level2+ evidence, not score-axis evidence, not Lean proof, not SMT proof
authority, not COBALT containment evidence, not Rust-to-Lean proof, not checker
transcript authority, not solver certificate authority, not benchmark evidence,
not external audit, not SOTA, not semantic correctness, not production
readiness, not full security, and not authority to execute an action.

## Tests

Focused tests cover:

- Phase 609 normalizer materializing through the Phase 607 capture path;
- command drift rejection;
- missing focused result-line rejection;
- skipped/missing-Z3 rejection;
- invalid provenance rejection;
- source-contract checks for the operator-facing example.
