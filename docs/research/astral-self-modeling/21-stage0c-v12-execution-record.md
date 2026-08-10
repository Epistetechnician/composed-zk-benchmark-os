# Stage 0C V12 Execution Record

State slice: `astral-stage0c-intervention-effect-target-validity-v12`.

Protocol:
[Stage 0C intervention-effect target validity V12](20-stage0c-intervention-effect-target-validity-v12.md).

Execution: `CompletedDevelopmentNoCandidate`. Confirmation:
`NotAuthorized`. Stage 1: `BlockedByStage0C`.

Executed 2026-07-26 with repository-external output and no use of the reserved
seeds or families.

- actor seeds `211`, `223`, and `229` each reproduced with train accuracy `1.0`
  and development accuracy `1.0`;
- record census: `24,576`;
- prediction census: `61,440`;
- telemetry pooled MSE: `148.1013903956875`;
- activation-only pooled MSE: `132.2657318381492`;
- constant pooled MSE: `99.50566867279663`;
- telemetry pooled correlation: `0.15062221990134333`;
- telemetry calibration slope: `0.18226704159713955`;
- telemetry top-one regret: `0.5913274404964436`;
- activation-only top-one regret: `0.6557041811183814`;
- manifest SHA-256:
  `aadb7a2002a7169b6cf3b712f2e9a5fa36d6a6d2b8aa3b13031b88cd69fce3fe`.

The classification is `DevelopmentNoCandidate`. Telemetry improved the
secondary top-one regret but failed the primary continuous-effect endpoint,
failed calibration, and was worse than the constant and activation-only
baselines. No estimator is nominated and no confirmation is authorized.

The development runner materialized assessment effects before emitting the
prediction file, although the frozen fitting code used only other-actor design
rows. This ordering cannot support a future nomination and must be replaced by
a prediction lock before assessment-effect materialization in any redesigned
protocol. It does not rescue the observed failure.

Evidence ceiling:
`LocalExploratoryInterventionPredictionDiagnostic`. This result does not
establish a causal graph, attribution validity, observer benefit, self-modeling,
introspection, correction value, benchmark evidence, or accepted evidence.
