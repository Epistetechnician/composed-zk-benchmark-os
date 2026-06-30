use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    attach_reproduction_bundle_to_pack, build_failure_corpus_entry, build_smoke_soak_config,
    generate_instance, plan_soak_shards, read_reproduction_bundle_from_pack,
    read_soak_report_bundle, run_soak_campaign, soak_artifact_manifest,
    validate_reproduction_bundle, validate_soak_campaign_config, validate_soak_report_bundle,
    write_soak_report_bundle, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    FailureCorpusEntryInput, FailureCorpusKind, FamilyKind, GeneratorConfig, GeneratorTunables,
    InstanceParams, LocalSoakRunnerConfig, MutationClass, ReproductionBundle, SoakArtifactLayout,
    SoakArtifactRole, SoakCampaignApproval, SoakCampaignArtifactRootPolicy, SoakCampaignConfig,
    SoakOutputPolicy, SoakReportBundle, SoakShardId,
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

fn campaign_bundle(campaign_id: &str, shard_count: usize) -> SoakReportBundle {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..shard_count as u64)
        .with_shard_count(shard_count);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config(campaign_id, dir.path().to_path_buf());
    run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle
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
fn reproduction_bundle_rejects_duplicate_entry_ids() {
    let entry = sample_entry("case_duplicate");
    let bundle = ReproductionBundle {
        bundle_id: "bundle_duplicate".to_string(),
        bundle_version: "phase-l-reproduction-bundle-v0".to_string(),
        pack_id: "pack_duplicate".to_string(),
        entries: vec![entry.clone(), entry],
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    };

    let error = validate_reproduction_bundle(&bundle)
        .expect_err("duplicate reproduction entries should fail");

    assert!(error.to_string().contains("entry id"));
    assert!(error.to_string().contains("duplicated"));
}

#[test]
fn reproduction_bundle_rejects_empty_bundle_identity() {
    let mut bundle = ReproductionBundle {
        bundle_id: String::new(),
        bundle_version: "phase-l-reproduction-bundle-v0".to_string(),
        pack_id: "pack_identity".to_string(),
        entries: vec![sample_entry("case_identity")],
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    };

    let error = validate_reproduction_bundle(&bundle).expect_err("empty bundle id should fail");
    assert!(error.to_string().contains("bundle id"));

    bundle.bundle_id = "bundle_identity".to_string();
    bundle.pack_id = String::new();
    let error = validate_reproduction_bundle(&bundle).expect_err("empty pack id should fail");
    assert!(error.to_string().contains("pack id"));
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
fn campaign_config_rejects_nonportable_campaign_ids() {
    let dir = tempdir().expect("tempdir should be available");
    for campaign_id in [
        "/tmp/escape",
        "../escape",
        "campaign/child",
        "campaign\\child",
        ".",
        "..",
    ] {
        let config = approved_config(campaign_id, dir.path().to_path_buf());
        let error = validate_soak_campaign_config(&config)
            .expect_err("nonportable campaign ids should fail");
        assert!(error.to_string().contains("portable path segment"));
    }
}

#[test]
fn soak_artifact_paths_are_portable_and_relative() {
    let shard_id = SoakShardId::from_index(3);
    let layout = SoakArtifactLayout::for_shard(&shard_id);
    assert!(layout.uses_relative_paths_only());

    let manifest = soak_artifact_manifest(
        "telemetry_shard_3",
        SoakArtifactRole::Telemetry,
        &layout.telemetry_path,
        &layout,
    )
    .expect("documented layout path should be accepted");
    assert_eq!(manifest.relative_path, layout.telemetry_path);
    assert_eq!(manifest.claim_boundary, ClaimBoundary::Level0DesignNote);

    for bad_path in [
        "",
        "/tmp/telemetry.json",
        "../telemetry.json",
        "shards/../telemetry.json",
        "shards\\telemetry.json",
    ] {
        let error =
            soak_artifact_manifest("bad_path", SoakArtifactRole::Telemetry, bad_path, &layout)
                .expect_err("non-portable artifact paths should be rejected");
        assert!(error.to_string().contains("portable and relative"));
    }

    for bad_artifact_id in ["", "telemetry/3", "telemetry\\3", "telemetry..3"] {
        let error = soak_artifact_manifest(
            bad_artifact_id,
            SoakArtifactRole::Telemetry,
            &layout.telemetry_path,
            &layout,
        )
        .expect_err("non-portable artifact ids should be rejected");
        assert!(error.to_string().contains("portable identifiers"));
    }
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
    assert_eq!(result.report_bundle.telemetry_reports.len(), shard_count);
    assert_eq!(
        result.report_bundle.failure_corpus_indexes.len(),
        shard_count
    );
    assert_eq!(result.report_bundle.shard_manifests.len(), shard_count);
    let bundle_validation = validate_soak_report_bundle(&result.report_bundle);
    assert!(
        bundle_validation.valid,
        "report bundle invalid: {:?}",
        bundle_validation.issues
    );
    assert_eq!(
        result.report_bundle.artifact_digest_set.artifacts.len(),
        1 + shard_count * 3
    );
    assert_eq!(
        result
            .report_bundle
            .artifact_digest_set
            .artifacts
            .iter()
            .filter(|artifact| artifact.role == SoakArtifactRole::AggregateReport)
            .count(),
        1
    );
    for role in [
        SoakArtifactRole::HealthReport,
        SoakArtifactRole::Telemetry,
        SoakArtifactRole::FailureCorpusIndex,
    ] {
        assert_eq!(
            result
                .report_bundle
                .artifact_digest_set
                .artifacts
                .iter()
                .filter(|artifact| artifact.role == role)
                .count(),
            shard_count
        );
    }
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
fn report_bundle_validation_rejects_nested_claim_boundary_elevation() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_nested_boundary", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    bundle.telemetry_reports[0].claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.contains("telemetry_reports[0]") && issue.contains("claim_boundary")
    }));
}

