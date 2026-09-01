# Astral Stage 0C Directional-Block Target Protocol V41

State slice: `astral-stage0c-qwen36-directional-block-target-v41`.

Status: `Authorized / InstrumentFeasibility / ScientificExecutionSealed`.

This is a fresh, separately authorized successor to V40. It is a protocol
design and authorization record. V41 qualification passed independently; no
V41 corpus, panel, preassessment, prediction, intervention effect, review
receipt, or assessment result exists yet. The V41 preassessment, review,
assessment, and finalization surfaces are implemented but cannot execute until
fresh corpus and panel custody exists.

## 1. Authorization scope

This state slice authorizes future additive source and hermetic tests under
`tools/astral-stage0c-qwen36-v41/`, a repository-external immutable Qwen3.6
model and corpus custody chain, a separate aggregate-only validator, and the
protocol and execution records under this research directory. It authorizes
qualification and fit/tune preassessment only after the inputs below are
freshly re-custodied. Assessment requires a sealed prediction lock and an
independent review receipt generated before assessment effects.

This authorization does not itself authorize network downloads, model
training, adapter or weight updates, production traffic, provider calls,
Evidence Ledger mutation, benchmark claims, Stage 0C promotion, Stage 1, or
any claim about introspection, consciousness, agency, identity, or general
self-modeling.

## 2. Rationale and falsifiable hypothesis

V40 passed its Qwen3.6 instrument qualification and then failed its fixed
tune utility gate. Its primary observer used a digest-derived hash-and-bucket
sketch of clean ordinary activation, clean counterfactual activation, and
their signed difference. V40 retained aggregate-only results, so V41 cannot
claim that hash collisions caused the failure. It can test that possibility as
a new hypothesis.

V41 asks:

> Does a fixed, bucket-free signed block projection of the paired activation
> geometry predict directly measured layer-replacement effects better than the
> constant, clean-activation-only, text-only, shuffled, and matched controls?

The only changed scientific factor is the fixed observer feature map. The
actor, layer-19 intervention target, response-margin definition, utility
thresholds, control families, prediction-lock order, retention policy, and
claim ceiling are not loosened in response to V40. Success is judged against
the absolute preregistered gates below, not against an informal improvement
over V40.

## 3. Closed lanes and non-reuse

V28-V29 remain closed after failed held-out utility. V25 remains an
information-presence result only. V30-V37 remain governance controls, not
scientific evidence. V61 remains docs-only. V82 remains stopped at missing
Gemma/oracle/monitor artifacts. The Neural Chameleon branch remains separate
and shares no actors, prompts, concepts, artifacts, or evidence with V41.

V40 may be cited only for aggregate design rationale. V41 must not consume,
transform, or compare scientific outputs from any V40 root, including its
model manifest, corpus, panel, concept registry, split manifest, feature
matrix, prediction lock, review packet, preassessment, effects, or final
result. A byte-identical frozen Qwen3.6 checkpoint may be re-custodied under a
new V41 model manifest; identical model bytes are custody information, not
reused scientific evidence.

## 4. Fresh data identity

The future V41 panel contains exactly 18 new Project Gutenberg documents and
144 new concept families:

| split | documents | families | families per document |
|---|---:|---:|---:|
| fit | 6 | 48 | 8 |
| tune | 6 | 48 | 8 |
| assessment | 6 | 48 | 8 |

The selection manifest must be sealed before panel construction and must
enforce:

- Gutenberg IDs, authors, source documents, and normalized texts absent from
  V40 and every prior Astral scientific panel;
- no anthology, collected-work, or contained-work overlap;
- author-, document-, concept-, and split-disjoint assignments;
- English public-domain status and canonical UTF-8 Project Gutenberg custody;
- a canonical `freshness_exclusion_ids` inventory containing every reserved
  prior-panel Gutenberg ID, with `freshness_exclusion_sha256` recomputed from
  its sorted integer list;
- no exact or normalized 12-gram overlap between selected family excerpts
  across splits;
- deterministic family construction from the selection-manifest digest;
- no effect-dependent filtering, family removal, or outcome-dependent split
  repair.

The V41 corpus root, panel root, model root, and result root must all be
outside the repository, immutable after publication, and independently
digest-bound. Corpus acquisition is an external precondition; this
authorization does not permit network access during model execution.

The exact 18-document selection is sealed in `protocol_v41.SELECTION` and is
copied byte-for-byte into `selection-manifest.json`. The acquisition validator
binds that manifest, its canonical selection digest, and the complete
`freshness_exclusion_ids` inventory before any panel builder can consume the
corpus.

