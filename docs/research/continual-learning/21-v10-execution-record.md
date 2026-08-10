# V10 factorized solvability-control execution record

State slice: `continual-learning-protocol-v10-factorized-solvability-control`.

Classification: `FactorizedSolvabilityControlPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentFactorizedSolvabilityControlPilot`.

## Scope and execution

V10 changed one protocol variable from V9: the deterministic modular-four
residue was supplied in training and assessment prompts, while the task token's
residue-to-option codebook remained to be learned. The raw pair remained in the
prompt as a distractor. This factorized arithmetic solvability from task-memory
retention; it did not add examples, change the model, or change the memory
mechanisms.

This was exactly one changed-design local preflight:

- cached Qwen2.5-0.5B-Instruct-4bit;
- seed `20260810`, order `0,1,2,3`;
- eight train and eight held-out examples per task, with two train and two
  held-out pairs per residue;
- 32 rows per update, 24 replay capacity, AdamW at `0.0001`, batch size `2`,
  eight LoRA layers, 192-token maximum sequence length, and 40 iterations;
- naive sequential LoRA, balanced replay LoRA, immutable task adapter bank,
  no-update, context-only, and retrieval controls;
- no replication, second model, or H100 allocation.

An initial execution was rejected before acceptance because its bank audit
used the current task adapter instead of the immutable `T0` route for later
target-task checkpoints. The instrumentation and independent validator were
corrected; no result from that artifact is used. The accepted preflight
artifact directory is
`/tmp/continual-learning-model-v10-qwen-seed20260810-order0123-corrected`.

## Results

| strategy | acquisition | retention after interference | recovery |
| --- | ---: | ---: | ---: |
| no update | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| naive sequential LoRA | 3/8 (0.375) | 2/8 (0.25) | 2/8 (0.25) |
| balanced replay LoRA | 3/8 (0.375) | 2/8 (0.25) | 2/8 (0.25) |
| immutable task adapter bank | 3/8 (0.375) | 3/8 (0.375) | 3/8 (0.375) |
| retrieval control | 8/8 (1.0) | 8/8 (1.0) | 8/8 (1.0) |

The solvability guard required naive acquisition of at least 6/8; it reached
3/8. Replay retention tied naive at 2/8, while the adapter bank reached 3/8 in
this single preflight. The bank result is secondary and cannot compensate for
the failed solvability guard or establish a memory breakthrough.

```text
solvability_floor: false
replay_retention_above_naive: false
bank_retention_above_naive: true
candidate_eligible: false
breakthrough_claim_eligible: false
```

The factorized prompt improved acquisition from the V9 bank's 2/8 to 3/8 but
did not make the task sufficiently learnable under the fixed update budget.
The remaining bottleneck is still local task-codebook acquisition, not measured
runtime or memory capacity.

## Audit and validation

The independent validator returned `valid: true`. It confirmed the fixed
contract, exact prompt bytes, the held-out split, 12 generated 32-row training
datasets, selected fact-ID membership, per-task replay counts, target-task
accuracy after every update, fresh bank adapters with `resumed_from: null`, and
manifest/audit hashes.

```text
manifest_sha256: 3419cd4b4aa5e266fc6bb0ad05fdaf02758a7151daabe21983860bd91d80a298
contract_sha256: 304e2e397d480c512dae4fa4a44fa6a3a64af980c29420b32cd3bd6e36066bc0
```

Audit hashes:

```text
naive_sequential_lora: 109348443fd3be66ba69a177f6592575f88c3a0276646244a1e0047015af71f2
replay_lora:           93ef51d91648f6e2c9d0b11567b0d8fc81a8f3b0bd9ef748d9ad7ffe3e675101
task_adapter_bank:     1bcb93e36c24faf749cd1f599ea488688aec8efd798a5f06aca35a93a934046c
```

## Decision

Stop V10. Do not replicate this design and do not provision an H100. The next
research object must change the task/update protocol again to make codebook
acquisition pass the solvability guard without increasing the fixed budget.
Only after that corrected protocol passes the replay-retention gate and a
measured runtime or memory profile identifies a hardware bottleneck should an
ephemeral H100 be considered.
