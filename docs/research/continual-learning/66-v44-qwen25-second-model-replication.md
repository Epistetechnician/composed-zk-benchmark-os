# V44 Qwen2.5 mechanism replication on a second model

Date: 2026-08-26

State slice: `continual-learning-qwen25-second-model-replication-v44`

Claim ceiling: `LocalDevelopmentSecondModelReplication`

## Frozen protocol

V44 tests whether the exact V40/V41 raw-text task-adapter-bank mechanism
transfers from the selected Qwen2.5 candidate to the already-cached
`Llama-3.2-1B-Instruct-4bit` checkpoint. The Qwen2.5 V43 dossier remains the
parent candidate-selection record. Existing Llama and Qwen3.6 sealed results
remain negative records and are not relabeled or reused as positive evidence.

The frozen second-model path is:

`/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit`

The parent candidate path is:

`/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit`

V44 uses fresh task seeds `20260862`, `20260863`, and `20260864`; fixed
optimizer seed base `20260856`; canonical acquisition/retention order `0123`;
orders `1023`, `1203`, and `1302`; 160 iterations; update budget 32; replay
capacity 24; and recovery budget 20. The order set is disjoint from V41's
`0213`, `0312`, and `0132` set.

The campaign freezes the V40/V41 task construction, prompt/completion masking,
optimizer surface, replay membership, assessment, and eligibility semantics.
The gates are acquisition improvement and target floors, nonconstant target
output, bank retention, naive/replay acquisition floors, and replay retention
strictly above naive retention. Prediction outputs are locked before
assessment effects are generated.

## Execution and custody contract

Before execution, the offline MLX runtime must emit a model manifest and
inference-only receipt. The receipt is independently revalidated against the
cached checkpoint and bound into the V44 contract. The V43 parent dossier is
also independently revalidated and bound by both its dossier digest and file
SHA-256.

Each acquisition, retention, and order-retention case runs in a separate
subprocess. Every case is written to a new immutable external artifact root,
then independently validated. The aggregate validator reruns the runtime and
parent validators, revalidates every case, checks saved validator results,
recomputes all digests, and rejects downstream execution after a failed gate.

No downloads, network access, adaptive tuning, result reuse, provider calls, or
production operation are allowed. Promotion requires all `3 + 3 + 9 = 15`
cases to be valid and eligible. A valid negative acquisition result is a
completed replication boundary, not an execution failure and not evidence for
a positive general continual-learning claim.

## Result

The immutable V44 artifact root is:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-second-model-replication-v44-20260826-r1`

The offline MLX runtime preflight independently validated with `valid=true`.
Its model manifest digest is
`ea36d761a8af224a35f644ff77e9871d80452288174012e6c82884327bfde680`; the
runtime receipt file SHA-256 is
`2de1317f703ebb766fba7690cc1a94e99b7557944257afbf89178320144bef85`.

The V44 aggregate validator independently returned `valid=true` with the
classification
`LlamaSecondModelReplicationStoppedAtAcquisitionEligibility`:

- acquisition: `3/3` cases structurally valid, `0/3` eligible;
- retention: `0` cases executed because acquisition eligibility failed;
- order retention: `0` cases executed because acquisition eligibility failed;
- total: `3/15` executed, all three structurally valid, replication ineligible.

For every fresh acquisition seed (`20260862`, `20260863`, `20260864`), the
frozen gates were identical: `all_task_train_above_no_update=false`,
`target_train_floor=false`, `target_heldout_floor=false`, and
`target_not_constant_output=false`. The target train and held-out outputs were
constant `A` for all three seeds. This is a valid negative second-model
replication boundary, not a runner failure, and no retention or order result
was generated.

The signed V44 contract digest is
`a501157d87d9ce86a8a4f18516d8012c7bf41468d3a31ad46cb17dbc98c4a7e0`; its file
SHA-256 is
`d0f3c10a3ede85845d04c180a0b80c72b042d167de71fc82831cd1bab65742a9`.
The signed report digest is
`310b78d7830a2d1a449136d89c0883b42c22bbf645a90e36b147e468b2553a47`; its file
SHA-256 is
`0680ec9db0d2cc824287345b14916de4cb4441fa9bc1a1738d0d5fed5541dfe9`.

## Boundary

V44 cannot establish general continual learning, provider readiness, production
readiness, or accepted scientific evidence. The negative result closes this
second-model candidate under the frozen mechanism; it does not authorize
adaptive tuning, relabeling, or another run in this state slice.
