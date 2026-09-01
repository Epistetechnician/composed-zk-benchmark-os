# Oak Lab experience-learning baselines V1

State slice: `oaklab-experience-learning-baselines-v1`

## Scope

This additive, dependency-free package is the first executable benchmark
kernel for the experience-learning and event-driven systems lanes. It does
not alter Astral's causal lane. It consumes one immutable `Experience` record
per `observe` call and writes only aggregate benchmark results when invoked by
the runner.

The synthetic `NoisyMNISTLikeStream` and `EventCameraLikeStream` are local
fixtures. They are not downloaded MNIST or event-camera data, and results on
them are not claims about those real datasets. A `NoisyMNISTArrayStream`
adapter accepts caller-supplied, already-custodied flattened arrays without
downloading, shuffling, or future-dependent preprocessing.

## Learners

- SGD and Adam at explicitly selected batch sizes 1, 32, and 128. Batches
  larger than one are visible in the result as intentional buffering; the
  batch-one arms have no gradient accumulation or replay.
- IDBD uses a bounded log step size per input coordinate. With
  `delta = target - prediction`, `g_i = delta x_i`,
  `beta_i <- beta_i + meta_step g_i h_i`, `alpha_i <- exp(beta_i)`,
  `w_i <- w_i + alpha_i g_i`, and
  `h_i <- max(0, h_i(1-alpha_i x_i^2)) + alpha_i g_i`.
- NetworkIDBD is a deliberately named nonlinear extension: the same diagonal
  step-size and first-order trace rule is applied to every parameter of a
  ReLU one-hidden-layer network. It is not represented as an exact reproduction
  of a published Network-IDBD implementation.
- TIDBD applies semi-gradient TD(0), `delta = r + gamma V(s') - V(s)`, then
  updates `beta_i <- beta_i + theta delta x_i h_i`,
  `z_i <- gamma lambda z_i + x_i`, `w_i <- w_i + alpha_i delta z_i`, and
  `h_i <- max(0, h_i(1-alpha_i x_i z_i)) + alpha_i delta z_i`. Independent
  one-step parity tests compare these transitions against `equations.py`.
- Replay is an explicit FIFO replay arm; replay examples are counted and are
  never silently included in strict batch-one arms.
- EWC is a diagonal quadratic consolidation penalty updated at explicit task
  boundaries.
- Plasticity guard attenuates updates after a declared surprise and recovers
  within fixed bounds. It is a benchmark baseline, not a claim that prior
  continual-learning experiments generalized.
- Event-driven is a software sparse simulator. It updates only coordinates
  whose event magnitude crosses a declared threshold and reports active
  synaptic operations. Its energy field is an operation-count proxy, not joules.

## Streams and endpoints

The runner uses disjoint deterministic fit, tune, and assessment ranges for:

1. sparse predictable signal plus unpredictable noise;
2. synthetic noisy/distractor-heavy digit-like patterns;
3. nonstationary feature relevance;
4. drifting targets;
5. delayed rewards for TD prediction;
6. sparse event-camera-like polarity events; and
7. a long-horizon composition of shifts, drift, and delayed observations.

TIDBD is scored only on the delayed-reward stream. Other algorithm/stream
pairs are recorded as `not_applicable` rather than silently treating a
supervised target as a zero-reward TD target.

The primary endpoint is cumulative prediction loss for each stream family.
The result also reports adaptation lag at task changes, forgetting,
calibration diagnostic, updates, events, active operations, replay bytes,
model/state bytes, wall-clock latency, operation-based energy proxy, and
rollback count. No hyperparameter is selected from assessment output.

## Batch-one and event accounting

Every learner receives exactly one current experience per `observe` call.
The result records `learner_observe_calls`,
`max_experience_items_per_observe`, explicit batch size, replay permission,
flush count, and a hidden-accumulation flag. Strict batch-one means batch size
one and no replay. Event-driven counts only threshold-passing coordinates;
hardware energy is intentionally out of scope until a defined hardware path
is measured.

## Independent validation and claim ceiling

`experiments/experience_learning/validate.py` independently recomputes the
result digest and checks schema, split, batch-one, replay, event, and aggregate
invariants. `experiments/experience_learning/replay.py` reruns the same
stream/learner configuration and compares canonical aggregate output; timing
is retained as a metric but excluded from the reproducibility digest. The
current ceiling is
`LocalDevelopmentOakLabExperienceLearningBaselineBenchmark`: executable local
baselines and synthetic-stream accounting only. This slice does not establish
SOTA, real-dataset superiority, causal self-modeling, Astral promotion,
neuromorphic energy gains, or production readiness.

## Source references

- [Oak Lab: Learning from experience instead of curated datasets](https://oaklab.ai/posts/learning-from-experience-instead-of-curated-datasets)
- [IDBD background](https://www.researchgate.net/publication/2783837_Adapting_Bias_by_Gradient_Descent_An_Incremental_Version_of_Delta-Bar-Delta)
- [TIDBD](https://arxiv.org/abs/1908.05751)
- [Event-Driven Learning for Spiking Neural Networks](https://arxiv.org/abs/2403.00270)
- [Event-Driven Random Back-Propagation](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2017.00324/full)
