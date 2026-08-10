# V7 held-out compositional task protocol

Status: `ProspectiveLocalDevelopmentCompositionalPilot`.

State slice: `continual-learning-model-adapter-v7-heldout-compositional-task`.

## Reason for redesign

V6 replication produced only `4/9` positive replay-retention deltas, with
median delta `0.0000`. The exact-fact task is therefore not sufficient for a
robust claim. V7 changes the task, not the hardware.

## Task

Each task defines a hidden permutation from modular residues `0..3` to options
`A..D`. A fact asks for the option produced by composing two symbols under
modular-four addition. Each task has sixteen pairs, split deterministically into
eight training pairs and eight held-out assessment pairs, with two train and two
test pairs per residue. Held-out pairs never appear in training datasets, and
their fact IDs are absent from prompts.

The retrieval strategy is an oracle compositional solvability control. It is
not neural evidence. Direct trainable assessment uses held-out pairs with source
context removed.

## Fixed preflight

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Eight train and eight held-out facts per task.
- Balanced full replay: 24 replay capacity, 32 rows per update.
- AdamW, learning rate `0.0001`, batch size `2`, eight LoRA layers, 192-token
  maximum sequence length, 40 steps per update.
- Exactly one local preflight; no replication or H100.

Run command:

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/compositional_model_benchmark.py \
  --output /tmp/continual-learning-model-v7-qwen-seed20260810-order0123 \
  --iters 40
```

Advancement requires disjoint held-out validation, retrieval above no-update,
trainable held-out acquisition above no-update, and replay held-out retention
above naive retention. Failure stops the slice.
