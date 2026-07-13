//! Phase 679 — soak telemetry coverage campaign.
//!
//! Focused local regression coverage for `crates/zkbench-core/src/soak/telemetry.rs`:
//! - All `MutationDistinguishabilityAxis` variants in `record_distinguishability_axis`.
//! - The `else` branch of `record_formal_lane_pipeline` (template_derived=false).
//! - `record_formal_lane_pipeline_outcome` with all `FormalLaneProofStatus` and
//!   `FormalPropertyScopeKind` variants.
//! - All `InternalTimingMetricKind` variants in `SoakTelemetryDurations::add_metric`.
//! - The `!is_internal_only()` rejection branch in `validate_soak_telemetry_report`.
//!
//! This is local regression evidence only; it is not benchmark evidence, ZK backend
//! performance evidence, Level2+ evidence, accepted evidence, or proof.

use zkbench_core::evidence::ClaimBoundary;
use zkbench_core::{
    build_smoke_soak_config, plan_soak_shards, validate_soak_telemetry_report, FamilyKind,
    FormalLanePipelineOutcome, FormalLaneProofStatus, FormalPropertyScopeKind,
    InternalTimingMetricKind, LocalSoakRunner, MockTelemetryClock, MutationClass,
    MutationDistinguishabilityAxis, MutationDistinguishabilityCell, SoakShardId,
    SoakTelemetryClassification, SoakTelemetryClock, SoakTelemetryCounters, SoakTelemetryDurations,
    SoakTelemetryReport, SoakTelemetrySnapshot,
};

fn run_tiny() -> SoakTelemetryReport {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::new(0, 7));
    runner
        .run_shard(SoakShardId::from_index(0))
        .expect("run should complete")
        .telemetry_report
}

#[test]
fn record_distinguishability_axis_covers_all_variants() {
    let mut counters = SoakTelemetryCounters::default();

    for axis in [
        MutationDistinguishabilityAxis::TruePositive,
        MutationDistinguishabilityAxis::DetectedRejection,
        MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate,
        MutationDistinguishabilityAxis::FalseRejectionCandidate,
        MutationDistinguishabilityAxis::Inconclusive,
    ] {
        counters.record_distinguishability_axis(axis);
    }

    assert_eq!(counters.distinguishability_true_positive_count, 1);
    assert_eq!(counters.distinguishability_detected_rejection_count, 1);
    assert_eq!(
        counters.distinguishability_unsound_acceptance_candidate_count,
        1
    );
    assert_eq!(
        counters.distinguishability_false_rejection_candidate_count,
        1
    );
    assert_eq!(counters.distinguishability_inconclusive_count, 1);
}

#[test]
fn record_distinguishability_axis_accumulates_repeatedly() {
    let mut counters = SoakTelemetryCounters::default();
    counters.record_distinguishability_axis(MutationDistinguishabilityAxis::Inconclusive);
    counters.record_distinguishability_axis(MutationDistinguishabilityAxis::Inconclusive);
    counters.record_distinguishability_axis(MutationDistinguishabilityAxis::TruePositive);
    assert_eq!(counters.distinguishability_inconclusive_count, 2);
    assert_eq!(counters.distinguishability_true_positive_count, 1);
}

