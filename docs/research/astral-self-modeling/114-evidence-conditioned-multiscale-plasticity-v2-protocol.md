# Evidence-conditioned multiscale plasticity v2 protocol

Date: 2026-08-28.

State slice: `astral-evidence-conditioned-multiscale-plasticity-v2`.

Status: `SyntheticFactorialExecuted / ModelBearingExecutionNotAuthorized`.

## Objective

Test whether evidence-conditioned admission and bounded multi-timescale
scheduling improve continual adaptation in an exact synthetic learner. The
experiment is a controller test, not a claim about transformer internals or
Astral self-modeling.

## Learner and ground truth

The learner has a six-dimensional parameter vector initialized at zero. Every
shard target is generated from a frozen seed-derived formula around a known
protected anchor. The loss is the exact quadratic

`L(theta, target) = mean((theta - target)^2) / 2`.

For learning rate `eta`, the exact update is

`theta_next = theta + eta * (target - theta)`.

The update delta, post-update parameters, protected-task interference, and
held-out loss are all mechanically derived. Interference is the nonnegative
increase in protected anchor and previously committed fit-task loss caused by
the candidate update. There is no learned model, stochastic learner noise, or
hand-authored gain field.

## Frozen factorial

The complete panel is 4 x 2 x 4:

1. `fixed_cadence`: all updates admitted, no wave;
2. `adaptive_verification`: taxonomy-conditioned verification/admission, no
   wave;
3. `wave_scheduling`: all updates admitted, bounded sine/cosine scheduling;
4. `adaptive_wave`: taxonomy-conditioned admission plus bounded scheduling.

Each mode is crossed with `deterministic` and `bounded_stochastic` scheduling,
then with `oracle`, `noisy`, `shuffled`, and `absent` taxonomy. The stochastic
arm is seeded and bounded; it is not uncontrolled learner randomness.

Each cell has preregistered replicate seeds `20260828`, `20260829`, and
`20260830`, and order seeds `4701`, `4702`, and `4703`. Each run has exactly
24 fit shards, 12 tune shards, and 12 assessment shards. Fit, tune, and
assessment targets are generated from distinct split namespaces and their
digests are retained in the aggregate report.

## Endpoint and guards

The single primary endpoint is held-out adaptation improvement after the fixed
24-update budget:

`mean_assessment_loss_at_zero - mean_assessment_loss_after_fit`.

Hard guards are forgetting, taxonomy calibration Brier score, exact rollback
fidelity, shard-order stability, verification cost, and equal learning compute.
Every arm executes 24 update attempts, 144 gradient units, and 144 shadow
units. Verification cost is separate overhead and is bounded at 72 units.

## Prediction lock and validation

Tune improvement is recorded for every replicate. The 288 tune predictions are
sealed into a digest before assessment loss is computed. The result reports
the lock digest and every replicate binds to it.

`validate_factorial_v2.py` is a separate aggregate-only validator. It
independently regenerates the seed-derived panel, recomputes split identity,
assessment baseline/final loss, the primary endpoint, forgetting, taxonomy
calibration, order stability, and compute guards. It does not import the
runner's metric functions.

## Decision rules

- A controller comparison is eligible only when every hard guard passes.
- If only adaptive gating improves the primary endpoint and adding waves does
  not, discard the wave mechanism for this learner.
- Any apparent wave gain with unequal learner compute is rejected.
- Stochasticity is rejected if its gain is confined to one seed or shard order.
- Synthetic continual-learning improvement does not establish an Astral result.

## Explicit boundary

The next model-bearing step requires a separate authorization. If authorized,
it may use only a cached model with reversible adapters, never base-weight
updates, never V48 artifacts, and never the closed V48 causal-target lane.
Astral integration may test only causal-effect prediction, calibration, or
instrumental correction. Real ZK/PQC backends come last; each must prove one
concrete statement and report overhead. Synthetic flags and fixture receipts
cannot satisfy that boundary.
