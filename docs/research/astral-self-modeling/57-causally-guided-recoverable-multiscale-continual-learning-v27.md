# Causally Guided Recoverable Multiscale Continual Learning V27

State slice: `astral-rgs-nested-recoverable-update-v27`.

Status: `Preregistered / DeterministicDevelopmentReplayMatched /
DevelopmentNoCandidate / AssessmentSealedNotAuthorized /
ModelBackedAssessmentNotRun`.

## Research question

Can a prospectively locked telemetry selector choose a recoverable model update
with lower constrained regret than text-only, output-only, activation-only,
random, shuffled, incorrect-report, and strongest-fixed-arm selectors?

This question is distinct from Stage 0C. V27 tests update selection over an
external RGS execution system; it does not establish privileged self-access,
introspection, or causal self-modeling.

## Repository boundary

Recoverable Ghost States owns model training, candidate updates, forked model
states, PCSM authorization, rollback journals, raw task observations, and
content-addressed execution bundles. Astral owns the preregistration,
prediction-lock contract, cross-repository packet validation, claim ledger, and
claim ceiling. Astral never imports an unpinned local RGS path as evidence.

## Frozen arms

1. `no_update`
2. `naive_sequential_lora`
3. `modular_ghost_state`
4. `compressed_adapter_recollection`
5. `representation_time_distillation`
6. `nested_multiscale_lora`

All six arms must declare `native_observed` before assessment. An emulation may
test the validator but cannot fill a scientific cell. A missing, emulated, or
`not_run` arm keeps the complete assessment `NotRun`.

RGS commit `d88b04213ddfbd03b3287fe5b8e2265be91a3fff` implements all six
mechanisms with deterministic pre-conversion seeding and content-addressed
adapter metadata. The commit-bound Qwen 0.5B development smoke passed with zero
method failures, and the revised immutable release reproduced it from detached
source and a copied model with an exact normalized probe match. That smoke used
one seed, one task order, three examples, and six optimizer steps per updated
arm. It establishes native mechanism exercisability and author replay only. It
does not fill any of the 54 qualification executions, open assessment, select
hyperparameters, or support C047/C048.

## Frozen selectors

- Astral telemetry selector;
- text-only reflection;
- output-only critic;
- activation-only predictor;
- shuffled telemetry;
- incorrect or permuted telemetry;
- random update;
- strongest fixed development arm;
- no update;
- post-hoc oracle, used only as a non-actionable regret upper bound.

The pre-assessment plan digest
`sha256:d8b761824e348e23e5d341118d730c94f5769cc6a2a63b1b3d4c7c49522f7e90`
freezes the selector feature schemas but truthfully marks every selector
implementation `PendingDevelopmentImplementation`. The strongest
nonprivileged selector is `PendingDevelopmentRanking`; the prediction lock is
`NotLockedSelectorsPending`. Assessment cannot open in this state.

RGS commit `57a66f9` implements the single capacity-matched estimator family,
model-derived feature extraction, exact-budget 54-execution development matrix,
and deterministic replay comparator. It consumed only development and tuning
families, produced the strongest-nonprivileged ranking, and left assessment
content and outcomes absent. It does not retroactively change the immutable
plan; the successor transition records the completed development state.

Before assessment outcomes exist, every selector seals predicted future-unseen
reward, protected-retention change, calibration change, recovery success and
loss, cost, and governance admissibility for every candidate. All candidates
then execute from identical forked model-state hashes.

## Primary endpoint

Candidates that violate any frozen gate are infeasible. For each assessment
family, seed, and task order:

```text
selection_regret =
  post_hoc_best_feasible_future_unseen_score
  - prospectively_selected_candidate_score
```

The primary scientific contrast is:

```text
regret(strongest nonprivileged selector) - regret(Astral selector)
```

Qualification requires mean improvement at least `0.05`, a task-family/seed
clustered-bootstrap 95% lower bound above zero, maximum protected-retention
drop at most `0.02`, Brier degradation at most `0.02`, exact recovery success
`100%`, recovered score within `0.01` of the pre-failure state, zero hard
governance violations, shuffled-telemetry specificity, and null telemetry
advantage at most `0.02`.

