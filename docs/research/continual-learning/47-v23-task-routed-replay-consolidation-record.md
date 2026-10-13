# V23 task-routed replay consolidation protocol record

State slice: `continual-learning-protocol-v23-task-routed-replay-consolidation`.

Classification: `TaskRoutedReplayConsolidationProtocolOnlyNoBreakthroughClaim`.

Claim ceiling: `LocalDevelopmentTaskRoutedReplayConsolidationProtocol`.

## Scope

V23 is a pure-data protocol preflight. It does not load a model, invoke a
trainer, create adapters, or spend replication budget. It constructs the full
three-seed by three-order schedule for the corrected task-routed replay
interface and independently validates the plan.

External plan artifact:

`/tmp/continual-learning-model-v23-task-routed-replay-protocol-plan.json`

Plan SHA-256:

`8b306619ef0c2b8cc4fb536a7485d9dbb5817c38f739cbc68aad27ae4fb66ac1`

## Result

```text
cell_count_exact: true
replay_schedule_deterministic: true
routed_no_replay_schedule_deterministic: true
same_update_row_budget: true
same_total_examples: true
same_total_optimizer_steps: true
slot_seed_policy_fixed: true
replay_rows_route_to_fact_task_slot: true
replay_not_rerunning_current_shared_design: true
model_training_authorized: false
h100_authorized: false
breakthrough_claim_eligible: false
```

The schedule preserves V22's fact-selection policy, 32 rows per update, 160
iterations per update, 128 total examples, 640 total optimizer iterations,
and fixed task-keyed slot seeds. The changed interface routes each replay fact
to its own persistent task slot, giving replay a causal path to preserve the
knowledge it is intended to retain.

## Decision

The V23 protocol contract passes. This does not establish replay retention and
does not authorize a replication matrix. The next bounded action is exactly
one corrected local model preflight of the routed replay candidate against the
routed no-replay control. Do not rerun the current shared replay design, spend
replication budget on V22's zero-effect path, provision an H100, or make a
breakthrough claim before that corrected local preflight passes its exposure
and retention gates.
