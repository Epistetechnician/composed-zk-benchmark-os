# V41R9 Checkpoint-Bound Layer-Geometry Implementation

State slice: `V41R9CheckpointBoundLayerGeometryCorrection`.

Status: `LocalImplementationComplete / IndependentValidatorComplete / ModelExecutionUnauthorized`.

RGS now validates the pinned GPT-OSS-20B `AutoConfig` and the loaded model
configuration independently before adapter construction. Both must declare the
exact 24-layer alternating attention schedule. The trainable gate then requires
complete q/k/v/o LoRA coverage: 96 modules, 192 tensors, and 3,981,312 scalar
parameters, with no expert, router, sink, MLP, or base trainables.

The independent Astral validator freezes the same model revision, checkpoint
config hash, geometry packet, inventory, runtime, memory, update, rollback,
real-logit, data-boundary, and source-correspondence requirements without
importing RGS implementation code.

Twenty-one focused RGS tests passed with one expected Torch-only skip. Seven
combined V41R8/V41R9 Astral tests passed. RGS `lint:fast` passed. Its complete
521-test focused registry finished with 518 passes, one skip, and two inherited
CL11 cross-family release-decision failures unrelated to V41R9; no CL11 source
was changed.

This is local implementation evidence only. V41R9 has not accessed a model or
GPU. Exact-runtime no-model parity, paid execution, pilot, tune, assessment,
acquisition, retention, continual learning, Astral selection, self-improvement,
and breakthrough evidence remain absent and unauthorized.

Claim ceiling: `LocalImplementationCheckpointBoundAttentionLoRAV41R9`.
