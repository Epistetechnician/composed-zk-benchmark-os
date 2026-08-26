# V38 fixed-optimizer retention preflight

State slice: `continual-learning-qwen25-fixed-optimizer-retention-v38`.

V38 consumes only the durable V37 acquisition campaign after independently
validating its three eligible cases. It keeps the Qwen2.5 model, route-bound
raw-text prompt, four-task order, task seeds, fixed optimizer seed policy,
optimizer settings, and fresh V34 readout seam unchanged. It adds the
retention boundary: Task 0 is acquired, Tasks 1–3 are applied as sequential
updates, Task 0 is read without source context, and Task 0 is explicitly
reacquired for recovery.

The comparison panel is:

- immutable task-routed adapter bank;
- naive sequential raw-text LoRA;
- bounded replay sequential raw-text LoRA;
- no-update control.

The single primary metric is replay retention minus naive retention. The
candidate gate requires a Task 0 acquisition floor for both sequential
strategies, an immutable-bank retention floor, and replay retention strictly
above naive retention. Recovery is recorded but is not used to tune or select
the assessment result.

The V38 experiment is independently executed relative to the V37 source
campaign, but it is not an independent model confirmation: the acquisition
manifests and immutable bank are intentionally reused as the validated input.
No provider calls, production operation, network access, second model, or
promotion to accepted scientific evidence is authorized.

Claim ceiling: `LocalDevelopmentModelRetentionPreflight`.

## Execution record

The campaign artifact, exact metrics, hashes, validator output, and durable
custody path will be appended here only after the campaign and independent
validator both complete. A failed gate remains a negative retention result;
the runner must not rewrite or promote it.

## Executed result

The first attempt was quarantined at
`/private/tmp/continual-learning-qwen25-fixed-optimizer-retention-v38-20260824-r1-incomplete`
after a runner-only audit-directory defect. The second attempt was quarantined
at
`/private/tmp/continual-learning-qwen25-fixed-optimizer-retention-v38-20260824-r2-incomplete`
after the independent validator exposed replay-order reconstruction drift.
Neither incomplete attempt is treated as evidence. The defects were fixed
before the sealed r3 execution.

Campaign root:
`/private/tmp/continual-learning-qwen25-fixed-optimizer-retention-v38-20260824-r3`.

Durable custody:
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-fixed-optimizer-retention-v38-20260824-r3`.

The independent campaign validator returned `valid: true` and
`campaign_eligible: true`. The exact Task 0 endpoint metrics were:

| task seed | no-update retention | adapter-bank retention | naive acquisition / retention / recovery | replay acquisition / retention / recovery | replay minus naive retention |
| --- | ---: | --- | --- | ---: | ---: |
| 20260856 | 0.50 | 1.00 / 1.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 |
| 20260857 | 0.50 | 1.00 / 1.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 |
| 20260858 | 0.50 | 1.00 / 1.00 / 1.00 | 1.00 / 0.00 / 1.00 | 1.00 / 0.25 / 0.25 | 0.25 |

All three cases passed the bank retention floor, naive and replay acquisition
floors, source acquisition eligibility, and strict replay-over-naive
retention gate. The primary metric is positive in all cases. This is local
retention preflight evidence for the declared raw-text adapter mechanisms; it
does not establish a general continual-learning improvement or independent
model confirmation.

The campaign report's internal digest is
`baae32fca3ca93ea48e5ec611002f5d0dfd55b1af0585f9e180e13746f77d1e4`.
The report file SHA-256 is
`93e722ad6f02aff05aa8a3e590d9b9c59b229da64bcdde5a3562ec7d4a0f7e3f` in both
temporary and durable custody. Case canonical result digests are:

- `20260856`: `b0240c8cc565293c065c53a16f2f474d69d9673ea1af33e5446cdb618cb97f1a`
- `20260857`: `5077be7fa36fb3f1718add886c792dc65ecdbcfc0f6e5e1e2361c840982d300e`
- `20260858`: `f34a7728a375c197d67b768e6c6828ffcfe72e396b0028764416f68840aacc3d`

Provider execution, production operation, network access, second-model
replication, accepted scientific-evidence mutation, and promotion beyond
`LocalDevelopmentModelRetentionPreflight` were not performed.
