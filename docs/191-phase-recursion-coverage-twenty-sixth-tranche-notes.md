# Phase 191 Recursion Coverage Twenty-Sixth Tranche Notes

State slice: `phase-191-recursion-coverage-twenty-sixth-tranche`.

## Claim

Phase 191 continues the bounded local coverage campaign by hardening reachable
recursion-envelope and recursion-adapter metadata validation behavior in
`crates/zkbench-core`. The tranche adds focused local regression tests for
existing public contracts only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 191 therefore targets the next reachable `zkbench-core` floor,
`recursion.rs`, without forcing unreachable branches or suppressing coverage.

## Implemented Coverage

- Recursion-envelope empty identity and missing-input validation.
- Recursion-envelope invalid digest algorithm, byte length, and hex-shape
  validation.
- Recursion-envelope metric claim-boundary escalation validation.
- Recursion-adapter preparation empty plan shape, missing source inputs, and
  missing expected artifacts.
- Recursion-adapter nested source-input digest, path, append-preview boundary,
  and Level2 eligibility boundary rejection.
- Recursion-adapter expected-artifact identity and portable-path rejection.
- Recursion manual-handoff wrapper and mapping claim-boundary drift rejection.
- Malformed JSON deserialization context for recursion envelope candidates,
  adapter-preparation plans, and manual handoff bundles.

## Coverage Result

Baseline target: `recursion.rs` reported `84.30%` region coverage, `84.21%`
function execution, and `77.29%` line coverage.

Post-tranche target: `recursion.rs` reported `96.83%` region coverage,
`92.11%` function execution, and `97.05%` line coverage.

Post-tranche `zkbench-core` package coverage reported `88.46%` region coverage,
`83.77%` function execution, and `89.10%` line coverage.

Post-tranche workspace coverage reported `90.70%` region coverage, `86.81%`
function execution, and `90.83%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floors are `pack/reader.rs` and
`evidence/review.rs`, tied at `77.40%` line coverage.

## Nonclaims

Phase 191 does not change recursion-envelope semantics, recursion-adapter
semantics, production source, Cargo metadata, dependencies, external execution,
generated artifact materialization, accepted Evidence Ledger policy, formal
evidence, benchmark evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.
