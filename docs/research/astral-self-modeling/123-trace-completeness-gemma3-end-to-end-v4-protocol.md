# Gemma 3 end-to-end trace completeness V4 protocol

State slice: `astral-trace-completeness-gemma3-end-to-end-v4`

Date: 2026-08-30

V4 is hypothesis 2 in a fresh state slice. V3's corpus, activations, logits,
effects, predictions, and result artifacts are excluded inputs. Source-level
capture infrastructure may be reused only through the V4 adapter and the
explicitly digested V2 implementation dependencies.

## Exact identity and claim ceiling

- protocol: `astral-trace-completeness-gemma3-v4.1`
- qualification ceiling: `LocalDevelopmentGemma3EndToEndCausalTraceQualificationV4`
- assessment ceiling, only after a new review and signed receipt:
  `LocalDevelopmentGemma3HeldOutCausalTraceAssessmentV4`
- model: `google/gemma-3-1b-pt`
- model root: `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`
- model manifest SHA-256:
  `5cc36128b456997e582a990ac2ce59d7fe43d925317a6e1dae48a3284895eb81`
- feature asset: `google/gemma-scope-2-1b-pt`
- asset revision: `b738dc06961818c011fb2e44a316352ca0f4e873`
- asset variant: `transcoder_all/layer_12_width_16k_l0_big_affine`
- hidden width: `1152`
- feature width: `16384`
- operator: `shaanp` on host `Shaans-MacBook-Pro`, UID `501`
- runner: `tools/astral-trace-completeness-v4/qualify_v4.py`
- validator: `tools/astral-trace-completeness-v4/validate_v4.py`, with
  independent replay in `reconcile_v4.py`
- custody root:
  `/Users/shaanp/Documents/astral-custody/trace-completeness-gemma3-end-to-end-v4`
- raw custody mode/owner: owner-only `0700`, UID `501`

The recorded V4 qualification result is the only claimable result under this
ceiling. It does not establish introspection, causal self-modeling, complete
kernel observability, consciousness, benchmark evidence, production
readiness, or provider evidence.

## Ordered authorization boundary

The fixed order is asset acquisition, asset QC, independent pre-load review,
offline model loading, fresh qualification, independent replay, raw expiry,
and aggregate-only reporting. Network access was limited to acquisition of the
fixed upstream asset. Model execution ran with Hugging Face offline flags.

The pre-load receipt is
`review/preload-review-v4.json`, SHA-256
`e57bc1cd62f23ac66d31442a35cb464f59a72d632324ca7fb5845f3039cddf99`.
It is a static validator receipt with status
`PRELOAD_ACCEPTED_STATIC_VALIDATOR`; it has
`signed_assessment_acceptance: false`, `model_execution: false`, and
`assessment_opened: false`. It does not authorize assessment.

## Fresh corpus and custody

The corpus is `gemma3-trace-causal-families-v4-2026-08-30`, seed `2026083004`,
manifest SHA-256
`3aaa574eb6189ad15f198ed3af51a70f552c25bd31c1c8e3b8b918c0ae7a79e0`. It has
48 deterministic families: 16 fit, 16 tune, and 16 assessment. Only fit
families were executed. No fit-row attrition was permitted.

Raw prompts, tokens, activations, logits, cache/state payloads, and per-trial
outcomes existed only under the external raw root. Raw retention was at most
72 hours. The reconciliation passed and the deletion receipt records exactly
35 deleted raw event/capture files with `raw_root_empty: true`. Aggregate
manifests, validator receipts, asset digests, and qualification digests remain.

## Executable causal abstraction and interchange operator

For a frozen model `M`, generation step `t`, module path `p`, and same-shape
donor `d`, the operator is:

`I(M, p, t, d): h_p(t) := d` followed by the unchanged downstream forward
pass, cache update, output distribution, and greedy sample. The executable
qualification object is `InterventionPlan(module_path, step, mode, donor)`.
The fixed paths are registered model module paths; V4 tested `noop` and `zero`
at `model.layers.12.post_feedforward_layernorm`, step `0`. Replacement requires
exact recipient shape and recipient dtype. The implementation provenance is
the frozen V2 `torch_adapter_v2.py`, bound under the V4 adapter and dependency
digests; every emitted event is V4-bound.

