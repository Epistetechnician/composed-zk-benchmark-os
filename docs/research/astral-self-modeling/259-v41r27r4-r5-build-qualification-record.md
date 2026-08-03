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
