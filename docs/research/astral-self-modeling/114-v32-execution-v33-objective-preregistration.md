# V32 Execution and V33 Target-Free Objective Preregistration

V32 status: `OptimizerDevelopmentBlocked / Consumed / ValidNegative`.

Artifact `astral-rgs-v32-optimizer-development-f2471c7c4030-r1`, manifest
`sha256:f2471c7c40308009c4e287d54f19b16a845d8dfd96af6d6ee4931042b5cd6d33`,
packet `sha256:9094f1a392e5e7660bffca1fe5a300180008afc7177905932f1ab632ad5afd28`.

Both arms retained V30 at 1.0 and converged stably, but direct and paraphrase
accuracy remained 0.125. Because the V32 training input contained the target
value, its near-zero loss is compatible with copying rather than learning the
key-value association.

V33 freezes one development arm: `fp32_clip_lr1e4`, using the same V32 keys but
the target-free input `Development registry key: <key>. Associated value:`.
The target appears only as the supervised next token. All other budgets,
controls, and gates remain those of V32.

Maximum claim: `LocalDevelopmentTargetFreeObjectiveQualificationV33`.
