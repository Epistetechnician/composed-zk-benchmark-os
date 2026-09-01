# Evidence-conditioned multiscale plasticity v1

State slice: `astral-evidence-conditioned-multiscale-plasticity-v1`.

Status: `ContractMechanicsOnly / ScientificExecutionNotAuthorized`.

## Purpose

This slice converts the proposed dynamic-shard idea into a falsifiable control
plane without loading a model or changing weights. Each fixture shard has a
digest-bound identity, measurable novelty/uncertainty/contradiction features,
a held-out fixture evaluation, and a reversible update record.

The controller compares four fixed modes:

1. `fixed_baseline`: no dynamic verification and no wave modulation;
2. `adaptive_gate`: risk-conditioned verification requirements;
3. `wave_only`: bounded high/low-frequency modulation without verification;
4. `adaptive_wave`: risk-conditioned verification plus bounded modulation.

The state machine is:

`new -> captured -> classified -> verified -> shadowed -> committed`

Failed identity, verification, repeatability, or held-out-gain checks route to
`quarantined`. A committed update can transition to `rolled_back` with an
explicit digest-bound event. Fast state and slow projected state are retained
separately in the fixture state record.

## Cryptographic boundary

The receipt interface contains integrity and computation flags, statement
digests, verifier cost, and a receipt digest. The source is explicitly
`deterministic-contract-fixture-not-zk-or-pqc`. No ZK proof or PQC signature is
generated or verified here. ZK would establish a specified computation;
signatures would establish provenance/integrity. Neither establishes semantic
truth, epistemic quality, or ontological correctness.

## Scientific boundary

This is not a neural-learning result and cannot reopen V48, unlock Stage 0C or
Stage 1, alter the Astral claim ledger, or support introspection,
self-modeling, consciousness, benchmark, or production claims. The fixture
taxonomy is a measurable control input, not privileged knowledge. Future work
must include predicted-taxonomy, oracle-taxonomy, shuffled-taxonomy, and
taxonomy-absent controls.

## Falsifiable next experiment

The first model-bearing experiment should use a controlled transformer or exact
synthetic learner with known causal ground truth and reversible adapters. Its
primary endpoint should be held-out adaptation gain after a fixed update
budget. Forgetting, calibration, rollback fidelity, shard-order leakage, and
verification cost are guards. Fixed cadence, adaptive gating, wave-only, and
full adaptive-wave arms must receive equal compute and fresh disjoint splits.

The experiment passes only if the full controller improves the primary endpoint
without violating the forgetting, calibration, rollback, custody, or compute
guards across preregistered seeds and shard orders. A gain that comes only from
more computation, leaked taxonomy labels, or uncontrolled stochasticity is a
failure.
