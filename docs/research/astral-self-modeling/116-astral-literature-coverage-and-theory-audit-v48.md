# Astral literature coverage and theory audit after V48

State slice: `astral-literature-coverage-theory-audit-v48`.

Date: 2026-08-28.

Status: documentation-only audit. This state slice does not authorize model
loading, corpus acquisition, implementation, GiveMeANode work, assessment,
Evidence Ledger mutation, or a new Astral experiment.

## Audit question

Have Astral's executed protocols fully tested the six theoretical directions
that could inform a future causal-target study?

Answer: no. Astral tested several intervention, prediction-locking, rival
control, custody, and independent-validation ingredients. It did not execute a
complete, theory-specific study of every direction below. A literature result
or a local instrumentation result is not a test of the corresponding scientific
claim.

## Coverage vocabulary

- **Direct test:** the theory's own causal variables, intervention, estimand,
  controls, and held-out endpoint were preregistered and executed in Astral.
- **Partial analogue:** Astral tested a related ingredient, but not the theory's
  defining construct or complete estimand.
- **Untested:** the direction exists as literature or a docket hypothesis only.
- **Separate branch:** the work is outside Astral's evidence boundary and cannot
  be used to fill an Astral gap.

## Coverage findings

### 1. Causal abstraction and interchange intervention

Disposition: **partial analogue, not a complete test**.

Astral directly used zero replacement, matched patching, paired replacement,
held-out intervention effects, prediction locking, and input/text rival
controls in the V12-V48 families. V48 also tested a bounded cross-view
transport target. These results validate parts of an intervention pipeline, not
an abstract causal model.

