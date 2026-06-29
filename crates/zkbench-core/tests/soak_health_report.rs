use zkbench_core::{
    aggregate_soak_health_reports, build_smoke_soak_config, deserialize_soak_health_report_json,
    health_findings_from_telemetry, plan_soak_shards, serialize_soak_health_report_json,
    validate_soak_health_report, ClaimBoundary, FamilyKind, LocalSoakRunner, MockTelemetryClock,
    MutationClass, SoakHealthFinding, SoakHealthFindingSeverity, SoakHealthRecommendation,
    SoakHealthStatus, SoakRegressionSignal, SoakRunResult, SoakShardId,
};

fn run_result() -> SoakRunResult {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());
    runner
        .run_shard(SoakShardId::from_index(0))
        .expect("run should complete")
}

fn run_health() -> zkbench_core::SoakHealthReport {
    run_result().health_report
}

#[test]
fn healthy_smoke_report_validates_and_contains_required_warnings() {
    let report = run_health();
    validate_soak_health_report(&report).expect("health report should validate");
    assert!(matches!(
        report.health_status,
        SoakHealthStatus::Healthy | SoakHealthStatus::HealthyWithWarnings
    ));
    let text = serde_json::to_string(&report).expect("health report should serialize");
    assert!(text.contains("Local soak telemetry is not official benchmark evidence."));
    assert!(text.contains("Internal timing telemetry is not ZK backend performance."));
    assert!(text.contains("No external backend was invoked."));
}

#[test]
fn health_report_detects_claim_boundary_elevation() {
    let mut report = run_health();
    report.claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    assert!(validate_soak_health_report(&report)
        .expect_err("claim elevation should fail")
        .to_string()
        .contains("Level0DesignNote"));
}

