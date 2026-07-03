# Phase 405 HSAI Fixed Local Z3 Execution Output Readback Notes

State slice: `Phase 405 HSAI fixed local Z3 execution output readback`.

Phase 405 materializes and reads back the Phase 404 fixed local Z3 execution
record for:

```text
gateway-local-digest-binding-determinism-v1
```

The output bundle is quarantined local readback evidence only. It is not an
accepted Evidence Ledger append, not Level2+ evidence, not a solver certificate,
not a checker transcript, and not proof authority.

## Implemented Surface

Phase 405 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_EXECUTION_OUTPUT_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_EXECUTION_OUTPUT_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_EXECUTION_OUTPUT_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3ExecutionOutputManifest`;
- `GatewayFormalTinyDigestBackendZ3ExecutionOutputRequest`;
- `GatewayFormalTinyDigestBackendZ3ExecutionOutputError`;
- `gateway_formal_tiny_digest_backend_z3_execution_output_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_execution_output_declared_files`;
- `gateway_formal_tiny_digest_backend_z3_execution_output_declared_sidecars`;
- `materialize_gateway_formal_tiny_digest_backend_z3_execution_output_bundle`;
- `read_gateway_formal_tiny_digest_backend_z3_execution_output_bundle`.

The materializer accepts one valid Phase 404
`GatewayFormalTinyDigestBackendZ3Execution` and writes a declared bundle under:

```text
gateway-formal-tiny-digest-z3-execution/
```

## Declared Files

The bundle declares exactly these files:

- `gateway-formal-tiny-digest-z3-execution/manifest.json`;
- `gateway-formal-tiny-digest-z3-execution/execution.json`;
- `gateway-formal-tiny-digest-z3-execution/nonclaims.md`.

Each declared file has a `.sha256` sidecar. Readback rejects undeclared files,
missing files, stale sidecars, symlinked bundle files, malformed JSON,
nonclaim drift, and manifest semantic drift.

## Write And Readback Controls

Phase 405 uses staged writes before moving the complete bundle into the caller
selected output root. The output request requires:

- a non-empty Phase 404 execution run id;
- a non-empty output root;
- explicit overwrite permission before replacing an existing output root;
- protected-root rejection;
- repository-root rejection through the existing output-root validator.

The readback path validates that the manifest matches the execution record
digest, input digest, probe digest, command descriptor digest, obligation
digest, solver verdict label, declared files, declared sidecars, declared file
digests, claim boundary, nonclaims, and all nonpromotion flags.

## Validation Coverage

Focused Phase 405 tests cover:

- materializing and reading back a valid fixed local Z3 execution bundle;
- rejecting stale execution sidecar digest drift;
- rejecting manifest promotion drift after sidecar recomputation;
- rejecting an undeclared `proof-artifact.json` file.

The tests reuse the Phase 404 local Z3 helper. If `/opt/homebrew/bin/z3` is not
present, they preserve the existing selected-lane-unavailable check instead of
fabricating a backend run.

## Claim Boundary

Phase 405 supports only this claim:

```text
HSAI can materialize and read back one quarantined fixed local Z3 execution output bundle for the tiny gateway digest-binding property, with digest sidecars and explicit nonpromotion validation.
```

It does not support accepted formal evidence, Level2+ evidence, score axes,
Lean execution, COBALT execution, Rust-to-Lean extraction, semantic
correctness, production readiness, SOTA, full security, or authority to execute
an action.

## Next Slice

Phase 406 should define a docs-first boundary for the next promotion decision:
either a reviewed local formal-evidence candidate that remains outside the
accepted Evidence Ledger, or a narrow checker-transcript/proof-artifact boundary
with explicit source authority. It must not mutate accepted evidence, create
Level2+ evidence, populate score axes, or make stronger public claims without a
separate accepted-evidence policy change.
