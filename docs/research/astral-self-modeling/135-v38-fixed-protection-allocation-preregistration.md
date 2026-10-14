# V38 Fixed Protection-Allocation Preregistration

Status: `PreregisteredAndImplementationAuthorized / ExecutionNotAuthorized`.

V38 reruns the V37 development corpus from the base checkpoint under four
equal-budget fixed schedules: recent task replay, reservoir task replay,
alternating recent/protected replay, and alternating reservoir/protected
replay. The alternating schedules use task replay on even steps and V30
protected replay on odd steps. Stage 1 remains identical.

The frozen matrix is four arms by two seeds by two orders: 16 cells, 2,048
gradient steps, and 786,432 update tokens. Every task, prompt, checkpoint,
optimizer, LoRA configuration, evaluation point, and mechanical gate remains
matched to V37.

A joint arm qualifies only if all cells pass final acquisition `>=0.75`,
protected retention `>=0.95`, finite loss, update parity, and reload; mean
prior retention is within `[0.60, 0.90]`; mean final paraphrase is `>=0.70`;
retention loss against its matched task-only control is at most `0.10`; and
that control misses protection in at least one cell.

This is outcome-informed development, not confirmation. Implementation is
authorized, execution is not. Maximum claim:
`LocalFixedProtectionAllocationDevelopmentV38`. Dynamic allocation, Astral
telemetry, CL-bench, confirmation, SOTA, and breakthrough claims remain blocked.
