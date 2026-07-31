# V41R7 Implementation and Torch-Parity Record

State slice: `V41R7ExpertLoRAMemoryCorrection`.

Status: `BuildParityPassed / RuntimeReceiptPending / ModelExecutionUnauthorized`.

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

Parity job `job-t8anv` reached `starting`, but GiveMeNode OAuth authorization
was lost before its no-model terminal receipt could be read. Do not duplicate
the job. Model-backed execution remains unauthorized and unrun until that
receipt is recovered and a fresh execution identity is committed.
