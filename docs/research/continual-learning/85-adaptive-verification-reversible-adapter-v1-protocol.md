# Adaptive verification with reversible adapters v1

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v1`.

Status: `ProtocolDraft / ModelExecutionClosedPendingIndependentReview`.

## Scientific boundary

This is a separate continual-learning control-plane experiment. It does not
reopen Astral V48, consume Astral causal-target artifacts, or create evidence
for introspection, causal self-modeling, Stage 0C, Stage 1, benchmark
superiority, or production readiness.

The theory is deliberately narrower than the earlier synthetic claim:

> Given a frozen base model, a fixed reversible-adapter training budget, and a
> fresh document-disjoint corpus, a predeclared evidence score can select a
> fixed number of update windows that improve held-out language-model loss
> relative to fixed-cadence selection, without violating protected-data,
> rollback, repeatability, or compute guards.

The evidence score is a measurable controller input, not semantic truth. It is
computed from frozen-base token loss and a lexical novelty statistic. The
experiment tests whether the controller is useful, not whether it knows why a
sample is useful.

## Fixed state slice and actors

- State slice: `continual-learning-adaptive-verification-reversible-adapter-v1`.
- Model role: one predeclared cached open-weight causal decoder.
- Adapter role: reversible LoRA adapter; base weights are never changed.
- Corpus role: a new Project Gutenberg bundle with twelve book identities,
  freshly acquired into a repository-external immutable root.
- Runner role: `experiments/continual_learning/adaptive_verification_reversible_adapter_v1.py`.
- Validator role: `experiments/continual_learning/validate_adaptive_verification_reversible_adapter_v1.py`,
  executed as a separate process and not imported by the runner.
- Custody root: an external absolute path under the registered research
  artifact volume. Repository paths are invalid output roots.
- Provider role: optional GiveMeANode/H100 execution only after this protocol,
  implementation contract, and review receipt are sealed. No provider call is
  implied by this protocol.

## Model and runtime contract

The initial eligible model is the already-cached
`google/gemma-3-1b-pt` MLX BF16 conversion at:

`/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`.

The model path, every stable model-file digest, model `config.json` digest,
Python interpreter digest, MLX version, and MLX-LM version are recorded before
qualification. The expected model has 26 transformer layers and hidden size
1152. The runner sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` during
model execution. No model download, network access, base-weight update, or
adapter merge is permitted.

An H100 execution, if later used, must run the identical sealed source,
configuration, model digest, corpus digest, container digest, CUDA/driver
receipt, and command digest. Hardware changes scale preregistered repetitions
only; they cannot change the model, controller, selection budget, optimizer,
adapter rank, thresholds, or data splits.

## Fresh corpus and split identity

The corpus consists of twelve Project Gutenberg books acquired by the new
state-slice acquisition script. Each book is one document identity; source URL,
HTTP metadata, raw bytes, normalized text, and file digests are retained in an
external manifest. Existing V39--V48, Gemma, recirculation, and other prior
corpus artifacts are not inputs.

The fixed book assignment is:

- fit: Gutenberg IDs `1342, 2701, 2554, 84, 1661, 16328`;
- tune: Gutenberg IDs `11, 1727, 43`;
- assessment: Gutenberg IDs `1513, 100, 345`.

Windows are generated without crossing document boundaries. Fit, tune, and
assessment document sets are disjoint. The runner uses 512-token windows with
256-token stride, requires at least 384 tokens per retained window, and keeps
at most four windows per book. The corpus manifest and split digests are sealed
before model qualification.

## Arms and fixed selection rule

The primary comparison has exactly two arms:

1. `fixed_cadence`: select every other eligible fit window in manifest order;
2. `adaptive_verification`: score every eligible fit window with the frozen
   base model and a lexical novelty statistic, then select the top half by a
   stable descending score with document-balanced tie breaking.

Both arms select the same number of windows, use the same LoRA rank, trainable
layer count, optimizer, learning rate, batch size, update iterations, and
token budget. The fixed arm computes the same frozen-base evidence scores but
does not use them for selection, so score-computation overhead is measured and
reported separately rather than hidden.

The V3 synthetic `plasticity_guard` remains an unexecuted hypothesis. It is not
combined with adaptive verification here because its synthetic plasticity
state has no validated model-equivalent observable. No wave schedule, replay,
stochastic schedule, model shopping, or adaptive parameter search is allowed.

## Estimand and thresholds

Let `L_a(A)` be mean assessment token NLL for arm `a` after fitting adapter
`A`, and let `L_0` be the same frozen-base assessment NLL. The primary
estimand is:

`Delta_adaptive = (L_0 - L_adaptive) - (L_0 - L_fixed)`

so positive values favor adaptive selection. It is evaluated per fixed seed and
then aggregated across the preregistered seed set.

The primary result is eligible only if all conditions hold:

- mean `Delta_adaptive >= 0.020` NLL per token;
- the 95% paired bootstrap lower bound across document-level assessment units
  is at least `0.000`;
- adaptive wins on at least 5 of 6 preregistered paired seed/order cases;
- no arm has assessment NLL more than 5% worse than its frozen-base baseline;
- protected fit-window loss change is no worse than +5% for either arm;
- exact adapter save/restore error is at most `1e-6` in the recorded probe;
- all equal-compute, custody, split, and validator gates pass.

