# Phase 201 Evidence Accepted Append Coverage Thirty-Sixth Tranche Notes

State slice: `phase-201-evidence-accepted-append-coverage-thirty-sixth-tranche`.

## Claim

Phase 201 continues the bounded local coverage campaign by hardening reachable
`accepted_append.rs` validation and append-report behavior in `crates/zkbench-core`.
The tranche adds focused local regression tests for existing public contracts
only. It changes no production Rust source.

The prior measured floor check confirmed that `replay/serialization.rs` and
`external_runner/serialization.rs` remain capped by structurally unreachable
`serde_json::to_string_pretty` error mappings for concrete derived structs.
Phase 201 targets the next visible non-serializer `zkbench-core` floor,
`evidence/accepted_append.rs`, without forcing unreachable branches or
suppressing coverage.

## Implemented Coverage

- Empty transaction and target-ledger identities are rejected.
- Invalid target ledgers are rejected before accepted-ledger append.
- Tampered preflight reports and mutating report flags are rejected.
- Invalid preflight requests remain invalid at transaction validation time.
- Current-tip drift is detected across the transaction, preflight request, and
  append-preview tip paths.
- Append-preview source-candidate, entry-count, entry-candidate,
  evidence-class, and claim-boundary drift are rejected.
- Missing source artifact digests are rejected and record conversion fails
  closed.
- Forbidden transaction note text is rejected.
- Post-append ledger validation rejects forbidden transaction-id text once it
  would be materialized into an evidence-record note.

## Coverage Result

Baseline target: `evidence/accepted_append.rs` reported `79.77%` line coverage,
`84.62%` function execution, and no branch data in the LCOV baseline used for
line-level auditing.

Post-tranche target: `evidence/accepted_append.rs` reported `98.29%` line
coverage, `92.31%` function execution, and no branch data in the LCOV after-run.

Post-tranche `zkbench-core` package coverage reported `90.13%` region coverage,
`85.71%` function execution, and `91.11%` line coverage.

Post-tranche workspace coverage reported `91.79%` region coverage, `88.15%`
function execution, and `92.26%` line coverage.

The remaining uncovered lines in `evidence/accepted_append.rs` are the defensive
`append reported success but ledger has no entries` guard after
`EvidenceLedger::append` returns `Ok`, and the `compute_artifact_digest` error
mapping over the concrete `EvidenceRecordCandidate` type. This tranche did not
force those branches.

The package floor is now `soak/health.rs` at `79.00%` line coverage. The lower
serializer-wrapper floors remain known caps: `replay/serialization.rs` at
`80.00%` and `external_runner/serialization.rs` at `80.69%` line coverage in
the after-LCOV run.

## Nonclaims

Phase 201 does not change accepted-append semantics, preflight semantics,
evidence-ledger semantics, candidate digest semantics, production source, Cargo
metadata, dependencies, external execution, generated artifact materialization,
accepted Evidence Ledger policy, formal evidence, benchmark evidence, real
score-axis population, Level2+ evidence, semantic-correctness claims,
production-readiness claims, unsafe coverage forcing, coverage suppression,
structurally unreachable serialization-error forcing, defensive
post-append-empty-ledger guard forcing, or whole-workspace 100% coverage claims.
