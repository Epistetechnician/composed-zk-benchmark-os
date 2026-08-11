# V25 Maintenance: Closed Classification Validator

State slice: `astral-telemetry-information-presence-v25`.

Date: 2026-08-10.

## Change

The independent V25 bundle validator now rejects any `result.json` classification
outside the six classifications emitted by the frozen V25 protocol:

- `NotRunInformationPresenceProbe`;
- `ProbeTargetBehaviorallySilent`;
- `ProbeControlFloorViolation`;
- `InformationPresenceReportGapObserved`;
- `InformationPresenceParityObserved`;
- `InformationPresenceNoCandidate`.

Previously, an unknown classification could pass the manifest and then bypass all
classification-specific checks. The validator is now fail-closed at the result
classification boundary. A hermetic regression test creates a manifest-consistent
bundle with an unknown classification and requires rejection.

## Validation

- `python -m py_compile tools/astral-telemetry-probe-v25/v25.py tools/astral-telemetry-probe-v25/validator_v25.py tools/astral-telemetry-probe-v25/tests/test_v25.py` — passed.
- A direct system-Python validator smoke test with a manifest-consistent
  `UnexpectedFutureOutcome` result — rejected as expected.
- The prescribed baseline/full pytest command was attempted before editing and
  could not collect V24/V25 tests because the active system Python lacks `mlx`.
  The repository `.venv` was also checked; its Python 3.14 environment has an
  incompatible Python 3.11 NumPy extension and cannot run the suite.

V25 remains closed and was not rerun, retuned, or used for new scientific
execution. No assessment artifact, concept, configuration, or external bundle
was modified.

## Claim boundary

This is validator hardening and local regression evidence only. It does not
replicate or extend the V25 result, does not create accepted Evidence Ledger
evidence, and does not authorize Stage 0C, Stage 1, benchmark, consciousness,
introspection, or production claims. The ceiling remains
`LocalDevelopmentPrivilegedTelemetryInformationPresence`.
