# Gemma 3 causal feature-effects V1 protocol

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v1`.

Protocol: `astral-trace-completeness-gemma3-causal-feature-effects-v1.0`.

## Claim ceiling and identities

The implementation and qualification ceiling is
`LocalDevelopmentGemma3CausalFeatureEffectsQualificationV1`. Only after the
sealed tune lock, a fresh held-out run, independent validation, and a genuine
packet-bound signed `ACCEPT` may the result be classified under
`LocalDevelopmentGemma3HeldOutCausalFeatureEffectsAssessmentV1`.

The model is the exact cached `google/gemma-3-1b-pt` checkpoint at
`/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`, with model
manifest digest
`5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81`. The
native runtime is PyTorch/Transformers eager attention, offline during model
execution. The required runtime identity is the V4 runtime manifest digest
`104c32975db6f7a80937fee9725312207527d194636be0059b110e70208c0aa0`, and the
asset is the official Gemma Scope 2 revision
`b738dc06961818c011fb2e44a316352ca0f4e873`, variant
`transcoder_all/layer_12_width_16k_l0_big_affine`. V1 requires fresh model,
runtime, asset-QC, corpus, and source digests in its own custody root.

Operator: `shaanp` on `Shaans-MacBook-Pro`. Runner:
`tools/astral-trace-completeness-gemma3-causal-feature-effects-v1/run_v1.py`.
Validator:
`tools/astral-trace-completeness-gemma3-causal-feature-effects-v1/validate_v1.py`.
The external custody root is
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v1`,
owner-only mode `0700`. GiveMeANode is the only permitted remote provider;
the exact node ID and allocation receipt must be supplied by the provider.

## Fresh corpus and retention

The fresh corpus is
`gemma3-causal-feature-effects-families-v1-20260831`, PRNG seed `2026083101`,
with 96 deterministic families: 32 fit, 32 tune, and 32 assessment. It is not
V4 data. Every family receives every declared arm in a fixed-seed randomized
order and every cell has three repeats. A failed family, arm, repeat, or event
accounting cell causes zero permitted attrition and closes the slice.

Prompts, token IDs, activations, logits, cache/state payloads, and per-trial
outcomes may exist only under the external raw custody root. Raw retention is
at most 72 hours after independent validation. The runner publishes only
aggregate rows, manifests, validator receipts, prediction-lock digests, and
deletion receipts. Raw expiry must prove an empty raw directory.

## Estimand and assumptions

The primary estimand is the paired mean change in the target-minus-distractor
logit margin under feature ablation versus natural execution, for each of four
fit-selected features evaluated on the held-out family IDs. The secondary
estimand is the paired total-variation change in the complete output
distribution, together with exact feature replacement, activation-patch, and
path-patch effects.

- Assignment: a fixed PRNG assigns arm order within each family; every eligible
  family receives every arm, so each causal contrast is within-family.
- Timing: the intervention occurs at generation step 0 after the declared
  layer-12 post-feedforward output and before the unchanged downstream pass.
- Consistency: the observed run is the potential outcome under the exact
  frozen model, module boundary, feature transform, donor, dtype, and runner.
- Positivity: all 96 sealed families, every arm, and all three repeats must
  execute and contribute; no imputation or selected-position exclusion exists.
- Interference: each family runs in isolation with a reset cache and no shared
  mutable model, adapter, or optimizer state.

## Executable causal abstraction and interchange

For recipient activation `h_p(t)`, input activation `x`, fixed encoder `E`,
fixed decoder `D`, and feature `j`, the exact feature-ablation donor is:

`h'_p(t) = h_p(t) + D(E(x),x) - D(E(x) with feature j set to 0,x)`.

Feature replacement substitutes the locked donor family’s value only at
feature `j` and the locked final sequence position. Activation patching sets
`h'_p(t)` to an exact-shape same-position donor activation. Path patching
applies the same replacement over the frozen path
`layer12.post_feedforward -> output_distribution`. All downstream modules,
cache updates, output distributions, sampled tokens, and behavioral links are
captured. The event metadata carries the intervention kind, feature index,
path ID, donor trial ID, and operator digest.

The four feature IDs are selected once by absolute fit activation, then frozen.
Fit effects fit the small graph
`feature_ablation_margin_delta ~ locked_feature_effect_mean`; coefficients are
digested before tune effects. No feature, layer, position, wrapper, threshold,
or control may be changed after the tune lock.

## Controls, falsifiers, and statistics

The fixed arms are natural, feature ablation, feature replacement, activation
patch, path patch, no-op, exact-copy, zero, shuffled donor, and constant donor.
No-op and exact-copy logit deltas must be `<=1e-5`; native parity must be
`<=1e-4`; deterministic repeatability must be `<=1e-5`; nonzero intervention
reach must exceed `1e-5`; output-distribution movement must exceed `1e-3` for a
qualifying causal effect. Missing cache transitions, malformed event census,
nonzero no-op/exact-copy effects, or shuffled/constant controls matching the
locked feature effect falsify the corresponding claim.

Uncertainty is 10,000 fixed-seed bootstrap resamples over family IDs with a
95-percent percentile interval. Holm correction at alpha `0.05` applies to the
four primary feature-ablation hypotheses. Power is preregistered at 0.80 for
standardized paired effect `0.50`, ICC `0.50`, 32 assessment families, and
three repeats per cell; the fixed-seed clustered simulation uses 10,000 draws
and must pass before assessment. Fresh V1 transcoder reconstruction is pooled
over the fit families and must satisfy NMSE `<=0.05`. Missingness is
fail-closed. Attrition is exactly zero.

## Authorization order

The order is: V4 freeze; source/runtime/model/asset/corpus/custody digests;
asset and corpus QC; independent review of the exact packet; GiveMeANode
allocation receipt and hard positive USD ceiling; fit feature selection and
effects; tune graph prediction and lock; independent signed `ACCEPT`; fresh
held-out causal scrubbing; independent aggregate validation; raw expiry; and
classification as either `HeldOutCausalFeatureEffectsAccepted` or
`NoCandidate`.

The repository currently authorizes implementation and qualification only.
Assessment effects and GiveMeANode execution remain closed until the missing
external allocation, spend, and independent-review facts are bound. This
protocol does not reopen V4, V48, Stage 0C, Stage 1, or the Evidence Ledger.
