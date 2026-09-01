# Recursive update-policy V1 protocol

State slice: `continual-learning-recursive-update-policy-v1`.

Protocol status: `PROTOCOL_DRAFT_PENDING_INDEPENDENT_REVIEW`.

Claim ceiling: `LocalDevelopmentRecursiveUpdatePolicySyntheticProtocol`.

## Purpose and theory

The prior plasticity-guard and plasticity-recovery mechanism families are
closed. This is a new, model-free protocol. It does not reopen those slices,
reuse their scientific artifacts, or authorize Astral, GiveMeANode, provider,
model-bearing, base-weight, or ZK/PQC execution.

The theory is **bounded recursive update-policy improvement**:

> A controller that evaluates a fixed set of update policies on fit/tune data,
> commits only a reversible policy-state change inside a sandbox, and receives
> fresh-task feedback can improve its future update policy. The improvement is
> meaningful only if it compounds across generations while retention and
> post-adaptation plasticity remain bounded.

This differs from a plasticity guard or protected-subspace projection. The
treatment is the recursive policy transition itself. Candidate evaluation,
memory integrity, checkpointing, and controller mutation are all explicit
parts of the causal system.

The protocol does not identify general recursive self-improvement. Its maximum
claim is a bounded synthetic demonstration of generational update-policy
selection under the stated learner and evaluator.

## Primary and secondary estimands

For case `c`, arm `a`, and generation `g`, the exact synthetic learner exposes
three separate outcomes:

```text
A(c,a,g) = assessment loss before fit updates
           - assessment loss after fit updates

R(c,a,g) = protected loss after fit updates
           - protected loss before fit updates

P(c,a,g) = probe loss before a fixed probe update
           - probe loss after the fixed probe update
```

Positive `A` is adaptation. Positive `R` is forgetting. Positive `P` is
post-adaptation plasticity.

The primary case-level compounding slope is the ordinary least-squares slope
of `A(c,a,g)` over generation indices `0, 1, 2, 3`:

```text
S(c,a) = slope_g A(c,a,g)
```

The primary campaign estimand is:

```text
G = mean_c [S(c,recursive_policy) - S(c,random_policy)]
```

The selection estimand is a secondary check:

```text
U = mean_c [mean_g A(c,recursive_policy,g)
            - mean_g A(c,random_policy,g)]
```

The fixed-policy contrast is descriptive and protective:

```text
F = mean_c [mean_g A(c,recursive_policy,g)
            - mean_g A(c,fixed_policy,g)]
```

The recursive arm is a candidate only if all of these predeclared conditions
hold:

```text
G >= 0.005
deterministic bootstrap lower bound for G >= 0.000
U >= 0.005
every recursive case has S(c,recursive_policy) >= 0.002
every arm/case passes retention, plasticity, rollback, memory, and compute guards
```

The untouched-base arm is an absolute reference. It performs the same shadow
candidate evaluations but commits no update. It is not replaced by a
fixed-policy comparison.

## Exact synthetic learner

The learner is a six-dimensional quadratic system. Its base state is the
all-zero vector and is immutable. A learner state contains exactly:

```text
theta: six finite floating-point values
plasticity_reserve: finite value in [0, 1]
policy_name: one of conservative, balanced, plastic
policy_version: nonnegative integer
checkpoint_sha256: digest of the preceding fields and state slice
```

The loss for state `theta` and target `y` is:

```text
loss(theta, y) = sum_i (theta_i - y_i)^2 / 6
```

Each target is generated mechanically from the SHA-256-derived unit function
in `recursive_update_policy_v1.py`. The anchor is:

```text
anchor_i(seed) = 0.12 * sin((i + 1) * 1.31 + seed * 0.0001)
```

Target scale is `0.18..0.21` for protected tasks, `0.62..0.70` for probe
tasks, and `0.55..0.77` for fit, tune, and assessment tasks. The signed
direction for coordinate `i` is derived from the state slice, seed,
generation, split, task index, coordinate, and the literal `direction`.
No external data are read.

The policy library is frozen:

