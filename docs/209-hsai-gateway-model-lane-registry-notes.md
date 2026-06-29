# Phase 209 HSAI Gateway Model Lane Registry Notes

Status: complete for local hermetic implementation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/209-hsai-gateway-model-lane-registry-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Purpose

Implement the first local Model Lane Registry surface for the HSAI Agent
Approval Gateway. The registry records and validates the model-lane provenance
that future local, rented, hosted, or premium adversarial lanes must disclose
before their outputs are treated as typed proposal metadata.

This registry is not a runtime model router. It does not execute models,
download weights, call providers, or grant authority. It is a deterministic
metadata validation layer for non-secret model-lane provenance.

## Implemented

Phase 209 adds:

- `GatewayModelLaneRegistryEntry`
- `GatewayModelLaneRegistry`
- `GatewayModelLaneRegistryIssue`
- `validate_gateway_model_lane_registry`

The validator rejects:

- invalid lane ids;
- duplicate lane ids;
- missing or invalid model family / artifact ids;
- missing prompt-template digests;
- missing non-secret statements;
- stale output-bundle digests;
- unbounded rented, hosted-small, or premium-escalation lane metadata.

Rented, hosted-small, and premium-escalation lanes must declare bounded
`max_cases_per_run` and `max_cost_units_per_case` values. Local lanes may still
be bounded by policy, but this phase only makes external-cost lanes fail closed
when their metadata is unbounded.

## Tests

Focused tests cover:

- accepting bounded local and rented lanes;
- rejecting missing model id and prompt digest metadata;
- rejecting missing non-secret statements and stale output digests;
- rejecting unbounded rented metadata;
- rejecting invalid and duplicate lane ids.

## Claim Boundary

This is local provenance metadata only. It is not model execution, not model
download, not provider verification, not a hosted-model call, not a runtime
router, not cost telemetry, not a generated corpus, not benchmark evidence, not
Level2+ evidence, not accepted Evidence Ledger mutation, not score-axis
population, not production readiness, not semantic correctness, not signer/tool
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
