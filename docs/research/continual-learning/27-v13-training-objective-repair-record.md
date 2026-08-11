# V13 training-objective repair record

State slice: `continual-learning-protocol-v13-training-objective-repair`.

Classification: `TrainingObjectiveRepairPilotNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentTrainingObjectiveRepairPilot`.

## Scope

V13 ran one changed-design, fit-only preflight against the accepted V11
residue-only prompt contract. The only changed variable was the optimization
iteration count: `40` to `160`. The model, seed, task order, dataset facts,
optimizer, learning rate, batch size, LoRA depth, sequence length, and total
training rows were fixed. Two fresh frozen-base controls were trained: a naive
fit adapter and a task-adapter-bank fit adapter.

Artifact directory:

`/tmp/continual-learning-model-v13-fit-repair`.

No retention comparison, replication panel, second model, or H100 was used.

## Findings

| check | result |
| --- | --- |
| fit controls | naive and task-adapter-bank |
| rows per control | 32, repeated from 8 task-0 training facts |
| total dataset rows audited | 64 |
| exact prompt/completion parity | passed |
| labels A/B/C/D single-token supervision | passed |
| naive fit | 8/8 (1.00) |
| task-adapter-bank fit | 8/8 (1.00) |
| final train/validation loss | 0.0 / 0.0 for both controls |
| final training step | 160 for both controls |
| final weights receipts | passed for both controls |
| maximum reported peak memory | 0.765 GB |
| fit floor, required 6/8 for both | passed |

The training-objective repair removed the prior fit failure under this local
pilot configuration. This result establishes fit adequacy for a subsequent
retention test; it does not establish replay benefit, retention improvement,
general continual-learning performance, or a breakthrough.

Independent validator:

```text
valid: true
fit_floor_passed: true
prompt_completion_parity: true
single_token_label_supervision: true
training_receipts_complete: true
```

Hashes:

```text
contract_sha256: add94c50014fa796110a8d4bc3304e1470ce452ffcb9086aa23c20fa3f915d84
manifest_sha256: 0a91fdd16fd579524b7dddb9d2153e275940425f8c8a204c16d969cf909ba3e9
result_sha256:   0cb81b1d7bf92b24bbfee1a166d440e0a04dad99612403ca1a449350fdc1bbaa
```

## Decision

Accept the V13 fit gate and stop this fit-only slice. The next authorized
research object is a retention preflight that carries the `160`-iteration
objective repair into the existing fixed-budget task/update comparison. It
must preserve the V11 residue-only solvability contract, total examples,
optimizer, seed, and task order, and must retain explicit replay exposure
audits. Provision an ephemeral H100 only if that corrected retention protocol
passes its scientific gates and local runtime or memory is demonstrated to be
the remaining bottleneck.
