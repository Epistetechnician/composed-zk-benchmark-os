# V41R21 Learnability-Decomposition Execution Record

State slice: `V41R21AcquisitionLearnabilityDecomposition`.

Status: `LearnabilityDecompositionComplete / UpdateSubstrateUnqualified / IndependentlyValidated / Consumed`.

The exact four-arm GPT-OSS-20B campaign completed on one clock-locked H100.
Every update arm executed 64 steps, 256 equal-weight examples, and exact
adapter reload.

| Arm | Overall | Composition | Bridge | Terminal | End-to-end | Protected |
|---|---:|---:|---:|---:|---:|---:|
| no update | 0.25000 | 0.25000 | 0.28125 | 0.25000 | 0.25000 | 1.0000 |
| direct oracle | 0.28125 | 0.28125 | 0.21875 | 0.28125 | 0.28125 | 0.3750 |
| two edge | 0.28125 | 0.25000 | 0.28125 | 0.28125 | 0.25000 | 0.4375 |
| two edge + protected | 0.26042 | 0.31250 | 0.25000 | 0.28125 | 0.31250 | 0.8125 |

The direct-oracle exact-prompt control missed its preregistered 0.90 floor by
0.61875. The campaign therefore stops at `UpdateSubstrateUnqualified`.
Primitive, compositional, and protected-replay differences remain descriptive
only because the update substrate failed its first positive-control gate.

This bounds the conclusion to the tested rank-8 all-attention LoRA, AdamW
`2e-4`, 64-step substrate. It does not show that the base model or every update
method cannot acquire the facts.

Result SHA-256 is
`sha256:09fdf9f6f830d44f1a0113977d435203ccc87133800d83991c579373151a3f19`.
Artifact `art-zmey7` has SHA-256
`bd0b7de12d5235d2c47525465fc3c852136c2c62e4a688358f26b845283a9d56`.
Independent validation returned zero errors; report SHA-256 is
`57809d7a3a5e9fc632ae0c7b56944c85eebe92ff2c6bf65bc1f6989a2d7ed069`.
Mission cost was USD 0.546, the node is stopped, and the identity is consumed.
No continual-learning or self-improvement claim is promoted.
