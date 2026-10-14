# V41R19 Persistent-Node Gradient Profile Execution Record

State slice: `V41R19PersistentNodeRuntimeAndGradientProfile`.

Status: `Complete / IndependentlyValidated / DiagnosticOnly`.

Command `cmd-safk5` ran the frozen V41R16 no-update profiler on restored node
`astral-v41r3-profile-node-r1` with exact Python 3.12.3, PyTorch 2.10.0+cu128,
CUDA 12.8, transformers 4.57.6, PEFT 0.18.1, and a clock-locked H100 80GB.
The setup passed all 35 frozen tests before model access.

The raw artifact contains 192 float32 tensors for each of three panels and an
exactly unchanged initialized-adapter state. No optimizer was constructed and
optimizer steps were zero. Independent validation recomputed every raw-tensor
summary and passed with zero errors.

Global cosines were 0.778633 bridge–terminal, 0.652160 bridge–protected,
0.817561 terminal–protected, and 0.804440 acquisition–protected. Every pair had
zero negative-cosine layers across all 24 layers. Protected norm was 2.47x the
combined acquisition norm, 3.68x bridge, and 1.73x terminal.

This rejects destructive global or localized gradient-direction conflict at
the initialized adapter. It supports magnitude/optimization imbalance as the
next bounded mechanism hypothesis. The result does not select a layer or prove
that normalization will improve acquisition.

Artifact `art-935kf` has SHA-256
`69809a7f02f8d063329901dcea55822820550020d9e5eed398323c5c2d495daf`;
result SHA-256 is
`sha256:4b79ea5e71e5307fe10ab1848feca36718a63510b0a9135ad417d8f1c9fc5e77`.
Mission cost was USD 1.915 and is closed. The node is stopped with disk intact.
The claim ceiling is `RemoteH100GradientInterferenceDiagnosticV41R16`.

The validator accepts both `2.10.0` PyPI distribution metadata and
`2.10.0+cu128` module metadata only when the independent CUDA field is exactly
`12.8`. This resolves representation variance without modifying the immutable
artifact or relaxing version/CUDA identity.
