# Evidence-conditioned multiscale plasticity v3

State slice: `astral-evidence-conditioned-multiscale-plasticity-v3`.

This slice translates the supplied continual-learning literature into an exact
synthetic learner whose state, update effects, interference, uncertainty fields,
and ground truth are mechanically known. It tests six memory/update policies:

- `single`: one fast parameter state;
- `fast_slow`: fast state plus slower consolidation;
- `replay`: bounded exact replay of prior shards;
- `ewc`: importance-weighted protection of prior state;
- `plasticity_guard`: bounded plasticity decay and recovery;
- `integrated`: all four mechanisms together.

It crosses those policies with fixed, single-frequency, dual-frequency, and
bounded seeded-stochastic schedules; fixed admission and evidence-conditioned
admission; and oracle, noisy, shuffled, and absent measurable taxonomy. The
factorial has 192 cells, 9 fixed replicates per cell, and 1,728 total
replicates. Every replicate has 48 micro-update attempts, split into 24 fit,
12 tune, and 12 assessment shards. Fit/tune predictions are locked before any
assessment loss is computed.

The taxonomy fields are measurable synthetic novelty, uncertainty, expected
utility, risk, surprise, and provenance-like confidence. They are not
epistemological or ontological truth. The verification signal is a deterministic
synthetic control input, not a ZK proof, PQC signature, provenance receipt, or
semantic truth claim.

## Run

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/astral_dynamics/tests/test_literature_informed_factorial_v3.py
PYTHONDONTWRITEBYTECODE=1 python experiments/astral_dynamics/literature_informed_factorial_v3.py --output /tmp/astral-literature-factorial-v3
PYTHONDONTWRITEBYTECODE=1 python experiments/astral_dynamics/validate_literature_factorial_v3.py /tmp/astral-literature-factorial-v3/result.json
```

The independent validator duplicates the closed-form panel, taxonomy, and loss
equations without importing the runner's metric functions. The report is
digest-bound and can be validated after a JSON round trip.

## Result boundary

The v3 result is exact-synthetic controller evidence only. It does not load a
model, update base weights, consume V48 artifacts, reopen the Astral
causal-target lane, mutate the accepted Evidence Ledger, or establish
introspection, self-modeling, Stage 0C, Stage 1, benchmark, production, ZK,
or PQC evidence. A cached-model experiment requires a separate authorization
and reversible adapters only.
