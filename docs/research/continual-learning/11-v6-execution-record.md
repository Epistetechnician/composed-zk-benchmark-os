# Balanced full-memory replay v6 execution record

State slice: `continual-learning-model-adapter-v6-balanced-full-memory-replay`.

Status: `LocalDevelopmentModelContinualLearningPilotCandidateEligibleForReplication`.

## Fixed contract

- Model: cached Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Four tasks, eight facts per task.
- Eight current facts plus all prior-task facts per replay update.
- Update budget: `32`; replay capacity: `24`.
- Replay policy: `balanced_full_memory_v1`.
- AdamW, learning rate `0.0001`, batch size `2`, eight LoRA layers,
  maximum sequence length `192`, forty steps per update.
- Contract SHA-256: `b67cf5ce9aae5ec1dc74445d6b2656b56bd0b143dc3de825cae1bcee8db27568`.
- Manifest SHA-256: `b2feb223ac0fcfdb847c63faf83d793c8de4d069684324f25ce2b2e9f49c0ef4`.

The independent validator confirmed prompt parity, fixed-contract integrity,
dataset membership, and balanced replay exposure. The replay datasets had
counts `{0: 8}`, `{0: 8, 1: 8}`, and `{0: 8, 1: 8, 2: 8}` at updates 1, 2,
and 3 respectively; every update contained 32 rows.

## Results

| Strategy | Acquisition | Retention after interference | Recovery | Paraphrase retention |
|---|---:|---:|---:|---:|
| no-update | 0.250 | 0.250 | 0.250 | n/a |
| context-only | 0.375 | 0.250 | 0.250 | n/a |
| retrieval upper control | 1.000 | 1.000 | 1.000 | n/a |
| naive sequential LoRA | 0.625 | 0.250 | 0.250 | 0.375 |
| replay LoRA | 0.625 | 0.625 | 0.375 | 0.500 |

Candidate gates:

- contract, prompt parity, and replay exposure: passed;
- retrieval above no-update: passed;
- trainable acquisition above no-update: passed;
- replay retention above naive: passed (`0.625 > 0.250`).

## Decision

The v6 protocol is eligible for a preregistered replication campaign across
multiple seeds and task orders, followed by a separately authorized second
model. This is local single-seed pilot evidence only. It does not establish a
breakthrough, general continual-learning improvement, SOTA, production
readiness, or hardware necessity. No H100 was provisioned.

External artifact:

- `/tmp/continual-learning-model-v6-qwen-seed20260810-order0123`