| Policy | Step size | Retention price | Memory mode |
| --- | ---: | ---: | --- |
| `conservative` | `0.18` | `0.80` | episodic |
| `balanced` | `0.30` | `0.45` | episodic |
| `plastic` | `0.38` | `0.20` | procedural |

For a target `y`, protected mean `p`, and memory bias `m`, the update is:

```text
task_gradient      = (y + 0.20*m) - theta
protected_gradient = p - theta
delta              = step_size * (task_gradient
                                   - retention_price*protected_gradient)
theta'             = theta + delta
reserve'           = clamp(reserve - 0.08*||delta||
                            + 0.015*[memory_mode == procedural], 0, 1)
```

The fixed probe always uses the `balanced` policy, the first probe target, and
zero memory bias. Probe updates are shadow-only and do not mutate learner
state.

## Fixed factorial and fresh splits

There are four generations, four replicate seeds, two order seeds, two fit
order directions, and four arms:

```text
generations:       0, 1, 2, 3
replicate seeds:   73101, 73102, 73103, 73104
order seeds:       8211, 8212
directions:        forward, reverse
arms:              untouched_base, fixed_policy, recursive_policy, random_policy
```

Each generation has fresh deterministic task instances with exactly:

```text
fit:        5 tasks
tune:       3 tasks
assessment: 4 tasks
probe:      2 tasks
protected:  3 tasks
```

Fit, tune, assessment, probe, and protected targets are disjoint by split and
generation. Fit order is deterministic from the order seed and direction.
Assessment, probe, and protected targets use the fixed forward order so the
fit-order treatment is not reintroduced at assessment.

The unit of analysis is the case, not a task, token, coordinate, or generated
candidate. There are `4 * 2 * 2 * 4 = 64` cases. Every case has exactly four
generation records.

## Controller recursion and sandbox

At each generation, all three policies are simulated from the same checkpoint
against the fit sequence and evaluated on the tune sequence. The resulting
three finite tune scores are recorded. The score is:

```text
tune adaptation gain
- retention_price * positive protected forgetting
+ 0.50 * post-fit probe gain
```

The arm policy then chooses one policy:

- `untouched_base`: evaluates all candidates, selects `balanced` for the
  sealed record, and commits no fit update;
- `fixed_policy`: always selects `balanced`;
- `recursive_policy`: selects the highest tune score, with candidate-library
  order as the exact tie-break;
- `random_policy`: uses `random.Random(seed + order_seed + 900000)` and one
  `randrange(3)` call per generation.

The selected policy becomes the next policy-state value for the updating arms.
This is the only recursive self-change permitted. The controller may not alter
the evaluator, task generator, protected suite, compute budget, assessment
split, validator, state slice, or claim ceiling.

The exact proposal envelope is:

```json
{
  "state_slice": "continual-learning-recursive-update-policy-v1",
  "generation": 0,
  "prior_policy": "balanced",
  "proposed_policy": "plastic",
  "candidate_score_digest": "64 lowercase hex characters",
  "controller_mode": "recursive_policy"
}
```

Unknown keys, non-finite values, unknown policies, wrong state slice, or any
immutable-field mutation are terminal proposal failures.

## External memory contract

Memory is external to the learner state and is never merged into base weights.
Each record has a memory key, concept key, generation, target digest,
provenance, status, support count, and poisoning/deletion flags.

The admission rules are fixed:

1. A record older than one generation is stale and rejected.
2. A poisoned or deleted record is quarantined with zero effect.
3. A record whose concept key conflicts with an existing target digest is
   rejected as a contradiction.
4. A matching concept with repeated support is promoted to procedural status
   at support count two.
5. Only active records are eligible for episodic mode; only procedural records
   are eligible for procedural mode.
6. Memory access is case-local. Cross-case reads are forbidden.

The contract probe must pass all six booleans before a synthetic campaign is
eligible: fresh accepted, stale rejected, contradiction rejected, poison
rejected, deletion rejected, and procedural promotion.

The memory probe is a safety and contract test. Its booleans are not scientific
effect evidence.

## Checkpoints and rollback

