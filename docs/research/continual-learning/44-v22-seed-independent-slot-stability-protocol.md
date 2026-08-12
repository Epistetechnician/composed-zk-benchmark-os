# V22 seed-independent slot stability replication protocol

State slice: `continual-learning-protocol-v22-seed-independent-init-replication`.

Source slice: `continual-learning-protocol-v21-seed-sensitivity-diagnosis`.

## Question

Does making compact-slot initialization and fresh optimizer state task-keyed
and independent of the experiment seed remove the V20 seed-specific failure,
while preserving the same task/update protocol and replay comparison?

## One changed design variable

The compact candidate changes from `experiment_seed + task_id` to the fixed
task-keyed slot seed `22000000 + task_id`. Each slot starts a fresh zero AdamW
optimizer state and never resumes another slot. This makes initialization and
optimizer-state selection independent of the cell's experiment seed and task
order. The effective slot seed, policies, adapter bytes, and adapter hashes are
recorded per update.

No control strategy changes. The inherited naive sequential LoRA, balanced
replay LoRA, and immutable adapter-bank controls retain their V20 seeds and
training machinery.

## Frozen controls

- Cached model: Qwen2.5-0.5B-Instruct-4bit.
- Seeds: `20260811`, `20260812`, `20260813`.
- Orders: `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Target task: task `0`, always first.
- Eight train and eight held-out facts per task.
- Thirty-two examples per update and 160 optimizer iterations.
- AdamW, learning rate `0.0001`, batch size `2`, maximum sequence length `192`.
- Four two-layer compact slots, matched against one eight-layer shared adapter.
- Total compact candidate budget: 128 examples and 640 optimizer iterations.
- No downloads, no network access, no adaptive tuning, and no favorable-seed
  selection.

## Independent audit

The validator checks every cell's immutable digests, fixed controls, slot seed
policy, no-resume/fresh-optimizer policy, adapter-byte parity, and per-task
adapter identity. It also reconstructs route-bound training rows from the
task facts and checks every recorded replay fact ID against the actual
`replay_lora/step-*/train.jsonl` dataset and per-task replay counts.

## Gates

```text
candidate_solvability_all_cells: every compact acquisition >= 0.75
candidate_retention_above_naive_all_cells: compact retention > naive in every cell
parameter_budget_matched_all_cells: every compact byte ratio in 0.75..1.25
replay_exposure_valid_all_cells: every recorded replay fact is in its dataset
replay_retention_above_naive_all_cells: replay retention > naive in every cell
slot_seed_policy_valid_all_cells: true
slot_adapter_identity_consistent_all_cells: true
```

Replay retention is an independent advancement gate. H100 authorization is
false unless replay retention passes and a separate runtime or memory audit
demonstrates that hardware is the remaining bottleneck. A positive V22 result
is still a local development replication, not a breakthrough, SOTA, production,
or general continual-learning claim.

## One-run command

```bash
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python experiments/continual_learning/seed_independent_slot_replication_matrix_preflight.py \
  --model /Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --output /tmp/continual-learning-model-v22-seed-independent-slot-replication \
  --iters 160
```
