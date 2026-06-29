# Phase 213 HSAI Gateway Effectiveness Metrics Notes

Status: complete for local hermetic implementation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/213-hsai-gateway-effectiveness-metrics-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Purpose

Implement a local effectiveness-summary surface for the HSAI Agent Approval
Gateway. The summary turns validated local corpus report data into buyer-facing
metrics without claiming official benchmark evidence or production readiness.

## Implemented

Phase 213 adds:

- `GatewayThreatCoverageRow`
- `GatewayEffectivenessSummary`
- `gateway_effectiveness_summary`

The summary validates the HSAI gateway report, then computes:

- unsafe case count;
- benign expected-accept count;
- unsafe action block rate in basis points;
- false rejection rate in basis points;
- quarantine rate in basis points;
- decision recomputation agreement rate in basis points;
- audit-bundle completeness;
- covered threat labels;
- per-threat case and blocked counts;
- explicit local claim boundary;
- `authority_granted = false`.

## Tests

Focused tests cover:

- full local adversarial corpus rates and threat coverage;
- invalid HSAI reports failing closed;
- zero-denominator rate handling for benign-only corpora.

## Claim Boundary

This is local summary metadata only. It is not a live metric collection system,
not benchmark evidence, not official evidence, not external replay, not model
execution, not production readiness, not semantic correctness, not accepted
Evidence Ledger mutation, not score-axis population, not signer/tool
integration, not custody, not fully secure, and not a claim above `Attested`.

## Validation

Run from repository root:

```sh
cargo fmt --all --check
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```