## 5. Actor, runtime, and direct target

The actor is a freshly re-custodied `Qwen3.6-35B-A3B-MLX-4bit` checkpoint. The
model directory must be repository-external, have the declared model identity,
and bind every regular file by byte length and SHA-256. Symlinks, missing
files, repository-contained model roots, and implicit downloads are failures.

The locked runtime records Python, `mlx==0.31.2`, `mlx-lm==0.31.3`, installed
Qwen source digests, runner digest, protocol digest, and validator digest.
Qualification and scientific execution are offline, deterministic, and do
not update weights or adapters.

The target remains a direct actor measurement at layer 19. For each ordinary
and counterfactual prompt pair, let `u` and `v` be the clean final-position
layer-19 activations and let `margin(x)` be the signed correct-minus-incorrect
response-logit margin. The paired intervention target is:

```text
effect_i = 0.5 * [
  margin(ordinary_i, do(layer_19_final := v_i)) - margin(ordinary_i, clean)
  + margin(counterfactual_i, do(layer_19_final := u_i))
  - margin(counterfactual_i, clean)
]
```

The target is measured from replacement executions. It is never inferred from
feature names, reports, textual explanations, or observer predictions.

Each family also receives a fixed unrelated-donor negative-control effect.
Donors must come from another document in the same split, match tokenized
sequence length and response position exactly, and satisfy the preregistered
activation-norm tolerance. Failure to find a donor is a protocol failure; the
matcher may not relax its constraints after effects are visible.

## 6. Qualification-first gates

Qualification runs before V41 corpus features or scientific effects are
materialized. It uses new neutral qualification prompts and a separate
external output root. Every gate must pass:

1. Native versus unmodified-wrapper maximum absolute logit delta is at most
   `1e-4`.
2. Deterministic repeated wrapped execution maximum absolute logit delta is at
   most `1e-5`.
3. Zero/no-op replacement at layers 12, 19, and 26 has maximum absolute logit
   delta at most `1e-5` at each layer.
4. Nonzero final-position replacement at layers 12, 19, and 26 reaches logits
   above `1e-6` at each layer.
5. Captures and replacements preserve batch, sequence, response-position, and
   hidden-width shape, with width `2048`.
6. The actor exposes exactly 40 text layers.
7. Ordinary and counterfactual pair capture is deterministic.
8. Model, runtime, installed-source, protocol, runner, and validator digests
   recompute and bind the receipt.

Any failed gate stops V41. Qualification can produce only
`InstrumentFeasibility` with ceiling
`LocalDevelopmentV41InstrumentFeasibilityOnly`; it cannot open assessment.

## 7. Fixed directional-block observer

V41 uses a pure-data, non-learned block map over each 2048-scalar activation.
The map has 128 non-overlapping blocks of 16 coordinates. Each coordinate in a
block receives a deterministic sign derived from the V41 protocol digest. For
activation vector `x`, the block projection is:

```text
B(x)_b = (1 / sqrt(16)) * sum(sign[b,j] * x[16*b+j]) for j in 0..15
```

The block boundaries, signs, normalization, feature ordering, and digest
derivation are sealed pure-data functions. There are no hash buckets, learned
embeddings, PCA directions, target-derived directions, feature search, or
assessment-derived normalization.

The primary fixed-width feature vector is 516 scalars:

```text
g(u,v) = [B(u), B(v), B(u-v), B(abs(u-v)),
          ||u||, ||v||, ||u-v||, cosine(u,v)]
```

The primary estimator is one standardized ridge regressor. Standardization is
fit-only. Candidate alphas are exactly `{1e-4, 1e-3, 1e-2, 1e-1}` and the
selection rule is tune-only.

The mandatory capacity-matched controls are:

- `clean_activation_only`: fixed block projections of `u`, `v`, `abs(u)`, and
  `abs(v)`, plus the same four scalar summaries, without the paired difference
  blocks;
- `text_only`: fixed 516-scalar digest-derived token and prompt sketch with no
  activation input;
- `shuffled`: the primary feature rows permuted by a protocol-derived
  within-split permutation before fit and tune;
- `constant`: the fit-fold target mean;
- `matched`: the unrelated-donor intervention distribution, never used as a
  learned target or tuning signal.

The model class, feature width, block map, alpha set, and control definitions
cannot expand after tune or assessment observations.

## 8. Fit, tune, lock, review, and assessment

