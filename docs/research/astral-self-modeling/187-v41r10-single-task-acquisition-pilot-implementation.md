# V41R10 Single-Task Acquisition Pilot Implementation

State slice: `V41R10AcquisitionPilotDesignAndImplementation`.

Status: `LocalImplementationComplete / IndependentValidatorComplete / ExecutionUnauthorized`.

RGS now contains the frozen pure-data pilot contract, balanced context-free and
context-only query construction, deterministic 32-step update schedule,
fail-closed gate algebra, and a real-model runner. The runner must destroy the
training model before loading a fresh pinned base and restoring the serialized
attention-LoRA state. Evaluation after reload contains no source facts,
retrieval context, or candidate panel in the prompt.

The independent Astral validator imports no RGS code. It recomputes metrics and
classification from raw rows and checks source-context flags, conditional-
likelihood normalization, selected candidates, protected retention, exact step
and microbatch coverage, state reload, adapter file hash, memory ceilings,
manifest, runtime/model/corpus/config locks, and committed-source hashes.

Twelve focused RGS tests and six independent Astral tests passed. RGS
`lint:fast` and both `git diff --check` gates passed. No V41R10 model or GPU
execution occurred.

Claim ceiling: `LocalImplementationSingleTaskAcquisitionPilotV41R10`.
