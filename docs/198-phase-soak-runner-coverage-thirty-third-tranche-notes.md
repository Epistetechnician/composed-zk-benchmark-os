# Phase 198 Soak Runner Coverage Thirty-Third Tranche Notes

State slice: `phase-198-soak-runner-coverage-thirty-third-tranche`.

## Claim

Phase 198 continues the bounded local coverage campaign by hardening reachable
local soak runner behavior in `crates/zkbench-core`. The tranche adds focused
local regression tests for existing public contracts only. It changes no
production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 198 therefore targets the next reachable pure-data floor,
`soak/runner.rs`, without forcing unreachable branches or suppressing coverage.

## Implemented Coverage

- Public shard wrapper helpers run a local shard and resume the same shard from
  a materialized checkpoint while preserving `Level0DesignNote` boundaries.
- Stop-on-first-failure runner policy records one failed replay case for a
  three-case shard when the local adapter id drifts from the manifest.
- Failure-pack-only output writes a failure pack, avoids sampled pack output,
  records replay-failure telemetry, and extracts replay-failure corpus entries.
- All-packs-within-limit output accepts an overwrite-enabled stale sampled-pack
  directory and writes the current deterministic pack without deleting unrelated
  caller-owned files.

## Coverage Result

Baseline target: `soak/runner.rs` reported `78.41%` line coverage, `83.67%`
function execution, and `78.48%` region coverage.

Post-tranche target: `soak/runner.rs` reported `89.42%` line coverage,
`95.92%` function execution, and `90.08%` region coverage.

Post-tranche `zkbench-core` package coverage reported `89.90%` region coverage,
`85.42%` function execution, and `90.67%` line coverage.

Post-tranche workspace coverage reported `91.64%` region coverage, `87.95%`
function execution, and `91.95%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining lower floors are serializer-wrapper files whose
uncovered lines are structurally unreachable `serde_json::to_string_pretty`
error mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `soak/resume.rs` at `78.61%` line
coverage.

## Nonclaims

Phase 198 does not change local soak runner semantics, resume semantics,
output-pack semantics, failure-corpus semantics, telemetry semantics,
production source, Cargo metadata, dependencies, external execution, generated
artifact materialization, accepted Evidence Ledger policy, formal evidence,
benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.
