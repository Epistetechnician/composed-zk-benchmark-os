# V34 Qwen2.5 raw-text acquisition record

State slice: `continual-learning-qwen25-raw-text-acquisition-v34`.

Protocol: `v34-qwen25-raw-text-acquisition-eligibility-v1`.

V34 is one focused acquisition-only repair against the V32 Qwen2.5
instability diagnosis. It preserves the V32 task construction, route-bound
assessment prompt, readout, fixed budgets, and target gates. It changes only
the update serialization: each training row is a single `text` field made of
the unchanged route-bound prompt and one completion, with completion masking
disabled (`--mask-prompt` absent). The campaign uses fresh fixed seeds
`20260856`, `20260857`, and `20260858`, in order `0,1,2,3`.

The runner, per-case validator, and campaign validator are additive under
`experiments/continual_learning/`. Each case is executed in a subprocess and
validated independently before campaign aggregation. The validator requires
exact raw-text row shape and prompt/completion binding, sealed artifact
digests, four adapters, exact train and held-out readout shape, and the full
all-task acquisition gate.

## Execution boundary

This phase executes local model training and isolated local readout only. It
does not execute retention, interference, reacquisition, provider calls,
production deployment, or network access. A passing campaign would authorize
only consideration of a separately specified retention phase; it would not be
retention evidence or a production claim.

## Result

The first attempted receipt was quarantined at
`/private/tmp/continual-learning-qwen25-raw-text-acquisition-v34-20260822-r1-incomplete`.
The original corrected transient receipt was
`/private/tmp/continual-learning-qwen25-raw-text-acquisition-v34-20260822-r2`,
but that transient root was not available for current independent readback.
The exact fixed campaign was therefore reconstituted on 2026-08-24 directly
under durable external custody at
`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-raw-text-acquisition-v34-20260824-r1`.
The reconstituted campaign completed all three cases, reproduced the recorded
campaign report digest, and passed independent campaign validation from the
durable path. This reconstitution preserves the existing V34 result; it does
not expand the claim ceiling or authorize retention.

Campaign report digest: `fde48cdba2384c615c0863d173c8463c1be3165c58f7d1dddf25029a971a6e05`.

| Seed | Valid | Eligible | T0 train | T0 held-out | All-task gate |
| --- | --- | --- | ---: | ---: | --- |
| 20260856 | yes | yes | 1.00 | 1.00 | pass |
| 20260857 | yes | no | 0.25 | 0.25 | fail |
| 20260858 | yes | yes | 1.00 | 1.00 | pass |

The V34 raw-text boundary improves two fresh cases to full all-task
acquisition, but it does not remove seed sensitivity. The campaign result is
`campaign_eligible: false`; seed `20260857` fails the target floors and the
all-task train-above-baseline gate. The bounded stop is to retain this
negative acquisition result and not run retention.

Claim ceiling: `LocalDevelopmentModelAcquisitionEligibilityPreflight`.
