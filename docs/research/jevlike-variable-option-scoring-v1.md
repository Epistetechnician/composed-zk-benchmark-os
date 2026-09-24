# Jevlike variable-option scoring V1

State slice: `jevlike-variable-option-scoring-v1`.

Status: `BOUNDED_EXTERNAL_EXECUTION_COMPLETE`.

## Purpose

This slice tests whether the Jevlike variable-option interface can rank the
first divergence position in the existing synthetic FSM task. The upstream
package is used from a separate checkout at a frozen revision; it is not
vendored into this repository. The task is option ranking, not neural
telemetry, introspection, causal explanation, or proof.

## Frozen boundary

- Upstream revision: `94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452`.
- Encoder: Jevlike `tiny`; no pretrained encoder or external weights.
- Device: CPU.
- Network during training/evaluation: disabled by policy.
- Input: existing archived synthetic FSM actor observations.
- Label: oracle-derived first-divergence index, with `no_divergence` as option
  zero.
- Split: entire source runs are assigned to fit, tune, or held-out test; rows
  are never split across those boundaries.
- Retention: checkpoints, JSONL rows, and raw command output remain outside
  the repository; only the aggregate report is admissible for review.

## Reproduction

The external checkout must exist at the pinned revision, and the repository
virtual environment must provide PyTorch:

```text
./scripts/python -B -m tools.jevlike_variable_option_scoring_v1.run_experiment \
  --repo-root /Users/shaanp/Documents/GitHub/composed-zk-benchmark-os \
  --upstream-root /Users/shaanp/.codex/external/jevlike-94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452 \
  --output-root /Users/shaanp/.codex/runs/jevlike-variable-option-scoring-v1
```

The command prints the held-out top-1/top-3 accuracy, expected calibration
error, shuffled-context control, option-permutation control, and report path.

## Claim ceiling

`LocalDevelopmentVariableOptionScoringFeasibilityOnly`.

A positive result would support only bounded candidate-ranking feasibility on
this synthetic FSM localization task. It would not establish a neural
localization signal, self-modeling, mechanistic interpretability, alignment,
benchmark superiority, proof, production readiness, or authority. The model
does not select an experiment, mutate a host, authorize an intervention, or
write the Evidence Ledger.

## Required disposition

The held-out result must be compared with the strongest baseline, not only a
random baseline. A candidate is not retained if it fails the shuffled-context
control, option-permutation invariant, or held-out calibration check. Any
future use with external weights, real host activations, or causal
interventions requires a fresh protocol identity and independent review.

Every mutation governed by this record touches state slice
`jevlike-variable-option-scoring-v1`.
