# V41R8 Native-MXFP4 Attention-LoRA Preregistration

State slice: `V41R8NativeMXFP4AttentionLoRACorrection`.

Status: `ImplementationAuthorized / ModelExecutionUnauthorized`.

V41R8 is a prospective target-geometry correction for the consumed V41R6 and
V41R7 expert-parametrization OOMs. It preserves the V41 model revision,
tokenizer, corpus, cases, rank, alpha, optimizer, effective batch, ordered
token-weighted microbatches, one-step profile, scoring, rollback, and closed
tune/assessment boundary.

The only model-path changes are native MXFP4 with `dequantize=false`, frozen
base/expert/router parameters, and LoRA over exactly q/k/v/o attention
projections in all 36 layers. `target_parameters`, `all-linear`, expert LoRA,
router updates, and attention-sink updates are forbidden.

The implementation must fail closed unless it finds exactly 144 targeted
modules, 288 LoRA tensors, 5,971,968 trainable scalar parameters, no trainable
expert/router/base state, zero-update candidate-log-probability parity within
`1e-7`, a changed post-step adapter hash, exact state and logit rollback, four
ordered microbatch receipts, model-ready allocation at most 24 GiB,
pre-update adapter allocation at most 32 GiB, and runtime peak below 72 GiB.

This slice authorizes additive implementation, hermetic tests, an independent
validator, and documentation only. It does not authorize an H100 job, model
access, pilot, qualification, tune, assessment, acquisition evidence,
continual-learning evidence, Astral selection, or a claim above
`LocalImplementationNativeMXFP4AttentionLoRAV41R8`.
