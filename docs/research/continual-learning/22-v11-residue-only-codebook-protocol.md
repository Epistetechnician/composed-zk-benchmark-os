# V11 residue-only task-codebook protocol

Status: `ProspectiveLocalDevelopmentResidueOnlyCodebookPilot`.

State slice: `continual-learning-protocol-v11-residue-only-codebook`.

## Hypothesis

V10 supplied the derived residue but retained the raw pair as a distractor. It
reached only `3/8` naive held-out acquisition, below the `6/8` solvability
guard. V11 removes the raw pair entirely and measures the smallest remaining
problem: learning and retaining each task's residue-to-option codebook.

This is a codebook-memory control. It no longer tests novel pair composition,
arithmetic, reasoning, transfer, general intelligence, or breakthrough
performance.

## Single changed design

Compared with V10, the prompt contains only the task token, the deterministic
derived residue, and the instruction to apply the task codebook. The raw pair
is absent from both training and assessment prompts. The held-out fact split,
task mappings, adapters, update mechanics, and all budgets remain unchanged.

## Fixed contract and gates

- Cached Qwen2.5-0.5B-Instruct-4bit; seed/order `20260810`, `0,1,2,3`.
- Eight train and eight held-out facts per task, with two per residue in each
  split; 32 rows/update and 24 replay capacity.
- AdamW `0.0001`, batch size `2`, eight LoRA layers, 192-token maximum sequence
  length, and 40 iterations.
- Naive sequential LoRA, balanced replay LoRA, immutable task adapter bank,
  no-update, context-only, and retrieval controls.
- Primary metric: replay retention minus naive retention.
- Solvability guard: naive acquisition at least `6/8`.
- Candidate eligibility: solvability guard and replay retention strictly above
  naive retention.
- Exactly one preflight; no replication, second model, or H100.

The validator must confirm residue-only prompt bytes, held-out membership,
replay counts, target-task accuracy after every update, fresh bank adapters,
fixed budgets, and manifest/audit hashes.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/residue_only_codebook_benchmark.py \
  --output /tmp/continual-learning-model-v11-qwen-seed20260810-order0123 \
  --iters 40
```
