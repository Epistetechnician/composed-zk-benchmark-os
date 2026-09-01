# Plasticity Guard Replication V1 Execution Authorization

State slice: `continual-learning-plasticity-guard-replication-v1`.

## Authorization

On 2026-08-28, the user authorized a new separately scoped replication with a
fresh disjoint cohort, new seeds and shard orders, an untouched-base/no-update
arm, fixed cadence, the predeclared `plasticity_guard`, identical compute,
and reversible adapters. The user required absolute held-out improvement
against the untouched base as the primary endpoint, guarded-versus-fixed as a
secondary endpoint, and closure of the mechanism if the replication fails.

This record opens only the named state slice. It does not reopen Phase 831,
change its result, or authorize Astral execution.

## Allowed execution

- offline use of the already-cached Gemma3 1B PT BF16 MLX checkpoint;
- the fixed NEWSROOM source, copied and digest-bound in a new external root;
- the next 12 eligible records after the prior 12-record cohort;
- seeds `1747` and `1749` and orders `interleave` and `outer_in`;
- `no_update`, `fixed_cadence`, and `plasticity_guard` arms;
- equal-budget LoRA candidate adapters with active-pointer rollback;
- prediction locking before assessment;
- PrimaryED publication, DAed mirror, and independent aggregate-only
  validation;
- documentation and hermetic tests for this state slice.

The `plasticity_guard` thresholds are inherited exactly from Phase 831:
current-window NLL gain at least `0.001` and protected-window degradation at
most `0.010`. No threshold, seed, order, split, or endpoint may be tuned after
observing replication data.

The frozen prior result is bound by both canonical body digests and raw file
SHA-256 values recorded in the protocol. A mismatch stops execution.

## Prohibited execution

This authorization does not allow model or corpus downloads, network access
during model execution, base-weight updates, adapter merging, model shopping,
waves, stochastic scheduling, provider/H100 execution, V48 or prior Astral
artifact reuse, accepted Evidence Ledger mutation, Astral causal-target
execution, introspection or self-modeling claims, benchmark evidence, ZK/PQC
evidence, or production traffic.

Any qualification, custody, prediction-lock, hard-guard, mirror, or validator
failure closes this execution without adaptive retry. Astral remains
`not_run`; any later integration requires a separate authorization and is
limited to causal-effect prediction, calibration, or instrumental correction.

Every mutation in this authorization record touches state slice
`continual-learning-plasticity-guard-replication-v1`.
