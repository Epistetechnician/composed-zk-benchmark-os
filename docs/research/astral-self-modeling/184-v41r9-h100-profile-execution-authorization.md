# V41R9 H100 Profile Execution Authorization

State slice: `V41R9ModelBackedH100ProfileAuthorizationAndExecution`.

Status: `Consumed / RuntimeProfileOperational / PilotUnauthorized`.

Exact-runtime no-model parity passed as `job-tr7dz`. One fresh model-backed
profile may test the corrected 24-layer GPT-OSS-20B native-MXFP4 attention-LoRA
runtime path. This is operational runtime qualification only.

The identity is bound to:

- RGS `2f5544d5f1707785ef509e407ba68ab656235dc8`;
- model `openai/gpt-oss-20b` at revision
  `d0e2aa76789354d715f8b22553b9feb6c462fcf0`;
- checkpoint configuration SHA-256
  `3a2a26ded679375b7928ddeca59764df7cea83220c1961035f6d6e232659e9ce`;
- context `ctx-a5180e1d`, 26,183,982 bytes, SHA-256
  `9b72439b3b5cca753a3834535726a1e11857f19244db80b9614a4485c05a2432`;
- Dockerfile SHA-256
  `085308eacffbed88433264f7a66854f87a673c46820fb79e7dde41771502ac05`;
- repository bundle SHA-256
  `5a609c15b040df74998dfb8b9878f6616bed757f310f19b9bffeb817b714319f`;
- Torch `2.10.0+cu128`, CUDA `12.8`, Transformers `4.57.6`, PEFT `0.18.1`;
- one clock-locked H100, zero restarts, 300 run minutes, USD 13.50 maximum;
- exact runner `scripts/run_v41r9_h100_profile.py --execute`.

The profile must use the real tokenizer, real logits, native non-dequantized
MXFP4 base, exact 24-layer/96-module/192-tensor/3,981,312-parameter inventory,
zero-update parity, one four-microbatch token-weighted optimizer step, all
memory ceilings, changed adapter state, byte-exact rollback, and post-rollback
logit parity. Failure must retain its fail-closed artifact.

The first terminal outcome consumes the identity. No restart, retry,
resubmission, adaptive patch, pilot, qualification, tune, assessment, Astral
selection, or scientific promotion is authorized. Maximum passing ceiling:
`RemoteH100RuntimeProfileOnlyV41R9`.

The authorized identity completed as job `job-nburr`. Its immutable outcome is
recorded in
`docs/research/astral-self-modeling/185-v41r9-h100-profile-execution-record.md`.
This authorization cannot be reused.
