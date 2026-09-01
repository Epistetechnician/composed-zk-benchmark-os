# Plasticity guard with reversible adapters V1 execution authorization

Date: 2026-08-28.

State slice: `continual-learning-plasticity-guard-reversible-adapter-v1`.

## Authorization

The user explicitly authorized the next step after the validated exact
synthetic factorial: run a separately scoped cached-model experiment using
reversible adapters, predeclare `plasticity_guard`, leave all base weights
untouched, and keep Astral integration limited to causal-effect prediction,
calibration, or instrumental correction.

This record activates only the protocol in
`89-plasticity-guard-reversible-adapter-v1-protocol.md` and the additive source
and validator named below. It does not authorize any other continual-learning,
Astral, provider, benchmark, production, ZK, or PQC lane.

## Authorized touch surface

- `experiments/continual_learning/plasticity_guard_reversible_adapter_v1.py`
- `experiments/continual_learning/validate_plasticity_guard_reversible_adapter_v1.py`
- `experiments/continual_learning/tests/test_plasticity_guard_reversible_adapter_v1.py`
- this protocol, execution record, and navigation/status records;
- repository-external immutable roots under PrimaryED and DAed for the cached
  model campaign.

## Explicit exclusions

No model download, networked model execution, base-weight update, adapter
merge, V48 or earlier Astral artifact reuse, accepted Evidence Ledger mutation,
Stage 0C or Stage 1 promotion, introspection claim, causal-self-modeling
claim, benchmark claim, production traffic, provider/H100 job, or real ZK/PQC
backend is authorized by this record.

Execution authorization is not a scientific-positive-result claim. The final
classification remains bounded by the protocol claim ceiling and independent
validator output.
