# Plasticity Recovery Mechanism Family Terminal Closure

State slices: `continual-learning-plasticity-recovery-v1` and
`continual-learning-plasticity-recovery-v2`.

## Decision

The plasticity-recovery mechanism family is closed as `NoCandidate`.

V1 tested bounded replay and selective low-utility reinitialization. V2 tested
one materially different protected-replay mechanism using fresh data and order
seeds. V2 produced the strongest held-out adaptation result, but it still
failed the unchanged per-case forgetting guard. The result did not justify a
cached-model run, GiveMeANode submission, Astral integration, or ZK/PQC proof
experiment.

The V1 and V2 result artifacts, prediction locks, custody manifests, and
independent validators remain immutable evidence for their bounded synthetic
claims only. The repository root gate remains non-green because the unrelated
`test_volume_path_rejects_non_volume_and_repository` test expects a `ValueError`
while `/Volumes/PrimaryED` is not mounted; the new focused tests and
`lint:fast` passed. This environmental failure does not alter either scientific
classification.

## Reopening rule

Any continuation requires a new named state slice and a materially new theory
and estimand that explicitly addresses the adaptation-forgetting tradeoff. It
must use a fresh protocol, fresh data and orders, prediction locking before
assessment, unchanged-base reversible adapters, preregistered thresholds and
hard guards, independent validation, and a written review before execution.
It must not silently tune the V1/V2 forgetting threshold or reuse their results
as assessment data.

Until that package exists and is separately authorized, no model-bearing run,
provider execution, Astral integration, or ZK/PQC custody-proof work may be
opened from this mechanism family.

Every mutation in this closure record touches the named plasticity-recovery
state slices above.
