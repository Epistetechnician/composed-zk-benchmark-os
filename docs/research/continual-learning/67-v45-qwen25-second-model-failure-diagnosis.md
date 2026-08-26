# V45 second-model failure diagnosis

State slice: `continual-learning-qwen25-second-model-failure-diagnosis-v45`  
Protocol: `v45-qwen25-second-model-failure-diagnosis-v1`  
Claim ceiling: `LocalDevelopmentSecondModelFailureDiagnosis`

## Purpose and boundary

V45 is a read-only diagnosis of the immutable V44 Llama second-model
replication artifact. It does not execute a model, training, inference,
network access, downloads, tuning, provider validation, production operation,
or promotion of V44 as positive evidence. It consumes the V44 result payloads,
raw JSONL receipts, adapter files, training logs, and the independent V44
validator output. Retention and order phases remain correctly unexecuted
because V44 stopped at acquisition eligibility.

The diagnosis is a separate artifact family. It does not mutate the V44 root
and does not relabel V44's negative eligibility result.

## Reproduction

The independent V44 validator was rerun from the source root and returned:

- `valid=true`;
- three acquisition cases, all structurally valid;
- zero of three acquisition cases eligible;
- `replication_eligible=false`;
- stop classification `LlamaSecondModelReplicationStoppedAtAcquisitionEligibility`.

Every task-0 receipt records 160 iterations and saved final adapter weights.
Therefore the blocker is not an unexecuted task or missing adapter artifact.

## Findings

Across all three fresh task seeds:

- task 0 remained constant `A` for no-update, adapter-train, and adapter-test,
  with `0.25` accuracy in each phase;
- tasks 1, 2, and 3 reached `1.0` adapter-train and adapter-test accuracy under
  the same 160-iteration, 32-update frozen schedule;
- every task's expected train/test labels were balanced across `A/B/C/D`;
- every raw-text split had 32 rows, 193-character prompt texts, balanced
  `A/B/C/D` completions, and exact task-token/route binding;
- every task had a saved adapter and a completed training receipt.

The conservative classification is:

`TaskSpecificTargetAcquisitionFailureWithConstantReadout`

This isolates a task-specific frozen-protocol acquisition/readout failure. It
does not identify the lower-level cause.

## Hypothesis ledger

| Hypothesis | Status | Evidence boundary |
| --- | --- | --- |
| Target task-specific acquisition/readout failure | Supported | Task 0 is A-only across three fresh seeds after completed training; tasks 1–3 learn under the same schedule. |
| Malformed or unbalanced target payload | Falsified | Task manifests and raw JSONL are balanced and route-bound with the same shape across tasks. |
| Frozen budget globally insufficient | Falsified | The same budget fits tasks 1–3. |
| Custody or validator artifact | Falsified | Independent V44 validation and source inventory checks reproduce the fail-closed result. |

## What remains unresolved

Task 0 uses the identity codebook while tasks 1–3 use shifted codebooks. V44
contains no matched-codebook counterfactual, so base-prior/codebook alignment
remains unresolved. The durable results contain argmax labels rather than
logits or intermediate activations; a smaller non-`A` probability movement
cannot be assessed from these artifacts. No authorized budget or optimizer
counterfactual exists, so target-specific budget insufficiency is not a causal
finding. No retention or order conclusion is available.

## Artifact custody

The V45 output is external and immutable:

`/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/continual-learning-qwen25-second-model-failure-diagnosis-v45-20260826-r1`

The output contains `contract.json` and `diagnosis.json`, each digest-bound.
The V45 validator independently reruns V44 validation, rechecks the complete
V44 source-file inventory, recomputes every case summary, and verifies the
diagnosis and execution boundary.

Implementation:

- `experiments/continual_learning/diagnose_qwen25_second_model_failure_v45.py`
- `experiments/continual_learning/validate_qwen25_second_model_failure_v45.py`
- `experiments/continual_learning/tests/test_qwen25_second_model_failure_v45.py`
