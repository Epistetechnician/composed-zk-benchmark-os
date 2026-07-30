# V36R2 Two-Task Execution Record

Status: `ValidNegative / TwoTaskContinualLearningPilotBlocked`.

The content-addressed artifact is
`astral-rgs-v36r2-two-task-stream-c39462eb2676-r1`, bound to clean RGS
`5e33a04` and Astral `8cc1910`. Independent model-free validation returned
`valid: true` with no errors.

The tokenizer preflight covered 48 prompts, measured a maximum of 83 tokens,
and passed the frozen 96-token window. All 12 cells completed 768 total
gradient steps and 294,912 exact update tokens. Adapter reload, finite-loss,
schedule, protected-retention, and update-parity checks passed.

The candidate did not qualify:

- `no_task_replay` mean first-task retention: 0.40625.
- `task_replay_25` mean first-task retention: 1.0.
- `joint_replay_25` mean first-task retention: 1.0.
- joint advantage over the strongest baseline: 0.0; required: 0.1.
- one shared seed/order first-acquisition score: 0.5; required: 0.75.
- protected V30 accuracy: 1.0 in all cells.

The bounded conclusion is that ordinary task replay was sufficient to prevent
forgetting in this small two-task stream, while joint protected replay supplied
no measured advantage. This does not validate continual-learning SOTA,
recovery, dynamic compression, self-improvement, or a breakthrough. CL-bench
and confirmation remain unauthorized.
