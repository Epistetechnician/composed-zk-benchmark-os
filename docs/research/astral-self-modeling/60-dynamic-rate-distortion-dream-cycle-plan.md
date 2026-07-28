# Dynamic Rate-Distortion DreamCycle Research Plan

State slice: `astral-rgs-nested-recoverable-update-v27`.

Status: `DesignOnly / PostQualification / NotAuthorized / NotImplemented / NotRun`.

Decision date: `2026-07-27`.

## Decision

Complete `astral-rgs-v27-model-backed-qualification-r1` before implementing a
DreamCycle system end to end. V27 first establishes whether the scientific
instrument, native continual-update arms, prospective selector comparison, and
recovery gates work on a real model. DreamCycle is a separately preregistered
post-qualification branch, not a seventh arm added retroactively to V27.

This ordering is mandatory because V27 already has a frozen six-arm contract
and an opened external diagnostic. Changing its required arms or primary
endpoint would destroy protocol identity. Building compression, replay,
counterfactual generation, multiscale promotion, and Astral selection at once
would also make a negative result uninterpretable.

The decision reverses only if an independent methodological review finds that
V27 cannot measure the proposed rate-distortion endpoint without implementing
DreamCycle first. Convenience, expected performance, or available compute are
not reversal conditions.

## Ordered program

### 1. Close and freeze V27-R1

Before model-backed assessment:

- create clean Astral and RGS commits without absorbing unrelated dirty files;
- pin Python, MLX or Torch, model, tokenizer, precision, operating system, and
  hardware identities;
- bind source trees, model files, datasets, licenses, splits, and commands in a
  sorted content manifest;
- implement the complete selector matrix and task-family/seed clustered
  bootstrap required by C048;
- enforce the stricter Astral retention, calibration, exact recovery, budget,
  null-specificity, and governance gates;
- add hierarchical comparison handling and adversarial packet tests;
- seal every prediction and configuration before candidate outcomes exist;
- provide one fail-closed clean-checkout replay command.

### 2. Run the native V27 qualification matrix

Execute the frozen six arms over at least three seeds and three task orders,
for at least 54 model-backed candidate runs. Candidate outcomes are generated
once per seed and order and shared by all prospectively locked selectors.
Missing or emulated arms remain `NotRun`; assessment data cannot repair them.

V27 keeps constrained update-selection regret as its primary endpoint. No
DreamCycle result may be pooled with, inserted into, or used to reinterpret the
V27 assessment.

### 3. Apply the DreamCycle authorization gate

After V27 produces a mechanically valid positive, null, or negative result:

- authorize DreamCycle if V27 qualifies a recoverable model-backed substrate;
- alternatively authorize a bounded redesign if retained V27 failure evidence
  specifically identifies memory capacity, replay quality, consolidation, or
  recovery cost as the limiting mechanism;
- do not authorize DreamCycle when V27 is invalid, incomplete, underpowered, or
  fails for an unrelated measurement, leakage, calibration, or governance
  reason;
- never tune DreamCycle on the opened V27 assessment. Allocate new development
  families and a new sealed assessment.

### 4. Build DreamCycle as a separate experiment

Only after authorization, RGS may implement the offline controller and model
updates. Astral may preregister candidate-effect predictions and validate the
result packet. This design note does not authorize that source or runtime work.

### 5. Confirm the combined system

A qualifying DreamCycle candidate enters a later fresh confirmation alongside
the strongest V27 arm and contemporary reproducible baselines. Confirmation
requires new task families, seeds, task orders, checkpoints, model families,
and an independently reviewed preregistration.

## Proposed system boundary

DreamCycle is an offline consolidation controller, not literal sleep,
consciousness, or autonomous promotion.

1. `WakeCapture`: admit only authorized, provenance-bound experiences,
   corrections, failures, and telemetry.
2. `NremConsolidate`: replay genuine experiences, deduplicate predictable
   state, preserve rare tails, and propose compression or distillation.
3. `RemExplore`: create provenance-labelled counterfactuals and failure
   perturbations in quarantine. Generated samples are hypotheses, not truth.
4. `AstralPredict`: seal each candidate's expected acquisition, retention,
   calibration, recovery, cost, and governance effects before evaluation.
5. `RgsForkEvaluate`: execute candidates from byte-identical state hashes and
   record PCSM decisions, resource use, rollback, and replay.
6. `PromoteOrRecover`: promote a bounded adapter or memory artifact only after
   every gate passes; otherwise restore the immutable recovery anchor.

Closed hosted-model APIs can support only external memory, prompt, skill, and
tool-state consolidation. Parameter or adapter promotion requires a legally
usable open-weight or explicitly fine-tunable model.

## Compression surfaces

The first implementation should compress replay memory and adapter deltas.
Activation traces and optimizer state are later ablations because they add
measurement and recovery complexity.

Never apply lossy compression to source manifests, licenses, assessment seals,
prediction locks, raw decision journals, content hashes, reviewer records, or
immutable recovery anchors.

Each admitted item receives a fit-only priority derived from:

```text
priority =
    novelty
  + prospective_causal_utility
  + interference_risk
  + recovery_value
  + protected_tail_rarity
  - provenance_risk
  - redundancy
```

