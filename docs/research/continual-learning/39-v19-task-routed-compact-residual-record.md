# V19 task-routed compact residual execution record

State slice: `continual-learning-protocol-v19-task-routed-compact-residual`.

Classification: `TaskRoutedCompactResidualPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentTaskRoutedCompactResidualPilot`.

## Execution

V19 ran one fixed local panel plus one compact task-routed candidate using the
cached Qwen2.5-0.5B-Instruct-4bit model. The inherited V18 panel preserved the
same task data, prompt contract, seed, order, optimizer, update budget, and 160
iterations. The changed candidate path trained four task-keyed two-layer LoRA
slots, one per task, with no resume between slots. Four slots times two layers
matched the eight-layer shared-adapter layer budget; actual adapter bytes were
also checked.

Artifact directory:

`/tmp/continual-learning-model-v19-qwen-seed20260810-order0123`

## Endpoint metrics

| strategy | acquisition | retention after interference | recovery after reacquisition |
| --- | ---: | ---: | ---: |
| no update | 4/8 (0.50) | 4/8 (0.50) | 4/8 (0.50) |
| context only | 2/8 (0.25) | 4/8 (0.50) | 4/8 (0.50) |
| retrieval | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |
| naive sequential LoRA | 8/8 (1.00) | 2/8 (0.25) | 2/8 (0.25) |
| balanced replay LoRA | 8/8 (1.00) | 2/8 (0.25) | 2/8 (0.25) |
| immutable task-adapter bank | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |
| compact task-routed residual | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |

Parameter budget:

```text
full shared adapter bytes: 5,877,295
compact routed slots total: 5,877,252
compact/full ratio: 0.9999926837090872
```

## Gates

```text
task_routed_solvability_floor: true
task_routed_retention_above_naive: true
parameter_budget_matched: true
v19_candidate_eligible: true
breakthrough_claim_eligible: false
h100_authorized: false
```

The compact routed candidate preserves the target task at matched adapter-byte
budget in this one local seed/order panel. This is evidence for a local,
task-separated parameter-routing pilot. It is not evidence that replay works:
balanced replay remains tied with naive at 2/8. It is also not a general
continual-learning, production, SOTA, or breakthrough claim.

## Independent validation and hashes

```text
validator: valid
manifest_sha256: 760bc75871d0ad07dc0a4974dcd18e1891c3482ecc7e1d9fd7fc3a824ebaccc5
result_sha256: 36d8c653657c503a01e17729fac52bc5aea959ee860f50fd1a9d98cec4cdc8b4
task_routed_audit_sha256: 5cf74a92db9acf68322a9cdfb6d883af399300b44c3c44748ee6cecb97010098
```

## Decision

Keep V19 as a positive local routing result and stop the current training
slice. The next research object is an independent multi-seed/order replication
of the compact routed protocol with the same byte-budget check, followed by a
direct comparison against a genuine replay mechanism. Do not provision an H100
until replay retention passes and runtime or memory is demonstrated to be the
bottleneck.
