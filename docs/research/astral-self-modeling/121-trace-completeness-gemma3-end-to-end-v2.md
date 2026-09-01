# Gemma 3 end-to-end trace completeness V2

State slice: `astral-trace-completeness-gemma3-end-to-end-v2`

Date: 2026-08-30

Qualification ceiling:
`LocalDevelopmentGemma3EndToEndCausalTraceQualification`

Maximum separately reviewed assessment ceiling:
`LocalDevelopmentGemma3HeldOutCausalTraceAssessment`

Initial disposition: `AUTHORIZED_FOR_QUALIFICATION_ASSESSMENT_SEALED`

## Authorization and separation

The user's 2026-08-30 authorization opens a new execution identity rather than
reopening Astral V48. It permits the exact cached Gemma 3 1B PT model to be
loaded through frozen local runtimes, permits acquisition and loading of the
model-matched Gemma Scope 2 feature assets, and permits the full qualification
and preassessment path described below. Model execution is offline after asset
acquisition.

Assessment effects remain sealed until a genuinely independent reviewer signs
an `ACCEPT` receipt bound to the final review-packet digest. The operator,
runner author, and validator author may not create or countersign that receipt.
An unsigned review, a fixture pass, or an operator-generated key cannot open
assessment.

## Frozen execution target

- model: `google/gemma-3-1b-pt`
- local model root:
  `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`
- architecture: `Gemma3ForCausalLM`
- layers: `26`
- hidden width: `1152`
- model dtype: `bfloat16`
- model weights must remain byte-identical
- native control: uninstrumented PyTorch/Transformers forward using the local
  safetensors and tokenizer only
- instrumented path: NNsight-backed PyTorch/Transformers execution with an
  independently enumerated model-module registry
- cross-runtime control: locked MLX `0.31.2` / MLX-LM `0.31.3`; cross-runtime
  differences are reported and cannot be relabeled as native parity
- feature assets: exact `google/gemma-scope-2-1b-pt` SAEs/transcoders or the
  circuit-tracer-compatible Gemma Scope 2 1B PT release, frozen by repository,
  revision, file manifest, and SHA-256
- circuit implementation: frozen `decoderesearch/circuit-tracer` revision,
  NNsight backend

No Qwen, Gemma instruction-tuned, Gemma 2, or differently quantized actor may
substitute for this identity.

## Required synchronized chain

Every run is bound by immutable `trial_id`, `run_id`, `prompt_family_id`, split,
repeat, model digest, runtime digest, registry digest, asset digest, and
prediction-lock digest. Typed events must account for:

1. input token and generation step;
2. embedding output;
3. every declared normalization, attention Q/K/V projection, Q/K norm,
   attention score/pattern, attention head/output projection, residual
   boundary, MLP gate/up/down projection, MLP activation, final normalization,
   unembedding input, and output logits;
4. every cache allocation, read, append/write, trim, and version transition;
5. RNG state digest, sampling parameters, sampled-token digest, and stop event;
6. exact intervention assignment, donor/recipient state digests, boundary,
   timing, and operator digest;
7. SAE/transcoder feature activations, reconstruction digest, reconstruction
   error, ablation assignment, and feature-to-logit effect;
8. graph node/edge identities, predicted signs/effects, patch/scrub assignment,
   and realized output-distribution changes;
9. generated-output digest, calibration score, task score, behavioral outcome,
   and aggregate custody/validation receipts.

Compiler-fused kernels, allocator state, and device-driver internals are outside
the observable claim. Registry completeness means complete coverage of the
frozen native Python module and declared cache API boundaries, not omniscient
hardware tracing.

## Fresh corpus and splits

Corpus identity:
`gemma3-trace-causal-families-v2-2026-08-30`.

