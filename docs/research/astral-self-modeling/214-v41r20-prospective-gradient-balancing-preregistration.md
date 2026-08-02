# V41R20 Prospective Gradient-Balancing Preregistration

State slice: `V41R20ProspectiveGradientBalancingIntervention`.

Status: `ProspectivelyFrozen / ImplementationPending / ExecutionUnauthorized`.

The candidate compares one whole-adapter panel-normalized intervention against
the immutable V41R15 equal-example result
`sha256:893451b417e6654096e87e7494e638f37daf0efe5cb73c2eacf28a6b415966b3`.
At each of the unchanged 64 steps it independently averages bridge, terminal,
and protected gradients, L2-normalizes each whole panel, combines them with
shares `0.375/0.375/0.25`, and unit-normalizes the combined gradient before the
unchanged clip and AdamW update.

No V41R19 layer statistic may affect execution. All 24 LoRA layers, data,
schedule, seed, optimizer, learning rate, update budget, scoring, restart,
gates, and protected suite remain unchanged. The primary metric is persistent
accuracy minus the V41R15 value `0.2604166667`, but the method is a signal only
if every unchanged acquisition, retention, reload, and step-count gate passes.

One run may be authorized only after independent-validator implementation and
clean immutable source commits. The USD 5 additional-spend ceiling and all
fail-closed stops in the RGS preregistration apply. Tune, assessment, retries,
qualification, confirmation, continual-learning proof, and claims above
`RemoteH100PanelBalancedAcquisitionDevelopmentV41R20` are forbidden.
