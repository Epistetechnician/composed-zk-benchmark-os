# Oak Lab selective-credit V3 protocol

State slice: `oaklab-experience-learning-selective-credit-v3`

Protocol status: frozen for independent pre-implementation review. No V3
learner implementation or scientific execution is authorized until that
review accepts the exact protocol bytes.

Machine-readable protocol:
`experiments/experience_learning/selective_credit_v3_protocol.json`.

## Scientific change

V1 reconstructed a one-step no-update prediction from the previous parameter
delta. V2 used sequential loss change. Both failed. V3 instead randomizes a
bounded update action and estimates its causal excursion effect over a fixed
future horizon:

`tau_H(c_t) = E[Y_t(0) - Y_t(1) | C_t=c_t, I_t=1]`

where `A_t=1` applies the fixed SGD update at an eligible anchor, `A_t=0`
skips it, and

`Y_t(a) = sum_(j=1)^H gamma^(j-1) loss_(t+j)(a)`.

A positive `tau_H` means that applying the anchor update lowers discounted
future loss under the fixed continuation policy. This is a conditional causal
excursion estimand for randomized eligible decisions. It is not a global
causal claim about parameters and is not an Astral estimand.

Micro-randomization and weighted centered regression are established methods,
not claimed inventions. The unvalidated research hypothesis is that applying
them to batch-one update selection can distinguish useful from harmful online
credit under a strict event and resource budget. Relevant anchors are the
[micro-randomized trial design](https://pmc.ncbi.nlm.nih.gov/articles/PMC4732571/),
[doubly robust contextual-bandit evaluation](https://arxiv.org/abs/1103.4601),
[expected eligibility traces](https://ojs.aaai.org/index.php/AAAI/article/view/17200),
and Oak Lab's distinction between learnable and unlearnable associations in
[experience streams](https://www.oaklab.ai/posts/learning-from-experience-instead-of-curated-datasets).

## Assignment, horizon, and carryover

- Horizon `H=8`, discount `gamma=0.9`, anchor stride `9`.
- Fit and tune anchors use fixed propensity `p=0.5` from a stateless SHA-256
  assignment over seed, stream, and anchor index.
- Proximal windows never overlap.
- Non-anchor items always receive the same fixed-rate SGD continuation update.
- The pre-action context contains only an intercept and clipped transformed
  current loss. Task identity, oracle features, and future outcomes are
  forbidden.
- The estimator updates only during the first third. It is frozen during tune.
- Tune is an eligibility check, not hyperparameter selection.
- Assessment restores a digest-bound tune snapshot and uses a deterministic
  frozen action rule. There is no assessment randomization or estimator update.

Sequential randomization identifies a history-conditional excursion effect;
it does not remove all long-horizon interference. Non-overlapping windows,
fixed continuation behavior, context restrictions, and assessment locking are
the declared carryover controls. Any interpretation beyond this estimand is
prohibited.

## Estimator and resource contract

The estimator is an online weighted-and-centered least-squares regression
implemented by fixed-step SGD. It contains four coefficients: two baseline
and two treatment-effect coefficients. The prediction is:

`alpha_0 + alpha_1*c + (A-p)*(beta_0 + beta_1*c)`.

The assessment anchor update is applied only when
`beta_0 + beta_1*c < 0`. No threshold grid is tuned.

The logical incremental state is exactly eight scalars: four estimator
coefficients and four pending-window values, or 64 bytes at float64 width.
The state noninferiority margin is therefore frozen at 64 bytes. Replay bytes
must remain zero. Every estimator multiply-add is included in active-operation
accounting. Candidate active operations must be at least 5% below fixed SGD in
each qualifying family, so the state allowance cannot hide compute expansion.

## Streams, fresh cohorts, and ablations

Synthetic streams:

- predictable/noise: `sparse_noisy`, `noisy_mnist_like`;
- delayed reward: `delayed_reward`;
- drift: `nonstationary`, `drifting`;
- event-driven: `event_camera_like`.

Each stream contains 768 ordered experiences. The 48 fresh paired seed offsets
are `100..147`. The only active reference is fixed `sgd_b1` at learning rate
`0.03`. Noise-floor and oracle-feature controls must execute.

Three fixed ablations are mandatory:

- horizon one;
- no context moderation;
- random assessment policy.

The closed plasticity guard is not an active arm and cannot be rerun.

## Multiplicity, power, and gate

The four primary family loss comparisons use Holm-Bonferroni at family alpha
`0.05`. The worst first-step alpha is `0.0125`. With 48 paired assessment
seeds, the frozen normal-approximation power is `0.833077` for standardized
effect `0.5`, above the `0.80` target.

Synthetic status is `candidate` only if at least two families pass all of the
following, including at least one delayed-reward or drift family:

- strictly lower family mean loss with Holm-adjusted `p <= 0.05`;
- non-inferior adaptation lag, with a strict adaptation improvement in at
  least one qualifying delayed-reward or drift family;
- updates no greater than fixed SGD;
- active operations at most 95% of fixed SGD;
- state no greater than fixed SGD plus 64 bytes;
- zero replay bytes;
- lower loss than the horizon-one and random-policy ablations in at least one
  qualifying family.

## Stop rules

Independent review rejection stops V3 before implementation. Tune-lock failure
stops before assessment. Synthetic `NoCandidate` closes V3 permanently and
prohibits real execution. A synthetic candidate still requires independent
execution review before fresh real panels are opened.

Any real campaign requires new custody identity, a new exact campaign
manifest, and a new privileged energy receipt. The V2 `664.824 J` receipt
cannot certify V3. Publication additionally requires strict quality,
adaptation, resource, multiplicity, and measured-energy success across at
least two real families. A failed real gate closes V3 without retuning.

Astral remains isolated throughout.

