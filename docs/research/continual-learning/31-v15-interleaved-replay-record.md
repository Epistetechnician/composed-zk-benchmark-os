# V15 interleaved replay retention record

State slice: `continual-learning-protocol-v15-interleaved-replay-retention`.

Classification: `InterleavedReplayRetentionPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentInterleavedReplayRetentionPilot`.

## Scope and execution

V15 changed one task/update variable after V14: replay rows were written in a
deterministic task-stratified round-robin schedule. Selected fact IDs, replay
counts, total rows, model, seed, order, optimizer, learning rate, batch size,
LoRA depth, sequence length, and 160-step update objective were fixed. The
panel retained naive sequential LoRA, interleaved replay LoRA, the immutable
task adapter bank, no-update, context-only, and retrieval controls.

Accepted artifact:

`/tmp/continual-learning-model-v15-qwen-seed20260810-order0123`.

No replication, second model, or H100 was used.

## Results

| strategy | acquisition | retention after interference | recovery |
| --- | ---: | ---: | ---: |
| no update | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| context only | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| naive sequential LoRA | 8/8 (1.00) | 2/8 (0.25) | 4/8 (0.50) |
| interleaved replay LoRA | 8/8 (1.00) | 0/8 (0.00) | 2/8 (0.25) |
| immutable task adapter bank | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |
| retrieval control | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |

The replay datasets retained the V14 selected fact IDs and per-task counts, and
the validator confirmed the task-route round-robin order in all replay update
datasets. The schedule changed exposure ordering without changing the example
multiset or the update budget.

Gates:

```text
solvability_floor: true
retrieval_above_no_update: true
replay_retention_above_naive: false
bank_retention_above_naive: true
candidate_eligible: false
breakthrough_claim_eligible: false
```

Interleaving did not create a replay benefit. It reduced replay retention from
V14's `2/8` to `0/8`, below naive's `2/8`. The result is a protocol-level
negative: scheduling order alone does not solve the shared-adapter interference
problem and may make it worse. The adapter bank remains a route-preservation
control, not replay evidence.

## Audit and validation

The independent validator returned `valid: true`. It checked the V14 source
state, exact V14 fixed budget, V15 schedule contract, held-out splits, prompt
parity, selected fact IDs, replay counts, row memberships, route ordering,
target-task accuracy after every update, adapter-bank routing, and hashes.

Hashes:

```text
contract_sha256: 3c7afb691af50090fa2f8a78657c7315468a165052f4b3068843c3bb97bd74fc
manifest_sha256: 13167f10b83e4850927c15f25f2e73f94e142591b5808a78103ff31fb3100498
result_sha256:   7ca701ee770ffa1d56c05d4de29978cfa38ebf7048f455aee6e0759d5688c5c1
```

Audit hashes:

```text
naive_sequential_lora: e8fa6fab56717cba907baa1f5fe7f4184d3d0b5647d687e0170424f0678f5c7e
replay_lora:           23f9db1fc03fb64f2172000c8cedbb983bdc15dad796bc3b5c42cb5d2f150bd8
task_adapter_bank:     b9b9f0b68982d505ec6eeff9ed24666721341bf62fea5c0153c48096f814b3b0
```

## Decision

Stop V15. Do not replicate interleaving, add a second model, or provision an
H100. The next research object must redesign the shared task/update interface
or representation boundary; further replay-sampling and row-order variants are
not justified by this evidence. The highest-value control is explicit task
routing, which should be treated as a separate memory architecture rather than
as proof that replay works.
