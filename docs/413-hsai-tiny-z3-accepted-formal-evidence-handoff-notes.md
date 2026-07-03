# Phase 413 HSAI Tiny Z3 Accepted Formal Evidence Handoff Notes

State slice: `Phase 413 HSAI tiny Z3 accepted-formal-evidence handoff`.

## Boundary

Phase 413 implements local accepted formal-evidence handoff metadata from one
Phase 411 tiny-Z3 reviewed formal-evidence record toward a future accepted
formal-evidence policy decision for:

```text
gateway-local-digest-binding-determinism-v1
```

The handoff records the current blocker: the accepted append path still blocks
formal-evidence promotion and the future formal-evidence acceptance policy is
unresolved. It does not implement accepted formal evidence, mutate the accepted
Evidence Ledger, change accepted append policy, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, execute Lean, execute COBALT, run Rust-to-Lean
extraction, submit benchmarks, deploy to production, or grant action
authority.

## Implemented Surface

Phase 413 adds these Rust surfaces under `hsai-agent-admission`:

- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_SCHEMA_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_STATE_SLICE`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_CLAIM_BOUNDARY`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_ACCEPTED_APPEND_POLICY_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_FORMAL_POLICY_VERSION`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_REQUESTED_CLASS`;
- `GATEWAY_FORMAL_TINY_DIGEST_BACKEND_Z3_ACCEPTED_HANDOFF_REQUESTED_CLAIM_BOUNDARY`;
- `GatewayFormalTinyDigestBackendZ3FormalAcceptancePolicyDecision`;
- `GatewayFormalTinyDigestBackendZ3AcceptedHandoffInput`;
- `GatewayFormalTinyDigestBackendZ3AcceptedHandoff`;
- `GatewayFormalTinyDigestBackendZ3AcceptedHandoffIssue`;
- `GatewayFormalTinyDigestBackendZ3AcceptedHandoffValidation`;
- `gateway_formal_tiny_digest_backend_z3_accepted_handoff_claim_boundary`;
- `gateway_formal_tiny_digest_backend_z3_accepted_handoff_required_nonclaims`;
- `gateway_formal_tiny_digest_backend_z3_accepted_handoff_current_blockers`;
- `build_gateway_formal_tiny_digest_backend_z3_accepted_handoff`;
- `validate_gateway_formal_tiny_digest_backend_z3_accepted_handoff_input`.

## Bound Provenance

The handoff binds:

- Phase 411 reviewed-record digest and input digest;
- Phase 409 review-preview digest and input digest;
- Phase 407 candidate digest and input digest;
- Phase 405 output-manifest digest;
- Phase 404 execution digest;
- Phase 403 probe digest;
- reviewer and verifier policy ids;
- reviewer decision id and timestamp;
- reviewed-scope statement digest;
- accepted-evidence-disabled acknowledgement digest;
- requested accepted-evidence class marker;
- requested claim-boundary marker;
- accepted append policy version;
- formal-evidence acceptance policy version;
- unresolved formal-evidence acceptance policy decision;
- current accepted append blocker digest;
- explicit nonclaim digest.

## Validation Rules

The validator rejects:

- invalid schema version, handoff id, or timestamps;
- missing or zero digests;
- Phase 411 reviewed-record digest drift;
- Phase 411 reviewed-record state drift;
- reviewer or verifier policy drift;
- requested accepted-evidence class drift;
- requested claim-boundary drift;
- accepted append policy-version drift;
- formal-evidence acceptance policy-version drift;
- non-unresolved formal-evidence policy decisions;
- current accepted append blocker drift;
- explicit nonclaim drift;
- accepted Evidence Ledger mutation attempts;
- accepted append policy-change attempts;
- accepted formal-evidence creation attempts;
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

- accepted-handoff metadata construction from a Phase 411 reviewed record;
- Phase 411 reviewed-record digest drift;
- reviewer policy drift;
- requested accepted-evidence class drift;
- requested claim-boundary drift;
- attempted formal-evidence policy approval;
- current accepted append blocker drift;
- promoted Phase 411 reviewed-record state drift;
- accepted evidence mutation, accepted policy change, accepted formal-evidence
  creation, Level2+, score-axis, proof/checker/solver promotion, SOTA,
  full-security, and authority attempts.

## Claim Boundary

Phase 413 supports only this claim:

```text
HSAI has local tiny-Z3 accepted formal-evidence handoff metadata that binds one
Phase 411 reviewed formal-evidence record to the current accepted append
blocker and an unresolved future policy decision.
```

That still does not support accepted formal evidence, accepted Evidence Ledger
mutation, accepted append policy change, Level2+ evidence, score-axis evidence,
a Lean proof, a COBALT containment proof, Rust-to-Lean extraction, checker
transcript evidence, solver certificate evidence, source correspondence proof,
whole-system proof, semantic correctness, production readiness, SOTA,
breakthrough status, full security, or authority to execute an action.

## Next Slice

Phase 414 should define a docs-first tiny-Z3 accepted formal-evidence policy
decision boundary. It must decide whether the current path remains forbidden or
whether a bounded class could be specified in a later phase. It must not mutate
accepted evidence, create accepted formal evidence, create Level2+ evidence,
populate score axes, claim semantic correctness, claim production readiness,
claim SOTA, claim breakthrough status, claim full security, or grant authority
to execute an action.
