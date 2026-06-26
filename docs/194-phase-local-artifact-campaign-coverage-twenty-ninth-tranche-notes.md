# Phase 194 Local Artifact Campaign Coverage Twenty-Ninth Tranche Notes

State slice: `phase-194-local-artifact-campaign-coverage-twenty-ninth-tranche`.

## Claim

Phase 194 continues the bounded local coverage campaign by hardening reachable
local artifact campaign validation and readback behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 194 therefore targets the next reachable pure-data floor,
`local_artifact_campaign.rs`, without forcing unreachable branches or
suppressing coverage.

## Implemented Coverage

- Empty campaign identity, invalid campaign id, duplicate artifact URI, invalid
  digest, and weaker-input boundary validation paths.
- Missing input and invalid artifact-ref scheme validation paths.
- Markdown rendering rejection for invalid manifests and invalid validation
  reports.
- Empty output root, existing file output root, and non-directory readback
  rejection.
- Digest-consistent malformed and non-UTF8 manifest readback failures.
- Digest-consistent malformed validation JSON, validation semantic drift, and
  rendered Markdown semantic drift failures.
- Non-UTF8 digest sidecar and non-UTF8 rendered Markdown failures.

## Coverage Result

Baseline target: `local_artifact_campaign.rs` reported `78.42%` region
coverage, `62.71%` function execution, and `77.69%` line coverage.

Post-tranche target: `local_artifact_campaign.rs` reported `85.30%` region
coverage, `72.88%` function execution, and `90.53%` line coverage.

Post-tranche `zkbench-core` package coverage reported `89.32%` region coverage,
`84.74%` function execution, and `90.01%` line coverage.

Post-tranche workspace coverage reported `91.26%` region coverage, `87.48%`
function execution, and `91.48%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `evidence/digest.rs` at `77.78%`
line coverage.

## Nonclaims

Phase 194 does not change local artifact campaign semantics, output-root
semantics, production source, Cargo metadata, dependencies, external execution,
generated artifact materialization, accepted Evidence Ledger policy, formal
evidence, benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.
