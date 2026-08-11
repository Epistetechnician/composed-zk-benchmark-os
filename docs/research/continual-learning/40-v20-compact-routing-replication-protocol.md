# V20 compact-routing replication protocol

State slice: `continual-learning-protocol-v20-compact-routing-replication`.

Source slice: `continual-learning-protocol-v19-task-routed-compact-residual`.

## Question

Does the V19 compact task-routed retention result replicate across fresh seeds
and task orders under the same prompt, optimizer, step, example, and adapter
byte-budget controls?

## Frozen matrix

- Model: cached Qwen2.5-0.5B-Instruct-4bit.
- Fresh seeds: `20260811`, `20260812`, `20260813`.
- Orders: `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Target task: task `0`, always first in the order.
- Eight train and eight held-out facts per task.
- Thirty-two examples per update and 160 optimizer iterations.
- AdamW, learning rate `0.0001`, batch size `2`, eight shared layers.
- Compact candidate: four task-keyed two-layer LoRA slots, no resume.
- Actual candidate adapter bytes must remain within `0.75..1.25` of one
  eight-layer shared adapter.

Each of the nine cells runs naive sequential LoRA, balanced replay LoRA, the
immutable full adapter-bank control, and compact task-routed residual slots.
No tuning is permitted between cells.

## Replication gates

```text
candidate_solvability_all_cells: every compact acquisition >= 0.75
candidate_retention_above_naive_all_cells: compact retention > naive in every cell
parameter_budget_matched_all_cells: every compact byte ratio in 0.75..1.25
```

The replay comparison is reported separately. A positive compact-routing
replication does not establish that replay works. H100 provisioning remains
unauthorized until replay retention passes and runtime or memory is shown to be
the bottleneck.

## One-run command

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python experiments/continual_learning/compact_routing_replication_matrix_preflight.py \
  --model /Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --output /tmp/continual-learning-model-v20-compact-routing-replication \
  --iters 160
```
