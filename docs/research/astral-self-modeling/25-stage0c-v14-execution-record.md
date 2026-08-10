# Stage 0C V14 Execution Record

State slice: `astral-stage0c-effect-transportability-diagnostic-v14`.

Execution: `CrossActorTransportFailure`. This is a retrospective diagnostic,
not a candidate nomination. V13 remains `DevelopmentNoCandidate`; confirmation
and Stage 1 remain unauthorized.

The read-only analysis validated and bound the V13 manifest before joining its
sealed telemetry and effects. Families `656..659` were the frozen within-actor
diagnostic fit half and `660..663` the test half.

| Method | Pooled MSE | Correlation | Calibration slope |
|---|---:|---:|---:|
| V13 cross-actor telemetry | 266.9838 | 0.0988 | 0.0707 |
| Cross-actor constant | 94.9856 | 0.3114 | 0.5944 |
| Actor-conditioned constant | 59.9579 | 0.6301 | 1.0003 |
| Actor-conditioned activation | 58.2625 | 0.6435 | 0.9983 |
| Actor-conditioned telemetry | 52.0259 | 0.6908 | 0.9721 |

Actor-conditioned telemetry beat activation-only for every actor/operator cell.
The actor-conditioned constant reduced MSE by `36.88%` relative to the
cross-actor constant. Variance decomposition attributed `0.43%` to actor mean,
`24.16%` to site/operator structure, and `75.41%` to residual variation.

The result supports a bounded diagnosis: raw telemetry coordinates and their
effect mapping do not transport across independently trained actors, while
within-actor local telemetry retains linear predictive information in this
post-hoc split. It does not establish a prospective within-actor estimator,
coordinate alignment, a causal graph, introspection, or self-modeling.

V14 manifest SHA-256:
`c08e50873cfecbf700f2885889cbd9e84ed340f2f53280c6e356bf30f08c013d`.
