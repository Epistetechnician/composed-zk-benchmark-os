# V21 seed-sensitivity diagnosis execution record

State slice: `continual-learning-protocol-v21-seed-sensitivity-diagnosis`.

Source slice: `continual-learning-protocol-v20-compact-routing-replication`.

Classification: `SeedSensitivityDiagnosisNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentSeedSensitivityDiagnosis`.

## Execution

V21 performed a read-only audit of the sealed V20 three-seed by three-order
matrix. It ran no training, changed no model state, and did not select or
discard cells based on their outcomes. The audit recomputed configuration,
manifest, result, log, and adapter hashes; checked route audits, slot depth,
no-resume status, and dataset row counts; compared task-shape signatures; and
parsed per-slot training telemetry.

Artifact directory:

`/tmp/continual-learning-model-v21-seed-sensitivity-diagnosis/report.json`

Source artifact directory:

`/tmp/continual-learning-model-v20-compact-routing-replication`

## Seed-level diagnosis

| seed | compact acquisition pass cells | task-0 final validation loss | interpretation |
| ---: | ---: | ---: | --- |
| 20260811 | 3/3 | 0.000 in all cells | compact slot converged |
| 20260812 | 0/3 | 0.309 in all cells | compact slot optimization plateau |
| 20260813 | 3/3 | 0.000 in all cells | compact slot converged |

The failing seed is order-invariant: seed `20260812` has acquisition `0.25` in
all three orders. The task-shape signature is identical across all nine cells,
and every configuration, manifest, result, route audit, training log, and
adapter hash validated. The candidate slot peak-memory range is
`0.644..0.654` GB, so a runtime or memory bottleneck is not demonstrated.

## Hypothesis classification

```text
seed_specific_optimizer_or_initialization_instability: supported
seed_specific_task_manifest_pathology: not_supported
route_or_order_implementation_bug: not_supported
compact_slot_capacity_mismatch: not_supported_as_sole_cause
artifact_or_audit_inconsistency: not_supported
diagnosis_confidence: supported_local_hypothesis_not_causal_proof
```

This is a local seed-sensitivity diagnosis, not causal proof and not a
replicated continual-learning breakthrough. V20 remains ineligible for a
robust replication claim; replay remains non-robust; and no H100 is authorized.

## Gates

```text
source_matrix_exact: true
all_cell_hashes_valid: true
all_route_audits_valid: true
failure_reproduced_across_all_failing_seed_orders: true
task_shape_invariant: true
h100_authorized: false
breakthrough_claim_eligible: false
```

## Decision

Accept the diagnosis as the next local research object. The next protocol may
make exactly one predeclared change: make slot initialization and optimizer
state independent of the experiment seed while preserving the same data,
example count, total steps, optimizer budget, task order matrix, and
adapter-byte budget. Do not rerun V20 unchanged, choose only successful seeds,
or provision an H100 before a corrected local protocol demonstrates replay
retention and runtime or memory is the remaining bottleneck.

Report hash:

`fe4747a5fe89c36807a37f899025cdb6f999f45a7650a56c685e3dc882666a66`
