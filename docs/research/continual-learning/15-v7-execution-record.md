# V7 held-out compositional execution record

State slice: `continual-learning-model-adapter-v7-heldout-compositional-task`.

Status: `LocalDevelopmentHeldoutCompositionalPilotStoppedAcquisitionGate`.

## Validated boundary

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seed/order: `20260810`, `0,1,2,3`.
- Four tasks with eight train pairs and eight disjoint held-out pairs each.
- Two train and two held-out pairs per modular residue.
- Balanced full replay: 24 capacity, 32 rows per update.
- Contract SHA-256: `a4e475c51f585c9f2bbf3aede81be028020017729825d71306128087e9e17b17`.
- Manifest SHA-256: `9d8ee293509914af03562294127b19e0fcd62ff666559fa2e7617e0cbb66a0c7`.

The independent validator confirmed the split, modular rule, prompt parity,
absence of fact IDs from prompts, exact dataset membership, balanced replay,
and immutable contract. Replay counts were `{0: 8}`, `{0: 8, 1: 8}`, and
`{0: 8, 1: 8, 2: 8}` at updates 1, 2, and 3.

## Results

| Strategy | Held-out acquisition | Held-out retention | Held-out recovery |
|---|---:|---:|---:|
| no-update | 0.375 | 0.375 | 0.375 |
| context-only | 0.250 | 0.375 | 0.375 |
| retrieval oracle | 1.000 | 1.000 | 1.000 |
| naive sequential LoRA | 0.250 | 0.125 | 0.250 |
| replay LoRA | 0.250 | 0.250 | 0.250 |

Gates:

- held-out split and contract validation: passed;
- retrieval above no-update: passed;
- trainable held-out acquisition above no-update: failed (`0.250 < 0.375`);
- replay held-out retention above naive: passed (`0.250 > 0.125`).

## Decision

Stop V7 before replication. The compositional task is structurally valid, but
the trainable path is not yet solvable above the no-update baseline. This is a
task/model calibration failure, not evidence for an H100. Do not provision
hardware or make a continual-learning claim.

The next bounded step is a pre-registered solvability calibration that changes
one task difficulty variable while preserving held-out disjointness. No V7
replication is authorized.

External artifact:

- `/tmp/continual-learning-model-v7-qwen-seed20260810-order0123`
