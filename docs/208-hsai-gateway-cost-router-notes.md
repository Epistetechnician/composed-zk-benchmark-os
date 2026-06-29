# Phase 208 HSAI Gateway Cost Router Notes

Status: complete for local hermetic implementation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/208-hsai-gateway-cost-router-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Purpose

Implement the first local cost-router surface for the HSAI Agent Approval
Gateway. The router decides how much review effort a typed gateway action
deserves before admission, without granting authority or executing any model,
tool, signer, wallet, payment, custody, or external rail.

This closes one product gap from the PRD: HSAI can reduce token spend by
deterministically handling routine or obviously invalid actions, using cheap
local review for moderate actions, routing threat-labeled actions to a verifier
mixture, escalating only high-value cases within budget, and failing closed to
operator review when premium escalation exceeds budget or the action is
operator-only.

## Implemented

Phase 208 adds:

- `GatewayCostRoute`
- `GatewayCostRouteReason`
- `GatewayCostRouterPolicy`
- `GatewayCostRouteDecision`
- `gateway_cost_router_default_policy`
- `route_gateway_action_cost`

The router is deterministic and local. It first maps the proposal through the
existing `gateway_action_candidate` policy surface. If that produces gateway
policy violations, the router returns `DeterministicOnly` with zero estimated
model cost. Clean moderate-value actions route to local open-weight review.
Threat-labeled actions route to verifier mixture review. High-value actions
route to premium escalation only when the configured budget covers the
escalation cost. Deployments and over-ceiling values route to operator review.

Every `GatewayCostRouteDecision` carries `authority_granted = false`.

## Tests

Focused tests cover:

- deterministic policy violations consuming no model-review cost;
- moderate clean actions routing to local open-weight review;
- threat-labeled actions routing to verifier mixture review;
- exhausted premium budget failing closed to operator review;
- deployment actions requiring operator review even when otherwise policy
  allowed;
- every route preserving `authority_granted = false`.

## Claim Boundary

This is local routing metadata only. It is not model execution, not a model
router runtime, not a verifier-agent implementation, not a package runtime, not
a scheduler, not cost telemetry from a real provider, not a pricing engine, not
production readiness, not semantic correctness, not benchmark evidence, not
Level2+ evidence, not accepted Evidence Ledger mutation, not score-axis
population, not signer/tool/payment/custody integration, not global
software-agent uniqueness, not fully secure, and not a claim above `Attested`.

## Validation

Run from repository root:

```sh
cargo fmt --all --check
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```