The generator must create 48 deterministic prompt families without using prior
Astral prompts or outcomes. Families are assigned before effects using seed
`20260830` to document-disjoint `fit=16`, `tune=16`, and `assessment=16`
partitions. Each family contains clean, corrupted, exact-copy/no-op, shuffled,
constant, matched-norm, activation-only, text-only, and access-null variants.
The raw prompt manifest and trial rows remain external; the repository retains
only generator source, family-level split digests, aggregate statistics, and
receipts.

## Estimand and fixed analysis

Primary estimand: the document-family-clustered average change in the locked
target-token logit margin caused by the preregistered feature/path intervention
relative to its paired no-op control on held-out assessment families.

- assignment: deterministic counterbalanced assignment by family and repeat,
  seed `20260830`, fixed before any assessment effect;
- timing: intervention is applied after the declared producer and before its
  declared downstream consumer in the same generation step;
- consistency: observed treatment uses the exact frozen operator, feature
  asset, boundary, donor, and recipient encoded by the assigned trial;
- positivity: every tested boundary has no-op, exact-copy, shuffled, constant,
  matched-norm, activation-only, text-only, and access-null support;
- interference: mutable cache and RNG state are isolated by run; no run shares
  state, and within-run cache transitions are part of the observed path.

Uncertainty is a two-sided 95% cluster bootstrap over prompt families with
10,000 resamples and seed `20260830`. Multiplicity uses Holm correction across
the frozen feature and graph-edge family at `alpha=0.05`. Power target is 0.90
for standardized effect 0.35 under ICC sensitivities 0.10 and 0.30. Two exact
repeats are required. Instrument missingness, duplication, unaccounted state
transition, and output missingness must each equal zero. Scientific attrition
is capped at 5%, with no imputation; exceeding it invalidates assessment.

## Qualification gates

- native-versus-instrumented maximum absolute logit delta `<=1e-4`;
- deterministic repeat maximum absolute logit delta `<=1e-5`;
- no-op identity maximum absolute logit delta `<=1e-5`;
- cross-runtime MLX-versus-PyTorch delta is reported but is not a parity gate;
- required-event missingness and duplication `=0`;
- unaccounted cache/state transitions `=0`;
- sampled-token and behavioral-outcome linkage missingness `=0`;
- SAE normalized reconstruction MSE `<=0.05`;
- feature stability cosine across repeats `>=0.90`;
- feature-ablation sign agreement `>=0.80`;
- feature-to-logit sign agreement `>=0.80`;
- held-out causal-scrub balanced accuracy `>=0.80`;
- scrub margin over shuffled control `>=0.10`.

Any failed qualification gate stops the affected lane. Thresholds, assets,
features, layers, graph edges, prompts, or controls may not be changed after
the associated effect is observed under this identity.

## Custody

Custody root:
`/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v2`.

The root and `raw`, `aggregate`, `assets`, `review`, and `receipts` subroots
must be owner-only `0700`, repository-external, nonsymlink paths. Raw prompts,
tokens, activations, logits, cache/state payloads, graphs containing raw text,
and per-trial outcomes expire no later than 72 hours after independent
validation. Assets may remain under the external asset root because their
immutable upstream identities are public; they are never committed here.
Only aggregate results, source/asset/model/runtime digests, expiry receipts,
and independent validator receipts may be retained in the repository.

## Ordered execution gates

1. Freeze code, model, runtimes, module/cache registry, corpus generator,
   custody identity, asset revisions, estimand, controls, thresholds, and
   retention policy.
2. Qualify uninstrumented/instrumented parity, repeatability, no-op identity,
   event completeness, and state accounting.
3. Validate SAE/transcoder reconstruction, stability, ablation, and
   feature-to-logit effects on fit/tune only.
4. Freeze graph nodes/edges and predicted intervention effects in a
   packet-digest-bound prediction lock.
5. Obtain an independent reviewer identity, public signing-key identity, and
   signed `ACCEPT` receipt covering the exact frozen packet.
6. Only after step 5, execute held-out assessment and causal scrubbing.
7. Independently validate aggregates, delete expired raw traces, publish
   digests and the exact achieved ceiling, and close the slice without adaptive
   retry if a gate fails.

