# V41R6 H100 Runtime-Profile OOM Record

State slice: `V41R6PosixWrapperCorrection`.

Status: `ConsumedRuntimeProfileFailure / NoScientificResult`.

GiveMeNode job `job-qqpmx`, label
`astral-v41r6-posix-wrapper-recovery-r1`, cache-hit the provider-confirmed V41
image, reached one clock-locked H100, and executed the unchanged profile runner.

The exact model revision downloaded three checkpoint files, loaded all three
shards, performed real pre-update tokenizer/logit scoring, installed the frozen
PEFT LoRA geometry, and entered the single training forward pass. PEFT warned
that `GptOssExperts` is an unsupported layer type. During expert
`gate_up_proj` parametrization, PEFT materialized `W + delta_weight` and Torch
failed to allocate 1,014 MiB.

At failure:

- H100 capacity reported by Torch: 79.18 GiB;
- process memory in use: 78.55 GiB;
- allocated by Torch: 77.20 GiB;
- reserved but unallocated: 700.13 MiB;
- free: 632.12 MiB.

The job exited 1 without a result JSON. Artifact `art-65dkt` is 10,240 bytes,
SHA-256
`e423e3dcb7b6a12c3932450e46127a405d9a0dfca0cdeaa455c8565c3dad6c4b`,
and contains only the output directory plus `INCOMPLETE`. A byte-identical copy
is retained outside the repositories at
`/Users/shaanp/Documents/research-artifacts/astral-v41r6-oom-job-qqpmx/art-65dkt.tar`.

This is a valid runtime-profile failure. It demonstrates that the frozen
official dequantized GPT-OSS-20B plus current PEFT expert-parameter LoRA path
does not fit its one-step training forward on one 80 GB H100. It does not
measure acquisition, retention, rollback, continual learning, or Astral
selection.

No retry is authorized. A future identity requires a prospective instrument
correction and parity validation. Candidate corrections must be evaluated
without assessment access and include avoiding full expert-weight
`W + delta_weight` materialization, reducing the trainable expert target set,
activation checkpointing, or a supported native GPT-OSS LoRA implementation.
Allocator configuration alone is not justified as the primary correction:
reserved-but-unallocated memory was below the failed allocation and total free
memory was insufficient.

The claim ceiling remains `RemoteH100RuntimeProfileOnlyV41`; the profile did
not qualify.
