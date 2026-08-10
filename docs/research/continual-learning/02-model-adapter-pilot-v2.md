# Model adapter pilot v2

Status: `LocalDevelopmentModelContinualLearningPilot`

State slice: `continual-learning-model-adapter-v2`.

## Scope

This slice replaces the deterministic learner with one cached local MLX model,
while preserving the v1 task, source-removal, and evaluation boundaries. It
uses four disjoint fact families and fixed four-choice conditional likelihoods.

The pilot compares `no_update`, `context_only`, `retrieval`,
`naive_sequential_lora`, and `replay_lora`. Both trainable strategies receive
the same number of update examples per task. Replay selection is deterministic
and capacity-bounded.

## Locked controls

- `no_update`: frozen base model without reference context.
- `context_only`: frozen base model with the full current fact context.
- `retrieval`: frozen base model with only the queried fact as reference.
- `naive_sequential_lora`: sequential adapter updates on the current task.
- `replay_lora`: sequential adapter updates with a fixed current-plus-replay
  example budget.

All model execution is offline. No downloads, providers, or external data are
permitted. Assessment answers are generated only after adapter training and
are not used to build training data.

## Pilot command

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/model_benchmark.py \
  --output /tmp/continual-learning-model-v2-seed20260810-order0123
```

Validate the external bundle:

```text
PYTHONDONTWRITEBYTECODE=1 python \
experiments/continual_learning/validate_model_benchmark.py \
  /tmp/continual-learning-model-v2-seed20260810-order0123
```

## Advancement rule

This pilot cannot produce a breakthrough claim. A candidate requires three
update seeds, three interference orders, a second cached model, paraphrase and
withheld-composition evaluation, paired uncertainty intervals, and independent
artifact validation. A larger claim also requires a comparison against the
best relevant published baseline under matched compute and memory budgets.
