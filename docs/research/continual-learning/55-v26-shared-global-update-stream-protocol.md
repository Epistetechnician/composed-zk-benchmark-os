# V26 shared-global-update-stream protocol

State slice: `continual-learning-protocol-v26-shared-global-update-stream`.

Source slice: `continual-learning-protocol-v25-shared-adapter-reference-initialization-preflight`.

## Decision basis

V25 repaired shared-adapter initialization but still failed acquisition at
`2/8`. A read-only trainer differential on the exact V25 step-0 dataset
reached `8/8` when the shared model used one globally seeded update stream.
The V24/V25 runner instead reset NumPy state per task group and trained each
update through separate task-group calls. V26 therefore changes the
task/update interface, not the model, data, optimizer, or compute budget.

## One changed protocol variable

`shared_global_update_stream_v1`:

- seed NumPy before model loading and MLX immediately before LoRA construction;
- use one shared eight-layer adapter;
- use one persistent AdamW optimizer state across all four updates;
- write all current and replay facts for an update into one dataset;
- do not reseed per task or split an update into task-group trainer calls;
- preserve balanced full-memory replay fact selection and route metadata for
  audit only.

This is a shared update stream, not a task-routed adapter bank. Every update
still trains the same shared parameters, so interference remains measurable.

## Frozen controls

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Preflight seed `20260812`, order `0,1,2,3`.
- Four tasks with eight training and eight held-out facts each.
- Thirty-two actual dataset rows and 160 optimizer iterations per update.
- 128 actual examples and 640 optimizer iterations per arm.
- AdamW, learning rate `0.0001`, batch size `2`, maximum sequence length `192`.
- One shared eight-layer adapter with exact byte reference.
- Replay and no-replay arms use identical budgets and task order.
- No adaptive tuning, favorable-cell selection, second model, replication
  matrix, or H100 is authorized by this preflight.

## Pure-data gates

The nine-cell schedule is deterministic and independently validated. It binds
the same V24 seed/order matrix, fixed example and optimizer budgets, one
shared optimizer-state policy, one shared dataset per update, and the
no-per-task-reseed rule. The pure-data plan does not train a model.

Plan artifact:

`/tmp/continual-learning-model-v26-shared-global-update-stream-plan.json`

Plan SHA-256:

`96bf3406f9190d64478a20bfdcbe96344e3666b6533d729918951918043e5973`.

## Advancement gate

One corrected local preflight is required. Candidate advancement requires
acquisition at least `6/8`, replay fact presence in actual datasets, optimizer
state persistence, exact budgets, matched adapter bytes, and replay retention
strictly above no-replay. A passing preflight authorizes only a separately
preregistered bounded replication decision. It does not authorize an H100 or
a breakthrough claim; accelerator provisioning requires a demonstrated
runtime or memory bottleneck after the scientific gate passes.
