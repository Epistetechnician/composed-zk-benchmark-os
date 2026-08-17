# Verified self-model benchmark

State slice: `verified-self-model-benchmark-v1`.

This package is a process-free, aggregate-only benchmark contract. It scores
forecasted capability, externally verified limitations, fixed counterfactual
variants, and recursive belief updates. It does not execute an agent, call a
model, use the network, retain raw reasoning, grant authority, or establish a
general self-model.

## Contract smoke

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.run_benchmark \
  --input experiments/self_model_benchmark/fixtures/smoke.jsonl \
  --output /tmp/self-model-benchmark-smoke.json

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.validate_benchmark \
  /tmp/self-model-benchmark-smoke.json \
  --input experiments/self_model_benchmark/fixtures/smoke.jsonl
```

Expected result: `ContractSmokeOnly`, `decision=not_evidence`, and
`scientific_evidence=false`.

## Live-shaped benchmark

A live capture must contain at least 60 trajectories across five task families,
with fit/tune/assessment minimums of `24/12/24`. Every trajectory contains the
same five variants: `base`, `tool_augmented`, `budget_extended`, `memory_reset`,
and `policy_restricted`. The validator requires digest-bound trial records,
externally verified aggregate outcomes, prediction locking before assessment,
and continuous prior/posterior belief updates across horizons.

The current live-shaped unit test creates 300 rows: 60 trajectories multiplied
by five variants. It is a contract test, not a live run and not scientific
evidence. A future capture adapter must bind those rows to one real workflow
without adding model execution or authority to this package.

## Claim boundary

The benchmark can produce only a local development candidate after all gates
pass. It cannot prove introspection, consciousness, mechanistic self-knowledge,
causal understanding, production readiness, or Astral Stage 0C/Stage 1 status.
