# V40R2 MLX Backend Primitives

State slice: `V40R2MLXAcquisitionBackendImplementation`.

Status: `MLXPrimitivesImplemented / ExecutableBackendIncomplete`.

The implementation now contains deterministic model/optimizer tensor-tree
identities, checked snapshot restoration, zero-based residual sites 3/7/11,
layer-7 attention entropy, layer-11 MLP-output norm, residual cosine,
candidate margins, and rolling-loss reductions.

The Qwen telemetry path is implemented but has not been executed. Numerical
tests use synthetic arrays only.

Batch construction, gradient updates, protected probes, counterfactual
evaluation, runner integration, artifact coordination, and independent result
validation remain incomplete. No model execution or scientific evidence is
authorized.
