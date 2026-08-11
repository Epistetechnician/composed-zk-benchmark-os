# V18 route-boundary representation execution record

State slice: `continual-learning-protocol-v18-route-boundary-representation`.

Classification: `RouteBoundaryRepresentationPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentRouteBoundaryRepresentationPilot`.

## Execution

V18 ran the fixed six-strategy local panel once using the cached
Qwen2.5-0.5B-Instruct-4bit model. The sole changed variable was the repeated
task route marker at the answer boundary. Data, optimizer, seed, task order,
update budget, and 160 objective iterations were fixed to the V14 repaired-
objective contract. The validator also confirmed 12 datasets of 32 rows,
replay fact IDs and per-task counts, and target-task accuracy after every
update.

Artifact directory:

`/tmp/continual-learning-model-v18-qwen-seed20260810-order0123`

## Endpoint metrics

| strategy | acquisition | retention after interference | recovery after reacquisition |
| --- | ---: | ---: | ---: |
| no update | 4/8 (0.50) | 4/8 (0.50) | 4/8 (0.50) |
| context only | 2/8 (0.25) | 4/8 (0.50) | 4/8 (0.50) |
| retrieval | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |
| naive sequential LoRA | 8/8 (1.00) | 2/8 (0.25) | 2/8 (0.25) |
| balanced replay LoRA | 8/8 (1.00) | 2/8 (0.25) | 2/8 (0.25) |
| immutable task-adapter bank | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |

## Gates

```text
solvability_floor: true
retrieval_above_no_update: true
replay_retention_above_naive: false
bank_retention_above_naive: true
candidate_eligible: false
breakthrough_claim_eligible: false
```

Replay retention is exactly tied with naive retention at 2/8. The route marker
did not create a measurable replay effect in this local panel. Retrieval and
the immutable adapter bank remain positive controls, establishing that the
task is solvable and that explicit task-separated state can preserve it; they
do not establish a replay breakthrough.

## Independent validation and hashes

```text
validator: valid
manifest_sha256: 4e6a0fc82f33f4878176c33544a07c375201792db52a505e002dddeae91e9703
result_sha256: 920c1aa27e6a23a89a421a0c8ac7a23217b7f13a3c116d0aad98b98cc652a31b
```

Audit hashes:

```text
naive_sequential_lora: aab297103ed12e62d682d5e5fd9675c10ff67d200c7589eafd029e2c8f727223
replay_lora: 5320153d9974a6ac78d9476e9e5126454fc6473cf2fee4e448f7bd5ba4a82130
task_adapter_bank: b9b9f0b68982d505ec6eeff9ed24666721341bf62fea5c0153c48096f814b3b0
```

## Decision

Stop V18. Do not buy compute and do not claim a continual-learning
breakthrough. The remaining bottleneck is protocol-level: balanced replay is
present and auditable but does not preserve the target task under the current
shared-update interface. The next research object must redesign task/update
interaction, with a new preregistered identity and the same fixed-budget
controls. H100 provisioning remains unauthorized because the local failure is
not demonstrably runtime- or memory-bound.