Before every fit update sequence, the active checkpoint digest is recorded.
After the sequence, a new digest is recorded. The base state digest must remain
constant across every case and generation. Rollback copies the prior immutable
state and computes the maximum absolute coordinate error. The fixed tolerance
is `1e-12`; a nonzero error is terminal.

No base weight, model directory, adapter, or external checkpoint is written by
this synthetic slice. A later cached-model experiment would require a separate
authorization and use reversible adapters only.

## Compute contract

Every case and arm evaluates all three policies on all five fit and three tune
tasks, then performs five fit-update attempts. This is exactly:

```text
candidate evaluations: 3 * (5 + 3) = 24
update attempts:       5
total per generation:  29
total per case:        4 * 29 = 116
```

The untouched arm performs the candidate simulations and shadow updates but
does not commit them. The validator requires identical total compute across
all arms. The number of committed updates is reported separately and is not
used as a hidden advantage.

## Prediction lock and state machine

No assessment effect is read before the generation lock. Each generation uses
this exact logical order:

```text
synthetic_initialized
fit_tune_completed
prediction_lock_sealed
assessment_completed
rollback_verified
```

The lock contains exactly the state slice, generation, selected policy,
proposal digest, `assessment_started: false`, and assessment task count. Its
digest is recorded in the generation row before assessment metrics exist.

The top-level result is retained only with `execution_authorized: false` and
contains aggregate values, digests, and contract booleans. No raw target,
memory payload, adapter tensor, model output, or exception text is retained.

## Guards and closure rules

Hard guards are:

```text
max positive protected forgetting <= 0.08
minimum post-adaptation plasticity gain >= -0.02
rollback error <= 1e-12
total compute exactly 116 per case
forward/reverse adaptation summary delta <= 0.08
memory contract probe all true
event chain contiguous and ordered
independent validator pass
```

The campaign is a candidate only when the primary estimand and all guards
pass. If recursive selection beats fixed policy but not random, classify it as
`SelectionWithoutRandomAdvantage`. If it beats random but has no positive
compounding slope, classify it as `NonCompoundingContinualLearning`. If it
passes all gates, classify it as `LocalSyntheticRecursiveUpdatePolicyCandidate`.
Any other failure is `NoCandidate`.

A positive result would not establish AGI, autonomy, general recursive
self-improvement, introspection, causal self-modeling, truth of memory, or
production readiness. A failed result closes this protocol identity; no
adaptive threshold, seed, order, split, endpoint, or guard repair is allowed.

## Independent validation and execution boundary

The additive runner and independent validator are:

```text
experiments/continual_learning/recursive_update_policy_v1.py
experiments/continual_learning/validate_recursive_update_policy_v1.py
experiments/continual_learning/tests/test_recursive_update_policy_v1.py
```

The validator imports no runner code. It recomputes the synthetic learner,
case coverage, event chain, memory probe, generation metrics, campaign
estimands, and result digest from the aggregate result.

Before any synthetic artifact is written, an independent review receipt must
bind this protocol's exact SHA-256 digest, use an exact schema with no unknown
keys, report all ten checks as `PASS`, and carry disposition
`APPROVED_FOR_SYNTHETIC_RUN`. The runner's `--mode synthetic` requires that
receipt. The repository currently contains no such acceptance receipt.

Required pre-review command:

```text
python -B experiments/continual_learning/recursive_update_policy_v1.py --mode contract-check
python -B -m pytest -q experiments/continual_learning/tests/test_recursive_update_policy_v1.py
```

After review, the bounded synthetic command is:

```text
python -B experiments/continual_learning/recursive_update_policy_v1.py \
  --mode synthetic \
  --review-receipt <accepted-review-receipt.json> \
  --output /Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v1-20260829/result.json
python -B experiments/continual_learning/validate_recursive_update_policy_v1.py \
  /Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v1-20260829/result.json
```

This protocol does not authorize model-bearing execution, provider spend,
GiveMeANode, Astral integration, accepted Evidence Ledger mutation, or ZK/PQC
backend evidence. Those remain separate authorization boundaries.

Every mutation governed by this protocol touches state slice
`continual-learning-recursive-update-policy-v1`.
