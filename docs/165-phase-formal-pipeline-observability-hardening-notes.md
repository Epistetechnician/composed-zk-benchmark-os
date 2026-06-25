# Phase 165 Formal Pipeline Observability Hardening Notes

State slice: `phase-165-post-164-professionalization-audit`.

## Claim

Phase 165 hardens the local formal-lane pipeline as observability metadata only.
It preserves the existing `NoopFormalVerifier` and `Level0DesignNote` claim
ceiling while making each pipeline pass explainable.

## Implemented

- `FormalLanePipelineOutcome` now records the source `MutationClass`, the
  primary `FormalPropertyScopeKind`, optional `FormalLaneProofStatus`, optional
  no-template reason, and mandatory nonclaims.
- `pipeline_outcome_is_declared_only` now reads the explicit proof-status field
  instead of re-deriving status through the nested evaluation record.
- `formal_pipeline_nonclaims` provides a reusable nonclaim bundle for pipeline
  outcomes.
- `SoakTelemetryCounters` now records formal-lane no-template count,
  scope-count metrics, and proof-status count metrics.
- `LocalSoakRunner` records full formal-lane pipeline outcomes into telemetry
  after successful local mutation application.
- Telemetry validation rejects impossible formal-lane counter relationships and
  classification drift in the new scope/status metrics.

## Nonclaims

This phase does not integrate a real formal tool, run proof checking, create
formal evidence, create benchmark evidence, populate score axes, mutate an
accepted Evidence Ledger, run external execution, create Level2+ evidence,
prove semantic correctness, or justify production-readiness claims.

Every formal-lane outcome remains local observability metadata. A
`DeclaredOnly` status is not proof.

## Validation

Focused validation:

```sh
cargo test -p zkbench-core --test phase_163_formal_lane_pipeline
cargo test -p zkbench-core --test soak_telemetry
```

Both focused suites pass with Phase 165 tests for:

- template-derived outcome metadata,
- no-template reasons,
- scope/status telemetry metrics,
- impossible formal-lane counter rejection, and
- metric classification rejection.
