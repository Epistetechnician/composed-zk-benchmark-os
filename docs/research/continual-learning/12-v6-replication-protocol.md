# V6 same-model replication protocol

Status: `ProspectiveLocalDevelopmentReplication`.

State slice: `continual-learning-model-adapter-v6-replication-campaign`.

## Scope

Replicate the accepted single-seed V6 pilot on the same cached Qwen2.5-
0.5B-Instruct-4bit model. The V6 training contract is unchanged. Only seed and
task order vary.

Campaign factors:

- Seeds: `20260810`, `20260811`, `20260812`.
- Orders: `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Total runs: nine.
- Update budget: `32`; replay capacity: `24`; forty steps per update.
- No second model, H100, or adaptive parameter tuning.

## Primary metric and gate

For every run, compute the paired retention delta:

`replay_retention - naive_retention`.

The replication gate passes only if all nine deltas are strictly positive and
all bundles independently validate. A failed or invalid run stops advancement.
The result remains local pilot evidence even if the gate passes.

Run command:

```text
PYTHONDONTWRITEBYTECODE=1 \
python experiments/continual_learning/replicate_model_benchmark.py \
  --output /tmp/continual-learning-v6-replication-qwen-20260810 \
  --iters 40
```

After the nine-run gate, a second-model replication is a separate decision.
H100 allocation remains unauthorized unless the unchanged campaign is
demonstrably compute- or memory-bound.
