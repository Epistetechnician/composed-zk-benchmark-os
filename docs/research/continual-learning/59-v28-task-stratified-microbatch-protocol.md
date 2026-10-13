# V28 task-stratified microbatch protocol

State slice: `continual-learning-protocol-v28-task-stratified-microbatch`.

Source slice: `continual-learning-protocol-v27-shared-global-update-stream-replication-preflight`.

## Decision basis

V27 replicated acquisition in all eight fresh cells, but replay tied
no-replay in both fresh `20260812` order cells. Inspection of the
MLX trainer showed that it creates length-sorted batches and then shuffles
those batches without task-balanced microbatch construction. V28 changes the
update interface at that boundary.

## One changed protocol variable

`task_stratified_microbatch_schedule_v1` constructs deterministic
round-robin task buckets before forming batch-size-two microbatches. The
global NumPy/MLX seed stream, one shared adapter, one persistent AdamW state,
selected fact IDs, replay policy, dataset rows, optimizer steps, and task
order remain fixed. This is a task/update interaction change, not a replay
selection, capacity, or model change.

## Frozen preflight

- Seed: `20260812`.
- Order: `0,2,3,1`, the first fresh V27 tie cell.
- Cached Qwen2.5-0.5B-Instruct-4bit.
- 32 actual rows and 160 optimizer iterations per update.
- 128 actual examples and 640 optimizer iterations per arm.
- One shared eight-layer adapter, AdamW `0.0001`, batch size `2`,
  maximum sequence length `192`.
- No adaptive tuning, matrix expansion, second model, or H100.

The pure-data plan preserves the exact V26 selected fact IDs and schedules.
Its plan hash is:

`fe2eaea5f8bec4397e84148a37639321657804a5c9b5dab7826a790e9f90c237`.

## Gate

The local preflight must pass replay exposure, optimizer custody, exact
budgets, matched adapter bytes, acquisition at least `6/8`, and
strict replay retention above no-replay. A pass is a targeted robustness
signal, not a replication claim or breakthrough claim.
