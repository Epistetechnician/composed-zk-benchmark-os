# V25 Maintenance: Bundle Boundary and Claim-Envelope Hardening

State slice: `astral-telemetry-information-presence-v25`.

Date: 2026-08-10.

## Measurable maintenance questions

1. Can a declared manifest path escape the external bundle root or resolve through a
   symlink? The validator must reject absolute/parent-traversal declarations and
   any symlink anywhere in the bundle before digest use.
2. Can a manifest-consistent result rewrite the V25 claim ceiling or blocked-phase
   status? The validator must require the exact frozen `NotAuthorized` /
   `Blocked` / `BlockedByStage0C` envelope and the unchanged
   `LocalDevelopmentPrivilegedTelemetryInformationPresence` ceiling.

## Changes kept

- Added confined path resolution for manifest and configuration-lock input names,
  with explicit failure messages for root escape.
- Added fail-closed symlink rejection for bundle trees.
- Added exact result-boundary validation for confirmation, Stage 0C, Stage 1, and
  claim ceiling fields.
- Added six hermetic adversarial regressions covering three path forms, symlink
  escape, and four result-boundary tamper cases.

These are independent artifact-validation controls. They do not alter V25
concepts, injection sites, strengths, wrappers, prompts, probe math,
qualification, sealed assessment, or emitted scientific results.

## Verification

- Red-before-implementation: the four result-boundary tests failed because the
  validator accepted the tampered manifest-consistent results.
- `python -m pytest -q tools/astral-telemetry-probe-v25/tests/test_validator_hardening.py tools/astral-telemetry-probe-v25/tests/test_v25.py`
  — `25 passed` after implementation.
- The authorized combined suite
  (`experiments/astral_fsm/tests tools/astral-hybrid-instrument-v24/tests
  tools/astral-telemetry-probe-v25/tests`) — `59 passed`.
- The verified offline MLX compatibility environment was used; no package
  installation or network access was attempted.

## Claim boundary

No V25 assessment was rerun, retuned, or reopened. No accepted Evidence Ledger
mutation or scientific claim upgrade occurred. The unchanged ceiling is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
