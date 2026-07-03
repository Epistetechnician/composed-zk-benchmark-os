# Phase 337 HSAI Accepted Formal Evidence Policy Decision Metadata Notes

State slice: `Phase 337 HSAI accepted formal-evidence policy-decision metadata implementation`.

## Boundary

Phase 337 implements local policy-decision metadata over one Phase 335 handoff.
It records that accepted formal evidence remains forbidden in the current
accepted append path.

This phase does not implement accepted formal evidence, mutate the accepted
Evidence Ledger, change accepted append policy, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, execute Lean, execute COBALT, run Rust-to-Lean
extraction, submit benchmarks, or deploy to production.

## Implemented Surface

Phase 337 adds these public Rust surfaces in `crates/hsai-agent-admission`:

- `GATEWAY_FORMAL_REAL_COMMAND_LANE_POLICY_DECISION_SCHEMA_VERSION`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_POLICY_DECISION_STATE_SLICE`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_POLICY_DECISION_VERSION`.
- `GATEWAY_FORMAL_REAL_COMMAND_LANE_POLICY_DECISION_CLAIM_BOUNDARY`.
- `GatewayFormalRealCommandLanePolicyDecisionInput`.
- `GatewayFormalRealCommandLanePolicyDecision`.
- `GatewayFormalRealCommandLanePolicyDecisionIssue`.
- `GatewayFormalRealCommandLanePolicyDecisionValidation`.
- `gateway_formal_real_command_lane_policy_decision_claim_boundary`.
- `gateway_formal_real_command_lane_policy_decision_statement`.
- `gateway_formal_real_command_lane_policy_decision_required_nonclaims`.
- `build_gateway_formal_real_command_lane_policy_decision`.
- `validate_gateway_formal_real_command_lane_policy_decision_input`.

The policy-decision record binds:

- Phase 335 handoff digest.
- Phase 335 handoff-input digest.
- Phase 333 reviewed-record digest.
- accepted append policy version.
- source formal-evidence acceptance policy version.
- Phase 337 policy-decision version.
- current-path policy decision.
- policy-decision statement digest.
- current accepted append blocker digest.
- explicit nonclaim digest.

## Current-Path Decision

The only valid Phase 337 decision is:

```text
AcceptedFormalEvidenceStillForbidden
```

The canonical decision statement is:

```text
accepted formal evidence remains forbidden in the current accepted append path
```

This records the Phase 336 boundary in local metadata. It does not authorize a
bounded formal-evidence class.

## Validation

The validator rejects:

- invalid schema version, decision id, or timestamp;
- missing or zero digests;
- Phase 335 handoff digest drift;
- Phase 335 handoff state drift;
- accepted append policy-version drift;
- source formal-evidence policy-version drift;
- Phase 337 policy-decision version drift;
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

Focused tests now cover:

- policy-decision metadata construction from a Phase 335 handoff;
- handoff digest drift;
- accepted append policy-version drift;
- attempted bounded formal-evidence class approval;
- current accepted append blocker drift;
- policy-decision statement drift;
- promoted handoff state drift;
- accepted evidence mutation, accepted append policy change, Level2+,
  score-axis, proof/checker/solver promotion, SOTA, full-security, and authority
  attempts.

## Claim Boundary

The maximum claim after Phase 337 is:

```text
HSAI has local policy-decision metadata recording that accepted formal evidence
remains forbidden in the current accepted append path, bound to one Phase 335
handoff and the current accepted append blocker set.
```

That still does not support:

- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy changes;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a checker transcript;
- a solver certificate;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Next Slice

Phase 338 may define a docs-first bounded formal-evidence class feasibility
boundary. It must not implement the class, mutate accepted evidence, change
accepted append policy, create Level2+ evidence, populate score axes, or claim
semantic correctness, production readiness, SOTA, full security, or action
authority.
