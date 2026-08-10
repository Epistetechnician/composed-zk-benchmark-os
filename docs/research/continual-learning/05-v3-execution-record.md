# Model adapter prompt-parity pilot v3 execution record

State slice: `continual-learning-model-adapter-v3-prompt-parity`.

Status: `LocalDevelopmentModelContinualLearningPilotStoppedReplayGate`.

## Validated boundary

- Model: cached Qwen2.5-0.5B-Instruct-4bit.
- Runtime: local MLX `mlx_lm` 0.31.3 with offline flags.
- Manifest: `a255eaad6702b74c5fc404ecac49615556e8502739ceb69fa3b254f119dfb4af`.
- Four tasks, eight balanced facts per task, order `0,1,2,3`.
- Sixteen examples per update for both LoRA strategies.
- Training and direct assessment prompts were byte-identical through the
  `\nAnswer:` suffix; the independent validator checked the external datasets.
- Source context was removed for acquisition, retention, and recovery.

## Results

| Strategy | Acquisition | Retention after interference | Recovery | Interpretation |
|---|---:|---:|---:|---|
| no-update | 0.250 | 0.250 | 0.250 | four-choice baseline |
| context-only | 0.375 | 0.250 | 0.250 | weak context control |
| retrieval | 0.375 | 0.375 | 0.375 | task-solvability control, weak |
| naive sequential LoRA | 0.500 | 0.250 | 0.250 | acquisition gate passed |
| replay LoRA | 0.500 | 0.250 | 0.250 | no retention advantage |

Independent candidate gates:

- retrieval above no-update: passed;
- trainable acquisition above no-update: passed;
- replay retention above naive: failed.

## Decision

Stop before three-seed/three-order expansion. V3 demonstrates a corrected
trainability path for one Qwen seed/order, but it does not demonstrate
continual-learning improvement. The claim ceiling remains
`LocalDevelopmentModelContinualLearningPilot`; breakthrough eligibility is
false.

The next useful change is task/update redesign, not more seeds: make the
retrieval control reliably strong, add a true held-out composition split, and
require replay to beat naive retention before spending replication budget.

External artifact:

- `/tmp/continual-learning-model-v3-qwen-seed20260810-order0123`
