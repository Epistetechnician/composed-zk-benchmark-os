# V41R7 Implementation and Torch-Parity Record

State slice: `V41R7ExpertLoRAMemoryCorrection`.

Status: `TorchParityPassed / OneH100ProfileAuthorized`.

RGS commit `6d865d147a5d912994540c3aff21eac2f090b58b` and Astral
validator commits `0cd0895` plus `d7fd65a` implement the additive microbatch
runner and fail-closed independent validator.

Inside exact Torch `2.10.0+cu128` and CUDA `12.8`, the image build passed 13/13
focused tests. These include unequal-token full-batch parity for loss,
gradients, clipping, and AdamW state at absolute tolerance `1e-7`. Corrected
context `ctx-125c868a` is 26,155,836 bytes with SHA-256
`ab3bc14c8ced013ab1f570139fbe84b86b1273379d3cac2acd93a6d7830ed679`.
The resulting image manifest is
`sha256:3ad18a5de223cf29d0cd10579f9914f3fd3aac69e676f7f4548399cf1445f3cc`.

The retained receipt was recovered on 2026-08-01. `job-t8anv` completed
successfully at `2026-07-31T17:39:14.481907Z` on one clock-locked H100 with
zero restarts and the exact result:

```json
{"classification":"V41R7TorchParityPassed","model_access":false,"scientific_execution":false}
```

This opens exactly one model-backed runtime profile under state slice
`V41R7H100ProfileExecution`. It must use RGS source commit
`6d865d147a5d912994540c3aff21eac2f090b58b`, context `ctx-125c868a`, the
manifest above, one clock-locked H100, the frozen runner, and a maximum runtime
of 300 minutes. The first terminal model attempt consumes the identity. No
scientific retry, pilot, qualification, tune, assessment, Astral selection, or
claim above `RemoteH100RuntimeProfileOnlyV41R7` is authorized.
