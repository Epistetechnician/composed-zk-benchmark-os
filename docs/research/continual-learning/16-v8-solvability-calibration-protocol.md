# V8 held-out compositional solvability calibration

Status: `ProspectiveLocalDevelopmentCompositionalCalibration`.

State slice: `continual-learning-model-adapter-v8-heldout-compositional-solvability-calibration`.

## Single changed variable

V7 failed held-out trainable acquisition: `0.250`, below no-update `0.375`.
V8 changes only the hidden task mapping family. The arbitrary seeded
permutation becomes a deterministic task-index shift:

`label = option[(residue + task_id) mod 4]`.

The held-out pair split, prompt format, fact-ID exclusion, model, seed, order,
optimizer, replay policy, update budget, and training steps remain unchanged.

## One-preflight contract

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Eight train and eight held-out pairs per task.
- Balanced replay: 24 capacity, 32 rows per update.
- AdamW, learning rate `0.0001`, batch size `2`, eight LoRA layers, 192-token
  maximum sequence length, 40 steps per update.
- Exactly one preflight; no V8 replication, second model, or H100.

Require held-out split validation, retrieval above no-update, trainable
held-out acquisition above no-update, and replay held-out retention above
naive. Failure stops the calibration slice.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/compositional_calibration_benchmark.py \
  --output /tmp/continual-learning-model-v8-qwen-seed20260810-order0123 \
  --iters 40
```
