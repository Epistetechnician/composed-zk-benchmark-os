# Oak Lab H100 Replication V8 Synthetic Qualification

State slice: `oaklab-experience-learning-h100-replication-v8`.

## Disposition

The packet-bound independent V8 review is a valid `ACCEPT`:

- receipt: `docs/research/experience-learning/63-oaklab-h100-replication-v8-independent-review.json`
- receipt self-digest: `9b0bd10329a1d832fea702451d5e531fc94945625d6918594ddf3a544930ac34`
- reviewed packet: `d2b1d91ebe8a50ddf1c40e5ce698623913837ebd23f7c7a641a99eb737ae23a4`
- effects run by reviewer: `false`

That acceptance opened the additive synthetic qualification slice only. It did
not authorize fit/tune locks, assessment, real streams, provider allocation,
H100 execution, spend, energy capture, or publication.

## Execution

The qualification used the frozen V8 synthetic roster: six families, 48 locked
seeds (`4000` through `4047`), 256 rows per trajectory, and a 128-row fit / 128-row
tune boundary. Each arm consumed exactly one row per update. The reference was
fixed batch-one SGD. The candidate was the V8 lagged selective-credit controller
with the declared hash-assigned fit policy and locked argmax tune policy. No
replay, hidden accumulation, real data, model execution, provider call, or
energy measurement occurred.

Raw per-family qualification rows include both arm trajectories, row digests,
and counter evidence. The independent validator derives all family estimates,
Holm-adjusted primary tests, adaptation predicates, resource predicates, and
status from those rows and counters; no caller-supplied gate boolean is trusted.

Commands executed:

```text
python -B -m pytest experiments/experience_learning/tests/test_oaklab_h100_v8_synthetic_qualification.py -q
python -B -m experiments.experience_learning.oaklab_h100_v8_synthetic_qualification --output experiments/experience_learning/oaklab_h100_v8_synthetic_qualification.json
python -B -m experiments.experience_learning.validate_oaklab_h100_v8_synthetic experiments/experience_learning/oaklab_h100_v8_synthetic_qualification.json
```

Observed checks: `3 passed`; qualification status `no_candidate`; independent
validation status `valid`.

## Gate findings

The strict synthetic gate is `no_candidate`:

- drift and delayed-reward families met the Holm-adjusted loss/no-worse
  predicate, but the complete gate still failed;
- adaptation was no worse in the declared shift families but was not strictly
  better in any shift family;
- operations and parameter updates were lower for the candidate, but controller
  state storage exceeded the five-percent resource bound in every family;
- the pure-noise null showed no candidate advantage;
- hardware energy is `not_run`, and no real-stream evidence exists.

The result artifact is
`experiments/experience_learning/oaklab_h100_v8_synthetic_qualification.json`
with result digest
`d4c75884613b84c3e12a4779a039fc3e4c6d89685193a0ff1c672d2c2cb0302b`.

## Boundary

V8 remains `no_candidate`. The failure closes this synthetic attempt under the
V8 stop rules; it does not authorize retuning, real execution, GiveMeANode or
H100 spend, privileged energy capture, assessment, SOTA claims, or publication.
V7, V6, Phase 836, and the plasticity guard remain historical and closed.
Astral remains isolated.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v8`.
