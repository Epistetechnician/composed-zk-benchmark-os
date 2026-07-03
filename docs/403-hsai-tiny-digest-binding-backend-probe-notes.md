# Phase 403 HSAI Tiny Digest-Binding Backend Probe Notes

State slice: `Phase 403 HSAI tiny digest-binding backend probe implementation`.

Phase 403 implements the first Rust metadata surface for the Phase 401 tiny
digest-binding property:

```text
gateway-local-digest-binding-determinism-v1
```

The implementation is intentionally bounded. It records local backend
availability and binds the required digest tuple for a future fixed Z3 run, but
it does not spawn a process and does not promote any proof or evidence.

## Implemented Surface

Phase 403 adds these public Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_PROBE_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_PROBE_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_PROBE_PROPERTY_ID`;
- `GatewayFormalTinyDigestBackendToolStatus`;
- `GatewayFormalTinyDigestBackendToolAvailability`;
- `GatewayFormalTinyDigestBackendProbeInput`;
- `GatewayFormalTinyDigestBackendProbe`;
- `GatewayFormalTinyDigestBackendProbeIssue`;
- `GatewayFormalTinyDigestBackendProbeValidation`;
- `gateway_formal_tiny_digest_backend_probe_claim_boundary`;
- `gateway_formal_tiny_digest_backend_probe_required_nonclaims`;
- `build_gateway_formal_tiny_digest_backend_probe`;
- `validate_gateway_formal_tiny_digest_backend_probe_input`;
- `validate_gateway_formal_tiny_digest_backend_probe`.

## Bound Inputs

The probe binds:

- selected Phase 401 property id;
- selected lane id;
- selected metadata-record digest;
- selected metadata-input digest;
- explicit nonclaim digest;
- accepted append blocker digest;
- command descriptor digest;
- expected-verdict descriptor digest;
- output quarantine descriptor digest;
- local tool availability for `smt-z3-local`, `lean-local-skeleton`, and
  `cobalt-local-skeleton`.

The validator treats unavailable selected lanes as invalid and requires any
available tool to provide an executable identity. Missing Lean, lake, or COBALT
must remain unavailable until a future phase detects them locally.

## Nonpromotion Rules

The probe always records:

- `process_spawned = false`;
- `backend_executed = false`;
- `proof_artifact_created = false`;
- `checker_transcript_created = false`;
- `solver_certificate_created = false`;
- `creates_accepted_evidence = false`;
- `creates_level2_evidence = false`;
- `populates_score_axes = false`;
- all public strong-claim flags as false.

Validation rejects accepted-evidence requests, Level2+ requests, score-axis
requests, proof/checker/solver promotion, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, and action-authority claims.

## Tests

Focused tests cover:

- valid probe construction for the `smt-z3-local` lane;
- selected unavailable lane rejection;
- digest-binding drift rejection;
- promotion-attempt rejection.

## Claim Boundary

Phase 403 supports only this claim:

```text
HSAI has local no-spawn backend-probe metadata for the Phase 401 digest-binding property, with explicit backend availability, digest binding, and nonpromotion validation.
```

It does not support backend execution, a system Z3 proof, Lean execution, COBALT
execution, Rust-to-Lean extraction, accepted formal evidence, Level2+ evidence,
score axes, semantic correctness, production readiness, SOTA, full security, or
authority to execute an action.

## Next Slice

Phase 404 may cross into a fixed local Z3 execution for this exact property if
it reuses the existing fixed-process, no-shell, cleared-environment,
bounded-output, quarantine, and nonpromotion discipline. It must not add a
generic backend runner, accepted evidence, Level2+ evidence, score axes, Lean
execution, COBALT execution, Rust-to-Lean extraction, or strong public claims.
