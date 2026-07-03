# Phase 404 HSAI Fixed Local Z3 Digest-Binding Execution Notes

State slice: `Phase 404 HSAI fixed local Z3 digest-binding execution`.

Phase 404 crosses the Phase 401 backend-execution boundary for one local SMT
lane by reusing the existing Phase 326 fixed-process runner. The executed
property is:

```text
gateway-local-digest-binding-determinism-v1
```

The execution remains quarantined local output. It is not accepted evidence and
not proof authority.

## Implemented Surface

Phase 404 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_EXECUTION_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_EXECUTION_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_EXECUTION_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3ExecutionInput`;
- `GatewayFormalTinyDigestBackendZ3Execution`;
- `GatewayFormalTinyDigestBackendZ3ExecutionIssue`;
- `GatewayFormalTinyDigestBackendZ3ExecutionValidation`;
- `gateway_formal_tiny_digest_backend_z3_execution_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_execution_required_nonclaims`;
- `run_gateway_formal_tiny_digest_backend_z3_execution`;
- `validate_gateway_formal_tiny_digest_backend_z3_execution_input`;
- `validate_gateway_formal_tiny_digest_backend_z3_execution`.

The runner accepts a valid Phase 403 probe, a fixed command descriptor, and a
caller-supplied fixed executable path. It reads the executable, binds its
digest into a compatibility preflight, and calls the existing Phase 326
`run_gateway_formal_real_command_lane_fixed_smt_process` path. No new
`std::process::Command` site is added.

## Local Z3 Run

The focused test `phase404_fixed_local_z3_digest_binding_executes_when_available`
uses `/opt/homebrew/bin/z3` when present. In the current local environment,
that binary exists and reports:

```text
Z3 version 4.15.0 - 64 bit
```

The test writes a non-secret SMT-LIB2 obligation under a temporary test root and
executes:

```text
/opt/homebrew/bin/z3 -smt2 <temporary-obligation-path>
```

The obligation asserts that the same digest-binding tuple is not equal to
itself, so the expected verdict is:

```text
solver_unsat_without_certificate
```

This is a local SMT execution result only. It is not a solver certificate, not
a proof artifact, and not accepted evidence.

## Nonpromotion Rules

The Phase 404 execution record preserves:

- `proof_artifact_created = false`;
- `checker_transcript_created = false`;
- `solver_certificate_created = false`;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- all semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, and authority flags as false.

Validation rejects promotion attempts in the execution input and rejects any
execution record that claims proof artifacts, checker transcripts, solver
certificates, accepted evidence, Level2+ evidence, score axes, strong public
claims, raw logs, raw provider responses, or action authority.

## Claim Boundary

Phase 404 supports only this claim:

```text
HSAI has a quarantined fixed local Z3 execution path for one tiny digest-binding SMT obligation, with bounded output and explicit nonpromotion validation.
```

It does not support Lean execution, COBALT execution, Rust-to-Lean extraction,
accepted formal evidence, Level2+ evidence, score axes, semantic correctness,
production readiness, SOTA, full security, or authority to execute an action.

## Next Slice

Phase 405 should decide whether to add a materialized/readback bundle for the
Phase 404 Z3 execution output or a reviewed local-evidence candidate. It must
not mutate the accepted Evidence Ledger, create Level2+ evidence, populate
score axes, or make stronger public claims without a separate accepted-evidence
policy change and proof-source authority boundary.
