# V37 Interference-Stream Execution Record

Status: `ValidNegative / MechanicalOrAcquisitionBlocked`.

The content-addressed artifact is
`astral-rgs-v37-interference-stream-e7a24a93e4d0-r1`, bound to clean RGS
`b50bb84` and Astral `feb178b`. Independent model-free validation returned
`valid: true` with no errors.

Tokenizer preflight covered 64 prompts with a maximum length of 83 inside the
frozen 96-token window. All 12 cells completed 1,536 gradient steps, 589,824
update tokens, 48 staged adapter saves, and restart comparisons. Final-task
acquisition, loss finiteness, reload equivalence, and update parity passed.

The interference target was reached:

- `no_task_replay` mean prior retention: `0.364583`;
- `recent_replay_25` mean prior retention: `0.791667`;
- `reservoir_replay_25` mean prior retention: `0.6875`;
- strongest replay advantage: `0.427083`;
- replay forgetting observed: `true`.

The benchmark gate still failed because three replay cells missed protected V30
retention `>=0.95`: recent forward seed 370037 scored `0.625`, recent reverse
seed 370038 scored `0.84375`, and reservoir reverse seed 370038 scored
`0.9375`.

The result identifies a local task-retention versus protected-retention
tradeoff. It does not qualify V37, validate a selector, or authorize dynamic
compression. The next defensible slice is a newly preregistered fixed replay
allocation study that restores protection under the same per-step memory and
compute budget. It must rerun matched controls and cannot tune V37 outcomes.
