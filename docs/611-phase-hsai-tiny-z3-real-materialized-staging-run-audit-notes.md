# Phase 611 HSAI Tiny Z3 Real Materialized Staging Run Audit Notes

State slice: `Phase 611 HSAI tiny Z3 real materialized staging run audit`.

Phase 611 implements the narrow in-memory audit summary authorized by
`docs/610-phase-hsai-tiny-z3-real-materialized-staging-run-audit-boundary.md`.

```text
Phase 607/609 capture manifest
  -> validation of capture shape and nonpromotion flags
  -> in-memory audit summary
```

This phase is local review metadata only. It does not write audit files, read
raw transcripts, import external results, mutate the accepted Evidence Ledger,
accept independent external reproduction, create accepted formal evidence,
create Level2+ evidence, populate score axes, run Lean, run SMT/Z3, run
COBALT, run Rust-to-Lean extraction, create proof artifacts, create checker
transcripts, create solver certificates, create benchmark evidence, record
human-review acceptance, or claim semantic correctness, production readiness,
SOTA status, breakthrough status, full security, global uniqueness, external
audit status, or authority to execute an action.

## Implemented Surface

Phase 611 adds local Rust types and functions under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3RealMaterializedStagingRunAuditRequest`;
- `GatewayFormalTinyZ3RealMaterializedStagingRunAuditSummary`;
- `GatewayFormalTinyZ3RealMaterializedStagingRunAuditError`;
- `gateway_formal_tiny_z3_real_materialized_staging_run_audit_claim_boundary`;
- `build_gateway_formal_tiny_z3_real_materialized_staging_run_audit_summary`.

The audit summary records source manifest digest, readback-validation digest,
nonpromotion digest, declared file and sidecar counts, source claim boundary,
audit claim boundary, quarantine/readback booleans, operator-review readiness,
and all nonpromotion flags.

## Guardrails

The implementation rejects:

- invalid audit ids;
- empty source capture labels;
- zero created-at timestamps;
- non-Phase-607 source manifests;
- missing declared files or sidecars;
- empty source readback-validation digests;
- empty source nonpromotion digests;
- source claim-boundary drift;
- non-quarantined source packets;
- any source promotion flag, including accepted evidence mutation,
  independent reproduction acceptance, human-review acceptance, accepted formal
  evidence, Level2, score axes, proof/checker/solver artifacts, Lean, SMT/Z3
  escalation, COBALT, Rust-to-Lean, benchmark evidence, external audit,
  semantic correctness, production readiness, SOTA, breakthrough, full
  security, global uniqueness, or authority.

## Evidence Meaning

Phase 611 supports only this claim:

```text
HSAI can summarize one readback-valid Phase 607/609 quarantined staging capture
manifest for local operator review visibility without promoting the packet.
```

It is not external result import, not accepted evidence, not accepted formal
evidence, not independent external reproduction accepted by the repo, not
Level2+ evidence, not score-axis evidence, not Lean proof, not SMT proof
authority, not COBALT containment evidence, not Rust-to-Lean proof, not checker
transcript authority, not solver certificate authority, not benchmark evidence,
not external audit, not SOTA, not semantic correctness, not production
readiness, not full security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful Phase 611 summary over a Phase 609-produced Phase 607 manifest;
- source promotion drift rejection;
- invalid audit request rejection;
- empty source readback-validation digest rejection.
