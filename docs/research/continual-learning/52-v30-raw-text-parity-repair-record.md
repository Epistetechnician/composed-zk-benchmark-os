# V30 raw-text parity repair record

Status: `CompleteNegativeLocalDevelopmentAcquisitionRepair`.

State slice: `continual-learning-model-acquisition-eligibility-v30`.

## Purpose

V30 tests one narrow repair to the Qwen3.6 acquisition failure: serialize each
training example as one raw text field containing the exact route-bound prompt
and completion, and remove chat-template wrapping and prompt masking. The
repair changes the training serialization boundary only. It does not run
retention, interference, reacquisition, provider, production, or scientific
promotion work.

## Execution boundary

The first execution used `/tmp/continual-learning-qwen36-acquisition-v30-20260821-r1`.
Training completed, but the transient output directory disappeared during the
isolated readout phase before the result was sealed. It is a quarantined
execution failure, not a scientific result.

The frozen protocol was then rerun without changing the model, seed, task
order, dataset, optimizer, iteration budget, or readout contract. The durable
sealed artifact is:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen36-acquisition-v30-20260821-r2`.

The independent validator returned `valid: true`. Recomputed result,
contract, audit, and manifest digests matched the sealed values. The task
accuracies were:

| Task | No-update train | Adapter train | Adapter held-out |
| --- | ---: | ---: | ---: |
| T0 | 2/8 | 4/8 | 4/8 |
| T1 | 2/8 | 2/8 | 2/8 |
| T2 | 2/8 | 2/8 | 2/8 |
| T3 | 2/8 | 2/8 | 2/8 |

The target output is no longer constant, but the target train floor, target
held-out floor, and all-task improvement gate remain false. V30 is therefore
an ineligible acquisition preflight, not a viable model improvement. No
retention, interference, reacquisition, provider, production, or scientific
promotion work is authorized from this result.

The authoritative completed result remains the independently validated V29
record at:

`/tmp/continual-learning-qwen36-acquisition-v29-20260821-r2`.

Claim ceiling: `LocalDevelopmentModelAcquisitionEligibilityPreflight`. The
result is a complete, independently validated negative local acquisition
diagnostic only.
