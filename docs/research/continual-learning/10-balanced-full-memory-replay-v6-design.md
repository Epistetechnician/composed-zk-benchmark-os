# Balanced full-memory replay v6 design

Status: `ProspectiveLocalDevelopmentProtocolDesign`.

State slice: `continual-learning-model-adapter-v6-balanced-full-memory-replay-design`.

## Reason for redesign

V5 proved that replay examples reach the training datasets, but replay does not
improve target-task retention. The target task receives 8 replay facts after
the first update, then only 4 and 3 as more tasks enter the reservoir. The
failure is therefore not an absent-replay plumbing defect. It is an ineffective
update allocation under the v5 contract.

## Proposed update path

Use full balanced replay over every previously observed task while keeping the
naive and replay strategies matched on total examples per update:

- eight current-task facts per update;
- eight replay facts for every previously observed task;
- update budget `32` at every step;
- replay capacity `24`;
- replay policy `balanced_full_memory_v1`;
- naive strategy repeats its eight current-task facts to the same 32-row
  budget;
- replay strategy uses each prior task's eight facts exactly once at later
  updates.

At the final update, task 0 receives eight replay facts rather than the three
facts observed in v5. The comparison remains budget-matched, and the optimizer,
learning rate, batch size, LoRA layer count, sequence length, seed, order, and
training steps remain fixed unless a new protocol explicitly records a change.

## Advancement gate

This design is prospective only. Run one local preflight after implementation.
Require:

1. the audit validator confirms exact per-task replay exposure;
2. replay retention exceeds naive retention on the same target facts; and
3. the result remains below any breakthrough claim ceiling until replication
   across seeds, orders, and a second model is separately authorized.

If full balanced replay still ties naive retention, stop changing replay
allocation. Redesign the task itself around a pre-registered compositional or
held-out generalization target before any replication or H100 allocation.

No H100 is authorized by this design. The v5 preflight is complete and remains
the only v5 run.
