# V20 compact-routing replication execution record

State slice: `continual-learning-protocol-v20-compact-routing-replication`.

Classification: `CompactRoutingReplicationNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentCompactRoutingReplication`.

## Execution

V20 ran the frozen three-seed by three-order matrix once using the cached
Qwen2.5-0.5B-Instruct-4bit model. Every cell retained the V19 controls,
route-boundary prompt, 160-iteration budget, and actual adapter-byte parity
check. No cell was tuned or rerun.

Artifact directory:

`/tmp/continual-learning-model-v20-compact-routing-replication`

## Cell outcomes

| seed | order | compact acquisition | compact retention | naive retention | replay retention | byte budget |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 20260811 | 0,1,2,3 | 1.00 | 1.00 | 0.25 | 0.25 | pass |
| 20260811 | 0,2,3,1 | 1.00 | 1.00 | 0.25 | 0.25 | pass |
| 20260811 | 0,3,1,2 | 1.00 | 1.00 | 0.25 | 0.25 | pass |
| 20260812 | 0,1,2,3 | 0.25 | 0.25 | 0.25 | 0.25 | pass |
| 20260812 | 0,2,3,1 | 0.25 | 0.25 | 0.25 | 0.25 | pass |
| 20260812 | 0,3,1,2 | 0.25 | 0.25 | 0.00 | 0.25 | pass |
| 20260813 | 0,1,2,3 | 1.00 | 1.00 | 0.00 | 0.25 | pass |
| 20260813 | 0,2,3,1 | 1.00 | 1.00 | 0.00 | 0.50 | pass |
| 20260813 | 0,3,1,2 | 1.00 | 1.00 | 0.00 | 0.25 | pass |

Compact routing exceeded naive retention in 7/9 cells. It met the acquisition
floor in 6/9 cells. Actual compact-to-full adapter-byte budget matched in 9/9
cells. Balanced replay exceeded naive retention in only 4/9 cells.

## Gates

```text
cell_count_exact: true
candidate_solvability_all_cells: false
candidate_retention_above_naive_all_cells: false
parameter_budget_matched_all_cells: true
replay_retention_above_naive_all_cells: false
replication_eligible: false
breakthrough_claim_eligible: false
h100_authorized: false
```

The V19 result does not replicate as a robust seed/order-invariant effect. The
failure is concentrated in seed `20260812`, where compact routing never clears
the acquisition floor. This is evidence of seed sensitivity, not evidence of a
general continual-learning solution. Replay also remains non-robust.

## Independent validation and hash

```text
validator: valid
matrix_sha256: 51c93af11a67ac8b36515983f2abdd596f1d0a134c3db33cac4c05b86272c1b6
```

## Decision

Stop V20. Do not provision an H100. The next research object is a local
seed-sensitivity diagnosis and protocol repair, with a predeclared hypothesis
about initialization or slot-training stability before another replication.
Do not claim a breakthrough or promote V19 beyond a single-panel local pilot.
