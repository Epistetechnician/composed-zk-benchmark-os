# V41R9 Exact-Runtime No-Model Parity Authorization

State slice: `V41R9ExactRuntimeNoModelParity`.

Status: `ExactRuntimeNoModelParityPassed / IdentityConsumed / ModelExecutionUnauthorized`.

One clock-locked H100 job with zero restarts and a 30-minute run ceiling may
build and test the exact V41R9 image. It is bound to RGS commit
`2f5544d5f1707785ef509e407ba68ab656235dc8`, context tar SHA-256
`9b72439b3b5cca753a3834535726a1e11857f19244db80b9614a4485c05a2432`,
Dockerfile SHA-256
`085308eacffbed88433264f7a66854f87a673c46820fb79e7dde41771502ac05`,
and the pinned Torch 2.10.0/CUDA 12.8 base image.

The build/run may verify dependencies, CUDA/H100 identity, native MXFP4,
checkpoint-free 24-layer GPT-OSS configuration, and hermetic V41R9/V41R8/V41
tests. It may not access the GPT-OSS tokenizer, checkpoint, or weights. Any
terminal failure consumes the identity. A pass opens only a separate
model-backed profile review and cannot establish a scientific claim.

## Execution receipt

- mission: `astral-v41r9-runtime-parity-r1`;
- job: `job-tr7dz`;
- terminal state/classification:
  `succeeded / V41R9ExactRuntimeParityPassed`;
- hardware: one clock-locked H100 at 1590 MHz;
- attempts/restarts/preemptions: one/zero/zero;
- checkpoint configuration SHA-256:
  `3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce`;
- validated geometry: `gpt_oss`, 24 hidden layers;
- model/tokenizer/checkpoint access: false;
- scientific execution: false;
- final cost: USD 0.045, no longer accruing;
- finished: `2026-08-01T22:16:37.788592+00:00`.

This is structural runtime evidence only. It does not validate acquisition,
retention, continual learning, self-improvement, or an Astral scientific
claim. The identity cannot be rerun. A paid V41R9 model-backed profile requires
a new explicit authorization and review.
