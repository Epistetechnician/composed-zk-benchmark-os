# Phase 800 — Serving Efficiency Lane Inert Metadata

Status: implemented.

Named state slice: `phase-800-serving-efficiency-lane-inert-metadata`.

Claim boundary: `Level0DesignNote`.

This phase implements the inert-metadata slice anticipated by the Phase 799
memory architecture sustainability and serving efficiency boundary
(`docs/799-phase-memory-architecture-sustainability-serving-efficiency-boundary.md`).
It adds one isolated pure-data crate, `crates/serving-efficiency-lane`, with
serde and sha2 as its only dependencies. The crate performs no model
execution, serving, benchmarking, network, process, environment, filesystem,
or evidence-lane I/O.

## What Was Built

- `CandidateClass` — the four Phase 799 candidate classes
  (`kda_hybrid_attention_model_lane`, `serving_side_kv_management`,
  `disaggregated_kv_storage_routing`, `agent_memory_policy_mode`) with a
  closed `PANEL`.
- `CandidateDisposition` — closed at `ReferenceOnly`; extending the enum is
  itself a future reviewed state slice.
- `EvaluationRegime` — `normalized_causal` and `native_best_deployment`, with
  `require_single_regime` rejecting pooled regime claims.
- `ServingBaselineDescriptor` — the Phase 799 recorded serving baseline, bound
  to the Phase 57+ Phala CVM attestation fixture by path, SHA-256
  `33135af6b978a4f0255cdcf453c3479c46b1fa2d8aac8f019649b4c1ed6becf3`, and byte
  length `54662`. `validate_baseline` is exact-equality fail-closed: the
  baseline is a recorded fact, not a tunable.
- `ServingEfficiencyLaneDescriptor`, `default_lane_descriptor`, and
  `validate_lane_descriptor` — state slice, schema version, baseline binding,
  non-empty duplicate-free candidate set, `ReferenceOnly` disposition, and
  default inert claim boundary, all fail-closed.
- `PreregisteredGates`, `MeasuredResults`, `EvaluationRequest`,
  `EvaluationReport`, and `ClaimCeiling::InertMetadataOnly` — evaluation
  contracts with separated `cached_input_tokens` / `uncached_input_tokens`
  cost lines, finite/range validation, and digest-chained request/report
  binding.
- `evaluate_adoption` — fail-closed adoption metadata. `adoption_authorized`
  is false unless every preregistered gate passes and the request names a
  separately reviewed adoption phase state slice. Even then it is a
  metadata-level decision only: actual adoption still requires license and
  supply-chain review, attestation compatibility, and measured regime evidence
  per Phase 799 section 5.
- `LaneClaimBoundary` — default `inert_metadata_only = true` with
  accepted-evidence, benchmark-evidence, production-readiness, SOTA, and
  authority flags all false; claim escalation rejects.
- Domain-separated `tagged_sha256` digests for baseline, lane descriptor,
  evaluation request, and evaluation report, with lowercase-hex encoding and
  validation helpers.

## Fail-Closed Behaviors

Eleven focused integration tests cover: baseline fixture digest agreement with
the repository file; inert default descriptor and `ReferenceOnly` disposition
for every candidate class; lane validation failure for wrong state slice,
wrong schema version, empty candidate set, duplicate candidate, claim
escalation, and baseline drift; baseline digest sensitivity; tagged-hash
determinism and field binding; adoption staying unauthorized without a named
reviewed phase; every gate (cost, reliability, latency, concurrency) blocking
adoption individually; request/report digest and regime binding failures;
regime pooling rejection; non-finite and out-of-range metric rejection; and
cached/uncached cost-line digest binding.

## Focused Gate Results

```text
cargo fmt -p serving-efficiency-lane -- --check                          PASS
cargo clippy -p serving-efficiency-lane --all-targets -- -D warnings     PASS
cargo test -p serving-efficiency-lane                                    PASS (11 tests)
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan         PASS (7 tests)
```

The workspace claim-boundary source scan covers the new crate and confirms no
process or network API usage and no `Proven` maturity emission.

## Claim Ceiling

This phase is inert local metadata only. It is not model execution, serving,
benchmark evidence, accepted evidence, Level2+ evidence, production readiness,
semantic correctness, SOTA, breakthrough, independent audit, full security, or
action authority. It adopts no candidate technology and changes no deployment.
Model-architecture facts about the served model remain sourced from the
model's public documentation and are not verified by this repository.

## Prohibitions

This phase does not permit model download or acquisition, provider spend, CVM
manifest changes, deployment changes, benchmark execution, accepted Evidence
Ledger mutation, evidence promotion, or any claim above `Level0DesignNote`.
