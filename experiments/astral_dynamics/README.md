# Evidence-conditioned multiscale plasticity harness

The current literature-informed exact-synthetic result is documented in
[README-v3.md](README-v3.md). The earlier contract-only and exact-synthetic
v1/v2 slices remain preserved as historical artifacts.

State slice: `astral-evidence-conditioned-multiscale-plasticity-v1`.

This is the first contract-only slice for the proposed Astral-adjacent
continual-learning control mechanism. It exercises deterministic shard
identity, measurable risk classification, dynamic verification requirements,
bounded high/low-frequency control multipliers, shadow-before-commit ordering,
and reversible rollback.

It does not load a model, train weights, access a provider, acquire a corpus,
generate ZK proofs, verify PQC signatures, mutate the accepted Evidence Ledger,
or establish neural-learning, Astral, Stage 0C, Stage 1, benchmark, or
production evidence. Receipt records are explicitly deterministic fixture
contracts and are not ZK/PQC evidence.

## Run

Run the hermetic tests:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/astral_dynamics/tests
```

Run the aggregate fixture report to an external directory:

```text
PYTHONDONTWRITEBYTECODE=1 python experiments/astral_dynamics/evidence_conditioned_dynamics_v1.py --output /tmp/astral-evidence-conditioned-dynamics-v1
```

The report has one primary mechanics metric, held-out fixture gain, and a
separate forgetting guard. Neither is a neural-learning result.

## Next gate

The next slice requires a separately frozen scientific protocol, a small
controlled transformer or exact simulator with causal ground truth, equal
compute across fixed/adaptive/wave arms, fresh data identity, prediction
locking, independent validation, and explicit rollback semantics. Real ZK/PQC
backends must be integrated as independently verified receipt producers before
any cryptographic claim is made.
