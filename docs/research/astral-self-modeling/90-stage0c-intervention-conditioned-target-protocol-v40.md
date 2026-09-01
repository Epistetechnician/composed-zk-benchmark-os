# Astral Stage 0C Intervention-Conditioned Target Protocol V40

State slice: `astral-stage0c-qwen36-intervention-conditioned-target-v40`.

Status: `Authorized / DevelopmentNoCandidate / AssessmentNotOpened`.

This document lays out a fresh protocol after V39 ended at
`DevelopmentNoCandidate`. V40 execution is authorized only within the named
state slice and the custody rules below. Qualification and fit/tune
preassessment are complete; the fixed tune utility gate failed, so assessment
was never opened.

## 1. Design decision

V39 established a usable Qwen3.6 layer-replacement seam and then failed its
narrow utility gate: the locked activation-only estimator did not beat the
constant baseline on tune or assessment. V39 retained no per-family effects,
so the failure cannot be decomposed into family-level causes. The only valid
next move is a new protocol that tests one materially different hypothesis
with a stronger design.

V40 tests this hypothesis:

> A predictor that is conditioned on both sides of the planned activation
> replacement, and on fixed geometric summaries of their difference, can
> predict direct intervention effects better than a constant, text-only,
> shuffled, and clean-activation-only control.

The intervention target remains externally measured, but the observer input is
changed from V39's fixed 64-scalar activation-difference sketch to a fixed,
intervention-conditioned representation. This is not a claim that the new
representation is a mechanism. It is a preregistered test of target
predictability.

## 2. Non-reuse and separation

V40 may cite V39's aggregate failure as design rationale only. It must not
consume or transform any V39 model manifest, panel, concept registry, split
manifest, feature matrix, prediction, effect, lock, review receipt, or result
file as scientific input.

The V39 model checkpoint may be re-custodied as the same frozen Qwen3.6
checkpoint only if its complete manifest, runtime, and source digests are
recomputed into a new V40 external root. An identical model digest is custody
information, not reused scientific evidence. A missing or changed digest is a
stop condition.

V25, V28-V29, V30-V37, V61, and V82 remain separate. V40 shares no actors,
concepts, prompts, effects, predictions, or evidence with those lanes.

## 3. Claim ceiling and authorization boundary

The proposal has no scientific claim. A future executed run may classify only
as one of:

- `InstrumentFeasibility`: qualification passed and assessment remains closed;
- `TargetDegenerateNoCandidate`: the fixed target panel is non-degenerate only
  below the preregistered target floor or fails a finite-census gate;
- `DevelopmentNoCandidate`: the complete locked panel fails the utility,
  control, calibration, or validation gate;
- `BoundedTargetValidity`: every target-validity and control gate passes under
  independent validation.

Only the last classification would produce the local ceiling
`LocalDevelopmentStage0CQwen36CausalTargetValidity`. It would be an input to
the existing Stage 0C gate, not Stage 0C itself. No V40 result establishes
introspection, causal self-modeling, consciousness, benchmark superiority,
Stage 1, production readiness, or general mechanistic understanding.

Assessment is not permitted until an external custody packet exists and an
independent reviewer accepts the sealed configuration before assessment.

## 4. Fresh data design

The external corpus must contain 18 new Project Gutenberg documents, six per
split, with 144 total concept families, 48 per split:

| split | documents | families | families per document |
|---|---:|---:|---:|
| fit | 6 | 48 | 8 |
| tune | 6 | 48 | 8 |
| assessment | 6 | 48 | 8 |

The selection manifest must enforce all of the following before panel
construction:

- no Gutenberg ID used by V39 or any prior Astral experiment;
- no anthology, collected-works, or contained-work overlap across documents;
- no author appears in more than one split;
- no source document appears in more than one split;
- English language, public-domain status, canonical plain-text custody, and
  reproducible Project Gutenberg boundary markers;
- no exact or normalized 12-gram overlap between selected family excerpts
  across splits;
- deterministic family construction from a digest-bound selection manifest;
- no outcome-dependent family filtering, target-effect filtering, or
  post-hoc document removal.

Both ordinary and counterfactual prompts are deterministically padded to the
fixed Qwen tokenizer length `320` before the response instruction. This makes
the exact-length donor requirement mechanically satisfiable without changing
the selected source excerpt, target word, distractor word, or split.

The validator must retain source-byte, metadata, selection, split, author, and
overlap digests. Raw source text may remain only in the repository-external
immutable corpus root. The V40 result root must not contain raw prompts or
source excerpts.

Each family has one ordinary/counterfactual prompt pair, fixed response
labels, fixed response-token positions, a source document identifier, a family
identifier, and a predeclared paired replacement direction. The prompt format
must be semantically neutral and must not ask for mental-state reports,
introspection, consciousness, or identity claims.

