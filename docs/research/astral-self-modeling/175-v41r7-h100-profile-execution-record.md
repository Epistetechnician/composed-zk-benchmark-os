# V41R7 H100 Profile Execution Record

State slice: `V41R7H100ProfileExecution`.

Status: `Consumed / RuntimeProfileIncomplete / ExpertParametrizationOOM`.

GiveMeNode job `job-e52w6` ran the single authorized profile on one
clock-locked H100 with zero restarts. It used RGS source
`6d865d147a5d912994540c3aff21eac2f090b58b`, exact context
`ctx-125c868a`, real GPT-OSS-20B weights, and the real tokenizer.

The run loaded all three checkpoint shards, completed direct and protected
pre-update scoring, and entered the first batch-one update forward. It failed
inside PEFT's expert `nn.Parameter` parametrization at `W + delta_weight` while
requesting 508 MiB with only 444.12 MiB free. Model-ready allocation was
41,830,484,480 bytes; final recorded peak allocation was 83,140,182,016 bytes.

Artifact `art-jyidx` is 10,240 bytes with SHA-256
`b8b7a05cf860de17309c64a5e4a41bbbf1ae161c2b40586a84739aa69ab653fd`.
It contains `RuntimeProfileIncomplete` plus an `INCOMPLETE` marker and is
preserved outside the repository under
`/Users/shaanp/Documents/research-artifacts/astral-v41r7-oom-job-e52w6/`.

The microbatch correction halved the immediate failed allocation relative to
V41R6 but did not remove expert-weight materialization. V41R7 is consumed and
may not be retried. The selected next design candidate is a fresh V41R8 using
native MXFP4 frozen experts and attention-only LoRA. Because that changes the
adapter target geometry, it requires prospective preregistration, parameter and
forward-parity locks, memory gates, local implementation review, and separate
paid authorization.

No acquisition, retention, continual-learning, Astral-selection, tune,
assessment, or scientific claim follows. The ceiling is
`RemoteH100RuntimeProfileIncompleteV41R7`.
