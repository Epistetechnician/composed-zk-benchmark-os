use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    build_smoke_soak_config, extract_failure_corpus, plan_soak_shards, resume_local_soak_shard,
    run_local_soak_shard, ClaimBoundary, FailureCorpusKind, FamilyKind, LocalJsonAdapter,
    LocalJsonAdapterConfig, LocalSoakRunner, LocalSoakRunnerConfig, MockTelemetryClock,
    MutationClass, SoakArtifactLayout, SoakCaseStatus, SoakOutputPolicy, SoakRunnerErrorPolicy,
    SoakShardId,
};

fn baseline_missing_constraints_config() -> zkbench_core::SoakRunConfig {
    build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
}

fn adapter_with_wrong_id() -> LocalJsonAdapter {
    LocalJsonAdapter {
        config: LocalJsonAdapterConfig {
            adapter_id: "phase_198_wrong_local_adapter".to_string(),
            ..LocalJsonAdapterConfig::default()
        },
    }
}

#[test]
fn public_shard_wrappers_run_and_resume_local_outputs() {
    let config =
        baseline_missing_constraints_config().with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);

    let run_result = run_local_soak_shard(plan.clone(), shard_id.clone())
        .expect("public run wrapper should run");
    assert_eq!(run_result.claim_boundary(), ClaimBoundary::Level0DesignNote);
    assert_eq!(run_result.shard_summary.progress.total_cases, 1);

    let dir = tempdir().expect("tempdir should be available");
    let first_resume = resume_local_soak_shard(plan.clone(), shard_id.clone(), dir.path())
        .expect("public resume wrapper should run and write checkpoint");
    assert_eq!(first_resume.shard_summary.progress.completed_cases, 1);

    let second_resume = resume_local_soak_shard(plan, shard_id, dir.path())
        .expect("public resume wrapper should read checkpoint");
    assert_eq!(
        second_resume.case_results[0].status,
        SoakCaseStatus::SkippedByResume
    );
    assert_eq!(second_resume.shard_summary.progress.skipped_cases, 1);
}

#[test]
fn failure_only_packs_and_stop_policy_record_replay_failure_once() {
    let dir = tempdir().expect("tempdir should be available");
    let config = baseline_missing_constraints_config()
        .with_seed_range(0..3)
        .with_output_policy(SoakOutputPolicy::FailurePacksOnly {
            max_failure_packs: 2,
        });
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let layout = SoakArtifactLayout::for_shard(&shard_id);
    let mut runner = LocalSoakRunner::new(plan.clone())
        .with_temp_or_user_output_dir(dir.path())
        .with_local_json_adapter(adapter_with_wrong_id())
        .with_clock(MockTelemetryClock::default())
        .with_runner_config(LocalSoakRunnerConfig {
            error_policy: SoakRunnerErrorPolicy::StopOnFirstFailure,
            ..LocalSoakRunnerConfig::default()
        });

    let result = runner
        .run_shard(shard_id.clone())
        .expect("replay failure should be recorded inside the run result");

    assert_eq!(result.case_results.len(), 1);
    assert_eq!(result.case_results[0].status, SoakCaseStatus::FailedReplay);
    assert_eq!(result.shard_summary.progress.total_cases, 3);
    assert_eq!(result.shard_summary.progress.failed_cases, 1);
    assert_eq!(result.telemetry_report.snapshot.counters.failure_count, 2);
    assert_eq!(
        result
            .telemetry_report
            .snapshot
            .counters
            .local_replay_failed_count,
        2
    );
    assert_eq!(
        result.telemetry_report.snapshot.counters.pack_write_count,
        1
    );
    assert!(dir
        .path()
        .join(&layout.failure_packs_dir)
        .join(&result.case_results[0].case_id)
        .join("pack.json")
        .exists());
    assert!(!dir.path().join(&layout.sampled_packs_dir).exists());

    let extracted = extract_failure_corpus(&plan, shard_id, &result.case_results);
    assert_eq!(
        extracted.entries.len(),
        result.case_results[0].failures.len()
    );
    assert!(extracted
        .entries
        .iter()
        .all(|entry| entry.failure_kind == FailureCorpusKind::ReplayFailure));
}

#[test]
fn all_packs_with_overwrite_allows_stale_sampled_pack_directory() {
    let dir = tempdir().expect("tempdir should be available");
    let config = baseline_missing_constraints_config()
        .with_output_policy(SoakOutputPolicy::AllPacksWithinLimit { max_packs: 1 });
    let plan = plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let layout = SoakArtifactLayout::for_shard(&shard_id);
    let case_id = plan.shard_manifests[0].assigned_case_ids[0].clone();
    let stale_pack_dir = dir.path().join(&layout.sampled_packs_dir).join(&case_id);
    fs::create_dir_all(&stale_pack_dir).expect("stale pack directory should be creatable");
    fs::write(stale_pack_dir.join("stale.txt"), b"stale").expect("stale marker should write");

    let mut runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default())
        .with_runner_config(LocalSoakRunnerConfig {
            overwrite_existing_packs: true,
            ..LocalSoakRunnerConfig::default()
        });

    let result = runner
        .run_shard(shard_id)
        .expect("overwrite-enabled runner should replace stale sampled pack");

    assert_eq!(
        result.case_results[0].status,
        SoakCaseStatus::CompletedWithLocalRejections
    );
    assert_eq!(
        result.telemetry_report.snapshot.counters.pack_write_count,
        1
    );
    assert_eq!(result.telemetry_report.snapshot.counters.failure_count, 0);
    assert!(stale_pack_dir.join("pack.json").exists());
    assert!(stale_pack_dir.join("stale.txt").exists());
}
