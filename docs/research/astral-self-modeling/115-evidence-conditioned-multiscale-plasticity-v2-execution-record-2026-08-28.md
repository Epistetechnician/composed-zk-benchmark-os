# Evidence-conditioned multiscale plasticity v2 execution record

Date: 2026-08-28.

State slice: `astral-evidence-conditioned-multiscale-plasticity-v2`.

Status: `SyntheticFactorialValidated / ModelBearingExecutionNotAuthorized`.

Claim ceiling: `LocalDevelopmentExactSyntheticControllerOnly`.

## Scope

The v2 run replaced the v1 hand-authored fixture with a closed-form synthetic
learner. It used a six-dimensional parameter vector, 24 fit shards, 12 tune
shards, and 12 assessment shards for each of three preregistered replicate
seeds. Every update target, parameter delta, interference value, loss, and
ground-truth risk value was generated mechanically. No model, base weights,
provider, external corpus, V48 artifact, Astral causal-target artifact, ZK
backend, or PQC backend was used.

## Frozen execution

The 32 factorial cells were:

- four modes: fixed cadence, adaptive verification, wave scheduling, adaptive
  wave;
- two scheduling regimes: deterministic and bounded seeded stochastic;
- four taxonomy conditions: oracle, noisy, shuffled, and absent.

Each cell ran 9 replicates: three seeds crossed with three fixed shard orders.
The 288 fit/tune predictions were locked before any assessment loss was
computed. The independent validator regenerated the panel and recomputed
assessment loss, forgetting, taxonomy calibration, order stability, rollback,
and compute guards from the serialized report.

Result digest:

```text
ecdadac8d16bc868319a62ede32a445db060093b62410196c6e12f8ad6e540ae
```

Prediction-lock digest:

```text
b185ebc1045b4f22e7b5cb8bc00f85c4a3c50c6e0639d15f94af179c4ad6763b
```

The focused v2 suite passed 6 tests. The independent aggregate validator
accepted the JSON round trip. All cells passed the currently frozen mechanical
guards. Every cell used 24 update attempts, 144 gradient units, and 144 shadow
units; verification cost remained within the 72-unit bound.

## Primary result

The primary endpoint was held-out assessment improvement after the fixed
24-update budget. Under the preregistered deterministic/oracle comparison:

| Cell | Primary mean | Mean committed shards | Max verification cost |
|---|---:|---:|---:|
| fixed cadence | 0.1139818618 | 24.0000 | 0 |
| adaptive verification | 0.1176014664 | 21.4444 | 24 |
| wave scheduling | 0.1146485699 | 24.0000 | 0 |
| adaptive wave | 0.1171129407 | 21.2222 | 24 |

Adaptive verification improved over fixed cadence by `0.0036196046` in this
synthetic panel. Adding waves after gating reduced the result by
`0.0004885257` relative to adaptive verification. Wave-only scheduling was
`0.0006667081` above fixed cadence, but the full-controller comparison did not
support the wave mechanism.

The bounded-stochastic adaptive/oracle result was `0.1149564223`, below the
deterministic adaptive/oracle result. The adaptive stochastic-minus-deterministic
delta was negative in the aggregate and positive in only 3 of 9 matched
replicates. This does not satisfy the preregistered robustness rule for a
stochastic improvement.

## Decision

For this exact learner, keep adaptive verification as a candidate controller
component and discard the wave mechanism. Do not generalize that result to
transformers: the synthetic learner was deliberately constructed with known
ground truth and its controller-visible taxonomy is a test input, not
epistemological or ontological knowledge.

The result does not establish that waves improve continual learning, that
stochasticity is useful, that taxonomy estimates are valid outside this panel,
that cryptographic verification improves learning, or that Astral has any
introspective or causal-self-modeling property.

## Next authorized boundary

The next step is a separately authorized cached-model experiment using
reversible adapters only, with no base-weight updates, no V48 artifacts, and no
reopening of the V48 causal-target lane. Astral integration, if separately
authorized, may measure only causal-effect prediction, calibration, or
instrumental correction. Real ZK/PQC backends come after controller evidence;
each backend must prove one concrete statement and report its overhead. A
fixture receipt or boolean flag cannot satisfy that requirement.