The order is immutable:

1. Recompute and validate all V41 custody, freshness, runtime, model, source,
   panel, split, and qualification digests.
2. Validate document, author, concept, contained-work, and cross-split
   overlap constraints without measuring assessment effects.
3. Measure fit features and direct fit target and matched-control effects.
4. Fit only the declared estimators and select alpha only from tune error.
5. Measure tune features and effects and compute tune-only summaries.
6. Materialize assessment predictions in memory from fit/tune estimator state,
   then create a digest-bound prediction lock containing fit-only states and
   assessment family order. The lock must state that assessment effects are
   absent.
7. Obtain independent review of custody, freshness, controls, donor matching,
   prediction locking, privacy retention, validator behavior, and claim
   ceiling.
8. Only after accepted review, measure assessment target and matched-control
   effects.
9. Join locked predictions with assessment effects in memory and retain only
   aggregate metrics and document-cluster sufficient statistics.
10. Run the independent validator and finalize the narrow classification.

Assessment effects, raw prompts, source excerpts, token arrays, activations,
logits, traces, per-family effects, and per-family predictions present before
the lock are fail-closed violations. The validator must reject them.

## 9. Fixed utility and control gates

The primary metric is unchanged and absolute:

```text
delta_rmse = RMSE(directional_block_primary) - RMSE(constant)
```

Target validity requires every condition below:

- `delta_rmse <= -0.01` on tune and assessment;
- the fixed six-document-cluster bootstrap 95% upper bound for assessment
  `delta_rmse` is below `-0.005`;
- primary assessment RMSE beats `clean_activation_only` and `shuffled` by at
  least `0.005`;
- `text_only` does not beat the primary estimator;
- matched-control mean satisfies `abs(mean) <= 0.25` with zero donor-matching
  violations;
- assessment target standard deviation is at least `0.05` and every split has
  the declared document/family census;
- custody, lock, retention, review, and independent-validator gates pass.

Thresholds, family identities, donor maps, layer, target, controls, feature
map, and alpha candidates are sealed before fit measurement. A tune failure
stops the run before assessment. There is no adaptive V41 retry.

## 10. Retention and validation

The result bundle may retain only model, runtime, source, corpus, panel,
qualification, split, estimator-summary, fit-only-state, lock, aggregate
target/control, document-cluster sufficient-statistic, uncertainty,
validator, and final-classification records. It may not retain raw prompts,
source excerpts, tokens, activations, logits, traces, reasoning text,
credentials, PII, per-family effects, or per-family predictions.

The independent validator must recompute source and file digests, model and
runtime identity, panel census, freshness exclusions, split and overlap
constraints, block-map digest, control definitions, alpha set, lock ordering,
assessment absence before review, aggregate metrics, retention census, and
claim ceiling. Unknown files, stale digests, changed thresholds, changed
controls, or assessment effects before the lock are failures.

## 11. Narrow classifications and advancement

- `InstrumentFeasibility`: qualification passed and assessment remains closed;
  ceiling `LocalDevelopmentV41InstrumentFeasibilityOnly`.
- `TargetDegenerateNoCandidate`: the fixed direct target is non-degenerate
  below the preregistered floor or fails its finite census.
- `DevelopmentNoCandidate`: the locked panel fails utility, controls,
  calibration, retention, review, or validation.
- `BoundedTargetValidity`: every target-validity and control gate passes under
  independent validation; ceiling
  `LocalDevelopmentStage0CQwen36CausalTargetValidity`.

Even `BoundedTargetValidity` is only a local, task-scoped causal-target result
and an input to the existing Stage 0C gate. It does not establish Stage 0C,
Stage 1, introspection, causal self-modeling, consciousness, benchmark
superiority, production readiness, or general mechanistic understanding.
Stage 1 remains blocked until the existing Stage 0C gate passes.

## 12. Stop rules and reversal condition

V41 stops immediately on custody mismatch, freshness failure, qualification
failure, missing exact donor, overlap or census failure, pre-lock assessment
material, review failure, retention failure, target degeneracy, utility-gate
failure, control failure, uncertainty failure, or independent-validator
failure. A stopped run is classified narrowly and cannot be repaired by
changing its threshold, feature map, panel, donor map, or estimator.

The design should be reversed only if an independently reviewed analysis shows
that the block projection is not the operative distinction—for example, if
the fixed block and V40-style hash representation are both tested on fresh
panels and fail for the same bounded reason. That analysis would itself
require a new protocol; it cannot rewrite a V41 result.
