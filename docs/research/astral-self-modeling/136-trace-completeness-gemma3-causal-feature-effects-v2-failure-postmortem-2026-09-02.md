# Astral Gemma 3 Causal Feature-Effects V2 Failure Decomposition

State slice: `astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3`.

This is an aggregate-only diagnosis of the permanently closed V2 slice
`astral-trace-completeness-gemma3-causal-feature-effects-v2`. It does not
reopen V2, retune its thresholds, reconstruct deleted rows, or use V2
scientific artifacts as V3 data.

## Terminal V2 result

V2 remains immutable `NoCandidate`. The fixed tune prediction gate was
`0.75 = 288/384`, below `0.80`. Feature `832` had tune Holm-adjusted
`p=0.32693958282470703`, so its tune effect gate failed. Fit reconstruction
NMSE `0.043354035141255125`, cross-half feature intersection `14`, fit effects,
power, and controls passed. Assessment and held-out scrubbing never opened.

The 384 prediction cells were four features x 32 tune families x three
repeats. They were not 384 independent families. V3 therefore makes family
the uncertainty and prediction unit and collapses repeats before scoring.

## What the aggregates identify

| Feature | Fit mean | Tune mean | Tune Holm p | Interpretation |
|---|---:|---:|---:|---|
| 385 | -0.06640625 | -0.087890625 | 0.003936767578125 | same direction; passed |
| 832 | 0.140625 | 0.087890625 | 0.32693958282470703 | weaker directional support; failed |
| 1529 | -0.18359375 | -0.28125 | 8.642673492431641e-07 | same direction; passed |
| 15972 | 0.052734375 | 0.056640625 | 0.013221502304077148 | same direction; passed |

Feature `832` had a nonzero-family rate of `28/32` in fit and `26/32` in
tune. Activation-rank stability therefore did not establish a stationary
causal feature-to-logit edge. The aggregate data show weakened replication,
not a universal sign reversal.

## What cannot be recovered

Raw deletion prevents assigning the 96 sign mismatches to prompt template,
operation, operand range, family, repeat, near-zero numerical changes,
coactivation, or downstream nonlinear interaction. It also prevents semantic
replay of donor tensors, logits, cache states, and intervention placement.
Passing parity, repeatability, no-op, exact-copy, event accounting, and
custody checks rules out a gross transport failure but does not prove
feature-semantic correctness after raw deletion. Simulated power does not
model context-dependent sign heterogeneity.

## Theory decision

The V2 isolated-feature theory is rejected as a robust predictive theory. A
genuinely new successor hypothesis is justified because V2 did not test it:

> A jointly causal three-feature SAE bundle has a non-additive downstream
> effect that is reproducible across family-disjoint splits; isolated feature
> activation rank is only candidate generation, not causal evidence.

This is a new treatment, new estimand, new selection rule, and new held-out
interchange test. It is not a layer, threshold, seed, or V2 effect repair.
The hypothesis remains unestablished until the V3 fit, tune, and held-out
causal-scrubbing gates pass.

