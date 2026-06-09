# Phase G zk-Harness Dry-Run Adapter Notes

## Implemented

Phase G adds zk-Harness adapter preparation to `zkbench-core`.

Implemented concepts:

- `ZkHarnessAdapterManifest`,
- `ZkHarnessDryRunPlan`,
- `ZkHarnessDryRunPlanner`,
- `ZkHarnessPackMapping`,
- inert `ZkHarnessPlannedCommand`,
- `ZkHarnessExecutionPolicy`,
- `ZkHarnessMetricMapping`,
- `ZkHarnessEvidencePolicy`,
- `ZkHarnessClaimBoundaryPolicy`,
- dry-run validation,
- deterministic JSON serialization.

zk-Harness dry-run plans are not benchmark results. External execution is disabled by default.

## Why Dry-Run Only

The repository has not verified a live zk-Harness schema, source version, runner interface, metric format, artifact model, or result import path. Phase G therefore creates reviewable adapter-preparation artifacts only.

No Phase G code:

- clones zk-Harness,
- executes zk-Harness,
- shells out to external tools,
- imports benchmark data,
- records performance metrics,
- creates Level2+ evidence.

## Adapter Manifest Summary

The adapter manifest records:

- manifest id and version,
- adapter id,
- dry-run-only status,
- source policy,
- schema assumption,
- compatibility target,
- supported local family kinds,
- supported mutation classes,
- supported local artifact kinds,
- unsupported features,
- dry-run capability declaration,
- evidence policy,
- claim-boundary policy,
- review status.

The source policy forbids external repo checkout, external command execution, and external benchmark result import.

The schema assumption says internal candidate mapping only and future verification required.

## Dry-Run Replay Plan Summary

The dry-run plan records:

- source local benchmark pack id,
- source pack manifest digest,
- local pack subject ids,
- family mappings,
- mutation mappings,
- trace mappings,
- expected outcome mappings,
- planned steps,
- planned artifacts,
- unsupported features,
- warnings,
- execution policy,
- claim boundary,
- evidence policy.

Dry-run plan claim boundary is `Level0DesignNote`.

## Local Benchmark Pack Mapping Summary

The mapper preserves:

- source pack id,
- source file digests,
- generated instance ids,
- mutation ids,
- local replay manifest ids,
- local replay result ids as local-only references,
- expected verdicts.

Candidate labels:

- `BaselineFsm` -> `control_flow_baseline_fsm`,
- `BranchingFsm` -> `control_flow_branching_fsm`,
- `BoundedCounterLoop` -> `control_flow_bounded_counter_loop`,
- `MissingConstraints` -> `missing_constraints_negative_case`,
- `CorruptedGuards` -> `corrupted_guards_negative_case`,
- `BadCounters` -> `bad_counters_negative_case`.

These are candidate mapping labels only, not official zk-Harness labels.

## Planned Command Inertness Model

`ZkHarnessPlannedCommand` is serializable data. It describes future intent but contains no process handle and exposes no live execution API.

Validation rejects:

- non-inert commands,
- live execution policy,
- absolute path-like values,
- shell metacharacter payloads,
- fake metric values,
- elevated claim boundaries.

## Metric Mapping Limitations

Metric mappings are schema-only. Phase G includes future metric kinds but no values:

- prover time,
- verifier time,
- proof size,
- memory usage,
- constraint count,
- setup time,
- witness generation time.

No Score Report performance axis can be filled from a dry-run plan.

## Evidence Policy

Phase G evidence policy:

- dry-run plan generation is `Level0DesignNote`,
- local source pack evidence remains `Level1LocalReplay`,
- future live external replay may become Level2 only after reproducible artifacts exist,
- imported external results require provenance and validation,
- benchmark pass is not proof,
- local replay is not official benchmark evidence,
- external replay is not formal evidence.

## Claim-Boundary Status

Actual Phase G artifacts remain `Level0DesignNote`:

- adapter manifests,
- dry-run plans,
- pack mappings,
- validation reports,
- metric mappings,
- evidence policies.

Referenced local pack evidence remains `Level1LocalReplay`. Mapping does not elevate it.

## Validation Summary

Phase G tests cover:

- adapter manifest JSON round-trip,
- dry-run plan JSON round-trip,
- disabled execution policy,
- inert planned command data,
- local pack mapping,
- source digest preservation,
- candidate family and mutation labels,
- absent metric values,
- claim-boundary preservation,
- rejection of shell-like payloads and absolute paths,
- source scan for external process APIs.

## Deliberately Unimplemented

Still not implemented:

- live zk-Harness execution,
- zk-Harness source checkout,
- official zk-Harness schema compatibility,
- external benchmark result import,
- prover time ingestion,
- verifier time ingestion,
- proof size ingestion,
- memory usage ingestion,
- constraint count ingestion,
- Level2+ evidence production,
- formal evidence.

## Next Recommended Slice

Phase H now implements a reviewed external-runner boundary and manual handoff schema, not live benchmark claims. Live zk-Harness execution remains future.

Implement:

- explicit opt-in external execution feature flag,
- sandbox/manual runner abstraction,
- no default external execution,
- no automatic zk-Harness cloning,
- dry-run-to-manual-run handoff docs,
- artifact capture contract,
- provenance contract,
- result import validation schema.

Do not recommend official zk-Harness benchmark execution until the external-runner boundary, artifact capture model, and result import validation schema are implemented and reviewed.
