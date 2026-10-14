# V41R5 Cached-Image Recovery Authorization

State slice: `V41R5CachedImageRecovery`.

Status: `AuthorizedOnce / NotRun`.

GiveMeNode confirmed that the corrected V41 image from failed run job
`job-psr8z` built successfully and remains in the provider's internal registry
as image digest
`sha256:d2f1e6723868bb4a88c072502cfe6812a5b0d109144432303d11df68e79a8528`.
Only that job's run worker was lost; the image is intact.

V41R5 authorizes one fresh cache-only recovery identity using the byte-identical
original build inputs:

- context `ctx-c93262db`, 26,136,797 bytes, SHA-256
  `e10cf1c0462b43780a91a15e17a0c09f0a97e41739abe045455e9c0989bb341f`;
- Dockerfile path `Dockerfile`;
- no build arguments;
- source commit `0403e731a91ead32f895b3822db8bcd044424f13`;
- one clock-locked H100;
- maximum duration 300 minutes and maximum cost $13.50;
- at most one provider-managed restart after worker loss.

The new command may change only artifact naming. The runner, model revision,
tokenizer, corpus, one-step LoRA profile, dependency versions, validator,
thresholds, and claim ceiling remain unchanged.

Submission must immediately reuse cached image digest
`sha256:d2f1e6723868bb4a88c072502cfe6812a5b0d109144432303d11df68e79a8528`.
If the job enters `building`, it must be canceled before a scientific attempt.
A completed scientific command consumes V41R5 regardless of outcome.

The maximum result remains `RemoteH100RuntimeProfileOnlyV41`. Pilot,
qualification, tune, assessment, continual-learning, self-improvement,
introspection, Stage 0C, SOTA, and breakthrough claims remain unauthorized.
