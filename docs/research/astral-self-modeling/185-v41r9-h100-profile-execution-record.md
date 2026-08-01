# V41R9 H100 Profile Execution Record

State slice: `V41R9ModelBackedH100ProfileAuthorizationAndExecution`.

Status: `Consumed / RuntimeProfileOperational / PilotUnauthorized`.

GiveMeNode job `job-nburr` executed the single authorized identity on one
clock-locked NVIDIA H100 80GB HBM3 with zero restarts and preemptions. It used
RGS `2f5544d5f1707785ef509e407ba68ab656235dc8`, context `ctx-a5180e1d`, and
the pinned GPT-OSS-20B revision.

The real `PreTrainedTokenizerFast`, native non-dequantized MXFP4 checkpoint,
and real candidate logits were used. The pre-load and live configuration both
matched the pinned 24-layer geometry. Inventory validation accepted exactly 96
q/k/v/o modules, 192 LoRA tensors, and 3,981,312 trainable parameters with all
forbidden base, expert, router, sink, and MLP state frozen.

Zero-update logit drift was `0.0`. One optimizer step ran four token-weighted
microbatches over four examples with loss `6.087016188580057` and gradient norm
`15.186728477478027`. The adapter hash changed, then returned byte-exactly to
its pre-update value. Post-rollback real-logit drift was `0.0`. Peak update
allocation was 14,457,340,928 bytes, below the 72 GiB gate.

Evidence:

- job/classification: `job-nburr / RuntimeProfileOperational`;
- finished: `2026-08-01T23:31:18.118676+00:00`;
- artifact: `art-t3gu6`, SHA-256
  `658110cfd3d64e11ec49a00c374dc67c461c82e15ac68d370067f6e98b7d296b`;
- profile result file SHA-256:
  `f81aa4af7251ce6ea1d3fc1ad7975442adce80da7fa4c6e92df3742320329437`;
- result content hash:
  `c601e46531b302bb419672d0c1dc1838973047ca4b9b5e040e89ed16a286ecb7`;
- independent validation: valid, zero errors;
- validation report SHA-256:
  `8ea63dbdebf26afa0ab1533cc930eb13c142b0b26e786e0b7c04f727c807306e`;
- durable external directory:
  `/Users/shaanp/Documents/research-artifacts/astral-v41r9-operational-job-nburr/`;
- total cost: USD 0.064, no longer accruing.

Tune and assessment remained closed and the artifact declares
`scientific_result: false`. This proves only bounded runtime update and exact
recovery capability for the pinned implementation/runtime/checkpoint. It is
not acquisition, retention, continual-learning, Astral-selection,
self-improvement, or breakthrough evidence. A pilot requires a fresh
preregistration and authorization.

Claim ceiling: `RemoteH100RuntimeProfileOnlyV41R9`.
