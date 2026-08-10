# Stage 0C Intervention-Effect Target Validity V12

State slice: `astral-stage0c-intervention-effect-target-validity-v12`.

Status: `PreregisteredDevelopmentOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Question

Can a frozen, capacity-matched telemetry estimator predict directly measured
head-intervention effects on unseen actor seeds and unseen prompt families
better than an activation-only estimator?

This is an intervention-prediction feasibility test. It is not attribution
ground truth, a circuit discovery result, self-modeling, or introspection.

## Frozen Actor and Data Boundary

- architecture: V5 `FrozenScientificTransformer`, width 32, one block, four
  eight-dimensional heads;
- training: V7 `family-complete-2000`;
- training families: `0..159`;
- checkpoint-selection families: `160..191`;
- V12 exploratory actor seeds: `211, 223, 229`;
- V12 estimator-design families: `576..607`;
- V12 estimator-assessment families: `608..639`;
- prohibited confirmation seeds: `173, 179, 181`;
- prohibited family reserve: `512..575`.

Every estimator assessment row is out of family and out of actor seed: use
leave-one-actor-out folds, fit on the other two actors' design families, and
score only the held-out actor's assessment families.

## Canonical Targets

For every example and each of four heads, record the signed change in correct-
class margin under:

1. `zero_ablation`: replace the head output at the classifier token with zero;
2. `matched_patch`: replace it with the same-family counterexample head state
   produced by flipping input bit zero.

The resulting eight-dimensional effect vector is the canonical target.
Absolute ranking and top-one regret are secondary summaries.

## Frozen Estimators

All learned estimators use standardized deterministic ridge regression with an
intercept and `alpha = 0.001`. Standardization statistics come from the fit
fold only. The three learned panels have exactly 16 scalar inputs:

- `input_output_only`: four bits, two clean logits, signed clean margin, four-
  head identifier, two-operator identifier, label, XOR of bits zero and one,
  and AND of bits two and three;
- `activation_only`: four bits, signed margin, four-head identifier,
  two-operator identifier, label, selected-head activation
  norm/mean/max-absolute, and selected-head attention to causal positions;
- `telemetry`: the same 12-scalar non-privileged prefix as `activation_only`,
  plus selected-head activation norm, gradient norm, signed
  gradient-times-activation, and attention to causal positions.

`constant` predicts the fit-fold target mean. `shuffled_telemetry` applies a
fixed SHA-256-derived permutation to the four telemetry-only suffix values
across fit rows, then fits the same ridge estimator. No hyperparameter,
feature, seed, family, or method selection occurs after scoring.

## Metrics and Development Disposition

Report per estimator, held-out seed, and operator:

- mean squared error and mean absolute error;
- coefficient of determination, retained even when negative;
- Pearson correlation when defined;
- calibration intercept and slope from predicted to measured effect;
- top-one absolute-effect regret per example.

The telemetry estimator is `DevelopmentCandidateEligible` only if:

1. every actor qualifies at at least `0.95` train and development accuracy and
   reproduces its batch plan, checkpoint, selected step, and trajectory;
2. all rows and both operators are present and finite;
3. telemetry MSE is at least `5%` lower than activation-only MSE for every
   held-out seed and operator;
4. telemetry beats `input_output_only`, `constant`, and
   `shuffled_telemetry` on pooled MSE;
5. telemetry pooled correlation is positive and pooled calibration slope lies
   in `[0.5, 1.5]`.

Otherwise classify `DevelopmentNoCandidate`. Either disposition leaves
`stage0_pass = false`, `accepted_evidence = false`, confirmation unauthorized,
and Stage 1 blocked.

## Sanity and Failure Rules

- Reject non-finite tensors, missing heads/operators, duplicate row IDs,
  unauthorized seeds/families, protocol-hash drift, repository-contained
  output roots, symlink output roots, and non-empty output roots.
- Record all actor qualifications before effect measurement.
- Parameter-randomization, label-randomization, alternate-reference, and
  additional granularity tests remain required before confirmation. Their
  absence prevents confirmation nomination even if the numerical development
  gate passes.
- Stop after this frozen panel. A failure does not authorize new estimator
  formulas or consumption of confirmation data.

## Artifact Contract

The repository-external bundle contains the protocol lock, actor qualification
records, semantic checkpoint digests, per-row JSONL records, fold predictions,
summary, and a SHA-256 manifest. The validator recomputes the manifest, protocol
binding, census, boundaries, metric aggregates, and final classification.
