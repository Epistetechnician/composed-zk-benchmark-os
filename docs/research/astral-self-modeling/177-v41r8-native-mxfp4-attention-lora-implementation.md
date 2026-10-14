# V41R8 Native-MXFP4 Attention-LoRA Implementation

State slice: `V41R8NativeMXFP4AttentionLoRACorrection`.

Status: `LocalImplementationComplete / IndependentValidatorImplemented / ModelExecutionUnauthorized`.

RGS now contains an additive native-MXFP4 attention-LoRA contract, H100 profile
runner, and hermetic tests. Astral independently validates the success artifact
without importing RGS code. The validator recomputes:

- exact model, revision, runtime, state slice, and claim ceiling;
- native MXFP4 with `dequantize=false`;
- frozen experts, routers, attention sinks, and empty `target_parameters`;
- all 288 trainable names and complete 36-layer q/k/v/o coverage;
- 5,971,968 trainable scalars and the inventory hash;
- memory ceilings and observed model, adapter, and update receipts;
- four ordered token-weighted microbatches;
- adapter state change and exact rollback;
- normalized real candidate log probabilities;
- zero-update and rollback logit deltas within `1e-7`;
- every committed source hash.

Local verification passed 9 focused RGS tests, with one Torch-dependent module
skipped because local Torch is absent, 3 Astral validator tests, RGS
`lint:fast`, and the complete 521-test RGS `test:focused` registry gate.
The heavy RGS lint gate passed all reached code, contract, replay, native-PCSM,
and ledger checks, then stopped on two pre-existing stale public-metrics
projections outside the V41R8 state slice; those unrelated files were not
regenerated.

This evidence establishes only a bounded local implementation. It does not
establish native-MXFP4 backward compatibility, H100 memory fitness, acquisition,
retention, continual learning, Astral selection, or any scientific result.
The next possible slice is an exact-runtime no-model image parity receipt under
a separate committed authorization. Model access and paid execution remain
unauthorized.

Claim ceiling: `LocalImplementationNativeMXFP4AttentionLoRAV41R8`.
