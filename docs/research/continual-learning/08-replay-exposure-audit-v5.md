# Replay-exposure audit v5

Status: `LocalDevelopmentModelContinualLearningPilot`.

State slice: `continual-learning-model-adapter-v5-replay-exposure-audit`.

## Baseline and scope

V4 is frozen as the baseline in
`docs/research/continual-learning/07-v4-execution-record.md`. V5 changes only
the audit surface. It does not change the model, task seed/order, prompt
contract, optimizer, learning rate, batch size, LoRA layer count, sequence
length, update budget, replay capacity, replay policy, or training steps.

The audit records, for each sequential update and each trainable strategy:

- selected fact IDs;
- current-task fact IDs;
- replay fact IDs and per-task replay counts;
- the actual training JSONL row count;
- target-task accuracy after the checkpoint, with source context removed.

The independent validator reconstructs fact IDs from the actual training JSONL
prompts and checks that every recorded replay fact is present in the dataset.
The audit manifests are included in the bundle digest.

## Fixed preflight contract

- Cached model: Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Four tasks, eight facts per task.
- Sixteen examples per update: eight current and eight replay.
- Replay capacity: sixteen.
- Optimizer: AdamW, learning rate `0.0001`.
- Batch size: `2`; LoRA layers: `8`; maximum sequence length: `192`.
- Training steps per update: `40`.

Run exactly one cached preflight:

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/model_benchmark.py \
  --output /tmp/continual-learning-model-v5-qwen-seed20260810-order0123 \
  --iters 40
```

## Decision rule

First independently validate the audit and the fixed contract. If replay facts
are absent from the actual datasets, repair the implementation and rerun only
the corrected one-seed preflight. If replay exposure is present and replay
retention remains tied with naive retention, stop and redesign the task/update
protocol. Do not spend replication budget and do not provision an H100 for
this state.
