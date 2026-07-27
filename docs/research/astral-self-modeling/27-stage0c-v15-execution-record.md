# Stage 0C V15 Execution Record

State slice: `astral-stage0c-prospective-actor-specific-explainer-v15`.

Execution: `DevelopmentNoCandidate`. Confirmation: `NotAuthorized`. Stage 1:
`BlockedByStage0C`.

All three actors reproduced at train/development accuracy `1.0`. The runner
sealed `23,040` predictions before materializing `3,840` assessment effects.

| Method | Pooled MSE | Correlation | Calibration slope |
|---|---:|---:|---:|
| Same-actor telemetry | 49.2301 | 0.6908 | 1.0055 |
| Same-actor activation | 56.9549 | 0.6286 | 1.0007 |
| Same-actor constant | 63.4133 | 0.5715 | 0.9999 |
| Same-actor text/input-output | 71.6010 | 0.4895 | 0.9935 |
| Same-actor shuffled telemetry | 72.4382 | 0.4804 | 0.9795 |
| Other-actor telemetry | 365.9778 | 0.0196 | 0.0114 |

Same-actor telemetry improved pooled MSE over activation-only by `13.56%` and
over other-actor telemetry by `86.55%`. However, the preregistered uniform gate
failed: seed `269` zero-ablation improved only `1.60%`, and seed `271`
matched-patch was `1.57%` worse than activation-only. No candidate advances.

The prospective result supports an actor-specific supervised-explainer
advantage in aggregate and strongly confirms coordinate nontransportability.
It does not establish uniform intervention prediction, introspection,
self-modeling, correction value, or Stage 0C confirmation.

Manifest SHA-256:
`6f482fe5320a9bac219b6b8454977a48308acf49b51d512238ddda3152bea7a8`.
