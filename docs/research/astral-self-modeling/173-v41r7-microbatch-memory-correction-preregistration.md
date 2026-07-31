# V41R7 Microbatch Memory-Correction Preregistration

State slice: `V41R7ExpertLoRAMemoryCorrection`.

Status: `ImplementationAuthorized / ExecutionUnauthorized`.

V41R7 preserves every V41 model, data, LoRA, optimizer, evaluation, rollback,
and claim boundary. It replaces only the batch-four training forward with four
ordered batch-one forwards whose losses are weighted by their nonignored
causal target-token counts. This must reproduce the full-batch mean-token loss,
gradients, clipping, and AdamW update under a zero-dropout fail-closed gate.

The additive runner may clear unused CUDA cache before training and must record
allocated, reserved, and peak memory per microbatch. Hermetic float64 parity
tests over unequal target lengths must pass at absolute tolerance `1e-7`, along
with existing V41 tests, before a separate execution authorization exists.

No model-backed run, pilot, qualification, tune, assessment, acquisition
claim, continual-learning claim, or higher claim is authorized by this
preregistration.
