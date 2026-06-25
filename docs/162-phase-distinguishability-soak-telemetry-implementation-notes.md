# Phase 162 Distinguishability Soak Telemetry Implementation Notes

Status: complete.

## Shipped

- `observed_distinguishability_axis` in `scoring/distinguishability.rs`.
- Backward-compatible `SoakTelemetryCounters` distinguishability fields with
  `#[serde(default)]` and `record_distinguishability_axis`.
- Soak runner records one axis per successful mutation replay from
  `expected_verdict` × first `backend_outcome`.
- Tests: `crates/zkbench-core/tests/phase_162_distinguishability_telemetry.rs`.

## Validation

- `cargo test -p zkbench-core --test phase_162_distinguishability_telemetry`
  passes, covering counter recording and merge behavior.

## Claim boundary

Telemetry is internal-only and does not populate `ScoreReport` axes.
