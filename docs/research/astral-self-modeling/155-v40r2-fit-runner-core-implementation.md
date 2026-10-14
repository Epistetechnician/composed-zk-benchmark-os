# V40R2 Fit Runner Core Implementation

State slice: `V40R2FitAcquisitionRunnerImplementation`.

Status: `TwoPassCoreImplemented / MLXBackendNotImplemented`.

The model-free orchestration core now requires complete feature sealing before
the label pass, exact model-state replay at all 384 source rows, optimizer
identity before both counterfactual branches, model and optimizer restoration
after each branch, and exact accounting of 1,024 canonical plus 768
counterfactual updates.

Hermetic tests reject second-pass state drift and counterfactual restoration
failure. Tune and assessment remain closed.

This is orchestration plumbing only. The MLX backend, internal telemetry
extraction, artifact coordinator, independent result validator, forward
passes, updates, labels, and scientific evidence remain unimplemented or
unauthorized.
