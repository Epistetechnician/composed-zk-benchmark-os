# V27 shared-global-update-stream replication protocol

State slice: `continual-learning-protocol-v27-shared-global-update-stream-replication`.

Source slice: `continual-learning-protocol-v26-shared-global-update-stream-preflight`.

## Purpose

V26 produced a positive local preflight for one seed/order cell:
shared-replay retention `4/8` versus shared-no-replay retention `0/8`.
V27 tests whether that effect survives the preregistered three-seed,
three-order matrix without rerunning the V26 development anchor.

The V26 anchor at seed `20260812`, order `0,1,2,3` is retained as a
validated development result and excluded from fresh replication execution.
The eight remaining seed/order cells are run exactly once.

## Frozen contract

- Same cached Qwen2.5-0.5B-Instruct-4bit model and V26 global update stream.
- Seeds `20260811`, `20260812`, `20260813`.
- Orders `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Four tasks with eight training and eight held-out facts each.
- Thirty-two actual rows and 160 optimizer iterations per update.
- 128 actual examples and 640 optimizer iterations per arm and cell.
- One shared eight-layer adapter, one persistent AdamW state, no per-task
  RNG reseeding, and balanced full-memory replay.
- No adaptive tuning, favorable-cell selection, second model, or H100.

## Replication gates

The strict replication gate requires all eight fresh cells to pass acquisition
at least `6/8`, replay exposure, optimizer-state custody, exact budgets,
matched adapter bytes, and replay retention strictly above no-replay. A
partial effect pattern is reported but does not support a robust replication
claim. H100 remains closed unless a scientifically advancing result also
demonstrates runtime or memory as the remaining bottleneck.

Pure-data plan artifact:

`/tmp/continual-learning-model-v27-shared-global-update-stream-replication-plan.json`

Plan SHA-256:

`e58ffdc94ab9cc585c23728296b0f6b6d007b9c32485983334132f1b76698e6e`.
