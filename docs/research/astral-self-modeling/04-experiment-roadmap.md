# Experiment Roadmap

## Current Decision

The tested one-pass local gradient-selector lane is closed. The planted control
validated measurement plumbing, but V5 returned `Null` and V10 selected no
method because activation magnitude remained stronger. Stage 1 observer work is
blocked until a redesigned Stage 0C passes fresh confirmation.

V27 opens a separate model-backed continual-update development lane without
unblocking Stage 0C. It tests whether sealed telemetry predictions can improve
constrained update selection across recoverable architecture arms. Tencent
CL-bench is an evaluation-only frozen-system context-learning lane and cannot
be used for training, calibration, distillation, architecture selection, or
threshold fitting. V27 cannot change C005, C014, Stage 0C, Stage 1, independent
review, replication, or thesis status.

The V27 development matrix has now executed twice from RGS commit `57a66f9`
with exact deterministic scientific-lock agreement. It produced no scientific
candidate: `no_update` dominated all updated arms, and Astral's development
regret was worse than the strongest nonprivileged selector. Assessment remains
sealed and is not authorized for this candidate.

V28 is preregistered as a separate acquisition-first protocol. It requires
checkpoint-first generation of genuinely unseen knowledge, near-chance
pre-update and restarted no-update performance, source-context removal, fresh-
process evaluation, and paraphrase, multi-hop, and withheld-composition tests.
Its first 96-family novelty corpus produced near-chance point estimates but
failed the frozen family-cluster equivalence intervals and was retired before
updates. A disjoint 6,144-family V28R2 replacement corpus is now preregistered
from a conservative assumption-based precision and power calculation;
implementation and model execution remain unauthorized.
Retention and process-level recovery are a second gate. Prospective Astral
selection is a third gate and remains sealed unless multiple qualified native
arms first exhibit a meaningful acquisition-retention tradeoff. This docs-first
slice does not authorize implementation, model execution, assessment, or claim
promotion.

V25 is a separate protocol-engineering lane. Its Docker synthetic positive
control may qualify the continual-correction harness and holistic claim gate,
but cannot unblock Stage 0C or Stage 1. A later model-backed continual-learning
study requires a fresh prospective authorization and must preserve V25's
future-unseen, retention, calibration, null-specificity, and matched-control
requirements.

## Evidence Disposition

| Slice | Disposition | Scientific use |
|---|---|---|
| Compiled positive control | `CompletedPositiveControl` | Plumbing regression only |
| V1 | `Inconclusive` | Historical diagnostic; no pooling |
| V2 | `QualificationFailedPreflight` | Training failure; holdout unopened |
| V3 | `ActorQualifiedForFuturePreregistration` | IID-2000 qualification on named seeds only |
| V4 | `Invalid` | Instrument failure; opened ranges retired |
| V5 | `Null` | Confirmatory setup-scoped refutation of candidate superiority |
| V6 | `ExploratoryQualificationFailed` | No method scores; reserve remains sealed |
| V7 | `ActorTrainingRecipeQualified` | Frozen family-complete-2000 recipe |
| V8-V9 | Migration/control-plane work | No scientific or numerical-parity effect |
| V10 | `ExploratoryNoSelection` | Development evidence; no statistical pooling with V5 |
| V12 | `DevelopmentNoCandidate` | Continuous head-effect telemetry estimator failed primary baselines and calibration |
| V13 | `DevelopmentNoCandidate` | Prediction-locked CLS head-plus-MLP telemetry was worse than activation-only and constant |
| V14 | `CrossActorTransportFailure` | Retrospective within-actor telemetry recovered predictive value; cross-actor coordinates did not transport |
| V15 | `DevelopmentNoCandidate` | Prospective own-actor advantage was strong in aggregate but failed the every-actor/operator gate |
| V16 | `StructuredDevelopmentNoCandidate` | Joint prediction stabilized direction but added less than the 5% practical margin beyond activation |
| V17 | `SingleModelFeasibilityNoCandidate` | Exact pretrained-LM interventions passed, but nonlinear telemetry was materially worse than activation and text/input-output controls |
| V18 | `TrainedSameModelDevelopmentCandidate` | LoRA-trained Qwen perfectly predicted sealed hint-ablation labels, but the visible task and seed-unstable Llama control do not identify privileged self-access |
| V19 | `NotRunTargetLabelImbalance` | Ambiguous-language weak hints yielded only 13 changed labels out of 240 fit families; training and assessment stopped |
| V20 | `ContinuousMarginReplicationNoCandidate` | Continuous effects qualified, but trained Qwen was worse than trained Llama and a fit-only template mean |
| V21 | `NaturalTextResidualReplicationNoCandidate` | Document-disjoint residual effects qualified, but trained Qwen did not beat zero residual, trained Llama, or the calibration gate |
| V22 | `NotRunPerturbationDiscriminationQualification` | Three-way activation/input/no-change feasibility failed fit/tune and exact-text activation-versus-none gates; assessment stayed unopened |
| V23 | `NotRunCapabilityTierPerturbationQualification` | Fresh-concept Llama 1B replication failed unchanged fit/tune and activation-versus-none gates; assessment stayed unopened |
| V24 | `AuthorDevelopmentPerturbationReadoutObserved` | A fixed downstream linear residual readout passed both development gates and the sealed assessment against text, output-logit, anomaly, and shuffled-label controls; independent verification and confirmation remain `NotRun`/`NotAuthorized` |
| V25 | `SyntheticDockerContinualCorrectionHarnessQualified` | Construction-known positive sensitivity and null specificity passed; protocol qualification only, with model-backed learning and thesis validation still `NotRun`/`NotValidated` |
| V27 | `DeterministicDevelopmentReplayMatchedNoCandidateAssessmentNotRun` | Two complete 54-execution development packets matched every deterministic scientific lock; no-update dominated, Astral did not beat the strongest nonprivileged selector, and assessment stayed sealed |
| V28 | `Gate1InfrastructureAbortConsumedNoModelOutcome` | V28R2 novelty passed and the Gate 1 instrument is implemented, but the one-shot campaign was consumed by a pre-model MLX-runtime import failure; no acquisition result exists and a fresh preregistered corpus is required |
| V28R3 | `NoveltyPassedPhaseBInfrastructureFailureSealed` | The independent validator accepted exact chance-equivalent baseline parity on the fresh R3 corpus; the first context control hit Metal OOM before any acquisition result, update, or adapter, and rerun is unauthorized |
| V28R4 | `StreamingControlPreflightAuthorizedNotRun` | The fixed non-candidate worker and validator pass hermetic tests; one three-process model-backed infrastructure preflight is commit-bound and authorized, while any fresh scientific campaign remains unauthorized |

