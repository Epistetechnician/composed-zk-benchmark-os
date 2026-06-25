use zkbench_core::{
    build_smoke_soak_config, deserialize_soak_telemetry_report_json, plan_soak_shards,
    score_report_from_local_mutation_evidence, serialize_soak_telemetry_report_json,
    validate_soak_telemetry_report, FamilyKind, InternalCountMetric, InternalSizeMetric,
    InternalTimingMetric, InternalTimingMetricKind, LocalMutationEvidenceSummary, LocalSoakRunner,
    MockTelemetryClock, MutationClass, SoakShardId, SoakTelemetryClassification,
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
fn telemetry_rejects_empty_identity_fields() {
    let mut telemetry = run_tiny();
    telemetry.report_id = String::new();
    let error =
        validate_soak_telemetry_report(&telemetry).expect_err("empty report id should fail");
    assert!(error.to_string().contains("report id"));

    telemetry = run_tiny();
    telemetry.report_version = String::new();
    let error =
        validate_soak_telemetry_report(&telemetry).expect_err("empty report version should fail");
    assert!(error.to_string().contains("report version"));

    telemetry = run_tiny();
    telemetry.source_config_id = String::new();
    let error =
        validate_soak_telemetry_report(&telemetry).expect_err("empty source config id should fail");
    assert!(error.to_string().contains("source config id"));

    telemetry = run_tiny();
    telemetry.shard_id = None;
    let error =
        validate_soak_telemetry_report(&telemetry).expect_err("missing shard id should fail");
    assert!(error.to_string().contains("shard-scoped"));

    telemetry = run_tiny();
    telemetry.shard_id = Some(SoakShardId {
        value: String::new(),
    });
    let error = validate_soak_telemetry_report(&telemetry).expect_err("empty shard id should fail");
    assert!(error.to_string().contains("shard id"));
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
fn telemetry_rejects_metric_classification_drift() {
    let mut telemetry = run_tiny();
    telemetry
        .snapshot
        .durations
        .internal_timing_metrics
        .push(InternalTimingMetric {
            metric_name: "local_extra_duration_ms".to_string(),
            kind: InternalTimingMetricKind::LocalReplay,
            duration_ms: 1,
            classification: vec![SoakTelemetryClassification::InternalOnly],
        });
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("timing metric classification drift should fail");
    assert!(error.to_string().contains("metric classification"));

    telemetry = run_tiny();
    telemetry
        .snapshot
        .counters
        .failure_count_by_phase
        .push(InternalCountMetric {
            metric_name: "local_failure_count".to_string(),
            count: 1,
            classification: vec![SoakTelemetryClassification::InternalOnly],
        });
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("count metric classification drift should fail");
    assert!(error.to_string().contains("metric classification"));

    telemetry = run_tiny();
    telemetry
        .snapshot
        .counters
        .bytes_written_by_artifact_role
        .push(InternalSizeMetric {
            metric_name: "local_artifact_bytes".to_string(),
            byte_count: 1,
            classification: vec![SoakTelemetryClassification::InternalOnly],
        });
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("size metric classification drift should fail");
    assert!(error.to_string().contains("metric classification"));

    telemetry = run_tiny();
    telemetry
        .snapshot
        .counters
        .formal_lane_count_by_scope
        .push(InternalCountMetric {
            metric_name: "formal_lane_scope_machine_count".to_string(),
            count: 1,
            classification: vec![SoakTelemetryClassification::InternalOnly],
        });
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("formal scope metric classification drift should fail");
    assert!(error.to_string().contains("metric classification"));

    telemetry = run_tiny();
    telemetry
        .snapshot
        .counters
        .formal_lane_count_by_status
        .push(InternalCountMetric {
            metric_name: "formal_lane_status_declared_only_count".to_string(),
            count: 1,
            classification: vec![SoakTelemetryClassification::InternalOnly],
        });
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("formal status metric classification drift should fail");
    assert!(error.to_string().contains("metric classification"));
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
fn telemetry_rejects_impossible_formal_lane_counter_relationships() {
    let mut telemetry = run_tiny();
    telemetry
        .snapshot
        .counters
        .formal_lane_template_derived_count = 0;
    telemetry.snapshot.counters.formal_lane_evaluation_count = 1;
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("evaluation without template should fail");
    assert!(error.to_string().contains("formal lane evaluations"));

    telemetry = run_tiny();
    telemetry
        .snapshot
        .counters
        .formal_lane_template_derived_count = 1;
    telemetry.snapshot.counters.formal_lane_evaluation_count = 1;
    telemetry.snapshot.counters.formal_lane_declared_only_count = 2;
    let error = validate_soak_telemetry_report(&telemetry)
        .expect_err("declared-only without evaluation should fail");
    assert!(error.to_string().contains("declared-only formal lane"));
}

#[test]
fn telemetry_records_formal_lane_scope_and_status_metrics() {
    let telemetry = run_tiny();
    assert!(telemetry
        .snapshot
        .counters
        .formal_lane_count_by_scope
        .iter()
        .any(
            |metric| metric.metric_name == "formal_lane_scope_transition_guard_count"
                && metric.count > 0
        ));
    assert!(telemetry
        .snapshot
        .counters
        .formal_lane_count_by_status
        .iter()
        .any(
            |metric| metric.metric_name == "formal_lane_status_declared_only_count"
                && metric.count > 0
        ));
    assert!(validate_soak_telemetry_report(&telemetry).is_ok());
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
