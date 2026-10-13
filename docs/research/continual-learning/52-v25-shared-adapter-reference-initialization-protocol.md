# V25 shared-adapter reference-initialization protocol

State slice: `continual-learning-protocol-v25-shared-adapter-reference-initialization`.

Source slice: `continual-learning-protocol-v24-shared-adapter-task-keyed-optimizer-state`.

## Decision basis

V24's task-keyed optimizer-state custody and replay exposure were valid, but
the shared adapter failed acquisition at `2/8` on the fixed `20260812 /
0,1,2,3` cell. A trainer-boundary differential ruled out the custom loop as
the sole cause: stock MLX LoRA reached `4/8` on the same data with the V24
initialization path. A predeclared fixed reference seed `20260811` reached
`8/8` on that same step-0 dataset.

That observation authorizes one bounded acquisition repair, not a claim. V25
changes only the shared adapter initialization seed to `20260811`, a seed
already successful in the prior compact-routing family. This is an explicit
fixed reference initialization, not adaptive seed selection during V25.

## Frozen controls

V24 remains frozen for the model, data seed, task order, prompt, fact
selection, replay capacity, examples, optimizer, learning rate, batch size,
sequence length, shared eight-layer adapter, task-keyed optimizer-state
custody, and total steps. The only changed variable is:

`shared_adapter_reference_initialization_v1`, with the seed applied after base
model load and immediately before LoRA module construction, matching the stock
MLX initialization boundary.

The candidate remains `shared_replay`; the control remains `shared_no_replay`.
No private adapter slots are introduced. Both arms update one shared adapter.

## Gates

The nine-cell pure-data schedule is inherited and independently revalidated.
Only one corrected local preflight is authorized on seed `20260812`, order
`0,1,2,3`. Required gates are replay exposure, optimizer-state persistence,
acquisition at least `6/8`, exact budgets, and matched adapter bytes. A positive
retention contrast is required before replication. H100 authorization remains
false.

If acquisition passes but replay retention ties `shared_no_replay`, reject V25
and redesign the task/update protocol. If acquisition fails, classify V25 as a
solvability failure and do not spend replication budget.
