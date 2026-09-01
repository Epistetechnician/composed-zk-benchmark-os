# Plasticity Recovery V2 Protocol

State slice: `continual-learning-plasticity-recovery-v2`.

## Rationale

The read-only V1 diagnosis found that ordinary replay lowered mean forgetting
but allowed early protected shards to age out of the bounded buffer. Selective
reinitialization alone did not improve aggregate forgetting. V2 therefore
tests one new mechanism only: `protected_replay`, which reserves the first
four accepted fit shards in an immutable protected replay memory and uses the
second fixed gradient slot for deterministic replay from that memory.

V1 remains frozen as `NoCandidate`. V1 artifacts are not scientific inputs to
V2. The V1 source transition kernel is reused only as implementation
infrastructure; V2 uses a new state namespace, fresh generated panel values,
fresh data seeds, and fresh fit-order seeds.

## Fixed factorial

The panel contains 16 fit, 8 tune, and 8 assessment shards per data seed.
Data seeds are `20261001`, `20261002`, `20261003`, and `20261004`; fit-order
seeds are `9111`, `9112`, and `9113`. The six arms are:

1. `no_update`: complete the shadow budget and retain the untouched base;
2. `fixed_adapter`: commit every ordinary adapter update;
3. `replay`: use the existing bounded four-shard replay buffer;
4. `selective_reinit`: use the unchanged low-utility mature-unit reset;
5. `replay_selective_reinit`: combine the two unchanged V1 controls;
6. `protected_replay`: reserve the first four accepted fit shards and replay
   one protected shard in the second gradient slot.

Every arm uses 16 fit updates, two gradient slots per update, 32 gradient
evaluations, 32 shadow evaluations, and the same learning rates as V1. The
base vector is unchanged. Adapter state is reversible and no adapter is
merged.

## Endpoint and guards

The primary endpoint is held-out assessment improvement over the untouched
base after the fixed update budget. The protected-replay arm is a candidate
only if its mean improvement is at least `0.01`, its deterministic
10,000-resample bootstrap lower bound is nonnegative, at least 9 of 12 paired
cases are positive, and every hard guard passes. The fixed guards are
forgetting at most `0.20` per case, calibration Brier score at most `0.25`,
zero rollback error, unchanged base, equal compute, and order range at most
`0.20`. Prediction locking occurs before assessment effects. No threshold,
seed, order, split, or endpoint is tuned after effects.

The prior arms are controls. A control result cannot promote the new
mechanism. If `protected_replay` fails, V2 is `NoCandidate` and no
model-bearing continuation is opened.

## Boundaries

This protocol authorizes only the local exact-synthetic run and its external
aggregate artifact. It does not authorize model or corpus downloads, model
execution, GiveMeANode, Astral integration, ZK/PQC proof generation, base
updates, adapter merges, or production traffic. Any later cached-model run
requires a separate authorization after this gate succeeds and remains
limited to reversible adapters. Astral remains limited to causal-effect
prediction, calibration, or instrumental correction; no introspection claim is
permitted.

Claim ceiling: `LocalDevelopmentPlasticityRecoveryV2SyntheticOnly`.

Every mutation in this protocol touches state slice
`continual-learning-plasticity-recovery-v2`.