#[test]
fn report_bundle_validation_rejects_bundle_and_plan_boundary_drift() {
    let mut bundle = campaign_bundle("campaign_phase_225_boundary_drift", 1);
    bundle.claim_boundary = ClaimBoundary::Level1LocalReplay;
    bundle.shard_plan.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("report bundle must remain Level0DesignNote")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("shard plan must remain Level0DesignNote")));
}

#[test]
fn report_bundle_validation_rejects_duplicate_or_digestless_artifacts() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_duplicate_artifact", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    let mut duplicate = bundle.artifact_digest_set.artifacts[0].clone();
    duplicate.digest = None;
    bundle.artifact_digest_set.artifacts.push(duplicate);
    bundle.artifact_digest_set.artifacts[1].artifact_id = String::new();

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("duplicate artifact id")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("duplicate artifact path")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("missing digest")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("artifact id is not portable")));
}

#[test]
fn report_bundle_validation_rejects_artifact_path_and_boundary_drift() {
    let mut bundle = campaign_bundle("campaign_phase_225_artifact_path_drift", 1);
    let artifact = bundle
        .artifact_digest_set
        .artifacts
        .iter_mut()
        .find(|artifact| artifact.role == SoakArtifactRole::HealthReport)
        .expect("campaign bundle should include a health artifact");
    artifact.relative_path = "../health_report.json".to_string();
    artifact.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("artifact path is not portable relative")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("exceeded Level0DesignNote")));
}

#[test]
fn report_bundle_validation_rejects_report_artifact_role_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_artifact_role_drift", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    let telemetry_index = bundle
        .artifact_digest_set
        .artifacts
        .iter()
        .position(|artifact| artifact.role == SoakArtifactRole::Telemetry)
        .expect("campaign bundle should include telemetry artifacts");
    bundle.artifact_digest_set.artifacts.remove(telemetry_index);

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("artifact_digest_set.telemetry count")));
}

#[test]
fn report_bundle_validation_rejects_health_and_failure_artifact_count_drift() {
    let mut bundle = campaign_bundle("campaign_phase_225_artifact_count_drift", 1);
    bundle.artifact_digest_set.artifacts.retain(|artifact| {
        !matches!(
            artifact.role,
            SoakArtifactRole::HealthReport | SoakArtifactRole::FailureCorpusIndex
        )
    });

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("artifact_digest_set.health_reports count")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("artifact_digest_set.failure_corpus_indexes count")));
}

#[test]
fn report_bundle_validation_rejects_report_artifact_identity_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config(
        "campaign_report_artifact_identity_drift",
        dir.path().to_path_buf(),
    );
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    let telemetry = bundle
        .artifact_digest_set
        .artifacts
        .iter_mut()
        .find(|artifact| artifact.role == SoakArtifactRole::Telemetry)
        .expect("bundle should include telemetry artifact");
    telemetry.artifact_id = "telemetry_wrong_shard".to_string();
    telemetry.relative_path = "shards/shard-0000/telemetry_wrong.json".to_string();

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("missing expected Telemetry artifact")));
}

#[test]
fn report_bundle_validation_rejects_aggregate_report_artifact_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config(
        "campaign_aggregate_artifact_drift",
        dir.path().to_path_buf(),
    );
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    let aggregate = bundle
        .artifact_digest_set
        .artifacts
        .iter_mut()
        .find(|artifact| artifact.role == SoakArtifactRole::AggregateReport)
        .expect("campaign bundle should include an aggregate report artifact");
    aggregate.artifact_id = "aggregate_wrong".to_string();
    aggregate.relative_path = "aggregate/wrong_report.json".to_string();
    let duplicate = aggregate.clone();
    bundle.artifact_digest_set.artifacts.push(duplicate);

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("aggregate_reports count")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("aggregate/aggregate_health_report.json")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("aggregate_health_")));
}

