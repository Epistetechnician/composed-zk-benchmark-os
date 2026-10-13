# V28 task-stratified microbatch preflight record

State slice: `continual-learning-protocol-v28-task-stratified-microbatch-preflight`.

Source slice: `continual-learning-protocol-v28-task-stratified-microbatch`.

Classification: `CorrectedLocalTaskStratifiedMicrobatchPreflightNoBreakthroughClaim`.

## Execution

One local preflight ran on seed `20260812`, order `0,2,3,1`,
the first V27 fresh tie cell. The preflight used the V28 task-stratified
round-robin microbatch schedule while preserving V26 selected fact IDs,
global initialization, one shared optimizer state, one shared adapter,
replay policy, and all compute budgets.

The immutable output was:

`/tmp/continual-learning-model-v28-task-stratified-microbatch-preflight-20260812-order0231`.

## Result

| arm | acquisition | retention after update 3 | replay exposure | optimizer state | adapter bytes | peak memory |
| --- | ---: | ---: | --- | --- | ---: | ---: |
| `shared_replay` | 8/8 | 4/8 | verified | verified | 5,877,295 | 0.763871514 GB |
| `shared_no_replay` | 8/8 | 2/8 | verified | verified | 5,877,295 | 0.763537532 GB |

Retention effect: `+0.25`.

Target-task accuracy after each update:

- `shared_replay`: 8/8, 6/8, 4/8, 4/8;
- `shared_no_replay`: 8/8, 4/8, 0/8, 2/8.

All 24 observed 32-row iterator constructions matched the declared
task-stratified schedule. Replay fact IDs were present in actual datasets,
with 128 examples and 640 optimizer steps per arm.

## Decision

V28 converts the first V27 tie cell into a positive local preflight, but it
does not establish robustness: the second fresh `20260812` order cell
was not rerun, and the V27 matrix still contains two ties under its frozen
protocol. This is a targeted local protocol signal, not replication, a
general continual-learning result, SOTA evidence, or a breakthrough claim.
Do not provision an H100; peak memory remains approximately 0.764 GB.

The initial validator expectation of eight iterator audits was corrected after
inspection showed three legitimate 32-row iterator constructions per update
(validation/training boundaries). The same immutable model output then passed
the corrected independent validator; no model rerun was used.

Hashes:

`contract_sha256: 14d6f98f0f3133b72e9f962f6cf1222c45caa30a52fd4793a78cf5d9af9f556
manifest_sha256: de95fa8d0fceb48de6db5d8843f134b70a497d8758c75c0c9983df0da8ca02da
result_sha256:   53be170d61eafbd7926e9f6dbd58d69bc7d3c9b9e41f51b32a716aa6f387b21c`.
