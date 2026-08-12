# V23 corrected task-routed replay preflight record

State slice: `continual-learning-protocol-v23-task-routed-replay-consolidation-preflight`.

Source slice: `continual-learning-protocol-v23-task-routed-replay-consolidation`.

Classification: `CorrectedLocalTaskRoutedReplayPreflightNoBreakthroughClaim`.

## Run identity

This is the one authorized changed-design local preflight:

- cached Qwen2.5-0.5B-Instruct-4bit;
- seed `20260812` and order `0,1,2,3`, the previously failing V20 cell;
- four tasks, eight train facts and eight held-out facts per task;
- 32 dataset rows and 160 optimizer iterations per update;
- 128 examples and 640 optimizer iterations per arm;
- AdamW, learning rate `0.0001`, batch size `2`, maximum sequence length `192`;
- four task-keyed two-layer slots, matched against one eight-layer adapter;
- no shared-replay rerun, replication matrix, download, or H100.

External output:

`/tmp/continual-learning-model-v23-task-routed-replay-preflight-20260812-order0123`.

The stock `mlx_lm lora` launcher was not used for the stateful updates because
its `--resume-adapter-file` path restores adapter weights but constructs a new
optimizer. The preflight runner therefore owns the local MLX loop boundary and
serializes each slot's optimizer state. First activation uses a fresh zero
state; subsequent activation restores the same slot state before continuing.

## Result

| Arm | Acquisition | Retention after update 3 | Examples | Optimizer iterations | Adapter bytes | Peak memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `routed_replay` | 8/8 | 8/8 | 128 | 640 | 5,877,252 total | 0.654 GB |
| `routed_no_replay` | 8/8 | 8/8 | 128 | 640 | 5,877,252 total | 0.654 GB |

The full eight-layer zero-step reference was `5,877,295` bytes, giving a
compact-to-full ratio of `0.9999927` for both arms. Replay fact IDs were
present in the actual per-slot training datasets at every replay update. The
optimizer state receipts verified persistent slot state and exact per-update
iteration accounting.

## Decision

The corrected protocol plumbing passed: replay exposure was real, optimizer
state custody was real, budgets were matched, and the compact byte budget was
matched. The primary retention effect was exactly `0.00` (`8/8 - 8/8`). The
candidate therefore fails the retention-above-routed-no-replay gate and is not
eligible for replication, an H100, or any breakthrough/continual-learning
generalization claim.

The result is constructive: the previous zero-effect concern was not caused by
missing replay rows or weight-only optimizer reset. Both routes now preserve
the target task on this cell, so the remaining question is protocol
discrimination rather than runtime capacity. The next research object must be
a separately preregistered task/update protocol redesign with a measurable
primary contrast; do not buy compute for this tie.
