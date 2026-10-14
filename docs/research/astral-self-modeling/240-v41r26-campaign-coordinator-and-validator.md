# V41R26 Campaign Coordinator and Independent Validator

State slice: `V41R26CrashSafeCampaignCoordinatorAndAggregationValidator`.

Status: `Implemented / LocallyValidated / ExecutionUnauthorized`.

The RGS coordinator is fixed to the passing V41R26 preflight result
`sha256:e87b2e95ce6058bf0f00d556b8a8d900c89805b416b9983de21668ed6db7ed13`.
It executes the preregistered 48-run cross-product sequentially, refuses dirty
source, stops on the first failed worker, and resumes only complete worker
directories whose result hash, frozen run specification, contract binding, and
nested manifest are exact.

The Astral campaign validator independently checks all 48 worker bundles using
the worker validator, reconstructs the panel-level estimator and Wilson bound,
checks the exact worker census and order, verifies the aggregate result hash and
top-level manifest, and resolves the committed coordinator, worker, method, and
runtime-lock hashes through Git. Missing, partial, extra, reordered, corrupted,
or source-unavailable evidence fails closed.

This slice authorizes no GPU execution or spending. It establishes executable
and independently checkable campaign infrastructure, not a positive result,
confirmation, continual-learning evidence, SOTA evidence, or Stage 0C evidence.
