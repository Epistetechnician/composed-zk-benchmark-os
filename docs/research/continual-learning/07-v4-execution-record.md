# Signed task/update path v4 execution record

State slice: `continual-learning-model-adapter-v4-signed-replay-path`.

Status: `LocalDevelopmentModelContinualLearningPilotStoppedReplayGate`.

## Validated boundary

- Model: cached Qwen2.5-0.5B-Instruct-4bit.
- Runtime: local MLX `mlx_lm` 0.31.3 with offline flags.
- Seed/order: `20260810`, task order `0,1,2,3`.
- Four tasks, eight balanced facts per task.
- Update budget: sixteen examples, split into eight current-task and eight
  replay examples.
- Replay capacity: sixteen facts using `stratified_hash_replay_v1`.
- Contract SHA-256: `db78068b2fb1cd6144f4868e49e7b5cd3797c16974b1ce05cac2aff2d8d2aab4`.
- Manifest SHA-256: `4c5fe7b6a513026dc79af3917f90e099aa38014e83f49c1139c95ba977784df1`.
- The independent validator confirmed contract integrity, prompt parity, and
  the fixed state slice.

## Results

| Strategy | Acquisition | Retention after interference | Recovery | Paraphrase retention |
|---|---:|---:|---:|---:|
| no-update | 0.250 | 0.250 | 0.250 | n/a |
| context-only | 0.375 | 0.250 | 0.250 | n/a |
| retrieval upper control | 1.000 | 1.000 | 1.000 | n/a |
| naive sequential LoRA | 0.500 | 0.250 | 0.250 | 0.250 |
| replay LoRA | 0.500 | 0.250 | 0.250 | 0.375 |

Retrieval is now a strong task-solvability control because it performs exact
lookup of the stored label. It is not evidence of neural learning. The
trainable acquisition path exceeds no-update, but replay retention is equal to
naive retention.

## Gates and decision

- Contract and prompt parity: passed.
- Retrieval above no-update: passed (`1.000 > 0.250`).
- Trainable acquisition above no-update: passed (`0.500 > 0.250`).
- Replay retention above naive: failed (`0.250 = 0.250`).

Stop before multi-seed/order replication and before second-model replication.
No replication budget was spent on the current zero-effect replay design. The
claim ceiling remains `LocalDevelopmentModelContinualLearningPilot`, and
breakthrough eligibility is false.

External artifact:

- `/tmp/continual-learning-model-v4-qwen-seed20260810-order0123`
