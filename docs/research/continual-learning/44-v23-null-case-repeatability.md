# V23 exact null-case repeatability record

State slice: `continual-learning-independent-replication-v23`

Status: `LocalDevelopmentIndependentExecutionCampaign`

Claim ceiling: `LocalDevelopmentIndependentExecutionCampaign`

## Purpose

This record closes the bounded repeatability check for the V23 case that did
not show a replay-retention advantage. It compares the original campaign
artifact with one fresh execution using the unchanged executor, validator,
model, task order, seed, and runtime parameters.

This is local model/runtime evidence only. It is not accepted benchmark
evidence, a scientific replication of a general continual-learning claim, a
production validation, or evidence that replay is ineffective outside this
frozen case.

## Frozen execution

- Model: `/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit`
- Seed: `20260820`
- Task order: `0,2,3,1`
- Task count: `4`
- Facts per task: `8`
- Replay capacity: `24`
- Update budget: `32`
- Iterations: `40`
- Learning rate: `0.0001`
- Optimizer: `adamw`
- Replay policy: `balanced_full_memory_v1`
- Executor SHA-256: `a4fb2dedb5eba61093922ddce17f31298103d64c953e45be6b517cc1f04a44c9`
- Validator SHA-256: `fc3dd9d1ba514951dd66d131032e2414e71c3ba191b19b3fcdfcdd0db636da93`
- Model manifest SHA-256: `73bc39b2007ff304fb27e4efd1143a77222ca53605721a38835c1a01358bb0e1`
- Contract SHA-256: `b9d22a56b75936d7e6b4e7691a316a2aaa86eb3a7dae327c91219eaa03b69845`

The original artifact is outside the repository at
`/tmp/continual-learning-independent-v23-20260819-r1/seed-20260820-order-0231`.
The fresh artifact is outside the repository at
`/tmp/continual-learning-v23-null-repeat-20260819-r1`.

## Repeatability result

The independently invoked validator returned `valid: true` for the fresh
artifact. The two artifact roots have byte-identical `config.json`,
`tasks.json`, and `result.json` files:

| Artifact | SHA-256 |
| --- | --- |
| `config.json` | `7409f0efb0011903b434be29fd918770952872efb05c0ad9db3064cbafc96dd2` |
| `tasks.json` | `5280dcdec92d54afb6a7bc9ec9b372aa301ea88ba12b3e200453c08aef89c17f` |
| `result.json` | `e007112331c0b7cdd3ebbbaacbac1bf0bded9ffd8a5a7316403a8fb490af66ad` |

The two trainable-strategy audit digests also match:

- `naive_sequential_lora`: `d4d3b8caf56ad159581b74c151e4bf2d78426d706294039dd736ec5af3788a9d`
- `replay_lora`: `bfff2ab898820da0268123834e913a0e61a1dae9467805c9c73b35661375faf3`

Retention after interference is identical in both runs:

| Strategy | Correct | Total | Retention |
| --- | ---: | ---: | ---: |
| `no_update` | 2 | 8 | `0.25` |
| `naive_sequential_lora` | 2 | 8 | `0.25` |
| `replay_lora` | 2 | 8 | `0.25` |
| `retrieval` | 8 | 8 | `1.0` |

The validator gates are therefore unchanged:

- `replay_retention_above_naive`: `false`
- `retrieval_above_no_update`: `true`
- `trainable_acquisition_above_no_update`: `false`
- `candidate_eligible`: `false`
- `breakthrough_claim_eligible`: `false`

## Interpretation and stop condition

The exact null case is locally repeatable under the frozen configuration.
The result supports only the narrow statement that this execution path
reproduced the same output and did not pass the replay-versus-naive candidate
gate twice. It does not support changing the replay algorithm, tuning against
this assessment, or generalizing to other seeds, orders, models, or providers.

The V23 slice is complete for this repeatability check. Further scientific
work requires a separately frozen fresh seed/order or a separately authorized
training-dynamics diagnostic. Provider validation remains a distinct V24
boundary and requires operator-supplied provider inputs; it is not implied by
this local result.
