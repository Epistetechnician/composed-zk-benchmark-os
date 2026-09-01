# Evidence-conditioned multiscale plasticity v2

State slice: `astral-evidence-conditioned-multiscale-plasticity-v2`.

This slice replaces the v1 hand-authored fixture with an exact synthetic
continual learner. Its state is a six-dimensional parameter vector. Each shard
has a mechanically generated target, the update is exact quadratic
target-tracking, interference is the exact increase in protected-task loss,
and held-out improvement is the exact reduction in tune/assessment loss after
24 update attempts.

The fixed factorial is 4 controller modes x 2 scheduling regimes x 4 taxonomy
conditions, with 3 preregistered replicate seeds and 3 preregistered shard
orders per cell:

- modes: fixed cadence, adaptive verification, wave scheduling, adaptive wave;
- scheduling: deterministic, bounded seeded stochastic;
- taxonomy: oracle, bounded noisy, shuffled, absent.

All arms execute the same number of update attempts, gradient units, and shadow
evaluations. Verification cost is reported separately and bounded. Assessment
metrics are computed only after a fit/tune prediction lock is sealed. A
separate aggregate validator duplicates the closed-form panel and loss
equations; it does not import the runner's metric functions.

The synthetic verification check is not a ZK proof, PQC signature, provenance
receipt, or semantic truth claim. Real ZK/PQC backends are a later independent
slice, with one concrete statement and measured overhead per backend.

## Run

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/astral_dynamics/tests/test_evidence_conditioned_dynamics_v2.py
PYTHONDONTWRITEBYTECODE=1 python experiments/astral_dynamics/evidence_conditioned_dynamics_v2.py --output /tmp/astral-evidence-conditioned-dynamics-v2
PYTHONDONTWRITEBYTECODE=1 python experiments/astral_dynamics/validate_factorial_v2.py /tmp/astral-evidence-conditioned-dynamics-v2/result.json
```

The result is local exact-synthetic controller evidence only. It does not load
a model, update base weights, consume V48 artifacts, reopen the Astral causal-
target lane, mutate the accepted Evidence Ledger, or establish introspection,
self-modeling, Stage 0C, Stage 1, benchmark, production, ZK, or PQC evidence.
