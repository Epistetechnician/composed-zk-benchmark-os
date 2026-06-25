//! Phase 162 — distinguishability soak telemetry wiring.

use zkbench_core::{
    observed_distinguishability_axis, BackendOutcome, ExpectedVerdict,
    MutationDistinguishabilityAxis, SoakTelemetryCounters,
};

#[test]
fn telemetry_counters_record_observed_axis() {
    let mut counters = SoakTelemetryCounters::default();
    let axis = observed_distinguishability_axis(ExpectedVerdict::Reject, BackendOutcome::Rejected);
    assert_eq!(axis, MutationDistinguishabilityAxis::DetectedRejection);
    counters.record_distinguishability_axis(axis);
    assert_eq!(counters.distinguishability_detected_rejection_count, 1);
}

#[test]
fn telemetry_counters_merge_distinguishability_fields() {
    let mut left = SoakTelemetryCounters {
        distinguishability_unsound_acceptance_candidate_count: 2,
        ..Default::default()
    };
    let right = SoakTelemetryCounters {
        distinguishability_inconclusive_count: 3,
        ..Default::default()
    };
    left.merge(&right);
    assert_eq!(
        left.distinguishability_unsound_acceptance_candidate_count,
        2
    );
    assert_eq!(left.distinguishability_inconclusive_count, 3);
}
