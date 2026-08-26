# V23 independent execution campaign protocol

State slice: `continual-learning-independent-replication-v23`  
Claim ceiling: `LocalDevelopmentIndependentExecutionCampaign`

V23 runs two fixed, disjoint seed/order cases in separate subprocesses. Each
case invokes the existing model-training benchmark as an external executor and
the independent benchmark validator as a separate process. Run roots are
immutable and repository-external. Prediction and validation contracts remain
fixed before assessment effects; network access remains disabled.

Run:

```text
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONDONTWRITEBYTECODE=1 python experiments/continual_learning/independent_replication.py \
  --output /tmp/continual-learning-independent-v23
```

The campaign gate is positive replay-retention delta for both fixed cases.
Failure stops advancement. Passing this local campaign is independent
execution evidence only; it is not production readiness, a scientific claim,
SOTA, breakthrough evidence, or official benchmark evidence.
