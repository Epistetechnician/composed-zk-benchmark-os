# Gemma 3 end-to-end trace completeness V3 protocol

State slice: `astral-trace-completeness-gemma3-end-to-end-v3`

Date: 2026-08-30

Qualification ceiling:
`LocalDevelopmentGemma3EndToEndCausalTraceQualificationV3`

Maximum separately reviewed assessment ceiling:
`LocalDevelopmentGemma3HeldOutCausalTraceAssessmentV3`

## Scope and ordering

V3 is a fresh continuation of the closed V2 trace-completeness lane. V2 bytes,
corpora, activations, logits, per-trial results, and raw traces are not V3
inputs. V3 may reuse source-level capture infrastructure only through a
separately digest-bound adapter identity.

The ordered gates are:

1. Freeze this protocol and the source manifest.
2. Acquire only the fixed upstream asset variant and exact revision into the
   external custody root.
3. Run the independent pre-load review over the complete V3 source set,
   protocol, custody root, asset configuration, parameter schema, and upstream
   examples schema. Any source change invalidates the prior receipt.
4. Only after that review may the cached model be loaded for V3 qualification.
5. Run fresh fit/tune/assessment-family generation-time trace qualification.
6. Stop before assessment effects unless the full review packet is independently
   signed `ACCEPT`.

## Exact identity

- state slice: `astral-trace-completeness-gemma3-end-to-end-v3`
- protocol: `astral-trace-completeness-gemma3-v3.1`
- model: `google/gemma-3-1b-pt`
- model root: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`
- asset repository: `google/gemma-scope-2-1b-pt`
- asset revision: `b738dc06961818c011fb2e44a316352ca0f4e873`
- asset variant: `transcoder_all/layer_12_width_16k_l0_small_affine`
- hidden width: `1152`
- feature width: `16384`
- custody root: `/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v3`
- operator: the local V3 runner identity recorded in the external receipt
- runner: `qualify_v3.py` after it is implemented and reviewed
- validator: `validate_v3.py` after it is implemented and reviewed
- fresh corpus: `gemma3-trace-causal-families-v3-2026-08-30`

The custody root and each subroot must be owner-only `0700`. Raw prompts,
tokens, activations, cache/state payloads, logits, and per-trial outcomes may
exist only under its raw subroot and must expire within 72 hours after
validation. Aggregate manifests and digests contain no raw values.

The first V3 pre-load receipt was superseded before model execution because
qualification source files were added after it was produced. The active review
receipt is `review/preload-review-v3-r2.json`; its source manifest covers the
complete pre-load reviewer set. The superseded receipt is historical only.

## Normalization estimand

For every eligible row `r` in the fresh fit split and every hidden coordinate
`d`, let `x[r,d]` be the model activation at
`model.layers.12.pre_feedforward_layernorm.output`, let `y[r,d]` be the model
activation at `model.layers.12.post_feedforward_layernorm.output`, and let
`f(x[r])` be the fixed affine JumpReLU transcoder reconstruction. Define one
global target mean over all rows and coordinates:

`mu = mean({ y[r,d] : all eligible rows r and all d })`

The primary metric is the pooled global-centered normalized reconstruction MSE:

`NMSE = sum_r,d((f(x[r])[d] - y[r,d])^2) / sum_r,d((y[r,d] - mu)^2)`

The gate is `NMSE <= 0.05`. Every finite row is included. Nonfinite values,
empty fit data, zero denominator, missing rows, duplicate rows, or shape
mismatches fail closed. The estimator is not a maximum over generation steps,
not a median, and not a per-row normalization.

The official `examples.safetensors` file is not used as `y`: its fixed schema
contains feature/example metadata and does not contain model target
activations. It is checked for provenance and schema only. This distinction is
part of the pre-load review.

## Causal and state contracts

The eventual interchange operator is exact module-output replacement with a
same-shape donor at a declared generation step. The operator has three
allowed qualification modes: identity/no-op, exact donor replacement, and
zero replacement. The model cache is reset between isolated trials.

The causal estimand, if assessment is ever separately opened, is the
difference in a fixed output-distribution or behavioral functional between
the assigned intervention and the no-intervention control. Assignment is
fixed by the sealed family/variant table; timing is the declared module and
generation step; consistency means the observed outcome equals the potential
outcome under the assigned exact operator; positivity requires every declared
variant to be executable; interference is excluded by cache reset and isolated
one-family runs.

Required controls remain activation-only, text-only, exact-copy/no-op,
shuffled, constant, and matched controls. Falsifiers are zero no-op delta,
shuffled-control indistinguishability, missing cache transitions, mismatched
event census, and failure of fresh held-out causal scrubbing. Predictions must
be locked before any assessment effects.

## Fixed statistical rules

- primary metric: pooled global-centered NMSE
- primary direction: lower is better
- threshold: `0.05`
- uncertainty: bootstrap over fresh family IDs, not individual tokens, with
  10,000 fixed-seed resamples and the 95% percentile interval
- missingness: any missing or invalid fit row fails; no imputation
- multiplicity: one primary asset/normalization candidate; no shopping
- repeats: two deterministic qualification repeats and one no-op/zero pair
- attrition: zero permitted after corpus sealing
- power: not applicable to the asset-only gate; assessment power must be
  independently reviewed before effects
- ICC: not claimed in qualification; assessment ICC requires a sealed
  family-cluster calculation

## Stop rules and claim ceiling

There are three allowed V3 hypotheses, each with a fresh state identity and
predeclared asset/estimand. The first candidate is the fixed affine 16k
L0-small transcoder with the estimand above. A failed candidate closes its
identity; no V2 threshold, normalization, layer, asset, or prompt may be
changed in place. A measurable breakthrough is a passing V3 pooled NMSE gate
with all trace/custody guards passing. If no candidate passes within the
three-hypothesis budget, the lane closes as `NoCandidate`.

Qualification can claim only
`LocalDevelopmentGemma3EndToEndCausalTraceQualificationV3`. Even a passing
qualification cannot claim introspection, causal self-modeling, complete
kernel observability, benchmark evidence, or production readiness.