Acquisition, average final accuracy, backward transfer, forgetting, forward
transfer, calibration, recovery latency, storage, update tokens, gradient
steps, wall time, peak memory, and safety are reported separately. No weighted
aggregate may conceal a failed causal, calibration, retention, safety,
recovery, budget, or governance gate.

## Dataset and split rules

The model-backed stream is newly generated, repository-owned, license-bound,
and split by complete task family. Assessment families never participate in
training, architecture selection, threshold fitting, calibration, or stopping
decisions. At least 12 assessment families, three seeds, and three task orders
are required. Family identifiers are bound by canonical hashes so aliases
cannot cross development, tuning, and assessment.

The primary architecture family compares every candidate arm with naive
sequential LoRA. At least one must improve future-unseen score by `0.05` with a
paired family/seed 20,000-replicate basic-bootstrap lower bound above zero and
Holm-adjusted one-sided alpha `0.05`. Only then may C048 compare Astral with
every confirmatory nonprivileged selector under the same inference plan.
Shuffled, wrong-report, and null telemetry form a separate Holm-corrected
specificity family whose upper bounds must each be at most `0.02`.

Tencent CL-bench is a separate terminal assessment. Its custom license permits
evaluation and benchmarking but forbids training, fine-tuning, calibration,
distillation, adaptation, and every parameter update. V27 therefore evaluates
only an already frozen system on CL-bench. CL-bench cannot select the V27 arm
or selector.

## Stop rules

- Stop before assessment if source, commit, tree, model, dataset, license,
  split, runtime, prediction lock, or artifact provenance is incomplete.
- Invalidate answer mappings, route cues, task-family overlap, assessment-label
  access, or candidate outcomes observed before the lock.
- Mark unequal-budget arms `NotComparable`; do not repair parity post hoc.
- Stop the selector claim unless Astral beats the strongest nonprivileged
  selector and strongest fixed arm.
- Stop the architecture claim unless a native arm beats naive sequential LoRA
  under every mandatory gate.
- Retain qualification failures, nulls, crashes, exclusions, and negative
  replications.

## Development execution result

Two complete 54-execution packets from RGS commit `57a66f9` passed their
539-file manifests and matched every deterministic source, plan, model,
candidate-execution, feature, outcome, fit, ranking, and transition lock. The
comparison digest is
`sha256:3964d71e0e8f5f4499673c0f12961dc479e2313d59447044328d79b4a46e403e`.

The result is a development negative. `no_update` achieved mean future score
`1.000000`; the best updated arms achieved `0.746914`. The strongest
nonprivileged selector, `text_only_reflection`, had zero development regret;
Astral had `0.222222`. Consequently, the development analogue of the primary
Astral advantage is `-0.222222`, below the required positive `0.05` margin.
Every updated arm also exceeded the final `0.02` Brier-degradation ceiling in
at least one development cell.

The assessment prediction lock was not sealed, assessment stayed unopened,
and no C047 or C048 assessment test was run. The development recovery value is
only an in-memory byte corruption roundtrip, not the final injected
process-level recovery experiment. The full artifact record and retained
nondeterministic-cost defect are in `58-v27-execution-record.md`.

## Claim ceiling

The maximum author-development classification is
`LocalAuthorDevelopmentCausallyGuidedRecoverableMultiscaleContinualLearningCandidateRequiresFreshReplicationAndReview`.
It is not confirmed continual learning, solved continual learning, autonomous
self-improvement, introspection, self-modeling, Stage 0C, Stage 1, independent
verification, replication, production readiness, or benchmark dominance.

## Primary source basis

- Self-Net, compressed weights stored in learned weights:
  <https://arxiv.org/abs/1805.10354>
- CaSSLe, representation-time distillation for continual self-supervision:
  <https://arxiv.org/abs/2112.04215>
- Nested Learning, multilevel optimization and update-frequency framing:
  <https://arxiv.org/abs/2512.24695>
- Tencent CL-bench, inference-time context-learning evaluation:
  <https://arxiv.org/abs/2602.03587>

These sources motivate distinct arms and controls. They do not supply evidence
that Astral or RGS has reproduced the papers' results.
