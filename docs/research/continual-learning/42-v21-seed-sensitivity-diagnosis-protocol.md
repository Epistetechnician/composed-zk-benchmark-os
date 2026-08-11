# V21 seed-sensitivity diagnosis protocol

State slice: `continual-learning-protocol-v21-seed-sensitivity-diagnosis`.

Source slice: `continual-learning-protocol-v20-compact-routing-replication`.

## Scope

V20 showed a compact task-routed residual candidate succeeding for seeds
`20260811` and `20260813` but failing for seed `20260812` across all three task
orders. V21 diagnoses that failure using only the sealed V20 outputs. It runs no
training and changes no model state.

## Probes

- Recompute config, manifest, result, log, and adapter hashes.
- Verify route audit shape, slot count, no-resume policy, and dataset row count.
- Compare task mapping, split, residue, and label-shape signatures across seeds.
- Parse compact-slot final train/validation losses, throughput, and peak memory.
- Compare failure by seed versus failure by task order.

## Falsifiable hypotheses

1. Seed-specific optimizer or initialization instability: the failing seed fails
   across all orders and its task-0 slot validation loss plateaus.
2. Seed-specific task-manifest pathology: the failing seed has a distinct task
   shape signature.
3. Route/order implementation bug: failure follows order rather than seed.
4. Compact-slot capacity mismatch: all seeds fail similarly.
5. Artifact or audit inconsistency: hashes, routes, or files disagree.

## Stop rule

This diagnosis does not authorize a new training run or H100. A successor
protocol requires one predeclared stability change only after the diagnosis
identifies a supported local hypothesis; data, total steps, optimizer budget,
and adapter-byte budget must remain fixed.

## Command

```bash
PYTHONDONTWRITEBYTECODE=1 python experiments/continual_learning/seed_sensitivity_diagnosis.py \
  --source /tmp/continual-learning-model-v20-compact-routing-replication \
  --output /tmp/continual-learning-model-v21-seed-sensitivity-diagnosis/report.json
```
