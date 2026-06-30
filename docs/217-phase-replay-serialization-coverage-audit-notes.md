# Phase 217 Replay Serialization Coverage Audit Notes

Status: complete for local coverage-floor audit.

## State Slice

This phase touched only:

- `docs/217-phase-replay-serialization-coverage-audit-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It also preserves the live Phase 214-216 documentation renumbering already
present in the worktree.

No Rust source, tests, Cargo metadata, generated artifacts, accepted Evidence
Ledger state, benchmark output, or score-axis state changed.

## Purpose

Audit the current `zkbench-core` package coverage floor after Phase 216 moved
`crates/zkbench-core/src/soak/health.rs` to `98.67%` line coverage.

The next measured floor is `crates/zkbench-core/src/replay/serialization.rs`.
This phase determines whether focused tests can honestly increase that floor
without fabricating impossible serializer failures or changing production
semantics.

## Coverage Measurement

The local package coverage command:

```sh
cargo llvm-cov -p zkbench-core --all-features --summary-only
```

reported for `zkbench-core`:

- region coverage: `90.28%`;
- function execution: `85.76%`;
- line coverage: `91.35%`.

The measured floor was:

- `crates/zkbench-core/src/replay/serialization.rs`: `75.00%` line coverage,
  `75.00%` function coverage, and `75.00%` region coverage.

The local missing-line audit command:

```sh
cargo llvm-cov report --text --show-missing-lines --output-path /tmp/zkbench-core-coverage-missing.txt
```

showed that the only uncovered lines in `replay/serialization.rs` are:

- line 10 and line 11: the `serialize_replay_manifest_json` `map_err`
  closure for `serde_json::to_string_pretty`;
- line 24 and line 25: the `serialize_replay_result_json` `map_err`
  closure for `serde_json::to_string_pretty`.

The deserializer error paths are already exercised: the same missing-line report
shows one hit each for the malformed JSON branches in
`deserialize_replay_manifest_json` and `deserialize_replay_result_json`.

## Audit Decision

No new Rust test was added.

The remaining uncovered lines are structurally capped under the current public
API because `ReplayManifest` and `ReplayResult` are concrete derived
serialization types. Reaching those `serde_json::to_string_pretty` error
closures would require changing the concrete types, adding dependency behavior,
or injecting a failing serializer path that the production API does not expose.

That would be coverage forcing, not regression coverage.

## Next Reachable Floor

The next visible low file remains
`crates/zkbench-core/src/external_runner/serialization.rs` at `76.65%` line
coverage in the same local package run.

That file should receive the same audit-first treatment: add tests only for
reachable public deserializer or wrapper behavior, and document any remaining
concrete-type serializer caps instead of forcing impossible serde failures.

## Claim Boundary

This is a coverage audit only. It does not change local replay semantics,
serialization semantics, production source, Cargo metadata, dependencies,
external execution, generated artifact materialization, accepted Evidence Ledger
policy, formal evidence, benchmark evidence, score-axis population, Level2+
evidence, semantic-correctness claims, production-readiness claims, unsafe
coverage forcing, coverage suppression, structurally unreachable branch forcing,
or whole-workspace 100% coverage claims.

## Validation

Validation passed for this docs-only audit:

```sh
cargo fmt --all --check
git diff --check
cargo test -p zkbench-core --test replay_manifest_serialization
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test -p zkbench-core --test repo_hygiene
cargo test --workspace --quiet
cargo llvm-cov -p zkbench-core --all-features --summary-only
```
