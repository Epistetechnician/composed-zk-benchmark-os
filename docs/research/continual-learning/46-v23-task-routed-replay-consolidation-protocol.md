# V23 task-routed replay consolidation protocol

State slice: `continual-learning-protocol-v23-task-routed-replay-consolidation`.

Source slice: `continual-learning-protocol-v22-seed-independent-init-replication`.

## Decision basis

V22 made compact-slot acquisition and retention `1.00` in all nine seed/order
cells, including the V21 failing seed. It also verified replay examples in all
nine actual replay datasets, yet replay did not exceed naive retention in every
cell. V15 independently showed that changing replay row order worsened
retention. The remaining failure is therefore the shared update interface, not
missing replay rows or row ordering.

## One changed protocol variable

V23 changes the replay update interface to
`task_routed_replay_consolidation_v1`:

- every current or replay fact is dispatched by its own task token to the
  matching two-layer slot;
- a slot is initialized once with the fixed seed `22000000 + task_id` and a
  fresh zero AdamW state;
- later replay updates continue that same task slot and optimizer state;
- no slot receives facts from another task and no cross-task adapter resume is
  allowed.

This preserves the V22 seed-independent initialization policy and makes the
changed variable the representation/update boundary. It is not another replay
sampling or row-order experiment.

## Frozen controls

- Cached Qwen2.5-0.5B-Instruct-4bit.
- Seeds `20260811`, `20260812`, `20260813`.
- Orders `0,1,2,3`; `0,2,3,1`; `0,3,1,2`.
- Four tasks with eight train and eight held-out facts each.
- Balanced full-memory fact selection and replay capacity `24`, identical to
  V22. The candidate's replay rows are not changed; only their destination
  slot changes.
- Thirty-two rows and 160 optimizer iterations per update.
- Total per cell: 128 rows and 640 optimizer iterations.
- Four two-layer slots, matched against one eight-layer shared adapter.
- AdamW, learning rate `0.0001`, batch size `2`, maximum sequence length `192`.
- No downloads, adaptive tuning, favorable-seed selection, second model, or
  H100.

## Controls and primary metric

The corrected panel compares:

1. `routed_no_replay`: current-task rows routed to the current task slot;
2. `routed_replay`: identical update budget and fact-selection policy, with
   current and replay rows routed to their matching task slots;
3. the immutable task-adapter bank as a route-preservation ceiling.

The V22 shared naive and shared replay results remain frozen historical
references and are not rerun in this protocol. The primary metric is
`routed_replay_retention - routed_no_replay_retention`. A secondary comparison
is against the frozen V22 shared-naive retention.

## Pure-data preflight and gates

The repository preflight constructs all nine schedules without loading a model
and independently checks exact fact selection, no unseen replay facts, route
keys, per-task route counts, slot seeds, row budgets, total optimizer steps,
and deterministic plan hashing.

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

Only after this pure-data plan validates may one corrected local model
preflight be considered. That run must still pass replay exposure and strict
retention gates before any replication or accelerator allocation is discussed.
