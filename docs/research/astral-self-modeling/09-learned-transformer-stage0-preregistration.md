# Learned Tiny-Transformer Stage 0 Preregistration

## Boundary

State slice: `astral-stage0-learned-transformer-measurement-validity`.

Status: `LocalImplementationAuthorized`. Evidence ceiling:
`LocalLearnedModelMeasurementCandidate`. Execution: `CompletedInconclusive`.

This slice may add `tools/astral-stage0-learned/`, this document, and project
navigation only. It permits one bounded local training attempt for each frozen
seed and one locked evaluation. It does not permit observer training, actor
updates after evaluation, external services, benchmark evidence, accepted
evidence, or claims of self-modeling or mechanistic understanding.

## Frozen Actor and Task

- Framework: local PyTorch `2.12.0`, CPU, float32.
- Architecture: one custom post-normalized transformer block, sequence length
  12, vocabulary 32, model width 32, four attention heads, feed-forward width
  64, GELU, no dropout, learned token and position embeddings, CLS classifier.
- Candidate components: the four attention-head outputs at CLS before output
  projection.
- Task: four tagged bits `A/B/C/D` are permuted among deterministic
  family-specific nuisance tokens. The label is
  `(A XOR B) XOR (C AND D)`.
- Families: 320 from generator seed `20260726`; all 16 bit assignments per
  family.
- Splits: train `0..159`, development `160..191`, reserved audit `192..255`,
  untouched evaluation `256..319`. Earlier tests touched the reserved range, so
  it is permanently excluded from confirmatory evaluation.
- Actor seeds: exactly `11`, `23`, `37`.
- Training: AdamW, learning rate `0.003`, weight decay `0.01`, batch 128,
  gradient clip 1.0, exactly 800 updates, one attempt per seed.
- Eligibility: train and development accuracy must each be at least 0.95.

## Measurement Separation

The candidate tracer uses one untouched forward/backward pass:

\[
\widehat{\Delta}_c =
-\left\langle
\frac{\partial m}{\partial h_c}, h_c
\right\rangle
\]

where `m` is correct-minus-incorrect logit margin and `h_c` is one CLS head
output. All method scores are serialized in memory before any intervention
rerun. The intervention phase separately measures zero-ablation effects.
Gradient scoring does not call the intervention function or read measured
effects.

Matched patching uses the same family and nuisance pattern, preserves `B/C/D`,
and flips `A`. It is confirmatory only.

## Locked Methods

- candidate: gradient times activation;
- competitive baselines: activation L2 norm, gradient L2 norm, and attention
  mass on the four causal-token positions;
- controls: deterministic within-prompt score permutation and zero.

Every method sees the same four candidates. The candidate must beat every
competitive baseline; evaluation results cannot select a convenient baseline.

## Endpoint and Gate

Per-prompt normalized top-one selection regret is:

\[
\frac{|\Delta_{c^*}|-|\Delta_{\hat c}|}
{\max(|\Delta_{c^*}|,10^{-4})}.
\]

Prompts with maximum absolute effect at or below `1e-4` remain present with zero
regret and are marked uninformative. Aggregate equally by family, then seed.

For each competitive baseline, calculate
`D = regret_baseline - regret_candidate`. Use a deterministic 2,000-draw
hierarchical paired bootstrap, seed `20260727`. Practical margin: `0.05`.

A local learned-measurement candidate passes only if:

1. all checkpoints meet eligibility;
2. informative coverage is at least 0.80 for every seed;
3. mean `D > 0.05` and the 95% interval lower bound exceeds `0.05` against
   every competitive baseline;
4. `D > 0` independently for every seed and baseline;
5. the candidate beats the permuted control;
6. no-op, hook, deterministic-repeat, split, and record-census controls pass;
7. the candidate-selected patch effect exceeds each baseline-selected patch
   effect in aggregate and for every seed;
8. all artifacts and hashes validate;
9. the 30-minute and 256 MiB caps are respected.

Otherwise the run is `Null`, `Inconclusive`, or `Invalid`. Top-one accuracy,
patch comparisons, evaluation task accuracy, and per-seed measurements are
descriptive and cannot rescue primary failure. Rank, calibrated magnitude error,
and signed-effect endpoints are deferred because no development-only calibration
contract has been implemented.

## Claim Ceiling

Passing would show only that first-order internal attribution ranks interventions
better than the named baselines for this learned actor, task, candidate census,
and run family. It would not show complete circuit recovery, global causal
fidelity, introspection, observer value, self-correction, or safety.

## Locked Execution Record — 2026-07-26

The one permitted attempt completed computation in 14.05 seconds. An
inventory-only defect initially omitted the score-file exception for an
ineligible seed; the exact existing payload was finalized without retraining or
reopening evaluation.

| Field | Result |
|---|---|
| Protocol digest | `de5f00b5382f19028ab650a1a969ba53f9df2163e20e28acfd808145e4aaa666` |
| Manifest digest | `712c72a4770a515b27362200dcef48335a088a2d3c29b1dd927c91c52da88515` |
| Seed 11 train / development accuracy | `1.00 / 1.00` |
| Seed 23 train / development accuracy | `0.75 / 0.75` |
| Seed 37 train / development accuracy | `1.00 / 1.00` |
| Eligible evaluation records | 2,048 from seeds 11 and 37 |
| No-op / repeated-score / split controls | Pass |
| Semantic bundle validation | Valid |
| Frozen verdict | `Inconclusive` |

Seed 23 failed the preregistered 0.95 checkpoint-eligibility floor. The protocol
forbids replacing the seed, changing training, or rerunning the confirmatory
family. Consequently the three-seed primary, coverage, placebo, and patch gates
were not estimable and Stage 0 did not pass.

Descriptively, the candidate was better than attention-mass and gradient-norm
baselines on the two eligible seeds, but it did not consistently beat activation
magnitude: the paired difference was favorable for seed 11 and unfavorable for
seed 37. Patch comparisons also failed the all-seed/all-baseline rule. These
descriptive results cannot be promoted or pooled into a redesigned run.

The bundle remained repository-external and was deleted after its aggregate
record and digests were captured here. Validation proves structural and metric
consistency only; it does not create accepted evidence.

Stage 1 observer work remains blocked. A new learned Stage 0 run family would
require a new dated preregistration, a training design chosen without using the
locked evaluation results for tuning, new untouched families, and another
independent pre-execution review.
