# Phase L Local Soak Acceptance Notes

## Status And Claim Boundary

Phase L is accepted for bounded local soak execution and sampled local report
generation as of 2026-06-17.

The accepted run is local operational telemetry only:

```text
Campaign: phase_l_qwable_local_soak_2026_06_17_extended_256
Claim boundary: Level0DesignNote
```

It is not official benchmark evidence, not ZK backend performance evidence, not
Level2 evidence, not accepted Evidence Record material, and not proof.

## State Slice

```text
.autoresearch/phase-l-qwable-overnight/
crates/zkbench-core/src/generator/config.rs
crates/zkbench-core/src/soak/config.rs
crates/zkbench-core/src/soak/runner.rs
crates/zkbench-core/tests/generator_determinism.rs
crates/zkbench-core/tests/soak_runner_smoke.rs
docs/21-phase-k-local-soak-runner-telemetry-notes.md
docs/61-phase-l-qwable-autoresearch-contract.md
docs/62-phase-l-local-soak-acceptance-notes.md
```

The durable campaign outputs live under the ignored artifact root. They are not
source artifacts and must not be used to claim official benchmark evidence.

## Accepted Campaign Result

The accepted extended local soak used the configured maximum seed count rather
than overriding the existing safety limits.

```text
planned_shards: 16
seed_range: 0..256
planned_cases: 768
planned_mutations: 2304
completed_cases: 768
mutation_variants_applied: 2048
targetless_mutation_combinations: 256
failed_cases: 0
failure_corpus_entries: 0
report_bundle_valid: true
report_bundle_issue_count: 0
aggregate_status: Healthy
contains_zk_backend_performance_claims: false
claim_boundary: Level0DesignNote
```

The `targetless_mutation_combinations` count is applicability telemetry. In the
accepted run it records `BranchingFsm` cases where `BadCounters` has no accepted
integer counter update target. Those combinations are not failure corpus entries
and do not fail the local soak case.

## Verification

The implementation and acceptance run were kept only after these checks passed:

```sh
cargo fmt --all --check
cargo test -p zkbench-core --test soak_runner_smoke
cargo run --manifest-path .autoresearch/phase-l-qwable-overnight/runner/Cargo.toml
cargo test --workspace
cargo test --workspace --features external-runner
cargo clippy --workspace --all-targets -- -D warnings
cargo doc --workspace --no-deps
```

The first attempted extension used `0..512` seeds and was rejected by the
existing `max_seeds = 256` guard. The accepted campaign used that configured
maximum instead of weakening the guard.

## Boundary Preserved

Phase L acceptance means the local benchmark OS loops can sustain a bounded
longer local run while preserving deterministic local health boundaries. It does
not authorize any of the following:

- live zk-Harness execution;
- external result import;
- official benchmark evidence;
- ZK backend performance claims;
- Level2+ evidence creation;
- dashboard claims;
- adapter-specific evidence promotion.

Future adapter work must still be opened by an explicit phase and must keep
recursion, zkML, and reproducible-pack claims evidence-capped.
