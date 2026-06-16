use tempfile::tempdir;
use zkbench_core::{
    attach_reproduction_bundle_to_pack, build_failure_corpus_entry, build_smoke_soak_config,
    generate_instance, plan_soak_shards, read_reproduction_bundle_from_pack, run_soak_campaign,
    validate_soak_campaign_config, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    FailureCorpusEntryInput, FailureCorpusKind, FamilyKind, GeneratorConfig, GeneratorTunables,
    InstanceParams, LocalSoakRunnerConfig, MutationClass, SoakCampaignApproval,
    SoakCampaignArtifactRootPolicy, SoakCampaignConfig, SoakOutputPolicy, SoakShardId,
};

fn sample_entry(case_id: &str) -> zkbench_core::FailureCorpusEntry {
    build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(0),
        case_id: case_id.to_string(),
        family_kind: FamilyKind::BaselineFsm,
        generator_seed: 7,
        tunables: GeneratorTunables::default(),
        mutation_class: Some(MutationClass::MissingConstraints),
        trace_id: None,
        failure_kind: FailureCorpusKind::ReplayFailure,
        local_error_summary: "simulated replay failure".to_string(),
    })
}

fn write_sample_pack(root: &std::path::Path) {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(11),
        InstanceParams::default(),
    )
    .expect("instance should generate");
    BenchmarkPackWriter::new("phase_l_attach_test_pack")
        .with_generated_instance(instance)
        .include_score_report(false)
        .write_to(root)
        .expect("pack should write");
}

fn approved_config(campaign_id: &str, artifact_root: std::path::PathBuf) -> SoakCampaignConfig {
    SoakCampaignConfig {
        campaign_id: campaign_id.to_string(),
        approval: SoakCampaignApproval {
            approved_by: "local_user".to_string(),
            approval_statement: "approved long local soak campaign".to_string(),
            approved_at_ms: 0,
        },
        artifact_root_policy: SoakCampaignArtifactRootPolicy {
            artifact_root,
            declared_outside_repo_or_ignored: true,
        },
        runner_config: LocalSoakRunnerConfig::default(),
        notes: Vec::new(),
    }
}

#[test]
fn attach_reproduction_bundle_round_trips_and_keeps_pack_valid() {
    let dir = tempdir().expect("tempdir should be available");
    let pack_root = dir.path().join("pack");
    write_sample_pack(&pack_root);

    let entries = vec![sample_entry("case_a"), sample_entry("case_b")];
    let attachment =
        attach_reproduction_bundle_to_pack(&pack_root, &entries).expect("bundle should attach");

    assert_eq!(attachment.entry_count, 2);
    assert_eq!(attachment.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        attachment.relative_path,
        "reproduction/reproduction_bundle.json"
    );

    let bundle = read_reproduction_bundle_from_pack(&pack_root).expect("bundle should read back");
    assert_eq!(bundle.entries, entries);
    assert_eq!(bundle.pack_id, "phase_l_attach_test_pack");
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);

    let validation = BenchmarkPackReader::read(&pack_root)
        .expect("pack should read")
        .validate();
    assert!(validation.valid, "pack invalid: {:?}", validation.errors);
}

#[test]
fn attach_rejects_empty_entries() {
    let dir = tempdir().expect("tempdir should be available");
    let pack_root = dir.path().join("pack");
    write_sample_pack(&pack_root);

    let error = attach_reproduction_bundle_to_pack(&pack_root, &[])
        .expect_err("empty entries should be rejected");
    assert!(error.to_string().contains("at least one"));
}

#[test]
fn campaign_config_requires_approval_and_safe_artifact_root() {
    let dir = tempdir().expect("tempdir should be available");
    let mut config = approved_config("campaign_validation", dir.path().to_path_buf());
    validate_soak_campaign_config(&config).expect("approved config should validate");

    config.approval.approval_statement = String::new();
    assert!(validate_soak_campaign_config(&config).is_err());
    config.approval.approval_statement = "approved".to_string();

    config.artifact_root_policy.declared_outside_repo_or_ignored = false;
    assert!(validate_soak_campaign_config(&config).is_err());
    config.artifact_root_policy.declared_outside_repo_or_ignored = true;

    config.artifact_root_policy.artifact_root = "relative/dir".into();
    assert!(validate_soak_campaign_config(&config).is_err());
}

#[test]
fn small_campaign_runs_all_shards_and_aggregates_reports() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2)
        .with_output_policy(SoakOutputPolicy::FailurePacksOnly {
            max_failure_packs: 2,
        });
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let shard_count = plan.shard_manifests.len();
    let config = approved_config("campaign_smoke", dir.path().to_path_buf());

    let result = run_soak_campaign(&config, plan).expect("campaign should run");

    assert_eq!(result.shard_outcomes.len(), shard_count);
    assert_eq!(result.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!result.contains_zk_backend_performance_claims());
    assert_eq!(
        result.report_bundle.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(result.report_bundle.health_reports.len(), shard_count);
    assert_eq!(
        result.aggregate_health_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    // Smoke cases succeed, so no failure packs and no attachments.
    assert!(result
        .shard_outcomes
        .iter()
        .all(|outcome| outcome.reproduction_bundle_attachments.is_empty()));

    let campaign_root = dir.path().join("campaign_smoke");
    assert!(campaign_root
        .join("aggregate/aggregate_health_report.json")
        .exists());
    assert!(campaign_root
        .join("aggregate/report_bundle/soak_report_bundle.json")
        .exists());
}

#[test]
fn campaign_refuses_to_run_without_approval() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let mut config = approved_config("campaign_unapproved", dir.path().to_path_buf());
    config.approval.approved_by = String::new();

    let error = run_soak_campaign(&config, plan).expect_err("unapproved campaign should fail");
    assert!(error.to_string().contains("approval"));
}
