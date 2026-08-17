# Narrative–Mechanism Measurement Stress Test V31

State slice: `astral-narrative-mechanism-stress-test-v31`.

Status: `Executed / LocalDevelopmentSyntheticMeasurementStressTest`.

## Purpose

Stress-test the V30 measurement instrument before any trained-model or loss
experiment. The test expands the planted actor matrix, adds strong baselines,
and records variance and failure modes instead of reporting only one favorable
four-feature circuit.

## Frozen matrix

- dimensions: `4`, `8`, and `12` features;
- task seeds: `0..3` for each dimension and mode;
- modes: `clean_linear`, `noisy_linear`, and `unmodeled_interaction`;
- twelve deterministic held-out intervention trials per task;
- deterministic fit interventions are used only for the train-mean baseline;
- no random runtime state, model, provider, network, prompt, trace, secret,
  PII, or prior Astral artifact.

The clean actor is linear with sparse planted weights. The noisy actor adds a
bounded deterministic measurement error to the mechanism report. The
interaction actor includes a held-out pair interaction that the linear report
cannot represent. The interaction mode is a declared instrument limitation,
not a failed claim hidden from the result.

## Observers and controls

Each task evaluates held-out intervention effects from:

- measured mechanism report;
- plausible narrative decoy;
- shuffled mechanism report;
- zero predictor;
- fit-only mean predictor;
- exact actor oracle, reported as a ceiling and not as a deployable observer.

The primary metric is `linear_all_baseline_win_rate`: the fraction of clean and
noisy linear tasks where the measured mechanism has strictly lower held-out
MSE than the narrative, shuffled, zero, and fit-mean baselines.

## Preregistered gates

- primary gate: linear all-baseline win rate at least `0.80`;
- narrative and shuffled controls must not be treated as equivalent to the
  mechanism report;
- interaction-mode failures, if present, must be counted and attributed to
  the unmodeled interaction rather than excluded;
- per-task MSE mean, variance, and failure counts must be emitted by the test;
- claim ceiling must remain
  `LocalDevelopmentSyntheticMeasurementStressTest`.

## Executed result

The matrix contained `36` tasks: `24` clean/noisy linear tasks and `12`
unmodeled-interaction tasks.

| Metric | Result |
| --- | ---: |
| Linear all-baseline win rate | `24/24 = 1.0` |
| Linear narrative-control win rate | `24/24 = 1.0` |
| Interaction all-baseline failures retained | `7/12` |
| Measured mechanism mean MSE | `12.0833333333` |
| Narrative mean MSE | `25.9236111111` |
| Shuffled mechanism mean MSE | `51.1689814815` |
| Zero mean MSE | `37.4074074074` |
| Fit-mean baseline mean MSE | `34.8518518519` |
| Measured MSE variance | `305.2006172840` |
| Exact actor oracle mean MSE | `0.0` |

The primary gate passed with a linear all-baseline win rate of `1.0`. The
seven interaction failures were retained as an explicit limitation: a linear
mechanism report cannot represent the planted pair interaction.

The pure-data test passed through standalone `rustc` with three passing tests
and emitted the aggregate summary. The focused V31 Cargo test, V30 regression
test, repository claim-boundary test, full `cargo test -p zkbench-core --quiet`,
format check, and diff check all passed. A transient earlier Cargo failure in
the unrelated untracked `crates/zkbench-core/src/experiment.rs` path resolved
in the dirty checkout without mutation by this task.

## Nonclaims

This protocol does not test a trained model, model-family transfer,
mechanistic faithfulness, self-understanding, introspection, provider attacks,
HSAI security, cryptography, Stage 0C, Stage 1, benchmark performance,
production readiness, or consciousness. A passing matrix validates only that
the local scoring design distinguishes measured structure from specified
decoys across a broader synthetic range.
