# Oak Lab selective-credit theory V2

State slice: `oaklab-experience-learning-selective-credit-v2`

## Why V2 is a new theory

V1 was rejected because a per-coordinate lower-confidence gate treated
uncertainty as harm and retained a full previous-delta vector. V2 changes both
the estimand and the state design. It does not change the closed plasticity
guard.

V2 estimates the expected one-step sequential loss change under the fixed
online process, not a causal counterfactual. If `ell_t` is the pre-update loss
on item `t`, the utility observation is:

`U_t = ell_(t-1) - ell_t`.

The learner tracks scalar exponential moments of `U_t`. After warm-up it uses
full-rate SGD unless `mean(U) + k*std(U) < 0`; only confidently harmful
sequences receive the fixed minimum gate. The learner stores only the previous
scalar loss and two scalar moments. It has one `Experience` per update, no
replay, and no hidden gradient accumulation.

## Frozen protocol

- Streams: sparse noisy, nonstationary feature relevance, drifting target,
  noisy-MNIST-like distractors, event-camera-like sparse events, and
  long-horizon mixed drift.
- Fresh seed offsets: `10, 11, 12, 13, 14`.
- 256 experiences per stream; fit, tune, and assessment are fixed thirds.
- Reference: fixed `sgd_b1`, learning rate `0.03`.
- Candidate: `TemporalUtilityGateLearner`, learning rate `0.03`, utility decay
  `0.8`, variance decay `0.9`, confidence multiplier `0.75`, minimum gate
  `0.1`, warm-up `8`.
- Controls: causal running-mean noise floor and oracle-feature SGD.
- Paired assessment alpha: `0.05`; at least two stream families are required.
- Prediction locking: learner hyperparameters and split boundaries are sealed
  before assessment; fit/tune/assessment state digests are retained.
- Real execution is prohibited until independent review passes.

Plan digest: `bcb3e6413adb9724a8b2aeef4ab52abedc2144665e52886c1252fad8c4b4ef1d`.

## Implementation

- Learner: `experiments/experience_learning/temporal_credit_v2.py`
- Qualification: `experiments/experience_learning/temporal_credit_qualification_v2.py`
- CLI: `experiments/experience_learning/run_temporal_credit_qualification_v2.py`
- Independent validator:
  `experiments/experience_learning/validate_temporal_credit_qualification_v2.py`
- Tests: `experiments/experience_learning/tests/test_temporal_credit_v2.py`

## Boundary

This slice is synthetic development evidence. It does not authorize reuse of
V1 artifacts as data, real-stream execution, hardware energy claims, Astral
integration, publication, or production traffic.
