# V36 Failed Execution and V36R2 Correction

Status: `V36ConstructionFailed / V36R2ImplementationAuthorized`.

The V36 one-shot identity is consumed. Its retained external failure directory
is `incomplete-astral-rgs-v36-d9c586dc`, bound to RGS `d9c586d` and Astral
`49f1f66`. The pinned Qwen tokenizer measured protected training prompts up to
83 tokens, exceeding the preregistered 64-token window. The worker stopped
before the first gradient step and emitted no model result.

This is neither a negative nor positive continual-learning result.

V36R2 changes only the compute window to 96 tokens and recomputes the locked
budgets: 12,288 tokens per task, 24,576 per cell, and 294,912 across 12 cells.
A tokenizer-aware preflight must cover every possible training prompt before
training. Tasks, arms, schedules, seeds, orders, steps, gates, and evaluation
points remain unchanged. Execution requires a separate one-shot authorization.
