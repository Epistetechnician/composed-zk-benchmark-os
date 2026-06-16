use zkbench_core::{
    build_smoke_soak_config, deserialize_soak_health_report_json, plan_soak_shards,
    serialize_soak_health_report_json, validate_soak_health_report, ClaimBoundary, FamilyKind,
    LocalSoakRunner, MockTelemetryClock, MutationClass, SoakHealthFinding,
    SoakHealthFindingSeverity, SoakHealthStatus, SoakShardId,
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
