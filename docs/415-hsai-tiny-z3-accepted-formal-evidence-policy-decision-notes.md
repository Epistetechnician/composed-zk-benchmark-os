# Phase 415 HSAI Tiny Z3 Accepted Formal Evidence Policy Decision Notes

State slice: `Phase 415 HSAI tiny Z3 accepted formal-evidence policy-decision`.

## Boundary

Phase 415 implements local policy-decision metadata over one Phase 413 tiny-Z3
accepted-handoff record for:

```text
gateway-local-digest-binding-determinism-v1
```

It records that tiny-Z3 accepted formal evidence remains forbidden in the
current accepted append path. It does not implement accepted formal evidence,
mutate the accepted Evidence Ledger, change accepted append policy, create
Level2+ evidence, populate score axes, generate proof artifacts, generate
checker transcripts, generate solver certificates, execute Lean, execute
COBALT, run Rust-to-Lean extraction, submit benchmarks, deploy to production,
or grant action authority.

## Implemented Surface

Phase 415 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_POLICY_DECISION_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_POLICY_DECISION_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_POLICY_DECISION_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_POLICY_DECISION_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3PolicyDecisionInput`;
- `GatewayFormalTinyDigestBackendZ3PolicyDecision`;
- `GatewayFormalTinyDigestBackendZ3PolicyDecisionIssue`;
- `GatewayFormalTinyDigestBackendZ3PolicyDecisionValidation`;
- `gateway_formal_tiny_digest_backend_z3_policy_decision_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_policy_decision_statement`;
- `gateway_formal_tiny_digest_backend_z3_policy_decision_required_nonclaims`;
- `build_gateway_formal_tiny_digest_backend_z3_policy_decision`;
- `validate_gateway_formal_tiny_digest_backend_z3_policy_decision_input`.

## Current-Path Decision

The only valid Phase 415 decision is:

```text
AcceptedFormalEvidenceStillForbidden
```

The canonical decision statement is:

```text
tiny-Z3 accepted formal evidence remains forbidden in the current accepted append path
```

This records the Phase 414 boundary in local metadata. It does not authorize a
bounded formal-evidence class.

## Bound Provenance

The policy-decision record binds:

- Phase 413 handoff digest;
- Phase 413 handoff-input digest;
- Phase 411 reviewed-record digest;
- accepted append policy version;
- source formal-evidence acceptance policy version;
- Phase 415 policy-decision version;
- current-path policy decision;
- policy-decision statement digest;
- current accepted append blocker digest;
- explicit nonclaim digest.

## Validation Rules

The validator rejects:

- invalid schema version, decision id, or timestamp;
- missing or zero digests;
- Phase 413 handoff digest drift;
- Phase 413 handoff state drift;
- accepted append policy-version drift;
- source formal-evidence policy-version drift;
- Phase 415 policy-decision version drift;
- decisions other than `AcceptedFormalEvidenceStillForbidden`;
- policy-decision statement drift;
- current accepted append blocker drift;
- explicit nonclaim drift;
- accepted Evidence Ledger mutation attempts;
- accepted append policy-change attempts;
- accepted formal-evidence creation attempts;
- bounded formal-evidence class approval attempts;
- Level2+ evidence attempts;
- score-axis population attempts;
- proof artifact promotion;
- checker transcript promotion;
- solver certificate promotion;
- benchmark/SOTA comparison claims;
- semantic-correctness, production-readiness, SOTA, breakthrough,
  full-security, or action-authority claims.

## Tests

Focused tests cover:

- policy-decision metadata construction from a Phase 413 handoff;
- handoff digest drift;
- accepted append policy-version drift;
- attempted bounded formal-evidence class approval;
- current accepted append blocker drift;
- policy-decision statement drift;
- promoted handoff state drift;
- accepted evidence mutation, accepted append policy change, accepted formal
  evidence creation, Level2+, score-axis, proof/checker/solver promotion,
  SOTA, full-security, and authority attempts.

## Claim Boundary

Phase 415 supports only this claim:

```text
HSAI has local tiny-Z3 policy-decision metadata recording that accepted formal
evidence remains forbidden in the current accepted append path, bound to one
Phase 413 handoff and the current accepted append blocker set.
```

That still does not support accepted formal evidence, accepted Evidence Ledger
mutation, accepted append policy change, Level2+ evidence, score-axis evidence,
a Lean proof, a COBALT containment proof, Rust-to-Lean extraction, checker
transcript evidence, solver certificate evidence, source correspondence proof,
whole-system proof, semantic correctness, production readiness, SOTA,
breakthrough status, full security, or authority to execute an action.

## Next Slice

Phase 416 should define a docs-first tiny-Z3 bounded formal-evidence class
feasibility boundary. It must not implement or approve the class, mutate
accepted evidence, change accepted append policy, create Level2+ evidence,
populate score axes, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, or grant authority
to execute an action.