The missing elements are an explicit high-level causal model, a mapping from
that model to the original model's mechanisms, a prespecified interchange
intervention suite, and a graded faithfulness score comparing the abstract and
original systems over held-out interventions. The causal-abstraction literature
provides this formal language and unifies several mechanistic methods, but it
does not make an attribution or replacement representation faithful by default:
[Geiger et al., *Causal Abstraction*](https://arxiv.org/abs/2301.04709).

### 2. Global-workspace/J-space theory

Disposition: **untested**.

Astral did not implement the Jacobian lens, identify a J-space representation,
test broadcast to arbitrary downstream computations, or measure workspace
stability across fresh contexts. V22's activation-versus-input discrimination
and V25's information-presence result are related information-boundary tests;
neither is a J-space test.

The cited work is an external, model-specific report of representations that
are reported to be verbalizable, summonable, retainable, and broadcast. Those
properties would need a separately defined causal accessibility protocol before
they could bear on Astral:
[J-space paper](https://arxiv.org/abs/2607.15495).

### 3. Circuit tracing and cross-layer transcoders

Disposition: **untested as accepted Astral evidence**.

The repository contains a literature entry and a historical conversation pilot
that reported transcoder-captured computation, but the pilot has no underlying
run artifacts and was not independently inspected. Astral has not trained or
custodied a cross-layer transcoder, measured replacement-model coverage and
reconstruction error, or validated an attribution graph against original-model
interventions.

Circuit tracing is therefore a candidate localization scaffold, not a causal
result. The primary methods report explicitly treats the replacement model as
an indirect approximation and uses perturbation validation; it also identifies
attention coverage, reconstruction error, and global-circuit limitations:
[Circuit Tracing methods](https://transformer-circuits.pub/2025/attribution-graphs/methods.html?slug=calc-36-plus-59).

### 4. Dynamical systems and observability

Disposition: **untested in the Astral causal lane**.

Astral has not measured residual-stream trajectories as a formal dynamical
system with predeclared persistence, observability, controllability, and
transport estimands. The repository's evidence-conditioned multiscale
plasticity work is a separate synthetic control-plane lane. Recirculation is a
separate continual-learning hypothesis. Neither supplies Astral causal
evidence.

The cited work proposes viewing the residual stream as a trajectory across
layers and reports continuity and attractor-like structure. Descriptive
trajectory structure is not evidence that a state is causally observable or
controllable:
[Transformer Dynamics](https://arxiv.org/abs/2502.12131).

### 5. Identifiable causal representation learning

Disposition: **untested; V48 is only a related diagnostic**.

V48 included cross-view recoverability as one bounded target and failed its
fixed gates. That is not an identifiability result. Astral has not specified
the required multi-view or multi-environment assumptions, shown equivalence of
representations under those assumptions, or established that a recovered
representation is unique up to an allowed transformation.

The cited thesis makes identifiability conditional on model-class assumptions
and sufficiently rich data. It is a design discipline for a future protocol,
not a certificate for existing Astral activations:
[Identifiable Causal Representation Learning](https://arxiv.org/abs/2406.13371).

### 6. Introspection falsification and rival models

Disposition: **partial analogue; no complete replication**.

V18-V25 and V22-V24 introduced useful rival-model pressure: input-only and
textual alternatives, exact-text activation/no-change pairs, gaslighting
controls, observer comparisons, and bounded report tasks. V25 remains an
information-presence/report-gap result only. No Astral slice reproduced both
recent cited studies with their model, task, and differential-sensitivity
definitions.

The literature is not a single settled result. One study reports that binary
detection can be an affirmative-logit artifact but finds partial, layer-
dependent disturbance localization under differential tests:
[Detecting the Disturbance](https://arxiv.org/abs/2512.12411). Another evaluates
21 open models against their own string probabilities and reports no privileged
self-access in the tested language-knowledge setting:
[Language Models Fail to Introspect](https://arxiv.org/abs/2503.07513).
This disagreement strengthens the requirement for task-specific causal
controls; it does not establish an Astral result.

## What Astral has actually established

The [cumulative V1-V48 synthesis](112-astral-cumulative-evidence-synthesis-stop-v48.md)
has the correct ceiling:

1. intervention and custody plumbing can be made reproducible;
2. exact no-op, matched, shuffled, constant, text-only, and input-only controls
   can be enforced where the protocol requires them;
3. V48's bounded causal-state-transport target failed its fixed localization,
   effect-prediction, and cross-view recoverability gates; and
4. no tested result establishes introspection, causal self-modeling, Stage 0C,
   Stage 1, benchmark evidence, consciousness, or production readiness.

The [closed theory docket](astral-theory-docket-v48-closed.md) remains
correct. Its recirculation, circuit-tracing, workspace/J-space,
cross-architecture, and Neural Chameleon entries are hypotheses or separate
branches, not evidence.

## Strongest future theory candidate

If Astral is ever reopened, the most defensible first candidate is a bounded
**causal-abstraction and circuit-localization audit**. Circuit tracing would
generate a candidate graph; causal abstraction would define the correspondence;
direct original-model interventions would decide whether the correspondence is
faithful. Neither graph readability nor activation correlation would be the
primary endpoint.

This is a proposal skeleton only. It is not a sealed protocol or authorization.

### Candidate estimand

For a held-out intervention row (i), let (\Delta_i^{orig}) be the change in
the predeclared output margin under an intervention in the original model, and
let (\Delta_i^{abs}) be the change predicted by applying the corresponding
interchange intervention to the abstract/replacement model. A possible primary
summary is the bounded graded-faithfulness score:

```text
GCF = 1 - mean_i(abs(delta_orig_i - delta_abs_i))
             / (mean_i(abs(delta_orig_i)) + epsilon)
```

The final score, threshold, uncertainty interval, missingness rule, and
multiplicity correction must be fixed in a reviewed protocol. The score must
be accompanied by raw-scale effect agreement, not reported alone.

### Required design

- define causal variables, assignment, timing, consistency, positivity, and
  no-interference assumptions;
- freeze the candidate graph, feature dictionary, replacement operator, output
  metric, and intervention construction before assessment;
- measure original-model versus replacement-model agreement on held-out
  interchange interventions;
- quantify reconstruction error, unexplained variance, attention/QK coverage,
  and intervention reach;
- include exact-copy/no-op, zero, shuffled-graph, constant, matched-energy,
  input-only, and text-only controls;
- use fresh document- and concept-disjoint fit, tune, and assessment splits;
- lock predictions before assessment effects are generated;
- power the study on the independent document or intervention-family unit and
  correct for all prespecified graph/component comparisons;
- retain aggregate results only and independently recompute the result from a
  sealed manifest; and
- cap the claim at bounded causal abstraction/localization unless a later,
  separately reviewed protocol establishes a stronger target.

### Falsifiers

The protocol must stop if any of the following occurs:

- the replacement model passes descriptive reconstruction but fails held-out
  intervention agreement;
- the graph's result is matched by shuffled or input-only controls;
- effect agreement depends on one layer, prompt family, graph, or seed without
  a prespecified interaction model;
- attention/QK omissions or reconstruction residuals explain the apparent
  causal path;
- the primary lower uncertainty bound misses the fixed threshold; or
- prediction locking, custody, retention, or independent-validator checks fail.

## Binding decision

This audit does not reopen Astral. No model, corpus, layer, wrapper, alpha,
position, threshold, assessment, or scientific execution is authorized. Stage
0C and Stage 1 remain blocked. V82 remains isolated and blocked for its missing
artifacts. The current dynamic-learning task remains separate control-plane
research and cannot be counted as Astral evidence.

Astral may resume only if an independent reviewer accepts a complete version
of the candidate protocol with an exact effect threshold, uncertainty and
multiplicity rules, power and reliability analysis, fresh data identity,
unchanged rival controls, prediction locking, a sealed implementation
contract, and a claim ceiling. Otherwise the Astral experimental branch stays
closed.

## Sources and repository records

- [Literature index](06-literature-index.md)
- [V12 causal-target protocol](20-stage0c-intervention-effect-target-validity-v12.md)
- [V22 activation-versus-input protocol](40-activation-input-discrimination-v22.md)
- [V48 execution record](111-v48-execution-record-2026-08-28.md)
- [V48 cumulative stop record](112-astral-cumulative-evidence-synthesis-stop-v48.md)
- [Closed theory docket](astral-theory-docket-v48-closed.md)
