# Replay-exposure audit v5 execution record

State slice: `continual-learning-model-adapter-v5-replay-exposure-audit`.

Status: `LocalDevelopmentModelContinualLearningPilotStoppedReplayGate`.

## Frozen contract

V4 was preserved as the baseline. V5 changed only the audit surface. The
model, seed/order, task shape, prompt contract, AdamW optimizer, learning rate,
batch size, LoRA layer count, sequence length, update budget, replay capacity,
replay policy, and forty training steps per update were unchanged.

- Contract SHA-256: `1de9f6345dc302dd120fbf620749c127c9121faf8bcccc2c7bed76d8db630d0a`.
- Manifest SHA-256: `6c0dfbc8745725360e68de5d171ea0a81544332cd76c4d97c60029e1b6995d7f`.
- Replay audit SHA-256: `b71e22b3695877bfe315b33026f7534ff3e0edd9a3c2b0ea8d2feb06f6cef12f`.
- Naive audit SHA-256: `3ae52c462bd141a91f63ef115039525a6ddca63cdef21b18b1231106c8a8f903`.

The independent validator reconstructed fact IDs from every training JSONL
file and confirmed that recorded replay facts were present in the datasets.
Every update contained sixteen rows.

## Replay exposure

| Update | Current task | Replay counts by task | Target accuracy after checkpoint |
|---:|---:|---|---:|
| 0 | 0 | `{}` | 0.500 |
| 1 | 1 | `{"0": 8}` | 0.250 |
| 2 | 2 | `{"0": 4, "1": 4}` | 0.250 |
| 3 | 3 | `{"0": 3, "1": 3, "2": 2}` | 0.250 |

Replay was therefore applied and auditable. The target task was exposed to
replay at every later update, but its measured accuracy did not recover.

## Endpoint results

| Strategy | Acquisition | Retention after interference | Recovery | Paraphrase retention |
|---|---:|---:|---:|---:|
| no-update | 0.250 | 0.250 | 0.250 | n/a |
| context-only | 0.375 | 0.250 | 0.250 | n/a |
| retrieval upper control | 1.000 | 1.000 | 1.000 | n/a |
| naive sequential LoRA | 0.500 | 0.250 | 0.250 | 0.250 |
| replay LoRA | 0.500 | 0.250 | 0.250 | 0.375 |

The replay-retention gate failed again: `0.250 = 0.250`. Replay exposure is
present, so this is not an absent-data or replay-plumbing failure. It is an
ineffective task/update design under the fixed training contract.

## Decision

Stop. Do not run replication, a second model, or an H100. Redesign the
task/update protocol before spending compute. The claim ceiling remains
`LocalDevelopmentModelContinualLearningPilot`; breakthrough eligibility is
false.

External artifact:

- `/tmp/continual-learning-model-v5-qwen-seed20260810-order0123`
