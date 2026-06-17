use zkbench_core::{
    build_smoke_soak_config, deserialize_soak_health_report_json, plan_soak_shards,
    serialize_soak_health_report_json, validate_soak_health_report, ClaimBoundary, FamilyKind,
    LocalSoakRunner, MockTelemetryClock, MutationClass, SoakHealthFinding,
    SoakHealthFindingSeverity, SoakHealthRecommendation, SoakHealthStatus, SoakRegressionSignal,
    SoakShardId,
};

fn run_health() -> zkbench_core::SoakHealthReport {
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
        .health_report
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
fn health_report_roundtrips_through_json() {
    let report = run_health();
    let json = serialize_soak_health_report_json(&report).expect("health report serialize");
    let roundtrip = deserialize_soak_health_report_json(&json).expect("health report deserialize");
    assert_eq!(roundtrip, report);
}
