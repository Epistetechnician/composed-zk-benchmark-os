# Stage 0C Effect Transportability Diagnostic V14

State slice: `astral-stage0c-effect-transportability-diagnostic-v14`.

Status: `PostHocDiagnosticOnly`. Parent: validated V13 bundle. No new actor
training, telemetry, intervention, or confirmation data is authorized.

## Question

Did V13 fail mainly because intervention effects do not transport across actor
coordinates, or because the available local telemetry is not predictive even
within one frozen actor?

## Frozen Analysis

For each V13 assessment actor, families `656..659` form a diagnostic fit half
and `660..663` form a diagnostic test half. This split is post hoc and cannot
nominate an estimator.

Compare on the diagnostic test half:

1. V13 cross-actor predictions;
2. cross-actor site/operator constant learned from V13 fitting records;
3. actor-conditioned site/operator constant learned from its diagnostic fit
   half;
4. actor-conditioned activation-only ridge;
5. actor-conditioned full-telemetry ridge.

Ridge uses the unchanged V13 features, standardization, and `alpha=0.001`.
Report MSE, MAE, correlation, calibration, per actor/operator results, and
variance fractions attributable to actor, site/operator, and residual
variation.

## Interpretation

- `CrossActorTransportFailure` if actor-conditioned constant reduces test MSE
  by at least 20% relative to the cross-actor constant and within-actor
  telemetry beats within-actor activation-only.
- `ActorBaselineShiftOnly` if the actor-conditioned constant improves by 20%
  but telemetry does not beat activation-only.
- `LocalTelemetryNonpredictive` if actor conditioning improves less than 20%
  and telemetry does not beat activation-only.
- otherwise `MixedDiagnostic`.

Every outcome is exploratory. It cannot rescue V13, authorize confirmation, or
support introspection/self-modeling claims.
