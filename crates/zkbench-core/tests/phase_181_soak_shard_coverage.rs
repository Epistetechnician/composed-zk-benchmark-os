use zkbench_core::{
    build_smoke_soak_config, plan_soak_shards, validate_soak_shard_manifest,
    validate_soak_shard_plan, validate_soak_shard_summary, ClaimBoundary, FamilyKind,
    MutationClass, SoakLimits, SoakShardPlanner, SoakShardProgress, SoakShardResumeToken,
    SoakShardStatus, SoakShardSummary,
};

fn shard_plan() -> zkbench_core::SoakShardPlan {
    plan_soak_shards(
        build_smoke_soak_config()
            .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
            .with_mutation_passes(vec![MutationClass::MissingConstraints])
            .with_seed_range(0..2)
            .with_shard_count(2),
    )
    .expect("phase 181 shard plan should build")
}

fn issue_messages(validation: &zkbench_core::SoakShardValidation) -> Vec<String> {
    validation
        .issues
        .iter()
        .map(|issue| issue.message.clone())
        .collect()
}

#[test]
fn shard_public_helpers_preserve_deterministic_local_boundary() {
    let progress = SoakShardProgress::new(7);
    assert_eq!(progress.total_cases, 7);
    assert_eq!(progress.completed_cases, 0);
    assert_eq!(progress.failed_cases, 0);
    assert_eq!(progress.skipped_cases, 0);

    let shard_id = zkbench_core::SoakShardId::from_index(3);
    assert_eq!(shard_id.value, "shard-0003");
    let short_token = SoakShardResumeToken::new(&shard_id, "abcdef");
    assert_eq!(short_token.value, "resume_shard-0003_abcdef");
    let long_token = SoakShardResumeToken::new(&shard_id, "0123456789abcdef");
    assert_eq!(long_token.value, "resume_shard-0003_0123456789ab");

    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BoundedCounterLoop])
        .with_mutation_passes(vec![MutationClass::BadCounters])
        .with_seed_range(4..6)
        .with_shard_count(2);
    let direct_plan = plan_soak_shards(config.clone()).expect("direct plan should build");
    let planner_plan = SoakShardPlanner::new(config)
        .plan()
        .expect("planner should delegate to plan_soak_shards");
    assert_eq!(planner_plan, direct_plan);
    assert_eq!(planner_plan.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn shard_planning_rejects_max_cases_per_shard_overflow() {
    let mut limits = SoakLimits::smoke();
    limits.max_cases_per_shard = 1;
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_shard_count(1)
        .with_limits(limits);

    let error = plan_soak_shards(config).expect_err("oversized shard should reject");
    let message = error.to_string();
    assert!(message.contains("soak.shard_plan.assignments"));
    assert!(message.contains("max_cases_per_shard"));
}

#[test]
fn shard_plan_validation_reports_manifest_digest_duplicate_and_missing_assignment_drift() {
    let plan = shard_plan();

    let mut invalid_manifest = plan.clone();
    invalid_manifest.shard_manifests[0].expected_case_count += 1;
    let error = validate_soak_shard_plan(&invalid_manifest)
        .expect_err("invalid nested manifest should reject");
    assert!(error.to_string().contains("invalid shard manifest"));

    let mut digest_drift = plan.clone();
    digest_drift.shard_manifests[0].config_digest = "different-config-digest".to_string();
    let error =
        validate_soak_shard_plan(&digest_drift).expect_err("config digest drift should reject");
    assert!(error.to_string().contains("config digest"));

    let mut duplicate_assignment = plan.clone();
    let duplicate_case = duplicate_assignment.shard_manifests[0].assigned_case_ids[0].clone();
    duplicate_assignment.shard_manifests[1]
        .assigned_case_ids
        .push(duplicate_case);
    duplicate_assignment.shard_manifests[1].expected_case_count = duplicate_assignment
        .shard_manifests[1]
        .assigned_case_ids
        .len();
    let error = validate_soak_shard_plan(&duplicate_assignment)
        .expect_err("duplicate case assignment should reject");
    assert!(error.to_string().contains("assigned more than once"));

    let mut missing_assignment = plan;
    missing_assignment.shard_manifests[0]
        .assigned_case_ids
        .pop();
    missing_assignment.shard_manifests[0].expected_case_count = missing_assignment.shard_manifests
        [0]
    .assigned_case_ids
    .len();
    let error = validate_soak_shard_plan(&missing_assignment)
        .expect_err("missing case assignment should reject");
    assert!(error.to_string().contains("do not match planned case ids"));
}

#[test]
fn shard_manifest_validation_reports_shape_boundary_and_portability_drift() {
    let plan = shard_plan();
    let mut manifest = plan.shard_manifests[0].clone();
    manifest.shard_id.value = " ".to_string();
    manifest.shard_index = manifest.shard_count;
    manifest.expected_case_count += 1;
    manifest.claim_boundary = ClaimBoundary::Level1LocalReplay;
    manifest.relative_artifact_refs = vec![
        "/absolute/path.json".to_string(),
        "nested/../escape.json".to_string(),
        "windows\\path.json".to_string(),
    ];

    let validation = validate_soak_shard_manifest(&manifest);
    assert!(!validation.valid);
    let messages = issue_messages(&validation);
    for expected in [
        "shard id is empty",
        "shard index must be less than shard count",
        "expected case count does not match assigned case ids",
        "shard manifest must remain Level0DesignNote",
    ] {
        assert!(
            messages.iter().any(|message| message.contains(expected)),
            "missing {expected:?}: {validation:?}"
        );
    }
    assert_eq!(
        messages
            .iter()
            .filter(|message| message.contains("portable relative paths"))
            .count(),
        3
    );
}

#[test]
fn shard_summary_validation_reports_boundary_progress_and_neutral_status_paths() {
    let mut summary = SoakShardSummary {
        shard_id: zkbench_core::SoakShardId {
            value: " ".to_string(),
        },
        status: SoakShardStatus::Running,
        progress: SoakShardProgress {
            total_cases: 2,
            completed_cases: 3,
            failed_cases: 3,
            skipped_cases: 4,
        },
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        notes: Vec::new(),
    };

    let validation = validate_soak_shard_summary(&summary);
    assert!(!validation.valid);
    let messages = issue_messages(&validation);
    for expected in [
        "shard id is empty",
        "shard summary must remain Level0DesignNote",
        "completed cases cannot exceed total cases",
        "failed cases cannot exceed total cases",
        "skipped resume cases cannot exceed completed cases",
    ] {
        assert!(
            messages.iter().any(|message| message.contains(expected)),
            "missing {expected:?}: {validation:?}"
        );
    }

    summary.shard_id = zkbench_core::SoakShardId::from_index(0);
    summary.progress = SoakShardProgress {
        total_cases: 3,
        completed_cases: 1,
        failed_cases: 1,
        skipped_cases: 0,
    };
    summary.claim_boundary = ClaimBoundary::Level0DesignNote;

    for status in [
        SoakShardStatus::Running,
        SoakShardStatus::Failed,
        SoakShardStatus::Resumable,
    ] {
        summary.status = status;
        let validation = validate_soak_shard_summary(&summary);
        assert!(
            validation.valid,
            "{status:?} should allow partial shard progress: {validation:?}"
        );
    }
}
