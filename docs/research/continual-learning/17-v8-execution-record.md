# V8 held-out compositional solvability calibration record

State slice: `continual-learning-model-adapter-v8-heldout-compositional-solvability-calibration`.

Status: `LocalDevelopmentHeldoutCompositionalCalibrationStoppedReplayGate`.

## Changed variable

V8 changed only the hidden task mapping from a seeded arbitrary permutation to
the deterministic task-index shift rule. Held-out pair disjointness, prompt
format, replay policy, model, seed, order, optimizer, update budget, and steps
were unchanged from V7.

- Contract SHA-256: `b63ec214c7dab1c6acb8f2e1f6f976ea1b1b87705a197954f3d9cfb97f640711`.
- Manifest SHA-256: `739f7de219069e7a1cad198f966d8d23ab716f52203d979634c340f4124ea5e6`.

The independent validator confirmed the task rule, held-out split, prompt
parity, dataset membership, balanced replay, and fixed contract.

## Results

| Strategy | Held-out acquisition | Held-out retention | Held-out recovery |
|---|---:|---:|---:|
| no-update | 0.125 | 0.125 | 0.125 |
| context-only | 0.250 | 0.125 | 0.125 |
| retrieval oracle | 1.000 | 1.000 | 1.000 |
| naive sequential LoRA | 0.250 | 0.250 | 0.125 |
| replay LoRA | 0.250 | 0.250 | 0.250 |

Gates:

- held-out structure and contract validation: passed;
- retrieval above no-update: passed;
- trainable acquisition above no-update: passed (`0.250 > 0.125`);
- replay held-out retention above naive: failed (`0.250 = 0.250`).

## Decision

Stop V8. The task is more solvable than V7, but replay does not improve
retention under this calibration. Do not replicate V8, provision an H100, or
claim a continual-learning breakthrough. The next research step requires a
newly preregistered memory/update mechanism or task formulation; further
single-variable mapping adjustments are not justified by this evidence.

External artifact:

- `/tmp/continual-learning-model-v8-qwen-seed20260810-order0123`
