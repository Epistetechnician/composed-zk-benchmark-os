# V11 residue-only task-codebook execution record

State slice: `continual-learning-protocol-v11-residue-only-codebook`.

Classification: `ResidueOnlyCodebookPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentResidueOnlyCodebookPilot`.

## Scope and execution

V11 removed the raw input pair from both training and assessment prompts. Each
prompt contained only the task token and deterministic residue, so the model
had to learn a task-specific residue-to-option codebook. This was the smallest
codebook-memory control after V10's residue-visible prompt still failed its
solvability guard.

The fixed contract remained unchanged: cached Qwen2.5-0.5B-Instruct-4bit,
seed `20260810`, order `0,1,2,3`, eight train and eight held-out facts per task,
32 rows/update, 24 replay capacity, AdamW `0.0001`, batch size `2`, eight LoRA
layers, 192-token maximum sequence length, and 40 iterations. The panel was
naive LoRA, balanced replay LoRA, immutable task adapter bank, no-update,
context-only, and retrieval. No replication, second model, or H100 was used.

The direct launcher initially failed before model work because its repository
import path was missing. That launcher-only defect was corrected; the accepted
preflight was run once at:

`/tmp/continual-learning-model-v11-qwen-seed20260810-order0123`.

## Results

| strategy | acquisition | retention after interference | recovery |
| --- | ---: | ---: | ---: |
| no update | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| naive sequential LoRA | 2/8 (0.25) | 4/8 (0.50) | 2/8 (0.25) |
| balanced replay LoRA | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| immutable task adapter bank | 2/8 (0.25) | 2/8 (0.25) | 2/8 (0.25) |
| retrieval control | 8/8 (1.0) | 8/8 (1.0) | 8/8 (1.0) |

All advancement gates failed:

```text
solvability_floor: false
replay_retention_above_naive: false
bank_retention_above_naive: false
candidate_eligible: false
breakthrough_claim_eligible: false
```

Removing the raw pair did not make codebook acquisition learnable. Replay was
worse than naive retention in this preflight (`2/8` versus `4/8`). The result
does not support a memory, reasoning, or breakthrough claim.

## Fit diagnosis

A read-only post-run check of the accepted adapters found task-0 training-set
accuracy of `2/8` for the task-0 bank adapter and `4/8` for the final naive
adapter. The V11 training logs reported approximately `0.763 GB` peak memory.
The model therefore did not reliably fit the supervised codebook, and the
observed bottleneck is training/representation fit rather than accelerator
memory. Training loss alone is not treated as task accuracy evidence.

## Audit and validation

The independent validator returned `valid: true`. It confirmed residue-only
prompt bytes, held-out membership, all 12 32-row datasets, selected fact-ID
membership, replay counts, target-task accuracy after every update, fresh bank
adapters, no resume source, and manifest/audit hashes.

```text
manifest_sha256: 9cb5803ae00fb5a1e3e2736f011de33b61de567207fdfb64a10859953e5a4f27
contract_sha256: 6edcae1a0b486ec6a9313e5233549dc061ba1d471797a362325e11dfd85ff220
```

Audit hashes:

```text
naive_sequential_lora: e7eb46c1fd04bf51af773df4342ef1d243c5c81e1dfd3c96bd72180ddc5e989f
replay_lora:           c9d4234cd09a7262732dcd1ef4df967156ab09f44ab075f05071d67c4694ab1a
task_adapter_bank:     6391950778197cb68e63a1e245fa6dc5ff23f30d79a2d94863b597d3a8701b82
```

## Decision

Stop V11. Do not replicate it and do not provision an H100. The next research
object is `v12-training-fit-audit`: mechanically verify the training objective,
completion-token supervision, exact train/evaluation prompt parity, and
per-adapter training accuracy before comparing retention mechanisms again.
That audit must pass a fit floor before another replay or memory preflight is
authorized.
