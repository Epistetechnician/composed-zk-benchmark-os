use zkbench_core::{
    build_regression_soak_config, build_smoke_soak_config, validate_soak_run_config, ClaimBoundary,
    FamilyKind, MutationClass, SoakFamilySelection, SoakLimits, SoakMutationSelection,
    SoakOutputPolicy, SoakRunConfig, SoakRunConfigVersion, SoakRunProfile, SoakSeedRange,
};

fn assert_config_error_contains(config: &SoakRunConfig, expected: &str) {
    let error = validate_soak_run_config(config)
        .expect_err("config should be rejected")
        .to_string();
    assert!(
        error.contains(expected),
        "expected error to contain {expected:?}, got {error:?}"
    );
}

fn tiny_valid_config() -> SoakRunConfig {
    build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
}

#[test]
fn soak_config_helpers_normalize_count_and_preserve_defaults() {
    let empty_range = SoakSeedRange::new(5, 5);
    assert_eq!(empty_range.len(), 0);
    assert!(empty_range.is_empty());
    assert!(empty_range.values().is_empty());

    let descending_range = SoakSeedRange::new(9, 3);
    assert_eq!(descending_range.len(), 0);
    assert!(descending_range.is_empty());

    let range = SoakSeedRange::new(2, 5);
    assert_eq!(range.len(), 3);
    assert_eq!(range.values(), vec![2, 3, 4]);
    assert_eq!(SoakSeedRange::default(), SoakSeedRange::new(0, 2));

    let family_selection = SoakFamilySelection {
        families: vec![
            FamilyKind::BoundedCounterLoop,
            FamilyKind::BaselineFsm,
            FamilyKind::BaselineFsm,
            FamilyKind::BranchingFsm,
        ],
    };
    assert_eq!(
        family_selection.normalized(),
        vec![
            FamilyKind::BaselineFsm,
            FamilyKind::BranchingFsm,
            FamilyKind::BoundedCounterLoop
        ]
    );

    let mutation_selection = SoakMutationSelection {
        mutation_classes: vec![
            MutationClass::BadCounters,
            MutationClass::MissingConstraints,
            MutationClass::BadCounters,
            MutationClass::CorruptedGuards,
        ],
    };
    assert_eq!(
        mutation_selection.normalized(),
        vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
            MutationClass::BadCounters
        ]
    );

    let config = tiny_valid_config()
        .with_families(family_selection.families)
        .with_mutation_passes(mutation_selection.mutation_classes)
        .with_seed_range(2..5);
    assert_eq!(config.normalized_families().len(), 3);
    assert_eq!(config.normalized_mutations().len(), 3);
    assert_eq!(config.planned_case_count(), 9);
    assert_eq!(config.planned_mutation_count(), 27);

    assert_eq!(
        SoakRunConfigVersion::default().value,
        "phase-k-local-soak-config-v0"
    );
}

#[test]
fn output_policies_report_requested_pack_writes() {
    assert_eq!(SoakOutputPolicy::NoPacks.max_pack_writes_requested(), 0);
    assert_eq!(
        SoakOutputPolicy::sampled_packs_and_failures().max_pack_writes_requested(),
        2
    );
    assert_eq!(
        SoakOutputPolicy::SampledPacks { max_packs: 7 }.max_pack_writes_requested(),
        7
    );
    assert_eq!(
        SoakOutputPolicy::FailurePacksOnly {
            max_failure_packs: 5
        }
        .max_pack_writes_requested(),
        5
    );
    assert_eq!(
        SoakOutputPolicy::AllPacksWithinLimit { max_packs: 11 }.max_pack_writes_requested(),
        11
    );
}

