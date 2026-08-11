# V17 task-keyed readout feasibility protocol

Status: `ProspectiveLocalDevelopmentTaskKeyedReadoutFeasibility`.

State slice: `continual-learning-protocol-v17-task-keyed-readout-feasibility`.

## Purpose

V16 isolated explicit task routing as the successful retention control. V17
tests whether a lightweight task-keyed readout can recover task separation from
the final shared replay representation without training a second full adapter
bank.

The preflight fits one of the 24 possible four-label permutations per task,
using only that task's eight training facts and the final shared replay
adapter's raw candidate logits. It then evaluates the locked permutation on
the eight held-out facts. This is a feasibility diagnostic, not a new
continual-learning result.

## Fixed boundary

- Source: accepted V14 final shared replay adapter, `replay_lora/step-3`.
- Same Qwen model, seed `20260810`, task order, 32-row update budget, AdamW,
  and 160-step training objective as V14.
- Four task-keyed readout slots; each is a 4-by-4 permutation table.
- Readout fitting uses train facts only; held-out predictions are locked after
  each permutation is selected.
- No model retraining, second model, replication, production claim, or H100.

## Gates

Require four exact route slots, all four readouts fitting at least `6/8` train
facts, and target-task held-out accuracy strictly above both raw shared replay
and naive retention. A pass only authorizes implementation of a trainable
shared-backbone/readout architecture; it does not establish a breakthrough.

```text
PYTHONDONTWRITEBYTECODE=1 python experiments/continual_learning/task_keyed_readout_preflight.py \
  --source /tmp/continual-learning-model-v14-qwen-seed20260810-order0123 \
  --output /tmp/continual-learning-model-v17-task-keyed-readout
```