The effect threshold is deliberately substantive. A positive but subthreshold
effect is `DevelopmentNoCandidate`, not a near-miss to be retuned.

## Uncertainty, missingness, and multiplicity

The unit of aggregation is the document, not the token or training row.
Assessment scores are paired by document, seed, and arm. The validator computes
10,000 deterministic bootstrap resamples using seed `20260828`, percentile
intervals, and the predeclared lower-bound rule above. Missing document scores,
non-finite losses, failed adapter loads, or failed case subprocesses are not
imputed; the case is invalid and the slice stops.

There is one primary comparison. Tune data may select no parameter: it is used
only to verify score computation, repeatability, and the frozen configuration.
No layer, rank, optimizer, learning rate, selection fraction, score weight,
model, corpus, or threshold may be selected after observing assessment data.
Secondary guard statistics are descriptive and cannot rescue a failed primary
gate. The fixed two-arm comparison receives the sole confirmatory alpha rule:
paired bootstrap lower bound at zero; no unregistered subgroup claims are
permitted.

## Controls and falsifiers

Qualification and assessment retain aggregate-only results for these controls:

- frozen base/no adapter;
- `fixed_cadence` adapter;
- `adaptive_verification` adapter;
- shuffled-score selection using a seed-bound permutation;
- constant-score selection using the same selection budget;
- matched-energy control with identical selected-window count and token count;
- text-only novelty score without frozen-model loss;
- score-only selection without lexical novelty.

The shuffled and constant arms falsify the claim that any deterministic
selection rule is sufficient. The text-only and score-only arms decompose the
controller. The matched-energy control prevents token-count or selected-text
length from explaining the effect. If adaptive selection wins only against the
base model but not fixed cadence, the result is not controller evidence.

## Prediction locking and retention

All fit and tune selection decisions, score vectors, selected window IDs,
command arrays, and guard predictions are serialized and digested before any
assessment adapter is loaded or assessment loss is computed. The lock records
`assessment_started: false`; the assessment runner refuses to proceed unless
the lock digest and sealed configuration digest match.

Raw prompts, token IDs, activations, logits, adapter tensors, and training logs
are retained only in the external custody root for the minimum validation
interval and are not copied into the repository or reports. Repository-visible
records contain digests, aggregate metrics, gate booleans, and the narrow
classification. The independent validator reads aggregate result files and
manifests only.

## Qualification gates

Qualification runs before fit or assessment and stops on the first failure:

1. model, runtime, source, command, and corpus digests are complete;
2. native model reload parity is within `1e-5` maximum absolute logit delta;
3. repeated frozen-base NLL is identical within `1e-8`;
4. empty/no-op adapter loading preserves native NLL within `1e-5`;
5. LoRA adapter save/restore is exact within `1e-6` on the probe;
6. adapter tensor shapes and declared layer count match the model;
7. a two-iteration qualification adapter produces a finite, nonzero change
   in probe logits or NLL;
8. external output root safety and independent validator preflight pass.

No adaptive repair is permitted. A failed qualification is classified
`InstrumentFeasibilityFailure` and closes this slice.

## Power and reliability plan

The fixed campaign is six paired cases: three training seeds crossed with two
fixed document orders. Each case has at least three fit books, three tune
books, and three assessment books represented in the aggregate panel. The
protocol was designed to detect the preregistered 0.020 NLL effect at the
document level; no claim of formal power is made until the sealed pilot
simulation and reliability report confirm the bootstrap lower-bound behavior.

Before assessment, a qualification simulation with 10,000 deterministic
resamples must show at least 0.80 rejection probability for a synthetic effect
of `0.020` and at most 0.05 rejection probability under a zero effect. If this
calibration fails, the slice stops before model assessment; the threshold is
not changed.

## Review and implementation authorization

Independent review must verify this protocol, the implementation contract,
source/runtime/model custody, fresh corpus identity, controls, prediction-lock
ordering, retention boundary, power/reliability plan, validator independence,
and claim ceiling. The reviewer must record `ACCEPT` or `REJECT`. `ACCEPT`
permits implementation-contract sealing only; it does not by itself authorize
model loading or H100 provisioning.

After acceptance, a separate implementation authorization must bind the actor,
runtime, access operator, corpus root, runner, validator, custody root, output
root, and claim ceiling. Only then may qualification run. Assessment requires a
second independent review of the configuration digest and event ordering.

## Result classification and terminal rules

Possible classifications are:

- `InstrumentFeasibility`: all qualification gates pass, no scientific
  assessment result is opened;
- `DevelopmentNoCandidate`: assessment executes but the primary or hard gates
  fail;
- `BoundedAdaptiveVerificationResult`: all primary, uncertainty, control,
  custody, and validator gates pass.

Even the final classification is bounded to
`LocalDevelopmentAdaptiveVerificationReversibleAdapterV1`. It does not
establish general continual learning, transformer-wide transfer, causal
verification, cryptographic proof validity, Astral evidence, introspection,
causal self-modeling, Stage 0C, Stage 1, benchmark evidence, or production
readiness.

Any custody, parity, repeatability, no-op, adapter-shape, nonzero-reach,
split, lock, missingness, or validator failure closes the slice without
retuning. V48 and V82 remain separate and unchanged.
