# Evidence-conditioned multiscale plasticity v3 protocol

Date: 2026-08-28.

State slice: `astral-evidence-conditioned-multiscale-plasticity-v3`.

Status: `SyntheticFactorialValidated / ModelBearingExecutionNotAuthorized`.

Claim ceiling: `LocalDevelopmentExactSyntheticLiteratureInformedControllerOnly`.

## Rationale

The supplied literature does not validate the proposed combination. It
provides separable mechanisms that can be made testable:

| Literature constraint | Frozen synthetic mechanism |
|---|---|
| Complementary Learning Systems: fast episodic storage and slower semantic consolidation | `fast_slow` keeps a fast state and a slower state with a fixed consolidation rate. |
| EWC, GEM, and experience replay: protect prior tasks and revisit prior information | `ewc` adds an importance-weighted retention penalty; `replay` replays a bounded exact buffer. The learner exposes exact interference, so GEM-like protection remains a measurable future variant rather than an unimplemented claim. |
| Loss of plasticity: continual updates can reduce future learnability | `plasticity_guard` tracks a bounded plasticity state that decays under updates and recovers under protected admission. The floor is a hard guard, not a claim about biological plasticity. |
| Cyclical learning rates and oscillatory selection/consolidation ideas | `single_frequency` and `dual_frequency` alter bounded update gain. The phase is a scheduling input; it does not receive extra update compute. |
| Bayesian surprise and epistemic uncertainty | Each shard has mechanically generated novelty, uncertainty, expected utility, risk, and surprise fields. `oracle`, `noisy`, `shuffled`, and `absent` taxonomy inputs test whether admission depends on useful information rather than a privileged ontology. |
| Two-time-scale stochastic approximation | Fast and slow learning rates are fixed before execution. Bounded stochastic scheduling is seeded and has a fixed amplitude bound. |

The protocol therefore tests evidence-conditioned multi-timescale plasticity,
not “neuroscience of AI.” Ontological categories are not supplied as ground
truth. The literature is rationale for controls, not evidence for the new
controller. Primary references are [Complementary Learning Systems](https://web.stanford.edu/~jlmcc/papers/McCMcNaughtonOReilly95.pdf),
[EWC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5380101/),
[Experience Replay](https://arxiv.org/abs/1811.11682),
[GEM](https://arxiv.org/abs/1706.08840),
[Loss of Plasticity](https://www.nature.com/articles/s41586-024-07711-7),
[Cyclical Learning Rates](https://arxiv.org/abs/1506.01186), and
[Bayesian Surprise](https://pmc.ncbi.nlm.nih.gov/articles/PMC2860069/).

## Exact learner

The learner is a six-dimensional parameter vector initialized at zero. Each
shard carries a mechanically generated target vector. The base task loss is

```text
L(theta, shard) = 0.5 * ||theta - target(shard)||^2
```

Each accepted micro-update has a closed-form target-tracking effect. The
policy-specific state includes fast and slow parameters, replay contents,
importance weights, and a bounded plasticity variable. Interference is the
exact increase in protected-task loss. Assessment improvement is the
assessment baseline loss minus final loss after the fixed update budget.

No learned controller, optimizer search, model forward pass, model weights,
corpus, provider, or cryptographic backend is used.

## Frozen factorial

The factorial is:

- memory/update policy: `single`, `fast_slow`, `replay`, `ewc`,
  `plasticity_guard`, `integrated`;
- schedule: `fixed`, `single_frequency`, `dual_frequency`,
  `bounded_stochastic_dual`;
- admission controller: `fixed_admission`, `evidence_conditioned`;
- taxonomy: `oracle`, `noisy`, `shuffled`, `absent`;
- three preregistered replicate seeds crossed with three preregistered shard
  order seeds.

This yields `6 x 4 x 2 x 4 = 192` cells, 9 replicates per cell, and 1,728
replicates. Each replicate uses 24 fit shards, 12 tune shards, and 12
assessment shards, with two micro-updates per fit shard: 48 update attempts in
every arm. Gradient and shadow compute are equalized; verification cost is
reported as separate overhead.

## Primary endpoint and hard guards

The one primary endpoint is
`heldout_adaptation_improvement_after_fixed_update_budget`.

Hard guards are fixed before execution:

- forgetting value at or below `0.22`;
- calibration Brier score at or below `0.12`;
- final plasticity at or above `0.25`;
- maximum shard-order range at or below `0.20`;
- exact rollback fidelity within `1e-12`;
- equal update, gradient, and shadow compute across arms;
- verification cost at or below `72` units.

All fit/tune predictions are sealed in a digest-bound prediction lock before
assessment loss is evaluated. The serialized result, cell summaries, split
digests, prediction lock, and independent validator are separate custody
surfaces.

## Decision rules

1. Compare admission controllers within the same memory, schedule, and
   taxonomy. A gating effect must survive the oracle, noisy, shuffled, and
   absent taxonomy panel to be treated as general controller evidence.
2. Compare single- and dual-frequency schedules at equal update and shadow
   compute. A positive wave result that depends on extra work is invalid.
3. Treat bounded stochastic scheduling as a candidate only if its gain is
   stable across preregistered seeds and shard orders and does not pay for the
   gain through guard or verification-cost failures.
4. Compare memory mechanisms separately against `single`; do not claim that
   `integrated` works merely because several mechanisms were enabled together.
5. If a mechanism does not survive this synthetic screen, do not carry it into
   a model-bearing run. If one does survive, it remains a hypothesis requiring
   a separately authorized cached-model experiment.

## Authorization boundary

This protocol does not authorize model or corpus acquisition, training, base
weight updates, adapter updates, Astral assessment effects, accepted Evidence
Ledger mutation, V48 artifact reuse, V48 reopening, Stage 0C or Stage 1
promotion, production traffic, or introspection/self-modeling claims. Real
ZK/PQC backends are a later independent slice. Each backend must prove one
concrete statement and report its overhead; a fixture receipt or boolean flag
cannot stand in for cryptographic evidence.
