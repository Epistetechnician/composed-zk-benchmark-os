# Astral causal-accessibility measurement audit V47 — design memo

State slice: `astral-stage0c-causal-accessibility-measurement-audit-v47`.

Date: 2026-08-28.

Status: `RejectedByIndependentReview / ExecutionNotAuthorized / AssessmentNotAuthorized`.

## Authorization scope

This memo is authorized as a literature-grounded design artifact for a
potential successor to V46. It defines a new causal theory, estimands, power
and reliability requirements, falsifiers, data identity requirements, control
contract, prediction-lock ordering, review gate, retention policy, and claim
ceiling.

This memo does not authorize model loading, model or corpus acquisition,
runtime changes, source changes, instrument implementation, qualification,
fit/tune execution, assessment, artifact-root creation, provider calls,
accepted Evidence Ledger mutation, Stage 0C promotion, or Stage 1 promotion.
Any executable successor requires a separate authorization naming its exact
state slice, actor, runtime, source digests, runner, validator, custody root,
data identity, and claim ceiling.

## Decision summary

The candidate theory is **causal accessibility of a task-relevant latent
state**. A latent state is eligible only when it is:

1. independently recoverable from more than one predeclared measurement view;
2. causally localizable to a bounded internal pathway;
3. intervention-sensitive, with a directly measured downstream consequence;
4. stable across fresh contexts, paraphrases, and held-out state transitions;
5. capable of changing the response to a separate target intervention; and
6. useful for held-out prediction beyond text-only, input-only, shuffled,
   constant, and matched controls.

This is a materially different question from V46. V46 asked whether a fixed
response-readout scalar predicted paired replacement effects. V47 asks whether
access to a candidate latent state changes the causal response to an
intervention, and whether that state supplies incremental held-out predictive
information. V46 remains permanently closed as
`AnswerAlignedNoCandidate`; its scientific artifacts are not V47 inputs.

The recommended first mechanism is a single predeclared state-access operator
motivated by deep-to-shallow state propagation, such as the fixed
recirculation-style transfer described below. A workspace lens, transcoder
graph, or other operator is not an interchangeable fallback. Selecting a
different operator requires a new rationale or a separately amended design
and must occur before fresh data are opened.

## Literature basis and limits

The following sources inform this design. They are external theory and prior
work, not Astral evidence. None authorizes execution or raises the Astral
claim ceiling.

