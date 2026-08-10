# Signed task/update path v4

Status: `LocalDevelopmentModelContinualLearningPilot`

State slice: `continual-learning-model-adapter-v4-signed-replay-path`.

## Contract lock

“Signed” means content-addressed and mechanically locked. The runner records a
SHA-256 contract digest over the model path, task seed/order, task shape,
prompt contract, update budget, replay capacity, and replay policy. The
independent validator recomputes that digest. This is provenance, not external
authorization or a cryptographic human signature.

## Task/update path

- Eight balanced four-choice facts per task.
- Eight current-task examples plus eight replay examples per update.
- Replay capacity: sixteen facts.
- Replay policy: `stratified_hash_replay_v1`, with deterministic per-task
  quotas and round-robin selection into the update budget.
- Retrieval is an exact non-parametric lookup returning the stored label. It is
  intentionally a strong solvability upper control, not a neural result.
- Training and direct assessment use the same canonical prompt through the
  `Answer:` suffix.
- Source context remains removed at acquisition, retention, and recovery.

## One-preflight rule

Run one cached Qwen preflight. Expand to replication only if all gates pass:

1. contract digest and prompt parity validate;
2. retrieval is above no-update;
3. a trainable strategy is above no-update on acquisition; and
4. replay retention is above naive sequential retention.

Failure of any gate stops the run. No replication budget is spent on a
zero-effect replay path.

Pilot command:

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/model_benchmark.py \
  --output /tmp/continual-learning-model-v4-qwen-seed20260810-order0123
```