#[test]
fn observed_axis_round_trip_through_distinguishability_cell() {
    use zkbench_core::scoring::distinguishability::axis_for_classification;
    use zkbench_core::{
        classify_result, observed_distinguishability_axis, BackendOutcome, ExpectedVerdict,
        ResultClassification,
    };

    let cases = [
        (
            ExpectedVerdict::Accept,
            BackendOutcome::Accepted,
            MutationDistinguishabilityAxis::TruePositive,
        ),
        (
            ExpectedVerdict::Reject,
            BackendOutcome::Rejected,
            MutationDistinguishabilityAxis::DetectedRejection,
        ),
        (
            ExpectedVerdict::UnsoundIfAccepted,
            BackendOutcome::Accepted,
            MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate,
        ),
        (
            ExpectedVerdict::Accept,
            BackendOutcome::Rejected,
            MutationDistinguishabilityAxis::FalseRejectionCandidate,
        ),
    ];
    for (expected, outcome, want_axis) in cases {
        let axis = observed_distinguishability_axis(expected, outcome);
        assert_eq!(axis, want_axis);

        let classification = classify_result(expected, outcome);
        let cell_axis = axis_for_classification(classification);
        assert_eq!(cell_axis, want_axis);

        let cell = MutationDistinguishabilityCell {
            expected_verdict: expected,
            backend_outcome: outcome,
            classification,
            axis: cell_axis,
        };
        assert_eq!(cell.axis, want_axis);
        assert_eq!(cell.classification, classify_result(expected, outcome));
    }

    let inconclusive_cases: [(ExpectedVerdict, BackendOutcome); 4] = [
        (ExpectedVerdict::Inconclusive, BackendOutcome::Inconclusive),
        (ExpectedVerdict::Accept, BackendOutcome::Inconclusive),
        (ExpectedVerdict::Reject, BackendOutcome::CapabilityGap),
        (ExpectedVerdict::Reject, BackendOutcome::Error),
    ];
    for (expected, outcome) in inconclusive_cases {
        let axis = observed_distinguishability_axis(expected, outcome);
        assert_eq!(axis, MutationDistinguishabilityAxis::Inconclusive);
        let classification = classify_result(expected, outcome);
        assert_ne!(classification, ResultClassification::ExpectedAcceptAccepted);
    }
}

#[test]
fn record_formal_lane_pipeline_covers_no_template_branch() {
    let mut counters = SoakTelemetryCounters::default();
    counters.record_formal_lane_pipeline(false, false);
    assert_eq!(counters.formal_lane_template_derived_count, 0);
    assert_eq!(counters.formal_lane_evaluation_count, 0);
    assert_eq!(counters.formal_lane_no_template_count, 1);
    assert_eq!(counters.formal_lane_declared_only_count, 0);

    counters.record_formal_lane_pipeline(true, false);
    assert_eq!(counters.formal_lane_template_derived_count, 1);
    assert_eq!(counters.formal_lane_evaluation_count, 1);
    assert_eq!(counters.formal_lane_declared_only_count, 0);

    counters.record_formal_lane_pipeline(true, true);
    assert_eq!(counters.formal_lane_template_derived_count, 2);
    assert_eq!(counters.formal_lane_evaluation_count, 2);
    assert_eq!(counters.formal_lane_declared_only_count, 1);
}

fn outcome(
    template_derived: bool,
    scope: FormalPropertyScopeKind,
    status: Option<FormalLaneProofStatus>,
) -> FormalLanePipelineOutcome {
    FormalLanePipelineOutcome {
        mutation_class: MutationClass::MissingConstraints,
        primary_formal_scope: scope,
        template_derived,
        evaluation: None,
        proof_status: status,
        no_template_reason: None,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        nonclaims: Vec::new(),
    }
}

#[test]
fn record_formal_lane_pipeline_outcome_covers_all_scope_and_status_variants() {
    let scopes = [
        FormalPropertyScopeKind::TransitionGuard,
        FormalPropertyScopeKind::Invariant,
        FormalPropertyScopeKind::LoopBound,
        FormalPropertyScopeKind::Machine,
        FormalPropertyScopeKind::NotApplicable,
    ];
    let statuses = [
        Some(FormalLaneProofStatus::DeclaredOnly),
        Some(FormalLaneProofStatus::ProofAttempted),
        Some(FormalLaneProofStatus::MachineCheckedScoped),
        Some(FormalLaneProofStatus::IndependentlyReproduced),
        None,
    ];

    let mut counters = SoakTelemetryCounters::default();
    for scope in scopes {
        counters.record_formal_lane_pipeline_outcome(&outcome(true, scope, None));
    }
    for status in statuses {
        counters.record_formal_lane_pipeline_outcome(&outcome(
            true,
            FormalPropertyScopeKind::TransitionGuard,
            status,
        ));
    }

    let expected_scope_metric_names = [
        "formal_lane_scope_transition_guard_count",
        "formal_lane_scope_invariant_count",
        "formal_lane_scope_loop_bound_count",
        "formal_lane_scope_machine_count",
        "formal_lane_scope_not_applicable_count",
    ];
    for name in expected_scope_metric_names {
        assert!(
            counters
                .formal_lane_count_by_scope
                .iter()
                .any(|metric| metric.metric_name == name),
            "missing scope metric {name}"
        );
    }

    let expected_status_metric_names = [
        "formal_lane_status_declared_only_count",
        "formal_lane_status_proof_attempted_count",
        "formal_lane_status_machine_checked_scoped_count",
        "formal_lane_status_independently_reproduced_count",
    ];
    for name in expected_status_metric_names {
        assert!(
            counters
                .formal_lane_count_by_status
                .iter()
                .any(|metric| metric.metric_name == name),
            "missing status metric {name}"
        );
    }
}

