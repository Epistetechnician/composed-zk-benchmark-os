# Docker Closed-Loop Correction Simulation V25

State slice: `astral-docker-closed-loop-correction-simulation-v25`.

Status: `Preregistered / AssessmentUnopened`.

Execution disposition: see
[V25 execution record](54-v25-execution-record.md). The preregistration above
remains the frozen pre-assessment contract.

## Purpose

V25 tests whether the proposed continual-correction measurement and validation
pipeline can distinguish a construction-known telemetry mechanism from matched
controls and reject the same mechanism in a null world. It is a protocol
positive control and specificity check. It is not a language-model experiment.

V24 established only that a fixed downstream linear readout could distinguish
an already-applied activation intervention in one author-run,
four-assessment-concept setup. V25 neither changes V24 nor treats V24 as
evidence of self-correction.

## Frozen question

Under a deterministic stream of synthetic binary tasks, does a task-local
correction policy supplied with construction-known causal telemetry improve
reward on future unseen examples more than the strongest preregistered control,
while preserving prior-task reward and calibration? Does the same gate remain
closed when telemetry is independent of the target mechanism?

## Claim ceiling

The maximum positive classification is
`SyntheticDockerContinualCorrectionHarnessQualified`.

It means only that the containerized harness detects its planted mechanism and
rejects its null counterpart under the frozen protocol. It does not establish
language-model continual learning, privileged model access, introspection,
self-modeling, Stage 0C, Stage 1, general self-improvement, or independent
replication.

## Synthetic actor and stream

- Actor dimension: `5`.
- Seeds: `2501, 2503, 2507, 2521, 2531, 2539`.
- Tasks per seed: `16`.
- Adaptation examples per task: `8`.
- Future unseen examples per task: `48`.
- Fixed replay examples per prior task: `16`.
- Update slots per condition and task: `8`.
- Bootstrap draws: `5000` over seed-task cells.
- Worlds: `positive_control` and `null_control`.

Each task has a construction-known target direction. The frozen actor contains
only the shared base direction. Task-local adapters are initially zero and are
stored separately, so the protocol can measure acquisition and prior-task
retention without parameter interference being hidden.

Positive-control telemetry reports the task direction with fixed deterministic
measurement noise. Null-world telemetry is generated from an independent
direction. Labels are available only for the eight adaptation examples. All
future and replay examples are disjoint deterministic draws.

## Conditions

1. `frozen`: no update.
2. `reflection`: a task-local scalar error correction.
3. `critic`: a task-local intercept learned from adaptation outcomes.
4. `ordinary_update`: bounded online logistic updates from visible examples and
   labels, without telemetry.
5. `telemetry`: the frozen telemetry policy.
6. `shuffled_telemetry`: another task's telemetry under the same update budget.
7. `incorrect_telemetry`: sign-inverted telemetry.
8. `random_direction`: norm-matched deterministic random telemetry.

The primary controls are all conditions except `telemetry`. The strongest
control is selected once by aggregate positive-world future reward, after which
paired seed-task differences are bootstrapped against that fixed condition.

## Primary metric

For each seed-task cell:

\[
\Delta_{future} =
R_{future}(telemetry)-R_{future}(strongest\ control)
\]

The primary statistic is the mean paired difference. Higher is better.

## Frozen positive-world gates

All gates must pass:

- telemetry future accuracy is at least `0.75`;
- mean paired advantage over the strongest control is at least `0.05`;
- the deterministic bootstrap 95% lower bound is greater than `0`;
- maximum prior-task replay accuracy loss is at most `0.02`;
- telemetry Brier score is no more than `0.02` worse than the strongest
  control;
- raw observation census, task split, update budget, and configuration contract
  validate exactly.

## Frozen null-world specificity gate

The positive-world gate must not pass in the null world. In addition, null-world
telemetry advantage over its strongest control must be no greater than `0.02`.

Qualification requires both positive sensitivity and null specificity.

## Ordering and sealing

1. Commit the protocol, source, tests, Dockerfile, and contracts.
2. Build with the digest-pinned base image and network disabled.
3. Run the container with no network, a read-only root filesystem, dropped
   capabilities, bounded memory, CPU, and processes, and only the
   caller-selected artifact parent writable.
4. Write raw observations, replay checks, configuration, runtime identity, and
   results before the artifact manifest.
5. Content-address the artifact by the manifest digest.
6. Validate by recomputing every aggregate and gate from raw records.
7. Append the execution disposition without deleting the preregistered row.

The assessment is the single complete execution of both worlds. Failed runs,
negative classifications, and validator failures are retained outside the
repository.

## Holistic claim gate

The V25 pipeline must enumerate every claim ID in the append-only Astral claim
ledger and classify its current evidence state. It fails closed on missing,
duplicate, or unexpectedly promoted claims. A mechanically valid pipeline may
still report `ThesisNotValidated` when required model-backed, causal,
independent, or replication evidence is absent.

## Stop rules

- Do not change thresholds after execution begins.
- Do not replace the null world after seeing results.
- Do not interpret a planted positive control as empirical support for model
  self-improvement.
- Do not continue to a model-backed continual-learning experiment unless V25
  qualifies mechanically and a separate prospective state slice is authorized.
