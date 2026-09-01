# Plasticity Guard Replication V1 Execution Record

State slice: `continual-learning-plasticity-guard-replication-v1`.

## Status

Execution completed on 2026-08-28. Qualification, prediction locking,
assessment, PrimaryED/DAed mirror validation, and independent aggregate-only
validation passed. The final bounded classification is
`RollbackInfrastructureOnly`.

## Frozen inputs

- model: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`;
- source: `/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/gemma3-manual-inputs-v1/newsroom/release/test.jsonl.gz`;
- PrimaryED output: `/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-plasticity-guard-replication-v1-20260828-r1`;
- DAed mirror: `/Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-plasticity-guard-replication-v1-20260828-r1`;
- prior candidate result digest: `46d0654b199205b2957e5a1fb758c1989c377db7d6ab86eaa0f6440de3bd8316`;
- prior candidate receipt digest: `ed707b95864627dbefb00b277dda41bc23ec6ecaa51f36677ff503c0be6798b6`;
- new seeds: `1747`, `1749`;
- new orders: `interleave`, `outer_in`;
- arms: `no_update`, `fixed_cadence`, `plasticity_guard`.

## Result

The new cohort was records 23 through 34, disjoint from the frozen prior
cohort records 11 through 22. All 12 cases completed with equal training
budgets. The no-update arm returned exactly zero adaptation improvement in all
four paired cases. The fixed arm returned negative held-out improvement in all
four cases. The guarded arm also returned negative absolute improvement in all
four cases:

- primary absolute guarded improvement versus untouched base: `-0.041830065`
  NLL/token;
- primary deterministic 10,000-resample bootstrap interval:
  `[-0.052287582, -0.031372549]`;
- guarded wins over no-update: `0/4`;
- secondary guarded-minus-fixed improvement: `0.117647059` NLL/token;
- secondary deterministic bootstrap interval: `[0.086274509, 0.151633988]`;
- guarded wins over fixed cadence: `4/4`;
- hard guards: passed;
- base weights: unchanged;
- classification: `RollbackInfrastructureOnly`;
- decision rule: `guard_beats_fixed_but_not_no_update`.

The guard committed one update and rolled back five in every case. The result
supports interference reduction relative to fixed cadence, but not useful
continual learning relative to leaving the base untouched. Per the frozen
decision rule, the learning mechanism is not promoted; the guard is retained
only as rollback/safety infrastructure.

## Validation note

The model run first encountered a validator implementation error that compared
an adapter directory with its tensor-file receipt. No data-dependent change or
training rerun occurred. The validator was corrected, the exact finalized
artifact was revalidated on both roots, and the recorded pre-fix validator
digest was reconstructed exactly from the artifact's source-digest receipt.
The corrected validation report is stored as `validator-receipt.json` in both
external roots. The initial false-negative attempt is not scientific evidence.

Receipt linkage:

```text
config_sha256: 30c9f1ade805091b8b59db1f638ce2131e156ab11f32cb056db45f41d60e5ab5
qualification_sha256: b19803015c740688af556d8d264c7b796b545be83f2f46e139dc8e040fa88a8e
prediction_lock_sha256: d7e25e636dec13b2b492ed1a08062dbaa9e6bbef36c5061233e73f1712054a46
results_sha256: 94ee07aa1cb4336f9fb6b977078f24230abc4265a70ef754673c5534f4cc96eb
receipt_sha256: 7c2080e664a8f3c0d528e5f4cd19853d62e423a3d207f7b088638d1c5899d8cc
model_manifest_sha256: 69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256
corpus_manifest_sha256: 8c1e6d1ee4d735f879c63509a3cdc83d702cdd843ba9722704a759be4448814e
```

Astral integration and ZK/PQC backends remain `not_run`.

## Execution boundary

The base checkpoint must remain byte-identical. The no-update arm may create
disposable shadow adapters to equalize training compute but may never apply
one. The fixed and guarded arms may use only reversible adapters; rejected
candidates remain uncommitted. Astral integration and ZK/PQC backends remain
`not_run`.

Every mutation in this execution record touches state slice
`continual-learning-plasticity-guard-replication-v1`.
