# V25 corrected shared-adapter reference-initialization preflight record

State slice: `continual-learning-protocol-v25-shared-adapter-reference-initialization-preflight`.

Classification: `CorrectedLocalSharedAdapterReferenceInitializationPreflightNoBreakthroughClaim`.

## Frozen execution identity

One corrected local cell ran with data seed `20260812` and task order
`0,1,2,3`. The V25 change was the fixed shared-adapter initialization seed
`20260811`, applied at the declared initialization boundary. The shared
eight-layer adapter, task-keyed persistent optimizer state, replay policy,
optimizer, learning rate, batch size, sequence length, examples, update
budgets, and total steps remained fixed.

The replay and no-replay arms each consumed `128` examples in `640` optimizer
iterations, with `32` rows and `160` iterations per update. The adapter
parameter budget was `5,877,295` bytes in both arms. Replay exposure and
optimizer-state persistence were independently verified.

## Result

| arm | acquisition | retention after interference | replay exposure | peak memory |
| --- | ---: | ---: | --- | ---: |
| `shared_replay` | `2/8 = 0.25` | `2/8 = 0.25` | verified | `0.82371223 GB` |
| `shared_no_replay` | `2/8 = 0.25` | `2/8 = 0.25` | verified | `0.80237723 GB` |

Retention effect (`shared_replay - shared_no_replay`): `0.0`.

Replay fact IDs were present in the training datasets at every replay update;
the replay counts were `step 0: {}`, `step 1: {T0: 8}`, `step 2: {T0: 8,
T1: 8}`, and `step 3: {T0: 8, T1: 8, T2: 8}`. The no-replay arm had no replay
rows by construction.

## Decision

V25 fails the acquisition floor and produces no replay-retention advantage.
It is rejected as a solvability candidate. No replication budget is spent, no
H100 is authorized, and the next research object must change the task/update
protocol rather than increase compute. The claim ceiling remains
`LocalDevelopmentSharedAdapterReferenceInitializationPreflight`.

External result artifact:

`/tmp/continual-learning-model-v25-shared-adapter-reference-initialization-preflight-20260812-order0123-r3/result.json`

Result SHA-256:

`4d50e866cef1d6e7ac52559828f831104992e317f1a182759195a45d967dafab`.
