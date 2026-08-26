# V41 fresh-task order retention replication

State slice: `continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41`.

## Frozen contract

V41 consumes only the campaign-eligible V40 acquisition source for fresh task
seeds `20260859`, `20260860`, and `20260861`. It crosses those seeds with
noncanonical task orders `0213`, `0312`, and `0132` while preserving the
cached Qwen2.5 model, fixed optimizer seed base `20260856`, raw-text update
seam, replay capacity, recovery budget, and V40 retention gates.

The primary metric is replay retention minus naive retention. Every case is
executed in its own subprocess and independently validated before campaign
aggregation. Provider, production, network, and second-model execution are
disabled.

Claim ceiling: `LocalDevelopmentFreshTaskOrderRetentionReplication`.

## Candidate inventory boundary

The current local model cache does not provide a new eligible second-model
candidate. The sealed Llama V27 replication is negative; the DeepSeek model
directory contains no regular model files; the gpt-oss directory contains only
`.DS_Store`. V41 therefore strengthens same-model order robustness without
presenting it as second-model evidence.

## Execution status

The first V41 attempt was quarantined at
`/private/tmp/continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41-20260824-r1-incomplete`
after the independent validator detected a runner manifest-digest binding
defect. The runner was corrected to recompute the manifest digest after
binding the V41 state slice and order.

The corrected campaign completed at
`/private/tmp/continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41-20260824-r2`.
All 9 cases were independently valid and eligible; the campaign validator
returned `campaign_eligible: true`.

The report's internal canonical digest is
`58e4cf347615b358c31b1ad915a743213259e0e3a6f004c4f24a4a0353181adc`.
The report file SHA-256 is
`081624933c9f430bdef189270c2f2566c36806c417bacad741684b21f97e2edb` in
both temporary and durable custody. The durable report is at
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-fresh-fixed-optimizer-order-retention-v41-20260824-r2/campaign_report.json`.

All immutable-bank retention floors passed. Naive retention was `0.00` in
all nine cases. Replay retention exceeded naive retention in every case, with
the following deltas:

| task seed | order `0213` | order `0312` | order `0132` |
| ---: | ---: | ---: | ---: |
| 20260859 | +0.50 | +0.25 | +1.00 |
| 20260860 | +0.25 | +0.25 | +1.00 |
| 20260861 | +1.00 | +0.25 | +0.75 |

Replay recovery varied by seed and order (`0.25` to `1.00`), so the result is
reported as order-replication evidence rather than flattened into a single
scientific score.

V41 strengthens same-model fresh-seed order robustness. It does not close the
second-model gap, provider validation gap, or production gap, and it does not
establish general continual-learning ability, SOTA, breakthrough, or accepted
scientific evidence.