## 5. Actor, target, and intervention

The actor is the exactly re-custodied `Qwen3.6-35B-A3B-MLX-4bit` checkpoint
under an external V40 model root. Qualification must recheck the loaded
architecture, all model-file digests, Python version, `mlx==0.31.2`,
`mlx-lm==0.31.3`, and the installed Qwen source digests. Network access,
training, adapter updates, and weight changes are forbidden.

The primary target is a signed correct-minus-incorrect response-logit margin
effect at layer 19:

```text
effect_i = 0.5 * [
  margin(ordinary_i, do(layer_19_final := counterfactual_i_final))
  - margin(ordinary_i, clean)
  + margin(counterfactual_i, do(layer_19_final := ordinary_i_final))
  - margin(counterfactual_i, clean)
]
```

This remains a direct actor measurement. It is never inferred from a report,
feature name, or observer prediction.

For every target family, V40 also measures a negative-control effect by
replacing the final layer-19 activation with an unrelated donor from a
different document in the same split. The donor must have the same tokenized
sequence length and response position. Its activation norm must be matched
within a fixed tolerance declared in the protocol. If an exact-length donor
cannot be found, the family is a protocol failure; the matcher may not relax
its rule after seeing effects.

The target and matched-control donor maps are fixed by the sealed family
registry and may not be used for tuning, estimator selection, or assessment
prediction construction.

## 6. Instrument qualification gates

Qualification runs before any scientific corpus feature or effect is
materialized. It uses two new neutral prompts and a separate external output
root. It must pass all gates below:

1. Native versus unmodified wrapper parity: maximum absolute logit delta at
   most `1e-4`.
2. Deterministic repeated wrapped execution: maximum absolute logit delta at
   most `1e-5`.
3. Zero/no-op replacement at layers 12, 19, and 26: maximum absolute logit
   delta at most `1e-5` for each layer.
4. Nonzero final-position replacement at layers 12, 19, and 26 reaches logits
   above `1e-6` for each layer.
5. Source and donor captures have identical token alignment, batch shape,
   sequence shape, and hidden width `2048`.
6. The actor exposes exactly 40 text layers and the replacement preserves the
   captured shape.
7. The pair-capture path is deterministic for both ordinary and
   counterfactual inputs.
8. Model, runtime, installed-source, protocol, and runner digests recompute
   independently and bind the qualification receipt.

Any failed gate stops V40. Qualification can produce only
`InstrumentFeasibility`; it cannot open assessment.

## 7. Intervention-conditioned activation representation

The primary observer receives no text features and no measured effect labels.
For each paired family it receives the clean ordinary activation `u`, the
clean counterfactual activation `v`, and a fixed transform of their geometry:

```text
z = [u, v, u - v, abs(u - v), ||u||, ||v||, ||u-v||, cosine(u,v)]
```

The vectors are converted to a fixed 256-scalar representation by a
protocol-hash-derived sign-and-bucket sketch. The sketch, bucket map, signs,
feature ordering, and scalar normalization are all pure-data functions of the
V40 protocol digest and are sealed before fit. No learned embedding, PCA,
feature search, target-derived transform, or assessment-derived normalization
is allowed.

The primary estimator is one ordinary ridge regressor over the fixed
256-scalar representation. Candidate alphas are exactly
`{1e-4, 1e-3, 1e-2, 1e-1}`; standardization is fit-only and alpha selection is
tune-only. The primary estimator is called `pair_conditioned_activation`.

The following controls are mandatory:

- `clean_activation_only`: a fixed 256-scalar sketch of `u` and `v` without
  pair geometry or intervention-difference blocks;
- `text_only`: a fixed 256-scalar hash sketch of the ordinary and
  counterfactual prompt pair, with no activations;
- `shuffled`: the primary activation representation with a protocol-derived
  row permutation within each split;
- `constant`: the fit-fold target mean;
- `matched`: the direct unrelated-donor effect distribution, never a tuning
  panel and never treated as a learned target.

The text-only and clean-activation controls are capacity-matched by feature
width and the same ridge candidate set. All transforms are deterministic and
source-bound. The model class is not expanded after observing tune results.

## 8. Fit, tune, lock, and assessment order

The execution order is immutable:

1. Recompute V40 model, runtime, source, corpus, author, split, registry, and
   qualification digests.
2. Validate all 18 documents, 144 families, author-disjoint splits, contained-
   work exclusions, and cross-split overlap scans.
