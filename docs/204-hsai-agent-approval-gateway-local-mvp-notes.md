# Phase 204 HSAI Agent Approval Gateway Local MVP Notes

Status: implemented for a local, hermetic Agent Approval Gateway MVP.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/204-hsai-agent-approval-gateway-local-mvp-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No Cargo metadata, dependencies, package runtime files, model weights, prompts,
generated corpora, generated output bundles, external replay outputs, signer or
tool integrations, accepted Evidence Ledger entries, score reports, or benchmark
outputs are part of this phase.

## Implemented Surface

The `hsai-agent-admission` crate now includes a local gateway layer over the
existing admission primitives:

- `GatewayActionId`
- `GatewayActionKind`
- `GatewayThreatLabel`
- `GatewayModelLaneKind`
- `GatewayModelLaneProvenance`
- `GatewayActionProposal`
- `GatewayPolicyViolation`
- `GatewayActionPolicy`
- `GatewayAcceptedHandoff`
- `GatewayActionOutcome`
- `GatewayCorpusCase`
- `GatewayRunMetrics`
- `GatewayCorpusReport`
- `gateway_required_nonclaims`
- `gateway_local_default_policy`
- `gateway_action_candidate`
- `evaluate_gateway_action`
- `accepted_gateway_handoff`
- `evaluate_gateway_corpus`
- `gateway_run_metrics`

The implementation maps a typed gateway proposal into an
`AgentAdmissionCandidate` with `AdmissionSourceKind::GatewayActionProposal`.
Gateway policy violations become deterministic admission reasons, and the
existing `AgentAdmissionJournal` remains the append-only authority/audit path.

Accepted gateway actions expose only a `GatewayAcceptedHandoff`. They do not
export a `ClaimEnvelope`, mutate an accepted Evidence Ledger, execute a signer or
tool, or perform any external action.

## Trust Rules Preserved

- Model output remains proposal-only.
- Strict typed gateway proposals are required before admission.
- Direct authority requests are rejected.
- Signer/tool requests before admission are rejected.
- Gateway decisions are recomputable through the existing admission policy.
- Rejected and quarantined decisions remain appendable audit metadata.
- Rented or hosted model output remains untrusted proposal metadata.
- Local gateway metrics remain local experimental data only.

## Focused Tests

Added focused coverage for:

- accepted gateway actions exposing a handoff only after admission;
- rejected gateway actions preserving audit metadata without a handoff;
- corpus metrics over accepted and unsafe cases;
- duplicate-key and policy-downgrade threat-label detection counts;
- decision recomputation agreement counts;
- journal completeness checks;
- replay rejection through the existing journal-chain duplicate candidate guard.

The focused admission suite now has 45 library tests.

## Claim Boundary

This is a local MVP only. It is not production readiness. It is not a signer,
wallet, custody, exchange, checkout, MCP, ACP, deployment, or payment
integration. It performs no model execution, no model download, no network
access, no credential access, no external replay, no official benchmark
submission, no accepted Evidence Ledger mutation, no score-axis population, and
no benchmark execution.

Gateway acceptance means only that a strict typed proposal passed the local
gateway policy and existing local admission policy. It is not proof. It is not
semantic correctness. It is not fraud prevention. It is not full security. It is
not global software-agent uniqueness. It is not Level2+ evidence. It is not a
claim above `Attested`.

## Validation

Run from repository root:

```sh
cargo fmt --all --check
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
```
