# V41R17 Prebuilt-Image Gradient Profile Authorization

State slice: `V41R17ProviderResolvedGradientProfileExecution`.

Status: `AuthorizedOnce / NotYetExecuted`.

Provider ticket `tkt-uktwn` remains open for the V41R16 registry publication
failure. V41R17 authorizes one distinct prebuilt-image execution that bypasses
image build and push entirely. It is bound to the pinned PyTorch 2.10/CUDA 12.8
image digest, source context `ctx-b71ccbe0` with SHA-256
`17722f66631eed9fc287613e9842322d4bcb245d87baf1ca0adf788a15b34d83`,
RGS implementation commit `0e8197fca05c42bd64ad74173385845d06c615ae`, and
Astral validator commit `a5aca309b75350937e801330be5d54282261207a`.

The source archive and repository bundle must be hash-verified inside the
runtime before installation or execution. The sole job uses one clock-locked
H100, zero restarts, a 180-minute ceiling, POSIX `set -eu`, and fresh mission
and idempotency identities. Any terminal outcome consumes the authorization.

All scientific boundaries remain those of V41R16: initialized-adapter raw
gradient capture only, no optimizer, no update, no query scoring, no selector,
no tune, and no assessment. A validated result reaches only
`RemoteH100GradientInterferenceDiagnosticV41R16`.
