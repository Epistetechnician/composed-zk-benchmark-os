# Phase 236 Soak Campaign Coverage Notes

## State Slice

Phase 236 is the soak-campaign coverage tranche for
`crates/zkbench-core/src/soak/campaign.rs`.

This slice is limited to a narrow local campaign adapter-injection helper under
`crates/zkbench-core/src/soak/`, public re-export updates under
`crates/zkbench-core/src/lib.rs`, focused Rust tests under
`crates/zkbench-core/tests/`, and navigation/status updates under `docs/`,
`README.md`, and `AGENTS.md`.

## Purpose

Phase 235 routed the next local coverage target to `soak/campaign.rs` after
`external_runner/policy.rs` reached `97.63%` line coverage.

The Phase 236 missing-line audit found uncovered reachable paths in:

- empty campaign id validation;
- campaign report-bundle write failure propagation after aggregate JSON write;
- campaign handling for pack-write failures without retained failure packs;
- reproduction-bundle attachment for retained failure packs produced during an
  approved local campaign.

## Implemented Coverage

Phase 236 adds focused tests to
`crates/zkbench-core/tests/phase_l_soak_campaign.rs`:

- `campaign_config_rejects_empty_campaign_id_before_portability_check`;
- `campaign_records_pack_write_failures_without_missing_reproduction_pack_attachment`;
- `campaign_with_explicit_adapter_attaches_reproduction_bundle_to_failure_pack`;
- `campaign_reports_bundle_write_failure_after_aggregate_json_write`.

To test the retained failure-pack path through a real public campaign API,
Phase 236 adds `run_soak_campaign_with_local_json_adapter`. The helper is
bounded to the existing local JSON adapter, still runs under explicit campaign
approval and artifact-root policy, and still writes only local soak health
artifacts.

## Coverage Result

Baseline before Phase 236:

- `soak/campaign.rs`: `85.42%` region / `90.91%` function / `85.79%` line
  coverage.
- `zkbench-core` package total: `91.72%` region / `87.64%` function /
  `93.47%` line coverage.

Measured after Phase 236:

- `soak/campaign.rs`: `96.15%` region / `100.00%` function / `97.49%` line
  coverage.
- `zkbench-core` package total: `91.83%` region / `87.71%` function /
  `93.56%` line coverage.

## Remaining Cap

The local missing-line report still lists `soak/campaign.rs` lines 211, 219,
225, 231, and 298 after rustfmt line numbering.

Lines 211, 219, 225, and 231 are error returns from internally constructed
`soak_artifact_manifest` calls whose ids and paths are derived from already
validated campaign ids, shard ids, and fixed artifact-layout paths. Line 298 is
the defensive branch for a retained failure pack with no matching failure
corpus entry; the shipped runner records matching corpus entries when it records
case failures. Phase 236 does not weaken those invariants or add test-only entry
points to force the defensive branches.

## Claim Boundary

This phase proves only that the local Rust test suite now exercises the
reachable soak-campaign validation, report-write failure, failure-pack skip, and
retained failure-pack reproduction-bundle attachment paths listed above.

It does not prove semantic correctness, production readiness, live external
runner safety, benchmark performance, official benchmark evidence, accepted
Evidence Ledger mutation, formal evidence, score-axis population, live provider
evidence, Level2+ evidence, SOTA status, or breakthrough status.

## Validation Commands

The following commands passed locally:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test phase_l_soak_campaign
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

The final Phase 236 gate also ran:

```sh
git diff --check
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
```

## Next Coverage Candidate

After Phase 236, `soak/campaign.rs` is capped by the structural branches listed
above. The lowest remaining non-serializer line-coverage candidate in the
current package summary is `mutation/invariant_strengthening.rs` at `86.00%`,
subject to a fresh missing-line audit before any mutation.
