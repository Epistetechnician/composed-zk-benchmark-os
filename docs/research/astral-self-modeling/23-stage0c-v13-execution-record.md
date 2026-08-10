# Stage 0C V13 Execution Record

State slice: `astral-stage0c-prediction-locked-causal-target-v13`.

Protocol:
[V13 prediction-locked causal target](22-stage0c-prediction-locked-causal-target-v13.md).

Execution: `DevelopmentNoCandidate`. Confirmation: `NotAuthorized`. Stage 1:
`BlockedByStage0C`.

All four actors reproduced at train/development accuracy `1.0`. The runner
sealed `12,800` assessment predictions before materializing `2,560` assessment
effects. The independent validator confirmed protocol binding, prediction-lock
digests, censuses, metrics, manifest, and non-escalating claim fields.

| Estimator | Pooled MSE | Correlation | Calibration slope |
|---|---:|---:|---:|
| Telemetry | 266.4422 | 0.0986 | 0.0706 |
| Activation-only | 148.1730 | 0.0604 | 0.0791 |
| Constant | 88.5933 | 0.3615 | 0.7465 |

Manifest SHA-256:
`d54125f2f5f4a8177dd267c509c5ba8026cea7cfddb57ab2d3c2b2fbd6de3ff4`.

The richer local vector was substantially worse than both activation-only and
the site/operator constant floor. Adding the causally connected CLS MLP site
and correcting prediction order did not rescue cross-actor effect prediction.
This closes the bounded CLS ridge-estimator lane. It does not refute nonlinear,
architecture-specific, or within-actor causal-effect models.

Evidence ceiling: `LocalDevelopmentCausalTargetDiagnostic`.
