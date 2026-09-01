# Information-budget frontier protocol v1

State slice: `continual-learning-information-budget-frontier-v1`.

## Purpose

The prior plasticity-recovery family is closed. This is a separate synthetic
lane with a materially different theory: adaptation quality is governed by the
geometry of an update relative to protected-task sensitivity, not by replay,
reinitialization, or plasticity decay.

The counterfactual protected-subspace projection (CPSP) controller decomposes
each candidate update into a component in the span of protected-task gradients
and a component in their null space. For each fixed risk price `lambda`, it
evaluates a finite preregistered alpha grid and commits the mixture with the
largest counterfactual objective:

```text
adaptation_gain - lambda * positive_protected_forgetting
```

The controller uses only exact synthetic protected references and a shadow
calculation. It has no access to assessment outcomes during selection.

## Estimand and endpoint

For each trial, adaptation gain is base adaptation loss minus final adaptation
loss. Positive protected forgetting is the positive part of final protected
loss minus base protected loss. The primary endpoint is adaptation-forgetting
frontier utility (AFFU):

```text
AFFU = mean over lambda in {0.25, 0.50, 1.00, 2.00}
       (adaptation_gain - lambda * positive_protected_forgetting)
```

The candidate must beat both the untouched and fixed-adapter arms on the
assessment AFFU and pass every hard guard. Raw adaptation gain is secondary.

## Fixed design

- Arms: `untouched`, `fixed_adapter`, `cpsp_frontier`, and
  `random_projection_control`.
- Splits: fit, tune, and assessment, each with eight adaptation shards and
  four protected shards.
- Replicate seeds: `20260841`, `20260842`, `20260843`.
- Order seeds: `6811`, `6812`, `6813`, each tested forward and reverse.
- Candidate order: `grid3_lr032`, `grid5_lr032`, `grid7_lr032`,
  `grid5_lr024`, `grid5_lr040`.
- Candidate selection uses tune AFFU only. The selected candidate is locked
  before assessment.
- Assessment requires a structured independent-review JSON receipt bound to
  this packet's digest and a prediction lock bound to the validated fit/tune
  artifact and selected tune AFFU.
- Compute is equalized by fixed gradient and shadow-unit counts.

## Hard guards

- Positive forgetting at most `0.08` per trial.
- Calibration Brier score at most `0.20`.
- Exact rollback error at most `1e-12`.
- Fixed update and shadow compute counts.
- Forward/reverse order delta at most `0.08`.
- Independent aggregate-only validator passes.

Any guard, custody, lock, or validator failure stops the run. No adaptive
threshold changes, seed changes, order changes, split changes, or endpoint
changes are allowed.

## Custody and authority

The source and tests are additive under `experiments/continual_learning/`.
Run receipts are written outside the repository under
`/Users/shaanp/Documents/research-artifacts/continual-learning-information-budget-frontier-v1-20260829/`.
Only aggregate JSON, TSV, lock, digest, and summary files are retained. No
model or corpus is loaded, downloaded, or mutated.

The bounded autoresearch limit is five candidate iterations followed by one
locked assessment. The run stops early on an unguarded candidate or validator
failure. This lane does not authorize GiveMeANode, H100/provider execution,
Astral integration, base-weight updates, production traffic, or ZK/PQC
evidence. Its claim ceiling is
`LocalDevelopmentInformationBudgetFrontierSyntheticOnly`.

Every mutation in this protocol names state slice
`continual-learning-information-budget-frontier-v1`.
