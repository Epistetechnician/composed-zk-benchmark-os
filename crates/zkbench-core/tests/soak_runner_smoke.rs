use tempfile::tempdir;
use zkbench_core::{
    build_smoke_soak_config, plan_soak_shards, ClaimBoundary, FailureCorpusKind, FamilyKind,
    LocalSoakRunner, MockTelemetryClock, MutationClass, SoakCaseStatus, SoakHealthStatus,
    SoakOutputPolicy, SoakShardId,
};

#[test]
fn tiny_smoke_run_executes_locally() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());

    let report = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("smoke shard should run");

    assert_eq!(report.claim_boundary(), ClaimBoundary::Level0DesignNote);
    assert!(!report.contains_zk_backend_performance_claims());
    assert!(report.telemetry().is_internal_only());
    assert!(
        report
            .telemetry_report
            .snapshot
            .counters
            .generated_instance_count
            > 0
    );
    assert!(
        report
            .telemetry_report
            .snapshot
            .counters
            .mutation_variant_count
            > 0
    );
    assert!(
        report
            .telemetry_report
            .snapshot
            .counters
            .local_replay_completed_count
            > 0
    );
    assert_eq!(
        report.health_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(matches!(
        report.health_report.health_status,
        SoakHealthStatus::Healthy | SoakHealthStatus::HealthyWithWarnings
    ));
    assert!(report.case_results.iter().all(|case| matches!(
        case.status,
        SoakCaseStatus::Completed | SoakCaseStatus::CompletedWithLocalRejections
    )));
}

#[test]
fn smoke_run_outputs_no_external_or_zk_harness_result_claims() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());
    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("local smoke run should complete");

    let health_json =
        serde_json::to_string(&result.health_report).expect("health report should serialize");
    assert!(!health_json.contains("zk-Harness result"));
    assert!(!health_json.contains("official benchmark evidence\":true"));
    assert_eq!(
        result.failure_corpus_index.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn default_smoke_scope_runs_all_implemented_families_without_generation_failures() {
    let config = build_smoke_soak_config()
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("default all-family plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());

    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("default all-family smoke run should complete");

    assert_eq!(
        result
            .telemetry_report
            .snapshot
            .counters
            .generated_instance_count,
        3
    );
    assert!(!result
        .failure_corpus_index
        .entries
        .iter()
        .any(|entry| entry.failure_kind == FailureCorpusKind::GenerationFailure));
}

#[test]
fn targetless_mutation_combination_is_counted_not_failed() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![MutationClass::BadCounters])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("branching fsm bad-counters plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());

    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("targetless local mutation should not fail the shard");

    assert_eq!(result.shard_summary.progress.failed_cases, 0);
    assert_eq!(
        result
            .telemetry_report
            .snapshot
            .counters
            .mutation_no_target_count,
        1
    );
    assert_eq!(result.telemetry_report.snapshot.counters.failure_count, 0);
    assert!(result.failure_corpus_index.entries.is_empty());
    assert!(result.case_results.iter().all(|case| matches!(
        case.status,
        SoakCaseStatus::Completed | SoakCaseStatus::CompletedWithLocalRejections
    )));
}