| Source | Contribution to this design | Limitation that remains binding |
|---|---|---|
| [Causal Abstraction](https://www.jmlr.org/papers/v26/23-0058.html) | Formalizes mechanistic hypotheses as graded causal abstractions evaluated through interventions, including patching, mediation, tracing, and feature transformations. | A proposed representation is not faithful merely because it is readable or predictive. |
| [Recirculation](https://arxiv.org/html/2608.17981v1) | Supplies a concrete state-access hypothesis: contextualized deep representations may be fed back to shallower processing so a state can influence later computation. | The local Qwen studies were mixed and model-specific; language-model improvement is not causal self-modeling. |
| [Verbalizable Representations Form a Global Workspace](https://arxiv.org/abs/2607.15495) | Supplies a workspace hypothesis involving intermediate, broadcast, reportable representations and a Jacobian-lens measurement idea. | It is a recent external preprint on other model families; workspace-like structure does not establish consciousness, selfhood, or causal faithfulness. |
| [Circuit Tracing](https://transformer-circuits.pub/2025/attribution-graphs/methods.html?slug=calc-36-plus-59) | Supplies feature-level attribution graphs and replacement-model validation for forming bounded mechanism hypotheses before direct interventions. | Replacement-model error and incomplete QK accounting can produce incomplete graphs; graph edges are not automatically the original model's full causal graph. |
| [Transformer Dynamics](https://arxiv.org/abs/2502.12131) | Motivates treating residual activity as a trajectory and measuring stability, observability, and controllability across depth. | Trajectory geometry alone does not identify a task-relevant causal state. |
| [Identifiable Causal Representation Learning](https://arxiv.org/abs/2406.13371) | Supplies the identifiability discipline: latent variables require structural assumptions and multiple environments or views to avoid arbitrary-basis explanations. | Identifiability conditions must be stated for the actual actor and data; they cannot be assumed from a probe. |
| [Activation Patching Best Practices](https://arxiv.org/abs/2309.16042) | Establishes that corruption, patch construction, and metric choices can change localization conclusions, requiring fixed methods and controls. | Best practices reduce measurement ambiguity but do not create causal ground truth. |
| [Partial Introspection](https://arxiv.org/abs/2512.12411) and [Self-access reality check](https://arxiv.org/abs/2503.07513) | Require rival input-only explanations and distinguish narrow, prompt-sensitive reporting from privileged access. | Negative results in one report paradigm do not prove all internal-state access impossible. |
| [Continuous-Depth Field Theory](https://arxiv.org/abs/2605.25225) | Offers a preliminary vocabulary of sensitivities, propagated fields, and Green-operator slices for response-kernel analysis. | It is a recent preprint and is an optional analysis framework, not a required instrument or validated Qwen3.6 method. |

The [Neural Chameleons study](https://arxiv.org/html/2512.11949v1) remains a
separate monitor-evasion branch. Its trigger-dependent activation shifts,
monitor suppression, and per-head or Q/K/V diagnostics cannot be imported as
V47 actors, data, artifacts, or evidence. The local [V82 preflight](82-neural-chameleon-replication-v1-preflight.md)
remains stopped at missing external Gemma, precursor, oracle, monitor, and
corpus artifacts.

## Causal theory

Let:

- `X` be the task context and observed input;
- `Z` be a candidate task-relevant latent state;
- `H` be the bounded internal carrier or pathway through which `Z` is used;
- `A` be a fixed state-access condition, with `A=1` enabling the declared
  access operator and `A=0` using its matched access-null condition;
- `I` be the separate target intervention, with `I=1` applying the declared
  counterfactual replacement and `I=0` applying the ordinary condition;
- `Y` be the directly measured behavioral or logit-margin outcome; and
- `T` be the telemetry supplied to the predictor or report mechanism.

The proposed causal structure is:

```text
X ───────► Z ───────► H ───────► Y
│          └──────► T
└──────────────────────────────► Y

A ─────────────────────────────► H
I ─────────────────────────────► H
```

The arrows from `A` and `I` enter the bounded carrier/pathway `H`; neither
condition is granted a direct outcome path. The outcome interaction is
therefore tested as an effect-modification question downstream of `H`, while
the direct `X -> Y` path preserves the rival explanation that the observed
input is sufficient. `T` is a measurement supplied to a predictor and is not
part of the intervention path.

The theory makes five testable claims:

1. **Recoverability:** `Z` can be recovered from independent predeclared
   views without using held-out intervention labels.
2. **Localization:** the pathway carrying `Z` can be bounded by direct causal
   interventions and survives replacement-model or feature reconstruction
   checks.
3. **Access:** enabling the declared access operator changes downstream use of
   `Z` relative to a matched access-null condition.
4. **Mediation:** access changes the response to the separate target
   intervention, rather than merely changing generic output quality.
5. **Privilege:** telemetry containing `Z` improves held-out prediction beyond
   information available from `X` and its text-only or input-only rivals.

Failure of any necessary claim prevents a bounded causal-accessibility result.
No verbal report is treated as evidence of a latent state without the causal
and rival-model tests.

## Primary and secondary estimands

For a fixed family, define `Y(i,a)` as the outcome under target-intervention
condition `i` and state-access condition `a`. The primary estimand is the
access-mediated intervention contrast:

```text
tau_access = E[Y(1,1) - Y(0,1)] - E[Y(1,0) - Y(0,0)]
```

Equivalently, this is the interaction between the target intervention `I` and
the state-access condition `A`. It asks whether access changes the causal
effect of the target intervention. It is not a correlation between a hidden
feature and a measured effect.

Identification requires a complete paired `2 x 2` factorial for every eligible
family: the same sealed family state and context must be executed under all
four cells `(I=0,A=0)`, `(I=1,A=0)`, `(I=0,A=1)`, and `(I=1,A=1)` using a
predeclared counterbalanced order. A family missing any cell is excluded by a
predeclared rule before effects are inspected. The family-level interaction
contrast is `D = Y(1,1) - Y(0,1) - Y(1,0) + Y(0,0)`; document clustering is
applied to these paired family contrasts rather than to individual tokens.

The exact outcome scale must be fixed before fresh data are opened. The
eligible scale may be a signed answer-logit margin or a bounded behavioral
score, but the choice must be single, theory-justified, and identical across
fit, tune, and assessment. The protocol must not switch scales after seeing
effects.

The secondary estimands are incremental held-out predictive values:

```text
delta_text  = Loss(text_only)  - Loss(state_aware)
delta_input = Loss(input_only) - Loss(state_aware)
```

where lower loss is better, all predictors are trained only on fit data, and
both comparisons are evaluated on document-, author-, template-, seed-, and
state-graph-disjoint assessment families. The state-aware predictor must beat
both text-only and input-only controls, as well as shuffled, constant, and
matched controls, under the same feature budget and fitting rule. Neither
`delta_text` nor `delta_input` may be replaced by a post hoc minimum or by a
single omnibus score.

Additional prespecified diagnostics are:

- cross-view recoverability of `Z`;
- cross-context transport of the locked state map;
- within-family and between-document variance;
- state and target-effect repeatability;
- calibration and interval coverage; and
- the fraction of assessment families for which the predicted and measured
  intervention-effect signs agree.

These diagnostics cannot be promoted to replacement estimands after
assessment begins.

## Proposed access mechanism

The preferred candidate is one fixed deep-to-shallow state-access operator
motivated by recirculation. In abstract form, for a declared source site `s`,
destination site `d`, and token position `p`, the access-enabled condition is:

```text
z_access[d,p] = alpha * normalize(z[s,p] | d) + (1 - alpha) * z[d,p]
```

The source site, destination site, position rule, normalization, coefficient,
and number of additional passes must be fixed by theory before data are
opened. They are not selected from V46 outcomes, fit/tune effects, or
assessment effects. The access-null condition must preserve the same prompt,
token position, execution count, shape, and measured norm budget without
carrying the candidate state.

The implementation authorization must also freeze a finite state cardinality
`K`, a state encoding, and two measurement views `V1` and `V2`. The views must
be constructed by separate predeclared measurement procedures, must not share
target-intervention labels or effects, and neither may be a deterministic
post-processing of the other. Recoverability is a fixed gate: the locked
cross-view decoder must have a lower 95% bootstrap bound for balanced accuracy
above `1/K + 0.10` on tune families, with the same decoder and threshold carried
to assessment. Localization is a separate fixed gate requiring the declared
carrier intervention to change the state-specific outcome contrast beyond its
matched generic-output control. These gates are requirements for the future
authorization, not results claimed by this memo.

This mechanism is a design candidate, not an execution authorization. The
future runner must independently validate native parity, no-op identity,
deterministic repeatability, bounded shapes, nonzero logit reach, and source /
runtime custody before any scientific measurement. If the cached Qwen3.6
runtime cannot support the operator without an unvalidated seam, execution
stops; a different operator cannot be substituted silently.

## Fresh data identity

V47 must use a new external custody chain. V39-V46 corpora, panels, family
identifiers, anchors, prompt templates, activation arrays, intervention
effects, predictors, and result bundles are excluded as inputs. Earlier results
may inform the written rationale only.

The data must test state access rather than generic literary prediction. The
required fresh panel has two jointly sealed components:

1. **External context component:** a new public-domain or independently
   licensed text source root, with source-byte digests and no overlap with the
   V39-V46 source inventory. Project Gutenberg may supply contexts, but its
   prose alone is not a state-transition ground truth.
2. **Controlled state component:** a separately generated state-transition
   wrapper with a new generator seed, new templates, and a declared finite
   state graph. Each family must have an ordinary and counterfactual context,
   a known state update, a target intervention, and a predeclared outcome
   mapping. The generated records and source inputs remain external and
   immutable.

Fit, tune, and assessment must be disjoint by source document, author, exact
   text, near-duplicate text, generator seed, template, semantic state graph,
   and counterfactual mapping. Each split requires a separate digest. A
   document or state graph may not contribute families to more than one split.
   The panel validator must perform exact and normalized duplicate checks before
   model execution.

No fresh corpus is acquired by this memo. The future acquisition record must
   bind the source revision, license or public-domain basis, selection rule,
   generator version, random seeds, per-record lengths, split membership, and
   complete file census.

## Power and reliability plan

The primary unit of inference is the document-level cluster, not an individual
token. Family-level observations within one document share context and must be
clustered in the bootstrap and uncertainty model. The primary analysis uses a
predeclared paired mixed-effects model or document-cluster bootstrap, with the
same method selected before fit data are inspected.

The following is a planning sensitivity calculation, not an observed result.
It assumes two-sided alpha `0.05`, 90% power, a standardized paired effect
threshold `d`, four families per document, and document ICC `0.20`. Here `d`
is the minimum family-level interaction effect standardized by the SD of
`D = Y(1,1) - Y(0,1) - Y(1,0) + Y(0,0)` before document clustering. The cluster
design effect is `1 + (4 - 1) * 0.20 = 1.60`; all adjusted counts are rounded
up before conversion to documents.

| Standardized `d` | Independent paired units before clustering | Cluster-adjusted family equivalents | Approximate documents before attrition | Planning documents with 20% attrition |
|---:|---:|---:|---:|---:|
| 0.30 | 117 | 188 | 47 | 59 |
| 0.40 | 66 | 106 | 27 | 34 |
| 0.50 | 43 | 69 | 18 | 23 |

The future authorization must replace these planning assumptions with a
sealed simulation using its exact family cardinality, cluster structure,
missingness rule, and primary estimand. No assessment opens below the sample
size that achieves at least 90% power at the preregistered minimum effect
under the preregistered ICC sensitivity range. Fit and tune sizes must also be
large enough to estimate the locked predictor without using assessment
effects.

Reliability is a separate gate from deterministic software repeatability. The
future protocol must include:

- an independent-process repeat on a predeclared fraction of fit and tune
  families;
- a paraphrase or alternate-view repeat that does not change the state graph;
- an intraclass correlation estimate for `Z` and the directly measured target
  effect;
- cluster-bootstrap interval coverage for `tau_access`;
- sign stability across the repeated measurements; and
- a complete variance decomposition separating document, family, token, and
  measurement-repeat components.

The recommended minimum reliability gates are a lower 95% confidence bound of
`0.80` for the state-map and target-effect absolute-agreement ICCs, estimated
with a predeclared `ICC(A,1)` method, plus a predeclared minimum sign-stability
threshold of `0.80`. These values are design requirements, not results, and
may only be changed by a separately reviewed protocol amendment before data
are opened.

## Unchanged controls and anti-shortcut requirements

The V46 control contract remains mandatory and cannot be weakened:

- `activation_only`;
- `text_only`;
- `exact_copy`;
- `shuffled`;
- `constant`; and
- `matched`.

The future access mechanism adds a matched access-null condition and a
matched-energy or matched-norm control. These are additions, not replacements
for the V46 controls. Any mechanism-specific operator control must be named in
the authorization before fit data are read.

The predictor must not receive target-intervention labels, assessment effects,
post-intervention activations, or any field that directly identifies the
ordinary/counterfactual outcome. Text-only and input-only controls must be
allowed to use all information visible in `X`, including the controlled task
description, so that an apparent telemetry advantage cannot be a prompt leak.

## Prediction locking and review order

The required order is:

1. verify fresh custody, model identity, runtime identity, and instrument
   qualification;
2. measure fit data and select only the predeclared state map and predictor;
3. emit and digest fit/tune predictions before generating the corresponding
   tune intervention effects;
4. freeze the predictor, feature map, access operator, metric, thresholds,
   controls, and retention policy;
5. obtain an independent review receipt against the frozen configuration;
6. open assessment only if the review receipt is valid; and
7. generate assessment effects, compare locked predictions with effects, and
   invoke the independent aggregate-only validator.

The reviewer must independently verify:

- actor, tokenizer, runtime, and source custody;
- fresh corpus and split identity;
- state-graph and counterfactual construction;
- access operator and access-null semantics;
- unchanged controls and anti-shortcut boundaries;
- power and reliability calculations;
- prediction-lock digest and ordering;
- exact estimand and metric;
- privacy and aggregate-only retention;
- claim ceiling and stop codes; and
- validator independence and behavior.

An invalid or absent review receipt closes assessment. No reviewer may repair a
failed gate by choosing another layer, wrapper, position, threshold, control,
corpus, feature map, or estimand.

## Retention and validation

The external immutable result root may retain only:

- protocol and configuration digests;
- model, tokenizer, runtime, source, and corpus digests;
- split and state-graph counts;
- aggregate intervention outcomes;
- aggregate predictions and uncertainty intervals;
- reliability summaries;
- stop codes;
- prediction-lock and review receipts; and
- independent validation receipts.

Raw prompts, raw activations, raw logits, raw generated text, per-token
telemetry, transcripts, credentials, PII, and unneeded model outputs are not
retained in the repository or result bundle. The independent validator must
recompute all retained aggregates from an approved, bounded input surface and
reject undeclared raw fields, digest drift, split leakage, lock-order drift,
or assessment execution without review.

## Falsifiers and stop rules

The audit stops without adaptive retry if any of the following occurs:

- native parity, no-op, repeatability, shape, logit-reach, or custody
  qualification fails;
- the fresh data manifest or split validator detects overlap or drift;
- `Z` is not recoverable across its predeclared independent views;
- the access operator changes generic output but not the predeclared state
  outcome;
- the access-by-intervention interaction is absent or unstable;
- the target effect is not reliable at the locked measurement scale;
- text-only or input-only controls match the telemetry predictor;
- shuffled, constant, or matched controls perform comparably;
- the locked predictor fails the preregistered held-out utility and uncertainty
  gates;
- the review receipt is missing or invalid; or
- the independent validator reports any error.

A near-miss correlation, isolated positive family, or directionally favorable
pilot does not reopen V46 and does not justify a post hoc change.

## Result classifications and claim ceiling

The only permitted classifications are:

1. `InstrumentFeasibility`: the access and measurement apparatus qualifies, but
   no scientific candidate is established.
2. `DevelopmentNoCandidate`: the apparatus qualifies, but the locked causal
   accessibility and prediction gates fail.
3. `BoundedCausalAccessibilityResult`: the complete preregistered causal
   accessibility, reliability, held-out prediction, control, review, retention,
   and independent-validation gates pass for the named actor, task family,
   access operator, and data identity.

Even the third classification would establish only a bounded local
   causal-accessibility or target-validity result. It would not establish
   introspection, consciousness, selfhood, general causal self-modeling,
   universal monitorability, benchmark evidence, production readiness, Stage
   0C, or Stage 1. Stage 0C requires a separate complete validated
   causal-target result through the existing gates. Stage 1 remains blocked
   until Stage 0C passes.

## Required next gate

Independent review rejected this design on 2026-08-28. The theory and primary
interaction estimand are plausible, but the memo does not operationalize
assignment, timing, consistency, positivity, and no-interference assumptions,
and its localization gate lacks a fixed effect metric, minimum threshold,
uncertainty bound, and multiplicity rule. These are protocol-validity defects,
not results to repair by tuning during execution.

Accordingly, no separate implementation authorization is issued. No corpus
acquisition, model qualification, fit/tune measurement, assessment, or result
retention may proceed under V47. Astral experimentation is stopped pending a
new separately authorized slice with a stronger scientific rationale and a
complete operational measurement audit. V46 remains permanently closed, Stage
0C and Stage 1 remain blocked, and V82 remains isolated and blocked.

V82 remains isolated and blocked. Its missing Neural Chameleon artifacts must
be supplied and authorized through its own branch; they cannot satisfy this
V47 gate.