#[test]
fn health_report_detects_forbidden_metric_labels() {
    let mut report = run_health();
    report.findings.push(SoakHealthFinding {
        id: "proof_size_regression".to_string(),
        severity: SoakHealthFindingSeverity::Error,
        message: "simulated forbidden label".to_string(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
    });
    assert!(validate_soak_health_report(&report)
        .expect_err("forbidden label should fail")
        .to_string()
        .contains("forbidden metric label"));
}

#[test]
fn health_report_rejects_stale_summary_counts() {
    let mut report = run_health();
    report.summary.generated_instances = report.summary.generated_instances.saturating_add(1);

    let error = validate_soak_health_report(&report).expect_err("stale health summary should fail");

    assert!(error.to_string().contains("generated_instances"));
    assert!(error.to_string().contains("does not match telemetry"));
}

#[test]
fn health_report_rejects_empty_identity_fields() {
    let mut report = run_health();
    report.report_id = String::new();
    let error = validate_soak_health_report(&report).expect_err("empty report id should fail");
    assert!(error.to_string().contains("report id"));

    report = run_health();
    report.report_version = String::new();
    let error = validate_soak_health_report(&report).expect_err("empty report version should fail");
    assert!(error.to_string().contains("report version"));

    report = run_health();
    report.source_config_id = String::new();
    let error =
        validate_soak_health_report(&report).expect_err("empty source config id should fail");
    assert!(error.to_string().contains("source config id"));

    report = run_health();
    report.shard_id = None;
    let error =
        validate_soak_health_report(&report).expect_err("missing scope identity should fail");
    assert!(error
        .to_string()
        .contains("either shard-scoped or aggregate-scoped"));
}

#[test]
fn health_report_rejects_empty_scope_values() {
    let mut report = run_health();
    report.shard_id = Some(SoakShardId {
        value: String::new(),
    });
    let error = validate_soak_health_report(&report).expect_err("empty shard id should fail");
    assert!(error.to_string().contains("shard id"));

    report = run_health();
    report.shard_id = None;
    report.aggregate_id = Some(String::new());
    let error = validate_soak_health_report(&report).expect_err("empty aggregate id should fail");
    assert!(error.to_string().contains("aggregate id"));
}

#[test]
fn health_report_rejects_ambiguous_scope_identity() {
    let mut report = run_health();
    report.aggregate_id = Some("aggregate".to_string());

    let error =
        validate_soak_health_report(&report).expect_err("ambiguous scope identity should fail");

    assert!(error
        .to_string()
        .contains("both shard-scoped and aggregate-scoped"));
}

#[test]
fn health_report_rejects_empty_nested_identity_fields() {
    let mut report = run_health();
    report.findings[0].id = String::new();
    let error = validate_soak_health_report(&report).expect_err("empty finding id should fail");
    assert!(error.to_string().contains("finding id"));

    report = run_health();
    report.regression_signals.push(SoakRegressionSignal {
        id: String::new(),
        active: false,
        message: "simulated empty signal id".to_string(),
    });
    let error =
        validate_soak_health_report(&report).expect_err("empty regression signal id should fail");
    assert!(error.to_string().contains("regression signal id"));

    report = run_health();
    report.recommendations.push(SoakHealthRecommendation {
        id: String::new(),
        message: "simulated empty recommendation id".to_string(),
    });
    let error =
        validate_soak_health_report(&report).expect_err("empty recommendation id should fail");
    assert!(error.to_string().contains("recommendation id"));
}

#[test]
fn health_report_rejects_nested_claim_boundary_elevation_and_unsafe_note() {
    let mut report = run_health();
    report.findings[0].claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    let error =
        validate_soak_health_report(&report).expect_err("finding boundary elevation should fail");
    assert!(error
        .to_string()
        .contains("findings must remain Level0DesignNote"));

    report = run_health();
    report
        .notes
        .push("ZK backend performance improved in this local run".to_string());
    let error = validate_soak_health_report(&report)
        .expect_err("unsafe ZK backend performance note should fail");
    assert!(error
        .to_string()
        .contains("must not imply ZK backend performance"));
}

#[test]
fn health_report_rejects_healthy_status_with_failure_corpus_entries() {
    let mut report = run_health();
    report.health_status = SoakHealthStatus::Healthy;
    report.summary.failure_corpus_entries = 1;

    let error = validate_soak_health_report(&report)
        .expect_err("healthy status with failure corpus entries should fail");

    assert!(error.to_string().contains("healthy status"));
    assert!(error.to_string().contains("failure corpus entries"));
}

#[test]
fn health_report_rejects_each_summary_counter_drift() {
    let mut report = run_health();
    report.summary.mutation_variants = report.summary.mutation_variants.saturating_add(1);
    let error =
        validate_soak_health_report(&report).expect_err("mutation variant drift should fail");
    assert!(error.to_string().contains("mutation_variants"));

    report = run_health();
    report.summary.local_replays = report.summary.local_replays.saturating_add(1);
    let error = validate_soak_health_report(&report).expect_err("local replay drift should fail");
    assert!(error.to_string().contains("local_replays"));

    report = run_health();
    report.summary.failures = report.summary.failures.saturating_add(1);
    let error = validate_soak_health_report(&report).expect_err("failure count drift should fail");
    assert!(error.to_string().contains("failures"));
}

#[test]
fn health_report_can_represent_pack_validation_failure_without_elevation() {
    let mut report = run_health();
    report.findings.push(SoakHealthFinding {
        id: "pack_validation_failure".to_string(),
        severity: SoakHealthFindingSeverity::Error,
        message: "simulated pack validation failure".to_string(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
    });
    validate_soak_health_report(&report).expect("pack validation finding stays claim-safe");
}

#[test]
fn aggregate_health_report_merges_counters_findings_and_failure_warnings() {
    let healthy = run_health();
    let mut warning = run_health();
    warning.report_id = "warning-health-report".to_string();
    warning.shard_id = Some(SoakShardId::from_index(1));
    warning.health_status = SoakHealthStatus::HealthyWithWarnings;
    warning.summary.failure_corpus_entries = 2;

    let aggregate =
        aggregate_soak_health_reports("phase_215_health_aggregate", &[healthy, warning])
            .expect("aggregate health report should build");

    assert_eq!(aggregate.shard_id, None);
    assert_eq!(aggregate.aggregate_id.as_deref(), Some("aggregate"));
    assert_eq!(
        aggregate.health_status,
        SoakHealthStatus::HealthyWithWarnings
    );
    assert_eq!(aggregate.summary.failure_corpus_entries, 2);
    assert!(aggregate
        .regression_signals
        .iter()
        .any(|signal| signal.id == "aggregate_failure_corpus_growth" && signal.active));
    assert!(aggregate
        .findings
        .iter()
        .any(|finding| finding.id == "local_soak_telemetry_not_official"));
    validate_soak_health_report(&aggregate).expect("aggregate report validates");
}

#[test]
fn aggregate_health_report_preserves_status_precedence() {
    let mut inconclusive = run_health();
    inconclusive.health_status = SoakHealthStatus::Inconclusive;
    let mut degraded = run_health();
    degraded.report_id = "degraded-health-report".to_string();
    degraded.shard_id = Some(SoakShardId::from_index(1));
    degraded.health_status = SoakHealthStatus::Degraded;

    let aggregate =
        aggregate_soak_health_reports("phase_215_status_precedence", &[inconclusive, degraded])
            .expect("degraded aggregate should build");
    assert_eq!(aggregate.health_status, SoakHealthStatus::Degraded);

    let mut failed = run_health();
    failed.report_id = "failed-health-report".to_string();
    failed.shard_id = Some(SoakShardId::from_index(2));
    failed.health_status = SoakHealthStatus::Failed;
    let aggregate =
        aggregate_soak_health_reports("phase_215_failed_precedence", &[aggregate, failed])
            .expect("failed aggregate should build");
    assert_eq!(aggregate.health_status, SoakHealthStatus::Failed);
}

#[test]
fn health_findings_from_telemetry_reports_validation_and_replay_failures() {
    let mut telemetry = run_result().telemetry_report;
    telemetry.snapshot.counters.local_replay_failed_count = 1;

    let findings = health_findings_from_telemetry(&telemetry);
    assert!(findings.iter().any(|finding| {
        finding.id == "local_replay_failure"
            && finding.severity == SoakHealthFindingSeverity::Warning
            && finding.claim_boundary == ClaimBoundary::Level0DesignNote
    }));

    telemetry.report_id = String::new();
    let findings = health_findings_from_telemetry(&telemetry);
    assert!(findings.iter().any(|finding| {
        finding.id == "telemetry_validation_failure"
            && finding.severity == SoakHealthFindingSeverity::Error
            && finding.claim_boundary == ClaimBoundary::Level0DesignNote
    }));
}

#[test]
fn health_report_roundtrips_through_json() {
    let report = run_health();
    let json = serialize_soak_health_report_json(&report).expect("health report serialize");
    let roundtrip = deserialize_soak_health_report_json(&json).expect("health report deserialize");
    assert_eq!(roundtrip, report);
}
