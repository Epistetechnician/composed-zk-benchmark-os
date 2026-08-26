# V40 fresh-task fixed-optimizer acquisition eligibility

State slice: `continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40`.

## Frozen contract

V40 executes the fresh-task campaign frozen by the V37 optimizer-seed policy
boundary. It uses the already-cached
`Qwen2.5-0.5B-Instruct-4bit` model, unchanged route-bound raw-text prompts,
task order `0123`, 160 LoRA iterations, 32 update rows, the fixed optimizer
seed base `20260856` plus task-id offsets, and fresh task seeds
`20260859`, `20260860`, and `20260861`.

The primary metric is campaign-wide acquisition eligibility: every task must
train above its no-update baseline, T0 must meet the train and held-out
`0.75` floors, and T0 must not emit a constant training output. Each case is
executed and independently validated before campaign aggregation. Retention,
interference, provider, production, and network execution are disabled in
this slice.

Claim ceiling: `LocalDevelopmentFreshModelAcquisitionEligibilityPreflight`.
This slice cannot establish retention, general continual-learning ability,
provider delivery, production readiness, SOTA, breakthrough, or accepted
scientific evidence.

## Execution status

The acquisition campaign completed at
`/private/tmp/continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40-20260824-r1`.
All three cases were independently valid and eligible. The independent
campaign validator returned `campaign_eligible: true`.

The acquisition report's internal canonical digest is
`3d91604f0e1705e74f2407ae31c9d56ad33ed0728cc9c1a52df72b2e5527e5be`.
The report file SHA-256 is
`fdfaabd01ec5da19ac99403f783e0d51faf9400a5de682c6580271d2f0fd61bb` in
both temporary and durable custody. The task readouts were identical for
all three fresh seeds:

| task seed | T0 no-update/train/test | T1 no-update/train/test | T2 no-update/train/test | T3 no-update/train/test |
| ---: | :--- | :--- | :--- | :--- |
| 20260859 | 0.50 / 1.00 / 1.00 | 0.00 / 1.00 / 1.00 | 0.25 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |
| 20260860 | 0.50 / 1.00 / 1.00 | 0.00 / 1.00 / 1.00 | 0.25 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |
| 20260861 | 0.50 / 1.00 / 1.00 | 0.00 / 1.00 / 1.00 | 0.25 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |

The durable acquisition source is
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-fresh-fixed-optimizer-acquisition-v40-20260824-r1`.

Because acquisition passed campaign-wide, the bounded retention continuation
was executed at
`/private/tmp/continual-learning-qwen25-fresh-fixed-optimizer-retention-v40-20260824-r1`
against that durable source. All three cases were independently valid and
eligible, including the source, bank-retention, naive-acquisition,
replay-acquisition, and replay-over-naive-retention gates.

| task seed | bank acquisition / retention / recovery | naive acquisition / retention / recovery | replay acquisition / retention / recovery | replay minus naive retention |
| ---: | :--- | :--- | :--- | ---: |
| 20260859 | 1.00 / 1.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 0.25 / 0.25 | +0.25 |
| 20260860 | 1.00 / 1.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 0.25 / 0.25 | +0.25 |
| 20260861 | 1.00 / 1.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 0.25 / 0.75 | +0.25 |

The retention report's internal canonical digest is
`946706a82ee968d857cef4d0b2ee0aa93a5e5a933a399b782ba8b835c80596e6`.
The retention report file SHA-256 is
`aa40d5e137913a7147046a8adb379fa0b576edc63b90d73976d97bd6e34baae6` in
both temporary and durable custody. The durable retention report is at
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-fresh-optimizer-retention-v40-20260824-r1/campaign_report.json`.

This remains local fresh-task acquisition and retention preflight evidence.
It does not establish general continual-learning ability, second-model
replication, provider delivery, production readiness, SOTA, breakthrough, or
accepted scientific evidence. Network, provider, and production execution
were false in both campaign reports.
