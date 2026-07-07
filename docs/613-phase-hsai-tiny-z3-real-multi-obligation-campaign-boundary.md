# Phase 613 HSAI Tiny Z3 Real Multi-Obligation Campaign Boundary

State slice: `phase-613-hsai-tiny-z3-real-multi-obligation-campaign-boundary`.

## Purpose

Define the next local-only widening after the Phase 612 residual-ceiling
report: summarize multiple Phase 529 hermetic local Z3 result objects in one
in-memory campaign record.

This is a data-collection boundary only. It exists so later local work can see
more than one scoped obligation result without inventing a backend, deployment,
accepted formal evidence, Level2 evidence, or score-axis population.

## Authorized Future Implementation

A following implementation slice may add Rust types and tests under
`crates/hsai-agent-admission/src/lib.rs` for:

- a campaign request with campaign id, timestamp, expected obligation count,
  and optional mixed-verdict requirement;
- per-obligation observation metadata copied from existing Phase 529
  `GatewayFormalTinyZ3HermeticBackendExecutionResult` objects;
- an in-memory campaign summary with result counts, `unsat` and `sat` counts,
  unique-obligation checks, mixed-verdict visibility, and explicit
  nonpromotion flags;
- fail-closed validation that each source result remains Phase 529 local
  hermetic backend execution metadata with no accepted-evidence, Level2,
  score-axis, proof, checker, solver-certificate, Lean, COBALT,
  benchmark, semantic-correctness, production-readiness, SOTA, full-security,
  external-audit, human-review, or action-authority claim.

## Nonclaims

Phase 613 does not permit Rust implementation code, Cargo metadata changes,
new dependencies, solver execution, campaign output files, accepted Evidence
Ledger mutation, accepted external evidence, accepted formal evidence,
accepted independent external reproduction, Level2+ evidence, score-axis
population, proof artifacts, checker transcripts, solver certificates, Lean
execution, COBALT execution, Rust-to-Lean extraction, benchmark submission,
production deployment, external-audit claims, semantic-correctness claims,
production-readiness claims, SOTA claims, breakthrough claims, full-security
claims, global uniqueness claims, human-review acceptance claims, or authority
to execute an action.

## Exit Criteria

Phase 613 is complete when this boundary is documented and referenced from the
repo navigation/status files.
