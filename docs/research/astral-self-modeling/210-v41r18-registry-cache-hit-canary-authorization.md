# V41R18 Registry Cache-Hit Canary Authorization

State slice: `V41R18RegistryRepairCanaryAndGradientProfile`.

Status: `CanaryAuthorizedOnce / ScientificExecutionUnauthorized`.

One no-model provider canary is authorized against the exact V41R15 build key:
context `ctx-e84c48d1`, size 26,241,090 bytes, SHA-256
`f36707f96030fb3f6e7b8dcabf27a0d4c59728d37224b6b449dc85acd7fb344e`,
and `Dockerfile`. Successful job `job-kgyid` establishes that this image already
exists in the provider cache.

The canary may verify only PyTorch `2.10.0+cu128`, CUDA `12.8`, exactly one H100,
and source commit `4cf2d05fec573e873eab5d1e3ff909aa52788d62`. Model loading, source injection,
adapter construction, gradients, optimization, data scoring, and scientific
claims are forbidden. Use one clock-locked H100, zero restarts, a 15-minute
ceiling, and one fresh mission/idempotency identity.

A pass establishes only that the known cached image can dispatch through the
repaired registry path. Scientific V41R18 execution requires a separate
commit-bound authorization after the canary completes.
