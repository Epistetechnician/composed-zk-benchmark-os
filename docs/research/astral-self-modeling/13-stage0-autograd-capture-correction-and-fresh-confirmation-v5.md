# Stage 0 Autograd-Capture Correction and Fresh Confirmation V5

State slice: `astral-stage0-autograd-capture-correction-and-fresh-confirmation-v5`.

Status before execution: `PreregisteredCorrectedFreshHoldoutConfirmation`.
Evidence ceiling: `LocalLearnedModelMeasurementCandidate`.

V5 corrects only the V4 autograd capture boundary. The override-capable actor
must compute the classifier CLS state directly from the exact returned head
tensor, while remaining bitwise equal to the V3 clean logits, heads, and
attention. A development-only test must demonstrate that the candidate gradient
with respect to the returned heads is finite and non-null before scientific
training or holdout access.

All V4 methods, endpoints, baselines, controls, thresholds, aggregation,
bootstrap, resource caps, verdict rules, and claim limits remain unchanged.
Training remains the frozen 2,000-update V3 procedure. New actor seeds are
exactly `137, 139, 149`. The new untouched holdout is exactly families
`448..511`. V4 seeds and families are permanently excluded. No V4 result is
pooled with V5.

Each actor seed is trained twice and must meet the same eligibility,
checkpoint, selected-step, and trajectory reproducibility gate before the
holdout is materialized. All 3,072 scores must be serialized and locked before
any intervention. Any failure follows the V4 `Inconclusive`, `Null`, `Invalid`,
and permanent-holdout-retirement rules.

A pass has the same narrow V4 meaning. It is not independent replication,
program-wide error-controlled evidence, complete circuit recovery, general
causal fidelity, introspection, self-modeling, correction, observer value,
safety, benchmark evidence, or accepted evidence.

## Execution Record — 2026-07-26

Frozen verdict: `Null`.

All three actor seeds qualified twice with identical selected update,
checkpoint digest, and trajectory digest:

| Seed | Train / development | Step | Checkpoint SHA-256 | Trajectory SHA-256 |
|---:|---|---:|---|---|
| `137` | `1.0 / 1.0` | `2000` | `efffe1357d082a52b4ff43079c12d98f12f22b83bc58b32d80f5a3037d000c9c` | `e7608a5d84321cc9cf0fc13358e76d5fba1b27a1bb286445ddc4c100f9f779d9` |
| `139` | `1.0 / 1.0` | `2000` | `c4fab9103da6a9c1f348b9ddbbab52f15543dcbf0adeb6806f0064c217b4307f` | `ec8da3ae031c97871e372cfebf8a05653c84067c302b3552f3d0b5ca6cc99ab0` |
| `149` | `1.0 / 1.0` | `2000` | `16e6198abd28fe4a7e6e383b67314b87552e41fb0e3a3830f1e7dde70c7d371e` | `12f944eab2deba7ed20de8a945a525939d9bdcb48591d2888e36770ebc81a9b6` |

The complete 3,072-record evaluation passed coverage, evaluation accuracy,
permutation, patch, no-op, repeatability, clean-parity, artifact, and semantic
validation gates. Runtime was `61.29` seconds. Informative coverage and
evaluation accuracy were `1.0` for every seed.

Paired regret advantage `D = baseline - candidate`:

| Baseline | Mean D | V5-local 95% interval | Per-seed D |
|---|---:|---|---|
| Activation norm | `0.0922` | `[-0.0552, 0.2877]` | `-0.0561, 0.2890, 0.0438` |
| Attention mass | `0.5104` | `[0.3538, 0.6789]` | `0.3522, 0.6824, 0.4966` |
| Gradient norm | `0.4090` | `[0.3489, 0.4459]` | `0.3477, 0.4340, 0.4453` |
| Permuted candidate | `0.3963` | `[0.2776, 0.4914]` | `0.2724, 0.4938, 0.4226` |

The primary gate failed only against activation norm: its interval lower bound
was below `0.05`, seed `137` was unfavorable, and seed `149` did not exceed the
`0.05` practical margin. Descriptive success against the other baselines and
all patch comparisons cannot rescue the intersection gate.

An inherited inventory label initially named the V4 family range in
`summary.json`. The existing V5 records already contained exactly families
`448..511`. The label and manifest binding were corrected without retraining,
rescoring, or rerunning interventions. The semantic validator then confirmed
3,072 unique records and verdict `Null`. Final manifest SHA-256:
`badd29b1bd9b168b76cf8562bc61851247f328e616eb90831b9c97a304d3e603`.

The scientific conclusion is narrow: the frozen V5 superiority criterion did
not hold. Gradient-times-activation was not reliably better than activation
magnitude across the three fresh actors. Stage 1 observer work remains blocked.
