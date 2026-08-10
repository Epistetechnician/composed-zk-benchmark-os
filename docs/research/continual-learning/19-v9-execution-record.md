# V9 immutable task-keyed adapter-bank execution record

State slice: `continual-learning-model-adapter-v9-immutable-task-adapter-bank`.

Classification: `ImmutableTaskAdapterBankPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentImmutableTaskAdapterBankPilot`.

## Scope and execution

V9 tested whether non-destructive parameter isolation could preserve a task
better than the signed V8 sequential/replay baselines. Each task was trained
into a fresh LoRA adapter from the frozen cached Qwen2.5-0.5B-Instruct-4bit
base. The exact task-token router selected `T0` through `T3`; no adapter was
resumed or overwritten.

This was one local preflight only:

- seed `20260810`, order `0,1,2,3`;
- eight train and eight held-out examples per task, with two train and two
  held-out pairs per residue;
- task rule `mod4_sum_then_task_shift_v2`, mapping policy
  `task_id_shift_v1`;
- 32 rows per update, AdamW at `0.0001`, batch size `2`, 40 iterations, eight
  LoRA layers, and 192-token maximum sequence length;
- the V8 prompt, source-context removal, model, seed, order, and assessment
  budgets were preserved;
- no replication, second model, or H100 allocation was authorized.

The external artifact directory was
`/tmp/continual-learning-model-v9-qwen-seed20260810-order0123`.

## Results

| strategy | acquisition | retention after interference | recovery |
| --- | ---: | ---: | ---: |
| no update | 1/8 (0.125) | 1/8 (0.125) | 1/8 (0.125) |
| naive sequential LoRA | 2/8 (0.25) | 2/8 (0.25) | 1/8 (0.125) |
| balanced replay LoRA | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| immutable task adapter bank | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| retrieval control | 8/8 (1.0) | 8/8 (1.0) | 8/8 (1.0) |

The bank cleared acquisition over no-update, but retention tied naive
sequential LoRA. Its candidate gate therefore failed:

```text
retrieval_above_no_update: true
bank_acquisition_above_no_update: true
bank_retention_above_naive: false
candidate_eligible: false
```

The result does not support a breakthrough claim. It identifies the remaining
local bottleneck as task solvability/generalization under the held-out split,
not adapter overwrite alone: every bank route reached only 2/8 held-out
examples despite preserving the task-specific adapter.

## Audit and validation

The V9 audit recorded four bank updates. Each update had eight selected train
fact IDs, 32 dataset rows, an exact route key, and `resumed_from: null`; the
validator also confirmed the selected examples were present in the generated
datasets and that the held-out split and task mapping were unchanged.

Validator result:

```text
valid: true
candidate_eligible: false
manifest_sha256: 1ab63ea261b8e9e6d12899e6867d88797519ec3e6cd373e633d3fd0c23d2400d
contract_sha256: 7ce887b7e3ad1884779c3a9195e4e17619cf3c7fe9ec4405b0e143ecf79b9a23
```

Focused regression result:

```text
17 passed
```

Audit hashes:

```text
naive_sequential_lora: 1f687bca5eabc194c9a5ff6cb2584ddd346e9eeab1025eac8cc703892a66fb0d
replay_lora:           9ed317ec53735f885da480964e2582d8ee0a87c79021f2840a147bdc12aa31b2
task_adapter_bank:     d9fc9ce7937dc622db1dd0b5cfbc5e5c58e8b396be9810b7625cbc3c8da3aafc
```

## Decision

Stop V9. Do not replicate the tied adapter-bank design and do not provision
an H100. The next research object must alter the task/update protocol so that
the model can demonstrate task-rule acquisition on held-out examples while
keeping the same budget and audit controls. Hardware becomes relevant only
after that corrected local protocol passes the replay-retention gate and the
remaining constraint is measured runtime or memory.
