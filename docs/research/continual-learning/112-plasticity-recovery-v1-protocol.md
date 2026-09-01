# Plasticity Recovery V1 Protocol

State slice: `continual-learning-plasticity-recovery-v1`.

## Purpose

This slice tests whether bounded replay and selective low-utility
reinitialization recover useful continual-learning behavior after the prior
plasticity-guard replication. It is a fresh exact synthetic learner, not a
transformer result. The synthetic state is an adapter analogue with known
targets, update effects, interference, and ground truth. The result cannot be
promoted to a model-bearing or Astral claim.

## Fixed design

The panel is generated independently for each of four seeds with 16 fit, 8
tune, and 8 assessment shards. The fit budget is 16 updates with two gradient
slots per update. The three fixed order seeds are `8111`, `8112`, and `8113`.
All arms use 32 gradient evaluations and 32 shadow evaluations per case.

The five arms are:

1. `no_update`: spend the complete shadow budget and evaluate the untouched
   base state;
2. `fixed_adapter`: commit every ordinary adapter update;
3. `replay`: commit ordinary updates plus one bounded replay target;
4. `selective_reinit`: periodically reset the lowest-utility mature unit;
5. `replay_selective_reinit`: combine bounded replay and selective reset.

Only reversible adapter state changes. The base vector is fixed at zero and
cannot be updated or merged. Replay capacity, reinitialization maturity and
period, learning rates, seeds, order seeds, split sizes, and thresholds are
defined in `experiments/continual_learning/plasticity_recovery_v1.py` before
assessment.

## Endpoint and guards

The primary endpoint is absolute held-out adaptation improvement over the
untouched base:

`untouched_base_assessment_loss - final_arm_assessment_loss`.

The fixed decision rule requires mean improvement at least `0.01`, a
nonnegative deterministic 10,000-resample bootstrap lower bound, at least 9 of
12 positive paired cases, and every hard guard. Forgetting, calibration,
rollback fidelity, base immutability, equal compute, and fit-order stability
are hard guards. The prediction lock is sealed from tune predictions before
assessment effects are computed. No threshold or arm is tuned after effects.

The result is a candidate only if the arm passes the primary endpoint and all
guards. A guard failure is a valid negative result and must remain visible in
the receipt. A positive improvement that fails a hard guard is not a candidate.

## Boundaries

The local synthetic run is the only execution opened by this protocol. A
future model-bearing run requires a new contract for model/runtime custody,
fresh data, reversible adapters, and independent validation. GiveMeANode may
run only the sealed package after an explicit hard USD spend ceiling is
recorded; no paid provider job is implied by this document. Astral integration
is deferred and, if separately authorized, is limited to causal-effect
prediction, calibration, or instrumental correction. ZK/PQC is deferred to a
separate custody-proof slice in which each backend proves one concrete
statement and reports overhead.

Prior Phase 831/832, Astral V48, and other scientific artifacts are not inputs
to this slice. The claim ceiling is
`LocalDevelopmentPlasticityRecoverySyntheticOnly`.

Every mutation in this protocol touches state slice
`continual-learning-plasticity-recovery-v1`.
