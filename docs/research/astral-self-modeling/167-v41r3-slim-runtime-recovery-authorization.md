# V41R3 Slim Runtime Recovery Authorization

State slice: `V41R3SlimRuntimeRecovery`.

V41R2 job `job-c5tv2` is retained as an infrastructure-only failure and was
canceled before the scientific command ran. Its third placement attempt
remained in `starting` after the prior 8.84 GB compressed devel image timed out
during image pull. It produced no scientific result or artifact.

V41R3 authorizes one fresh H100 runtime-profile identity with the exact V41
scientific source commit `0403e731a91ead32f895b3822db8bcd044424f13`.
The runner, checkpoint revision, corpus, one-step LoRA profile, validator,
budget, stopping rule, artifact schema, and claim ceiling are unchanged.

The sole correction is the runtime container:

- official base:
  `pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime`;
- immutable linux/amd64 manifest:
  `sha256:b85566342b86d13a67712e9315d40cdc2dad7f8d86df1aff3831f80835edbcca`;
- base compressed layer total: `4,432,776,135` bytes;
- only `git` plus the six V41 pinned Python requirements are added;
- the embedded Git bundle must resolve to the exact source commit and remain
  clean;
- the image build must assert Torch `2.10.0`, Transformers `4.57.6`, PEFT
  `0.18.1`, Accelerate `1.12.0`, Kernels `0.11.7`, Safetensors `0.7.0`, and
  Torch CUDA `12.8`.

Job `job-kvmnr` is retained as a canceled pre-execution packaging attempt. Its
Docker Hub pull advanced only from 90.18 MB to 138.41 MB over approximately
179 seconds, projecting beyond the prior 30-minute pull limit. It produced no
run attempt, result, artifact, or scientific evidence.

The authorized transport correction exports the already locally validated
runtime filesystem, hashes the 8,337,189,888-byte rootfs as
`fd192bac6cb4c0f4325df507e172de3c708e382f1a39e76f129f2e89e55410c0`,
reconstructs it from `scratch`, repeats the exact source and dependency checks,
and packages it as a 3,822,107,009-byte context with SHA-256
`3cc47aae720f6ccfb89776142ca880efaa68b9818a6eb88da386a45c25936cf1`.
The finalized context is `ctx-430ce5ca`. One fresh `r2` job identity may use
this verified context. This changes transport only, not runtime bytes or the
scientific contract.

Before model access, the job must fail closed unless CUDA is available, exactly
one device is visible, the device is an H100, compute capability is at least
9.0, and the dependency assertions still pass. The runner's own hardware check
remains authoritative.

The job ceiling is `$13.50`, duration is at most 300 minutes, clock locking is
required, and `max_restarts=1`. A completed scientific command consumes V41R3
regardless of outcome. Packaging, pull, placement, or worker loss before any
run-log or artifact is retained as infrastructure evidence, not scientific
evidence.

The maximum inner-artifact claim remains
`RemoteH100RuntimeProfileOnlyV41`. V41R3 does not authorize pilot,
qualification, tune, assessment, Astral selection, continual-learning,
self-improvement, introspection, Stage 0C, Stage 1, SOTA, or breakthrough
claims.
