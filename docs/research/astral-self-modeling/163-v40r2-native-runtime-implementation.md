# V40R2 Native MLX Runtime Implementation

State slice: `V40R2NativeMLXRuntimeImplementation`.

Status: `ImplementedAndHermeticallyTested / ModelUpdateNotRun`.

RGS now contains a concrete implementation of the V40R2 executable runtime.
It binds the real tokenizer, locked rank-4 LoRA and AdamW configuration,
fixed-window batches, answer-boundary logits, Qwen telemetry, gradient
clipping, exact model/optimizer identities, reversible snapshots, and all
locked fit-only scoring groups.

Feature capture computes and caches the exact scheduled current-batch gradient.
Canonical update consumes that cache without another current-batch forward.
The cache is content-bound to case ids, prompts, targets, candidate order, and
roles. Cross-batch consumption, overwrite, double consumption, or leakage
across state boundaries fails closed.

Telemetry is gathered at each row's actual answer boundary rather than padded
position 95. Layer-7 attention evidence also masks keys after that boundary.

Focused tests validate the contract and adversarial cache behavior without
loading or updating a model. No native optimizer step, model update, external
artifact, tune access, assessment access, or scientific promotion occurred.
Execution requires a separately committed native-runtime qualification smoke,
independent validator, exact source bindings, and explicit one-shot
authorization.
