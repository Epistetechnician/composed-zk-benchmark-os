# Oak Lab experience-learning benchmark V2

State slice: `oaklab-experience-learning-benchmark-v2`

## Purpose and boundary

V2 turns the V1 executable learner kernel into a reproducible assessment
protocol. A sealed hyperparameter manifest is hashed before any assessment
seed runs. Every seed uses fixed fit, tune, and assessment ranges; assessment
metrics cannot alter the manifest. This is the benchmark implementation of the
Oak Lab premise that learning from an experience stream must separate
learnable signal from unlearnable correlation.

The V2 result is aggregate-only and digest-bound. It does not claim SOTA,
real-dataset validity, neuromorphic energy savings, production readiness, or
causal evidence. Astral remains a separate lane and is not an input to this
benchmark.

## Statistical contract

The default assessment uses five distinct seed offsets (`0, 1, 2, 3, 4`). For
each algorithm and stream, the result retains only per-seed scalar metrics and
their mean, sample standard deviation, and 95 percent normal-approximation
confidence interval. Each non-reference algorithm also receives a paired
normal-approximation t test against `sgd_b1` on the same seed offsets. The
test is explicitly labeled and is not a substitute for a preregistered
distributional analysis at publication scale.

The Pareto report treats mean loss, updates, active synaptic operations, and
state bytes as lower-is-better dimensions. The publication gate requires a
mechanism to improve mean loss while being no worse on all three resource
dimensions in at least two stream families. A frontier point alone is not a
publication claim.

## Controls and execution accounting

Every stream includes a causal running-mean noise-floor control and an
oracle-feature SGD control projected onto the stream's declared predictable
coordinates. These controls diagnose whether an apparent gain comes from
learnable structure, unlearnable noise, or privileged feature access.

V1's exact one-experience accounting remains in force. Batch sizes 32 and 128
are explicit buffering baselines; strict batch-one arms have one current item,
no hidden gradient accumulation, and no replay. Replay is reported separately.
All update, event, active-operation, replay-storage, and state-byte fields are
retained as operation/resource measurements.

## Real-data and energy boundaries

`custody.py` is a read-only JSONL adapter for caller-custodied NoisyMNIST,
event-camera, sensor, and long-horizon artifacts. It verifies file digests,
row schemas, finite values, and contiguous source order without downloading,
shuffling, or future-dependent normalization. The first four real source
archives and bounded panels are held in an external immutable custody root;
they are not bundled in Git.

`energy.py` accepts one digest-bound CSV receipt from a declared hardware path
and reports joules per event. `operation_energy_proxy` remains a separate
operation-count diagnostic and cannot be presented as joules. Dense CPU,
sparse CPU, GPU, event-driven software, and neuromorphic backends remain
The backend parity runner now covers dense CPU, sparse CPU, optional CUDA, and
event-driven software execution, with GPU unavailable status explicit on hosts
without CUDA. The declared macOS `powermetrics` CPU path and trapezoidal
integration tool exist, but no hardware energy result is asserted here because
privileged sampling was unavailable during this run.

## Commands and validation

```sh
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.run_v2 \
  --output /tmp/oaklab-experience-learning-v2.json --steps 256
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.validate_v2 \
  /tmp/oaklab-experience-learning-v2.json
PYTHONDONTWRITEBYTECODE=1 python -m experiments.experience_learning.replay_v2 \
  /tmp/oaklab-experience-learning-v2.json
pnpm --ignore-workspace run verify:experience-learning-v2
```

The synthetic matrix remains available for fast local regression. The external
real-panel matrices now have independent custody and powered assessment
receipts, but the full-campaign gate is still `no_candidate`; no SOTA or
hardware-energy claim is made.

## References

- [Oak Lab: Learning from experience instead of curated datasets](https://oaklab.ai/posts/learning-from-experience-instead-of-curated-datasets)
- [IDBD background](https://cdn.aaai.org/AAAI/1992/AAAI92-027.pdf)
- [Original TIDBD algorithm](https://arxiv.org/abs/1804.03334)
- [TIDBD real-world predictive-knowledge evaluation](https://arxiv.org/abs/1908.05751)
- [Event-Driven Learning for Spiking Neural Networks](https://arxiv.org/abs/2403.00270)
