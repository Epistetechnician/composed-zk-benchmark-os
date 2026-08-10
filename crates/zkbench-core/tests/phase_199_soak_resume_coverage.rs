//! Phase 199 soak resume checkpoint coverage thirty-fourth tranche.
//!
//! Focused local regression coverage for reachable `SoakShardCheckpoint`
//! validation and persistence paths in `crates/zkbench-core/src/soak/resume.rs`
//! that were not previously exercised. Every covered path is a reachable public
//! API behavior. Serializer-wrapper error closures over `#[derive(Serialize,
//! Deserialize)]` leaf structs remain capped and are intentionally not forced.

use tempfile::tempdir;
use zkbench_core::{
    build_smoke_soak_config, read_soak_shard_checkpoint, validate_soak_shard_checkpoint,
    write_soak_shard_checkpoint, ClaimBoundary, FailureArtifactRef, FamilyKind, MutationClass,
    SoakShardCheckpoint, SoakShardId, SoakShardResumeToken,
};

fn baseline_triple() -> (SoakShardCheckpoint, String, SoakShardResumeToken) {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = zkbench_core::plan_soak_shards(config).expect("plan should build");
    let shard_id = SoakShardId::from_index(0);
    let manifest = &plan.shard_manifests[0];
    let resume_token = SoakShardResumeToken::new(&shard_id, &manifest.config_digest);
    let checkpoint = SoakShardCheckpoint::empty(
        shard_id,
        manifest.config_digest.clone(),
        resume_token.clone(),
    );
    (checkpoint, manifest.config_digest.clone(), resume_token)
}

fn other_resume_token() -> SoakShardResumeToken {
    let other_id = SoakShardId::from_index(99);
    SoakShardResumeToken::new(&other_id, "0123456789ab")
}

#[test]
fn validate_rejects_elevated_claim_boundary() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.claim_boundary = ClaimBoundary::Level1LocalReplay;
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("elevated claim boundary should be rejected");
    assert!(error.to_string().contains("Level0DesignNote"));
}

#[test]
fn validate_rejects_empty_shard_id() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.shard_id = SoakShardId {
        value: "  ".to_string(),
    };
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("empty shard id should be rejected");
    assert!(error.to_string().contains("shard id is empty"));
}

#[test]
fn validate_rejects_resume_token_mismatch() {
    let (checkpoint, expected_digest, _expected_token) = baseline_triple();
    let other_token = other_resume_token();
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &other_token)
        .expect_err("resume token mismatch should be rejected");
    assert!(error.to_string().contains("resume token mismatch"));
}

#[test]
fn validate_rejects_artifact_ref_with_empty_relative_path() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "   ".to_string(),
        role: "checkpoint".to_string(),
        notes: Vec::new(),
    });
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("empty relative path should be rejected");
    assert!(error.to_string().contains("relative path"));
}

#[test]
fn validate_rejects_artifact_ref_with_empty_role() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "shards/shard-0000/checkpoint.json".to_string(),
        role: "\t".to_string(),
        notes: Vec::new(),
    });
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("empty role should be rejected");
    assert!(error.to_string().contains("must have a role"));
}

#[test]
fn validate_rejects_artifact_ref_with_parent_traversal() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "shards/../escape/checkpoint.json".to_string(),
        role: "checkpoint".to_string(),
        notes: Vec::new(),
    });
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("parent traversal should be rejected");
    assert!(error.to_string().contains("relative portable paths"));
}

#[test]
fn validate_rejects_artifact_ref_with_backslash() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "shards\\shard-0000\\checkpoint.json".to_string(),
        role: "checkpoint".to_string(),
        notes: Vec::new(),
    });
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("backslash relative path should be rejected");
    assert!(error.to_string().contains("relative portable paths"));
}

#[test]
fn validate_accepts_portable_artifact_ref() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "shards/shard-0000/checkpoint.json".to_string(),
        role: "checkpoint".to_string(),
        notes: vec!["local-only marker".to_string()],
    });
    validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect("portable artifact ref should validate");
}

#[test]
fn validate_rejects_empty_failed_id_after_completed_subset_check() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.completed_case_ids.push("case_a".to_string());
    checkpoint.failed_case_ids.push("   ".to_string());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("empty failed id should be rejected");
    assert!(error.to_string().contains("empty"));
}

