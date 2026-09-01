# Plasticity Recovery V1 Forgetting Diagnosis

State slice: `continual-learning-plasticity-recovery-v1`.

## Scope

This is a read-only reconstruction of the frozen V1 exact-synthetic
transition kernel. It reads the sealed V1 result, verifies its result digest,
reconstructs each fixed case, and records protected-shard degradation,
unit-level positive loss contribution, replay-target accounting,
reinitialization events, and fit-order sensitivity. It does not change V1
thresholds, seeds, orders, splits, endpoints, or results.

Diagnosis artifact root:

`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-recovery-v1-forgetting-diagnosis-20260829`

Diagnosis SHA-256:

`6c9632ecb39680a2610b9d8aef9b6f0c2ba15de94d8751596eae67196ea0b738`

The independent diagnosis validator passed the artifact and source-result
custody checks.

## Findings

- `fixed_adapter`: maximum forgetting `0.42748450`, mean `0.27619477`, and
  order-dependent forgetting range `0.24431338`.
- `replay`: maximum forgetting `0.36374588`, mean `0.17096203`, with 180
  replay slots across the 12 cases. Replay reduced average forgetting but
  still left guard failures in individual cases.
- `selective_reinit`: maximum forgetting `0.40326561`, mean `0.28171442`,
  with 36 resets. Reinitialization alone did not reduce aggregate forgetting.
- `replay_selective_reinit`: maximum forgetting `0.34287617`, mean `0.17361644`,
  with 180 replay slots and 36 resets. The combination reduced the maximum
  relative to fixed adapter but remained above the per-case guard.
- The largest positive protected-loss contributions concentrate in units 2,
  4, and 5 depending on arm; combined reinitialization selected unit 5 in 23
  of 36 events. This is an attribution, not evidence that unit identity is a
  model-semantic feature.
- Held-out adaptation order ranges stayed small, but forgetting order ranges
  remained large. Therefore the failure is protected-memory instability, not
  merely an assessment-gain ordering artifact.

## Decision

V1 remains frozen as `NoCandidate`. The diagnosis supports one new
predeclared hypothesis: reserve a protected replay memory for the early
protected shards instead of allowing the bounded buffer to age them out.
That hypothesis must be tested in a new state slice with fresh seeds, fresh
splits, unchanged V1 thresholds, prediction locking, and the same hard guards.
This record does not authorize that run, model-bearing execution, GiveMeANode,
Astral integration, or ZK/PQC custody proof.

Every mutation in this diagnosis record touches state slice
`continual-learning-plasticity-recovery-v1`.
