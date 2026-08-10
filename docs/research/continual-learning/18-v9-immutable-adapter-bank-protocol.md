# V9 immutable task-keyed adapter-bank protocol

Status: `ProspectiveLocalDevelopmentMemoryMechanismPilot`.

State slice: `continual-learning-model-adapter-v9-immutable-task-adapter-bank`.

## Mechanism

V9 preserves the V8 held-out compositional task and changes only the memory
mechanism. Each task is trained into a fresh LoRA adapter from the frozen base;
previous adapters are never resumed or overwritten. A deterministic exact
router maps the task token to its adapter at assessment.

This is a modular-memory control, not evidence of general intelligence. Its
purpose is to test whether non-destructive parameter isolation can preserve
held-out knowledge when sequential replay is insufficient.

## Fixed contract

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Eight train and eight held-out pairs per task.
- V8 task rule and prompt contract unchanged.
- 32 rows per update, 24 replay capacity for shared baselines.
- AdamW, learning rate `0.0001`, batch size `2`, eight LoRA layers, 192-token
  maximum sequence length, 40 steps per update.
- Exactly one preflight; no replication, second model, or H100.

Require route integrity, held-out split validation, bank acquisition above
no-update, and bank retention above naive sequential retention. Failure stops
the mechanism slice.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/immutable_adapter_bank_benchmark.py \
  --output /tmp/continual-learning-model-v9-qwen-seed20260810-order0123 \
  --iters 40
```