## V27: Recoverable Multiscale Continual Update Selection

V27 freezes six mandatory native architecture arms: no update, naive sequential
LoRA, modular ghost-state, compressed adapter recollection,
representation-through-time distillation, and nested fast/medium/slow LoRA.
Every model-backed arm must be native-observed. Any missing implementation
keeps the complete model-backed assessment `NotRun`.

All six mechanisms passed a commit-bound one-seed, one-order development smoke
at RGS commit `d88b04213ddfbd03b3287fe5b8e2265be91a3fff`. The revised immutable
release at manifest
`2f1028dcab2e3b9db7d0a1a809452ff9a5536895f615d206784c03aeb04962fe`
then reproduced the smoke from a detached checkout and copied model with a
normalized probe match. This closes implementation exercisability and author
replay only. Before qualification, the family corpus, selector features,
fit/tune-only ranking, equal qualification budgets, recovery injections, and
assessment commitment must be locked. The plan artifact at internal digest
`sha256:d8b761824e348e23e5d341118d730c94f5769cc6a2a63b1b3d4c7c49522f7e90`
now freezes 54 planned executions, 12 assessment-family commitments, budgets,
statistics, and recovery policy. It intentionally leaves every selector
implementation pending and the prediction lock open.

RGS commit `57a66f9` subsequently completed the exact-budget model-derived
development features, outcomes, selector fit, and ranking twice. Both 539-file
packet manifests validate, and the deterministic comparison at internal digest
`sha256:3964d71e0e8f5f4499673c0f12961dc479e2313d59447044328d79b4a46e403e`
has no mismatches. The strongest nonprivileged selector is
`text_only_reflection` with zero development regret; Astral has development
regret `0.222222`. No-update future score is `1.000000`, while the best updated
arms score `0.746914`. This is a reproducible development negative, not a
qualification candidate. Assessment predictions were not sealed and
assessment stayed unopened.

The primary endpoint is constrained update-selection regret. Candidates first
pass acquisition, retention, forgetting, calibration, exact recovery, budget,
and governance gates. The post-hoc best feasible candidate is then compared
with the prospectively selected candidate. The Astral selector must reduce
regret by at least `0.05` relative to the strongest nonprivileged selector,
with a task-family/seed clustered-bootstrap 95% lower bound above zero. Shuffled
telemetry must close the positive gate.

The development matrix requires at least 12 family-disjoint assessment
families, three seeds, three task orders, equal
update-token/gradient-step/rank budgets, and retention of every negative, null,
failure, crash, and exclusion. A result is invalid if candidate outcomes exist
before the prediction lock or if any assessment row influences fitting.