#[test]
fn record_formal_lane_pipeline_outcome_increments_existing_scope_metric_in_place() {
    let mut counters = SoakTelemetryCounters::default();
    let o = outcome(true, FormalPropertyScopeKind::Machine, None);
    counters.record_formal_lane_pipeline_outcome(&o);
    counters.record_formal_lane_pipeline_outcome(&o);
    let machine_metric = counters
        .formal_lane_count_by_scope
        .iter()
        .find(|metric| metric.metric_name == "formal_lane_scope_machine_count")
        .expect("machine scope metric should exist");
    assert_eq!(machine_metric.count, 2);
    assert_eq!(counters.formal_lane_count_by_scope.len(), 1);
}

#[test]
fn add_metric_covers_all_internal_timing_metric_kinds() {
    let mut durations = SoakTelemetryDurations::default();
    durations.add_metric(InternalTimingMetricKind::Generation, 10);
    durations.add_metric(InternalTimingMetricKind::Mutation, 20);
    durations.add_metric(InternalTimingMetricKind::LocalOracle, 30);
    durations.add_metric(InternalTimingMetricKind::LocalReplay, 40);
    durations.add_metric(InternalTimingMetricKind::PackWriteRead, 50);
    durations.add_metric(InternalTimingMetricKind::ProposalReviewPreview, 60);
    durations.add_metric(InternalTimingMetricKind::SoakRunnerTotal, 70);

    assert_eq!(durations.generation_duration_ms, 10);
    assert_eq!(durations.mutation_duration_ms, 20);
    assert_eq!(durations.local_oracle_duration_ms, 30);
    assert_eq!(durations.local_replay_duration_ms, 40);
    assert_eq!(durations.pack_write_duration_ms, 50);
    assert_eq!(durations.proposal_preview_duration_ms, 60);
    assert_eq!(durations.soak_runner_total_duration_ms, 70);
    assert_eq!(durations.internal_timing_metrics.len(), 7);
}

#[test]
fn add_metric_accumulates_and_records_each_call() {
    let mut durations = SoakTelemetryDurations::default();
    durations.add_metric(InternalTimingMetricKind::Generation, 10);
    durations.add_metric(InternalTimingMetricKind::Generation, 25);
    assert_eq!(durations.generation_duration_ms, 35);
    assert_eq!(durations.internal_timing_metrics.len(), 2);
}

#[test]
fn validate_soak_telemetry_report_rejects_non_internal_only_classification() {
    let mut report = run_tiny();
    report.snapshot.classification = vec![SoakTelemetryClassification::LocalEngineeringMetric];
    let error = validate_soak_telemetry_report(&report)
        .expect_err("non-InternalOnly classification should fail");
    assert!(error.to_string().contains("InternalOnly"));
}

#[test]
fn validate_soak_telemetry_report_accepts_internal_only_snapshot() {
    let report = run_tiny();
    assert!(report.is_internal_only());
    assert!(validate_soak_telemetry_report(&report).is_ok());
}

#[test]
fn snapshot_default_uses_level0_claim_boundary_and_internal_classification() {
    let snapshot = SoakTelemetrySnapshot::default();
    assert_eq!(snapshot.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(snapshot
        .classification
        .contains(&SoakTelemetryClassification::InternalOnly));
    assert!(snapshot
        .classification
        .contains(&SoakTelemetryClassification::NotZkBackendPerformance));
    assert!(snapshot
        .classification
        .contains(&SoakTelemetryClassification::NotOfficialBenchmarkEvidence));
}

#[test]
fn mock_telemetry_clock_steps_deterministically() {
    let clock = MockTelemetryClock::new(100, 7);
    assert_eq!(clock.now_ms(), 100);
    assert_eq!(clock.now_ms(), 107);
    assert_eq!(clock.now_ms(), 114);
}

#[test]
fn mock_telemetry_clock_default_starts_at_zero() {
    let clock = MockTelemetryClock::default();
    assert_eq!(clock.now_ms(), 0);
    assert_eq!(clock.now_ms(), 5);
}
