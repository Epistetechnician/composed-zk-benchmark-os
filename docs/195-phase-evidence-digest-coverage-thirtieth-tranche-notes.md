# Phase 195 Evidence Digest Coverage Thirtieth Tranche Notes

State slice: `phase-195-evidence-digest-coverage-thirtieth-tranche`.

## Claim

Phase 195 continues the bounded local coverage campaign by hardening reachable
evidence digest helper behavior in `crates/zkbench-core`. The tranche adds
focused local regression tests for existing public contracts only. It changes
no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 195 therefore targets the next reachable pure-data floor,
`evidence/digest.rs`, without forcing unreachable branches or suppressing
coverage.

## Implemented Coverage

- Deterministic struct serialization through `canonical_json_bytes`.
- `compute_artifact_digest` equivalence with the exact bytes returned by
  `canonical_json_bytes`.
- Raw byte digest metadata for algorithm, byte length, kind, role, and lowercase
  SHA-256 hex shape.
- Pretty versus compact JSON byte-level digest distinction.
- Metadata-only kind/role differences without changing the underlying content
  digest.
- Empty raw payload SHA-256 behavior.
- Real serialization-error propagation through both `canonical_json_bytes` and
  `compute_artifact_digest` by using a failing `Serialize` implementation.

## Coverage Result

Baseline target: `evidence/digest.rs` reported `77.78%` line coverage,
`60.00%` function execution, and `74.36%` region coverage.

Post-tranche target: `evidence/digest.rs` reported `100.00%` line coverage,
`100.00%` function execution, and `97.44%` region coverage.

Post-tranche `zkbench-core` package coverage reported `89.36%` region coverage,
`84.85%` function execution, and `90.04%` line coverage.

Post-tranche workspace coverage reported `91.29%` region coverage, `87.56%`
function execution, and `91.50%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `soak/config.rs` at `78.21%` line
coverage.

## Nonclaims

Phase 195 does not change digest semantics, serialization policy, production
source, Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, real score-axis population, Level2+ evidence, semantic-correctness
claims, production-readiness claims, unsafe coverage forcing, coverage
suppression, structurally unreachable serialization-error forcing, or
whole-workspace 100% coverage claims.
