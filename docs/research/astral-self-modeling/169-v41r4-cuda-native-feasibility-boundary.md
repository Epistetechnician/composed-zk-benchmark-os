# V41R4 CUDA-Native Feasibility Boundary

State slice: `V41R4CudaNativeFeasibilityDesign`.

Status: `DesignComplete / ScientificExecutionUnauthorized`.

## Decision

The catalog `cuda-12.4` image is suitable for a CUDA-native infrastructure
probe, but it is not a scientifically equivalent runtime for the locked V41
profile. V41 remains unchanged and scientifically unrun.

The inspected image contains Ubuntu 22.04, NVIDIA driver 580.159.03, CUDA
12.4.131 with `nvcc`, Python 3.10.12, and an H100 with compute capability 9.0.
It does not contain Torch, Transformers, PEFT, Accelerate, Safetensors, NumPy,
or any other inspected model runtime.

## Required V41 operations

The immutable V41 runner requires all of the following:

1. exact Harmony chat-template tokenization for
   `openai/gpt-oss-20b` revision
   `d0e2aa76789354d715f8b22553b9feb6c462fcf0`;
2. MXFP4 checkpoint loading with deterministic dequantization;
3. bfloat16 causal-language-model forward passes and real candidate logits;
4. LoRA injection into all linear modules and selected mixture-of-experts
   parameters;
5. automatic differentiation, cross-entropy loss, gradient clipping, and
   AdamW;
6. byte-inventoried trainable state, one optimizer update, exact adapter
   rollback, and post-rollback real-logit replay;
7. exact locked package and runtime identities.

CUDA and `nvcc` provide kernels and compilation primitives, not these
model-, tokenizer-, optimizer-, adapter-, or serialization-level semantics.
A fresh CUDA/C++ implementation would be a new experimental instrument. It
could not inherit V41's preregistration, parity assumptions, validator, or
claim ceiling without an independently validated equivalence campaign.

## Two-lane design

### Lane A: catalog-native CUDA probe

Lane A may use only the inspected catalog image and must remain
infrastructure-only. A future separately authorized command may:

- record OS, driver, GPU, compute capability, CUDA compiler, free disk, and
  clock-lock identities;
- compile a small `sm_90` CUDA program with `nvcc`;
- execute deterministic bfloat16 matrix multiplication and reduction kernels;
- verify repeatability, finite outputs, device memory allocation, and
  host/device transfer;
- record peak memory, wall time, and hashes in a repository-external artifact;
- stop the node immediately.

Lane A must not access the model, tokenizer, corpus, assessment material, or
V41 runner. Passing Lane A establishes only
`RemoteH100CudaToolchainOperationalV41R4`. It is not real-logit, acquisition,
training, continual-learning, or scientific evidence and does not consume a
V41 scientific identity.

### Lane B: unchanged V41 runtime profile

Lane B remains the only scientific route. It must use source commit
`0403e731a91ead32f895b3822db8bcd044424f13`, the unchanged V41 runner and
corpus, and the exact locked Python packages. Preferred transport order:

1. provider catalog image or snapshot with Torch 2.10.0 and CUDA 12.8;
2. provider-side clone of a previously built verified image;
3. restored high-throughput package or object transport;
4. a content-addressed wheelhouse uploaded once and reused from persistent
   storage.

Before execution, the environment must prove exact package versions, CUDA
availability, one visible H100, compute capability 9.0 or greater, real
tokenizer loading, and one deterministic no-training real-logit probe. Any
runtime correction requires a fresh identity and must not change the
scientific source, data, thresholds, or evaluation.

## Rejected substitutions

The following do not preserve V41:

- replacing real logits with a synthetic CUDA kernel;
- implementing a partial tokenizer or approximate Harmony formatting;
- using random or generated weights;
- replacing MXFP4 with an unvalidated precision or quantization path;
- hand-coding only the LoRA update while changing the model forward path;
- treating a CUDA microbenchmark as model-backed acquisition;
- changing the locked package versions merely because the base image is
  CUDA 12.4.

## Gate

Do not redesign the scientific experiment around the catalog image. Use the
catalog image to falsify hardware/toolchain problems cheaply, then add or
mount the exact higher-level runtime. If the exact runtime cannot be supplied,
V41 remains `RuntimeProfileNotRun`.

