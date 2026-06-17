# Phase K Local Soak Runner And Telemetry Notes

## Implemented

Phase K adds local-only soak infrastructure for the benchmark OS:

- `SoakRunConfig`, profile, scope, output, telemetry, claim-boundary, and limit models.
- Deterministic `SoakShardPlanner`, `SoakShardPlan`, `SoakShardManifest`, and `SoakShardId`.
- Resumable `SoakShardCheckpoint` with config digest and resume token validation.
- `LocalSoakRunner` library API.
- Internal benchmark OS telemetry reports.
- Local health reports.
- Failure corpus indexes, reproduction manifests, and minimization metadata.
- Local soak artifact layout and report bundle schemas.
- Deterministic JSON serialization helpers.

## Why Local Soak Is Valuable

Local soak runs repeatedly exercise the local pipeline:

```text
generated benchmark family
  -> concrete benchmark instance
  -> mutation variant
  -> local replay result
  -> optional benchmark pack
  -> internal telemetry
  -> local health report
  -> failure corpus
```

This catches deterministic generation regressions, mutation no-target drift, local replay failures, pack validation failures, claim-boundary elevation, and failure corpus growth before any future external adapter work.

## Claim Boundary

Local soak telemetry is not official benchmark evidence. Internal timing telemetry is not ZK backend performance. Failure corpus entries are reproduction aids, not accepted evidence.

Phase K artifacts stay conservative:

- soak configs are `Level0DesignNote`
- shard plans and manifests are `Level0DesignNote`
- shard checkpoints are `Level0DesignNote`
- telemetry reports are `Level0DesignNote`
- health reports are `Level0DesignNote`
- failure corpus indexes are `Level0DesignNote`
- report bundles are `Level0DesignNote`
- local replay artifacts remain `Level1LocalReplay` at most
- append previews remain preview-only
- no Phase K artifact creates accepted Level2+ evidence

A benchmark pass is not proof. Local replay is not official benchmark evidence. A recursion proof is not semantic proof. zk-Harness dry-run plans are not benchmark results. Manual handoff bundles are not benchmark results. Synthetic result candidates are not benchmark results. Evidence append proposals are not accepted evidence. Evidence-record candidates are not accepted evidence. Append previews do not mutate EvidenceLedger. Level2 eligibility is not Level2 evidence. External execution is disabled by default. Local oracle acceptance is semantic-local only. Unsound acceptance candidate is not a proven exploit.

## Soak Config Summary

`SoakRunConfig` supports:

- `Smoke`
- `Focused`
- `Regression`
- `NightlyLocal`
- `Custom`

Default limits are small. `NightlyLocal` requires explicit opt-in and larger explicit limits. Tests use only tiny smoke-like profiles. Long local soak jobs must run only with explicit user approval.

The default soak scope selects all implemented v0 families and uses shared generator tunables that are valid for each selected family. `BranchingFsm` needs at least four states so it can form `start`, two branch states, and `final`; default soak tunables therefore use `state_count = 4` and `trace_length = 3`.

Targetless local mutation combinations are applicability telemetry, not failure evidence. For example, `BadCounters` requires an accepted trace action with an integer counter update, so a `BranchingFsm` case that lacks that target increments `mutation_no_target_count` without adding a failure-corpus entry or failing the case.

## Deterministic Sharding Summary

Shard planning uses stable case ids derived from family kind and seed, sorted case order, and deterministic index partitioning. Shard ids use `shard-0000` style ids. Shard manifests include the source config digest, assigned case ids, expected case count, output policy, claim boundary, resume token, and relative artifact refs.

The planner uses no system randomness and no wall-clock shard ids.

## Resumability Summary

`SoakShardCheckpoint` records completed, failed, and skipped case ids, last completed case index, artifact refs written so far, telemetry counters, failure corpus refs, config digest, resume token, and claim boundary.

Resume validates config digest and resume token before skipping completed cases. The runner does not duplicate completed case execution on resume.

## Runner Pipeline Summary

`LocalSoakRunner` runs local Rust functions only:

1. Generate a Benchmark Instance.
2. Apply selected implemented mutation passes individually.
3. Build local replay manifests for the generated and mutated instances.
4. Replay through `LocalJsonAdapter`.
5. Optionally write sampled or failure packs within limits.
6. Collect internal benchmark OS telemetry.
7. Write checkpoints when an output directory is configured.
8. Extract failure corpus entries.
9. Build a local health report.

It does not shell out. It does not run zk-Harness. It does not clone external repositories. It does not import real external benchmark data.

## Telemetry Summary

Allowed Phase K telemetry includes internal counts and local engineering durations for:

- generation
- mutation
- local oracle evaluation
- local replay
- pack write/read
- proposal-preview counters
- failure counts by local phase
- bytes by local artifact role
- total local runner duration

Forbidden telemetry labels include `prover_time`, `verifier_time`, `proof_size`, `zk_harness_time`, and `constraint_count`. Internal timing telemetry must not populate Score Report performance fields.

## Health Report Summary

`SoakHealthReport` summarizes generated instances, mutation variants, local replays, failures, failure corpus entries, reproducibility notes, determinism notes, output artifact notes, regression signals, and recommendations.

Every health report carries warnings that local soak telemetry is not official benchmark evidence, internal timing is not ZK backend performance, and no external backend was invoked.

## Failure Corpus Summary

`FailureCorpusIndex` stores reproducibility aids only. Entries include family kind, seed, tunables, optional mutation class, optional trace id, local error summary, reproduction manifest, artifact refs, minimization hints, triage status, claim boundary, and notes.

Failure minimization metadata exists, but Phase K does not implement a reducer.

## Artifact Layout Summary

The local layout is:

```text
<soak-root>/
  soak_run_config.json
  shard_plan.json
  shards/
    shard-0000/
      shard_manifest.json
      checkpoint.json
      telemetry.json
      health_report.json
      failure_corpus_index.json
      sampled_packs/
      failure_packs/
      reports/
        local_summary.json
  aggregate/
```

Tests use tempdirs. Future long soak output should live outside the repository or under an ignored artifact directory unless explicitly requested.

## Validation Summary

Phase K tests cover config validation, deterministic shard planning, runner smoke execution, checkpoint resume, telemetry labels and JSON round-trips, health report validation, failure corpus extraction, and claim-boundary preservation.

The required Rust gates remain:

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
```

## Deliberately Unimplemented

Phase K does not implement:

- live zk-Harness execution
- external repository checkout
- real external result import
- accepted Level2+ evidence
- official benchmark evidence
- ZK backend performance claims
- formal evidence
- dashboards
- long-running NightlyLocal execution inside tests
- a full failure reducer

## Next Recommended Slice

Phase L should run long local soak execution and sampled local report generation. It should include user-approved long-running local jobs, shard output outside the repo or under an ignored artifact directory, sampled pack retention, failure-pack retention, aggregate telemetry reports, regression corpus curation, and local-only report publishing under strict claim boundaries.

Do not recommend live zk-Harness execution until local soak telemetry proves the benchmark OS can generate, mutate, replay, pack, validate, review, preview, and report at scale without breaking claim boundaries.