The qualification operator is a trace/instrument integrity test, not a claim
that a causal graph has been validated. Graph construction, causal scrubbing,
held-out intervention prediction, and assessment were not opened.

## Reconstruction estimand and assumptions

For every eligible fit row `r` and hidden coordinate `d`, `x[r,d]` is the
activation at `model.layers.12.pre_feedforward_layernorm.output`, `y[r,d]` is
the activation at `model.layers.12.post_feedforward_layernorm.output`, and
`f(x[r])` is the fixed L0-big affine JumpReLU reconstruction. With one mean
over every target coordinate in the fresh fit split:

`mu = mean({y[r,d] : all eligible fit rows r and all d})`

`NMSE = sum_r,d((f(x[r])[d] - y[r,d])^2) / sum_r,d((y[r,d] - mu)^2)`

Assumptions are fixed as follows:

- assignment: fixed official L0-big asset and every eligible fresh fit row;
- timing: asset gate before effects, then activation capture and reconstruction
  during qualification;
- consistency: the observed trace/output is the potential result under the
  assigned frozen module boundary, dtype conversion, and operator;
- positivity: every finite sealed fit row must execute and contribute;
- interference: each family runs in isolation with cache reset between trials.

The fixed quality threshold is NMSE `<=0.05`. Feature repeat stability must be
cosine `>=0.90`; native/instrumented, repeat, and no-op logit deltas must be
`<=1e-4`, `<=1e-5`, and `<=1e-5` respectively; zero replacement must have a
logit delta `>1e-5`; event replay must pass exactly.

The uncertainty rule reserved for a separately opened assessment is 10,000
fixed-seed bootstrap resamples over family IDs with a 95% percentile interval.
Missingness is fail-closed with no imputation. Multiplicity is one predeclared
asset/normalization candidate per fresh slice. Qualification repeats are one
fresh fit repeat plus fixed no-op and zero controls; assessment repeats, power,
and ICC require a separately reviewed design. Attrition is zero after corpus
sealing.

Fixed controls and falsifiers are activation-only, text-only, exact-copy/no-op,
shuffled, constant, and matched controls; zero no-op delta, missing cache
transitions, malformed event census, and held-out scrubbing failure falsify the
corresponding causal trace claim. No assessment effect was measured.

## Source and runtime digests

The qualification source manifest SHA-256 is
`613b666cecf48cfec443b09e9a48fb1add89892b40be8681b8f85cb95500f673`.
It includes every V4 loader, contract, custody, validator, review,
qualification, reconciliation, and expiry source file. V2 implementation
dependency digests are explicitly included:

- `protocol_v2.py`:
  `6aac765cf490cedb5febf8c0bc9c4036670130cf870710a829ccadefddce3e35`
- `registry_v2.py`:
  `2967fdc40702d22b15c03ce7138fe3348151c7aff64ddb7e2af199b001364d49`
- `torch_adapter_v2.py`:
  `e8052bb66903b7c3ac3f3d19b4c642cba16a9b6767f0b2cc44f1ee9a45e38559`
- `validate_v2.py`:
  `ecf2f19550090c0220aa4e508ea14976f940c88e504d92c2b27c2c596451f22b`

Runtime manifest SHA-256 is
`104c32975db6f7a80937fee9725312207527d194636be0059b110e70208c0aa0`:
Python `3.14.5`; Torch `2.12.0`; Transformers `4.57.3`; NNsight `0.6.1`;
circuit-tracer `0.5.3.dev1+g6018ed8d3`; TransformerLens `3.2.1`; and
Safetensors `0.7.0`.

Asset QC SHA-256 is
`a19f47ff2d36db1591476ae1c8b3a645b282b781df2e4303fc097cf413510abb`.

## Review boundary

The static pre-load review is not the requested independent assessment review.
No genuinely independent packet-bound signed `ACCEPT` receipt exists for V4.
Therefore assessment effects, causal graph claims, prediction locking for
assessment, and any broader scientific conclusion remain closed.