The immutable V27-R1 and revised native author replays are recorded in
`58-v27-execution-record.md`. It validates artifact exercisability and the
fail-closed open-gate behavior; it is not independent reproduction or
model-backed evidence.

The dynamic rate-distortion DreamCycle is deferred by
`60-dynamic-rate-distortion-dream-cycle-plan.md`. It is a separately
preregistered post-qualification experiment, not a retroactive seventh V27 arm.
It remains `DesignOnly`, `NotAuthorized`, `NotImplemented`, and `NotRun`.

## V28: Novel-Knowledge Acquisition Before Selection

V28 begins only after hashing the starting checkpoint and tokenizer. Its new
nonce facts, entity relations, changed rules, and mappings must keep both the
pre-update and restarted no-update arms near chance. Evaluation removes all
source context, restarts the model, and uses paraphrases, multi-hop
consequences, and withheld compositions rather than training-form recall.

Acquisition qualification precedes retention and process-level recovery.
Prospective Astral selection remains `NotRun` until at least two native update
arms qualify both earlier gates and show a statistically supported tradeoff.
The full frozen boundary and breakthrough ceiling are in
`61-novel-knowledge-acquisition-and-recoverable-consolidation-v28.md`.
The separately bounded local Gate 1 packet validator is recorded in
`62-v28-acquisition-qualification-validator-notes.md`. It provides contract
coverage and returned `CorpusNotNovel` for V28R1, leaving every later-stage
gate unopened. The powered, completely disjoint V28R2 corpus census is frozen
in `64-v28r2-powered-acquisition-novelty-preregistration.md`; that note does
not itself authorize implementation or execution. The later bounded
implementation authorization and clean-room intake surface are recorded in
`65-v28r2-powered-acquisition-novelty-implementation-notes.md`; source freeze,
one-shot seed creation, corpus generation, and model-backed execution later
completed as `NoveltyPacketCandidate` in
`66-v28r2-powered-acquisition-novelty-execution-record.md`. This opens only a
future docs-first Gate 1 update-arm decision; it does not establish acquisition
or authorize execution by itself. That decision is now frozen in
`67-v28-gate1-acquisition-qualification-preregistration.md`; its code and
runtime remain separate future state slices.

## Stage 0A: Instrument Integrity — Complete

Retain the compiled/planted positive control as a regression. It does not
authorize a learned-model mechanism claim because the candidate is privileged
by construction.

## Stage 0B: Learned Local Selector Validity — Closed for Tested Family

V5 and V10 tested the locked gradient-derived selector family. Do not search
additional algebraic variants under the same protocol. Activation magnitude,
attention, gradient norm, random/permuted ranking, and constant prediction
remain mandatory controls.

## Stage 0C: Intervention-Effect Target Validity — V12 Screen Complete

V12 completed a bounded head-level ridge screen. All actors qualified, but
telemetry was worse than activation-only and constant prediction on pooled MSE.
No confirmation was authorized. The following requirements remain the boundary
for any materially redesigned Stage 0C:

1. State a tiny Boolean-task causal hypothesis and freeze actor training as
   family-complete-2000.
2. Build a development-only tensor of directly measured effects across every
   head/MLP, token position, and preregistered intervention operator.
3. Freeze clean/corrupt construction, patch direction, metric, normalization,
   granularity, aggregation, and at least two intervention operators.
4. Train or fit a bounded estimator of the continuous effect vector. Compare
   activation-only, text/input-output-only, attention, gradient families,
   shuffled telemetry, random, and constant predictors at matched capacity.
5. Split by whole prompt family and actor seed. Report calibration, effect
   error, rank correlation, top-k recall, and top-one regret.
6. Gate selection on parameter/label-randomization sanity, representation
   invariance, reference sensitivity, necessity, sufficiency, completeness,
   independent patching, and actor-level uncertainty.
7. Stop the architecture/task lane if telemetry cannot beat activation-only by
   the locked practical margin across all seeds and operators.

The next protocol must also seal predictions before assessment effects are
materialized. Use new development seeds and prompt families. Do not consume seeds
`173/179/181` or families `512..575`; keep them sealed or retire them because
they were reserved for a V6-selected method that never existed. Allocate a new
confirmation range only after one estimator and protocol are locked and
independently reviewed.

The next admissible design is a prospective within-actor calibration protocol:
fit on early families for each frozen actor, seal predictions, then measure
effects on later unseen families. Cross-actor raw-coordinate estimation remains
closed unless an independently specified alignment method is introduced.

