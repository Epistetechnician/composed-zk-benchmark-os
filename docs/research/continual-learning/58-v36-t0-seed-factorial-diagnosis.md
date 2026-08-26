# V36 T0 task-seed versus optimizer-seed diagnosis

State slice: `continual-learning-qwen25-t0-seed-factorial-diagnosis-v36`.

V36 isolates the confound identified by V35. V34 used one campaign seed both
to construct the task split and to seed the LoRA trainer. V36 keeps the
Qwen2.5 model, raw-text update format, route-bound prompt, target T0, 160
iterations, 32 update rows, optimizer, and exact readout fixed while running
two one-factor arms:

- `optimizer_seed_arm`: task seed fixed to failing V34 seed `20260857`,
  optimizer seeds `20260856..20260858`;
- `task_seed_arm`: optimizer seed fixed to `20260857`, task seeds
  `20260856..20260858`.

Each case trains and reads only the T0 adapter. The independent validator
checks exact task identity, raw-text rows, adapter artifact, digests, and the
T0 gates: train above no-update, held-out at least `0.75`, and nonconstant
output.

This is a local diagnosis, not a campaign eligibility result. It does not
execute retention, interference, provider, production, or network work. The
six sealed cases completed and all six passed independent validation.

## Result

| Arm | Fixed factor | Eligibility outcomes | Finding |
| --- | --- | --- | --- |
| optimizer seed | task seed `20260857` | `true, false, true` | optimizer-seed variation observed |
| task seed | optimizer seed `20260857` | `false, false, false` | fixed failing optimizer seed remains failing |

The independent campaign validator returned `valid: true` with
classification `OptimizerSeedSensitivityObserved`. For the fixed failing
task split, optimizer seeds `20260856` and `20260858` reached `1.00` train and
held-out accuracy, while `20260857` reached `0.25` on both. Holding optimizer
seed `20260857` fixed produced `0.25` train and held-out accuracy for all three
task seeds. Three repeated identical readouts for both the pass and fail
adapters were byte-stable on train and held-out splits, so readout noise was
not observed. The repeated-readout payload digests were:

| Adapter | Split | Stable payload SHA-256 |
| --- | --- | --- |
| optimizer `20260856` | train | `57393a582abdbee0625c589a676fe58366783903a960cb5297037888c4087e65` |
| optimizer `20260856` | test | `b15d6fa01ecd455757d501e767b0d0b5fa9c8920b0370580a3f232ba3496bdb6` |
| optimizer `20260857` | train | `4784d979eb3f6d319f402b507689b713637a85b05561c9a6b3b8d01febf9eae3` |
| optimizer `20260857` | test | `4bad3537de392a9d49e9b725ef57aef33a83633e9ba33274109f80683bb7626e` |

Campaign report digest:
`c924bbd519cac0144535ea8572bbc92a785641d9a1ceb09decd563b709c5091b`.
The immutable campaign was executed at
`/private/tmp/continual-learning-qwen25-t0-seed-factorial-v36-20260824-r1`
and copied byte-identically into durable repository-external custody at
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-t0-seed-factorial-v36-20260824-r1`.
The campaign report file SHA-256 is
`02edf46eea99e7213e8bfffbf1db4efbb2beda46b3d0182bbbac93819ae82538`.

Live revalidation on 2026-08-24 independently checked all six sealed cases
from the durable custody root: the campaign validator returned `valid: true`,
the report digest matched the recorded value, and the custody root contained
80 files. No training or artifact mutation occurred during this
revalidation.

The diagnosis supports optimizer-seed sensitivity for this cached Qwen2.5
T0 route under the tested local conditions. It does not authorize retention;
the next required step is a full campaign rerun only after a separately
frozen optimizer-seed policy is defined.

Claim ceiling: `LocalDevelopmentQwen25T0SeedSensitivityDiagnosis`.
