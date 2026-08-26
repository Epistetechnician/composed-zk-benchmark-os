# V37 fixed-optimizer acquisition preflight

State slice: `continual-learning-qwen25-fixed-optimizer-acquisition-v37`.

V37 validates the V36 optimizer-seed diagnosis at full four-task campaign
scale. It reuses the V34 raw-text update format, exact route-bound prompt,
Qwen2.5 model, task order, 160 iterations, 32 update rows, and independent
case/campaign validators. Task seeds remain `20260856`, `20260857`, and
`20260858`. The optimizer seed base is fixed to `20260856`, the first seed in
the already-declared V36 set, with explicit per-task training seeds
`20260856 + task_id`.

This is a post-diagnosis repair validation, not independent confirmation:
the fixed optimizer policy was selected from V36 after observing the target
seed sensitivity. It is not seed mining because the policy is frozen before
the V37 campaign cases execute, but it cannot support an independent
replication claim.

The campaign is acquisition-only. Retention, interference, reacquisition,
provider, production, and network work remain disabled. A campaign-wide pass
would authorize only separate consideration of retention under its own
contract; it would not itself be retention or production evidence.

Claim ceiling: `LocalDevelopmentModelAcquisitionEligibilityPreflight`.

## Executed result

Campaign root: `/private/tmp/continual-learning-qwen25-fixed-optimizer-acquisition-v37-20260824-r1`.

Durable artifact custody: `/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-fixed-optimizer-acquisition-v37-20260824-r1`.

The independent campaign validator returned `valid: true` and
`campaign_eligible: true`. All three cases passed all four acquisition gates:
trained T0 accuracy above its no-update baseline, T0 train floor, T0 held-out
floor, and nonconstant T0 output. The full task readout was:

| task seed | optimizer seeds by task | T0 no-update / train / test | T1 no-update / train / test | T2 no-update / train / test | T3 no-update / train / test |
| --- | --- | --- | --- | --- | --- |
| 20260856 | 20260856, 20260857, 20260858, 20260859 | 0.50 / 1.00 / 1.00 | 0.00 / 1.00 / 1.00 | 0.25 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |
| 20260857 | 20260856, 20260857, 20260858, 20260859 | 0.50 / 1.00 / 1.00 | 0.00 / 1.00 / 1.00 | 0.25 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |
| 20260858 | 20260856, 20260857, 20260858, 20260859 | 0.50 / 1.00 / 1.00 | 0.00 / 1.00 / 1.00 | 0.25 / 1.00 / 1.00 | 0.50 / 1.00 / 1.00 |

The campaign report's internal canonical digest is
`c622d08dbb44f5dd726a7fece6efbecaae84583760f8940e46c257ac6afe3797`.
The report file SHA-256 is
`4644cacd736f1a29450bee2023ba8a40e5cd576aed32f7dc1f97946c8a35ae83` in
both temporary and durable custody. The three result canonical digests are:

- `20260856`: `1731a6ff8667a334083dd68441a7f8efcba8ecc9d34482f97a03bf6f51c3cedc`
- `20260857`: `d085402adcff6b5dd8386d7a0b2aad3d9df8284b404506a696957c0d6d8d7507`
- `20260858`: `19740f12742bac5b6db04c027c1ee7bad16673aa499c7c885982e12de09bdbc9`

This result clears acquisition eligibility only. It does not establish
retention, interference resistance, continual-learning improvement, provider
delivery, production readiness, or an independent replication. No retention,
interference, provider, production, or network execution was performed.