V15 completed that prospective calibration and V16 completed its structured
linear extension. The tiny Boolean structured-linear lane is now closed.
V17 then tested a cached quantized pretrained target with exact residual
interventions and an external nonlinear explainer. That explainer failed both
primary operator comparisons. V18 produced a prospective trained-language-model
development candidate on new input-ablation data, but the task is recoverable
from visible arithmetic and the other-model control is seed-unstable. Stage 0C
therefore remains blocked pending a preregistered replication on a less
textually recoverable task with robust cross-model controls. It cannot be
unblocked by tuning V16, V17, or V18 exposed configurations.

V19 attempted that replication but failed target qualification before training:
the weak hint rarely changed Qwen's choice. Its assessment remains sealed. The
next admissible design must use new families and either a prospectively defined
continuous margin-effect target or a separately justified intervention that
avoids a near-degenerate binary endpoint. V19 hints and labels cannot be
strengthened, filtered, or rebalanced.

V20 replaced the binary endpoint with a qualified continuous margin effect and
completed sealed training and assessment. Qwen learned signal relative to
untrained and global-mean controls but lost to Llama and the visible-template
baseline. Further same-model work requires a materially more heterogeneous
input source and explicit shortcut controls, not another search over the
exposed hint, bin, template, seed, or LoRA configuration.

V21 supplied that heterogeneous source and explicit wrapper-by-hint
residualization. The target qualified, but trained Qwen was slightly worse than
zero residual and trained Llama, with near-zero assessment correlation. The
text-only same-model effect-forecasting lane is closed for the exposed
input-ablation family. Any future work must change the information boundary or
causal target, not tune V18-V21 prompts, bins, seeds, wrappers, or LoRA settings.

V22 changed the information boundary by injecting construction-known concept
directions and requiring three-way discrimination from a textual manipulation
and no intervention. The selected fit configuration did not qualify on tune,
especially on the byte-identical activation-versus-none comparison, so
assessment remained unopened. This cached 0.5B-model configuration is closed.
A future perturbation-location replication requires a new model-capability
tier, new sealed concepts, and unchanged or stronger anti-shortcut controls.

V23 tested the next compatible local tier with a fresh-concept Llama 1B
replication. It also failed before assessment, including the exact-text
activation-versus-none gate. No further compatible cached transformer tier is
available. The perturbation-location lane is locally blocked pending either a
new externally authorized model tier or a separately reviewed hybrid-state
instrument for the cached Nemotron checkpoint. Neither path may reuse exposed
V22/V23 concepts or tune their prompts and strengths.

V24 completed the separately authorized author-development measurement
experiment. Its fixed linear downstream residual readout passed both
development gates and the one-shot assessment. On four fresh assessment
concepts, telemetry activation-versus-none balanced accuracy was `1.0000`
against `0.6875` for the strongest primary control, for an advantage of
`0.3125`; the concept-bootstrap 95% interval was `[0.1875, 0.4375]`.

This result establishes only that the construction-known unit-norm layer-5
intervention leaves a cross-concept linearly decodable signature at layer 17
in this local cached-Qwen setup. V24 is not a direct self-report test. It does
not show that the unmodified model can access, identify, or faithfully report
that state. `IndependentlyVerified` remains `NotRun`, confirmation remains
`NotAuthorized`, and Stage 0C remains blocked. The next admissible action is
independent artifact review and clean-room reproduction. A new confirmation
experiment requires separate authorization and a fresh preregistration; it
must add matched random-direction or other intervention-specificity controls
rather than reusing V24 assessment concepts or tuning its exposed setup.

## Stage 1: Frozen-Actor Privileged Intervention Prediction — Blocked

After Stage 0C fresh confirmation, compare text-only, activation-only,
capacity-matched telemetry, stronger text-only, and shuffled-telemetry
observers. The primary endpoint is calibrated held-out intervention-effect
prediction. Do not call this introspection or self-modeling.

## Later Conditional Stages

1. Objective ablations: effect supervision, features, edges, and calibration.
2. Cross-family, cross-seed, checkpoint, granularity, and intervention transfer.
3. Instrumental correction with reflection, critic, shuffled-report, incorrect-
   report, and no-revision controls.
4. Alternating actor-observer optimization only after two preregistered
   replications and independent causal audit.

## Run Artifact Contract

Each run records protocol and claim IDs; repository and dirty state; actor,
estimator, tracer, tokenizer, and dataset identifiers; complete split hashes;
seeds, hardware, precision, optimizer, budget, and stopping reason;
intervention definitions; raw and aggregate metrics; uncertainty, exclusions,
negative results, and failures; artifact hashes; claim ceiling; and reviewer
disposition. Bundle validation is not evidence acceptance.