#[test]
fn config_builders_and_profiles_stay_local_and_validate() {
    let smoke = SoakRunConfig::smoke();
    smoke.validate().expect("smoke config should validate");
    assert_eq!(smoke.profile, SoakRunProfile::Smoke);
    assert_eq!(smoke.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(smoke.limits, SoakLimits::smoke());
    assert!(smoke
        .notes
        .iter()
        .any(|note| note.contains("not official benchmark evidence")));

    let regression = SoakRunConfig::regression();
    assert_eq!(regression, build_regression_soak_config());
    assert_eq!(regression.profile, SoakRunProfile::Regression);
    assert_eq!(regression.scope.seed_range, SoakSeedRange::new(0, 4));
    assert_eq!(
        regression.output_policy,
        SoakOutputPolicy::FailurePacksOnly {
            max_failure_packs: 2
        }
    );
    regression
        .validate()
        .expect("regression config should validate");

    let mut focused = tiny_valid_config();
    focused.profile = SoakRunProfile::Focused;
    focused.validate().expect("focused config should validate");

    focused.profile = SoakRunProfile::Custom;
    focused.validate().expect("custom config should validate");

    let nightly_limits = SoakLimits::nightly_local_explicit();
    assert!(nightly_limits.max_instances > SoakLimits::smoke().max_instances);
    assert!(
        nightly_limits.max_internal_duration_ms_hint
            > SoakLimits::smoke().max_internal_duration_ms_hint
    );
}

#[test]
fn validation_rejects_identity_boundary_and_empty_scope_drift() {
    let mut config = tiny_valid_config();
    config.id = "   ".to_string();
    assert_config_error_contains(&config, "soak config id is empty");

    let mut config = tiny_valid_config();
    config.claim_boundary = ClaimBoundary::Level1LocalReplay;
    assert_config_error_contains(&config, "soak config must remain Level0DesignNote");

    let mut config = tiny_valid_config();
    config.claim_boundary_policy.soak_artifact_claim_boundary = ClaimBoundary::Level1LocalReplay;
    assert_config_error_contains(
        &config,
        "Phase K soak artifacts must remain Level0DesignNote",
    );

    let mut config = tiny_valid_config();
    config.claim_boundary_policy.local_replay_claim_boundary_max =
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    assert_config_error_contains(
        &config,
        "local replay artifacts must remain Level1LocalReplay",
    );

    let config = tiny_valid_config().with_families(Vec::new());
    assert_config_error_contains(&config, "at least one family is required");

    let config = tiny_valid_config().with_seed_range(9..9);
    assert_config_error_contains(&config, "seed range must not be empty");

    let config = tiny_valid_config().with_mutation_passes(Vec::new());
    assert_config_error_contains(&config, "at least one mutation class is required");

    let config = tiny_valid_config().with_mutation_passes(vec![MutationClass::StaleStateReads]);
    assert_config_error_contains(&config, "not implemented for Phase K local soak runs");
}

#[test]
fn validation_rejects_limit_and_pack_policy_overflows() {
    let mut limits = SoakLimits::smoke();
    limits.max_families = 1;
    let config = build_smoke_soak_config()
        .with_families(vec![
            FamilyKind::BaselineFsm,
            FamilyKind::BranchingFsm,
            FamilyKind::BoundedCounterLoop,
        ])
        .with_limits(limits);
    assert_config_error_contains(&config, "exceeds max_families");

    let mut limits = SoakLimits::smoke();
    limits.max_instances = 1;
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..2)
        .with_limits(limits);
    assert_config_error_contains(&config, "exceeds max_instances");

    let mut limits = SoakLimits::smoke();
    limits.max_mutations = 1;
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_seed_range(0..1)
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
            MutationClass::BadCounters,
        ])
        .with_limits(limits);
    assert_config_error_contains(&config, "exceeds max_mutations");

    let config = tiny_valid_config().with_shard_count(0);
    assert_config_error_contains(&config, "shard count must be greater than zero");

    let mut limits = SoakLimits::smoke();
    limits.max_pack_writes = 2;
    let config = tiny_valid_config()
        .with_output_policy(SoakOutputPolicy::AllPacksWithinLimit { max_packs: 3 })
        .with_limits(limits);
    assert_config_error_contains(&config, "exceeds max_pack_writes");
}
