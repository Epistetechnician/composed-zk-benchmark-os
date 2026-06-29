# Phase 212 HSAI Gateway Baseline Comparison Notes

Status: complete for local hermetic implementation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/212-hsai-gateway-baseline-comparison-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Purpose

Implement the first local baseline-comparison surface for the HSAI Agent
Approval Gateway. The comparison lets a local adversarial corpus report be
compared against simple baseline decisions without making official benchmark,
production-readiness, or semantic-correctness claims.

This is the first code-level support for the PRD's "Baselines To Beat" section.
It remains local metadata only.

## Implemented

Phase 212 adds:

- `GatewayBaselineKind`
- `GatewayBaselineDecision`
- `GatewayBaselineRun`
- `GatewayBaselineComparison`
- `GatewayBaselineComparisonIssue`
- `GatewayBaselineComparisonError`
- `gateway_baseline_required_nonclaims`
- `compare_gateway_baseline`

The comparison validates the HSAI gateway report, validates baseline decision
shape, requires local nonclaims, then computes:

- HSAI unsafe accepted count;
- baseline unsafe accepted count;
- HSAI false rejection count;
- baseline false rejection count;
- HSAI audit-bundle completeness;
- baseline audit-bundle completeness;
- explicit local claim boundary;
- `authority_granted = false`.

## Tests

Focused tests cover:

- a no-approval baseline accepting unsafe adversarial cases while HSAI blocks
  them;
- malformed HSAI reports failing closed;
- missing baseline nonclaims failing closed;
- duplicate, missing, and unknown baseline decisions failing closed.

## Claim Boundary

This is local comparison metadata only. It is not a live baseline run, not a
benchmark, not official evidence, not external replay, not a model execution,
not an LLM judge, not production readiness, not semantic correctness, not
accepted Evidence Ledger mutation, not score-axis population, not signer/tool
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
