# Stage 0 Training Qualification and Independent Replication V2

## Boundary

State slice: `astral-stage0-training-qualification-and-independent-replication-v2`.

Status: `LocalImplementationAuthorized`. Evidence ceiling:
`LocalLearnedModelMeasurementCandidate`. Execution:
`QualificationFailedPreflight`.

This run changes only the actor-training procedure in response to v1 seed 23
failing train/development eligibility. It does not use v1 evaluation outcomes to
change the actor architecture, task, candidates, tracer, baselines,
interventions, endpoint, thresholds, or gate.

Touch surface: this document, project navigation, and additive files under
`tools/astral-stage0-learned-v2/`. V1 files and records remain immutable.

## Frozen Training Change

- Actor: unchanged v1 one-block, width-32, four-head, feed-forward-64 model.
- Task and generator: unchanged.
- Train families: `0..159`; development families: `160..191`.
- Families `192..319`: permanently excluded.
- Evaluation-v2 families: untouched `320..383`.
- Optimizer, learning rate, weight decay, batch size, and gradient clipping:
  unchanged.
- Update budget: 1,500.
- Development evaluation: every 25 updates.
- Checkpoint selection: lowest finite development cross-entropy; exact ties go
  to the earliest update.
- Eligibility: selected checkpoint train and development accuracy each at least
  0.95.

## Qualification Gate

Qualification seeds are exactly `41, 43, 47, 53, 59`. Each is trained twice.
Qualification passes only if all five:

1. meet train/development eligibility in both reproductions;
2. select the same update twice;
3. produce identical semantic checkpoint and trajectory digests twice;
4. use no evaluation-v2 example;
5. remain finite and within the 30-minute total cap.

Qualification seeds cannot substitute for confirmatory seeds. Failure stops the
run before evaluation-v2 materialization.

After qualification, confirmatory seeds `11, 23, 37` are trained and reproduced
under the same rules. All three must pass with identical update and checkpoint
digest before `qualification.lock.json` permits evaluation construction.

## Frozen Measurement

The four v1 CLS attention-head candidates, gradient-times-activation candidate,
activation-norm, gradient-norm, attention-mass baselines, permuted and zero
controls, zero ablation, matched patching, dead zone, normalized regret,
2,000-draw hierarchical bootstrap, seed `20260727`, practical margin `0.05`,
coverage `0.80`, and every-seed/every-baseline gates remain unchanged.

Scores and captures must be materialized and hashed before intervention effects
are computed. Missing seeds are never represented by zero-filled estimates.

## Verdicts

- `QualificationFailed`: qualification seed failure; evaluation unopened.
- `Inconclusive`: confirmatory actor qualification or estimability failure;
  evaluation unopened.
- `Invalid`: contamination, control, cap, or artifact failure.
- `Null`: valid complete evaluation misses any scientific gate.
- `Pass`: valid complete evaluation clears every unchanged gate.

Passing remains local learned-model measurement evidence only. It does not
authorize observer training, Qwen, SRE self-correction, actor updates, accepted
evidence, or mechanistic-understanding claims.

## Qualification Record — 2026-07-26

The first qualification seed, `41`, was run twice through the frozen
1,500-update, development-loss checkpoint-selection procedure during
pre-evaluation qualification testing. Its combined eligibility and
reproducibility predicate returned false.

The protocol requires all five qualification seeds to pass and mandates an
immediate stop on any failure. Therefore:

- remaining qualification seeds were not used to rescue the procedure;
- confirmatory seeds `11, 23, 37` were not trained under V2;
- `qualification.lock.json` was not issued;
- evaluation-v2 families `320..383` were never materialized or inspected;
- no V2 measurement records, tracer comparison, patch result, or scientific
  verdict exists.

The preflight test did not initially persist submetrics. A separately classified
development-only diagnostic reran seed 41 without accessing or qualifying the
holdout:

| Diagnostic | Result |
|---|---|
| First train / development accuracy | `0.8125 / 0.8125` |
| Second train / development accuracy | `0.8125 / 0.8125` |
| Selected update | `1200` in both runs |
| Selected development loss | `0.26009008288383484` |
| Checkpoint digest | `21c21ce1abfefee3f1a3ff959fcf46469a33be97920724550a98cfe6df442605` |
| Trajectory digest | `ad7df6c4e5a601f8a9aa4d28ed6118272953e8d4ebc31c6abc6182a9f77222bc` |
| Reproducible | Yes |

The failure is training capability, not nondeterminism or checkpoint-selection
instability. Increasing the update budget from 800 to 1,500 did not make the
unchanged actor reliably learn the task. The diagnostic is not a V2
qualification retry and cannot reverse the stop classification.

The classification is `QualificationFailedPreflight`, not `Inconclusive`,
`Null`, or `Pass`.

Further progress requires a new dated training-qualification protocol that first
makes qualification diagnostics durable, uses a test-only seed distinct from
the frozen qualification panel, and still does not access families `320..383`.
A larger actor would be a new exploratory actor family, not an independent
replication of V1.
