# V24 shared-adapter task-keyed optimizer-state protocol

State slice: `continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state`.

Source slice: `continual-learning-protocol-v23-task-routed-replay-consolidation-preflight`.

## Decision basis

V23 corrected the custody path: replay fact IDs were present in the actual
training datasets and task-slot optimizer state persisted. It still produced a
retention tie because both arms routed facts into isolated task slots. In that
architecture, no-replay already preserves the target slot by construction;
replay cannot improve the primary retention metric.

V24 restores a shared parameter interference surface and changes one protocol
variable: optimizer state is task-keyed and persistent while the adapter
parameters remain shared.

## Changed protocol variable

`shared_adapter_task_keyed_optimizer_state_v1`:

- one shared eight-layer LoRA adapter is used by every task;
- every row is routed by its task token to a task-keyed AdamW state;
- first activation of a task creates fresh zero optimizer state with seed
  `22000000 + task_id`;
- later updates restore and continue that task's optimizer state;
- all task-keyed optimizers update the same shared adapter parameters;
- no task receives a private parameter slot.

The candidate is `shared_replay`; the control is `shared_no_replay`. Replay
selection, examples, order, model, optimizer family, learning rate, batch
size, sequence length, adapter bytes, and total optimizer iterations remain
fixed. Only the update interface changes from one shared optimizer state to
task-keyed optimizer state over the same shared adapter.

## Frozen contract

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seeds `20260811`, `20260812`, `20260813`.
- Orders `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Four tasks with eight train and eight held-out facts each.
- Thirty-two rows and 160 optimizer iterations per update.
- 128 examples and 640 optimizer iterations per cell and arm.
- AdamW, learning rate `0.0001`, batch size `2`, maximum sequence length `192`.
- One shared eight-layer adapter; no private task adapter bank.
- No downloads, adaptive tuning, favorable-cell selection, second model, or
  H100.

## Pure-data result

The nine-cell schedule is independently deterministic. For the first update,
`shared_replay` and `shared_no_replay` both use task 0 and 160 steps. On later
replay updates, each active task receives its own routed rows and a
proportional optimizer-step allocation. With 32 rows and four active tasks,
that allocation is exactly 40 steps per task, summing to the fixed 160-step
budget.

The protocol checks exact fact selection, no unseen replay, route keys,
task-keyed state identifiers, fixed task seeds, shared-adapter identity,
per-update budgets, total budgets, deterministic hashes, and authority
boundaries. It does not run a model and does not establish replay retention.

## Next gate

Only one corrected local preflight may follow the validated pure-data plan.
The primary metric is:

`shared_replay_retention - shared_no_replay_retention`.

If replay exposure is present and this contrast remains tied, stop this design
and redesign the task/update protocol again. Do not spend replication budget or
provision an H100 on a zero-effect or ceiling-tied design.
