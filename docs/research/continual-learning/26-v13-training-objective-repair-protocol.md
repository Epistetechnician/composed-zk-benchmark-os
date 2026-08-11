# V13 training-objective repair protocol

Status: `ProspectiveLocalDevelopmentTrainingObjectiveRepairPilot`.

State slice: `continual-learning-protocol-v13-training-objective-repair`.

## Purpose

V12 established that V11's prompt/completion data and single-token label
supervision were valid, but the adapters failed to fit their own eight training
facts. V13 changes one optimization variable: training iterations increase
from `40` to `160`. The model, seed, examples, prompt, optimizer, learning
rate, batch size, LoRA depth, and sequence length remain fixed.

This is a fit-only preflight. It performs no retention comparison and cannot
support a continual-learning or breakthrough claim.

## Controls and gates

Two fresh frozen-base controls are trained on the same task-0 residue-only
dataset: a naive fit adapter and a task-0 adapter-bank fit. Each uses 32 rows
formed from the eight task-0 training facts, with no resume source.

Require:

- exact prompt/completion parity over 64 rows;
- labels A–D remain single-token targets;
- final weights and 160-step receipts for both controls;
- both controls reach at least `6/8` training accuracy.

If the fit floor fails, stop. Do not run a retention panel, replication, second
model, or H100 allocation.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/fit_repair_preflight.py \
  --output /tmp/continual-learning-model-v13-fit-repair \
  --iters 160
```
