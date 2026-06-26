# Phase 189 External Runner Importer Coverage Twenty-Fourth Tranche Notes

State slice: `phase-189-external-runner-importer-coverage-twenty-fourth-tranche`.

## Claim

Phase 189 continues the bounded local coverage campaign by hardening reachable
synthetic external-runner importer behavior in `crates/zkbench-core`. The
tranche adds focused local regression tests for existing public contracts only.
It changes no production Rust source.

The initial measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` are capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 189 therefore moved to the next reachable `zkbench-core` floor,
`external_runner/importer.rs`, without forcing unreachable branches or
suppressing coverage.

## Implemented Coverage

- Relative-file artifact resolver success, traversal rejection, and missing
  file error mapping.
- `SyntheticResultImporter::import_candidate_json` malformed JSON
  deserialization context.
- Explicit importer config/source preservation on quarantine bundles.
- Invalid synthetic import config and artifact-capture contract forwarding.
- Resolver digest algorithm, resolver-byte drift, and missing candidate digest
  rejection paths.
- Metric parse failure, metric source path rejection, and nested official,
  formal, and soundness claim text detection.

## Coverage Result

Baseline target: `external_runner/importer.rs` reported `77.34%` region
coverage, `81.82%` function execution, and `77.00%` line coverage.

Post-tranche target: `external_runner/importer.rs` reported `93.11%` region
coverage, `93.18%` function execution, and `92.84%` line coverage.

Post-tranche `zkbench-core` package coverage reported `88.14%` region coverage,
`83.49%` function execution, and `88.51%` line coverage.

Post-tranche workspace coverage reported `90.50%` region coverage, `86.62%`
function execution, and `90.42%` line coverage.

The package floor remains `replay/serialization.rs` at `75.00%` line coverage.
The next visible floor is `external_runner/serialization.rs` at `76.65%` line
coverage. Both remaining floors are serializer-wrapper files whose uncovered
lines are structurally unreachable `serde_json::to_string_pretty` error
mappings for concrete derived structs; this tranche did not force those
branches or suppress coverage.

The next reachable `zkbench-core` floor is `generator/instance.rs` at `77.27%`
line coverage.

## Nonclaims

Phase 189 does not change external-runner importer semantics, production
source, Cargo metadata, dependencies, external execution, generated artifact
materialization, accepted Evidence Ledger policy, formal evidence, benchmark
evidence, real score-axis population, Level2+ evidence,
semantic-correctness claims, production-readiness claims, unsafe coverage
forcing, coverage suppression, structurally unreachable serialization-error
forcing, or whole-workspace 100% coverage claims.
