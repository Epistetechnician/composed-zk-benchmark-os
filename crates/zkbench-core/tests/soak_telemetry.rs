use zkbench_core::{
    build_smoke_soak_config, deserialize_soak_telemetry_report_json, plan_soak_shards,
    score_report_from_local_mutation_evidence, serialize_soak_telemetry_report_json,
    validate_soak_telemetry_report, FamilyKind, InternalTimingMetric, InternalTimingMetricKind,
    LocalMutationEvidenceSummary, LocalSoakRunner, MockTelemetryClock, MutationClass, SoakShardId,
    SoakTelemetryClassification,
};

fn run_tiny() -> zkbench_core::SoakTelemetryReport {
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
fn telemetry_counters_increment_for_generation_mutation_and_replay() {
    let telemetry = run_tiny();
    assert!(telemetry.snapshot.counters.generated_instance_count > 0);
    assert!(telemetry.snapshot.counters.mutation_variant_count > 0);
    assert!(telemetry.snapshot.counters.local_replay_completed_count > 0);
    assert!(telemetry.snapshot.durations.generation_duration_ms > 0);
    assert!(telemetry.snapshot.durations.mutation_duration_ms > 0);
    assert!(telemetry.snapshot.durations.local_replay_duration_ms > 0);
}

#[test]
fn mock_clock_produces_deterministic_durations() {
    let first = run_tiny();
    let second = run_tiny();
    assert_eq!(first.snapshot.durations, second.snapshot.durations);
}

#[test]
fn telemetry_rejects_forbidden_backend_metric_labels() {
    let mut telemetry = run_tiny();
    telemetry
        .snapshot
        .durations
        .internal_timing_metrics
        .push(InternalTimingMetric {
            metric_name: "prover_time_ms".to_string(),
            kind: InternalTimingMetricKind::LocalReplay,
            duration_ms: 1,
            classification: vec![SoakTelemetryClassification::InternalOnly],
        });
    assert!(validate_soak_telemetry_report(&telemetry)
        .expect_err("forbidden label should fail")
        .to_string()
        .contains("forbidden metric label"));
}

#[test]
fn telemetry_rejects_oracle_counts_exceeding_traces() {
    let mut telemetry = run_tiny();
    telemetry.snapshot.counters.traces_evaluated = 1;
    telemetry.snapshot.counters.local_oracle_accepted_count = 2;
    telemetry.snapshot.counters.local_oracle_rejected_count = 1;
    telemetry
        .snapshot
        .counters
        .local_oracle_capability_gap_count = 1;

    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("impossible oracle counts should fail");

    assert!(error.to_string().contains("local oracle"));
    assert!(error.to_string().contains("exceed traces_evaluated"));
}

#[test]
fn telemetry_rejects_replay_attempts_without_inputs() {
    let mut telemetry = run_tiny();
    telemetry.snapshot.counters.generated_instance_count = 1;
    telemetry.snapshot.counters.mutation_variant_count = 0;
    telemetry.snapshot.counters.local_replay_completed_count = 2;
    telemetry.snapshot.counters.local_replay_failed_count = 1;

    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("impossible replay counts should fail");

    assert!(error.to_string().contains("local replay"));
    assert!(error
        .to_string()
        .contains("generated instances plus mutation variants"));
}

#[test]
fn telemetry_is_internal_and_does_not_populate_score_performance() {
    let telemetry = run_tiny();
    assert!(telemetry.is_internal_only());
    assert!(telemetry
        .snapshot
        .classification
        .contains(&SoakTelemetryClassification::NotZkBackendPerformance));

    let score = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: telemetry.snapshot.counters.local_oracle_accepted_count,
        local_rejected_traces: telemetry.snapshot.counters.local_oracle_rejected_count,
        mutation_variants_generated: telemetry.snapshot.counters.mutation_variant_count,
        outcome_changes_observed: 0,
        unsound_acceptance_candidates: 0,
    });
    assert!(score.performance.is_none());
}

#[test]
fn telemetry_roundtrips_through_json() {
    let telemetry = run_tiny();
    let json = serialize_soak_telemetry_report_json(&telemetry).expect("telemetry serialize");
    let roundtrip = deserialize_soak_telemetry_report_json(&json).expect("telemetry deserialize");
    assert_eq!(roundtrip, telemetry);
}
