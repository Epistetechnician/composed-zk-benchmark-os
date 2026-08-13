# V29 replay-anchored temporal microbatch protocol

State slice: `continual-learning-protocol-v29-replay-anchored-temporal-microbatch`.

Source slice: `continual-learning-protocol-v28-task-stratified-microbatch-confirmation-preflight`.

## Decision basis

V28 confirmed replay exposure and optimizer custody but tied no-replay on the
second frozen `20260812`, order `0,3,1,2` cell. V28 changed batch composition,
but the trainer still randomly permuted the resulting batches. The next
protocol therefore changes the temporal task/update order, not replay fact
selection or model capacity.

## One changed protocol variable

`replay_anchored_temporal_microbatch_schedule_v1` removes random batch
permutation and emits deterministic oldest-replay-task batches first, followed
by the current-task batch in each temporal cycle. Remaining current batches are
emitted after replay anchors are exhausted. The no-replay control emits only
current-task batches under the same fixed batch size.

## Frozen contract

- Same cached Qwen2.5-0.5B-Instruct-4bit model.
- Same seed `20260812`, order `0,3,1,2`, selected fact IDs, prompts, and
  balanced replay policy as V26/V28.
- Same 32 rows and 160 optimizer iterations per update.
- Same 128 examples and 640 optimizer iterations per arm.
- Same one shared eight-layer adapter, persistent AdamW state, learning rate,
  batch size, and sequence length.
- No adaptive tuning, matrix expansion, second model, or H100.

The V28 confirmation effect is frozen at `0.00`; this is not a favorable-cell
selection. A preflight is authorized only after independent temporal schedule
validation.
