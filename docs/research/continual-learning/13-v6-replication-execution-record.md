# V6 same-model replication execution record

State slice: `continual-learning-model-adapter-v6-replication-campaign`.

Status: `LocalDevelopmentReplicationGateFailed`.

## Campaign boundary

- Same cached Qwen2.5-0.5B-Instruct-4bit model.
- Unchanged V6 update, optimizer, prompt, and evaluation contract.
- Seeds: `20260810`, `20260811`, `20260812`.
- Orders: `0123`, `0231`, `0312`.
- Nine total runs.
- Every bundle independently validated before inclusion.
- Primary metric: replay retention minus naive retention.
- Preregistered gate: all nine paired deltas strictly positive.

## Results

| Seed | Order | Naive retention | Replay retention | Delta |
|---:|:---:|---:|---:|---:|
| 20260810 | 0123 | 0.250 | 0.625 | +0.375 |
| 20260810 | 0231 | 0.250 | 0.250 | +0.000 |
| 20260810 | 0312 | 0.250 | 0.250 | +0.000 |
| 20260811 | 0123 | 0.250 | 0.500 | +0.250 |
| 20260811 | 0231 | 0.250 | 0.375 | +0.125 |
| 20260811 | 0312 | 0.250 | 0.250 | +0.000 |
| 20260812 | 0123 | 0.125 | 0.250 | +0.125 |
| 20260812 | 0231 | 0.250 | 0.250 | +0.000 |
| 20260812 | 0312 | 0.250 | 0.125 | -0.125 |

Summary:

- Positive deltas: `4/9`.
- Ties: `4/9`.
- Negative deltas: `1/9`.
- Mean delta: `+0.0833`.
- Median delta: `0.0000`.
- Replication gate: failed.

## Decision

The V6 replay effect is not robust to seed/order variation under the current
task. Stop the replication campaign. Do not add more seeds opportunistically,
run a second model, provision an H100, or claim a general continual-learning
improvement.

The next research object is a task redesign with a pre-registered held-out
compositional/generalization target. The current exact-fact retention task is
not sufficient for a breakthrough claim, even though one V6 pilot run passed
its local gate.

External artifact:

- `/tmp/continual-learning-v6-replication-qwen-20260810`
