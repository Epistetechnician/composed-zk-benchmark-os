# Model adapter prompt-parity pilot v3

Status: `LocalDevelopmentModelContinualLearningPilot`

State slice: `continual-learning-model-adapter-v3-prompt-parity`.

## Correction

V2 trained the answer after an `Answer:` suffix but assessed the preceding
prompt. V3 makes the canonical assessment prompt include that suffix and uses
the exact same string as the masked training prefix. The independent validator
now checks the suffix in every sequential training dataset and rejects bundles
without the parity contract.

The V2 artifacts remain preserved as diagnostics and are not pooled with V3.

## Advancement gates

The first V3 Qwen run must satisfy all of these before any replication:

- prompt parity contract is present and independently validated;
- no-update is near the four-choice baseline;
- retrieval is above no-update, proving the task is solvable;
- at least one trainable strategy exceeds no-update acquisition; and
- replay retention exceeds naive sequential retention on the same cases.

If acquisition or replay fails, stop and redesign the task/update path. Do not
expand to three seeds, three orders, or a second model.

## Pilot command

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/model_benchmark.py \
  --output /tmp/continual-learning-model-v3-qwen-seed20260810-order0123
```

The claim ceiling remains local model-pilot evidence. It does not authorize a
breakthrough, SOTA, production, or general continual-learning claim.
