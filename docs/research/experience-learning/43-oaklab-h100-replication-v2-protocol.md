# Oak Lab H100 replication V2 protocol

State slice: `oaklab-experience-learning-h100-replication-v2`.

Disposition: protocol/compiler only. No learner, model, data, provider, H100,
energy, or assessment execution is authorized until an independent review
accepts the exact frozen packet.

## Scientific object

V2 tests a lagged cross-fitted selective-credit policy against fixed batch-one
SGD on identical ordered experience streams. The policy may use only the
previous completed block's prediction residual, uncertainty summary, and
resource counters to choose the next block's update mask. Current-block
outcomes are unavailable at decision time. The complete policy trajectory is
the treatment; individual update decisions are not treated as independent
treatments.

The primary estimand is the paired post-washout block regret difference,

`ATE = E[ R(policy) - R(SGD_b1) ]`,

where each episode is assigned once to a fixed arm before execution, both arms
consume the same ordered stream bytes, the first block is a fixed washout, and
the remaining horizon is 32 blocks of 128 items. Carryover is controlled by
resetting learner state at episode boundaries and by reporting the first,
middle, and final post-washout block separately. No outcome-adaptive arm
switching, replay, reshuffling, or hidden accumulation is allowed.

The policy controller is fixed before tuning: it computes a lagged utility
estimate from the previous block, applies a declared uncertainty threshold,
and either updates the affected parameters or emits a no-update decision. The
threshold, controller state, and all transitions are encoded in the compiled
artifact; they cannot be tuned after assessment begins.

## Streams and design

The real campaign requires two independently custodied stream families: fresh
NoisyMNIST with distractors and a fresh event-camera or sensor stream. Each
family has disjoint fit, tune, and assessment cohorts. Synthetic qualification
must first cover predictable signal plus noise, delayed reward, feature
relevance drift, and event sparsity.

Treatment assignment is SHA-256-counter PRNG block randomization at the episode
level with propensity `1/2`, using a fresh seed roster fixed in the packet.
Fit selects no scientific claim. Tune locks the controller configuration and
prediction before assessment. Assessment uses fresh seeds and no further
selection.

## Gates and resource accounting

The primary quality endpoint is mean post-washout regret difference. The
adaptation endpoint is shift-segment lag. A candidate must improve both versus
fixed SGD batch one with Holm-adjusted paired tests, 0.80 planned power, and a
predeclared minimum effect. It must be non-inferior on active operations,
parameter updates, storage bytes, wall-clock latency, and measured joules per
learned event. Energy is accepted only from a privileged raw trace bound to
the exact workload manifest; operation counts are retained separately.

Every result root is closed-world: the manifest enumerates every allowed file,
rejects symlinks and unlisted paths, and binds provider allocation, start/stop,
cost, raw trace, integration, and validator receipts. Any missing, extra,
non-finite, or digest-mismatched artifact is a terminal failure.

## Execution order

1. Freeze this source, compiled artifact, compiler, validator, tests, and the
   current `AGENTS.md` digest.
2. Obtain independent packet-bound `ACCEPT`.
3. Implement and qualify the learner on synthetic streams only.
4. Obtain an independent tune lock.
5. Obtain separate real-execution authorization, fresh custody manifests, a
   GiveMeANode allocation, and a positive hard USD ceiling.
6. Run one bounded H100 job after no-spend preflight.
7. Independently validate the raw trace, joule receipt, result root, and
   statistical gate.

Any rejection or failed gate closes V2 as `no_candidate` without retuning.
V6, Phase 836, the plasticity guard, and Astral remain isolated historical
lanes.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v2`.
