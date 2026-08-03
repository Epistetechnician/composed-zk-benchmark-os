# V41R27R4 and V41R27R5 build-qualification record

These build-only state slices did not execute scientific workers and do not
change any Astral evidence state or claim ceiling.

## V41R27R4

Job `job-d9t9t` failed at attempt zero before container start because the pinned
PyTorch runtime image did not provide `conda`. No optimizer was constructed and
no scientific result exists. The identity is terminal and was not retried.

## V41R27R5

Job `job-a3n8u` failed at attempt zero before image construction. Its uploaded
context was a plain tar, but the provider requires a Zstandard-compressed tar.
The terminal error was `Unknown frame descriptor`. No image layer ran, no
container started, no model was accessed, no optimizer was constructed, and no
scientific result exists. The identity is terminal and was not retried.

RGS commit `d6c17e513635bcb284ce975d053c515cfb97423f` adds fail-closed
content-addressed source-archive identity. Its build context binds raw archive
SHA-256 `481a54f3dd1857567cb8b2f7f43906140f4aea07b8fd58433ae9699dfca52b5f`
and extracted tree SHA-256
`2c807f1e0c2007c8dade5e922e2531ae54a3fa9afe831d5b6872f230a66d68a8`.

## Next bounded state slice

`V41R27R6ZstdContextBuildQualification` may only re-encode the byte-identical
V41R27R5 context as a Zstandard-compressed tar, validate that transport locally,
and run one zero-restart build-only canary. It does not authorize scientific
execution, assessment access, claim promotion, confirmation, SOTA,
introspection, or self-improvement. Failure consumes the identity without
retry.

The claim ceiling remains
`RemoteH100AGEMPartialQualificationInfrastructureInterruptedV41R27R2`.

## V41R27R6

Job `job-xw96t` accepted and extracted the corrected Zstandard context, then
failed at attempt zero because the pinned base image's externally managed Python
environment rejected system-level `pip install` under PEP 668. No container
started, no GPU or model was accessed, no tokenizer was loaded, no optimizer
was constructed, no runtime charge was added, and no scientific result exists.
The identity is terminal and was not retried.

`V41R27R7IsolatedPythonBuildQualification` may run one build-only canary that
creates an isolated virtual environment inheriting the base image's pinned
PyTorch, installs the exact frozen requirements there, and corrects the
build-time source-identity assertion to compare the exact commit/hash tuple.
It may not use
`--break-system-packages`, OS package installation, Conda, a different base
image, scientific workers, assessment access, or claim promotion.

The locally verified V41R27R7 context has SHA-256
`cfb68090d2a151d0c7910070561bf3e902cf08b673660f02d8db83bcaf8585f5`,
size 83,584,855 bytes, and provider identity `ctx-f748a052`. Build-only job
`job-hjv44` is attempt zero with zero restarts, a one-minute runtime ceiling,
and maximum runtime charge `$0.04995`. Its submitted, queued, or building state
does not qualify the image and does not change the claim ceiling.

## V41R27R7 terminal result and V41R27R8 boundary

Job `job-hjv44` failed at attempt zero because the pinned image omits
`ensurepip` and `python3.12-venv`; its isolated environment could not be
created. No container started, no GPU or model was accessed, no tokenizer was
loaded, no optimizer was constructed, no runtime charge was added, and no
scientific result exists. V41R27R7 is terminal and was not retried.

`V41R27R8PinnedContainerPythonBuildQualification` may replace only that failed
layer with pip's documented PEP 668 override inside the immutable container,
then require `pip check` and exact direct-package version assertions. It remains
one zero-restart build-only canary and does not authorize scientific workers,
assessment access, or claim promotion.

## V41R27R8 terminal result and V41R27R9 boundary

Job `job-2y6wt` installed the frozen requirements and passed `pip check`, then
failed because its version assertion expected `torch` metadata `2.10.0` rather
than the pinned CUDA build's PEP 440 local version `2.10.0+cu128`. It did not
start a container or produce scientific evidence and is terminal.

`V41R27R9CudaLocalVersionBuildQualification` may change only that assertion to
the exact observed local version. It remains a zero-restart build-only canary
without assessment access, scientific-worker authorization, or claim promotion.

## V41R27R9 terminal result and V41R27R10 boundary

Job `job-nm97u` passed pinned installation, `pip check`, and exact package
versions, then failed the source-tree binding after BuildKit directory-copy
reconstruction. The submitted context independently reproduces the frozen hash
when decompressed locally. No model, GPU, tokenizer, optimizer, or scientific
execution occurred, and V41R27R9 is terminal.

`V41R27R10ArchiveExtractionBuildQualification` may verify and extract the raw
content-addressed Git archive inside the image, add the immutable binding, run
the unchanged validator, and correct the canary's return-value assertion. It
may not regenerate the binding or authorize scientific execution or claims.

V41R27R10 context `ctx-59535d63` has SHA-256
`11b00616f2c6fedbcc994e2104a530ed850d5d3b4dbcd0053e36838b60d17cfa`
and size 41,751,817 bytes. Job `job-md3dg` is attempt zero with zero restarts,
a one-minute runtime ceiling, and maximum runtime charge `$0.04995`. Building
does not change any evidence or claim state.

## V41R27R10 provider finalization hold

BuildKit completed the full image, exact 20-file model snapshot, image manifest
`sha256:7831a071c81717267cbdb2dd316d52a47a0bd1e2115a482ddc4f6e91ed9732c5`,
config `sha256:274e20cb25a65f9ae5c04101832713bc5dfbb07d58b0d53e794df8b595ddf6a0`,
and tarball transfer. Job `job-md3dg` still reported `building` after the
configured 90-minute build ceiling, before H100 runtime or tokenizer execution.

Provider ticket `tkt-6smjh` requests reconciliation of that stuck state without
retry or substitution. The canary is not passed, failed, or scientific evidence
while provider state remains nonterminal. The claim ceiling is unchanged.
