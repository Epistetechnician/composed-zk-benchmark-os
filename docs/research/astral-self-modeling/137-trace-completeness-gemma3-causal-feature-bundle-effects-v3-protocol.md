# Astral Gemma 3 Causal Feature-Bundle Effects V3 Protocol

State slice: `astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3`.

V2 is permanently terminal `NoCandidate`. This is a fresh theory packet. V2
scientific corpora, activations, effects, predictions, and result artifacts
are excluded as V3 inputs. Source-level adapter infrastructure may be reused
only through the separately digest-bound V3 source manifest.

## Identities and claim ceiling

| Field | V3 value |
|---|---|
| Protocol | `astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.0` |
| Model | `google/gemma-3-1b-pt`; cached BF16 checkpoint; manifest bound in packet |
| Feature asset | Gemma Scope 2 `16k/L0-big` affine at the frozen official revision; fresh V3 QC receipt |
| Corpus | `gemma3-causal-feature-bundle-effects-cross-half-v3-20260902`; seed `2026090201`; 144 families |
| Splits | 48 fit / 48 tune / 48 assessment; fit has two disjoint 24-family halves |
| Repeats | three isolated repeats per family/arm; family is the statistical unit |
| Custody | `/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-causal-feature-bundle-effects-v3`; external owner-only `0700`; raw retention at most 72 hours |
| Operator | `shaanp`; runner `tools/astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3/run_v3.py` |
| Validator | `tools/astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3/validate_v3_slice.py` |
| Provider | GiveMeANode; exact node and positive hard USD ceiling must be packet-bound before execution |
| Qualification ceiling | `LocalDevelopmentGemma3JointBundleCausalQualificationV3` |
| Assessment ceiling | `LocalDevelopmentGemma3HeldOutJointBundleCausalAssessmentV3` only if every held-out gate passes |

The packet remains non-executable until the model, runtime, asset, corpus,
source, custody, operator, runner, validator, provider allocation, node ID,
positive hard spend ceiling, and independent signed Ed25519 `ACCEPT` are all
bound. The operator cannot self-sign acceptance.

## Theory and estimand

At final position `p` of layer-12 post-feedforward activation `h`, let `z=E(h)`
and decoder `D`. The predata rule selects exactly one bundle `B={i,j,k}`.
The output metric is the target-minus-distractor logit margin.

The primary estimand is

`tau_B = E_f[m(h_{B<-0}) - m(h)]`,

where the expectation is over sealed families after averaging their three
repeats. The non-additivity estimand is

`kappa_B = tau_B - (tau_i + tau_j + tau_k)`.

Assignment is fixed-seed balanced arm order within each family, with every
family receiving every declared arm. Timing is generation step 0 after the
recipient module output and before unchanged downstream computation.
Consistency means each observed run equals the potential outcome under its
exact frozen model, tokenizer, transcoder, donor, dtype, and downstream pass.
Positivity requires every family/arm/repeat cell to be finite and present;
no imputation or selected-position exclusion is allowed. Interference is
blocked by one family per isolated run, cache reset between trials, and no
shared mutable state.

## Predata bundle selection

For each fit half, rank features by mean absolute final-position activation and
intersect the two top-16 sets. Require at least six shared features. Enumerate
all unordered triples in the intersection. For each triple compute the minimum
of its three absolute pairwise correlations separately in both halves. Select
the triple maximizing the lower of those two scores, then pooled score, then
lexicographic feature-index order. Require the selected lower-half score to be
at least `0.30`. Tune and assessment values cannot affect selection. No other
bundle size, layer, position, asset, threshold, or subspace may be searched.

## Exact operators

- Bundle ablation: `h' = h + D(z_B=0) - D(z)`.
- Singleton ablation: the same operator with exactly one bundle coordinate set to zero.
- Bundle replacement: `h' = h + D(z_{B}=z_{d,B}) - D(z)` using a fixed donor family.
- Activation patch: replace the exact-shape recipient activation with the donor activation.
- Path patch: apply the same exact bundle interchange over the frozen path from layer-12 post-feedforward output to the output distribution.
- Causal scrubbing: `h_{f<-d}=h_f+D(z_{f,B<-d,B})-D(z_f)` using a predeclared assessment donor permutation.

The locked abstraction is a fixed seven-term ridge model: intercept, three
standardized bundle coordinates, and three standardized pairwise products,
with ridge lambda `1.0`, fit once on fit-family bundle-ablation effects. The
held-out prediction is `g(z_{d,B}) - g(z_{f,B})`.

## Gates and falsifiers

Qualification requires native/instrumented parity `<=1e-4`, repeatability and
no-op/exact-copy identity `<=1e-5`, pooled reconstruction NMSE `<=0.05`, exact
event/state-transition accounting, complete donor shape/dtype, nonzero joint
effect `>1e-5`, and output-distribution TV `>=1e-3`.

Fit requires complete joint and singleton cells, two-sided bootstrap 95%
intervals excluding zero for both `tau_B` and `kappa_B`, Holm-adjusted alpha
`0.05` over those two quantities, interaction ratio `|kappa_B|/|tau_B| >=0.25`,
and simulated power `>=0.80` using 10,000 fixed-seed simulations, ICC `0.50`,
three repeats, and 48 assessment families.

Tune requires the locked family-level predictor to reach sign agreement
`>=39/48=0.8125`, `R^2>=0.25`, repeat-collapsed joint and interaction gates,
and all fixed controls. Only after this lock does assessment open.

Held-out scrubbing requires true-donor balanced accuracy `>=0.80`, shuffled
and constant donor controls `<=0.60`, repeat-collapsed joint and interaction
gates, complete controls, fresh assessment families, and no adaptive retuning.

Fixed falsifiers are failed reconstruction/parity, missing or duplicate event
or family cells, a zero joint effect, a zero/non-significant interaction, a
tune or held-out predictor failure, shuffled/constant controls approaching
the true score, or an equivalent deterministic decoy triple.

## Statistics, custody, and ordering

Uncertainty is a 10,000-resample fixed-seed percentile bootstrap over family
IDs after repeat collapse. Missingness is fail-closed. Attrition is zero after
corpus sealing: any failed family, arm, repeat, event, custody, or digest
accounting closes the slice. Raw prompts, tokens, activations, logits,
cache/state payloads, and per-trial outcomes may exist only below the external
raw root and must be deleted before final validation. Publication is aggregate
results and digests only.

Lock order is source/runtime/model/asset/corpus/custody freeze; fit bundle
selection; fit effects; tune predictor and prediction lock; independent
packet-bound `ACCEPT`; one bounded node qualification; fresh held-out
scrubbing; independent digest/event/custody validation; closure as either
`HeldOutCausalFeatureBundleAssessmentV3` or `NoCandidate`.

