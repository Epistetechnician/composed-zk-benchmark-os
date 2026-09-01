# Oak Lab constrained update policy V4 protocol

State slice: `oaklab-experience-learning-constrained-update-policy-v4`

Status: `frozen_pending_independent_review`

Claim ceiling: `LocalDevelopmentOakLabConstrainedUpdatePolicyV4ProtocolOnly`

## Decision

V4 does not repair V3's isolated-update causal model. It changes the object of
study. The treatment is the complete sequential learner policy, including all
carryover from earlier apply/skip decisions. The assessment directly runs the
locked policy and fixed batch-one SGD from identical zero model states on the
same immutable ordered stream.

For family `f`, the scientific estimand is

`tau_f = E_seed[sum_t loss_t(fixed SGD) - sum_t loss_t(locked policy)]`.

Every loss is half-squared prediction error measured before that row's action.
The primary paired statistic uses the per-seed mean across family streams of

`D = log((candidate cumulative loss + 1e-12) / (SGD cumulative loss + 1e-12))`.

Negative `D` favors V4. This is a direct policy-level paired comparison, not a
claim that any individual update has an isolated causal effect.

## Mechanism

The model is fixed-rate linear SGD. A six-weight linear action-value controller
chooses `apply` or `skip` from three causal features: intercept, clipped
pre-update loss, and declared event density. Fit uses exact domain-separated
epsilon exploration. The controller is trained with the true-online
Sarsa-lambda recurrence and a bounded dual multiplier for an apply-rate budget
that depends only on model dimension. The per-row budget is
`min(0.75,max(0,(3d-8)/(3d+3)))`, so the dense model work saved by skipping
covers all eleven compiled-controller operations. Tune and assessment freeze
the controller, compile its two action blocks into three margin coefficients,
and act greedily; ties apply.

Eligibility traces are used because the effect of an update is visible in
later pre-update losses, while the policy-level assessment makes that full
carryover part of the treatment. True-online temporal-difference learning is
an established exact online forward/backward-view construction, but its use
here does not make the V4 controller or its outcome a published theorem. See
[True Online TD(lambda)](https://proceedings.mlr.press/v32/seijen14.html) and
[True Online Temporal-Difference Learning](https://www.jmlr.org/papers/v17/15-599.html).
The resource budget is a small declared Lagrangian controller, informed by the
constrained-policy literature rather than claimed equivalent to any published
algorithm; see the [primal-dual constrained-MDP framework](https://proceedings.mlr.press/v180/jain22a.html).

## Fresh cohorts and streams

Fit seeds are `4000..4015`, tune seeds are `5000..5015`, and assessment seeds
are `6000..6047`. Each trajectory has 252 ordered rows. Each cohort and stream
uses an independently initialized, implementation-specified SplitMix64 stream.
The machine protocol freezes integer arithmetic, uniform conversion, bounded
normal approximation, every generator equation, target, dimension, event
definition, oracle feature, and change point.

Primary families are:

- predictable/noise: sparse predictable and noisy-MNIST-like distractors;
- delayed reward: a nine-row cue/reward sequence whose mapping changes midway;
- drift: feature-relevance change and two piecewise coefficient shifts;
- event: sparse event polarity with a midpoint mapping reversal.

An all-unlearnable pure-noise stream is a mandatory falsification control, not
a primary publication family. Assessment panel bytes may not be materialized
until the tune lock is independently accepted.

## Exact training and locking

Fit processes streams, seeds, and rows in fixed ascending order. The model is
reset to zero for each stream-seed trajectory; controller weights and the dual
multiplier persist across fit trajectories, while the eligibility trace and
old action value reset. The last row supplies a terminal reward for the prior
action; neither candidate nor reference updates on that row.

Tune starts every model from zero and freezes the fit controller. It performs
no hyperparameter selection. The lock binds the protocol and review digests,
implementation and runtime identities, panel manifests, exact binary64
controller values, dual value, matched-random probability, accounting schema,
fit/tune receipts, every tune gate, empty trace state, independent validator,
and independent lock decision. Assessment reconstructs zero models and the
locked controller; no fit or tune model weights are reused.

## Primary statistics and power

The 48 assessment seed pairs are tested with the exact normal-approximation
paired statistic frozen in the machine protocol. Four two-sided family tests
use Holm correction with a fixed family and tie order. Zero variance has an
explicit finite result. A family must have negative mean `D` and adjusted
`p<=0.05`. At least two families must qualify, including delayed reward or
drift.

At worst-case Holm alpha `0.0125`, 48 pairs, and standardized effect `0.5`, the
frozen normal approximation has power `0.8330770040094296`. This power claim
applies only to the primary family log-loss ratio, not adaptation, mechanisms,
resources, or the composite publication gate.

## Temporal and resource gates

Adaptation lag is algorithmic: use the median of 16 losses before each declared
shift, a recovery threshold of `1.10` times that baseline, two consecutive
eight-row recovery windows, and fixed right censoring. Candidate mean lag must
be no more than two rows worse in every qualifying temporal family and strictly
better in at least one delayed-reward or drift family.

Resource accounting separates model forward, gradient, update, parameter
writes, controller inference/training, scalar controls, events, logical bytes,
latency, and joules. Assessment requires at most 75 percent of fixed-SGD model
writes, no more total declared operations, no replay, no hidden accumulation,
and at most 64 additional logical state bytes. The deployed compiled controller
is three binary64 values, or 24 bytes. Fit-only controller and trace overhead is 112 bytes and must remain
within the separate 128-byte ceiling. Measured energy is never inferred from
operation counts.

## Falsification

Mandatory arms are fixed SGD, V4, lambda zero, no dual, matched random,
reward-shifted training, always skip, noise floor, oracle-feature SGD, and a
tune-only H=8 twin-trajectory oracle. The oracle duplicates state only to test
whether the controller margin predicts actual apply-versus-skip utility; its
cost is excluded from candidate deployment resources and separately reported.
V4 must beat matched random and the myopic trace ablation, beat always skip on
predictable signal, retain oracle-over-noise-floor sanity, and prevent the
reward-shifted control from passing the candidate gate.

## Stop boundary

Independent review of the exact bytes is required before implementation. A
rejected review terminally closes V4. Accepted review permits only additive
V4 implementation, hermetic equation and tamper tests, and independent
implementation validation. Tune failure or lock rejection closes V4 before
assessment. Synthetic failure closes V4 without retuning. A synthetic
candidate still does not authorize real execution.

Real work requires a separate review, fresh custody and backends, an exact V4
campaign manifest, raw privileged power telemetry, a new digest-bound energy
receipt, and independent validation. No V2 energy evidence is eligible. The
plasticity guard and V1-V3 remain closed. Astral remains isolated.

Machine-readable contract:
`experiments/experience_learning/constrained_update_policy_v4_protocol.json`.
