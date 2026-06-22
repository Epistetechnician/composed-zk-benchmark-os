use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    build_smoke_soak_config, plan_soak_shards, ClaimBoundary, FailureCorpusKind, FamilyKind,
    LocalSoakRunner, LocalSoakRunnerConfig, MockTelemetryClock, MutationClass, SoakArtifactLayout,
    SoakCaseStatus, SoakHealthStatus, SoakOutputPolicy, SoakRunRequest, SoakRunnerErrorPolicy,
    SoakShardId,
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

#[test]
fn sampled_pack_run_materializes_static_final_checkpoint_and_pack_artifacts() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::SampledPacks { max_packs: 1 });
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let layout = SoakArtifactLayout::for_shard(&shard_id);
    let case_id = plan.shard_manifests[0].assigned_case_ids[0].clone();
    let mut runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());

    let result = runner
        .run_shard(shard_id)
        .expect("sampled pack run should complete");

    assert_eq!(result.shard_summary.progress.completed_cases, 1);
    assert_eq!(
        result.telemetry_report.snapshot.counters.pack_write_count,
        1
    );
    assert_eq!(
        result
            .telemetry_report
            .snapshot
            .counters
            .pack_read_validation_count,
        1
    );
    for relative_path in [
        &layout.run_config_path,
        &layout.shard_plan_path,
        &layout.shard_manifest_path,
        &layout.checkpoint_path,
        &layout.telemetry_path,
        &layout.health_report_path,
        &layout.failure_corpus_index_path,
        &layout.local_summary_path,
    ] {
        assert!(
            dir.path().join(relative_path).exists(),
            "{relative_path} should be materialized"
        );
    }
    assert!(dir
        .path()
        .join(&layout.sampled_packs_dir)
        .join(case_id)
        .join("pack.json")
        .exists());
}

#[test]
fn checkpoint_resume_marks_completed_cases_as_skipped_without_rerunning() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let mut first_runner = LocalSoakRunner::new(plan.clone())
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let first = first_runner
        .run_shard(shard_id.clone())
        .expect("first run should complete");
    assert_eq!(first.shard_summary.progress.completed_cases, 1);

    let mut resumed_runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let resumed = resumed_runner
        .run_shard(shard_id)
        .expect("resume should read checkpoint and skip completed case");

    assert_eq!(resumed.case_results.len(), 1);
    assert_eq!(
        resumed.case_results[0].status,
        SoakCaseStatus::SkippedByResume
    );
    assert_eq!(resumed.shard_summary.progress.completed_cases, 1);
    assert_eq!(resumed.shard_summary.progress.skipped_cases, 1);
    assert_eq!(
        resumed
            .telemetry_report
            .snapshot
            .counters
            .generated_instance_count,
        first
            .telemetry_report
            .snapshot
            .counters
            .generated_instance_count
    );
}

#[test]
fn run_request_resume_false_ignores_existing_checkpoint() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let mut first_runner = LocalSoakRunner::new(plan.clone())
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    first_runner
        .run_shard(shard_id.clone())
        .expect("first run should complete");

    let mut rerun_runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let rerun = rerun_runner
        .run_request(SoakRunRequest {
            shard_id,
            resume: false,
        })
        .expect("resume false should ignore existing checkpoint");

    assert!(rerun
        .case_results
        .iter()
        .all(|case| case.status != SoakCaseStatus::SkippedByResume));
    assert_eq!(
        rerun
            .telemetry_report
            .snapshot
            .counters
            .generated_instance_count,
        1
    );
}

#[test]
fn runner_reports_unknown_shard_missing_resume_token_and_missing_case_plan() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("plan should build");

    let unknown_error = LocalSoakRunner::new(plan.clone())
        .run_shard(SoakShardId::from_index(99))
        .expect_err("unknown shard should fail");
    assert!(unknown_error.to_string().contains("unknown shard id"));

    let mut missing_token_plan = plan.clone();
    missing_token_plan.shard_manifests[0].resume_token = None;
    let token_error = LocalSoakRunner::new(missing_token_plan)
        .run_shard(SoakShardId::from_index(0))
        .expect_err("missing resume token should fail");
    assert!(token_error.to_string().contains("missing resume token"));

    let mut missing_case_plan = plan;
    missing_case_plan.case_plans.clear();
    let case_error = LocalSoakRunner::new(missing_case_plan)
        .run_shard(SoakShardId::from_index(0))
        .expect_err("missing case plan should fail");
    assert!(case_error.to_string().contains("was not found in plan"));
}

#[test]
fn stop_on_first_failure_halts_after_unimplemented_mutation_class() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let mut plan = plan_soak_shards(config).expect("plan should build");
    for case_plan in &mut plan.case_plans {
        case_plan.mutation_classes = vec![MutationClass::StaleStateReads];
    }
    let runner_config = LocalSoakRunnerConfig {
        error_policy: SoakRunnerErrorPolicy::StopOnFirstFailure,
        ..LocalSoakRunnerConfig::default()
    };
    let mut runner = LocalSoakRunner::new(plan)
        .with_runner_config(runner_config)
        .with_clock(MockTelemetryClock::default());

    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("mutation failure should be recorded, not thrown");

    assert_eq!(result.case_results.len(), 1);
    assert_eq!(
        result.case_results[0].status,
        SoakCaseStatus::FailedMutation
    );
    assert_eq!(result.shard_summary.progress.failed_cases, 1);
    assert_eq!(result.shard_summary.progress.completed_cases, 0);
    assert_eq!(result.failure_corpus_index.entries.len(), 1);
    assert_eq!(
        result.failure_corpus_index.entries[0].failure_kind,
        FailureCorpusKind::MutationFailure
    );
}

#[test]
fn stale_sampled_pack_directory_records_pack_write_failure_without_overwrite() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::SampledPacks { max_packs: 1 });
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let layout = SoakArtifactLayout::for_shard(&shard_id);
    let case_id = plan.shard_manifests[0].assigned_case_ids[0].clone();
    let stale_pack_dir = dir.path().join(&layout.sampled_packs_dir).join(&case_id);
    fs::create_dir_all(&stale_pack_dir).expect("stale pack dir should be creatable");
    fs::write(stale_pack_dir.join("stale.txt"), b"stale").expect("stale marker should write");
    let mut runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());

    let result = runner
        .run_shard(shard_id)
        .expect("pack write failure should be recorded, not thrown");

    assert_eq!(result.case_results.len(), 1);
    assert_eq!(
        result.case_results[0].status,
        SoakCaseStatus::FailedPackWrite
    );
    assert_eq!(
        result.case_results[0].failures[0].failure_kind,
        FailureCorpusKind::PackValidationFailure
    );
    assert_eq!(
        result.telemetry_report.snapshot.counters.pack_write_count,
        0
    );
    assert_eq!(result.telemetry_report.snapshot.counters.failure_count, 1);
    assert_eq!(result.failure_corpus_index.entries.len(), 1);
}
