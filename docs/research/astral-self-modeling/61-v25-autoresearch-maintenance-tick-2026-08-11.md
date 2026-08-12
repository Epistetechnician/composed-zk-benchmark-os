# V25 bounded autoresearch maintenance tick — 2026-08-11 (required-field fail-closed checks)

State slice: `astral-telemetry-information-presence-v25`.

## Research question

Does the independent V25 artifact validator reject missing required fields in
the configuration lock and manifest with deterministic `ValueError`s, rather
than leaking `KeyError` exceptions?

Measurable criterion: a lock missing either `assessment_results_absent` or
`inputs`, and a manifest missing `files`, must be rejected at the validator
boundary; the exact canonical suite must pass; and all changes must remain in
the authorized V25 source/test/documentation scope.

## Inspection and reproduction

The existing shape checks handled non-object JSON documents and malformed
`inputs`/`files` values, but missing required keys were still accessed directly.
That made malformed artifacts fail through incidental dictionary exceptions
instead of the validator's explicit fail-closed error path.

## Change kept

Added explicit presence checks for the lock ordering marker, lock inputs, and
manifest file map. Added hermetic regressions for each missing-field case. No
concepts, prompts, injection sites, strengths, wrappers, probe math,
qualification, assessment, or claim boundary changed.

## Validation

The canonical command and its exact result are recorded in the maintenance
report delivered for this tick. No network, downloads, model execution,
training, adaptive tuning, assessment rerun, retuning, prior-data/adapter
reuse, or Evidence Ledger mutation occurred.

## Checkpoint and claim boundary

Kept paths are exactly this validator, its manifest-structure tests, and this
phase note. The unchanged claim ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.