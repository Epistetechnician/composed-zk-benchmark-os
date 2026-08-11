# V15 interleaved replay task/update protocol

Status: `ProspectiveLocalDevelopmentInterleavedReplayRetentionPilot`.

State slice: `continual-learning-protocol-v15-interleaved-replay-retention`.

## Purpose

V14 passed solvability and replay-exposure audits, but balanced replay tied
naive retention at `2/8` while the task-routed adapter bank retained `8/8`.
V15 therefore changes the task/update protocol, not the replay budget: replay
rows are scheduled in a deterministic task-stratified round-robin order within
each update dataset.

This creates a preregistered causal target for replay scheduling while holding
the selected examples, total rows, optimizer, seed, order, model, and update
steps fixed. It remains a local protocol pilot and cannot support a general
continual-learning or breakthrough claim.

## Fixed and changed variables

Fixed from V14:

- cached Qwen2.5-0.5B-Instruct-4bit; seed `20260810`; order `0,1,2,3`;
- eight train and eight held-out facts per task, residue-only prompts;
- 32 rows/update, 24 replay capacity, AdamW `0.0001`, batch size `2`;
- eight LoRA layers, sequence length `192`, `160` update iterations;
- 20-step recovery operation and the same no-update, context-only, retrieval,
  naive, replay, and adapter-bank controls.

Changed only:

- replay dataset row schedule: `task_stratified_round_robin_v1`.

The selected fact IDs and per-task replay counts remain identical to V14. The
validator checks both membership and route schedule. The adapter-bank control
is retained as a route-preservation ceiling, not as evidence of replay gain.

## Gates

Require naive acquisition at least `6/8`, retrieval above no-update, and replay
retention strictly above naive. If interleaving still ties naive, stop and
redesign the task/update interface again; do not run replication or provision
an H100. A passing result would justify a bounded replication of the corrected
protocol, not a breakthrough claim.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/interleaved_replay_retention_preflight.py \
  --output /tmp/continual-learning-model-v15-qwen-seed20260810-order0123 \
  --iters 160
```
