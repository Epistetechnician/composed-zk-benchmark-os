# V14 repaired-objective retention record

State slice: `continual-learning-protocol-v14-repaired-objective-retention`.

Classification: `RepairedObjectiveRetentionPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentRepairedObjectiveRetentionPilot`.

## Scope and execution

V14 carried the V13 fit repair into one fixed-budget retention preflight. The
only changed design relative to V11 was update training at `160` iterations
instead of `40`; the model, seed, task order, task facts, prompt, optimizer,
data budget, replay capacity, and recovery operation were fixed. The panel was
naive sequential LoRA, balanced replay LoRA, immutable task adapter bank,
no-update, context-only, and retrieval.

Accepted artifact:

`/tmp/continual-learning-model-v14-qwen-seed20260810-order0123`.

No replication, second model, or H100 was used.

## Results

| strategy | acquisition | retention after interference | recovery |
| --- | ---: | ---: | ---: |
| no update | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| context only | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| naive sequential LoRA | 8/8 (1.00) | 2/8 (0.25) | 4/8 (0.50) |
| balanced replay LoRA | 8/8 (1.00) | 2/8 (0.25) | 2/8 (0.25) |
| immutable task adapter bank | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |
| retrieval control | 8/8 (1.00) | 8/8 (1.00) | 8/8 (1.00) |

Replay exposure was present at every update. The replay audit recorded zero
replay rows at step 0, then `8` prior-task rows at step 1, `8 + 8` at step 2,
and `8 + 8 + 8` at step 3. The validator confirmed that the selected fact IDs,
per-task replay counts, 32-row datasets, and actual dataset memberships all
matched those receipts.

Gates:

```text
solvability_floor: true
retrieval_above_no_update: true
replay_retention_above_naive: false
bank_retention_above_naive: true
candidate_eligible: false
breakthrough_claim_eligible: false
```

The repaired objective solved the local acquisition/fit problem, but replay
did not improve retention: it tied naive at `2/8`. The adapter bank retained
the target task at `8/8`, showing that a routed immutable memory mechanism can
preserve this codebook while sequential replay cannot under the current
task/update protocol. This is a protocol diagnostic, not a general continual-
learning or breakthrough result.

## Audit and validation

The independent validator returned `valid: true`. It checked the V13 source
state slice, fixed `160`-step objective, prompt contract, held-out splits,
selected fact IDs, replay counts, target-task accuracy after every update,
dataset membership, bank adapter freshness and routing, and all hashes.

A metadata-only launcher defect was found before acceptance: the wrapper had
updated the V14 contract in `result.json` without rewriting `config.json`. The
external artifact metadata was repaired, the launcher was fixed to write both
files, and the validator then passed. No model training was rerun.

Hashes:

```text
contract_sha256: a6b196b7404a8ce4aeeea0d431636757b522358b98a03d394e4b2575ec1860d2
manifest_sha256: 45fe98d2f074ca0d6feacdc241c4edbe17bc7a3cea4e5c31ba9c6c6cc5f70d30
result_sha256:   49972e067525d5fbb46b4b98a725bb2c7af4bf0b2705bca4587da0ea6e13da2f
```

Audit hashes:

```text
naive_sequential_lora: e8fa6fab56717cba907baa1f5fe7f4184d3d0b5647d687e0170424f0678f5c7e
replay_lora:           e555a96e11ca454e9447a04d40e381c6af46225d624dc39580f8fb27082683bc
task_adapter_bank:     b9b9f0b68982d505ec6eeff9ed24666721341bf62fea5c0153c48096f814b3b0
```

## Decision

Stop V14. Do not replicate, add a second model, or provision an H100. Replay
exposure is real but its retention effect is tied with naive, so the next
research object must redesign the task/update protocol rather than spend
replication or accelerator budget on this replay mechanism. The adapter-bank
result is a useful control: future designs should preserve explicit routing or
otherwise change the update interface so replay has a measurable causal target.