## Claim exclusions

This slice cannot establish complete accelerator-kernel tracing,
introspection, self-modeling, consciousness, general circuit recovery,
benchmark validity, Stage 0C/1 promotion, production readiness, or any result
for Qwen3.6, Nemotron-H, prior Astral runs, or models other than the exact actor
above.

## Qualification execution result

Campaign: `29c2eb957a79419995992533d3b843a7`

Disposition: `QualificationFailedSAEReconstruction`

Qualification digest:
`9100fd0296376f9226169968834453d76a7cf3232dd6832acb601c824c448932`

Frozen identities:

- model manifest:
  `5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81`
- runtime manifest:
  `104c32975db6f7a80937fee9725312207527d194636be0059b110e70208c0aa0`
- Gemma Scope 2 asset manifest:
  `676956ae3a28ff542708c3bb71f49ebe5a9783f14de315b9468575b2322eaae9`
- fresh corpus manifest:
  `0572b1e6797ff2b4d3e85f1fd0216fe300df8d55b293d51adae74a13bad129a4`
- native module registry:
  `db08792456921d79dff66d4d3b115c74e3e038b89a8dd31385130c5d1ebe27c8`

The offline run produced four independently replayed two-step event streams:
repeat A, repeat B, exact no-op, and zero replacement. Raw event streams and
selected feature-boundary captures are owner-only `0600` files below the
external `0700` custody root. No raw values were published to the repository.

| Gate | Result | Status |
|---|---:|---|
| native/instrumented max logit delta | `0.0` | pass |
| deterministic repeat max logit delta | `0.0` | pass |
| exact no-op max logit delta | `0.0` | pass |
| zero-replacement max logit delta | `3.8212890625` | pass: nonzero reach |
| exact event replay | four of four valid | pass |
| feature repeat cosine | `1.0` | pass |
| SAE/transcoder normalized reconstruction MSE | `0.3353789150714874` | **fail**, required `<=0.05` |

The repeated SAE measurements were byte-stable. Prefill normalized MSE was
`0.06334932148456573`; the first cached generation-step normalized MSE was
`0.3353789150714874`. The official Gemma Scope 2 layer-12 config binds input to
`model.layers.12.pre_feedforward_layernorm.output` and output to
`model.layers.12.post_feedforward_layernorm.output`; the execution used those
exact boundaries and the circuit-tracer Gemma Scope 2 loader.

Because the reconstruction gate failed, ordered execution stopped before
feature ablation, feature-to-logit assessment, causal graph construction,
prediction locking, independent review, causal scrubbing, or held-out
assessment. `assessment_opened=false`. No signed `ACCEPT` receipt exists.
Changing the normalization denominator, threshold, layer, asset sparsity, or
prompt after seeing this result is prohibited under V2.

A no-model custody reconciliation subsequently replayed all four retained raw
event streams, recomputed each original run-aggregate hash, reconstructed the
two capture manifests, and persisted event-manifest and validator-receipt bytes
under the external `aggregate` and `receipts` roots. Reconciliation R2 binds
the preserved qualification source, current verifier dependencies, and exact
persisted receipt-file hashes. Its digest is
`e95c643bfc4608d19f53b01da9fce162f878eeb638f09ccefd27c28c9112ad98`;
it supersedes the first reconciliation digest
`24f6bab21b9749369061b7366a196e081a6e32b2631974ba098a187f3b991db8`.
This repairs later replayability; it does not change the failed qualification,
open assessment, or constitute independent signed review.

After reconciliation R2, the targeted expiry runner verified the six retained
raw event/capture files against their manifests, recorded a deletion intent,
deleted only those files, verified the raw root was empty, and recorded an
irreversible completion receipt. Completion digest:
`0f33f7642be6acd879fd104f5e2ba381bbb0495cd74465058eba4206b10ed088`.
Aggregate results, public feature assets, manifests, and validator receipts
remain external; raw prompts, events, activations, logits, and per-trial values
do not.