#[test]
fn validate_rejects_empty_failure_corpus_ref() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.failure_corpus_refs.push("   ".to_string());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("empty failure corpus ref should be rejected");
    assert!(error.to_string().contains("empty"));
}

#[test]
fn validate_rejects_duplicate_completed_case_id() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.completed_case_ids = vec!["case_a".to_string(), "case_a".to_string()];
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("duplicate completed id should be rejected");
    assert!(error.to_string().contains("duplicated"));
}

#[test]
fn validate_rejects_absolute_artifact_ref_path() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.artifact_refs_written.push(FailureArtifactRef {
        relative_path: "/tmp/absolute-checkpoint.json".to_string(),
        role: "checkpoint".to_string(),
        notes: Vec::new(),
    });
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("absolute artifact path should be rejected");
    assert!(error.to_string().contains("relative portable paths"));
}

#[test]
fn validate_rejects_skipped_case_not_subset_of_completed() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.completed_case_ids.push("case_a".to_string());
    checkpoint.skipped_case_ids.push("case_missing".to_string());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("skipped outside completed should be rejected");
    assert!(error.to_string().contains("subset of completed"));
}

#[test]
fn validate_rejects_completed_and_failed_overlap() {
    let (mut checkpoint, expected_digest, expected_token) = baseline_triple();
    checkpoint.completed_case_ids.push("case_a".to_string());
    checkpoint.failed_case_ids.push("case_a".to_string());
    let error = validate_soak_shard_checkpoint(&checkpoint, &expected_digest, &expected_token)
        .expect_err("completed/failed overlap should be rejected");
    assert!(error.to_string().contains("overlap"));
}

#[test]
fn mark_helpers_are_idempotent_for_duplicate_case_ids() {
    let (mut checkpoint, _expected_digest, _expected_token) = baseline_triple();
    checkpoint.mark_completed("case_a".to_string(), 0);
    checkpoint.mark_completed("case_a".to_string(), 3);
    checkpoint.mark_failed("case_b".to_string());
    checkpoint.mark_failed("case_b".to_string());
    checkpoint.mark_skipped("case_a".to_string());
    checkpoint.mark_skipped("case_a".to_string());

    assert!(checkpoint.completed_case("case_a"));
    assert_eq!(checkpoint.completed_case_ids, vec!["case_a".to_string()]);
    assert_eq!(checkpoint.failed_case_ids, vec!["case_b".to_string()]);
    assert_eq!(checkpoint.skipped_case_ids, vec!["case_a".to_string()]);
    assert_eq!(checkpoint.last_completed_case_index, Some(3));
}

#[test]
fn write_checkpoint_rejects_parent_path_that_is_a_file() {
    let dir = tempdir().expect("tempdir should be available");
    let (checkpoint, _expected_digest, _expected_token) = baseline_triple();
    let parent_as_file = dir.path().join("not-a-directory");
    std::fs::write(&parent_as_file, b"block parent creation").expect("blocker file should write");
    let nested = parent_as_file.join("checkpoint.json");
    let error = write_soak_shard_checkpoint(&nested, &checkpoint)
        .expect_err("file-as-parent should fail create_dir_all");
    assert!(error.to_string().contains("not-a-directory"));
}

#[test]
fn write_then_read_checkpoint_round_trip_with_parent_creation() {
    let dir = tempdir().expect("tempdir should be available");
    let (checkpoint, _expected_digest, _expected_token) = baseline_triple();
    let nested = dir.path().join("deep/nested/dir/checkpoint.json");
    write_soak_shard_checkpoint(&nested, &checkpoint).expect("write should create parent dirs");
    let round_trip = read_soak_shard_checkpoint(&nested).expect("read should round-trip");
    assert_eq!(round_trip, checkpoint);
}

#[test]
fn read_checkpoint_rejects_missing_file() {
    let dir = tempdir().expect("tempdir should be available");
    let missing = dir.path().join("does-not-exist.json");
    let error = read_soak_shard_checkpoint(&missing).expect_err("missing file should be rejected");
    assert!(error.to_string().contains("does-not-exist.json"));
}

#[test]
fn read_checkpoint_rejects_malformed_json() {
    let dir = tempdir().expect("tempdir should be available");
    let path = dir.path().join("malformed.json");
    std::fs::write(&path, b"{ not json").expect("malformed file should write");
    let error = read_soak_shard_checkpoint(&path).expect_err("malformed json should be rejected");
    assert!(error.to_string().contains("read_soak_shard_checkpoint"));
}
