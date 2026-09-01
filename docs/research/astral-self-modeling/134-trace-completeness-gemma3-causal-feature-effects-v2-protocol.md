# Astral Gemma 3 Causal Feature-Effects V2 Protocol

State slice: `astral-trace-completeness-gemma3-causal-feature-effects-v2`.

Protocol identity: `astral-trace-completeness-gemma3-causal-feature-effects-v2.0`.

## Boundary and identities

This is a fresh continuation after the immutable V1 `NoCandidate` closure. V2
does not use V1 scientific corpus, prompts, token sequences, activations,
logits, per-trial effects, selected features, prediction locks, or result
bytes. Shared model and upstream asset identities are re-bound into a fresh
V2 custody chain; matching a historical digest does not make a historical
scientific artifact an input.

| Field | Frozen value |
|---|---|
| Model | `google/gemma-3-1b-pt`, local `gemma-3-1b-pt-bf16` |
| Model manifest digest | `5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81` |
| Runtime manifest digest | `f9a7697c44765df350baabb9b62f2d83a21f883abdf8555db9bcc8c250814caa` |
| Feature asset | `google/gemma-scope-2-1b-pt` revision `b738dc06961818c011fb2e44a316352ca0f4e873`, `transcoder_all/layer_12_width_16k_l0_big_affine` |
| Fresh asset QC digest | `35760a5a4bc47ab3ee11d9082e629f560449644753a8924bda30050351ebc361` |
| Operator | `shaanp` on `Shaans-MacBook-Pro` |
| Runner | `tools/astral-trace-completeness-gemma3-causal-feature-effects-v2/run_v2.py` |
| Validator | `tools/astral-trace-completeness-gemma3-causal-feature-effects-v2/validate_v2_slice.py` |
| Fresh custody root | `/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-effects-v2` |
| Provider | GiveMeANode, H100/CUDA 12.9, node `3f4edebf-5601-4de3-be62-fdd87db72906` |
| Spend ceiling | USD 50 hard ceiling; one bounded qualification only |
| Qualification ceiling | `LocalDevelopmentGemma3CausalFeatureEffectsQualificationV2` |
| Assessment ceiling | `LocalDevelopmentGemma3HeldOutCausalFeatureEffectsAssessmentV2` |

The node allocation receipt is execution authorization only. It does not
authorize model execution or assessment by itself. The exact packet must first
receive an independent packet-bound Ed25519 `ACCEPT`.

## Fresh corpus and predeclared feature stability

Corpus identity is
`gemma3-causal-feature-effects-cross-half-stability-v2-20260901`, seed
`2026090101`, manifest digest
`3ad84978dd63c240dd242f1b594b0750285b449187365b1904c26ad34a6f6d00`, with 96
families: 32 fit, 32 tune, and 32 assessment. The fit split is divided before
model-derived selection into a discovery half and replication half of 16
families each. The corpus public manifest exposes family identities and
digests, not prompt text.

The feature-stability estimand is the intersection of the top-16 feature ranks
computed independently from the absolute final-position transcoder activation
score in each fit half. The selection rule is fixed before new model data are
collected: require an intersection of at least four features; if that gate
passes, select exactly four from the intersection by pooled absolute activation
score, with deterministic tie-breaking. If it fails, close V2 as `NoCandidate`
and do not search another K, layer, asset, position, or corpus.

## Causal estimands and assumptions

The primary estimand is the paired mean change in target-minus-distractor
decimal-answer logit margin under feature ablation versus natural execution,
with three repeats per family/arm. Secondary estimands are total-variation
movement of the output distribution and effects of exact feature replacement,
activation patching, and one-edge path patching.

Assignment is fixed-seed balanced arm-order randomization within each family;
every eligible family receives every declared arm. Timing is generation step 0,
after the declared recipient module output and before the unchanged downstream
pass. Consistency means one observed run equals its potential outcome under the
exact frozen model, tokenizer, feature transform, donor, dtype, and downstream
computation. Positivity requires every sealed family, arm, and repeat to be
finite and present. Interference is excluded by one family per isolated run,
cache reset between trials, and no shared mutable model or adapter state.

The executable interchange operators are:

- Feature ablation: `h'_p(t)=h_p(t)+D(E(x),x)-D(E(x with feature j=0),x)` at
  `layer12.post_feedforward`.
- Feature replacement: `h'_p(t)=h_p(t)+D(E(x),x with feature j replaced by
  locked donor value)-D(E(x),x)`.
- Activation patch: `h'_p(t)=h_p^donor(t)` for an exact-shape, same-position
  donor run.
- Path patch: the same exact-shape replacement over the frozen path
  `layer12.post_feedforward -> output_distribution`.

Controls are `noop`, `exact_copy`, `zero`, shuffled donor, constant donor,
activation-only donor, and text-only donor. Falsifiers are no-op/exact-copy
identity, shuffled and constant controls, failed intervention reach, parity
failure, event-accounting failure, and a shuffled causal-scrub null.

## Gates and statistics

The fixed thresholds are primary alpha `0.05`, feature and prediction sign
agreement at least `0.80`, scrub balanced accuracy at least `0.80`, shuffled
scrub balanced accuracy at most `0.60`, native parity maximum absolute logit
delta `1e-4`, repeat maximum `1e-5`, no-op and exact-copy maximum `1e-5`,
nonzero effect at least `1e-5`, output TV at least `1e-3`, and pooled centered
transcoder NMSE at most `0.05`.

Uncertainty is a fixed-seed 10,000-resample bootstrap over family IDs with a
95-percent percentile interval. Holm correction is applied across the four
selected features for the primary ablation family; controls and secondary
effects are labeled separately. Power is a fixed-seed simulation target of
0.80 under standardized paired effect 0.50, ICC 0.50, 32 assessment families,
three repeats per cell, and 10,000 simulations. Missingness is fail-closed:
no imputation, replacement, selected-position exclusion, or partial-family
analysis. Attrition is zero after corpus sealing; any failed family, arm,
repeat, event count, or custody check closes the slice.

Feature selection, fit effects, and tune prediction are locked before any
assessment effects. Held-out assessment is admissible only if the fit and tune
gates pass, the exact packet has an independent signed `ACCEPT`, and the
configuration remains unchanged. A breakthrough claim requires both the fit
gate and fresh held-out causal-scrubbing gate, including passing shuffled and
constant controls. Otherwise the terminal classification is `NoCandidate`.

## Custody, retention, and publication

The root and all subroots are owner-only mode `0700`; private files are mode
`0600`. Raw prompts, token IDs, activations, logits, cache/state payloads,
per-trial outcomes, and raw event streams may exist only under the external
`raw/` subroot for at most 72 hours. The runner is offline during model
execution. Independent validation must verify source/model/runtime/asset/
corpus/node/review digests, event accounting, interventions, aggregate
recomputation, raw deletion, and final custody state. Only aggregate results
and digests may be published.

V2 is implementation/qualification-authorized, not a general observability,
introspection, causal-self-modeling, Stage 0C, Stage 1, benchmark,
production-readiness, or provider-evidence claim. No assessment result exists
until the independent review receipt and held-out gates are present.
