# Oak Lab selective-credit theory V1

State slice: `oaklab-experience-learning-selective-credit-v1`

## Decision

The powered real plasticity-guard assessment is closed as a negative result.
This slice does not retune that mechanism. It tests a different hypothesis:
credit should be assigned from delayed predictive utility, not from current
error surprise.

For update `t-1`, retain only its parameter delta `d`. On the next experience
`(x_t, y_t)`, compute the current loss and reconstruct the no-update
counterfactual:

`U_t = loss(y_t, yhat_t - d · [x_t, 1]) - loss(y_t, yhat_t)`.

`U_t` is a one-step downstream loss reduction. Each coordinate tracks an
exponential mean and second moment of `U_t`. The next update is full-strength
when its utility lower confidence bound is positive and uses a fixed minimum
gate otherwise. The first four items are an ungated warm-up. The mechanism
retains one delta vector, never a replay example, and never an accumulated
gradient.

The theory is falsifiable: it must improve assessment loss and adaptation on
at least two stream families while remaining non-inferior in updates, active
operations, and state bytes versus fixed batch-one SGD. A synthetic result
cannot authorize a real-data or hardware claim.

## Frozen contract

- Six deterministic synthetic streams: sparse noisy, nonstationary feature
  relevance, drifting target, noisy-MNIST-like distractors, event-camera-like
  sparse events, and long-horizon mixed drift.
- Five independent seed offsets: `0..4`.
- 256 experiences per stream, fit/tune/assessment thirds.
- Candidate: `PredictiveUtilityCreditLearner`, learning rate `0.03`, utility
  decay `0.9`, variance decay `0.9`, confidence multiplier `0.5`, minimum gate
  `0.05`, warm-up `4`.
- Reference: fixed `sgd_b1`, learning rate `0.03`.
- Controls: causal running-mean noise floor and oracle-feature SGD.
- Assessment is paired by seed. The normal-approximation paired test uses
  alpha `0.05`; the multi-stream gate requires two qualifying families.
- No network, model-bearing execution, real-data custody reuse, Astral
  integration, replay, hidden accumulation, or assessment retuning.

Plan digest: `716f7b6bc1939f296b5f28b2da1341d0bd67770e38d6f699c479c981bcf9e325`.

## Implementation

- Learner: `experiments/experience_learning/selective_credit_v1.py`
- Qualification: `experiments/experience_learning/selective_credit_qualification_v1.py`
- CLI: `experiments/experience_learning/run_selective_credit_qualification_v1.py`
- Independent validator:
  `experiments/experience_learning/validate_selective_credit_qualification_v1.py`
- Hermetic tests:
  `experiments/experience_learning/tests/test_selective_credit_v1.py`

## Result

External aggregate-only receipt:

`/Users/shaanp/Documents/research-artifacts/oaklab-experience-learning-selective-credit-v1/qualification.json`

Result digest: `274a561b9e5cc34cf4d8d8a6e5a4ad796a27f942b320e6e2bb580e90f912805f`

Independent validation passed. The result is `no_candidate`: the candidate
had higher assessment loss than fixed SGD on all six streams and carried
larger state. This is a theory rejection, not evidence to retune the closed
plasticity guard. The synthetic claim ceiling is
`LocalDevelopmentOakLabSelectiveCreditSyntheticQualification`.

## Required continuation

No real-data execution follows this receipt. A new theory would require a new
estimand that addresses this failure, a fresh protocol and seeds, prediction
locking, independent review, and a new state slice. The existing full-campaign
publication gate remains `no_candidate` until an operator supplies a privileged
`powermetrics` receipt and an independently validated mechanism wins the strict
quality/adaptation/resource gate.
