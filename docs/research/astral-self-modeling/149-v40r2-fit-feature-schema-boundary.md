# V40R2 Fit-Feature Schema Boundary

Status: `ModelFreeSchemaImplemented / FeatureAcquisitionNotAuthorized`.

The schema freezes seven nonprivileged features and six internal telemetry
features at layers 3, 7, and 11. Every row must bind a fit-family id, stage,
step, `before_step_update` timing marker, and exact source-state hash. Coverage is 384
rows: four fit families by three later stages by 32 steps.

The validator rejects tune/assessment families, post-update timing, outcomes,
retention or protection results, unknown/missing features, nonfinite values,
duplicates, coverage gaps, and source-state mismatches. No model-derived values
exist yet.
