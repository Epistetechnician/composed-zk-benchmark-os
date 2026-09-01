# Evidence-conditioned multiscale plasticity v3 execution record

Date: 2026-08-28.

State slice: `astral-evidence-conditioned-multiscale-plasticity-v3`.

Status: `SyntheticFactorialValidated / ModelBearingExecutionNotAuthorized`.

Claim ceiling: `LocalDevelopmentExactSyntheticLiteratureInformedControllerOnly`.

## Execution and validation

The exact synthetic learner ran the frozen `6 x 4 x 2 x 4` factorial: 192
cells, 9 replicates per cell, and 1,728 replicates. Every replicate used 48
micro-update attempts, 288 gradient units, and 288 shadow units. The final
report was serialized and accepted by the independent aggregate-only
validator.

Result SHA-256:

```text
ef06664cfd1dcf5817918668d74c76b2869383bc18d136819e8472191fff9577
```

Prediction-lock SHA-256:

```text
88ec35eb53c961fb6ce8d379a1e6dc1716f3ccbef833bdfcee24ae15771fbf85
```

The focused v3 suite passed 6 tests. All 192 cells passed the mechanical
guards. Maximum verification cost was 38 units; maximum shard-order range was
0.0359424922; minimum final plasticity was 0.9162312651; rollback error was
zero. The equal-compute tuple was `(48, 288, 288)` for every cell.

## Primary result

Higher primary values are better. The table below uses the deterministic,
oracle, evidence-conditioned arm unless noted otherwise.

| Memory policy | Primary mean | Delta versus `single` |
|---|---:|---:|
| `single` | 0.0898568074 | 0 |
| `fast_slow` | 0.0895596595 | -0.0002971479 |
| `replay` | 0.0875669286 | -0.0022898788 |
| `ewc` | 0.0898883913 | +0.0000315839 |
| `plasticity_guard` | 0.0901909211 | +0.0003341137 |
| `integrated` | 0.0893457266 | -0.0005110808 |

The synthetic screen therefore nominates `plasticity_guard` as the strongest
memory-policy candidate in this panel. The EWC-style variant is effectively
neutral at this scale. Replay and the all-mechanisms combination are negative
relative to the single-state baseline; replay is not carried forward.

## Schedule and admission results

For the `integrated`, oracle, evidence-conditioned arm:

| Schedule | Primary mean | Delta versus fixed |
|---|---:|---:|
| `fixed` | 0.0893457266 | 0 |
| `single_frequency` | 0.0896860392 | +0.0003403126 |
| `dual_frequency` | 0.0895948883 | +0.0002491617 |
| `bounded_stochastic_dual` | 0.0897252157 | +0.0003794891 |

Dual frequency was below single frequency by `0.0000911509`; the wave
mechanism is not supported as a useful addition. Stochastic dual scheduling
was positive against deterministic dual scheduling in the oracle panel by
`0.0001303274`, but that small effect was not stable across taxonomies: it was
positive for oracle and noisy, negative for absent, and positive only in 3 of 9
shuffled replicates. It is rejected under the stability rule.

For the integrated dual-frequency arm, evidence-conditioned admission versus
fixed admission produced:

| Taxonomy | Admission delta | Positive matched replicates |
|---|---:|---:|
| `oracle` | +0.0012125356 | 6/9 |
| `noisy` | -0.0000629840 | 7/9 |
| `shuffled` | +0.0010955689 | 4/9 |
| `absent` | -0.0003759930 | 4/9 |

Gating is not a general result because it fails the noisy and absent taxonomy
conditions. It remains a bounded synthetic candidate only for a future test
where the controller is explicitly trained or specified against measurable,
reliable evidence; it is not evidence that “verification” improves learning.

## Decision

Keep `plasticity_guard` as the next synthetic-controller candidate. Do not
carry replay, the integrated combination, dual-frequency waves, or bounded
stochastic scheduling into a model-bearing experiment based on this run. Keep
EWC-style protection as a neutral comparator, not a positive result. The
result is a mechanism screen, not a scientific claim about transformers,
neuroscience, cryptographic verification, or Astral.

No Astral integration was run. The controller-only code reports
`not_run_synthetic_controller_only`; it did not predict Astral causal effects,
calibration, or instrumental correction.

## Next gate

The next experiment requires separate authorization for a cached-model run
using reversible adapters only. It must use fresh splits, prediction locking,
independent validation, equal compute, and the surviving candidate as a
predeclared controller comparison—not as an adaptive search. Base weights,
V48 artifacts, and the closed V48 causal-target lane remain untouched. Real
ZK/PQC work comes later and must begin with one concrete proof statement and
measured overhead per backend.
