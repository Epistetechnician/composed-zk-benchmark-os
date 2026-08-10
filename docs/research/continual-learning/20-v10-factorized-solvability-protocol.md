# V10 factorized solvability-control protocol

Status: `ProspectiveLocalDevelopmentFactorizedSolvabilityControlPilot`.

State slice: `continual-learning-protocol-v10-factorized-solvability-control`.

## Hypothesis

V7 through V9 used a held-out compositional task, but the model reached only
2/8 held-out examples after updating. That confounds task-memory retention with
failure to execute the modular arithmetic rule. V10 factorizes the protocol:
the deterministic residue is supplied, while the task-specific residue-to-label
codebook remains to be learned and retained.

This is a solvability control for continual-learning memory. It is not a claim
of reasoning, transfer, general intelligence, or breakthrough performance.

## Single changed design

The only experimental change from V9 is the prompt contract. Training and
assessment prompts include the derived modular-four residue and preserve the
raw pair as a distractor. The label is not included. Task token `T0` through
`T3` still selects the task-specific codebook, and held-out pairs remain
disjoint from training pairs.

## Fixed contract

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Eight train and eight held-out pairs per task, two per residue in each split.
- 32 rows per update, 24 replay capacity, AdamW `0.0001`, batch size `2`,
  eight LoRA layers, 192-token maximum sequence length, and 40 iterations.
- Naive sequential LoRA, balanced replay LoRA, immutable task adapter bank,
  no-update, context-only, and retrieval controls remain in the panel.
- Training rows, optimizer, steps, seed, order, and generated audit fields are
  fixed. Only the prompt solvability control changes.
- Exactly one changed-design preflight. No replication, second model, or H100.

## Gates

The primary metric is replay retention minus naive retention after interference.
The solvability guard is naive acquisition at least `6/8`; if it fails, the
protocol remains unsolved and the memory comparison is not advanced. Candidate
eligibility requires the solvability guard and replay retention strictly above
naive retention. The adapter-bank result is recorded as a secondary mechanism.

The validator must confirm exact prompt bytes, fact-ID membership, per-task
replay counts, target-task accuracy after every update, fresh bank adapters,
no resume source, fixed budgets, and manifest/audit hashes.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/factorized_solvability_benchmark.py \
  --output /tmp/continual-learning-model-v10-qwen-seed20260810-order0123-corrected \
  --iters 40
```