3. Measure fit features and direct target/matched effects.
4. Fit only the declared estimators and select alpha only from tune error.
5. Measure tune features and effects; compute tune-only summaries.
6. Materialize assessment predictions in memory from the fit/tune-fitted
   estimator states, then create a digest-bound prediction lock containing only
   those serialized fit-only states and the assessment family order. The lock
   must state that assessment effects are absent; per-family predictions are
   not retained.
7. Obtain an independent review of custody, freshness, target definition,
   controls, donor matching, privacy retention, prediction lock, validator
   behavior, and claim ceiling.
8. Only after review acceptance, measure assessment target and matched-control
   effects.
9. Join the locked predictions with assessment effects in memory and retain
   only aggregate results.
10. Run the independent validator and finalize the narrow classification.

An assessment effect file, raw activation, token array, prompt, logit vector,
trace, or per-family target record present before the prediction lock is a
fail-closed protocol violation.

## 9. Primary success gate

The single primary metric is the paired assessment RMSE difference:

```text
delta_rmse = RMSE(pair_conditioned_activation)
             - RMSE(constant)
```

The target-validity gate passes only if all of these conditions hold:

- `delta_rmse <= -0.01` on tune and assessment;
- the assessment paired cluster-bootstrap 95% upper bound for `delta_rmse`
  is below `-0.005`, with six document clusters and a fixed bootstrap seed;
- paired activation assessment RMSE beats `clean_activation_only` and
  `shuffled` by at least `0.005`;
- the text-only control does not beat the paired activation estimator;
- the matched-control mean remains within the preregistered negative-control
  envelope `abs(mean) <= 0.25` and its donor census has zero matching
  violations;
- assessment target standard deviation is at least `0.05` and every split has
  the declared family/document census;
- all output, digest, retention, and validator gates pass.

The thresholds are fixed before fit measurement. No threshold, family, alpha,
layer, donor, or control may be chosen after assessment effects are visible.

Only aggregate per-document counts and squared-error sums may be retained for
uncertainty calculation. These sufficient statistics permit independent
recomputation of RMSE and the fixed document-cluster bootstrap without
retaining raw per-family effects, prompts, or predictions.

## 10. Retention and independent validation

The external V40 result bundle may contain only:

- model, runtime, source, corpus, author, panel, qualification, and split
  digests;
- fit/tune estimator summaries and selected alpha;
- serialized fit-only estimator states and assessment family-order binding;
- assessment prediction-lock digest;
- aggregate target and matched-control summaries;
- aggregate per-document counts and squared-error sums;
- fixed-seed uncertainty summaries;
- validator receipts and final classification.

It may not contain raw prompts, source excerpts, token arrays, activations,
logits, traces, reasoning text, credentials, PII, per-family effects, or
per-family predictions. The validator must reject unknown files, stale or
recomputed-digest mismatches, missing source custody, split overlap, pre-lock
assessment effects, changed controls, changed feature maps, changed alpha
sets, and elevated claim ceilings.

The reviewer and validator must be independent of the process that generated
the assessment effects. A user-attested review may satisfy an explicit local
workflow precondition only if the receipt records that limitation; it is not
equivalent to independent scientific replication.

## 11. End-to-end stop rules

V40 stops immediately on any of the following:

- model, runtime, source, corpus, author, or split custody mismatch;
- any V39 or prior-lane artifact consumed as scientific input;
- missing or malformed family metadata, overlap, anthology, or author leak;
- parity, repeatability, shape, or intervention-reach failure;
- exact-length/norm-matched donor unavailable;
- any assessment effect or raw assessment artifact before prediction lock;
- review absent, late, self-issued, or inconsistent with the lock;
- output census or aggregate-only retention failure;
- utility, target non-degeneracy, control, uncertainty, or validator failure.

The disposition is then `InstrumentFeasibility`,
`TargetDegenerateNoCandidate`, or `DevelopmentNoCandidate` as appropriate.
There is no adaptive retry inside V40.

## 12. Required artifacts before assessment authorization

Before assessment authorization, the executed V40 slice requires:

1. a separately approved V40 state-slice authorization;
2. a new 18-document selection manifest with author-disjoint assignments;
3. an immutable external corpus and custody validator;
4. a pure-data family registry and contained-work/overlap validator;
5. a qualified Qwen3.6 re-custody bundle;
6. a runner and independent validator whose source digests are sealed;
7. a reviewer packet with the exact controls, target, thresholds, and
   retention census;
8. an explicit assessment authorization after review acceptance.

Items 1-7 are present for the current external roots. The locked tune utility
gate failed before assessment, so item 8 was not pursued and the pending review
packet cannot authorize execution. The V39 result remains the latest completed
assessment disposition, V82 remains blocked on its missing Gemma/oracle/monitor
artifacts, and Stage 0C and Stage 1 remain blocked.