The coefficients, normalization, missing-value behavior, and tie-breaking rule
must be frozen before assessment. Entropy or surprise alone is insufficient:
noise can be high-entropy, while rare low-frequency observations can be
scientifically or operationally important.

## Primary endpoint

DreamCycle uses a distinct rate-distortion endpoint:

```text
minimum_verified_bytes =
  minimum retained replay-plus-update bytes among candidates satisfying every
  acquisition, retention, forgetting, calibration, exact recovery, safety,
  budget, provenance, and governance gate
```

Lower is better. A candidate with fewer bytes but any failed guard is
infeasible. A weighted score cannot compensate for distortion, rare-tail loss,
failed recovery, provenance failure, or a governance violation.

The scientific contrast is the byte reduction relative to the strongest
matched non-Astral compression baseline. The practical margin, uncertainty
method, minimum seeds, task orders, and power target must be selected from
development data and independently reviewed before the new assessment is
created.

Constrained selector regret remains a secondary diagnostic in this branch and
the primary endpoint in V27. The two endpoints are never pooled.

## Proposed arms

1. `no_sleep_no_compression`
2. `replay_no_compression`
3. `fixed_uniform_compression`
4. `adaptive_replay_compression_nonastral`
5. `dynamic_rate_distortion_nrem_only`
6. `dynamic_rate_distortion_full_without_astral`
7. `dynamic_rate_distortion_full_with_astral`
8. `dynamic_rate_distortion_shuffled_astral`

All arms receive matched source data, replay opportunities, candidate-update
budgets, and storage ceilings. Compute-matched and storage-matched comparisons
are reported separately when both cannot be equal simultaneously.

## Mandatory mechanism ablations

- remove compressed adapter recollection;
- remove representation-time distillation;
- collapse fast, medium, and slow update clocks;
- remove REM counterfactual generation;
- replace REM samples with matched random samples;
- remove Astral telemetry;
- shuffle or falsify Astral priorities;
- replace RGS recovery with ordinary checkpoints;
- vary failure timing, task boundaries, tail rarity, and corruption class;
- compare lossless, quantized, factorized, distilled, and reconstruction-based
  storage at matched byte budgets.

A combined-system win does not establish that every named component caused the
gain. Only the corresponding randomized or factorial contrast may support a
component-level claim.

## Data and safety rules

- Preserve a fixed quota of authoritative non-generated data in every replay
  cycle; recursive generated-only learning is prohibited.
- Track real, transformed, generated, human-corrected, and externally sourced
  records as distinct provenance classes.
- Exclude Tencent CL-bench and CL-bench Life from capture, replay, compression
  selection, calibration, distillation, and parameter updates. They remain
  terminal frozen evaluations only.
- Apply privacy, secret, license, retention, and deletion policy before an
  experience enters any memory tier.
- Never allow the candidate model, DreamCycle controller, or author-side agent
  to waive a failed promotion gate.
- Retain negative cycles, rejected candidates, compression failures, tail-loss
  events, model-collapse indicators, and recovery failures.

## Stop rules

- Stop before DreamCycle implementation while V27 source, validator, runtime,
  native arms, or clean replay remains incomplete.
- Stop before assessment if any priority coefficient, compression codec,
  memory quota, synthetic-data ratio, threshold, or selector remains adaptive.
- Stop the compression claim if the strongest matched baseline uses fewer
  bytes at the same gates or if uncertainty includes the locked null margin.
- Stop the continual-learning claim after any protected-retention,
  calibration, recovery, rare-tail, safety, budget, provenance, or governance
  failure.
- Stop recursive REM training if generated-data share exceeds its frozen cap or
  any tail-coverage or collapse sentinel fires.
- Stop confirmation unless the result survives new data, checkpoints, model
  families, independent artifact reproduction, and independent implementation.

## Claim boundary

This plan adds no claim-ledger entry and changes no V27 status. It does not
authorize DreamCycle implementation, model training, assessment creation or
opening, confirmation, Stage 0C, Stage 1, independent verification, benchmark
submission, or evidence promotion.

Even a positive later result could support only a benchmark- and setup-scoped
recoverable dynamic rate-distortion continual-memory claim. It would not prove
optimal compression, solved continual learning, autonomous self-improvement,
introspection, self-modeling, consciousness, production readiness, or universal
state-of-the-art performance.

## Primary source basis

- Self-Net, continual compressed self-modeling:
  <https://arxiv.org/abs/1805.10354>
- CaSSLe, representation-through-time distillation:
  <https://arxiv.org/abs/2112.04215>
- Nested Learning, multilevel optimization and update frequencies:
  <https://arxiv.org/abs/2512.24695>
- Sleep-like unsupervised replay:
  <https://www.nature.com/articles/s41467-022-34938-7>
- Memory replay with adaptive data compression:
  <https://openreview.net/forum?id=a7H7OucbWaU>
- Compressed activation replay:
  <https://arxiv.org/abs/2010.02418>
- Recursive generated-data model-collapse risk:
  <https://www.nature.com/articles/s41586-024-07566-y>

These sources motivate the design and baselines. They do not validate Astral,
RGS, DreamCycle, the proposed priority function, or the combined system.
