# V14 repaired-objective retention protocol

Status: `ProspectiveLocalDevelopmentRepairedObjectiveRetentionPilot`.

State slice: `continual-learning-protocol-v14-repaired-objective-retention`.

## Purpose

V13 established that the V11 residue-only task codebook can fit when the only
changed optimization variable is the update iteration count: `160` rather than
`40`. V14 carries that repaired objective into one retention preflight. The
task/update protocol, solvability control, data budget, optimizer, seed, order,
and replay exposure remain fixed.

This is a local retention pilot. It cannot support a general continual-learning
claim, a breakthrough claim, or an H100 allocation by itself.

## Fixed contract

- Cached Qwen2.5-0.5B-Instruct-4bit; seed `20260810`; order `0,1,2,3`.
- Four tasks with eight train and eight held-out facts per task; residue-only
  prompts with the raw pair absent.
- 32 rows/update, eight current facts, 24 balanced full-memory replay rows.
- AdamW `0.0001`, batch size `2`, eight LoRA layers, 192-token maximum sequence
  length, and `160` update iterations.
- Recovery remains the inherited fixed 20-step reacquisition operation.
- Naive sequential LoRA, balanced replay LoRA, immutable task adapter bank,
  no-update, context-only, and retrieval controls.
- Every update records selected fact IDs, replay counts by task, and target-task
  accuracy after the update. Validator checks confirm replay rows are present in
  the written training datasets.

The only changed design relative to V11 is the V13-cleared iteration repair.
The runner rejects drift in model, seed, order, task count, or update steps.

## Gates

Require all of the following for candidate eligibility:

- naive acquisition reaches at least `6/8`;
- retrieval acquisition exceeds no-update acquisition;
- replay retention after interference is strictly above naive retention; and
- the immutable adapter-bank retention comparison is recorded, whether or not
  it exceeds naive.

If replay exposure is present but replay retention remains tied with naive,
stop and redesign the task/update protocol. Do not replicate, add a second
model, or provision an H100 on a tied or otherwise failed candidate.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/repaired_objective_retention_preflight.py \
  --output /tmp/continual-learning-model-v14-qwen-seed20260810-order0123 \
  --iters 160
```
