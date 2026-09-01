# Recursive update-policy V2 protocol

Date: 2026-08-29.

State slice: `continual-learning-recursive-update-policy-v2`.

Protocol status: `PROTOCOL_DRAFT_PENDING_INDEPENDENT_REVIEW`.

Claim ceiling: `LocalDevelopmentRecursiveUpdatePolicySyntheticProtocolV2`.

## Theory and estimands

The V1 review rejected the package before execution because rollback, custody,
receipt enforcement, reserve semantics, order stability, and result freezing
were incomplete. V2 is a new sealed identity. It preserves the theory that a
bounded controller may improve its future update policy from fresh-task
feedback, but makes the adaptation-forgetting tradeoff causal in the learner:
the plasticity reserve scales later update and probe capacity.

For case `c`, arm `a`, and generation `g`:

```text
A(c,a,g) = assessment loss before fit updates
           - assessment loss after fit updates
R(c,a,g) = protected loss after fit updates
           - protected loss before fit updates
P(c,a,g) = probe loss before a fixed probe update
           - probe loss after the fixed probe update
```

The primary case contrast is the difference in ordinary least-squares
adaptation slopes over generations `0..3`:

```text
S(c,a) = slope_g A(c,a,g)
D_GR(c) = S(c,recursive_policy) - S(c,random_policy)
G = mean_c D_GR(c)
```

The selection contrast is:

```text
U = mean_c [mean_g A(c,recursive_policy,g)
            - mean_g A(c,random_policy,g)]
```

The fixed-policy contrast is descriptive and is required to be non-negative:

```text
F = mean_c [mean_g A(c,recursive_policy,g)
            - mean_g A(c,fixed_policy,g)]
```

The primary synthetic candidate rule requires `G >= 0.005`, a deterministic
bootstrap lower bound for `G >= 0`, `U >= 0.005`, `F >= 0`, every recursive case
slope `>= 0.002`, and every hard guard. A positive result is a synthetic
candidate only; it is not evidence of RSI, AGI, autonomy, introspection, or
causal self-modeling.

## Exact learner

The learner is a six-dimensional quadratic system. The immutable base state is
`theta=(0,0,0,0,0,0)` with base-state digest
`sha256(canonical_json({"state_slice": STATE_SLICE, "theta": [0,0,0,0,0,0]}))`.
Each state also contains a finite `plasticity_reserve` in `[0,1]`, policy name,
policy version, and a checkpoint digest.

For policy `p`, target `y`, protected mean `q`, memory bias `m`, and reserve
`r`, the exact update is:

```text
effective_step = p.step_size * (0.50 + 0.50*r)
task_gradient = (y + 0.20*m) - theta
protected_gradient = q - theta
delta = effective_step * (task_gradient - p.retention_price*protected_gradient)
theta' = theta + delta
r' = clamp(r - 0.08*||delta|| + 0.015*[p.memory_mode == procedural], 0, 1)
```

The reserve therefore affects both adaptation and the fixed post-adaptation
probe, rather than being a disconnected bookkeeping field. The policy table is
fixed:

| policy | step size | retention price | memory mode |
| --- | ---: | ---: | --- |
| `conservative` | `0.18` | `0.80` | `episodic` |
| `balanced` | `0.30` | `0.45` | `episodic` |
| `plastic` | `0.38` | `0.20` | `procedural` |

Targets are SHA-256-derived, deterministic, and disjoint by split and
generation. Fit, tune, assessment, protected, and probe counts are `5`, `3`,
`4`, `3`, and `2`. The memory prototype is not an assessment split: it is a
stable synthetic target derived from the seed and concept index and is used only
to test repeated memory support.

## Factorial and compute

The fixed factorial is four replicate seeds (`74101..74104`), two order seeds
(`8311, 8312`), two fit directions (`forward, reverse`), four arms
(`untouched_base`, `fixed_policy`, `recursive_policy`, `random_policy`), and
four generations. There are `64` cases and `256` generation rows.

At every generation all three policy candidates are simulated from the same
checkpoint and evaluated on the same fit/tune/protected/probe data. The selected
candidate is then run as the actual update for updating arms; the untouched arm
performs the same shadow work and commits nothing. Each generation reports
exactly `24` candidate-evaluation units and `5` update-attempt units, for `29`
units per generation and `116` units per case. Candidate selection cannot change
the budget.

## Recursion, memory, and sandbox

The recursive controller chooses the highest tune score:

```text
tune gain - retention_price*max(protected delta, 0) + 0.50*probe gain
```

Exact ties use policy-library order. The random arm uses one deterministic
`Random(seed + order_seed + 900000)` stream and one draw per generation. Only
`policy_name` and `policy_version` may change in the controller state. The
evaluator, splits, task generator, protected suite, compute budget, validator,
state slice, and claim ceiling are immutable.

Memory is case-local and external to learner state. Records contain a stable
concept key, generation, target digest, provenance, and status. Fresh active
records are admitted; records older than one generation are stale; poisoned or
deleted records are quarantined with zero effect; contradictory target digests
are rejected; repeated consistent support promotes the concept to procedural at
support two. Stable prototypes make promotion part of the actual case stream,
while the six-condition memory probe remains a safety contract, not effect
evidence.

## Checkpoint, rollback, and custody

Before every actual fit sequence, the complete learner state is copied as an
immutable checkpoint. After the sequence, a separate restore operation rebuilds
the prior state from that checkpoint and computes the maximum absolute theta,
reserve, policy, and version discrepancy. The hard tolerance is `1e-12`; no
self-comparison or hard-coded zero is valid. The post-update state is retained
only after restoration has been verified.

The exact external root is:

```text
/Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v2-20260829/
```

The root must not exist at run start, must be a new regular directory, and must
not be a symlink. The only result path is `<root>/result.json`. Every artifact
writer requires the accepted independent-review receipt, validates its exact
canonical encoding and protocol digest, and rejects all other roots or outputs.
The repository receives no raw targets, memory payloads, model outputs, or
training artifacts.

## Lock, validation, and closure

Each generation follows exactly:

```text
synthetic_initialized
fit_tune_completed
prediction_lock_sealed
assessment_completed
rollback_verified
```

The lock is sealed before assessment metrics exist. The result includes an
explicit mechanically recomputed classification, base-state digest, campaign
summary, case digests, event log, and result digest. The independent validator
does not import the runner and recomputes the learner, case coverage, metrics,
locks, rollback, memory, order guard, compute, classification, and digests.

Hard guards are maximum positive forgetting `0.08`, minimum plasticity gain
`-0.02`, rollback error `1e-12`, exact compute `116` per case, exact order delta
`max(|ΔA|, |ΔR|, |ΔP|) <= 0.08`, base digest invariance, complete memory probe,
contiguous event chain, and independent validation. If recursive selection
improves random selection but does not compound, classify as
`NonCompoundingContinualLearning` and retain only infrastructure value. If it
fails random selection or any hard guard, classify as `NoCandidate` and close
this protocol identity. If all candidate conditions pass, classify as
`LocalSyntheticRecursiveUpdatePolicyCandidate`.

No cached model, reversible adapter, GiveMeANode/provider, Astral, ZK, or PQC
execution is authorized by this protocol. A model-bearing experiment would be a
new separately authorized slice. Astral remains limited to causal-effect
prediction, calibration, or instrumental correction.

Every mutation governed by this protocol names state slice
`continual-learning-recursive-update-policy-v2`.