#[test]
fn report_bundle_validation_rejects_empty_bundle_identity() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_bundle_identity_drift", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    bundle.bundle_id = String::new();
    bundle.bundle_version = String::new();

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("bundle id")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("bundle version")));
}

#[test]
fn report_bundle_validation_rejects_config_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_config_drift", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    bundle.config.id = "drifted_config".to_string();

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("bundle config does not match shard_plan.config")));
}

#[test]
fn report_bundle_validation_rejects_shard_cardinality_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_cardinality_drift", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    bundle.telemetry_reports.pop();
    bundle.health_reports.pop();
    bundle.failure_corpus_indexes.pop();

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("telemetry_reports count")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("health_reports count")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("failure_corpus_indexes count")));
}

#[test]
fn report_bundle_validation_rejects_shard_manifest_content_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config("campaign_manifest_content_drift", dir.path().to_path_buf());
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    bundle.shard_manifests[0]
        .assigned_case_ids
        .push("unplanned_case".to_string());

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue
            .contains("shard_manifests[0] does not match shard_plan.shard_manifests[0]")));
    assert!(validation.issues.iter().any(|issue| {
        issue.contains("shard_manifests[0] invalid")
            && issue.contains("expected case count does not match assigned case ids")
    }));
}

#[test]
fn report_bundle_validation_rejects_nested_report_shard_identity_drift() {
    let dir = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(2);
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let config = approved_config(
        "campaign_report_shard_identity_drift",
        dir.path().to_path_buf(),
    );
    let mut bundle = run_soak_campaign(&config, plan)
        .expect("campaign should run")
        .report_bundle;

    bundle.telemetry_reports[0].shard_id = Some(bundle.shard_manifests[1].shard_id.clone());
    bundle.health_reports[0].shard_id = Some(bundle.shard_manifests[1].shard_id.clone());
    let mut entry = sample_entry("case_bundle_shard_mismatch");
    entry.reproduction_manifest.shard_id = bundle.shard_manifests[1].shard_id.clone();
    bundle.failure_corpus_indexes[0].summary.entry_count = 1;
    bundle.failure_corpus_indexes[0]
        .summary
        .replay_failure_count = 1;
    bundle.failure_corpus_indexes[0].entries.push(entry);

    let validation = validate_soak_report_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("telemetry_reports[0].shard_id")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("health_reports[0].shard_id")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.contains("failure_corpus_indexes[0].entries[0]")));
}

#[test]
fn soak_report_bundle_io_rejects_file_roots_non_empty_roots_and_invalid_bundles() {
    let bundle = campaign_bundle("campaign_phase_225_bundle_io", 1);
    let dir = tempdir().expect("tempdir should be available");

    let file_root = dir.path().join("bundle-file");
    fs::write(&file_root, b"occupied").expect("file root should write");
    let error = write_soak_report_bundle(&file_root, &bundle)
        .expect_err("file root should reject before writing");
    assert!(error.to_string().contains("not a directory"));

    let non_empty_root = dir.path().join("non-empty-root");
    fs::create_dir_all(&non_empty_root).expect("non-empty root should create");
    fs::write(non_empty_root.join("existing.txt"), b"occupied")
        .expect("existing file should write");
    let error = write_soak_report_bundle(&non_empty_root, &bundle)
        .expect_err("non-empty root should reject");
    assert!(error.to_string().contains("non-empty"));

    let mut invalid_bundle = bundle.clone();
    invalid_bundle.bundle_id.clear();
    let error = write_soak_report_bundle(dir.path().join("invalid-bundle"), &invalid_bundle)
        .expect_err("invalid bundle should reject before write");
    assert!(error.to_string().contains("invalid bundle"));
}

#[test]
fn soak_report_bundle_io_round_trips_and_rejects_missing_or_malformed_json() {
    let bundle = campaign_bundle("campaign_phase_225_bundle_readback", 1);
    let dir = tempdir().expect("tempdir should be available");
    let output_root = dir.path().join("bundle-output");

    write_soak_report_bundle(&output_root, &bundle).expect("bundle should write");
    let read_back = read_soak_report_bundle(&output_root).expect("bundle should read");
    assert_eq!(read_back, bundle);

    let missing_root = dir.path().join("missing-output");
    let error = read_soak_report_bundle(&missing_root).expect_err("missing bundle should reject");
    assert!(error.to_string().contains("soak_report_bundle.json"));

    fs::write(output_root.join("soak_report_bundle.json"), b"{not json")
        .expect("malformed bundle JSON should write");
    let error = read_soak_report_bundle(&output_root).expect_err("malformed JSON should reject");
    assert!(error.to_string().contains("read_soak_report_bundle"));
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
