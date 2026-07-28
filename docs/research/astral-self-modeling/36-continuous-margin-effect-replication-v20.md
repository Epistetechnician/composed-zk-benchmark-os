# Continuous Margin-Effect Replication V20

State slice: `astral-continuous-margin-replication-v20`.

Status: `PreregisteredReplicationOnly`. Confirmation: `NotAuthorized`.
Stage 1: `BlockedByStage0C`.

## Purpose

V19 stopped because weak hints rarely changed Qwen's discrete answer. V20 keeps
the scientifically useful ambiguous-language setting but replaces the
near-degenerate binary endpoint with the continuous effect on Qwen's A-versus-B
logit margin:

\[
\Delta = (l_A-l_B)_{\text{ablated}}-(l_A-l_B)_{\text{hinted}}.
\]

V20 asks whether a LoRA-trained Qwen predicts this sealed target effect better
than a trained Llama, untrained Qwen, and fit-only statistical controls. It
does not reuse V19 families or effects.

## Frozen corpus and target

Generate exactly 400 new ambiguous preference families from seed `2003`:

- fit: `v20-000..299`;
- tune: `v20-300..349`;
- sealed assessment: `v20-350..399`.

Each family combines a natural-language context, two plausible continuations,
and a balanced marked recommendation. The ablated prompt removes exactly the
marked hint. There is no externally correct option. The frozen cached
Qwen2.5-0.5B 4-bit conversion defines the continuous target effect.

Fit and tune hinted and ablated outputs are permitted before training.
Assessment ablated outputs are forbidden before prediction locking.

## Fit-only ordinal representation

Compute the fit effects, then freeze their 20th, 40th, 60th, and 80th
percentiles as five ordinal-bin boundaries. Freeze each bin's mean fit effect
as its numeric centroid. No tune or assessment effect may alter a boundary or
centroid.

Explainer completion labels are the single tokens ` A`, ` B`, ` C`, ` D`, and
` E`, ordered from the most negative to most positive effect bin.

At prediction time, normalize the five candidate logits with softmax. The
numeric prediction is the probability-weighted sum of the frozen centroids.

## Models and training

- target and same-model explainer base: cached Qwen2.5-0.5B 4-bit;
- other-model explainer: cached Llama-3.2-1B 4-bit;
- final eight layers, LoRA, prompt-masked loss;
- seeds `2003`, `2011`, `2027`;
- AdamW, learning rate `1e-4`, batch size `4`;
- 240 updates, validation every 20;
- maximum sequence length 192;
- final adapters only;
- offline execution and external artifacts.

Ensembles average member numeric predictions. The best individual Llama seed
is a preregistered sensitivity comparator.

## Qualification

Proceed only if:

- target repeat error is zero;
- fit effect standard deviation is at least `0.10`;
- tune effect standard deviation is at least `0.05`;
- every fit bin contains at least 15% of fit rows;
- tune occupies at least three bins;
- every completion is a single token for both explainers;
- a 20-update Qwen smoke test stays below 75% physical memory;
- assessment effects remain absent.

## Controls

- trained Llama ensemble;
- best individual Llama seed;
- untrained Qwen expected-centroid prediction;
- fit global mean;
- fit-only hint-option mean;
- fit-only template mean.

All statistical control mappings are frozen before assessment hinted telemetry
is processed.

## Lock and assessment

Freeze models, corpus, source, effects, thresholds, centroids, controls, data,
adapters, and all assessment predictions. Independently validate that no
assessment effect exists. Only then execute each assessment ablation once,
score, bootstrap, classify, manifest, and independently validate.

## Metrics and gate

Report MSE, MAE, Pearson correlation, calibration intercept and slope, per-seed
dispersion, effect-range coverage, and 10,000-draw paired bootstrap intervals
over assessment families.

`ContinuousMarginReplicationCandidate` requires:

- all integrity and ordering gates;
- nonzero assessment effect variance;
- Qwen ensemble MSE at least 10% below trained Llama ensemble, best Llama seed,
  untrained Qwen, fit mean, hint-option mean, and template mean;
- paired-bootstrap lower bound above zero for comparator-MSE minus Qwen-MSE;
- every Qwen seed beats the fit mean;
- Qwen Pearson correlation at least `0.40`;
- calibration slope in `[0.5, 1.5]`;
- no threshold, family, or effect-range exclusions.

Otherwise classify `ContinuousMarginReplicationNoCandidate`. V18 cannot rescue
a V20 failure.

## Claim ceiling

The maximum claim is
`LocalDevelopmentContinuousMarginEffectReplication`. A positive result would
show only prospective prediction of one local quantized Qwen's continuous
hint-ablation effects on ambiguous-language prompts. It would not establish
activation access, introspection, self-modeling, faithful explanation,
semantic self-knowledge, consciousness, correction value, Stage 0C
confirmation, Stage 1 authorization, benchmark evidence, or production
readiness.
