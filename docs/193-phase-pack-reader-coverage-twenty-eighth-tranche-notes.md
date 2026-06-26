# Phase 193 Pack Reader Coverage Twenty-Eighth Tranche Notes

State slice: `phase-193-pack-reader-coverage-twenty-eighth-tranche`.

## Claim

Phase 193 continues the bounded local coverage campaign by hardening reachable
benchmark-pack reader validation and readback behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 193 therefore targets the next reachable pure-data floor,
`pack/reader.rs`, without forcing unreachable branches or suppressing coverage.

## Implemented Coverage

- Missing and malformed `pack.json` reader errors.
- Manifest-level non-relative and parent-traversing pack file rejection.
- Direct evidence-ledger and score-report path validation through reader load
  helpers.
- Missing optional file handling as nonblocking validation.
- Missing required file handling as validation failure.
- Missing evidence-ledger role, missing evidence-ledger file, and malformed
  evidence-ledger JSON readback failures.
- Missing score-report file and malformed score-report JSON readback failures.
- Claim-boundary elevation rejection and remaining summary/id drift checks.
- Explicit safe nonclaim note exemptions for official benchmark-evidence/result
  wording.

## Coverage Result

Baseline target: `pack/reader.rs` reported `75.44%` region coverage, `75.00%`
function execution, and `77.40%` line coverage.

Post-tranche target: `pack/reader.rs` reported `97.97%` region coverage,
`100.00%` function execution, and `97.95%` line coverage.

Post-tranche `zkbench-core` package coverage reported `89.07%` region coverage,
`84.40%` function execution, and `89.60%` line coverage.

Post-tranche workspace coverage reported `91.10%` region coverage, `87.24%`
function execution, and `91.19%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `local_artifact_campaign.rs` at
`77.69%` line coverage.

## Nonclaims

Phase 193 does not change benchmark-pack reader semantics, benchmark-pack
manifest semantics, production source, Cargo metadata, dependencies, external
execution, generated artifact materialization, accepted Evidence Ledger policy,
formal evidence, benchmark evidence, real score-axis population, Level2+
evidence, semantic-correctness claims, production-readiness claims, unsafe
coverage forcing, coverage suppression, structurally unreachable
serialization-error forcing, or whole-workspace 100% coverage claims.
