# Stage 0 Exploratory Actor-Capacity Qualification V3

## Boundary

State slice: `astral-stage0-exploratory-actor-capacity-qualification-v3`.

Status before execution: `PreregisteredExploratoryLocalStudy`.
Evidence ceiling: `LocalExploratoryActorCapacityDiagnostic`.

V3 addresses the V2 training-capability failure. It is development-only. It
does not score attribution methods, run interventions, issue a Stage 0
scientific verdict, replicate V1, or authorize observer work.

Only train families `0..159` and development families `160..191` may be
materialized. Families `192..319` remain excluded. The unopened V2 families
`320..383` remain sealed and retired to V2. Families `384..447` are reserved
for a possible separately preregistered confirmation and must not be
materialized by V3.

## Frozen Capacity Panel

All configurations use vocabulary 32, sequence length 12, four attention
heads, post-norm residual blocks, GELU, no dropout, a CLS classifier, AdamW
with learning rate `0.003` and weight decay `0.01`, batch size `128`, gradient
clipping at `1.0`, and deterministic execution.

| ID | Blocks | Width | Head width | Feed-forward width |
|---|---:|---:|---:|---:|
| `a-width32-block1` | 1 | 32 | 8 | 64 |
| `b-width64-block1` | 1 | 64 | 16 | 128 |
| `c-width64-block2` | 2 | 64 | 16 | 128 |

Training lasts exactly 2,000 updates. Development cross-entropy is measured
every 25 updates. The selected checkpoint has the lowest finite development
loss; exact ties select the earliest update. Each reproduction is eligible only
when selected-checkpoint train and development accuracy are each at least
`0.95`.

Architecture-selection seeds are exactly `67, 71, 73`. Each configuration and
seed is trained twice. A configuration is selection-eligible only if every
reproduction is eligible and each same-seed pair has identical selected step,
checkpoint digest, and trajectory digest. Select the eligible configuration
with the smallest exact trainable parameter count, then lexicographically by
ID. If none qualifies, stop as `CapacityPanelFailed`; do not add seeds,
updates, or configurations.

## Independent Actor Qualification

The selected configuration is locked before qualification. Qualification seeds
are exactly `79, 83, 89`, each trained twice. The first failed eligibility or
reproducibility pair stops qualification after its durable record is written.
No later seed may rescue the procedure.

All three passing yields `ActorQualifiedForFuturePreregistration`. This means
only that the selected local configuration reproducibly met the frozen
train/development floor on the named seed panels. It is not out-of-sample
generalization evidence.

Seed `131` is reserved for bounded implementation tests and cannot enter
selection or qualification. Seeds `109, 113, 127` are reserved for a possible
future scientific protocol and must not be trained in V3.

## Artifact and Stop Rules

The runner writes only to a caller-selected, repository-external, empty,
non-symlink output directory. It persists the protocol and environment record,
every reproduction before evaluating its gate, the complete selection matrix,
a selection lock only on success, qualification records through the first
failure, and a qualification lock only when all qualification seeds pass.

Nonfinite loss or parameters, a data-boundary breach, an unplanned retry,
digest mismatch, malformed artifacts, or provenance failure makes the run
`Invalid`. Tests must spy on family requests and prove that every requested
family is below `192`. V3 artifacts must contain no score, intervention,
bootstrap, tracer, or scientific-verdict fields.

## Claim Ceiling

V3 may report exact configuration, seed, accuracy, reproducibility, and gate
results. It cannot establish attribution superiority, causal fidelity,
independent replication, mechanistic understanding, introspection,
self-modeling, correction, safety, accepted evidence, or benchmark evidence.

Any scientific continuation requires a new protocol, independent pre-run
review, fresh actor seeds, a frozen measurement object and method census, and a
new untouched holdout. The safest reserved family block is `384..447`.

## Qualification Record — 2026-07-26

Execution classification: `ActorQualifiedForFuturePreregistration`.

Every architecture-selection reproduction was eligible and reproducible:

| Configuration | Parameters | Seeds | Train / development accuracy | Selected update |
|---|---:|---|---|---:|
| `a-width32-block1` | `9,890` | `67, 71, 73` | `1.0 / 1.0` for every reproduction | `2000` |
| `b-width64-block1` | `36,162` | `67, 71, 73` | `1.0 / 1.0` for every reproduction | `2000` |
| `c-width64-block2` | `69,378` | `67, 71, 73` | `1.0 / 1.0` for every reproduction | `2000` |

The frozen smallest-model rule selected `a-width32-block1`. It then passed
qualification seeds `79, 83, 89` twice each. Every selected checkpoint had
train and development accuracy `1.0`, selected update `2000`, and identical
same-seed checkpoint and trajectory digests.

| Seed | Checkpoint SHA-256 | Trajectory SHA-256 |
|---:|---|---|
| `79` | `5db6938751b93417d22aba7a82f0c6bef23ce9cdad879217285c23637dcf889f` | `436e413d59be82173eb638db64d9706125ba8b2cf5d2fce229980ca62300db9d` |
| `83` | `5e91c1df41964bb87ae0ed7e870a7d48a1fd5abc6142be01f78c3c98ffaa7fa1` | `a9056dceceefaaf1f9d3f01dcc7548feaf664a3bb2054c12398f396b3869c9d9` |
| `89` | `dfa04484bfdd1f31cc72f7ddb1c739b7671157ecfd01ea62e3ad9fe5b6180c72` | `1cee69e62b0d1ec1bb1a823bb7e832f8a6eceb07d71632acb3f69cc8050fae8b` |

The 17-file external artifact bundle had canonical manifest SHA-256
`da2bb8a2e294a303132f0c9a47e6bdb2f045377b116f06aedcf0ead7ad7e9cf0`
and passed the V3 semantic validator before deletion.

The bounded conclusion is that the original width-32 actor can meet the frozen
development qualification when trained for 2,000 updates under this procedure.
V3 does not determine whether 2,000 updates are minimal, generalize beyond the
reused development families, or validate any attribution method. Families
`192+`, including sealed V2 families `320..383` and reserved future families
`384..447`, were not materialized.
