# Oak Lab H100 replication V10 protocol

State slice: `oaklab-experience-learning-h100-replication-v10`.

V10 is a fresh protocol identity. V9 is historical and is not an input.
The treatment is a dual-budgeted segment-credit controller. At each 32-row
boundary it may enable the next segment using only the completed previous
segment's loss, active-operation count, and charged storage. The controller
maintains utility, operation, and storage exponential moving averages. Current
row outcomes and current-segment counters are unavailable to action selection.
Controller state is charged in every arm; replay and hidden accumulation are
forbidden.

The primary estimand is paired segment utility over identical ordered streams,
identical initial checkpoints, randomized arm order, one warmup segment, and
seven post-washout segments. Utility is
`-loss - 0.001*active_operations - 0.05*storage_bytes/dimension`.
The six streams cover predictable noise, drift, delayed reward, event sensing,
long horizon, and an independent pure-noise null. Fit, tune, and assessment
seeds are disjoint (48/24/48), with three repeats, 0.80 power, ICC 0.50,
minimum effect 0.05, and Holm correction. Adaptation is segment-bounded and
censored at trajectory end. Statistics must be derived from raw counter rows;
caller-supplied gate booleans are invalid.

The compiler and validator enforce canonical JSON bytes, recursive closed
schemas, exact draw order, numeric ASTs and byte layouts, controller storage,
counter-derived resource metrics, prediction-lock-before-assessment, an absent
assessment root, provider allocation/cost/stop cross-binding, a closed result
root, and a positive hard USD ceiling declaration. The campaign-manifest
artifact binds source, compiler, validator, tests, the frozen current
`AGENTS.md`, compiled protocol, packet, backend, guard, custody, locks,
provider, energy, and result-root digests.

Implementation is prohibited before an independent packet-bound signed
`ACCEPT`. Synthetic qualification is the only permitted post-acceptance work.
Real execution requires a separate candidate result and authorization, a fresh
campaign manifest, privileged joules, and a new review. V6, V7, V8, V9,
Phase 836, and the plasticity guard remain closed historical lanes. Astral is
isolated. Publication remains `no_candidate` until all quality, adaptation,
resource, statistical, custody, and measured-energy gates pass across at least
two real families.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v10`.
