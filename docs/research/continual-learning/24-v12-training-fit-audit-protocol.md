# V12 training-fit audit protocol

Status: `ProspectiveLocalDevelopmentTrainingFitAudit`.

State slice: `continual-learning-protocol-v12-training-fit-audit`.

## Purpose

V11 failed codebook acquisition and a read-only check found that the adapters
also failed to fit their own training facts. V12 audits the training boundary
before any further memory comparison. It consumes the accepted V11 artifact,
performs inference and receipt inspection only, and does not train or alter the
source artifact.

## Checks

- exact training prompt/completion parity across the 12 V11 update datasets;
- single-token supervision for labels `A`, `B`, `C`, and `D`;
- per-adapter task-0 and current-task training accuracy;
- final train/validation loss receipts and final-weight presence;
- peak-memory receipts without treating memory as a performance claim.

The fit floor requires both final naive task-0 train accuracy and task-0 bank
train accuracy to reach `6/8`. A failed fit floor stops all new replay or
memory preflights. No replication, second model, or H100 is authorized.

```text
PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python experiments/continual_learning/training_fit_audit.py \
  --source /tmp/continual-learning-model-v11-qwen-seed20260810-order0123 \
  --output /tmp/continual-learning-model-v12-training-fit-audit
```
