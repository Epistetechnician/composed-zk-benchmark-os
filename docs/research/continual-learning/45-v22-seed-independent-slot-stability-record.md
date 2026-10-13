# V22 seed-independent slot stability execution record

State slice: `continual-learning-protocol-v22-seed-independent-init-replication`.

Source slice: `continual-learning-protocol-v21-seed-sensitivity-diagnosis`.

Classification: `SeedIndependentSlotStabilityReplicationNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentSeedIndependentSlotStabilityReplication`.

## Execution

V22 ran exactly one three-seed by three-order changed-design matrix over the
cached Qwen2.5-0.5B-Instruct-4bit model. The compact candidate changed only
slot initialization and fresh optimizer-state selection: every task slot used
the fixed seed `22000000 + task_id`, started a fresh zero AdamW state, and did
not resume another slot. The inherited naive sequential LoRA, balanced replay
LoRA, and immutable adapter-bank controls retained their V20 training paths.

Artifact directory:

`/tmp/continual-learning-model-v22-seed-independent-slot-replication`

Matrix SHA-256:

`24d5ad189188543607fc0ccd72ea70184ae7365020cfa1ecc39cef1635911b51`

## Compact candidate outcome

| seed | order cells | acquisition | retention | naive retention | replay retention |
| ---: | --- | ---: | ---: | ---: | ---: |
| 20260811 | all three | 1.00 in 3/3 | 1.00 in 3/3 | 0.25 in 3/3 | 0.25 in 3/3 |
| 20260812 | all three | 1.00 in 3/3 | 1.00 in 3/3 | 0.25, 0.25, 0.00 | 0.25, 0.25, 0.25 |
| 20260813 | all three | 1.00 in 3/3 | 1.00 in 3/3 | 0.00 in 3/3 | 0.25, 0.50, 0.25 |

The V21 failing seed no longer fails: compact acquisition and retention are
`1.00` in all 9/9 cells. The four task-slot adapter identities are identical
across all cells, and the matched adapter-byte budget passes in all cells.

## Replay exposure and advancement gates

The independent validator reconstructed route-bound rows from the task facts
and verified every recorded replay fact against the actual
`replay_lora/step-*/train.jsonl` files. Replay exposure is therefore present
in 9/9 cells, with 32 training rows per update and eight target-task facts
replayed after each later update. Despite that exposure, replay retention does
not exceed naive retention in every cell.

```text
candidate_solvability_all_cells: true
candidate_retention_above_naive_all_cells: true
parameter_budget_matched_all_cells: true
replay_exposure_valid_all_cells: true
replay_retention_above_naive_all_cells: false
slot_seed_policy_valid_all_cells: true
slot_adapter_identity_consistent_all_cells: true
replication_eligible: true
breakthrough_claim_eligible: false
h100_authorized: false
```

Candidate slot peak memory was `0.632..0.654` GB, with observed throughput of
`14.268..28.861` iterations per second. A runtime or memory bottleneck is not
demonstrated. The positive compact-routing stability result is local evidence,
not a general continual-learning, replay, SOTA, production, or breakthrough
claim.

## Decision

Keep V22 as evidence that the V20 seed sensitivity was consistent with
seed-dependent compact-slot initialization and fresh optimizer-state selection.
Stop the current replication lane because replay exposure is present but the
replay-retention gate remains non-robust. Do not provision an H100. The next
research object is a preregistered task/update protocol redesign that targets
replay retention directly while preserving the now-stable slot-state policy;
do not spend another replication budget on the current replay design.
