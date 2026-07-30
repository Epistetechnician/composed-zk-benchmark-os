# V36 Two-Task Continual-Learning Pilot Preregistration

State slice: `astral-rgs-v36-two-task-stream-preregistration`.

Status: `DocsFirstPreregistered / ImplementationUnauthorized / NotRun`.

V36 freezes two new eight-association tasks, orders `A_then_B/B_then_A`, seeds
`360036/360037`, and matched arms `no_task_replay`, `task_replay_25`, and
`joint_replay_25`. First-task training is identical. Second-task mixtures are
respectively `3 current + 1 V30`, `3 current + 1 prior`, and
`2 current + 1 prior + 1 V30`.

Every task uses 32 batch-4 steps with fixed 64-token compute windows: exactly
8,192 update tokens per task and 16,384 per cell. Qwen checkpoint, rank 4,
eight layers, float32 target loss, clipping 1.0 and learning rate `1e-4` are
locked.

Per-cell gates: first-task acquisition `>=0.75`, second-task acquisition
`>=0.75`, retained first-task direct/paraphrase `>=0.75`, forgetting
`<=0.125`, V30 protection `>=0.95`, exact reload, finite nonincreasing loss.
The candidate must pass all four seed/order cells and exceed the strongest
matched baseline's mean retained-first-task accuracy by `>=0.10`.

Maximum claim: `LocalTwoTaskContinualLearningPilotV36`.
