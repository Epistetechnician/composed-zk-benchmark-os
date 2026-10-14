# V41R9 Checkpoint-Bound Layer-Geometry Preregistration

State slice: `V41R9CheckpointBoundLayerGeometryCorrection`.

Status: `ImplementationAuthorized / ModelExecutionUnauthorized`.

The consumed V41R8 profile proved that the pinned GPT-OSS-20B checkpoint loads
in native MXFP4 well below the memory gate, but also exposed an invalid frozen
inventory assumption. Transformers 4.57.6 defaults `GptOssConfig` to 36 layers;
the immutable GPT-OSS-20B revision's own config declares 24. The downloaded
checkpoint config SHA-256 is
`3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce`.

V41R9 may change only the geometry binding. It must require live checkpoint
configuration `num_hidden_layers == 24` before adapter construction and then
require complete q/k/v/o LoRA coverage over layers 0 through 23: 96 target
modules, 192 A/B tensors, and 3,981,312 trainable parameters. Every native
MXFP4, optimizer, microbatch, logit-parity, rollback, memory, data-boundary, and
claim-ceiling rule remains unchanged.

This slice permits additive implementation, adversarial hermetic tests,
independent validator correction, and documentation only. It does not permit
checkpoint access, an H100 run, runtime parity, pilot, tune, assessment,
scientific promotion, or retrying V41R8.
