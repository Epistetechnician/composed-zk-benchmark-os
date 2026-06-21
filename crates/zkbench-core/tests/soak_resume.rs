use tempfile::tempdir;
use zkbench_core::{
    build_smoke_soak_config, deserialize_soak_shard_checkpoint_json, plan_soak_shards,
    read_soak_shard_checkpoint, serialize_soak_shard_checkpoint_json,
    validate_soak_shard_checkpoint, write_soak_shard_checkpoint, FailureArtifactRef, FamilyKind,
    LocalSoakRunner, MockTelemetryClock, MutationClass, SoakCaseStatus, SoakShardId,
};

#[test]
fn runner_writes_checkpoint_and_resume_skips_completed_cases() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");

    let mut first = LocalSoakRunner::new(plan.clone())
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let first_result = first
        .run_shard(SoakShardId::from_index(0))
        .expect("first run should complete");
    assert_eq!(first_result.checkpoint.completed_case_ids.len(), 2);

    let checkpoint_path = dir.path().join("shards/shard-0000/checkpoint.json");
    let checkpoint =
        read_soak_shard_checkpoint(&checkpoint_path).expect("checkpoint should be readable");
    assert_eq!(checkpoint.completed_case_ids.len(), 2);

    let mut second = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let second_result = second
        .run_shard(SoakShardId::from_index(0))
        .expect("resume should complete");
    assert!(second_result
        .case_results
        .iter()
        .all(|case| case.status == SoakCaseStatus::SkippedByResume));
    assert_eq!(
        second_result
            .telemetry_report
            .snapshot
            .counters
            .local_replay_completed_count,
        first_result
            .telemetry_report
            .snapshot
            .counters
            .local_replay_completed_count
    );
}

#[test]
fn resume_rejects_mismatched_config_digest_and_checkpoint_roundtrips() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan.clone())
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("run should complete");

    let json =
        serialize_soak_shard_checkpoint_json(&result.checkpoint).expect("checkpoint serialize");
    let roundtrip = deserialize_soak_shard_checkpoint_json(&json).expect("checkpoint deserialize");
    assert_eq!(roundtrip, result.checkpoint);

    let mut bad = result.checkpoint.clone();
    bad.config_digest = "bad_digest".to_string();
    let checkpoint_path = dir.path().join("shards/shard-0000/checkpoint.json");
    write_soak_shard_checkpoint(&checkpoint_path, &bad).expect("bad checkpoint should write");

    let mut resumed = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    assert!(resumed
        .run_shard(SoakShardId::from_index(0))
        .expect_err("mismatched digest should fail")
        .to_string()
        .contains("config digest mismatch"));
}

#[test]
fn checkpoint_rejects_ambiguous_case_id_state() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("run should complete");
    let expected_digest = result.checkpoint.config_digest.clone();
    let expected_token = result.checkpoint.resume_token.clone();

    let mut checkpoint = result.checkpoint.clone();
    checkpoint
        .completed_case_ids
        .push(checkpoint.completed_case_ids[0].clone());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("duplicate completed ids should be rejected");
    assert!(error.to_string().contains("duplicated"));

    checkpoint = result.checkpoint.clone();
    checkpoint
        .failed_case_ids
        .push(checkpoint.completed_case_ids[0].clone());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("completed/failed overlap should be rejected");
    assert!(error.to_string().contains("overlap"));

    checkpoint = result.checkpoint.clone();
    checkpoint
        .skipped_case_ids
        .push("case_not_completed".to_string());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("skipped ids outside completed ids should be rejected");
    assert!(error.to_string().contains("subset"));

    checkpoint = result.checkpoint.clone();
    checkpoint.failure_corpus_refs.push(String::new());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("empty failure corpus ref should be rejected");
    assert!(error.to_string().contains("empty"));
}

#[test]
fn checkpoint_rejects_invalid_artifact_refs() {
    let dir = tempdir().expect("tempdir should be available");
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(dir.path())
        .with_clock(MockTelemetryClock::default());
    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("run should complete");
    let expected_digest = result.checkpoint.config_digest.clone();
    let expected_token = result.checkpoint.resume_token.clone();
    let mut checkpoint = result.checkpoint.clone();

    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "/absolute/checkpoint.json".to_string(),
        role: "checkpoint".to_string(),
        notes: Vec::new(),
    });

    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("absolute checkpoint artifact ref should be rejected");

    assert!(error.to_string().contains("relative portable paths"));
}
