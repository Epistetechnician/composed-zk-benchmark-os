# Astral Stage 0C V38-Derived Qwen3.6 Layer-Effect Protocol V39

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

Status: `Authorized / QualificationOnly / AssessmentSealed`.

This is a fresh, separately authorized protocol derived from the V38
instrument boundary. It does not reopen V28 or V29, reuse V25 artifacts, or
turn the V38 feasibility result into scientific evidence. The V38 boundary
states that its maximum claim is
`LocalDevelopmentInstrumentFeasibilityOnly` and requires a new identity,
custody packet, fresh splits, prediction lock, direct held-out effects,
controls, independent validation, and separate assessment authorization
([V38 boundary](80-qwen36-layer-instrument-feasibility-v38.md#claim-ceiling)).

## Closed lanes and separation

| Lane | Disposition | V39 treatment |
|---|---|---|
| V28–V29 | Closed after failed held-out utility | No prompts, effects, channels, configurations, predictions, or artifacts are inputs. |
| V25 | Information-presence result only | No concepts, reports, residuals, predictions, or artifacts are inputs. |
| V30–V37 | Governance and validation controls, not scientific evidence | Their control ideas may be cited as policy; their result artifacts cannot supply V39 evidence. |
| V61 | Docs-only full-bandwidth boundary | No actors, artifacts, or evidence are shared. |
| V82 | Blocked at missing Gemma/oracle/monitor artifact custody | V39 does not satisfy or advance the Neural Chameleon branch. |

V39 has its own protocol identity, state slice, source digests, external
qualification root, future concept-registry digest, split digests, prediction
lock, validator receipt, and claim ceiling. The Neural Chameleon study remains
a separate branch with no shared actors, artifacts, or evidence.

The source-custody implementation is documented in [V39 Project Gutenberg
corpus intake](85-v39-gutenberg-corpus-intake.md). It is a preparation tool
only: it acquires explicit external documents and leaves the concept registry,
prediction lock, independent review, and assessment closed.

## Question and claim ceiling

The qualification question is whether the cached Qwen3.6 MLX implementation
exposes a deterministic, shape-correct layer capture and replacement seam that
can reach logits. The future scientific question is whether a fixed
activation-only observer predicts directly measured held-out layer-replacement
effects better than text-only, shuffled, constant, and matched controls.

Qualification alone can produce only `InstrumentFeasibility` at
`LocalDevelopmentInstrumentFeasibilityOnly`. A fully executed future panel may
classify as `DevelopmentNoCandidate` or `BoundedTargetValidity`; neither
classification establishes introspection, causal self-modeling, Stage 0C,
Stage 1, benchmark evidence, or production readiness. A bounded target-validity
result is an input to the existing Stage 0C gate, not an automatic Stage 0C
pass.

## Exact custody contract

The operator supplies a repository-external, resolved model directory. The
directory basename must be exactly `Qwen3.6-35B-A3B-MLX-4bit`, and the loaded
architecture must be `Qwen3_5MoeForConditionalGeneration`. The qualification
contract expects 40 text layers and hidden width 2048. Every regular model
file is bound by byte length and SHA-256 in a recomputed model manifest;
symlinks, missing files, downloads, and repository-contained model roots are
rejected.

The locked runtime is:

- Python version recorded by the runner;
- `mlx==0.31.2`;
- `mlx-lm==0.31.3`;
- the installed source digests for `mlx_lm.models.qwen3_5` and
  `mlx_lm.models.qwen3_5_moe`;
- SHA-256 digests for the V39 qualification runner and pure-data protocol
  module.

The qualification output root is also repository-external, resolved, and
empty before execution. It may contain only `qualification-result.json` and
the non-secret `validator-receipt.json`. The result contains aggregate
metrics and custody digests only. Prompts, token arrays, hidden states,
logits, traces, credentials, PII, and reasoning traces are not retained.

## Instrument seam and qualification gates

The runner wraps the native objects at
`model.language_model.model.layers`, captures each post-layer output, and
tests only the final token at target layer 19. The replacement is a synthetic
final-position addition with fixed scale `0.01`; it is not a per-head, Q/K/V,
route, or mechanistic-transplant instrument.

Qualification executes in this order for two new neutral qualification
prompts whose raw text is not retained:

1. Run the native model and the unmodified layer wrapper on identical tokens;
   maximum absolute logit delta must be at most `1e-4`.
2. Repeat the unmodified wrapped run; maximum absolute logit delta must be at
   most `1e-5`.
3. Apply zero replacement; maximum absolute logit delta must be at most
   `1e-5`.
4. Apply the fixed nonzero layer-19 replacement; maximum absolute logit delta
   must exceed `1e-6`.
5. Confirm every captured and replaced layer has shape
   `(batch=1, sequence_length, hidden_width=2048)`, with 40 layers.
6. Recompute model, runtime, and source digests independently. Any failed
   gate stops qualification and cannot open an assessment.

The qualification runner cannot create a corpus, prediction lock, assessment
effect file, or Stage 0C record. The independent validator rechecks the
aggregate result, output census, external model manifest, runtime versions,
installed runtime-source digests, runner/protocol digests, and all gates. It
does not treat a result JSON as custody by itself.

## Future scientific panel

The scientific panel is not opened by qualification. It requires a new,
immutable external corpus bundle and a separately reviewed configuration.
The following are frozen before any fit measurement:

- 48 fresh concept families from 12 source documents, with 16 families and
  four documents assigned to each of fit, tune, and assessment;
- document-disjoint and concept-disjoint splits, with no source document
  appearing in more than one split;
- a concept-registry digest that is not present in V25 or V28–V29 artifact
  manifests, plus explicit freshness exclusions for those protocols;
- paired ordinary/counterfactual prompts, fixed response labels, fixed token
  positions, and fixed document/family identifiers;
- target layer 19 and a signed correct-minus-incorrect response-logit margin;
- direct intervention target
  `effect = margin(do(layer_19_final := matched_layer_19_final)) -
  margin(clean)`, measured from the actor rather than inferred from a report;
- a fixed ridge candidate set `{1e-4, 1e-3, 1e-2, 1e-1}`, fit-only
  standardization, tune-only selection, and no assessment tuning.

The mandatory observer and control panels are:

- `activation_only`: a fixed 64-scalar projection of the transient layer-19
  activation, with no text features;
- `text_only`: a fixed 64-scalar token-feature panel, with no activation
  features;
- `shuffled`: the activation panel with a protocol-hash-derived row
  permutation applied before fit and tune, breaking activation/effect
  alignment without changing capacity;
- `constant`: the fit-fold target mean;
- `matched`: a norm-, sequence-length-, position-, and document-matched
  unrelated replacement control, kept separate from the target pair and not
  used to tune the candidate.

All feature transforms, permutations, response labels, layer selection, and
hyperparameter choices are sealed before assessment effects are measured.
The matched control is retained as a negative-control distribution, not as a
mechanistic explanation.

## Execution order and prediction lock

1. Verify external custody, source/runtime digests, freshness exclusions, and
   the passed V39 qualification receipt.
2. Validate the new concept registry and document-disjoint fit/tune/
   assessment split manifest without measuring assessment effects.
3. Measure fit features and direct fit intervention effects; fit the frozen
   candidate/control estimators.
4. Measure tune features/effects and select only the preregistered ridge
   candidate using tune error. No assessment statistic may influence this
   choice.
5. Materialize all assessment predictions and a digest-bound
   `prediction-lock.json`. The lock must state that assessment effects are
   absent and bind the protocol, model, corpus, split, estimator, and source
   digests.
6. Obtain independent review. The reviewer must verify custody, fresh data
   identity, split disjointness, controls, prediction lock, privacy retention,
   validator behavior, and claim ceiling. A missing review or an opened
   assessment invalidates the run.
7. Only after the sealed lock and review receipt exist, measure assessment
   effects, including the matched negative-control panel.
8. Join predictions to effects, compute aggregate-only metrics and uncertainty
   intervals, finalize the classification, and run the independent validator.

Any assessment-effect artifact present before the prediction lock is a
fail-closed protocol violation. No raw assessment artifact is copied into the
repository or the result bundle.

## Classification and advancement

- `InstrumentFeasibility`: qualification passed, assessment unopened. Ceiling
  remains `LocalDevelopmentInstrumentFeasibilityOnly`.
- `DevelopmentNoCandidate`: the complete locked panel fails the preregistered
  held-out utility, calibration, finite-census, or matched-control gate.
  Development stops and no Stage 0C candidate is nominated.
- `BoundedTargetValidity`: the complete locked panel passes the preregistered
  held-out target-validity and control gates, with independent validation and
  no claim escalation. Its ceiling is
  `LocalDevelopmentStage0CQwen36CausalTargetValidity`.

Even the last classification does not establish introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark evidence, or production
readiness. Existing gates remain controlling: Stage 0C requires a complete
validated causal-target result, and Stage 1 remains blocked until Stage 0C
passes. V82 remains stopped at missing external artifacts.
